"""Posting flow for new Go and Help requests."""

import datetime
import calendar
import logging
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

import reflex as rx

from app.reward_display import reward_display
from sqlalchemy import text

from app.membership import (
    cap_message,
    check_post_allowance,
    post_interval_for_tier,
)
from app.image_processing import (
    ALLOWED_IMAGE_SUFFIXES,
    PHOTO_MAX_BYTES,
    PHOTO_SUFFIX,
    process_help_photo_bytes,
    read_image_upload,
)
from app.request_draft import (
    REQUEST_TEXT_FIELDS,
    EDITABLE_POST,
    EDIT_REQUEST_UPDATE,
    normalize_request_payload,
    validate_request,
    valid_request_point,
)
from app.countries import supported_currency
from app.states.auth_state import AuthState
from app.states.membership_state import MembershipState

from app.models import (
    CATEGORY_LABELS,
    HELP_DURATION_OPTIONS,
    HELP_DURATION_VALUES,
    DEFAULT_SCHEDULE_TIMEZONE,
    RECURRENCE_BIWEEKLY,
    RECURRENCE_MONTHLY,
    RECURRENCE_WEEKLY,
)
from app.recurring_help import (
    CADENCE_CHOICES,
    cadence_allows_interval,
    cadence_summary,
    clean_cadence,
    clean_interval,
    interval_choices,
    materialize_due_schedules,
    next_occurrence,
)
from app.skill_categories import (
    CATEGORY_CHOICES,
    CATEGORY_UPGRADE_REASON,
    FREE_REQUEST_CATEGORIES,
    MAX_REQUEST_CATEGORIES,
    PREMIUM_REQUEST_CATEGORIES,
    category_labels,
    category_limit_message,
    join_categories,
    normalize_categories,
    primary_category,
    request_category_limit,
)

REWARD_LABELS: dict[str, str] = {
    "lunch": "Lunch",
    "dinner": "Dinner",
    "accommodation": "Accommodation",
    "guided_tours": "Guided tours",
    "workshops": "Workshops",
    "lessons": "Lessons",
    "other": "Other",
}

MAX_PHOTOS = 5
JOB_INFO_MAX_CHARS = 500

URGENCY_VALUES: list[str] = ["flexible", "soon", "urgent"]
DURATION_VALUES: list[str] = HELP_DURATION_VALUES


class RecentPost(TypedDict):
    id: int
    title: str
    description: str
    category: str
    category_label: str
    reward_label: str
    reward_details: str
    location: str
    scheduled: str
    status: str
    urgency: str
    created: str
    photos: list[str]
    helpers_needed: int
    duration_minutes: int
    tools: str
    knowledge_skills: str
    accepted_location_name: str
    date_time_duration: str
    can_edit: bool


class RecurringSummary(TypedDict):
    id: int
    title: str
    cadence: str
    cadence_label: str
    status: str
    status_label: str
    next_label: str
    end_label: str
    count: int
    is_active: bool
    is_paused: bool
    is_ended: bool


class PostCounts(TypedDict):
    total: int
    open: int
    upcoming: int


EMPTY_COUNTS: PostCounts = {"total": 0, "open": 0, "upcoming": 0}


