"""Messaging threads, job completion, reciprocal reviews, success stories
and private bad-experience reports."""

import datetime
import json
import logging
import random
import string
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import quote

import reflex as rx
from sqlalchemy import text
from app.message_photos import decode_message, message_preview

from app.image_processing import (
    ALLOWED_IMAGE_SUFFIXES,
    PHOTO_MAX_BYTES,
    process_help_photo_bytes,
    read_image_upload,
)
from app.member_blocks import BLOCK_UNAVAILABLE_MESSAGE, are_members_blocked
from app.interface_i18n import translate
from app.models import (
    CATEGORY_LABELS,
    CHECK_IN_NOTE_MAX_LENGTH,
    CHECK_IN_PROMPT_MAX_LENGTH,
    CHECK_IN_STATUS_CANCELLED,
    CHECK_IN_STATUS_COMPLETED,
    CHECK_IN_STATUS_PENDING,
    COMPLETED_TASK_PHOTO_MAX_COUNT,
    HELP_DURATION_LABELS,
    HELP_DURATION_VALUES,
    help_duration_label,
    MODERATION_STATUS_WARNED,
    REVIEW_HELPER_CATEGORY_LABELS,
    REVIEW_POSTER_CATEGORY_LABELS,
    SAFETY_REPORT_CATEGORIES,
    SAFETY_REPORT_CATEGORY_LABELS,
    SAFETY_STATUS_OPEN,
)
from app.states.auth_state import AuthState
from app.verification import public_base_url

REVIEW_WORD_LIMIT = 500
REVIEW_CONTENT_PREFIX = "skillkind-review:"
REVIEW_ELIGIBILITY_ERROR = (
    "This review is not eligible for this completed task."
)


def encode_review_content(comment: str, response: str = "") -> str:
    return f"{REVIEW_CONTENT_PREFIX}{json.dumps({'version': 1, 'text': comment, 'response': response}, ensure_ascii=False)}"


def decode_review_content(comment: str | None) -> tuple[str, str]:
    raw = comment or ""
    if not raw.startswith(REVIEW_CONTENT_PREFIX):
        return raw, ""
    try:
        payload = json.loads(raw[len(REVIEW_CONTENT_PREFIX) :])
        if (
            not isinstance(payload, dict)
            or payload.get("version") != 1
            or not isinstance(payload.get("text"), str)
            or not isinstance(payload.get("response", ""), str)
        ):
            return "Review text unavailable.", ""
        return payload["text"], payload.get("response", "")
    except (ValueError, TypeError, RecursionError) as e:
        logging.exception(f"Error: {e}")
        return "Review text unavailable.", ""


def review_released_sql(alias: str = "r") -> str:
    """Only trusted SQL aliases, never member input."""
    if alias not in {"r", "r2", "r3"}:
        raise ValueError("Invalid review alias")
    return f"""EXISTS (
        SELECT 1 FROM skillkind_completed_task release_task
        WHERE release_task.id = {alias}.completed_task_id
          AND release_task.poster_id <> release_task.helper_id
          AND (({alias}.reviewer_id = release_task.poster_id
                AND {alias}.reviewee_id = release_task.helper_id
                AND release_task.poster_confirmed)
            OR ({alias}.reviewer_id = release_task.helper_id
                AND {alias}.reviewee_id = release_task.poster_id
                AND release_task.helper_confirmed))
    )"""


async def refresh_review_ratings(asession, member_ids: list[int]):
    """Refresh both recipients using the immediate public release rule."""
    await asession.execute(
        text(f"""
        UPDATE skillkind_profile p SET
            helper_rating_avg = totals.helper_avg,
            helper_rating_count = totals.helper_count,
            traveller_rating_avg = totals.poster_avg,
            traveller_rating_count = totals.poster_count
        FROM (
            SELECT target.subscriber_id,
                COALESCE(AVG(r.rating) FILTER (WHERE r.direction = 'poster_to_helper'), 0) AS helper_avg,
                COUNT(r.id) FILTER (WHERE r.direction = 'poster_to_helper') AS helper_count,
                COALESCE(AVG(r.rating) FILTER (WHERE r.direction = 'helper_to_poster'), 0) AS poster_avg,
                COUNT(r.id) FILTER (WHERE r.direction = 'helper_to_poster') AS poster_count
            FROM skillkind_profile target
            LEFT JOIN skillkind_review r ON r.reviewee_id = target.subscriber_id
                AND {review_released_sql()}
            WHERE target.subscriber_id = ANY(:members)
            GROUP BY target.subscriber_id
        ) totals WHERE p.subscriber_id = totals.subscriber_id
    """),
        {"members": member_ids},
    )


# Bad-experience details: required, with a sensible upper bound.
REPORT_DETAILS_MIN = 20
REPORT_DETAILS_MAX = 2000
# More than two one-star reviews flags an account for admin inspection.
ONE_STAR_FLAG_THRESHOLD = 2
# Shown whenever a direct-request decision touches no qualifying row.
STALE_REQUEST_ERROR = (
    "That request is no longer open — it may have been withdrawn, "
    "already answered, or given to another helper."
)


def unique_photo_name() -> str:
    token = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=12)
    )
    return f"story_{token}.webp"


SHARE_SCRIPT_TEMPLATE = """(async () => {{
  const payload = {payload};
  if (navigator.share) {{
    try {{
      await navigator.share(payload);
      return "shared";
    }} catch (err) {{
      return "cancelled";
    }}
  }}
  const line = payload.text + " " + payload.url;
  try {{
    await navigator.clipboard.writeText(line);
    return "copied";
  }} catch (err) {{
    return "unavailable";
  }}
}})()"""

REVIEW_FIELD_KEYS: list[str] = [
    "category_one",
    "category_two",
    "category_three",
    "category_four",
]


def category_labels_for(direction: str) -> list[str]:
    """Both roles use the form's Timeliness, Work ethic, Skill, Friendliness order."""
    if direction == "poster_to_helper":
        return REVIEW_POSTER_CATEGORY_LABELS
    return REVIEW_HELPER_CATEGORY_LABELS


def category_pairs(direction: str, scores: list[int]) -> list[dict[str, str]]:
    return [
        {"label": label, "score": str(score)}
        for label, score in zip(category_labels_for(direction), scores)
    ]


REWARD_LABELS: dict[str, str] = {
    "lunch": "Lunch",
    "dinner": "Dinner",
    "accommodation": "Accommodation",
    "guided_tours": "Guided tours",
    "workshops": "Workshops",
    "lessons": "Lessons",
    "other": "Other",
}

DURATION_LABELS: dict[int, str] = HELP_DURATION_LABELS

DURATION_VALUES: list[str] = HELP_DURATION_VALUES


class ThreadItem(TypedDict):
    id: int
    post_id: int
    post_title: str
    category: str
    category_label: str
    reward_label: str
    reward_details: str
    location: str
    scheduled: str
    post_status: str
    application_status: str
    duration_label: str
    my_role: str
    role_label: str
    other_id: int
    other_name: str
    other_avatar_seed: str
    other_avatar: str
    other_handle: str
    other_rating: float
    other_rating_count: int
    message_count: int
    last_snippet: str
    last_at: str
    task_id: int
    poster_confirmed: bool
    helper_confirmed: bool
    reward_confirmed: bool
    completed_at: str
    story_note: str
    reward_given: str
    is_completed: bool
    i_confirmed: bool
    can_complete: bool
    my_review_done: bool
    other_verified: bool
    reviews_on_task: int
    perfect_reviews_on_task: int
    both_perfect: bool
    my_report_done: bool
    application_id: int
    poster_id: int
    helper_id: int
    first_sender_id: int
    is_direct_request: bool


EMPTY_THREAD: ThreadItem = {
    "id": 0,
    "post_id": 0,
    "post_title": "",
    "category": "",
    "category_label": "",
    "reward_label": "",
    "reward_details": "",
    "location": "",
    "scheduled": "",
    "post_status": "",
    "application_status": "none",
    "duration_label": "",
    "my_role": "helper",
    "role_label": "",
    "other_id": 0,
    "other_name": "",
    "other_avatar_seed": "",
    "other_avatar": "",
    "other_handle": "",
    "other_rating": 0.0,
    "other_rating_count": 0,
    "message_count": 0,
    "last_snippet": "",
    "last_at": "",
    "task_id": 0,
    "poster_confirmed": False,
    "helper_confirmed": False,
    "reward_confirmed": False,
    "completed_at": "",
    "story_note": "",
    "reward_given": "",
    "is_completed": False,
    "i_confirmed": False,
    "can_complete": False,
    "my_review_done": False,
    "other_verified": False,
    "reviews_on_task": 0,
    "perfect_reviews_on_task": 0,
    "both_perfect": False,
    "my_report_done": False,
    "application_id": 0,
    "poster_id": 0,
    "helper_id": 0,
    "first_sender_id": 0,
    "is_direct_request": False,
}


class StoryPhoto(TypedDict):
    id: int
    url_name: str
    uploader_name: str
    mine: bool
    created: str


class MessageItem(TypedDict):
    id: int
    sender_id: int
    sender_name: str
    sender_avatar_seed: str
    body: str
    photos: list[str]
    sent_at: str
    mine: bool


class ReviewItem(TypedDict):
    id: int
    reviewer_name: str
    reviewer_avatar_seed: str
    reviewer_avatar: str
    reviewee_name: str
    direction: str
    direction_label: str
    rating: int
    percent: int
    comment: str
    response: str
    can_respond: bool
    waiting: bool
    kindness_flag: bool
    created: str
    mine: bool
    categories: list[dict[str, str]]


class ReviewField(TypedDict):
    field: str
    label: str
    score: int


class ReportCategory(TypedDict):
    value: str
    label: str


class CheckInItem(TypedDict):
    id: int
    prompt: str
    note: str
    due_at: str
    status: str
    status_label: str
    creator_label: str
    mine: bool
    is_pending: bool
    is_completed: bool


# Practical presets: a check-in is always one short, answerable question.
CHECK_IN_PROMPTS: list[str] = [
    "Confirm you're on the way",
    "Share a progress update",
    "Confirm the task is finished",
    "Confirm the meeting point still works",
    "Let me know if anything is needed",
]


class MessagingState(rx.State):
    threads: list[ThreadItem] = []
    selected_thread: ThreadItem = EMPTY_THREAD
    messages: list[MessageItem] = []
    reviews: list[ReviewItem] = []

    review_target_open: bool = False
    review_targets: list[ThreadItem] = []
    dismissed_review_task_ids: list[int] = []
    review_navigation_pending: bool = False
    thread_filter: str = "all"
    review_scores: dict[str, int] = {
        "category_one": 0,
        "category_two": 0,
        "category_three": 0,
        "category_four": 0,
    }

    is_loading: bool = False
    is_loading_thread: bool = False
    is_sending: bool = False
    is_completing: bool = False
    is_reviewing: bool = False
    responding_id: int = 0
    response_error: str = ""
    response_error_id: int = 0
    error: str = ""
    success: str = ""

    # --- Completion success story (photos + share captions) ---------------
    completion_photos: list[StoryPhoto] = []
    share_caption: str = ""
    photo_busy: bool = False
    photo_error: str = ""
    photo_success: str = ""
    share_note: str = ""

    # --- Private bad-experience report ------------------------------------
    report_open: bool = False
    report_category: str = ""
    is_reporting: bool = False
    report_error: str = ""
    report_success: str = ""

    # --- Scheduled job check-ins ---
    check_ins: list[CheckInItem] = []
    check_in_prompt: str = ""
    check_in_busy: bool = False
    check_in_acting_id: int = 0
    check_in_error: str = ""
    check_in_success: str = ""
    check_in_prompt_options: list[str] = CHECK_IN_PROMPTS

    report_categories: list[ReportCategory] = [
        {
            "value": key,
            "label": SAFETY_REPORT_CATEGORY_LABELS.get(key, key.title()),
        }
        for key in SAFETY_REPORT_CATEGORIES
    ]

    rating_values: list[int] = [1, 2, 3, 4, 5]

    duration_options: list[dict[str, str]] = [
        {"value": "30", "label": "About 30 minutes"},
        {"value": "60", "label": "About an hour"},
        {"value": "120", "label": "Two hours"},
        {"value": "240", "label": "Half a day"},
        {"value": "480", "label": "A full day"},
    ]

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_thread["id"] > 0

    # ------------------------------------------------------------------
    # Direct requests a post owner sent straight to me
    # ------------------------------------------------------------------

    @rx.var
    def direct_help_requests(self) -> list[ThreadItem]:
        """Genuine pending requests a post owner sent directly to me."""
        return [
            t
            for t in self.threads
            if t["my_role"] == "helper" and t["is_direct_request"]
        ]

    @rx.var
    def direct_request_count(self) -> int:
        return len(self.direct_help_requests)

    @rx.var
    def can_review(self) -> bool:
        return (
            self.selected_thread["task_id"] > 0
            and self.selected_thread["i_confirmed"]
            and not self.selected_thread["my_review_done"]
        )

    @rx.var
    def review_direction(self) -> str:
        if self.selected_thread["my_role"] == "poster":
            return "poster_to_helper"
        return "helper_to_poster"

    @rx.var
    def review_title(self) -> str:
        return f"Review {self.selected_thread['other_name']}"

    @rx.var
    def review_fields(self) -> list[ReviewField]:
        labels = ["Timeliness", "Work ethic", "Skill", "Friendliness"]
        return [
            {
                "field": key,
                "label": label,
                "score": int(self.review_scores.get(key, 0)),
            }
            for key, label in zip(REVIEW_FIELD_KEYS, labels)
        ]

    @rx.var
    def review_ready(self) -> bool:
        return all(
            1 <= int(self.review_scores.get(key, 0)) <= 5
            for key in REVIEW_FIELD_KEYS
        )

    @rx.var
    def review_average_label(self) -> str:
        scores = [int(self.review_scores.get(k, 0)) for k in REVIEW_FIELD_KEYS]
        if not all(1 <= s <= 5 for s in scores):
            return "Score all four categories"
        return f"Overall {sum(scores) / 4:.1f} out of 5"

    # ------------------------------------------------------------------
    # Success story: only after a perfect reciprocal pair of reviews
    # ------------------------------------------------------------------

    @rx.var
    def can_share_success(self) -> bool:
        thread = self.selected_thread
        return (
            thread["task_id"] > 0
            and thread["is_completed"]
            and thread["reviews_on_task"] >= 2
            and thread["perfect_reviews_on_task"] >= 2
        )

    @rx.var
    def photo_slots_left(self) -> int:
        return max(
            0, COMPLETED_TASK_PHOTO_MAX_COUNT - len(self.completion_photos)
        )

    @rx.var
    def photo_slots_label(self) -> str:
        left = self.photo_slots_left
        if left == 0:
            return f"All {COMPLETED_TASK_PHOTO_MAX_COUNT} photo slots used"
        if left == 1:
            return "1 photo slot left"
        return f"{left} photo slots left"

    @rx.var
    def default_share_caption(self) -> str:
        thread = self.selected_thread
        title = thread["post_title"] or "a job on Go and Help"
        note = str(thread["story_note"] or "").strip()
        base = (
            f"Finished together: “{title}”. Five stars both ways on "
            "Go and Help."
        )
        if note:
            base = f"{base} {note}"
        return base[:400]

    @rx.var
    def share_text(self) -> str:
        typed = self.share_caption.strip()
        return (typed or self.default_share_caption)[:400]

    @rx.var
    def share_url(self) -> str:
        try:
            return public_base_url(str(self.router.url))
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Error: {e}")
            return ""

    @rx.var
    def share_links(self) -> dict[str, str]:
        body = self.share_text
        url = self.share_url
        subject = "A Go and Help success story"
        mail_body = quote(f"{body}\n\n{url}", safe="")
        mail_subject = quote(subject, safe="")
        enc_text = quote(body, safe="")
        enc_url = quote(url, safe="")
        combined = quote(f"{body} {url}".strip(), safe="")
        return {
            "telegram": (
                f"https://t.me/share/url?url={enc_url}&text={enc_text}"
            ),
            "whatsapp": f"https://wa.me/?text={combined}",
            "facebook": (
                "https://www.facebook.com/sharer/sharer.php"
                f"?u={enc_url}&quote={enc_text}"
            ),
            "x": (
                f"https://twitter.com/intent/tweet?text={enc_text}"
                f"&url={enc_url}"
            ),
            "pinterest": (
                "https://www.pinterest.com/pin/create/button/"
                f"?url={enc_url}&description={enc_text}"
            ),
            "email": f"mailto:?subject={mail_subject}&body={mail_body}",
            "instagram": "https://www.instagram.com/",
            "tiktok": "https://www.tiktok.com/",
        }

    @rx.var
    def can_report(self) -> bool:
        thread = self.selected_thread
        return (
            thread["task_id"] > 0
            and thread["is_completed"]
            and not thread["my_report_done"]
        )

    @rx.var
    def report_ready(self) -> bool:
        return self.report_category in SAFETY_REPORT_CATEGORIES

    @rx.var
    def thread_count_label(self) -> str:
        count = len(self.threads)
        if count == 1:
            return "1 conversation"
        return f"{count} conversations"

    @rx.var
    def awaiting_other_confirm(self) -> bool:
        thread = self.selected_thread
        return (
            thread["task_id"] > 0
            and thread["i_confirmed"]
            and not thread["is_completed"]
        )

    def _row_to_thread(self, row, sid: int) -> ThreadItem:
        poster_id = int(row[13])
        helper_id = int(row[16])
        my_role = "poster" if poster_id == sid else "helper"
        other_id = helper_id if my_role == "poster" else poster_id
        other_name = (
            str(row[17] or "") if my_role == "poster" else str(row[14] or "")
        )
        other_avatar_seed = (
            str(row[18] or "") if my_role == "poster" else str(row[15] or "")
        )
        category = str(row[5] or "")
        reward = str(row[6] or "")
        place = str(row[10] or "")
        city = str(row[9] or "")
        # Privacy: the typed address of an `approximate` request is never shown
        # in a thread. Only the exact accepted meeting place (already limited to
        # the poster and the accepted helper by the query) may replace it.
        job_location_mode = str(row[34] or "approximate")
        accepted_place = str(row[35] or "").strip()
        if job_location_mode == "place":
            where = ", ".join([p for p in [place, city] if p])
        elif accepted_place:
            where = ", ".join([p for p in [accepted_place, city] if p])
        else:
            where = city or "Approximate area"
        duration = int(row[12] or 60)
        application_status = str(row[19] or "none")
        task_id = int(row[20] or 0)
        poster_confirmed = bool(row[21])
        helper_confirmed = bool(row[22])
        is_completed = task_id > 0 and poster_confirmed and helper_confirmed
        i_confirmed = (
            poster_confirmed if my_role == "poster" else helper_confirmed
        )
        return {
            "id": int(row[0]),
            "post_id": int(row[1]),
            "post_title": str(row[4] or str(row[2] or "Help request")),
            "category": category,
            "category_label": CATEGORY_LABELS.get(
                category, category.replace("_", " ").title()
            ),
            "reward_label": REWARD_LABELS.get(
                reward, reward.replace("_", " ").title()
            ),
            "reward_details": str(row[7] or ""),
            "location": where,
            "scheduled": row[11].strftime("%b %d · %H:%M")
            if row[11] is not None
            else "Time to agree",
            "post_status": str(row[8] or "open"),
            "application_status": application_status,
            "duration_label": help_duration_label(duration),
            "my_role": my_role,
            "role_label": "You posted this job"
            if my_role == "poster"
            else "You accepted this job",
            "other_id": other_id,
            "other_name": other_name or "A Go and Help neighbour",
            "other_avatar_seed": other_avatar_seed,
            "other_avatar": str(row[38] or ""),
            "other_handle": f"@{row[39]}" if row[39] else "",
            "other_rating": float(row[40] or 0),
            "other_rating_count": int(row[41] or 0),
            "message_count": int(row[26] or 0),
            "last_snippet": message_preview(row[27])[:120],
            "last_at": row[3].strftime("%b %d · %H:%M")
            if row[3] is not None
            else "",
            "task_id": task_id,
            "poster_confirmed": poster_confirmed,
            "helper_confirmed": helper_confirmed,
            "reward_confirmed": bool(row[23]),
            "completed_at": row[24].strftime("%b %d, %Y")
            if row[24] is not None
            else "",
            "story_note": str(row[25] or ""),
            "reward_given": str(row[29] or ""),
            "is_completed": is_completed,
            "i_confirmed": i_confirmed,
            "can_complete": application_status == "accepted"
            and not is_completed,
            "my_review_done": int(row[28] or 0) > 0,
            "other_verified": bool(row[30]),
            "reviews_on_task": int(row[31] or 0),
            "perfect_reviews_on_task": int(row[32] or 0),
            "both_perfect": int(row[31] or 0) >= 2 and int(row[32] or 0) >= 2,
            "my_report_done": int(row[33] or 0) > 0,
            "application_id": int(row[36] or 0),
            "poster_id": poster_id,
            "helper_id": helper_id,
            "first_sender_id": int(row[37] or 0),
            # A direct helpee request: still pending, and the very first
            # message in the thread came from the post owner.
            "is_direct_request": application_status == "pending"
            and int(row[37] or 0) == poster_id,
        }

    @rx.event
    def set_review_score(self, field: str, value: int):
        if field in REVIEW_FIELD_KEYS and 0 <= value <= 5:
            self.review_scores[field] = value

    async def _localized_feedback_text(self, source: str) -> str:
        async with self:
            language = (await self.get_state(AuthState)).preferred_language
        return translate(language, source)

    def _reset_review_scores(self):
        self.review_scores = {key: 0 for key in REVIEW_FIELD_KEYS}

    def _reset_story_and_report(self):
        self.completion_photos = []
        self.share_caption = ""
        self.photo_error = ""
        self.photo_success = ""
        self.photo_busy = False
        self.share_note = ""
        self.report_open = False
        self.report_category = ""
        self.report_error = ""
        self.report_success = ""

    @rx.event
    def set_share_caption(self, value: str):
        self.share_caption = value[:400]
        self.share_note = ""

    @rx.event
    def toggle_report_form(self):
        self.report_open = not self.report_open
        self.report_error = ""
        self.report_success = ""

    @rx.event
    def set_report_category(self, value: str):
        self.report_category = value
        self.report_error = ""

    # ------------------------------------------------------------------
    # Scheduled job check-ins
    # ------------------------------------------------------------------

    @rx.var
    def can_manage_check_ins(self) -> bool:
        thread = self.selected_thread
        return (
            int(thread["id"]) > 0
            and str(thread["application_status"]) == "accepted"
            and not bool(thread["is_completed"])
        )

    @rx.var
    def check_in_ready(self) -> bool:
        return len(self.check_in_prompt.strip()) > 0

    @rx.var
    def pending_check_ins(self) -> list[CheckInItem]:
        return [item for item in self.check_ins if item["is_pending"]]

    @rx.var
    def closed_check_ins(self) -> list[CheckInItem]:
        return [item for item in self.check_ins if not item["is_pending"]]

    @rx.event
    def set_check_in_prompt(self, value: str):
        self.check_in_prompt = value[:CHECK_IN_PROMPT_MAX_LENGTH]
        self.check_in_error = ""

    def _reset_check_ins(self):
        self.check_ins = []
        self.check_in_prompt = ""
        self.check_in_busy = False
        self.check_in_acting_id = 0
        self.check_in_error = ""
        self.check_in_success = ""

    @rx.event(background=True)
    async def load_check_ins(self):
        """Retired: job coordination now happens through Inbox messages."""
        return
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            thread_id = int(self.selected_thread["id"])
        if not sid.isdigit() or thread_id <= 0:
            async with self:
                self.check_ins = []
            return
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, c.prompt, c.note, c.due_at, c.status,
                               c.creator_id, s.display_name
                        FROM skillkind_job_check_in c
                        JOIN skillkind_subscriber s ON s.id = c.creator_id
                        JOIN skillkind_message_thread t ON t.id = c.thread_id
                        WHERE c.thread_id = :tid
                          AND (t.poster_id = :sid OR t.helper_id = :sid)
                        ORDER BY c.due_at ASC, c.id ASC
                        LIMIT 50
                        """
                    ),
                    {"tid": thread_id, "sid": int(sid)},
                )
            ).all()
        status_labels = {
            CHECK_IN_STATUS_PENDING: "Upcoming",
            CHECK_IN_STATUS_COMPLETED: "Done",
            CHECK_IN_STATUS_CANCELLED: "Cancelled",
        }
        loaded: list[CheckInItem] = []
        for row in rows:
            status = str(row[4] or CHECK_IN_STATUS_PENDING)
            mine = int(row[5]) == int(sid)
            loaded.append(
                {
                    "id": int(row[0]),
                    "prompt": str(row[1] or ""),
                    "note": str(row[2] or ""),
                    "due_at": row[3].strftime("%b %d, %Y · %H:%M")
                    if row[3] is not None
                    else "",
                    "status": status,
                    "status_label": status_labels.get(status, status.title()),
                    "creator_label": "You asked"
                    if mine
                    else f"{str(row[6] or 'They')} asked",
                    "mine": mine,
                    "is_pending": status == CHECK_IN_STATUS_PENDING,
                    "is_completed": status == CHECK_IN_STATUS_COMPLETED,
                }
            )
        async with self:
            self.check_ins = loaded

    @rx.event(background=True)
    async def create_check_in(self, form_data: dict[str, Any]):
        """Retired: job coordination now happens through Inbox messages."""
        return
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            thread = self.selected_thread
            prompt = self.check_in_prompt.strip()
        due_raw = str(form_data.get("due_at", "") or "").strip()
        note = str(form_data.get("note", "") or "").strip()
        due: datetime.datetime | None = None
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif int(thread["id"]) <= 0:
            problem = "Open a job conversation first."
        elif str(thread["application_status"]) != "accepted":
            problem = "Check-ins open once a helper is accepted."
        elif bool(thread["is_completed"]):
            problem = "This job is already complete."
        elif not prompt:
            problem = "Choose what the check-in should ask."
        elif len(prompt) > CHECK_IN_PROMPT_MAX_LENGTH:
            problem = (
                f"Keep the check-in under {CHECK_IN_PROMPT_MAX_LENGTH} "
                "characters."
            )
        elif len(note) > CHECK_IN_NOTE_MAX_LENGTH:
            problem = (
                f"Keep the note under {CHECK_IN_NOTE_MAX_LENGTH} characters."
            )
        elif not due_raw:
            problem = "Pick the date and time for this check-in."
        if not problem:
            try:
                due = datetime.datetime.fromisoformat(due_raw)
            except ValueError:
                problem = "That date and time couldn't be read."
        if not problem and due is not None:
            if due.tzinfo is None:
                due = due.replace(tzinfo=datetime.UTC)
            if due <= datetime.datetime.now(datetime.UTC):
                problem = "Choose a moment in the future."
        if problem:
            async with self:
                self.check_in_error = problem
                self.check_in_success = ""
            return
        async with self:
            self.check_in_busy = True
            self.check_in_error = ""
            self.check_in_success = ""
        thread_id = int(thread["id"])
        other_id = int(thread["other_id"])
        post_id = int(thread["post_id"])
        async with rx.asession() as asession:
            # Participation, acceptance, live job and block state are all
            # re-checked inside the same statement that inserts the row.
            created = (
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_job_check_in
                            (thread_id, creator_id, due_at, prompt, note,
                             status)
                        SELECT t.id, :sid, :due, :prompt, :note, 'pending'
                        FROM skillkind_message_thread t
                        JOIN skillkind_help_post p ON p.id = t.post_id
                        JOIN skillkind_job_application a
                              ON a.post_id = t.post_id
                             AND a.helper_id = t.helper_id
                        WHERE t.id = :tid
                          AND (t.poster_id = :sid OR t.helper_id = :sid)
                          AND a.status = 'accepted'
                          AND p.status NOT IN ('completed', 'cancelled',
                                               'deleted')
                          AND :due > now()
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = t.poster_id
                                     AND mb.blocked_id = t.helper_id)
                                 OR (mb.blocker_id = t.helper_id
                                     AND mb.blocked_id = t.poster_id)
                          )
                        ON CONFLICT ON CONSTRAINT
                            uq_job_check_in_thread_due_prompt
                        DO NOTHING
                        RETURNING id
                        """
                    ),
                    {
                        "tid": thread_id,
                        "sid": int(sid),
                        "due": due,
                        "prompt": prompt,
                        "note": note,
                    },
                )
            ).first()
            if created is None:
                await asession.rollback()
                async with self:
                    self.check_in_busy = False
                    self.check_in_error = (
                        "We couldn't add that check-in — it may already "
                        "exist, or this job is no longer active."
                    )
                return
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         help_post_id, target_route)
                    VALUES (:other, 'inbox_message', :title, :body, :sid,
                            :pid, 'inbox')
                    """
                ),
                {
                    "other": other_id,
                    "sid": int(sid),
                    "pid": post_id,
                    "title": "New check-in on a job",
                    "body": prompt[:255],
                },
            )
            await asession.commit()
        async with self:
            self.check_in_busy = False
            self.check_in_prompt = ""
            self.check_in_success = "Check-in scheduled."
        from app.states.notification_state import NotificationState
        from app.states.unified_inbox_state import UnifiedInboxState

        yield UnifiedInboxState.load_index
        yield NotificationState.load_notifications

    async def _close_check_in(
        self, check_in_id: int, status: str, is_completed: bool = False
    ) -> tuple[bool, str]:
        """Complete or cancel one pending check-in on the open thread."""
        sid = (await self.get_state(AuthState)).subscriber_id
        thread_id = int(self.selected_thread["id"])
        if not sid.isdigit() or thread_id <= 0 or check_in_id <= 0:
            return False, "Open a job conversation first."
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_job_check_in c
                        SET status = CAST(:status AS varchar),
                            completed_at = CASE WHEN CAST(:done AS boolean)
                                                THEN now() ELSE NULL END,
                            updated_at = now()
                        WHERE c.id = :cid
                          AND c.thread_id = :tid
                          AND c.status = 'pending'
                          AND EXISTS (
                              SELECT 1 FROM skillkind_message_thread t
                              WHERE t.id = c.thread_id
                                AND (t.poster_id = :sid OR t.helper_id = :sid)
                          )
                        RETURNING c.prompt
                        """
                    ),
                    {
                        "cid": int(check_in_id),
                        "tid": thread_id,
                        "sid": int(sid),
                        "status": status,
                        "done": bool(is_completed),
                    },
                )
            ).first()
            if row is None:
                await asession.rollback()
                return False, "That check-in is no longer pending."
            if status == CHECK_IN_STATUS_COMPLETED:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_member_notification
                            (recipient_id, kind, title, body, actor_id,
                             help_post_id, target_route)
                        VALUES (:other, 'inbox_message', :title, :body, :sid,
                                :pid, 'inbox')
                        """
                    ),
                    {
                        "other": int(self.selected_thread["other_id"]),
                        "sid": int(sid),
                        "pid": int(self.selected_thread["post_id"]),
                        "title": "A job check-in was completed",
                        "body": str(row[0] or "")[:255],
                    },
                )
            await asession.commit()
        return True, ""

    @rx.event
    async def complete_check_in(self, check_in_id: int):
        return
        self.check_in_acting_id = int(check_in_id)
        ok, problem = await self._close_check_in(
            int(check_in_id),
            CHECK_IN_STATUS_COMPLETED,
            is_completed=True,
        )
        self.check_in_acting_id = 0
        self.check_in_error = problem
        self.check_in_success = "Check-in marked done." if ok else ""
        if not ok:
            return
        from app.states.notification_state import NotificationState
        from app.states.unified_inbox_state import UnifiedInboxState

        return [
            MessagingState.load_check_ins,
            UnifiedInboxState.load_index,
            NotificationState.load_notifications,
        ]

    @rx.event
    async def cancel_check_in(self, check_in_id: int):
        return
        self.check_in_acting_id = int(check_in_id)
        ok, problem = await self._close_check_in(
            int(check_in_id),
            CHECK_IN_STATUS_CANCELLED,
            is_completed=CHECK_IN_STATUS_CANCELLED == CHECK_IN_STATUS_COMPLETED,
        )
        self.check_in_acting_id = 0
        self.check_in_error = problem
        self.check_in_success = "Check-in cancelled." if ok else ""
        if ok:
            return MessagingState.load_check_ins

    def _apply_threads(self, loaded: list[ThreadItem], selected_id: int):
        self.threads = [
            t
            for t in loaded
            if self.thread_filter == "all"
            or (self.thread_filter == "active" and t["task_id"] == 0)
            or (self.thread_filter == "completed" and t["task_id"] > 0)
        ]
        self.review_targets = [
            t
            for t in loaded
            if t["task_id"] > 0
            and t["i_confirmed"]
            and not t["my_review_done"]
            and t["task_id"] not in self.dismissed_review_task_ids
        ]
        self.selected_thread = next(
            (t for t in loaded if t["id"] == selected_id), dict(EMPTY_THREAD)
        )
        if not self.selected_thread["id"]:
            self.messages = []
            self.reviews = []
            self.review_target_open = False

    @rx.event
    def load_review_targets(self):
        if not self.review_navigation_pending:
            self.review_target_open = False
        self.review_navigation_pending = False
        return MessagingState.load_threads

    @rx.event
    def select_review_target(self, task_id: int):
        if self.is_reviewing:
            return
        target = next(
            (t for t in self.review_targets if t["task_id"] == task_id), None
        )
        if target is None:
            return
        self.selected_thread = target
        self.review_target_open = True
        self.error = ""
        self._reset_review_scores()
        return MessagingState.load_conversation

    @rx.event
    def dismiss_review_target(self, task_id: int):
        if self.is_reviewing:
            return
        if not any(t["task_id"] == task_id for t in self.review_targets):
            return
        self.dismissed_review_task_ids = [
            *self.dismissed_review_task_ids,
            task_id,
        ]
        self.review_targets = [
            t for t in self.review_targets if t["task_id"] != task_id
        ]
        if self.selected_thread["task_id"] == task_id:
            self.review_target_open = False
            self._reset_review_scores()
        self.error = ""

    @rx.event
    def close_review_target(self):
        self.review_target_open = False

    @rx.event
    async def open_review_target(self):
        if not self.can_review:
            return
        from app.states.profile_state import ProfileState
        from app.states.community_state import CommunityState

        profile = await self.get_state(ProfileState)
        community = await self.get_state(CommunityState)
        profile.active_tab = "community"
        community.section = "reviews"
        community.error = ""
        self.review_target_open = True
        self.review_navigation_pending = True
        task_id = self.selected_thread["task_id"]
        self.dismissed_review_task_ids = [
            i for i in self.dismissed_review_task_ids if i != task_id
        ]
        if not any(t["task_id"] == task_id for t in self.review_targets):
            self.review_targets = [
                *self.review_targets,
                dict(self.selected_thread),
            ]

    @rx.event
    def confirm_job_done(self):
        return MessagingState.mark_complete(
            {"actual_minutes": "60", "reward_given": "", "story_note": ""}
        )

    @rx.event
    async def clear_selection(self):
        from app.states.unified_inbox_state import UnifiedInboxState

        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        (await self.get_state(UnifiedInboxState)).selected_key = ""
        self.review_target_open = False
        self.selected_thread = EMPTY_THREAD
        self.messages = []
        self.reviews = []
        self._reset_review_scores()
        self._reset_story_and_report()
        self._reset_check_ins()

    # Set by another screen (a job offer or a direct help request) so the next
    # thread load opens exactly that conversation.
    pending_thread_id: int = 0
    composer_generation: int = 0

    @rx.event
    async def focus_thread(self, thread_id: int):
        """Open the Inbox with exactly one job conversation revealed."""
        from app.states.contacts_state import EMPTY_CONTACT, ContactsState
        from app.states.noncontact_state import (
            EMPTY_CONVERSATION,
            NonContactMessagingState,
        )
        from app.states.profile_state import ProfileState
        from app.states.unified_inbox_state import UnifiedInboxState

        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        self.pending_thread_id = int(thread_id)
        self.composer_generation += 1
        self.error = ""
        self.success = ""
        profile = await self.get_state(ProfileState)
        unified = await self.get_state(UnifiedInboxState)
        unified.preserve_next_mount = profile.active_tab != "inbox"
        unified.view = "thread"
        profile.active_tab = "inbox"
        contacts = await self.get_state(ContactsState)
        contacts.selected_contact = EMPTY_CONTACT
        contacts.contact_messages = []
        noncontact = await self.get_state(NonContactMessagingState)
        noncontact.selected = EMPTY_CONVERSATION
        noncontact.messages = []
        unified = await self.get_state(UnifiedInboxState)
        unified.selected_key = f"job:{int(thread_id)}"
        return MessagingState.load_threads

    @rx.event
    def select_thread(self, thread_id: int):
        self.review_target_open = False
        self.error
        self.success = ""
        self._reset_review_scores()
        self._reset_story_and_report()
        self.reviews = []
        self.response_error = ""
        for thread in self.threads:
            if thread["id"] == thread_id:
                self.selected_thread = thread
                return MessagingState.load_conversation
        self.pending_thread_id = int(thread_id)
        return MessagingState.load_threads

    # ------------------------------------------------------------------
    # Direct helpee requests
    # Direct helpee requests: accept / decline, server-authoritative
    # ------------------------------------------------------------------

    deciding_request_id: int = 0

    @staticmethod
    async def _direct_request_row(asession, application_id: int, sid: int):
        """Locked lookup proving this is a genuine direct request to me.

        The application must be mine and still pending, the post still open,
        and the earliest message in the (post, helper) thread must have been
        sent by the post owner. An ordinary helper-originated offer starts
        with a message from the helper, so it never qualifies here.
        The application and post rows are locked for the transaction so two
        helpers cannot concurrently become accepted.
        """
        await asession.execute(
            text("""
            SELECT p.id FROM skillkind_help_post p
            WHERE p.id = (SELECT post_id FROM skillkind_job_application WHERE id = :aid)
            FOR UPDATE
        """),
            {"aid": int(application_id)},
        )
        return (
            await asession.execute(
                text(
                    """
                    SELECT a.id, a.post_id, p.author_id, p.title
                    FROM skillkind_job_application a
                    JOIN skillkind_help_post p ON p.id = a.post_id
                    WHERE a.id = :aid
                      AND a.helper_id = :sid
                      AND a.status = 'pending'
                      AND p.status = 'open'
                      AND NOT EXISTS (
                          SELECT 1 FROM skillkind_member_block mb
                          WHERE (mb.blocker_id = p.author_id
                                 AND mb.blocked_id = a.helper_id)
                             OR (mb.blocker_id = a.helper_id
                                 AND mb.blocked_id = p.author_id)
                      )
                      AND EXISTS (
                          SELECT 1
                          FROM skillkind_message_thread t
                          WHERE t.post_id = a.post_id
                            AND t.helper_id = a.helper_id
                            AND (SELECT m.sender_id
                                   FROM skillkind_message m
                                  WHERE m.thread_id = t.id
                                  ORDER BY m.sent_at ASC, m.id ASC
                                  LIMIT 1) = p.author_id
                      )
                    FOR UPDATE OF a, p
                    """
                ),
                {"aid": int(application_id), "sid": int(sid)},
            )
        ).first()

    @rx.event(background=True)
    async def accept_direct_request(self, application_id: int):
        """Accept a direct request: match the post and confirm me as helper."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        stale = STALE_REQUEST_ERROR
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.deciding_request_id = int(application_id)
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            row = await self._direct_request_row(
                asession, int(application_id), int(sid)
            )
            if row is None:
                await asession.rollback()
                async with self:
                    self.deciding_request_id = 0
                    self.error = stale
                yield MessagingState.load_threads
                return
            post_id = int(row[1])
            poster_id = int(row[2])
            title = str(row[3] or "a help request")
            # With the rows locked, no rival can slip in between this check
            # and the accepting update below.
            rival = (
                await asession.execute(
                    text(
                        """
                        SELECT 1 FROM skillkind_help_post p
                        WHERE p.id = :pid AND
                          (SELECT COUNT(*) FROM skillkind_job_application other
                           WHERE other.post_id = p.id AND other.status = 'accepted')
                          >= GREATEST(COALESCE(p.helpers_needed, 1), 1)
                        """
                    ),
                    {"pid": post_id, "aid": int(application_id)},
                )
            ).first()
            if rival is not None:
                await asession.rollback()
                async with self:
                    self.deciding_request_id = 0
                    self.error = stale
                yield MessagingState.load_threads
                return
            claimed = await asession.execute(
                text(
                    """
                    UPDATE skillkind_job_application
                    SET status = 'accepted', responded_at = now()
                    WHERE id = :aid AND helper_id = :sid
                      AND status = 'pending'
                    """
                ),
                {"aid": int(application_id), "sid": int(sid)},
            )
            if int(claimed.rowcount or 0) != 1:
                await asession.rollback()
                async with self:
                    self.deciding_request_id = 0
                    self.error = stale
                yield MessagingState.load_threads
                return
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_job_application
                    SET status = 'declined', responded_at = now()
                    WHERE post_id = :pid AND id <> :aid
                      AND status = 'pending'
                      AND (SELECT COUNT(*) FROM skillkind_job_application a
                           WHERE a.post_id = :pid AND a.status = 'accepted') >=
                          (SELECT GREATEST(COALESCE(helpers_needed, 1), 1)
                           FROM skillkind_help_post WHERE id = :pid)
                    """
                ),
                {"pid": post_id, "aid": int(application_id)},
            )
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_help_post
                    SET status = CASE WHEN
                        (SELECT COUNT(*) FROM skillkind_job_application a
                         WHERE a.post_id = :pid AND a.status = 'accepted') >=
                        GREATEST(COALESCE(helpers_needed, 1), 1)
                        THEN 'matched' ELSE 'open' END, updated_at = now()
                    WHERE id = :pid
                    """
                ),
                {"pid": post_id},
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         help_post_id, target_route)
                    VALUES (:sid, 'help_confirmed', :title, :body,
                            :poster, :pid, '')
                    """
                ),
                {
                    "sid": int(sid),
                    "poster": poster_id,
                    "pid": post_id,
                    "title": f"You're confirmed to help: {title}"[:200],
                    "body": (
                        f"You accepted the direct request to help with "
                        f"“{title}”. Open Help to see the day, place and hours."
                    )[:255],
                },
            )
            await self._ensure_job_thread(
                asession, post_id, poster_id, int(sid), title
            )
            await asession.commit()
        async with self:
            self.deciding_request_id = 0
            self.success = f"Accepted — you're helping with “{title}”."
        yield rx.toast(
            await self._localized_feedback_text(
                "Request accepted. Job confirmed."
            ),
            duration=4000,
        )
        yield MessagingState.load_threads
        from app.states.help_hub_state import HelpHubState

        yield HelpHubState.load_help_hub
        from app.states.notification_state import NotificationState

        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def decline_direct_request(self, application_id: int):
        """Decline only my own pending, genuinely direct, request."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        stale = STALE_REQUEST_ERROR
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.deciding_request_id = int(application_id)
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            row = await self._direct_request_row(
                asession, int(application_id), int(sid)
            )
            if row is None:
                await asession.rollback()
                async with self:
                    self.deciding_request_id = 0
                    self.error = stale
                yield MessagingState.load_threads
                return
            declined = await asession.execute(
                text(
                    """
                    UPDATE skillkind_job_application
                    SET status = 'declined', responded_at = now()
                    WHERE id = :aid AND helper_id = :sid
                      AND status = 'pending'
                    """
                ),
                {"aid": int(application_id), "sid": int(sid)},
            )
            if int(declined.rowcount or 0) != 1:
                await asession.rollback()
                async with self:
                    self.deciding_request_id = 0
                    self.error = stale
                yield MessagingState.load_threads
                return
            await asession.commit()
        async with self:
            self.deciding_request_id = 0
            self.success = "Request declined — the conversation stays open."
        yield rx.toast(
            await self._localized_feedback_text("Request declined."),
            duration=3000,
        )
        yield MessagingState.load_threads

    async def _ensure_job_thread(
        self,
        asession,
        post_id: int,
        poster_id: int,
        helper_id: int,
        subject: str,
    ) -> int:
        """Reuse the (post, helper) thread, creating or reopening as needed."""
        existing = (
            await asession.execute(
                text(
                    """
                    SELECT id FROM skillkind_message_thread
                    WHERE post_id = :pid AND helper_id = :hid
                    """
                ),
                {"pid": post_id, "hid": helper_id},
            )
        ).first()
        if existing is not None:
            thread_id = int(existing[0])
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_message_thread
                    SET is_archived = FALSE, last_message_at = now()
                    WHERE id = :tid
                    """
                ),
                {"tid": thread_id},
            )
            return thread_id
        try:
            created = (
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_message_thread
                            (post_id, poster_id, helper_id, subject,
                             is_archived, last_message_at)
                        VALUES (:pid, :poster, :hid, :subject, FALSE, now())
                        RETURNING id
                        """
                    ),
                    {
                        "pid": post_id,
                        "poster": poster_id,
                        "hid": helper_id,
                        "subject": subject[:200],
                    },
                )
            ).first()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Error: {e}")
            return 0
        return int(created[0]) if created is not None else 0

    @rx.event(background=True)
    async def load_threads(self):
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            selected_id = self.pending_thread_id or self.selected_thread["id"]
            self.pending_thread_id = 0
            if not sid.isdigit():
                self.threads = []
                self.review_targets = []
                self.selected_thread = EMPTY_THREAD
                self.messages = []
                self.reviews = []
                self.is_loading = False
                return
            self.is_loading = True
            self.error = ""
        try:
            match = await self._load_threads_data(sid, selected_id)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                self.error = "We couldn't load your Inbox just now. Please use Refresh to try again."
            return
        from app.states.unified_inbox_state import UnifiedInboxState

        yield UnifiedInboxState.load_index
        if match:
            yield MessagingState.load_conversation

    async def _load_threads_data(self, sid: str, selected_id: int) -> bool:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT t.id, t.post_id, t.subject,
                               COALESCE(t.last_message_at, t.created_at),
                               p.title, p.category, p.reward_type,
                               p.reward_details, p.status, p.city,
                               p.location_name, p.scheduled_for,
                               p.duration_minutes,
                               t.poster_id, ps.display_name, CONCAT('member-', ps.id),
                               t.helper_id, hs.display_name, CONCAT('member-', hs.id),
                               COALESCE(a.status, 'none'),
                               COALESCE(ct.id, 0),
                               COALESCE(ct.poster_confirmed, FALSE),
                               COALESCE(ct.helper_confirmed, FALSE),
                               COALESCE(ct.reward_confirmed, FALSE),
                               ct.completed_at,
                               COALESCE(ct.story_note, ''),
                               (SELECT COUNT(*) FROM skillkind_message m
                                 WHERE m.thread_id = t.id),
                               (SELECT m2.body FROM skillkind_message m2
                                 WHERE m2.thread_id = t.id
                                 ORDER BY m2.sent_at DESC LIMIT 1),
                               (SELECT COUNT(*) FROM skillkind_review r
                                 WHERE r.completed_task_id = ct.id
                                   AND r.reviewer_id = :sid),
                               COALESCE(ct.reward_given, ''),
                               CASE WHEN t.poster_id = :sid
                                    THEN hs.is_verified ELSE ps.is_verified END,
                               (SELECT COUNT(*) FROM skillkind_review r2
                                 WHERE r2.completed_task_id = ct.id
                                   AND (r2.reviewer_id = :sid OR {review_released_sql("r2")})), 
                               (SELECT COUNT(*) FROM skillkind_review r3
                                 WHERE r3.completed_task_id = ct.id
                                   AND r3.rating = 5
                                   AND (r3.reviewer_id = :sid OR {review_released_sql("r3")})),
                               (SELECT COUNT(*) FROM skillkind_safety_report sr
                                 WHERE sr.completed_task_id = ct.id
                                   AND sr.reporter_id = :sid),
                               COALESCE(p.location_mode, 'approximate'),
                               CASE WHEN COALESCE(a.status, 'none') = 'accepted'
                                    THEN COALESCE(p.accepted_location_name, '')
                                    ELSE '' END,
                               COALESCE(a.id, 0),
                               COALESCE((SELECT m4.sender_id
                                           FROM skillkind_message m4
                                          WHERE m4.thread_id = t.id
                                          ORDER BY m4.sent_at ASC, m4.id ASC
                                          LIMIT 1), 0),
                               COALESCE(op.avatar_path, ''),
                               COALESCE(op.username, ''),
                               COALESCE(ratings.average, 0),
                               COALESCE(ratings.total, 0)
                        FROM skillkind_message_thread t
                        JOIN skillkind_help_post p ON p.id = t.post_id
                        JOIN skillkind_subscriber ps ON ps.id = t.poster_id
                        JOIN skillkind_subscriber hs ON hs.id = t.helper_id
                        LEFT JOIN skillkind_profile op ON op.subscriber_id =
                            CASE WHEN t.poster_id = :sid THEN t.helper_id ELSE t.poster_id END
                        LEFT JOIN LATERAL (
                            SELECT AVG(r.rating) AS average, COUNT(*) AS total
                            FROM skillkind_review r
                            WHERE r.reviewee_id = op.subscriber_id
                              AND r.direction = CASE WHEN t.poster_id = :sid
                                  THEN 'poster_to_helper' ELSE 'helper_to_poster' END
                              AND {review_released_sql()}
                        ) ratings ON TRUE
                        LEFT JOIN skillkind_job_application a
                               ON a.post_id = t.post_id
                              AND a.helper_id = t.helper_id
                        LEFT JOIN skillkind_completed_task ct
                               ON ct.post_id = t.post_id
                              AND ct.helper_id = t.helper_id
                              AND ct.poster_id = t.poster_id
                        WHERE (t.poster_id = :sid OR t.helper_id = :sid)
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = t.poster_id
                                     AND mb.blocked_id = t.helper_id)
                                 OR (mb.blocker_id = t.helper_id
                                     AND mb.blocked_id = t.poster_id)
                          )
                        ORDER BY COALESCE(t.last_message_at, t.created_at) DESC
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()

        loaded = [self._row_to_thread(r, int(sid)) for r in rows]
        async with self:
            if (await self.get_state(AuthState)).subscriber_id != sid:
                self.is_loading = False
                return False
            self._apply_threads(
                loaded, self.selected_thread["id"] or selected_id
            )
            match = self.has_selection
            self.is_loading = False
        return match

    @rx.event(background=True)
    async def load_conversation(self):
        async with self:
            if self.is_loading_thread:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            thread = self.selected_thread.copy()
            if not sid.isdigit() or thread["id"] <= 0:
                self.messages = []
                self.reviews = []
                self.is_loading_thread = False
                return
            self.is_loading_thread = True
            self.error = ""

        try:
            outcome = await self._load_conversation_data(sid, thread)
            async with self:
                self.is_loading_thread = False
                if (
                    self.selected_thread["id"] != thread["id"]
                    or (await self.get_state(AuthState)).subscriber_id != sid
                ):
                    return
                if outcome == "unauthorized":
                    self.messages = []
                    self.reviews = []
                    self.selected_thread = EMPTY_THREAD
                    return
            if outcome != "ok":
                return
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading_thread = False
                if (
                    self.selected_thread["id"] == thread["id"]
                    and (await self.get_state(AuthState)).subscriber_id == sid
                ):
                    self.error = (
                        "We couldn't load this conversation. Please try again."
                    )
            return

        from app.states.notification_state import NotificationState
        from app.states.unified_inbox_state import UnifiedInboxState

        yield UnifiedInboxState.mark_opened(f"job:{thread['id']}", sid)
        yield NotificationState.load_notifications
        yield MessagingState.load_completion_photos
        yield MessagingState.load_check_ins

    async def _load_conversation_data(
        self, sid: str, thread: ThreadItem
    ) -> str:
        thread_id = int(thread["id"])
        task_id = int(thread["task_id"])
        async with rx.asession() as asession:
            # A blocked poster/helper pair never loads its job conversation.
            allowed = (
                await asession.execute(
                    text(
                        """
                        SELECT 1 FROM skillkind_message_thread t
                        WHERE t.id = :tid
                          AND (t.poster_id = :sid OR t.helper_id = :sid)
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = t.poster_id
                                     AND mb.blocked_id = t.helper_id)
                                 OR (mb.blocker_id = t.helper_id
                                     AND mb.blocked_id = t.poster_id)
                          )
                        """
                    ),
                    {"tid": thread_id, "sid": int(sid)},
                )
            ).first()
            if allowed is None:
                return "unauthorized"
            message_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT m.id, m.sender_id, s.display_name, CONCAT('member-', s.id),
                               m.body, m.sent_at
                        FROM skillkind_message m
                        JOIN skillkind_subscriber s ON s.id = m.sender_id
                        WHERE m.thread_id = :tid
                        ORDER BY m.sent_at ASC, m.id ASC
                        LIMIT 200
                        """
                    ),
                    {"tid": thread_id},
                )
            ).all()
            review_rows = []
            if task_id > 0:
                review_rows = (
                    await asession.execute(
                        text(
                            f"""
                            SELECT r.id, rv.display_name, CONCAT('member-', rv.id),
                                   re.display_name, r.direction, r.rating,
                                   r.comment, r.kindness_flag, r.created_at,
                                   r.reviewer_id,
                                   COALESCE(r.category_one, 0),
                                   COALESCE(r.category_two, 0),
                                   COALESCE(r.category_three, 0),
                                   COALESCE(r.category_four, 0),
                                   r.reviewee_id, {review_released_sql()} AS released,
                                   COALESCE(rv_profile.avatar_path, '')
                            FROM skillkind_review r
                            JOIN skillkind_subscriber rv ON rv.id = r.reviewer_id
                            LEFT JOIN skillkind_profile rv_profile ON rv_profile.subscriber_id = rv.id
                            JOIN skillkind_subscriber re ON re.id = r.reviewee_id
                            WHERE r.completed_task_id = :ctid
                              AND (r.reviewer_id = :sid OR {review_released_sql()})
                              AND EXISTS (
                                  SELECT 1 FROM skillkind_completed_task ct
                                  JOIN skillkind_message_thread t ON t.post_id = ct.post_id
                                    AND t.poster_id = ct.poster_id AND t.helper_id = ct.helper_id
                                  WHERE ct.id = r.completed_task_id AND t.id = :tid
                                    AND :sid IN (ct.poster_id, ct.helper_id)
                              )
                            ORDER BY r.created_at ASC
                            LIMIT 2
                            """
                        ),
                        {"ctid": task_id, "sid": int(sid), "tid": thread_id},
                    )
                ).all()
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_message
                    SET read_at = now()
                    WHERE thread_id = :tid
                      AND sender_id <> :sid
                      AND read_at IS NULL
                    """
                ),
                {"tid": thread_id, "sid": int(sid)},
            )
            # Clear only the inbox notices for this one job conversation.
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_member_notification
                    SET is_read = true, read_at = now()
                    WHERE recipient_id = :sid
                      AND kind = 'inbox_message'
                      AND help_post_id = :pid
                      AND is_read = false
                    """
                ),
                {"sid": int(sid), "pid": int(thread["post_id"])},
            )
            await asession.commit()

        loaded_messages: list[MessageItem] = [
            {
                "id": int(r[0]),
                "sender_id": int(r[1]),
                "sender_name": str(r[2] or ""),
                "sender_avatar_seed": str(r[3] or ""),
                **decode_message(r[4]),
                "sent_at": r[5].strftime("%b %d · %H:%M")
                if r[5] is not None
                else "",
                "mine": int(r[1]) == int(sid),
            }
            for r in message_rows
        ]
        loaded_reviews: list[ReviewItem] = [
            {
                "id": int(r[0]),
                "reviewer_name": str(r[1] or ""),
                "reviewer_avatar_seed": str(r[2] or ""),
                "reviewer_avatar": str(r[16] or "") if len(r) > 16 else "",
                "reviewee_name": str(r[3] or ""),
                "direction": str(r[4] or ""),
                "direction_label": "Give Help score"
                if str(r[4]) == "poster_to_helper"
                else "Get Help score",
                "rating": int(r[5] or 0),
                "percent": max(0, min(100, round(int(r[5] or 0) / 5 * 100))),
                "comment": decode_review_content(r[6])[0],
                "response": decode_review_content(r[6])[1],
                "can_respond": int(r[14]) == int(sid)
                and bool(r[15])
                and not decode_review_content(r[6])[1],
                "waiting": not bool(r[15]),
                "kindness_flag": bool(r[7]),
                "created": r[8].strftime("%b %d, %Y")
                if r[8] is not None
                else "",
                "mine": int(r[9]) == int(sid),
                "categories": category_pairs(
                    str(r[4] or ""),
                    [
                        int(r[10] or 0),
                        int(r[11] or 0),
                        int(r[12] or 0),
                        int(r[13] or 0),
                    ],
                ),
            }
            for r in review_rows
        ]
        async with self:
            if (
                self.selected_thread["id"] != thread_id
                or (await self.get_state(AuthState)).subscriber_id != sid
            ):
                return "stale"
            self.messages = loaded_messages
            self.reviews = loaded_reviews
        return "ok"

    @rx.event(background=True)
    async def load_completion_photos(self):
        """Read the success-story gallery for the open completed job."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            task_id = int(self.selected_thread["task_id"])
        if not sid.isdigit() or task_id <= 0:
            async with self:
                self.completion_photos = []
            return
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT ph.id, ph.path, s.display_name,
                               ph.uploader_id, ph.created_at
                        FROM skillkind_completed_task_photo ph
                        JOIN skillkind_subscriber s ON s.id = ph.uploader_id
                        WHERE ph.completed_task_id = :ctid
                        ORDER BY ph.display_order ASC, ph.id ASC
                        LIMIT 5
                        """
                    ),
                    {"ctid": task_id},
                )
            ).all()
        loaded: list[StoryPhoto] = [
            {
                "id": int(r[0]),
                "url_name": str(r[1] or ""),
                "uploader_name": str(r[2] or "A Go and Help neighbour"),
                "mine": int(r[3]) == int(sid),
                "created": r[4].strftime("%b %d, %Y")
                if r[4] is not None
                else "",
            }
            for r in rows
        ]
        async with self:
            self.completion_photos = loaded

    @rx.event
    async def send_message(self, form_data: dict[str, Any]):
        from app.states.message_attachment_state import MessageAttachmentState
        from app.states.unified_inbox_state import UnifiedInboxState

        if self.is_sending:
            return
        attachments = await self.get_state(MessageAttachmentState)
        body = str(form_data.get("body", "") or "").strip()
        sid = (await self.get_state(AuthState)).subscriber_id
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif self.selected_thread["id"] <= 0:
            problem = "Open a conversation first."
        elif not body and not attachments.pending:
            problem = "Write something before sending."
        elif len(body) > 2000:
            problem = "Keep messages under 2000 characters."
        if problem:
            self.error = problem
            self.success = ""
            return
        self.is_sending = True
        self.error = ""
        self.success = ""
        try:
            await attachments._persist(
                "job",
                self.selected_thread["id"],
                body,
                expected_key=str(form_data.get("conversation_key", "")),
            )
            self.composer_generation += 1
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "We couldn't send your message. Please try again."
            )
            return
        finally:
            self.is_sending = False
        yield MessagingState.load_conversation
        yield MessagingState.load_threads
        yield UnifiedInboxState.load_index

    @rx.event(background=True)
    async def mark_complete(self, form_data: dict[str, Any]):
        async with self:
            if self.is_completing:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            thread = dict(self.selected_thread)
        reward_given = str(form_data.get("reward_given", "") or "").strip()
        story_note = str(form_data.get("story_note", "") or "").strip()
        minutes_raw = str(form_data.get("actual_minutes", "60") or "60").strip()
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif thread["id"] <= 0:
            problem = "Open a conversation first."
        elif thread["application_status"] != "accepted":
            problem = "Only accepted jobs can be marked complete."
        elif thread["is_completed"]:
            problem = "This job is already fully confirmed."
        elif minutes_raw not in DURATION_VALUES:
            problem = "Choose how long the task actually took."
        elif len(story_note) > 2000:
            problem = "Keep the story note under 2000 characters."
        elif len(reward_given) > 255:
            problem = "Keep the reward under 255 characters."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_completing = True
            self.error = ""
            self.success = ""

        post_id = int(thread["post_id"])
        role = thread["my_role"]
        poster_id = int(sid) if role == "poster" else int(thread["other_id"])
        helper_id = int(sid) if role == "helper" else int(thread["other_id"])
        minutes = int(minutes_raw)
        finalized = False
        removed_paths: list[str] = []

        async with rx.asession() as asession:
            authorized = (
                await asession.execute(
                    text("""
                SELECT t.poster_id, t.helper_id, t.post_id
                FROM skillkind_message_thread t
                JOIN skillkind_help_post p ON p.id = t.post_id
                JOIN skillkind_job_application a ON a.post_id = p.id AND a.helper_id = t.helper_id
                WHERE t.id = :tid AND (t.poster_id = :sid OR t.helper_id = :sid)
                  AND a.status = 'accepted' AND p.status NOT IN ('completed', 'cancelled', 'deleted')
                FOR UPDATE OF p
            """),
                    {"tid": int(thread["id"]), "sid": int(sid)},
                )
            ).first()
            if authorized is None:
                async with self:
                    self.is_completing = False
                    self.error = "This job is no longer available to complete."
                return
            poster_id, helper_id, post_id = map(int, authorized)
            role = "poster" if poster_id == int(sid) else "helper"
            application = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM skillkind_job_application
                        WHERE post_id = :post_id AND helper_id = :helper_id
                        """
                    ),
                    {"post_id": post_id, "helper_id": helper_id},
                )
            ).first()
            application_id = (
                int(application[0]) if application is not None else None
            )
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT id, poster_confirmed, helper_confirmed
                        FROM skillkind_completed_task
                        WHERE post_id = :post_id AND helper_id = :helper_id
                        """
                    ),
                    {"post_id": post_id, "helper_id": helper_id},
                )
            ).first()
            if existing is None:
                created = (
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_completed_task
                                (post_id, application_id, poster_id, helper_id,
                                 actual_duration_minutes, reward_given,
                                 reward_confirmed, poster_confirmed,
                                 helper_confirmed, story_note)
                            VALUES
                                (:post_id, :app_id, :poster_id, :helper_id,
                                 :minutes, :reward, :reward_ok, :poster_ok,
                                 :helper_ok, :story)
                            RETURNING id, poster_confirmed, helper_confirmed
                            """
                        ),
                        {
                            "post_id": post_id,
                            "app_id": application_id,
                            "poster_id": poster_id,
                            "helper_id": helper_id,
                            "minutes": minutes,
                            "reward": reward_given,
                            "reward_ok": role == "poster"
                            and reward_given != "",
                            "poster_ok": role == "poster",
                            "helper_ok": role == "helper",
                            "story": story_note,
                        },
                    )
                ).first()
                task_id = int(created[0])
                poster_ok = bool(created[1])
                helper_ok = bool(created[2])
            else:
                task_id = int(existing[0])
                poster_ok = bool(existing[1]) or role == "poster"
                helper_ok = bool(existing[2]) or role == "helper"
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_completed_task
                        SET poster_confirmed = :poster_ok,
                            helper_confirmed = :helper_ok,
                            actual_duration_minutes = actual_duration_minutes,
                            reward_given = CASE WHEN :reward = ''
                                                THEN reward_given ELSE :reward END,
                            reward_confirmed = CASE WHEN :reward = ''
                                                    THEN reward_confirmed ELSE TRUE END,
                            story_note = CASE WHEN :story = ''
                                              THEN story_note ELSE :story END,
                            completed_at = now()
                        WHERE id = :ctid
                        """
                    ),
                    {
                        "poster_ok": poster_ok,
                        "helper_ok": helper_ok,
                        "minutes": minutes,
                        "reward": reward_given,
                        "story": story_note,
                        "ctid": int(existing[0]),
                    },
                )
            already_done = existing is not None and (
                bool(existing[1]) and bool(existing[2])
            )
            if poster_ok and helper_ok and not already_done:
                finalized = True
                removed_paths = [
                    str(row[0])
                    for row in (
                        await asession.execute(
                            text(
                                "DELETE FROM skillkind_help_post_photo WHERE help_post_id = :pid RETURNING path"
                            ),
                            {"pid": post_id},
                        )
                    ).all()
                ]
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_help_post
                        SET status = 'completed', updated_at = now()
                        WHERE id = :post_id
                        """
                    ),
                    {"post_id": post_id},
                )
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_profile
                        SET tasks_helped_count = tasks_helped_count + 1,
                            kindness_points = kindness_points + 10,
                            updated_at = now()
                        WHERE subscriber_id = :helper_id
                        """
                    ),
                    {"helper_id": helper_id},
                )
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_profile
                        SET tasks_received_count = tasks_received_count + 1,
                            kindness_points = kindness_points + 5,
                            updated_at = now()
                        WHERE subscriber_id = :poster_id
                        """
                    ),
                    {"poster_id": poster_id},
                )
                await refresh_review_ratings(asession, [poster_id, helper_id])
            await asession.commit()

        async with self:
            if (
                await self.get_state(AuthState)
            ).subscriber_id == sid and self.selected_thread["id"] == thread[
                "id"
            ]:
                self.selected_thread = {
                    **self.selected_thread,
                    "task_id": task_id,
                    "poster_confirmed": poster_ok,
                    "helper_confirmed": helper_ok,
                    "i_confirmed": True,
                    "is_completed": poster_ok and helper_ok,
                    "can_complete": False,
                }
        yield MessagingState.open_review_target

        for photo_path in removed_paths:
            try:
                root = rx.get_upload_dir().resolve()
                candidate = (root / photo_path).resolve()
                if candidate.is_relative_to(root):
                    candidate.unlink(missing_ok=True)
            except Exception as e:
                logging.exception(f"Error: {e}")

        async with self:
            self.is_completing = False
            self.success = (
                "Job completed by both sides — leave a review to close the loop."
                if finalized
                else "Your side is confirmed. Waiting for the other person."
            )
        toast_source = (
            "Task completed." if finalized else "Completion confirmed."
        )
        yield rx.toast(
            await self._localized_feedback_text(toast_source), duration=3500
        )
        yield MessagingState.load_threads
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile

    @rx.event(background=True)
    async def submit_review(self, form_data: dict[str, Any]):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            thread = self.selected_thread
            scores = [
                int(self.review_scores.get(key, 0)) for key in REVIEW_FIELD_KEYS
            ]
        comment = str(form_data.get("comment", "") or "").strip()
        kindness = False
        rating = int(sum(scores) / 4 + 0.5) if all(scores) else 0
        rating = max(1, min(5, rating)) if rating else 0
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."

        elif thread["task_id"] <= 0 or not thread["i_confirmed"]:
            problem = "Confirm your side of the job before writing a review."
        elif thread["my_review_done"]:
            problem = "You've already reviewed this task."
        elif not all(1 <= score <= 5 for score in scores):
            problem = (
                "Give a 1–5 star score for all four categories before saving."
            )
        elif len(comment.split()) > REVIEW_WORD_LIMIT:
            problem = "Keep your review to 500 words or fewer."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_reviewing = True
            self.error = ""
            self.success = ""

        task_id = int(thread["task_id"])
        try:
            async with rx.asession() as asession:
                task = await self._eligible_review_task(
                    asession, task_id, int(sid)
                )
                if task is None:
                    async with self:
                        self.is_reviewing = False
                        self.error = REVIEW_ELIGIBILITY_ERROR
                    return
                poster_id, helper_id = int(task[0]), int(task[1])
                reviewee_id = helper_id if int(sid) == poster_id else poster_id
                direction = (
                    "poster_to_helper"
                    if int(sid) == poster_id
                    else "helper_to_poster"
                )
                saved = (
                    await asession.execute(
                        text("""
                    INSERT INTO skillkind_review
                        (completed_task_id, reviewer_id, reviewee_id, direction,
                         rating, category_one, category_two, category_three,
                         category_four, comment, kindness_flag)
                    VALUES (:ctid, :sid, :recipient, :direction, :rating,
                            :c1, :c2, :c3, :c4, :comment, :kindness)
                    ON CONFLICT ON CONSTRAINT uq_review_task_reviewer DO NOTHING
                    RETURNING id
                """),
                        {
                            "ctid": task_id,
                            "sid": int(sid),
                            "recipient": reviewee_id,
                            "direction": direction,
                            "rating": rating,
                            "c1": scores[0],
                            "c2": scores[1],
                            "c3": scores[2],
                            "c4": scores[3],
                            "comment": encode_review_content(comment),
                            "kindness": kindness,
                        },
                    )
                ).first()
                if saved is None:
                    async with self:
                        self.is_reviewing = False
                        self.error = "You've already reviewed this task."
                    return
                await refresh_review_ratings(asession, [poster_id, helper_id])
                await asession.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_reviewing = False
                self.error = "We couldn't save your review. Please try again."
            return
        async with self:
            self.is_reviewing = False
            self._reset_review_scores()
            if self.selected_thread["task_id"] == task_id:
                self.selected_thread = {
                    **self.selected_thread,
                    "my_review_done": True,
                }
                self.review_target_open = False
            self.review_targets = [
                t for t in self.review_targets if t["task_id"] != task_id
            ]
            self.success = "Your review is now public. Thank you for sharing your experience."
        yield rx.toast(
            await self._localized_feedback_text("Your review is now public."),
            duration=4000,
        )
        yield MessagingState.load_threads
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile

    async def _eligible_review_task(self, asession, task_id: int, sid: int):
        return (
            await asession.execute(
                text("""
            SELECT ct.poster_id, ct.helper_id
            FROM skillkind_completed_task ct
            JOIN skillkind_help_post p ON p.id = ct.post_id AND p.author_id = ct.poster_id
            JOIN skillkind_subscriber poster ON poster.id = ct.poster_id
            JOIN skillkind_subscriber helper ON helper.id = ct.helper_id
            WHERE ct.id = :ctid AND :sid IN (ct.poster_id, ct.helper_id)
              AND ct.poster_id <> ct.helper_id
              AND ((ct.poster_id = :sid AND ct.poster_confirmed)
                OR (ct.helper_id = :sid AND ct.helper_confirmed))
              AND poster.is_active
              AND helper.is_active
              AND EXISTS (
                  SELECT 1 FROM skillkind_job_application a
                  WHERE (ct.application_id IS NULL OR a.id = ct.application_id)
                    AND a.post_id = ct.post_id
                    AND a.helper_id = ct.helper_id AND a.status IN ('accepted', 'completed')
              )
              AND NOT EXISTS (
                  SELECT 1 FROM skillkind_member_block mb
                  WHERE (mb.blocker_id = ct.poster_id AND mb.blocked_id = ct.helper_id)
                     OR (mb.blocker_id = ct.helper_id AND mb.blocked_id = ct.poster_id)
              )
            FOR UPDATE OF ct
        """),
                {"ctid": task_id, "sid": sid},
            )
        ).first()

    @rx.event(background=True)
    async def submit_review_response(
        self, review_id: int, form_data: dict[str, Any]
    ):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.response_error = ""
            self.response_error_id = review_id
        response = str(form_data.get("response", "") or "").strip()
        if (
            not sid.isdigit()
            or not response
            or len(response.split()) > REVIEW_WORD_LIMIT
        ):
            async with self:
                self.response_error = (
                    "Write a response of 1–500 words."
                    if sid.isdigit()
                    else REVIEW_ELIGIBILITY_ERROR
                )
            return
        async with self:
            self.responding_id = review_id
        try:
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(f"""
                    SELECT r.comment, r.completed_task_id, r.reviewer_id
                    FROM skillkind_review r
                    WHERE r.id = :rid AND r.reviewee_id = :sid
                      AND r.reviewer_id <> :sid AND {review_released_sql()}
                    FOR UPDATE OF r
                """),
                        {"rid": review_id, "sid": int(sid)},
                    )
                ).first()
                problem = REVIEW_ELIGIBILITY_ERROR
                if row is not None:
                    task = await self._eligible_review_task(
                        asession, int(row[1]), int(sid)
                    )
                    original, existing_response = decode_review_content(row[0])
                    if task is not None and {int(task[0]), int(task[1])} == {
                        int(sid),
                        int(row[2]),
                    }:
                        if existing_response:
                            problem = "A response has already been posted. Responses can only be written once."
                        elif (
                            row[0]
                            and row[0].startswith(REVIEW_CONTENT_PREFIX)
                            and encode_review_content(
                                original, existing_response
                            )
                            != row[0]
                        ):
                            problem = "This review cannot be updated right now."
                        else:
                            await asession.execute(
                                text("""
                                UPDATE skillkind_review SET comment = :comment WHERE id = :rid
                            """),
                                {
                                    "rid": review_id,
                                    "comment": encode_review_content(
                                        original, response
                                    ),
                                },
                            )
                            await asession.commit()
                            problem = ""
                async with self:
                    self.response_error = problem
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.response_error = (
                    "We couldn't save your response. Please try again."
                )
        finally:
            async with self:
                self.responding_id = 0
        yield MessagingState.load_conversation
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile

    # ------------------------------------------------------------------
    # Completion success story: photos of the finished work
    # ------------------------------------------------------------------

    @rx.event
    async def handle_completion_photos(self, files: list[rx.UploadFile]):
        """Add up to five completion photos, participants only.

        Original help-post photos are never touched: these rows live in
        `skillkind_completed_task_photo` and are normalised to WebP under 1 MB.
        """
        sid = (await self.get_state(AuthState)).subscriber_id
        thread = self.selected_thread
        task_id = int(thread["task_id"])
        self.photo_error = ""
        self.photo_success = ""
        if not sid.isdigit():
            self.photo_error = "Your session expired — please sign in again."
            return
        if task_id <= 0 or not thread["is_completed"]:
            self.photo_error = (
                "Photos open once both sides confirm the job is finished."
            )
            return
        if not files:
            self.photo_error = "Choose at least one photo to add."
            return
        self.photo_busy = True
        yield

        added = 0
        skipped = 0
        try:
            async with rx.asession() as asession:
                task = (
                    await asession.execute(
                        text(
                            """
                            SELECT poster_id, helper_id
                            FROM skillkind_completed_task
                            WHERE id = :ctid
                            """
                        ),
                        {"ctid": task_id},
                    )
                ).first()
                if task is None or int(sid) not in (
                    int(task[0]),
                    int(task[1]),
                ):
                    self.photo_busy = False
                    self.photo_error = (
                        "Only the two people who did this job can add photos."
                    )
                    return
                tally = (
                    await asession.execute(
                        text(
                            """
                            SELECT COUNT(*), COALESCE(MAX(display_order), -1)
                            FROM skillkind_completed_task_photo
                            WHERE completed_task_id = :ctid
                            """
                        ),
                        {"ctid": task_id},
                    )
                ).first()
                stored = int(tally[0] or 0) if tally is not None else 0
                order = int(tally[1]) if tally is not None else -1
                upload_dir = rx.get_upload_dir()
                upload_dir.mkdir(parents=True, exist_ok=True)
                for upload in files:
                    if stored >= COMPLETED_TASK_PHOTO_MAX_COUNT:
                        skipped += 1
                        continue
                    suffix = Path(str(upload.name or "")).suffix.lower()
                    if suffix not in ALLOWED_IMAGE_SUFFIXES:
                        skipped += 1
                        continue
                    try:
                        raw = await read_image_upload(upload)
                    except Exception as e:  # noqa: BLE001
                        logging.exception(f"Error: {e}")
                        skipped += 1
                        continue
                    payload = process_help_photo_bytes(
                        raw,
                        str(upload.name or ""),
                        str(getattr(upload, "content_type", "") or ""),
                    )
                    if payload is None or len(payload) >= PHOTO_MAX_BYTES:
                        skipped += 1
                        continue
                    name = unique_photo_name()
                    try:
                        (upload_dir / name).write_bytes(payload)
                    except Exception as e:  # noqa: BLE001
                        logging.exception(f"Error: {e}")
                        skipped += 1
                        continue
                    order += 1
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_completed_task_photo
                                (completed_task_id, uploader_id, path,
                                 caption, display_order)
                            VALUES (:ctid, :sid, :path, '', :ord)
                            """
                        ),
                        {
                            "ctid": task_id,
                            "sid": int(sid),
                            "path": name,
                            "ord": order,
                        },
                    )
                    stored += 1
                    added += 1
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Error: {e}")
            self.photo_busy = False
            self.photo_error = (
                "We couldn't save those photos — please try again."
            )
            return

        self.photo_busy = False
        if added and skipped:
            self.photo_success = (
                f"{added} photo(s) added. {skipped} were skipped — five photos "
                "per story, common image formats only."
            )
        elif added:
            self.photo_success = f"{added} photo(s) added to your story."
        else:
            self.photo_error = (
                "No photo could be added. Check the format (JPG, PNG, WebP, "
                "maximum 3 MB, static images only, no video) and the five-photo limit.",
            )
        yield MessagingState.load_completion_photos

    @rx.event(background=True)
    async def remove_completion_photo(self, photo_id: int):
        """Remove one of your own story photos. Help-post photos are untouched."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            task_id = int(self.selected_thread["task_id"])
        if not sid.isdigit() or task_id <= 0 or photo_id <= 0:
            return
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    DELETE FROM skillkind_completed_task_photo
                    WHERE id = :pid
                      AND completed_task_id = :ctid
                      AND uploader_id = :sid
                    """
                ),
                {"pid": int(photo_id), "ctid": task_id, "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.photo_success = "Photo removed from the story."
            self.photo_error = ""
        yield MessagingState.load_completion_photos

    # ------------------------------------------------------------------
    # Sharing: standard public share URLs only, nothing is posted for you
    # ------------------------------------------------------------------

    @rx.event
    def share_via_device(self, network_label: str):
        """Offer the device share sheet, falling back to copying the caption.

        Instagram and TikTok have no public prefilled web posting endpoint, so
        nothing is ever posted automatically on your behalf.
        """
        payload = json.dumps(
            {
                "title": "A Go and Help success story",
                "text": self.share_text,
                "url": self.share_url,
            }
        )
        self.share_note = f"Preparing your {network_label} share…"
        return rx.call_script(
            SHARE_SCRIPT_TEMPLATE.format(payload=payload),
            callback=MessagingState.share_result,
        )

    @rx.event
    def share_result(self, outcome: str):
        if outcome == "shared":
            self.share_note = (
                "Your device share sheet opened — finish the post in the app "
                "you picked."
            )
        elif outcome == "copied":
            self.share_note = (
                "Sharing isn't available in this browser, so your caption and "
                "link were copied — paste them into the app."
            )
        elif outcome == "cancelled":
            self.share_note = "Share cancelled — nothing was posted."
        else:
            self.share_note = (
                "We couldn't open a share sheet or copy automatically. Select "
                "the caption above and copy it by hand."
            )

    @rx.event
    def copy_share_caption(self):
        payload = json.dumps(
            {
                "title": "A Go and Help success story",
                "text": self.share_text,
                "url": self.share_url,
            }
        )
        return rx.call_script(
            SHARE_SCRIPT_TEMPLATE.format(payload=payload),
            callback=MessagingState.share_result,
        )

    # ------------------------------------------------------------------
    # Private bad-experience report
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def submit_safety_report(self, form_data: dict[str, Any]):
        """File one private report about the other participant in this job."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            thread = self.selected_thread
            category = self.report_category
        details = str(form_data.get("details", "") or "").strip()
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif thread["task_id"] <= 0 or not thread["is_completed"]:
            problem = "Reports open once the job is confirmed complete."
        elif thread["my_report_done"]:
            problem = "You've already reported this job. Our team has it."
        elif category not in SAFETY_REPORT_CATEGORIES:
            problem = "Choose what happened so we route it correctly."
        elif len(details) < REPORT_DETAILS_MIN:
            problem = (
                "Please describe what happened in a little more detail "
                f"({REPORT_DETAILS_MIN} characters or more)."
            )
        elif len(details) > REPORT_DETAILS_MAX:
            problem = (
                f"Keep the description under {REPORT_DETAILS_MAX} characters."
            )
        if problem:
            async with self:
                self.report_error = problem
                self.report_success = ""
            return
        async with self:
            self.is_reporting = True
            self.report_error = ""
            self.report_success = ""

        task_id = int(thread["task_id"])
        reported_id = int(thread["other_id"])
        failure = ""
        async with rx.asession() as asession:
            task = (
                await asession.execute(
                    text(
                        """
                        SELECT poster_id, helper_id, poster_confirmed,
                               helper_confirmed
                        FROM skillkind_completed_task
                        WHERE id = :ctid
                        """
                    ),
                    {"ctid": task_id},
                )
            ).first()
            if task is None:
                failure = "We couldn't find that completed job."
            else:
                poster_id = int(task[0])
                helper_id = int(task[1])
                participants = {poster_id, helper_id}
                if int(sid) not in participants:
                    failure = "Only the two people on this job can report it."
                elif reported_id not in participants or reported_id == int(sid):
                    failure = (
                        "A report can only be about the other person on "
                        "this job."
                    )
                elif not (bool(task[2]) and bool(task[3])):
                    failure = "Reports open once both sides confirm the job."
            if not failure:
                duplicate = (
                    await asession.execute(
                        text(
                            """
                            SELECT id FROM skillkind_safety_report
                            WHERE completed_task_id = :ctid
                              AND reporter_id = :sid
                            """
                        ),
                        {"ctid": task_id, "sid": int(sid)},
                    )
                ).first()
                if duplicate is not None:
                    failure = "You've already reported this job."
            if failure:
                async with self:
                    self.is_reporting = False
                    self.report_error = failure
                yield MessagingState.load_threads
                return
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_safety_report
                        (completed_task_id, reporter_id, reported_id,
                         category, details, status)
                    VALUES (:ctid, :sid, :reported, :cat, :details, :status)
                    """
                ),
                {
                    "ctid": task_id,
                    "sid": int(sid),
                    "reported": reported_id,
                    "cat": category,
                    "details": details,
                    "status": SAFETY_STATUS_OPEN,
                },
            )
            risk = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM skillkind_review r
                              WHERE r.reviewee_id = :reported AND r.rating = 1),
                            (SELECT COUNT(*) FROM skillkind_safety_report sr
                              WHERE sr.reported_id = :reported
                                AND sr.status IN ('open', 'reviewing'))
                        """
                    ),
                    {"reported": reported_id},
                )
            ).first()
            one_star = int(risk[0] or 0) if risk is not None else 0
            open_reports = int(risk[1] or 0) if risk is not None else 0
            # Flag for manual admin inspection only. Never an automatic ban,
            # and never a public accusation.
            if one_star > ONE_STAR_FLAG_THRESHOLD or open_reports >= 1:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_subscriber
                        SET moderation_status = :status,
                            moderation_updated_at = now()
                        WHERE id = :reported
                          AND moderation_status = 'clear'
                        """
                    ),
                    {
                        "status": MODERATION_STATUS_WARNED,
                        "reported": reported_id,
                    },
                )
            await asession.commit()

        async with self:
            self.is_reporting = False
            self.report_open = False
            self.report_category = ""
            self.report_success = (
                "Thank you — this report is private and now with our review "
                "team. Nothing is published and no one is accused publicly."
            )
        yield rx.toast(
            await self._localized_feedback_text(
                "Report sent privately to our team."
            ),
            duration=4000,
        )
        yield MessagingState.load_threads
