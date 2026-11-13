"""Community noticeboard: section switching and persistent text discussions.

Everything here reads and writes the real `skillkind_community_topic` and
`skillkind_community_comment` tables — no sample content is ever generated.
"""

from typing import TypedDict
import datetime
import logging

import reflex as rx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    COMMUNITY_COMMENT_MAX_WORDS,
    COMMUNITY_SUBJECT_ICONS,
    COMMUNITY_SUBJECT_OTHER,
    COMMUNITY_SUBJECTS,
    COMMUNITY_TOPIC_MAX_WORDS,
    COMMUNITY_TOPIC_TITLE_MAX_LENGTH,
)
from app.member_blocks import BLOCK_UNAVAILABLE_MESSAGE, are_members_blocked
from app.interface_i18n import translate
from app.membership import db_is_premium
from app.states.auth_state import AuthState
from app.states.membership_state import MembershipState

FORUM_TOPIC_REASON = "Go premium to start more topics"
FORUM_COMMENT_REASON = "Go premium to comment more"
FORUM_TOPIC_CAP = "Free members can start 1 topic per UTC calendar month."
FORUM_COMMENT_CAP = "Free members can post 10 comments total per UTC calendar month across all discussions."
FORUM_LOCK_NAMESPACE = 918274


def forum_month_bounds(
    stamp: datetime.datetime,
) -> tuple[datetime.datetime, datetime.datetime]:
    start = stamp.astimezone(datetime.UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end = (
        start.replace(year=start.year + 1, month=1)
        if start.month == 12
        else start.replace(month=start.month + 1)
    )
    return start, end


async def forum_usage(
    session: AsyncSession, sid: int, *, lock: bool = False
) -> tuple[bool, int, int, datetime.datetime]:
    """The locked snapshot must share its transaction and timestamp with INSERT."""
    if lock:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:namespace, :sid)"),
            {"namespace": FORUM_LOCK_NAMESPACE, "sid": sid},
        )
    premium = await db_is_premium(session, sid)
    stamp = datetime.datetime.now(datetime.UTC)
    start, end = forum_month_bounds(stamp)
    row = (
        await session.execute(
            text("""
        SELECT
          (SELECT COUNT(*) FROM skillkind_community_topic
           WHERE author_id=:sid AND created_at >= :start AND created_at < :end),
          (SELECT COUNT(*) FROM skillkind_community_comment
           WHERE author_id=:sid AND created_at >= :start AND created_at < :end)
    """),
            {"sid": sid, "start": start, "end": end},
        )
    ).first()
    return premium, int(row[0] or 0), int(row[1] or 0), stamp


# Sentinel used by the compact topic dropdown for "All topics".
SUBJECT_SELECT_ALL = "__all__"

# Canonical subject order, resolved once for the parameterized feed ordering.
SUBJECT_ORDER: dict[str, int] = {
    subject: index for index, subject in enumerate(COMMUNITY_SUBJECTS)
}


class TopicItem(TypedDict):
    id: int
    title: str
    subject: str
    subject_icon: str
    body: str
    preview: str
    author_id: int
    author_name: str
    author_avatar_seed: str
    author_handle: str
    author_avatar: str
    author_verified: bool
    created: str
    comment_count: int
    mine: bool


class CommentItem(TypedDict):
    id: int
    author_id: int
    author_name: str
    author_avatar_seed: str
    author_handle: str
    author_avatar: str
    author_verified: bool
    body: str
    created: str
    mine: bool


EMPTY_TOPIC: TopicItem = {
    "id": 0,
    "title": "",
    "subject": "",
    "subject_icon": "",
    "body": "",
    "preview": "",
    "author_id": 0,
    "author_name": "",
    "author_avatar_seed": "",
    "author_handle": "",
    "author_avatar": "",
    "author_verified": False,
    "created": "",
    "comment_count": 0,
    "mine": False,
}


def _word_count(value: str) -> int:
    return len([word for word in value.split() if word])


def _fmt_stamp(value) -> str:
    return value.strftime("%b %d, %Y · %H:%M") if value is not None else ""


class CommunityState(rx.State):
    """The three-section Community screen and its discussion feed."""

    section: str = "community"

    sections: list[dict[str, str]] = [
        {"value": "community", "label": "Forum", "icon": "messages-square"},
        {"value": "events", "label": "Events", "icon": "calendar-days"},
        {"value": "reviews", "label": "Reviews", "icon": "star"},
    ]

    # The compact dropdown is a momentary control: it resets to its prompt
    # after every toggle so the same subject can be chosen again.
    subject_select_value: str = ""
    subject_list_open: bool = False

    @rx.event
    def toggle_subject_list(self):
        self.subject_list_open = not self.subject_list_open

    @rx.event
    def close_subject_list(self):
        self.subject_list_open = False

    # Pinned discussion subjects, in their canonical order.
    subject_options: list[dict[str, str]] = [
        {
            "value": subject,
            "label": subject,
            "icon": COMMUNITY_SUBJECT_ICONS.get(subject, "circle-ellipsis"),
        }
        for subject in COMMUNITY_SUBJECTS
    ]

    # Composer choice: exactly one subject per new discussion.
    subject_draft: str = ""

    # Feed filter: any number of pinned subjects at once, stored in browser
    # local storage so the choice survives closing and reopening the app.
    # An empty value means "All topics".
    subject_filter_store: str = rx.LocalStorage(
        "", name="gah_community_subject_filters"
    )

    topics: list[TopicItem] = []
    selected_topic: TopicItem = EMPTY_TOPIC
    comments: list[CommentItem] = []

    title_draft: str = ""
    body_draft: str = ""
    comment_draft: str = ""
    draft_version: int = 0
    comment_version: int = 0

    forum_premium: bool = False
    monthly_topics_used: int = 0
    monthly_comments_used: int = 0

    @rx.var
    def topics_remaining(self) -> int:
        return max(0, 1 - self.monthly_topics_used)

    @rx.var
    def comments_remaining(self) -> int:
        return max(0, 10 - self.monthly_comments_used)

    @rx.var
    def topic_allowance_available(self) -> bool:
        return self.forum_premium or self.topics_remaining > 0

    @rx.var
    def comment_allowance_available(self) -> bool:
        return self.forum_premium or self.comments_remaining > 0

    def _set_usage(self, premium: bool, topics: int, comments: int):
        self.forum_premium = premium
        self.monthly_topics_used = topics
        self.monthly_comments_used = comments

    async def _quota_rejected(self, topic: bool):
        self.is_posting = False
        self.is_commenting = False
        self.success = ""
        self.error = FORUM_TOPIC_CAP if topic else FORUM_COMMENT_CAP
        membership = await self.get_state(MembershipState)
        membership.paywall_open = True
        membership.upgrade_reason = (
            FORUM_TOPIC_REASON if topic else FORUM_COMMENT_REASON
        )

    composer_open: bool = False
    is_loading: bool = False
    is_loading_topic: bool = False
    is_posting: bool = False
    is_commenting: bool = False
    error: str = ""
    success: str = ""

    # ------------------------------------------------------------------
    # Derived counters used by the noticeboard UI
    # ------------------------------------------------------------------

    @rx.var
    def title_length(self) -> int:
        return len(self.title_draft.strip())

    @rx.var
    def title_remaining(self) -> int:
        return COMMUNITY_TOPIC_TITLE_MAX_LENGTH - len(self.title_draft.strip())

    @rx.var
    def title_over_limit(self) -> bool:
        return len(self.title_draft.strip()) > COMMUNITY_TOPIC_TITLE_MAX_LENGTH

    @rx.var
    def body_words(self) -> int:
        return _word_count(self.body_draft)

    @rx.var
    def body_over_limit(self) -> bool:
        return _word_count(self.body_draft) > COMMUNITY_TOPIC_MAX_WORDS

    @rx.var
    def comment_words(self) -> int:
        return _word_count(self.comment_draft)

    @rx.var
    def comment_over_limit(self) -> bool:
        return _word_count(self.comment_draft) > COMMUNITY_COMMENT_MAX_WORDS

    @rx.var
    def subject_chosen(self) -> bool:
        return self.subject_draft in SUBJECT_ORDER

    @rx.var
    def subject_is_other(self) -> bool:
        return self.subject_draft == COMMUNITY_SUBJECT_OTHER

    @rx.var
    def subject_hint(self) -> str:
        if not self.subject_draft:
            return "Choose the pinned subject this discussion belongs under."
        if self.subject_draft == COMMUNITY_SUBJECT_OTHER:
            return (
                "Filed under Other — your own title is required so people know "
                "what this is about."
            )
        return (
            f"Filed under {self.subject_draft} — give it your own descriptive "
            "title as well."
        )

    @rx.var
    def selected_subject_filters(self) -> list[str]:
        """The persisted multi-selection, cleaned against the known subjects."""
        chosen: list[str] = []
        for value in self.subject_filter_store.split("|"):
            name = value.strip()
            if name in SUBJECT_ORDER and name not in chosen:
                chosen.append(name)
        return sorted(chosen, key=lambda name: SUBJECT_ORDER[name])

    @rx.var
    def has_subject_filters(self) -> bool:
        return len(self.selected_subject_filters) > 0

    @rx.var
    def filter_label(self) -> str:
        chosen = self.selected_subject_filters
        if not chosen:
            return "All topics"
        return ", ".join(chosen)

    @rx.var
    def filter_summary(self) -> str:
        count = len(self.selected_subject_filters)
        if count == 0:
            return "Showing every subject on the board."
        if count == 1:
            return f"Filtered to {self.selected_subject_filters[0]}."
        return f"Filtered to {count} subjects: {self.filter_label}."

    @rx.var
    def can_post_topic(self) -> bool:
        title = self.title_draft.strip()
        body = self.body_draft.strip()
        return (
            self.subject_draft in SUBJECT_ORDER
            and len(title) > 0
            and len(title) <= COMMUNITY_TOPIC_TITLE_MAX_LENGTH
            and len(body) > 0
            and _word_count(body) <= COMMUNITY_TOPIC_MAX_WORDS
        )

    @rx.var
    def can_post_comment(self) -> bool:
        body = self.comment_draft.strip()
        return (
            len(body) > 0
            and _word_count(body) <= COMMUNITY_COMMENT_MAX_WORDS
            and self.selected_topic["id"] > 0
        )

    @rx.var
    def has_topic_open(self) -> bool:
        return self.selected_topic["id"] > 0

    @rx.var
    def comment_count_label(self) -> str:
        count = len(self.comments)
        if count == 1:
            return "1 reply"
        return f"{count} replies"

    @rx.var
    def title_limit_label(self) -> str:
        return (
            f"{self.title_length}/{COMMUNITY_TOPIC_TITLE_MAX_LENGTH} characters"
        )

    @rx.var
    def body_limit_label(self) -> str:
        return f"{self.body_words} of {COMMUNITY_TOPIC_MAX_WORDS} words"

    @rx.var
    def comment_limit_label(self) -> str:
        return f"{self.comment_words} of {COMMUNITY_COMMENT_MAX_WORDS} words"

    @rx.var
    async def forum_display(self) -> dict[str, str]:
        auth = await self.get_state(AuthState)
        language = auth.preferred_language
        chosen = [
            translate(language, subject)
            for subject in self.selected_subject_filters
        ]
        label = (
            ", ".join(chosen) if chosen else translate(language, "All topics")
        )
        summary = translate(language, "Showing every subject on the board.")
        if len(chosen) == 1:
            summary = translate(language, "Filtered to {subject}.").format(
                subject=chosen[0]
            )
        elif chosen:
            summary = translate(
                language, "Filtered to {count} subjects: {subjects}."
            ).format(count=len(chosen), subjects=label)
        count = len(self.comments)
        return {
            "filter_label": label,
            "filter_summary": summary,
            "title_hint": translate(
                language, "required · max {limit} characters"
            ).format(limit=COMMUNITY_TOPIC_TITLE_MAX_LENGTH),
            "body_hint": translate(
                language, "required · text only · max {limit} words"
            ).format(limit=f"{COMMUNITY_TOPIC_MAX_WORDS:,}"),
            "comment_hint": translate(
                language, "text only · max {limit} words"
            ).format(limit=f"{COMMUNITY_COMMENT_MAX_WORDS:,}"),
            "title_limit": translate(
                language, "{count}/{limit} characters"
            ).format(
                count=self.title_length, limit=COMMUNITY_TOPIC_TITLE_MAX_LENGTH
            ),
            "body_limit": translate(
                language, "{count} of {limit} words"
            ).format(count=self.body_words, limit=COMMUNITY_TOPIC_MAX_WORDS),
            "comment_limit": translate(
                language, "{count} of {limit} words"
            ).format(
                count=self.comment_words, limit=COMMUNITY_COMMENT_MAX_WORDS
            ),
            "replies": translate(
                language, "{count} reply" if count == 1 else "{count} replies"
            ).format(count=count),
            "comment_allowance": translate(
                language,
                "10 comments per month · {count} remaining this UTC month",
            ).format(count=self.comments_remaining),
            "topic_allowance": translate(
                language,
                "Free: 1 topic per month · 10 comments per month. Remaining this UTC month: {topics} topic · {comments} comments. Text only, kept forever on the board — titles up to 200 characters and posts up to 5,000 words.",
            ).format(
                topics=self.topics_remaining, comments=self.comments_remaining
            ),
            "title_error": translate(
                language, "Titles can be at most {limit} characters."
            ).format(limit=COMMUNITY_TOPIC_TITLE_MAX_LENGTH),
            "body_error": translate(
                language,
                "That post is longer than {limit} words — please shorten it.",
            ).format(limit=COMMUNITY_TOPIC_MAX_WORDS),
            "comment_error": translate(
                language, "Comments are limited to {limit} words."
            ).format(limit=COMMUNITY_COMMENT_MAX_WORDS),
        }

    @rx.event
    async def show_forum_toast(self, source: str):
        auth = await self.get_state(AuthState)
        return rx.toast(
            translate(auth.preferred_language, source), duration=3000
        )

    # ------------------------------------------------------------------
    # Section switching and drafts
    # ------------------------------------------------------------------

    @rx.event
    def set_section(self, value: str):
        self.section = value
        self.error = ""
        self.success = ""
        from app.states.notification_state import NotificationState

        if value == "community":
            return CommunityState.load_topics
        if value == "events":
            from app.states.event_state import EventState

            # Entering Events clears only the event notices.
            return [
                EventState.load_events,
                NotificationState.mark_events_read,
            ]
        if value == "reviews":
            return NotificationState.mark_reviews_read
        return None

    @rx.event
    def set_subject_draft(self, value: str):
        self.subject_draft = value if value in SUBJECT_ORDER else ""
        self.error = ""

    @rx.event
    def toggle_subject_filter(self, value: str):
        """Add or remove one pinned subject from the persisted selection."""
        if value not in SUBJECT_ORDER:
            return None
        chosen = list(self.selected_subject_filters)
        if value in chosen:
            chosen.remove(value)
        else:
            chosen.append(value)
        chosen.sort(key=lambda name: SUBJECT_ORDER[name])
        self.subject_filter_store = "|".join(chosen)
        self.error = ""
        self.success = ""
        return CommunityState.load_topics

    @rx.event
    def choose_subject_from_select(self, value: str):
        """The dropdown drives exactly the same persisted multi-selection."""
        raw = str(value or "").strip()
        self.subject_select_value = ""
        if not raw:
            return None
        if raw == SUBJECT_SELECT_ALL:
            return CommunityState.clear_subject_filter
        return CommunityState.toggle_subject_filter(raw)

    @rx.event
    def clear_subject_filter(self):
        self.subject_filter_store = ""
        self.error = ""
        self.success = ""
        return CommunityState.load_topics

    @rx.event
    def set_title_draft(self, value: str):
        self.title_draft = value

    @rx.event
    def set_body_draft(self, value: str):
        self.body_draft = value

    @rx.event
    async def set_comment_draft(self, value: str):
        auth = await self.get_state(AuthState)
        if auth.subscriber_id.isdigit() and auth.is_signed_in:
            self.comment_draft = value

    @rx.event(background=True)
    async def open_comment_paywall(self):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            signed_in = auth.is_signed_in
        if not signed_in or not sid.isdigit():
            return
        async with rx.asession() as session:
            premium, topics, comments, _ = await forum_usage(session, int(sid))
        async with self:
            self._set_usage(premium, topics, comments)
            if not self.comment_allowance_available:
                await self._quota_rejected(False)

    @rx.event(background=True)
    async def toggle_composer(self):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            signed_in = auth.is_signed_in
            if self.composer_open:
                self.composer_open = False
                return
        if not signed_in or not sid.isdigit():
            async with self:
                self.error = "Please sign in to start a discussion."
            return
        async with rx.asession() as session:
            premium, topics, comments, _ = await forum_usage(session, int(sid))
        async with self:
            self._set_usage(premium, topics, comments)
            if not self.topic_allowance_available:
                await self._quota_rejected(True)
                return
            self.composer_open = True
            self.error = ""
            self.success = ""

    @rx.event
    def clear_feedback(self):
        self.error = ""
        self.success = ""

    @rx.event
    def close_topic(self):
        self.selected_topic = EMPTY_TOPIC
        self.comments = []
        self.comment_draft = ""
        self.comment_version += 1
        self.error = ""
        self.success = ""

    @rx.event(background=True)
    async def open_notification_topic(self, topic_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            return
        try:
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text("""
                    SELECT t.id, t.title, t.body, t.subject_category, t.author_id,
                           s.display_name, COALESCE(pr.avatar_path, ''), s.is_verified
                    FROM skillkind_community_topic t
                    JOIN skillkind_subscriber s ON s.id=t.author_id AND s.is_active
                    LEFT JOIN skillkind_profile pr ON pr.subscriber_id=s.id
                    WHERE t.id=:tid AND NOT EXISTS (
                        SELECT 1 FROM skillkind_member_block b
                        WHERE (b.blocker_id=:sid AND b.blocked_id=t.author_id)
                           OR (b.blocked_id=:sid AND b.blocker_id=t.author_id))
                    LIMIT 1
                """),
                        {"sid": int(sid), "tid": topic_id},
                    )
                ).first()
            if not row:
                raise ValueError("Discussion unavailable")
            async with self:
                self.selected_topic = {
                    **EMPTY_TOPIC,
                    "id": int(row[0]),
                    "title": str(row[1]),
                    "body": str(row[2]),
                    "subject": str(row[3]),
                    "author_id": int(row[4]),
                    "author_name": str(row[5]),
                    "author_avatar_seed": f"member-{row[4]}",
                    "author_avatar": str(row[6]),
                    "author_verified": bool(row[7]),
                    "mine": int(row[4]) == int(sid),
                }
            yield CommunityState.load_comments
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "That discussion is no longer available."
            yield CommunityState.show_forum_toast(
                "That discussion is no longer available."
            )

    @rx.event
    def open_topic(self, topic_id: int):
        self.error = ""
        self.success = ""
        self.comment_draft = ""
        self.comment_version += 1
        from app.states.notification_state import NotificationState

        for topic in self.topics:
            if topic["id"] == topic_id:
                self.selected_topic = topic
                # Only this topic's notices are cleared.
                return [
                    CommunityState.load_comments,
                    NotificationState.mark_topic_read(int(topic_id)),
                ]
        self.selected_topic = EMPTY_TOPIC
        self.comments = []
        self.error = "That discussion is no longer on the board."
        return None

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_topics(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            open_id = self.selected_topic["id"]
            subject_filters = list(self.selected_subject_filters)
        if not sid.isdigit():
            async with self:
                self.topics = []
                self.selected_topic = EMPTY_TOPIC
                self.comments = []
                self.error = "Please sign in to join the community board."
            return
        async with self:
            self.is_loading = True
            self.error = ""

        # Busiest discussion first (most replies), then newest. Every value
        # below is a bound parameter — no user text touches the SQL.
        params: dict[str, str | int] = {"sid": int(sid)}
        # Directional hiding: discussions started by members this viewer
        # blocked never reach their board.
        where_sql = (
            "WHERE NOT EXISTS ("
            "    SELECT 1 FROM skillkind_member_block mb"
            "     WHERE mb.blocker_id = :sid AND mb.blocked_id = t.author_id)"
        )
        if subject_filters:
            # Every chosen subject is bound, never interpolated.
            keys = []
            for index, subject in enumerate(subject_filters):
                key = f"f{index}"
                keys.append(f":{key}")
                params[key] = subject
            where_sql += f" AND t.subject_category IN ({', '.join(keys)})"

        async with rx.asession() as asession:
            premium, topics_used, comments_used, _ = await forum_usage(
                asession, int(sid)
            )
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT t.id, t.title, t.body, t.created_at,
                               a.id, a.display_name, CONCAT('member-', a.id),
                               COALESCE(pr.username, ''),
                               COALESCE(pr.avatar_path, ''),
                               (SELECT COUNT(*)
                                  FROM skillkind_community_comment c
                                 WHERE c.topic_id = t.id
                                   AND NOT EXISTS (
                                       SELECT 1
                                         FROM skillkind_member_block mbc
                                        WHERE mbc.blocker_id = :sid
                                          AND mbc.blocked_id = c.author_id)),
                               COALESCE(t.subject_category, 'Other'),
                               COALESCE(a.is_verified, FALSE)
                        FROM skillkind_community_topic t
                        JOIN skillkind_subscriber a ON a.id = t.author_id
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = a.id
                        {where_sql}
                        ORDER BY (SELECT COUNT(*)
                                    FROM skillkind_community_comment c2
                                   WHERE c2.topic_id = t.id
                                     AND NOT EXISTS (
                                         SELECT 1
                                           FROM skillkind_member_block mbo
                                          WHERE mbo.blocker_id = :sid
                                            AND mbo.blocked_id
                                                = c2.author_id)) DESC,
                                 t.created_at DESC
                        LIMIT 50
                        """
                    ),
                    params,
                )
            ).all()

        loaded: list[TopicItem] = [
            {
                "id": int(r[0]),
                "title": str(r[1] or ""),
                "subject": str(r[10] or COMMUNITY_SUBJECT_OTHER),
                "subject_icon": COMMUNITY_SUBJECT_ICONS.get(
                    str(r[10] or COMMUNITY_SUBJECT_OTHER), "circle-ellipsis"
                ),
                "body": str(r[2] or ""),
                "preview": str(r[2] or "")[:240],
                "author_id": int(r[4]),
                "author_name": str(r[5] or "A Go and Help neighbour"),
                "author_avatar_seed": str(r[6] or ""),
                "author_handle": f"@{r[7]}" if str(r[7] or "") else "",
                "author_avatar": str(r[8] or ""),
                "author_verified": bool(r[11]),
                "created": _fmt_stamp(r[3]),
                "comment_count": int(r[9] or 0),
                "mine": int(r[4]) == int(sid),
            }
            for r in rows
        ]
        match = [t for t in loaded if t["id"] == open_id]
        async with self:
            self._set_usage(premium, topics_used, comments_used)
            self.topics = loaded
            self.selected_topic = match[0] if match else EMPTY_TOPIC
            if not match:
                self.comments = []
            self.is_loading = False
        if match:
            yield CommunityState.load_comments

    @rx.event(background=True)
    async def load_comments(self):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id if auth.is_signed_in else ""
            topic_id = self.selected_topic["id"]
        if not sid.isdigit() or topic_id <= 0:
            async with self:
                self.comments = []
            return
        async with self:
            self.is_loading_topic = True

        async with rx.asession() as asession:
            premium, topics_used, comments_used, _ = await forum_usage(
                asession, int(sid)
            )
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, c.body, c.created_at,
                               a.id, a.display_name, CONCAT('member-', a.id),
                               COALESCE(pr.username, ''),
                               COALESCE(pr.avatar_path, ''),
                               COALESCE(a.is_verified, FALSE)
                        FROM skillkind_community_comment c
                        JOIN skillkind_subscriber a ON a.id = c.author_id
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = a.id
                        WHERE c.topic_id = :tid
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE mb.blocker_id = :sid
                                AND mb.blocked_id = c.author_id
                          )
                        ORDER BY c.created_at ASC
                        LIMIT 300
                        """
                    ),
                    {"tid": int(topic_id), "sid": int(sid)},
                )
            ).all()

        loaded: list[CommentItem] = [
            {
                "id": int(r[0]),
                "author_id": int(r[3]),
                "author_name": str(r[4] or "A Go and Help neighbour"),
                "author_avatar_seed": str(r[5] or ""),
                "author_handle": f"@{r[6]}" if str(r[6] or "") else "",
                "author_avatar": str(r[7] or ""),
                "author_verified": bool(r[8]),
                "body": str(r[1] or ""),
                "created": _fmt_stamp(r[2]),
                "mine": int(r[3]) == int(sid),
            }
            for r in rows
        ]
        async with self:
            self._set_usage(premium, topics_used, comments_used)
            self.comments = loaded
            self.is_loading_topic = False

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def create_topic(self):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id if auth.is_signed_in else ""
            title = self.title_draft.strip()
            body = self.body_draft.strip()
            subject = self.subject_draft.strip()
        # The subject is decided on the server: anything unknown is refused.
        if subject not in SUBJECT_ORDER:
            async with self:
                self.is_posting = False
                self.error = "Choose one of the pinned subjects first."
                self.success = ""
            return
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif not title and subject == COMMUNITY_SUBJECT_OTHER:
            problem = (
                "Subjects filed under Other need your own title so the board "
                "knows what it is about."
            )
        elif not title:
            problem = "Give your discussion a title."
        elif len(title) > COMMUNITY_TOPIC_TITLE_MAX_LENGTH:
            problem = (
                "Titles can be at most "
                f"{COMMUNITY_TOPIC_TITLE_MAX_LENGTH} characters."
            )
        elif not body:
            problem = "Write a few words so people know what you mean."
        elif _word_count(body) > COMMUNITY_TOPIC_MAX_WORDS:
            problem = (
                "That post is longer than "
                f"{COMMUNITY_TOPIC_MAX_WORDS} words — please shorten it."
            )
        if problem:
            async with self:
                self.is_posting = False
                self.is_commenting = False
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_posting = True
            self.error = ""
            self.success = ""

        try:
            async with rx.asession() as asession:
                premium, topics, comments, stamp = await forum_usage(
                    asession, int(sid), lock=True
                )
                if not premium and topics >= 1:
                    await asession.rollback()
                    async with self:
                        self._set_usage(premium, topics, comments)
                        await self._quota_rejected(True)
                    return
                await asession.execute(
                    text("""
                        INSERT INTO skillkind_community_topic
                            (author_id, title, body, subject_category, created_at)
                        VALUES (:sid, :title, :body, :subject, :stamp)
                    """),
                    {
                        "sid": int(sid),
                        "title": title,
                        "body": body,
                        "subject": subject,
                        "stamp": stamp,
                    },
                )
                await asession.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_posting = False
                self.error = "We couldn't post your discussion. Your draft is saved here; please try again."
            return

        async with self:
            self._set_usage(premium, topics + 1, comments)
            self.is_posting = False
            self.title_draft = ""
            self.body_draft = ""
            self.subject_draft = ""
            self.draft_version += 1
            self.composer_open = False
            self.success = "Your discussion is pinned to the board."
        yield CommunityState.show_forum_toast("Discussion posted.")
        yield CommunityState.load_topics

    @rx.event(background=True)
    async def add_comment(self):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id if auth.is_signed_in else ""
            topic_id = self.selected_topic["id"]
            body = self.comment_draft.strip()
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif topic_id <= 0:
            problem = "Open a discussion first."
        elif not body:
            problem = "Write your reply before posting."
        elif _word_count(body) > COMMUNITY_COMMENT_MAX_WORDS:
            problem = (
                f"Comments are limited to {COMMUNITY_COMMENT_MAX_WORDS} words."
            )
        if problem:
            async with self:
                self.is_commenting = False
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_commenting = True
            self.error = ""
            self.success = ""

        try:
            async with rx.asession() as asession:
                premium, topics, comments, stamp = await forum_usage(
                    asession, int(sid), lock=True
                )
                if not premium and comments >= 10:
                    await asession.rollback()
                    async with self:
                        self._set_usage(premium, topics, comments)
                        await self._quota_rejected(False)
                    return
                exists = (
                    await asession.execute(
                        text("""
                    SELECT id, author_id, title FROM skillkind_community_topic
                    WHERE id = :tid
                """),
                        {"tid": int(topic_id)},
                    )
                ).first()
                if exists is None:
                    await asession.rollback()
                    async with self:
                        self.is_commenting = False
                        self.error = (
                            "That discussion is no longer on the board."
                        )
                    yield CommunityState.load_topics
                    return
                if await are_members_blocked(
                    asession, int(sid), int(exists[1])
                ):
                    await asession.rollback()
                    async with self:
                        self.is_commenting = False
                        self.comment_draft = ""
                        self.comment_version += 1
                        self.selected_topic = EMPTY_TOPIC
                        self.comments = []
                        self.error = BLOCK_UNAVAILABLE_MESSAGE
                    yield CommunityState.load_topics
                    return
                await asession.execute(
                    text("""
                    INSERT INTO skillkind_community_comment
                        (topic_id, author_id, body, created_at)
                    VALUES (:tid, :sid, :body, :stamp)
                """),
                    {
                        "tid": int(topic_id),
                        "sid": int(sid),
                        "body": body,
                        "stamp": stamp,
                    },
                )
                author_id = int(exists[1])
                if author_id != int(sid):
                    await asession.execute(
                        text("""
                        INSERT INTO skillkind_member_notification
                            (recipient_id, kind, title, body, actor_id,
                             community_topic_id, target_route)
                        VALUES (:author, 'community_reply', :title, :body,
                                :sid, :tid, '')
                    """),
                        {
                            "author": author_id,
                            "sid": int(sid),
                            "tid": int(topic_id),
                            "title": "New reply on your discussion",
                            "body": body[:255],
                        },
                    )
                await asession.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_commenting = False
                self.error = "We couldn't post your reply. Your draft is saved here; please try again."
            return

        async with self:
            self._set_usage(premium, topics, comments + 1)
            self.is_commenting = False
            self.comment_draft = ""
            self.comment_version += 1
            self.success = "Your reply is on the board."
        yield CommunityState.load_comments
        yield CommunityState.load_topics