class HelpPostState(rx.State):
    edit_post_id: int = 0
    edit_busy: bool = False
    edit_error: str = ""
    request_title: str = ""
    request_description: str = ""
    request_category: str = ""
    request_date: str = ""
    request_reward: str = ""
    request_currency: str = "USD"
    request_budget: str = ""
    request_other: str = ""
    request_quote: bool = False

    @rx.var
    def request_date_min(self) -> str:
        return datetime.date.today().isoformat()

    @rx.var
    def request_date_max(self) -> str:
        return (
            self._two_year_ceiling(datetime.datetime.now(datetime.UTC))
            .date()
            .isoformat()
        )

    @rx.event
    def set_request_field(
        self, field: str, value: str | int | float | bool | None
    ):
        if not self.edit_busy and field in REQUEST_TEXT_FIELDS:
            setattr(self, field, normalize_request_payload(value))

    @rx.event
    def toggle_request_quote(self):
        if not self.edit_busy:
            self.request_quote = not self.request_quote

    @rx.event
    def cancel_edit(self):
        if not self.edit_busy:
            self.edit_post_id = 0
            self.edit_error = ""

    @rx.event
    async def begin_edit(self, post_id: int):
        from app.states.map_picker_state import MapPickerState
        from app.states.help_hub_state import LEGACY_REWARD_TYPE

        if self.edit_busy:
            return
        auth = await self.get_state(AuthState)
        if not auth.is_signed_in or not auth.subscriber_id.isdigit():
            return
        self.edit_error = ""
        try:
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text(f"""
                    SELECT p.title, p.description, p.category, p.scheduled_for,
                        p.reward_types, p.reward_type, p.reward_details,
                        p.reward_currency, COALESCE(p.reward_value, 0), p.other_reward_details,
                        p.accepted_latitude, p.accepted_longitude
                    FROM skillkind_help_post p
                    WHERE p.id = :pid AND {EDITABLE_POST} LIMIT 1
                """),
                        {"pid": post_id, "sid": int(auth.subscriber_id)},
                    )
                ).first()
            if row is None:
                self.edit_error = "This request cannot be edited after any help offer has been sent, or when it is no longer open."
                return
            self.request_title = str(row[0])
            self.request_description = str(row[1] or "")
            self.request_category = primary_category([str(row[2])])
            self.request_date = row[3].date().isoformat() if row[3] else ""
            self.request_reward = str(row[4] or "").split(",")[0]
            if not self.request_reward:
                self.request_reward = next(
                    (
                        key
                        for key, value in LEGACY_REWARD_TYPE.items()
                        if value == row[5]
                    ),
                    "other_reward",
                )
            self.request_currency = supported_currency(str(row[7] or "USD"))
            self.request_budget = f"{row[8]:.2f}"
            self.request_quote = "quote requested" in str(row[6] or "").lower()
            self.request_other = str(row[9] or row[6] or "")
            picker = await self.get_state(MapPickerState)
            picker._reset_point()
            picker.open_key = "edit-help-request"
            self.edit_post_id = post_id
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.edit_error = (
                "Could not open this request for editing. Please try again."
            )

    @rx.event
    async def save_edit(self):
        from app.states.map_picker_state import MapPickerState
        from app.states.help_hub_state import HelpHubState
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState

        if self.edit_busy or not self.edit_post_id:
            return
        auth = await self.get_state(AuthState)
        if not auth.is_signed_in or not auth.subscriber_id.isdigit():
            self.edit_error = "Please sign in again."
            return
        self.edit_busy = True
        self.edit_error = ""
        yield
        try:
            params = validate_request(
                self.request_title,
                self.request_description,
                self.request_category,
                self.request_date,
                self.request_reward,
                self.request_currency,
                self.request_budget,
                self.request_quote,
                self.request_other,
            )
            picker = await self.get_state(MapPickerState)
            repin = picker.open_key == "edit-help-request" and picker.has_point
            if repin and not valid_request_point(
                True, picker.latitude, picker.longitude
            ):
                raise ValueError("Choose a valid replacement map pin.")
            params.update(
                pid=self.edit_post_id,
                sid=int(auth.subscriber_id),
                repin=repin,
                latitude=picker.latitude if repin else None,
                longitude=picker.longitude if repin else None,
            )
            async with rx.asession() as session:
                # The FK's key-share lock serializes concurrent offer inserts with this lock.
                await session.execute(
                    text(
                        "SELECT id FROM skillkind_help_post WHERE id = :pid AND author_id = :sid FOR UPDATE"
                    ),
                    {"pid": self.edit_post_id, "sid": int(auth.subscriber_id)},
                )
                updated = (
                    await session.execute(text(EDIT_REQUEST_UPDATE), params)
                ).first()
                if updated is None:
                    await session.rollback()
                    self.edit_error = "Cannot edit: someone has sent a help offer, or this request is no longer open. Your changes were not saved."
                    return
                await session.commit()
            self.edit_post_id = 0
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.edit_error = str(e)
            return
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.edit_error = "Could not save your changes. Please try again."
            return
        finally:
            self.edit_busy = False
        yield HelpPostState.load_recent
        yield HelpHubState.load_help_hub
        yield ProfileState.load_profile
        yield DiscoveryState.load_jobs
        yield rx.toast("Help request updated.", duration=3500)

    # Legacy PRIMARY category: always mirrors the first multi-select choice.
    selected_category: str = ""
    # 1-3 current categories stored as `HelpPost.category_tags`.
    selected_categories: list[str] = []
    category_dropdown_open: bool = False

    @rx.event
    def toggle_category_dropdown(self):
        self.category_dropdown_open = not self.category_dropdown_open

    @rx.event
    def close_category_dropdown(self):
        self.category_dropdown_open = False

    reward_type: str = "lunch"
    is_saving: bool = False
    is_loading: bool = False
    has_loaded: bool = False
    error: str = ""
    success: str = ""
    recent_posts: list[RecentPost] = []
    counts: PostCounts = EMPTY_COUNTS
    pending_photo_paths: list[str] = []
    photo_error: str = ""
    photo_notice: str = ""
    photo_busy: bool = False
    job_info_length: int = 0
    schedule_min: str = ""
    schedule_max: str = ""

    @staticmethod
    def _two_year_ceiling(now: datetime.datetime) -> datetime.datetime:
        year = now.year + 2
        day = min(now.day, calendar.monthrange(year, now.month)[1])
        return now.replace(year=year, day=day)

    @rx.event
    def refresh_date_bounds(self):
        now = datetime.datetime.now(datetime.UTC)
        self.schedule_min = (now + datetime.timedelta(minutes=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        self.schedule_max = self._two_year_ceiling(now).strftime(
            "%Y-%m-%dT%H:%M"
        )

    # --- Recurring request controls (default: one-time) ---
    repeat_enabled: bool = False
    repeat_cadence: str = RECURRENCE_WEEKLY
    repeat_interval: int = 1
    cadence_choices: list[dict[str, str]] = CADENCE_CHOICES
    recurring_schedules: list[RecurringSummary] = []
    schedule_busy_id: int = 0
    schedule_error: str = ""
    schedule_notice: str = ""

    # The canonical shared taxonomy, in its canonical order.
    categories: list[dict[str, str]] = CATEGORY_CHOICES

    reward_options: list[dict[str, str]] = [
        {"value": "lunch", "label": "Lunch"},
        {"value": "dinner", "label": "Dinner"},
        {"value": "accommodation", "label": "Accommodation"},
        {"value": "guided_tours", "label": "Guided tours"},
        {"value": "workshops", "label": "Workshops"},
        {"value": "lessons", "label": "Lessons"},
        {"value": "other", "label": "Other"},
    ]

    duration_options: list[dict[str, str]] = HELP_DURATION_OPTIONS

    urgency_options: list[dict[str, str]] = [
        {"value": "flexible", "label": "Flexible — any time works"},
        {"value": "soon", "label": "Soon — within a few days"},
        {"value": "urgent", "label": "Urgent — I need help now"},
    ]

    @rx.var
    def repeat_interval_applies(self) -> bool:
        return cadence_allows_interval(self.repeat_cadence)

    @rx.var
    def repeat_interval_options(self) -> list[dict[str, str]]:
        return interval_choices(self.repeat_cadence)

    @rx.var
    def repeat_summary(self) -> str:
        if not self.repeat_enabled:
            return "One-time request"
        return cadence_summary(self.repeat_cadence, self.repeat_interval)

    @rx.var
    def has_recurring(self) -> bool:
        return len(self.recurring_schedules) > 0

    @rx.event
    def toggle_repeat(self):
        self.repeat_enabled = not self.repeat_enabled
        self.error = ""

    @rx.event
    def set_repeat_cadence(self, value: str):
        cadence = clean_cadence(value)
        if not cadence:
            return
        self.repeat_cadence = cadence
        if not cadence_allows_interval(cadence):
            self.repeat_interval = 1
        self.repeat_enabled = True
        self.error = ""

    @rx.event
    def set_repeat_interval(self, value: str):
        count = clean_interval(value, self.repeat_cadence)
        if count:
            self.repeat_interval = count
        self.error = ""

    @rx.var
    def reward_is_other(self) -> bool:
        return self.reward_type == "other"

    @rx.var
    def job_info_remaining(self) -> int:
        return max(JOB_INFO_MAX_CHARS - self.job_info_length, 0)

    @rx.var
    def job_info_near_limit(self) -> bool:
        return self.job_info_length > JOB_INFO_MAX_CHARS - 100

    @rx.var
    def photo_slots_left(self) -> int:
        return max(MAX_PHOTOS - len(self.pending_photo_paths), 0)

    @rx.event
    def set_job_info(self, value: str):
        self.job_info_length = min(len(value), JOB_INFO_MAX_CHARS)

    @rx.var
    def selected_category_label(self) -> str:
        return CATEGORY_LABELS.get(self.selected_category, "")

    @rx.var
    def selected_category_labels(self) -> list[str]:
        return category_labels(self.selected_categories)

    @rx.var
    def category_summary_label(self) -> str:
        labels = self.selected_category_labels
        if not labels:
            return ""
        return ", ".join(labels)

    @rx.var
    async def category_limit(self) -> int:
        """This member's per-request allowance: 1 free, 3 with premium."""
        premium = await self.get_var_value(MembershipState.is_premium)
        return request_category_limit(bool(premium))

    @rx.var
    async def category_slots_left(self) -> int:
        limit = await self.category_limit
        return max(limit - len(self.selected_categories), 0)

    @rx.var
    async def category_slot_hint(self) -> str:
        limit = await self.category_limit
        if limit <= 1:
            return "required — choose 1"
        return f"required — choose 1 to {limit}"

    @rx.var
    async def category_count_label(self) -> str:
        limit = await self.category_limit
        chosen = len(self.selected_categories)
        left = max(limit - chosen, 0)
        if left > 0:
            if limit <= 1:
                return (
                    "Choose 1 category. Select or unselect an option. "
                    f"Premium members can add up to {PREMIUM_REQUEST_CATEGORIES}."
                )
            return f"{chosen} of {limit} chosen — you can add {left} more."
        if limit == FREE_REQUEST_CATEGORIES:
            return (
                f"Free members choose {limit} category. Tap it again to swap it, "
                f"or go premium for up to {PREMIUM_REQUEST_CATEGORIES}."
            )
        return f"All {limit} categories chosen. Unselect one to swap it."

    @rx.event
    async def set_category(self, value: str):
        """Multi-select toggle, capped by the member's premium entitlement."""
        membership = await self.get_state(MembershipState)
        premium = bool(membership.is_premium)
        limit = request_category_limit(premium)
        chosen = list(self.selected_categories)
        if value in chosen:
            chosen = [item for item in chosen if item != value]
        elif len(chosen) >= limit:
            # The existing selection is always kept intact.
            if not premium:
                membership.paywall_open = True
                membership.upgrade_reason = CATEGORY_UPGRADE_REASON
                return
            self.error = category_limit_message(limit)
            return
        else:
            chosen = [*chosen, value]
        self.selected_categories = normalize_categories(chosen, limit)
        self.selected_category = (
            primary_category(self.selected_categories)
            if self.selected_categories
            else ""
        )
        self.error = ""

    @rx.event
    def set_reward_type(self, value: str):
        if value in REWARD_LABELS:
            self.reward_type = value
        self.error = ""

    @rx.event
    def clear_feedback(self):
        self.error = ""
        self.success = ""

    def _row_to_post(self, row, photos: list[str]) -> RecentPost:
        from app.help_languages import decode_knowledge
        from app.states.help_hub_state import _dates_label, _hours_label

        duration = int(row[13] or 0)
        knowledge = str(row[15] or "")
        dates = _dates_label(str(row[17] or ""), row[8], str(row[18] or ""))
        duration_label = (
            _hours_label(duration, knowledge)
            if duration
            else "Duration to agree"
        )
        category = str(row[3] or "")
        reward = str(row[4] or "")
        city = str(row[7] or "")
        place = str(row[6] or "")
        location = place if not city else f"{place}, {city}" if place else city
        return {
            "id": int(row[0]),
            "title": str(row[1]),
            "description": str(row[2] or ""),
            "category": category,
            "category_label": CATEGORY_LABELS.get(
                category, category.replace("_", " ").title()
            ),
            "reward_label": reward_display(
                reward,
                str(row[20] or "") if len(row) > 20 else reward,
                row[21] if len(row) > 21 else 0,
                str(row[22] or "USD") if len(row) > 22 else "USD",
                str(row[5] or ""),
            ),
            "reward_details": (
                ""
                if "money"
                in (str(row[20] or reward) if len(row) > 20 else reward).split(
                    ","
                )
                or reward in ("other", "other_reward")
                else str(row[5] or "")
            ),
            "location": location,
            "scheduled": row[8].strftime("%b %d, %Y · %H:%M")
            if row[8] is not None
            else "Time to agree",
            "status": str(row[9] or "open"),
            "urgency": str(row[10] or "flexible"),
            "created": row[11].strftime("%b %d, %Y")
            if row[11] is not None
            else "",
            "photos": photos,
            "helpers_needed": max(1, int(row[12] or 1)),
            "duration_minutes": duration,
            "tools": str(row[14] or ""),
            "knowledge_skills": decode_knowledge(knowledge)[0],
            "accepted_location_name": str(row[16] or ""),
            "date_time_duration": f"{dates} · {duration_label}",
            "can_edit": bool(row[19]) if len(row) > 19 else False,
        }

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if self.photo_busy:
            return
        self.photo_busy = True
        yield
        try:
            await self._process_photos(files)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.photo_error = (
                "Pictures could not be uploaded. Please try again."
            )
        finally:
            self.photo_busy = False
        yield

    async def _process_photos(self, files: list[rx.UploadFile]):
        """Process each upload server-side; only compressed WebP files persist."""
        if not files:
            return
        self.photo_error = ""
        self.photo_notice = ""
        remaining = MAX_PHOTOS - len(self.pending_photo_paths)
        if remaining <= 0:
            self.photo_error = f"You already have {MAX_PHOTOS} photos attached — remove one before adding another."
            return

        accepted = 0
        rejected: list[str] = []
        skipped = 0
        upload_dir = rx.get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        for file in files:
            if remaining <= 0:
                skipped += 1
                continue
            suffix = Path(file.name).suffix.lower()
            content_type = str(getattr(file, "content_type", "") or "").lower()
            if suffix not in ALLOWED_IMAGE_SUFFIXES or (
                content_type and not content_type.startswith("image/")
            ):
                rejected.append(file.name)
                continue
            try:
                raw = await read_image_upload(file)
            except ValueError:
                rejected.append(file.name)
                continue
            except Exception as e:
                logging.exception(f"Error: {e}")
                rejected.append(file.name)
                continue
            processed = process_help_photo_bytes(raw, file.name, content_type)
            if processed is None or len(processed) >= PHOTO_MAX_BYTES:
                rejected.append(file.name)
                continue
            filename = f"help_post_{uuid4().hex}{PHOTO_SUFFIX}"
            try:
                file_path = upload_dir / filename
                with file_path.open("wb") as output_file:
                    output_file.write(processed)
            except Exception as e:
                logging.exception(f"Error: {e}")
                rejected.append(file.name)
                continue
            self.pending_photo_paths.append(filename)
            accepted += 1
            remaining -= 1

        messages: list[str] = []
        if rejected:
            names = ", ".join(rejected[:3])
            messages.append(
                f"Couldn't accept {names}. Use static JPEG/JPG, PNG or WebP, maximum 3 MB per source. No video; stored results are under 1 MB."
            )
        if skipped:
            messages.append(
                f"{skipped} photo(s) were skipped: {MAX_PHOTOS} photos is the maximum."
            )
        self.photo_error = " ".join(messages)
        if accepted:
            self.photo_notice = f"{accepted} photo(s) optimised to WebP under 1 MB and ready to post."

    @rx.event
    def remove_photo(self, filename: str):
        """Drop a pending photo (and its processed file) before submission."""
        if filename not in self.pending_photo_paths:
            return
        self.pending_photo_paths = [
            path for path in self.pending_photo_paths if path != filename
        ]
        try:
            (rx.get_upload_dir() / filename).unlink(missing_ok=True)
        except Exception as e:
            logging.exception(f"Error: {e}")
        self.photo_error = ""
        self.photo_notice = "Photo removed."

    @rx.event(background=True)
    async def load_recent(self):
        """Idempotent loader: overlapping mount calls are ignored."""
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            if not sid.isdigit():
                self.recent_posts = []
                self.counts = EMPTY_COUNTS
                self.is_loading = False
                self.has_loaded = True
                return
            self.is_loading = True
            self.schedule_error = ""
        async with rx.asession() as asession:
            # Lazy, idempotent catch-up for anything this member's schedules
            # owe. Runs in its own committed transaction before the reads.
            try:
                await materialize_due_schedules(asession, int(sid))
            except Exception as e:
                logging.exception(f"Error: {e}")
                await asession.rollback()
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, title, description, category, reward_type,
                               reward_details, location_name, city, scheduled_for,
                               status, urgency, created_at, helpers_needed,
                               COALESCE(duration_minutes, 0), COALESCE(tools, ''),
                               COALESCE(knowledge_skills, ''), COALESCE(accepted_location_name, ''),
                               COALESCE(help_dates, ''), COALESCE(start_time, ''),
                               (p.author_id = :sid AND p.status = 'open' AND NOT EXISTS (
                                   SELECT 1 FROM skillkind_job_application a WHERE a.post_id = p.id
                               )) AS can_edit,
                               COALESCE(p.reward_types, ''), COALESCE(p.reward_value, 0),
                               COALESCE(p.reward_currency, 'USD')
                        FROM skillkind_help_post p
                        WHERE author_id = :sid
                          AND status NOT IN ('cancelled', 'deleted')
                        ORDER BY created_at DESC
                        LIMIT 6
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            post_ids = [int(row[0]) for row in rows]
            photo_map: dict[int, list[str]] = {
                post_id: [] for post_id in post_ids
            }
            if post_ids:
                photo_params = {
                    f"post_id_{index}": post_id
                    for index, post_id in enumerate(post_ids)
                }
                photo_placeholders = ", ".join(
                    f":post_id_{index}" for index in range(len(post_ids))
                )
                photo_rows = (
                    await asession.execute(
                        text(
                            f"""
                            SELECT help_post_id, path
                            FROM skillkind_help_post_photo
                            WHERE help_post_id IN ({photo_placeholders})
                            ORDER BY help_post_id, display_order
                            """
                        ),
                        photo_params,
                    )
                ).all()
                for photo_row in photo_rows:
                    photo_map[int(photo_row[0])].append(str(photo_row[1]))
            count_row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COUNT(*),
                            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END),
                            SUM(CASE WHEN scheduled_for >= now() THEN 1 ELSE 0 END)
                        FROM skillkind_help_post
                        WHERE author_id = :sid
                          AND status NOT IN ('cancelled', 'deleted')
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
            schedule_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, p.title, s.cadence, s.interval_count,
                               s.status, s.next_occurrence_at, s.end_date,
                               s.occurrence_count
                        FROM skillkind_recurring_help_schedule s
                        JOIN skillkind_help_post p ON p.id = s.source_post_id
                        WHERE s.owner_id = :sid
                        ORDER BY
                            CASE s.status WHEN 'active' THEN 0
                                          WHEN 'paused' THEN 1
                                          ELSE 2 END,
                            s.next_occurrence_at ASC NULLS LAST,
                            s.created_at DESC
                        LIMIT 12
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
        schedules = [self._row_to_schedule(r) for r in schedule_rows]
        async with self:
            self.recurring_schedules = schedules
            self.recent_posts = [
                self._row_to_post(r, photo_map.get(int(r[0]), [])) for r in rows
            ]
            self.counts = {
                "total": int(count_row[0] or 0) if count_row else 0,
                "open": int(count_row[1] or 0) if count_row else 0,
                "upcoming": int(count_row[2] or 0) if count_row else 0,
            }
            self.is_loading = False
            self.has_loaded = True

    @staticmethod
    def _row_to_schedule(row) -> RecurringSummary:
        cadence = str(row[2] or RECURRENCE_WEEKLY)
        interval = max(1, int(row[3] or 1))
        status = str(row[4] or "active")
        next_at = row[5]
        end_date = row[6]
        status_labels = {
            "active": "Active",
            "paused": "Paused",
            "completed": "Ended",
        }
        return {
            "id": int(row[0]),
            "title": str(row[1] or "Help request"),
            "cadence": cadence,
            "cadence_label": cadence_summary(cadence, interval),
            "status": status,
            "status_label": status_labels.get(status, status.title()),
            "next_label": next_at.strftime("%b %d, %Y · %H:%M")
            if next_at is not None
            else "No further dates",
            "end_label": end_date.strftime("%b %d, %Y")
            if end_date is not None
            else "No end date",
            "count": int(row[7] or 0),
            "is_active": status == "active",
            "is_paused": status == "paused",
            "is_ended": status == "completed",
        }

    async def _update_schedule(
        self, schedule_id: int, assignments: str, notice: str
    ) -> bool:
        """Ownership-enforced status change on one schedule row."""
        sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit() or schedule_id <= 0:
            self.schedule_error = "Your session expired — please sign in again."
            return False
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        f"""
                        UPDATE skillkind_recurring_help_schedule
                        SET {assignments}, updated_at = now()
                        WHERE id = :schedule_id AND owner_id = :sid
                        RETURNING id
                        """
                    ),
                    {"schedule_id": int(schedule_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                await asession.rollback()
                self.schedule_error = (
                    "That repeating request is no longer available."
                )
                return False
            await asession.commit()
        self.schedule_error = ""
        self.schedule_notice = notice
        return True

    @rx.event
    async def pause_schedule(self, schedule_id: int):
        self.schedule_busy_id = int(schedule_id)
        done = await self._update_schedule(
            int(schedule_id),
            "status = 'paused'",
            "Repeating request paused — no new posts will be created.",
        )
        self.schedule_busy_id = 0
        if done:
            return HelpPostState.load_recent

    @rx.event
    async def end_schedule(self, schedule_id: int):
        self.schedule_busy_id = int(schedule_id)
        done = await self._update_schedule(
            int(schedule_id),
            (
                "status = 'completed', next_occurrence_at = NULL, "
                "completed_at = now()"
            ),
            "Repeating request ended. Existing posts stay as they are.",
        )
        self.schedule_busy_id = 0
        if done:
            return HelpPostState.load_recent

    @rx.event(background=True)
    async def resume_schedule(self, schedule_id: int):
        """Resume a paused schedule, moving its next date into the future."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.schedule_busy_id = int(schedule_id)
            self.schedule_error = ""
        if not sid.isdigit():
            async with self:
                self.schedule_busy_id = 0
                self.schedule_error = (
                    "Your session expired — please sign in again."
                )
            return
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT cadence, interval_count, timezone_name,
                               next_occurrence_at, end_date, start_date
                        FROM skillkind_recurring_help_schedule
                        WHERE id = :schedule_id AND owner_id = :sid
                          AND status = 'paused'
                        FOR UPDATE
                        """
                    ),
                    {"schedule_id": int(schedule_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                await asession.rollback()
                async with self:
                    self.schedule_busy_id = 0
                    self.schedule_error = (
                        "That repeating request can't be resumed."
                    )
                return
            cadence = str(row[0] or RECURRENCE_WEEKLY)
            interval = max(1, int(row[1] or 1))
            tz_name = str(row[2] or DEFAULT_SCHEDULE_TIMEZONE)
            end_date = row[4]
            now = datetime.datetime.now(datetime.UTC)
            candidate = row[3]
            if candidate is None:
                candidate = now
            elif candidate.tzinfo is None:
                candidate = candidate.replace(tzinfo=datetime.UTC)
            guard = 0
            while candidate <= now and guard < 400:
                candidate = next_occurrence(
                    candidate, cadence, interval, tz_name
                )
                guard += 1
            finished = end_date is not None and candidate.date() > end_date
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_recurring_help_schedule
                    SET status = CAST(:status AS varchar),
                        next_occurrence_at = :next_at,
                        completed_at = CASE WHEN CAST(:finished AS boolean)
                                            THEN now() ELSE NULL END,
                        updated_at = now()
                    WHERE id = :schedule_id AND owner_id = :sid
                    """
                ),
                {
                    "schedule_id": int(schedule_id),
                    "sid": int(sid),
                    "status": "completed" if finished else "active",
                    "finished": bool(finished),
                    "next_at": None if finished else candidate,
                },
            )
            await asession.commit()
        async with self:
            self.schedule_busy_id = 0
            self.schedule_notice = (
                "Repeating request reached its end date."
                if finished
                else "Repeating request resumed."
            )
        yield HelpPostState.load_recent

    @rx.event(background=True)
    async def create_post(self, form_data: dict[str, Any]):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            categories = normalize_categories(self.selected_categories)
            reward_type = self.reward_type
            photo_paths = list(self.pending_photo_paths)
            repeat_enabled = self.repeat_enabled
            repeat_cadence = self.repeat_cadence
            repeat_interval = self.repeat_interval

        requester = str(form_data.get("requester_name", "") or "").strip()
        title = str(form_data.get("title", "") or "").strip()
        description = str(form_data.get("description", "") or "").strip()
        reward_details = str(form_data.get("reward_details", "") or "").strip()
        location_name = str(form_data.get("location_name", "") or "").strip()
        city = str(form_data.get("city", "") or "").strip()
        country = str(form_data.get("country", "") or "").strip()
        schedule_raw = str(form_data.get("scheduled_for", "") or "").strip()
        duration_raw = str(
            form_data.get("duration_minutes", "60") or "60"
        ).strip()
        urgency = str(
            form_data.get("urgency", "flexible") or "flexible"
        ).strip()

        now = datetime.datetime.now(datetime.UTC)
        ceiling = self._two_year_ceiling(now)
        scheduled: datetime.datetime | None = None
        problem = ""
        if len(photo_paths) > MAX_PHOTOS:
            problem = (
                f"You can attach up to {MAX_PHOTOS} photos per help request."
            )
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif len(requester) < 2:
            problem = "Add the name helpers should ask for."
        elif not categories:
            problem = (
                "Pick at least one category so helpers know what kind of task "
                "this is."
            )
        elif len(categories) > MAX_REQUEST_CATEGORIES:
            problem = (
                f"Choose at most {MAX_REQUEST_CATEGORIES} categories for one "
                "help request."
            )
        elif len(title) < 4:
            problem = "Give your request a short title (4+ characters)."
        elif len(title) > 160:
            problem = "Keep the title under 160 characters."
        elif len(description) < 15:
            problem = (
                "Describe the task in a little more detail (15+ characters)."
            )
        elif len(description) > JOB_INFO_MAX_CHARS:
            problem = (
                f"Job info must stay within {JOB_INFO_MAX_CHARS} characters."
            )
        elif reward_type not in REWARD_LABELS:
            problem = "Choose the reward you can offer."
        elif reward_type == "other" and len(reward_details) < 3:
            problem = "Tell helpers what your custom reward is."
        elif len(reward_details) > 255:
            problem = "Keep the reward details under 255 characters."
        elif not location_name:
            problem = "Add the meeting point or address for this task."
        elif not city:
            problem = "Add the city so nearby helpers can find you."
        elif not schedule_raw:
            problem = "Pick the date and time you need help."
        if not problem:
            try:
                scheduled = datetime.datetime.fromisoformat(schedule_raw)
                if scheduled.tzinfo is None:
                    scheduled = scheduled.replace(tzinfo=datetime.UTC)
                scheduled = scheduled.astimezone(datetime.UTC)
                if scheduled < now:
                    problem = "Choose a future date and time (UTC)."
                elif scheduled > ceiling:
                    problem = "Choose a date no more than two calendar years from now (UTC)."
            except ValueError as e:
                logging.exception(f"Error: {e}")
                problem = "That date and time couldn't be read — pick it again."
        duration = 60
        if not problem:
            if duration_raw not in DURATION_VALUES:
                problem = "Choose roughly how long the task will take."
            else:
                duration = int(duration_raw)
        if not problem and urgency not in URGENCY_VALUES:
            problem = "Choose how urgent this request is."

        # --- Recurring request validation (server-side, authoritative) ---
        repeat_end: datetime.date | None = None
        timezone_name = (
            str(form_data.get("repeat_timezone", "") or "").strip()
            or DEFAULT_SCHEDULE_TIMEZONE
        )
        if not problem and repeat_enabled:
            cadence = clean_cadence(repeat_cadence)
            interval = clean_interval(repeat_interval, cadence)
            end_raw = str(form_data.get("repeat_end_date", "") or "").strip()
            if not cadence:
                problem = "Choose how often this request should repeat."
            elif not interval:
                problem = "Choose a valid repeat interval."
            else:
                repeat_cadence = cadence
                repeat_interval = interval
            if not problem and end_raw:
                try:
                    repeat_end = datetime.date.fromisoformat(end_raw)
                except ValueError:
                    problem = "That repeat end date couldn't be read."
                else:
                    if repeat_end > ceiling.date():
                        problem = "The repeat end date cannot be more than two calendar years from today (UTC)."
                    elif (
                        scheduled is not None and repeat_end < scheduled.date()
                    ):
                        problem = (
                            "The repeat end date must be on or after the "
                            "first date you need help."
                        )
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return

        async with self:
            self.is_saving = True
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            # Authoritative, locked check in the same transaction as the INSERT.
            allowed, premium, _used, limit = await check_post_allowance(
                asession, int(sid)
            )
            if not allowed:
                await asession.rollback()
                message = cap_message(premium, limit)
                async with self:
                    self.is_saving = False
                    self.error = message
                    membership = await self.get_state(MembershipState)
                    if not premium:
                        membership.paywall_open = True
                        membership.upgrade_reason = message
                return
            # Category allowance is decided by the database membership record,
            # never by client state.
            category_limit = request_category_limit(premium)
            if len(categories) > category_limit:
                await asession.rollback()
                async with self:
                    self.is_saving = False
                    self.error = category_limit_message(category_limit)
                    membership = await self.get_state(MembershipState)
                    if not premium:
                        membership.paywall_open = True
                        membership.upgrade_reason = CATEGORY_UPGRADE_REASON
                return
            helpers_needed = 1
            if premium:
                raw_helpers = str(form_data.get("helpers_needed", "1")).strip()
                if (
                    not raw_helpers.isascii()
                    or not raw_helpers.isdecimal()
                    or not 1 <= int(raw_helpers) <= 500
                ):
                    await asession.rollback()
                    async with self:
                        self.is_saving = False
                        self.error = "Number of people required must be a whole number from 1 to 500."
                    return
                helpers_needed = int(raw_helpers)
            lifetime = post_interval_for_tier(premium)
            post_row = (
                await asession.execute(
                    text(
                        f"""
                        INSERT INTO skillkind_help_post
                            (author_id, title, description, category,
                             category_tags, reward_type,
                             reward_details, reward_value, reward_currency,
                             location_name, city, country, latitude, longitude,
                             scheduled_for, duration_minutes, urgency,
                             helpers_needed, status, view_count,
                             expires_at, premium_priority)
                        VALUES
                            (:sid, :title, :description, :category,
                             :category_tags, :reward_type,
                             :reward_details, 0, 'USD',
                             :location_name, :city, :country, NULL, NULL,
                             :scheduled, :duration, :urgency,
                             :helpers_needed, 'open', 0,
                             now() + INTERVAL '{lifetime}', :priority)
                        RETURNING id
                        """
                    ),
                    {
                        "sid": int(sid),
                        "title": title,
                        "description": description,
                        "category": primary_category(categories),
                        "category_tags": join_categories(
                            categories, category_limit
                        ),
                        "reward_type": reward_type,
                        "reward_details": reward_details,
                        "location_name": location_name,
                        "city": city,
                        "country": country,
                        "scheduled": scheduled,
                        "duration": duration,
                        "urgency": urgency,
                        "priority": premium,
                        "helpers_needed": helpers_needed,
                    },
                )
            ).first()
            post_id = int(post_row[0]) if post_row is not None else 0
            if post_id <= 0:
                async with self:
                    self.is_saving = False
                    self.error = "We couldn't create that help request. Please try again."
                return
            from app.field_requests import notify_field_helpers

            try:
                await notify_field_helpers(asession, post_id)
            except Exception as e:
                logging.exception(f"Error: {e}")
                await asession.rollback()
                async with self:
                    self.is_saving = False
                    self.error = (
                        "We couldn't create that request. Please try again."
                    )
                return
            if photo_paths:
                photo_values = [
                    f"(:post_id, :photo_path_{index}, {index})"
                    for index in range(len(photo_paths))
                ]
                photo_params: dict[str, str | int] = {"post_id": post_id}
                for index, photo_path in enumerate(photo_paths):
                    photo_params[f"photo_path_{index}"] = photo_path
                photo_values_sql = ", ".join(photo_values)
                try:
                    await asession.execute(
                        text(
                            f"""
                            INSERT INTO skillkind_help_post_photo
                                (help_post_id, path, display_order)
                            VALUES {photo_values_sql}
                            """
                        ),
                        photo_params,
                    )
                except Exception as e:
                    logging.exception(f"Error: {e}")
                    async with self:
                        self.is_saving = False
                        self.error = (
                            "We couldn't attach those photos. Please try again."
                        )
                    return
            if repeat_enabled and scheduled is not None:
                first_at = (
                    scheduled
                    if scheduled.tzinfo is not None
                    else scheduled.replace(tzinfo=datetime.UTC)
                )
                next_at = next_occurrence(
                    first_at, repeat_cadence, repeat_interval, timezone_name
                )
                finished = (
                    repeat_end is not None and next_at.date() > repeat_end
                )
                try:
                    schedule_row = (
                        await asession.execute(
                            text(
                                """
                                INSERT INTO
                                    skillkind_recurring_help_schedule
                                    (owner_id, source_post_id, cadence,
                                     interval_count, weekday, month_day,
                                     start_time, timezone_name, start_date,
                                     end_date, next_occurrence_at,
                                     last_occurrence_at, occurrence_count,
                                     status, note)
                                VALUES
                                    (:sid, :post_id, :cadence, :interval,
                                     :weekday, :month_day, :start_time, :tz,
                                     :start_date, :end_date, :next_at,
                                     :first_at, 1, :status, '')
                                RETURNING id
                                """
                            ),
                            {
                                "sid": int(sid),
                                "post_id": post_id,
                                "cadence": repeat_cadence,
                                "interval": repeat_interval,
                                "weekday": first_at.weekday()
                                if repeat_cadence
                                in (RECURRENCE_WEEKLY, RECURRENCE_BIWEEKLY)
                                else None,
                                "month_day": first_at.day
                                if repeat_cadence == RECURRENCE_MONTHLY
                                else None,
                                "start_time": first_at.strftime("%H:%M"),
                                "tz": timezone_name,
                                "start_date": first_at.date(),
                                "end_date": repeat_end,
                                "next_at": None if finished else next_at,
                                "first_at": first_at,
                                "status": "completed" if finished else "active",
                            },
                        )
                    ).first()
                    if schedule_row is not None:
                        await asession.execute(
                            text(
                                """
                                INSERT INTO
                                    skillkind_recurring_help_occurrence
                                    (schedule_id, generated_post_id,
                                     occurrence_at)
                                VALUES (:schedule_id, :post_id, :first_at)
                                ON CONFLICT ON CONSTRAINT
                                    uq_recurring_occurrence_schedule_time
                                DO NOTHING
                                """
                            ),
                            {
                                "schedule_id": int(schedule_row[0]),
                                "post_id": post_id,
                                "first_at": first_at,
                            },
                        )
                except Exception as e:
                    logging.exception(f"Error: {e}")
                    await asession.rollback()
                    async with self:
                        self.is_saving = False
                        self.error = (
                            "We couldn't set up the repeating schedule. "
                            "Please try again."
                        )
                    return
            await asession.execute(
                text(
                    "UPDATE skillkind_subscriber SET display_name = :name WHERE id = :sid"
                ),
                {"name": requester, "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.is_saving = False
            self.selected_category = ""
            self.selected_categories = []
            self.reward_type = "lunch"
            self.pending_photo_paths = []
            self.photo_error = ""
            self.photo_notice = ""
            self.job_info_length = 0
            self.repeat_enabled = False
            self.repeat_cadence = RECURRENCE_WEEKLY
            self.repeat_interval = 1
            self.success = (
                f'"{title}" is live - helpers nearby can see it now.'
                + (
                    f" It repeats: {cadence_summary(repeat_cadence, repeat_interval)}."
                    if repeat_enabled
                    else ""
                )
            )
            auth = await self.get_state(AuthState)
            auth.display_name = requester
        yield rx.toast("Help request posted.", duration=4000)
        yield HelpPostState.load_recent
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile
