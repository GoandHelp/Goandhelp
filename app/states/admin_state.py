"""Admin-style backend activity view over all SkillKind records."""

import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.models import (
    CATEGORY_LABELS,
    MODERATION_STATUS_BANNED,
    MODERATION_STATUS_LABELS,
    MODERATION_STATUS_WARNED,
    SAFETY_REPORT_CATEGORY_LABELS,
    SAFETY_REPORT_STATUS_LABELS,
    SAFETY_SEVERE_CATEGORIES,
    SAFETY_STATUS_DISMISSED,
    SAFETY_STATUS_RESOLVED,
    SAFETY_STATUS_REVIEWING,
)
from app.states.auth_state import AuthState

ADMIN_NOTE_MAX = 1000


class AdminSummary(TypedDict):
    subscribers: int
    active_week: int
    posts: int
    posts_open: int
    posts_matched: int
    posts_completed: int
    applications: int
    accepted: int
    threads: int
    messages: int
    completed_tasks: int
    reviews: int
    open_reports: int
    flagged_members: int


EMPTY_SUMMARY: AdminSummary = {
    "subscribers": 0,
    "active_week": 0,
    "posts": 0,
    "posts_open": 0,
    "posts_matched": 0,
    "posts_completed": 0,
    "applications": 0,
    "accepted": 0,
    "threads": 0,
    "messages": 0,
    "completed_tasks": 0,
    "reviews": 0,
    "open_reports": 0,
    "flagged_members": 0,
}


class SafetyReportRow(TypedDict):
    """One line of the incident ledger, as an admin sees it."""

    id: int
    task_id: int
    job_title: str
    category: str
    category_label: str
    is_severe: bool
    details: str
    reporter: str
    reporter_email: str
    reported_id: int
    reported: str
    reported_email: str
    status: str
    status_label: str
    created: str
    one_star_count: int
    moderation_status: str
    moderation_label: str
    warning_count: int
    account_active: bool
    reviewer: str
    reviewed_at: str
    admin_note: str


class ContentReportRow(TypedDict):
    id: int
    target_type: str
    target_id: int
    excerpt: str
    category: str
    details: str
    reporter: str
    reported: str
    status: str
    created: str
    reviewed: str
    admin_note: str
    note_updated: str


class SubscriberRow(TypedDict):
    id: int
    name: str
    avatar_path: str
    email: str
    mode: str
    joined: str
    last_seen: str
    posts: int
    applications: int
    reviews: int
    kindness: int


class PostRow(TypedDict):
    id: int
    title: str
    author: str
    category: str
    reward: str
    city: str
    status: str
    urgency: str
    applicants: int
    created: str


class AcceptedRow(TypedDict):
    id: int
    title: str
    poster: str
    helper: str
    post_status: str
    accepted_at: str


class MessageRow(TypedDict):
    id: int
    thread_id: int
    title: str
    sender: str
    snippet: str
    sent_at: str
    read: bool


class TaskRow(TypedDict):
    id: int
    title: str
    poster: str
    helper: str
    minutes: int
    reward_given: str
    poster_confirmed: bool
    helper_confirmed: bool
    completed_at: str


class ReviewRow(TypedDict):
    id: int
    reviewer: str
    reviewee: str
    direction_label: str
    rating: int
    comment: str
    kindness_flag: bool
    created: str


class AdminState(rx.State):
    section: str = "subscribers"
    is_loading: bool = False
    summary: AdminSummary = EMPTY_SUMMARY
    avg_rating: float = 0.0

    # Safety review desk
    safety_reports: list[SafetyReportRow] = []
    content_reports: list[ContentReportRow] = []
    content_ban_confirm_id: int = 0
    admin_note: str = ""
    ban_confirm_id: int = 0
    is_moderating: bool = False
    moderation_error: str = ""
    moderation_success: str = ""

    subscribers: list[SubscriberRow] = []
    posts: list[PostRow] = []
    accepted_jobs: list[AcceptedRow] = []
    recent_messages: list[MessageRow] = []
    completed_tasks: list[TaskRow] = []
    reviews: list[ReviewRow] = []

    sections: list[dict[str, str]] = [
        {"value": "subscribers", "label": "Subscribers", "icon": "users-round"},
        {"value": "posts", "label": "Help posts", "icon": "notebook-pen"},
        {"value": "accepted", "label": "Accepted jobs", "icon": "hand-helping"},
        {"value": "messages", "label": "Messages", "icon": "send"},
        {"value": "tasks", "label": "Completed", "icon": "circle-check-big"},
        {"value": "reviews", "label": "Reviews", "icon": "star"},
        {"value": "safety", "label": "Safety review", "icon": "shield-alert"},
    ]

    @rx.event
    def set_section(self, value: str):
        self.section = value

    @rx.event
    def set_admin_note(self, value: str):
        self.admin_note = value[:ADMIN_NOTE_MAX]

    @rx.event
    def request_ban(self, report_id: int):
        self.ban_confirm_id = int(report_id)
        self.moderation_error = ""
        self.moderation_success = ""

    @rx.event
    def cancel_ban(self):
        self.ban_confirm_id = 0

    async def _verify_admin(self, sid: str) -> tuple[int, str]:
        """Return (admin subscriber id, problem). Zero id means not allowed.

        The database `is_admin` flag is the only authority here.
        """
        if not sid.isdigit():
            return 0, "Your session expired — please sign in again."
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT is_admin FROM skillkind_subscriber
                        WHERE id = :sid AND is_active = TRUE
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
        if row is None or not bool(row[0]):
            return 0, "Only an administrator can take moderation actions."
        return int(sid), ""

    async def _resolve_report(self, report_id: int) -> tuple[int, int, str]:
        """Return (report id, reported subscriber id, problem)."""
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT id, reported_id FROM skillkind_safety_report
                        WHERE id = :rid
                        """
                    ),
                    {"rid": int(report_id)},
                )
            ).first()
        if row is None:
            return 0, 0, "That report no longer exists."
        return int(row[0]), int(row[1]), ""

    @rx.event(background=True)
    async def warn_member(self, report_id: int):
        """Warn the reported member and keep the account active."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.admin_note.strip()[:ADMIN_NOTE_MAX]
        admin_id, problem = await self._verify_admin(sid)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        rid, reported_id, problem = await self._resolve_report(report_id)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        async with self:
            self.is_moderating = True
            self.moderation_error = ""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_subscriber
                    SET moderation_status = :status,
                        warning_count = warning_count + 1,
                        moderation_note = :note,
                        moderation_updated_at = now(),
                        is_active = TRUE
                    WHERE id = :reported
                    """
                ),
                {
                    "status": MODERATION_STATUS_WARNED,
                    "note": note,
                    "reported": reported_id,
                },
            )
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_safety_report
                    SET status = :status, reviewed_at = now(),
                        reviewed_by_id = :admin, admin_note = :note
                    WHERE id = :rid
                    """
                ),
                {
                    "status": SAFETY_STATUS_REVIEWING,
                    "admin": admin_id,
                    "note": note,
                    "rid": rid,
                },
            )
            await asession.commit()
        async with self:
            self.is_moderating = False
            self.ban_confirm_id = 0
            self.admin_note = ""
            self.moderation_success = (
                "Warning recorded. The account stays active and under review."
            )
        yield AdminState.load_activity

    @rx.event(background=True)
    async def ban_member(self, report_id: int):
        """Ban the reported member. Deliberately manual and confirmed."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.admin_note.strip()[:ADMIN_NOTE_MAX]
            confirmed = self.ban_confirm_id == int(report_id)
        admin_id, problem = await self._verify_admin(sid)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        if not confirmed:
            async with self:
                self.moderation_error = "Confirm the ban before it is applied."
            return
        rid, reported_id, problem = await self._resolve_report(report_id)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        async with self:
            self.is_moderating = True
            self.moderation_error = ""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_subscriber
                    SET moderation_status = :status,
                        is_active = FALSE,
                        moderation_note = :note,
                        moderation_updated_at = now()
                    WHERE id = :reported
                    """
                ),
                {
                    "status": MODERATION_STATUS_BANNED,
                    "note": note,
                    "reported": reported_id,
                },
            )
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_safety_report
                    SET status = :status, reviewed_at = now(),
                        reviewed_by_id = :admin, admin_note = :note
                    WHERE id = :rid
                    """
                ),
                {
                    "status": SAFETY_STATUS_RESOLVED,
                    "admin": admin_id,
                    "note": note,
                    "rid": rid,
                },
            )
            await asession.commit()
        async with self:
            self.is_moderating = False
            self.ban_confirm_id = 0
            self.admin_note = ""
            self.moderation_success = (
                "Account banned and deactivated. The report is resolved."
            )
        yield AdminState.load_activity

    @rx.event(background=True)
    async def dismiss_report(self, report_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.admin_note.strip()[:ADMIN_NOTE_MAX]
        admin_id, problem = await self._verify_admin(sid)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        rid, _reported, problem = await self._resolve_report(report_id)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        async with self:
            self.is_moderating = True
            self.moderation_error = ""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_safety_report
                    SET status = :status, reviewed_at = now(),
                        reviewed_by_id = :admin, admin_note = :note
                    WHERE id = :rid
                    """
                ),
                {
                    "status": SAFETY_STATUS_DISMISSED,
                    "admin": admin_id,
                    "note": note,
                    "rid": rid,
                },
            )
            await asession.commit()
        async with self:
            self.is_moderating = False
            self.admin_note = ""
            self.ban_confirm_id = 0
            self.moderation_success = (
                "Report dismissed. No action taken against the account."
            )
        yield AdminState.load_activity

    @rx.event(background=True)
    async def resolve_report(self, report_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.admin_note.strip()[:ADMIN_NOTE_MAX]
        admin_id, problem = await self._verify_admin(sid)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        rid, _reported, problem = await self._resolve_report(report_id)
        if problem:
            async with self:
                self.moderation_error = problem
            return
        async with self:
            self.is_moderating = True
            self.moderation_error = ""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_safety_report
                    SET status = :status, reviewed_at = now(),
                        reviewed_by_id = :admin, admin_note = :note
                    WHERE id = :rid
                    """
                ),
                {
                    "status": SAFETY_STATUS_RESOLVED,
                    "admin": admin_id,
                    "note": note,
                    "rid": rid,
                },
            )
            await asession.commit()
        async with self:
            self.is_moderating = False
            self.admin_note = ""
            self.ban_confirm_id = 0
            self.moderation_success = "Report marked resolved."
        yield AdminState.load_activity

    @rx.event
    async def request_content_ban(self, report_id: int):
        try:
            sid = (await self.get_state(AuthState)).subscriber_id
            _, problem = await self._verify_admin(sid)
            if problem:
                self.moderation_error = problem
                return
            self.content_ban_confirm_id = report_id
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.moderation_error = "Could not authorize this action."

    @rx.event
    def cancel_content_ban(self):
        self.content_ban_confirm_id = 0

    @rx.event(background=True)
    async def moderate_content(self, report_id: int, action: str):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.admin_note.strip()[:ADMIN_NOTE_MAX]
            confirmed = self.content_ban_confirm_id == report_id
        if action not in ("reviewing", "resolved", "dismissed", "warn", "ban"):
            return
        try:
            async with rx.asession() as session:
                admin = (
                    await session.execute(
                        text(
                            "SELECT id FROM skillkind_subscriber WHERE id = :sid AND is_admin = TRUE AND is_active = TRUE FOR UPDATE"
                        ),
                        {"sid": int(sid) if sid.isdigit() else 0},
                    )
                ).first()
                if admin is None:
                    raise ValueError(
                        "Only an administrator can moderate reports."
                    )
                if action == "ban" and not confirmed:
                    raise ValueError("Confirm the ban before applying it.")
                report = (
                    await session.execute(
                        text(
                            "SELECT reported_id FROM skillkind_content_report WHERE id = :rid FOR UPDATE"
                        ),
                        {"rid": report_id},
                    )
                ).first()
                if report is None:
                    raise ValueError("That report no longer exists.")
                if action in ("warn", "ban"):
                    if report[0] is None:
                        raise ValueError(
                            "The reported account no longer exists."
                        )
                    account = (
                        await session.execute(
                            text(
                                "SELECT is_admin, moderation_status FROM skillkind_subscriber WHERE id = :sid FOR UPDATE"
                            ),
                            {"sid": int(report[0])},
                        )
                    ).first()
                    if account is None or bool(account[0]):
                        raise ValueError(
                            "This account cannot be moderated here."
                        )
                    if action == "warn" and str(account[1]) == "banned":
                        raise ValueError(
                            "A warning cannot reactivate a banned account."
                        )
                    await session.execute(
                        text("""
                        UPDATE skillkind_subscriber SET moderation_status = :status,
                            warning_count = COALESCE(warning_count, 0) + :increment,
                            is_active = CASE WHEN :ban THEN FALSE ELSE is_active END,
                            moderation_note = :note, moderation_updated_at = now()
                        WHERE id = :sid
                    """),
                        {
                            "sid": int(report[0]),
                            "status": "banned" if action == "ban" else "warned",
                            "increment": 1 if action == "warn" else 0,
                            "ban": action == "ban",
                            "note": note,
                        },
                    )
                status = {"warn": "reviewing", "ban": "resolved"}.get(
                    action, action
                )
                await session.execute(
                    text("""
                    UPDATE skillkind_content_report SET status = :status,
                        reviewed_at = now(), reviewed_by_id = :admin,
                        admin_note = :note, admin_note_updated_at = now()
                    WHERE id = :rid
                """),
                    {
                        "status": status,
                        "admin": int(admin[0]),
                        "note": note,
                        "rid": report_id,
                    },
                )
                await session.commit()
            async with self:
                self.moderation_error = ""
                self.moderation_success = "Moderation decision saved."
                self.content_ban_confirm_id = 0
                self.admin_note = ""
            yield AdminState.load_activity
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.moderation_error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Could not save the moderation decision. Please try again."
                )
                self.moderation_success = ""

    @rx.event(background=True)
    async def load_activity(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        try:
            _, problem = await self._verify_admin(sid)
        except Exception as e:
            logging.exception(f"Error: {e}")
            problem = "Could not authorize this dashboard."
        if problem:
            async with self:
                self.summary = EMPTY_SUMMARY
                self.safety_reports = []
                self.content_reports = []
                self.subscribers = []
                self.posts = []
                self.accepted_jobs = []
                self.recent_messages = []
                self.completed_tasks = []
                self.reviews = []
                self.moderation_error = problem
                self.is_loading = False
            return
        async with self:
            self.is_loading = True

        async with rx.asession() as asession:
            summary_row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM skillkind_subscriber),
                            (SELECT COUNT(*) FROM skillkind_subscriber
                              WHERE last_seen_at >= now() - INTERVAL '7 days'),
                            (SELECT COUNT(*) FROM skillkind_help_post),
                            (SELECT COUNT(*) FROM skillkind_help_post WHERE status = 'open'),
                            (SELECT COUNT(*) FROM skillkind_help_post WHERE status = 'matched'),
                            (SELECT COUNT(*) FROM skillkind_help_post WHERE status = 'completed'),
                            (SELECT COUNT(*) FROM skillkind_job_application),
                            (SELECT COUNT(*) FROM skillkind_job_application WHERE status = 'accepted'),
                            (SELECT COUNT(*) FROM skillkind_message_thread),
                            (SELECT COUNT(*) FROM skillkind_message),
                            (SELECT COUNT(*) FROM skillkind_completed_task),
                            (SELECT COUNT(*) FROM skillkind_review),
                            (SELECT COALESCE(AVG(rating), 0) FROM skillkind_review),
                            ((SELECT COUNT(*) FROM skillkind_safety_report
                               WHERE status IN ('open', 'reviewing'))
                             + (SELECT COUNT(*) FROM skillkind_content_report
                                WHERE status IN ('open', 'reviewing'))),
                            (SELECT COUNT(*) FROM skillkind_subscriber
                              WHERE moderation_status <> 'clear')
                        """
                    )
                )
            ).first()
            safety_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT sr.id, sr.completed_task_id, p.title,
                               sr.category, sr.details, sr.status,
                               sr.created_at,
                               rep.display_name, rep.email,
                               sub.id, sub.display_name, sub.email,
                               COALESCE(sub.moderation_status, 'clear'),
                               COALESCE(sub.warning_count, 0),
                               sub.is_active,
                               (SELECT COUNT(*) FROM skillkind_review r
                                 WHERE r.reviewee_id = sub.id
                                   AND r.rating = 1),
                               COALESCE(adm.display_name, ''),
                               sr.reviewed_at,
                               COALESCE(sr.admin_note, '')
                        FROM skillkind_safety_report sr
                        JOIN skillkind_completed_task ct
                               ON ct.id = sr.completed_task_id
                        JOIN skillkind_help_post p ON p.id = ct.post_id
                        JOIN skillkind_subscriber rep ON rep.id = sr.reporter_id
                        JOIN skillkind_subscriber sub ON sub.id = sr.reported_id
                        LEFT JOIN skillkind_subscriber adm
                               ON adm.id = sr.reviewed_by_id
                        ORDER BY
                            CASE sr.status
                                WHEN 'open' THEN 0
                                WHEN 'reviewing' THEN 1
                                ELSE 2 END,
                            sr.created_at ASC
                        LIMIT 60
                        """
                    )
                )
            ).all()
            content_rows = (
                await asession.execute(
                    text("""
                SELECT cr.id, cr.target_type, cr.target_id, cr.target_excerpt,
                       cr.category, cr.details, rep.display_name,
                       COALESCE(sub.display_name, 'Deleted member'), cr.status,
                       cr.created_at, cr.reviewed_at, cr.admin_note,
                       cr.admin_note_updated_at
                FROM skillkind_content_report cr
                JOIN skillkind_subscriber rep ON rep.id = cr.reporter_id
                LEFT JOIN skillkind_subscriber sub ON sub.id = cr.reported_id
                ORDER BY CASE cr.status WHEN 'open' THEN 0 WHEN 'reviewing' THEN 1 ELSE 2 END,
                         cr.created_at ASC
                LIMIT 60
            """)
                )
            ).all()
            subscriber_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.display_name, s.email, s.help_mode,
                               s.joined_at, s.last_seen_at,
                               (SELECT COUNT(*) FROM skillkind_help_post p
                                 WHERE p.author_id = s.id),
                               (SELECT COUNT(*) FROM skillkind_job_application a
                                 WHERE a.helper_id = s.id),
                               (SELECT COUNT(*) FROM skillkind_review r
                                 WHERE r.reviewee_id = s.id),
                               COALESCE(pr.kindness_points, 0), COALESCE(pr.avatar_path, '')
                        FROM skillkind_subscriber s
                        LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
                        ORDER BY s.joined_at DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()
            post_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.title, s.display_name, p.category,
                               p.reward_type, p.city, p.status, p.urgency,
                               (SELECT COUNT(*) FROM skillkind_job_application a
                                 WHERE a.post_id = p.id),
                               p.created_at
                        FROM skillkind_help_post p
                        JOIN skillkind_subscriber s ON s.id = p.author_id
                        ORDER BY p.created_at DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()
            accepted_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, p.title, ps.display_name, hs.display_name,
                               p.status, COALESCE(a.responded_at, a.created_at)
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        JOIN skillkind_subscriber ps ON ps.id = p.author_id
                        JOIN skillkind_subscriber hs ON hs.id = a.helper_id
                        WHERE a.status = 'accepted'
                        ORDER BY COALESCE(a.responded_at, a.created_at) DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()
            message_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT m.id, m.thread_id, p.title, s.display_name,
                               m.body, m.sent_at, m.read_at
                        FROM skillkind_message m
                        JOIN skillkind_message_thread t ON t.id = m.thread_id
                        JOIN skillkind_help_post p ON p.id = t.post_id
                        JOIN skillkind_subscriber s ON s.id = m.sender_id
                        ORDER BY m.sent_at DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()
            task_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT ct.id, p.title, ps.display_name, hs.display_name,
                               ct.actual_duration_minutes, ct.reward_given,
                               ct.poster_confirmed, ct.helper_confirmed,
                               ct.completed_at
                        FROM skillkind_completed_task ct
                        JOIN skillkind_help_post p ON p.id = ct.post_id
                        JOIN skillkind_subscriber ps ON ps.id = ct.poster_id
                        JOIN skillkind_subscriber hs ON hs.id = ct.helper_id
                        ORDER BY ct.completed_at DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()
            review_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, rv.display_name, re.display_name,
                               r.direction, r.rating, r.comment,
                               r.kindness_flag, r.created_at
                        FROM skillkind_review r
                        JOIN skillkind_subscriber rv ON rv.id = r.reviewer_id
                        JOIN skillkind_subscriber re ON re.id = r.reviewee_id
                        ORDER BY r.created_at DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()

        async with self:
            if summary_row is not None:
                self.summary = {
                    "subscribers": int(summary_row[0] or 0),
                    "active_week": int(summary_row[1] or 0),
                    "posts": int(summary_row[2] or 0),
                    "posts_open": int(summary_row[3] or 0),
                    "posts_matched": int(summary_row[4] or 0),
                    "posts_completed": int(summary_row[5] or 0),
                    "applications": int(summary_row[6] or 0),
                    "accepted": int(summary_row[7] or 0),
                    "threads": int(summary_row[8] or 0),
                    "messages": int(summary_row[9] or 0),
                    "completed_tasks": int(summary_row[10] or 0),
                    "reviews": int(summary_row[11] or 0),
                    "open_reports": int(summary_row[13] or 0),
                    "flagged_members": int(summary_row[14] or 0),
                }
                self.avg_rating = float(summary_row[12] or 0)
            self.content_reports = [
                {
                    "id": int(row[0] or 0),
                    "target_type": str(row[1] or ""),
                    "target_id": int(row[2] or 0),
                    "excerpt": str(row[3] or ""),
                    "category": str(row[4] or ""),
                    "details": str(row[5] or ""),
                    "reporter": str(row[6] or ""),
                    "reported": str(row[7] or ""),
                    "status": str(row[8] or ""),
                    "created": row[9].strftime("%b %d, %Y · %H:%M")
                    if row[9] is not None
                    else "",
                    "reviewed": row[10].strftime("%b %d, %Y · %H:%M")
                    if row[10] is not None
                    else "",
                    "admin_note": str(row[11] or ""),
                    "note_updated": row[12].strftime("%b %d, %Y · %H:%M")
                    if row[12] is not None
                    else "",
                }
                for row in content_rows
            ]
            self.safety_reports = [
                {
                    "id": int(r[0]),
                    "task_id": int(r[1] or 0),
                    "job_title": str(r[2] or ""),
                    "category": str(r[3] or ""),
                    "category_label": SAFETY_REPORT_CATEGORY_LABELS.get(
                        str(r[3] or ""),
                        str(r[3] or "").replace("_", " ").capitalize(),
                    ),
                    "is_severe": str(r[3] or "") in SAFETY_SEVERE_CATEGORIES,
                    "details": str(r[4] or ""),
                    "status": str(r[5] or "open"),
                    "status_label": SAFETY_REPORT_STATUS_LABELS.get(
                        str(r[5] or "open"), str(r[5] or "open").title()
                    ),
                    "created": r[6].strftime("%b %d, %Y · %H:%M")
                    if r[6] is not None
                    else "",
                    "reporter": str(r[7] or ""),
                    "reporter_email": str(r[8] or ""),
                    "reported_id": int(r[9] or 0),
                    "reported": str(r[10] or ""),
                    "reported_email": str(r[11] or ""),
                    "moderation_status": str(r[12] or "clear"),
                    "moderation_label": MODERATION_STATUS_LABELS.get(
                        str(r[12] or "clear"), str(r[12] or "clear").title()
                    ),
                    "warning_count": int(r[13] or 0),
                    "account_active": bool(r[14]),
                    "one_star_count": int(r[15] or 0),
                    "reviewer": str(r[16] or ""),
                    "reviewed_at": r[17].strftime("%b %d, %Y")
                    if r[17] is not None
                    else "",
                    "admin_note": str(r[18] or ""),
                }
                for r in safety_rows
            ]
            self.subscribers = [
                {
                    "id": int(r[0]),
                    "name": str(r[1] or ""),
                    "avatar_path": str(r[10] or "") if len(r) > 10 else "",
                    "email": str(r[2] or ""),
                    "mode": str(r[3] or "both").replace("_", " "),
                    "joined": r[4].strftime("%b %d, %Y")
                    if r[4] is not None
                    else "",
                    "last_seen": r[5].strftime("%b %d · %H:%M")
                    if r[5] is not None
                    else "never",
                    "posts": int(r[6] or 0),
                    "applications": int(r[7] or 0),
                    "reviews": int(r[8] or 0),
                    "kindness": int(r[9] or 0),
                }
                for r in subscriber_rows
            ]
            self.posts = [
                {
                    "id": int(r[0]),
                    "title": str(r[1] or ""),
                    "author": str(r[2] or ""),
                    "category": CATEGORY_LABELS.get(
                        r[3] or "",
                        str(r[3] or "").replace("_", " ").title(),
                    ),
                    "reward": str(r[4] or "").replace("_", " "),
                    "city": str(r[5] or ""),
                    "status": str(r[6] or ""),
                    "urgency": str(r[7] or ""),
                    "applicants": int(r[8] or 0),
                    "created": r[9].strftime("%b %d, %Y")
                    if r[9] is not None
                    else "",
                }
                for r in post_rows
            ]
            self.accepted_jobs = [
                {
                    "id": int(r[0]),
                    "title": str(r[1] or ""),
                    "poster": str(r[2] or ""),
                    "helper": str(r[3] or ""),
                    "post_status": str(r[4] or ""),
                    "accepted_at": r[5].strftime("%b %d · %H:%M")
                    if r[5] is not None
                    else "",
                }
                for r in accepted_rows
            ]
            self.recent_messages = [
                {
                    "id": int(r[0]),
                    "thread_id": int(r[1]),
                    "title": str(r[2] or ""),
                    "sender": str(r[3] or ""),
                    "snippet": str(r[4] or "")[:140],
                    "sent_at": r[5].strftime("%b %d · %H:%M")
                    if r[5] is not None
                    else "",
                    "read": r[6] is not None,
                }
                for r in message_rows
            ]
            self.completed_tasks = [
                {
                    "id": int(r[0]),
                    "title": str(r[1] or ""),
                    "poster": str(r[2] or ""),
                    "helper": str(r[3] or ""),
                    "minutes": int(r[4] or 0),
                    "reward_given": str(r[5] or "—"),
                    "poster_confirmed": bool(r[6]),
                    "helper_confirmed": bool(r[7]),
                    "completed_at": r[8].strftime("%b %d, %Y")
                    if r[8] is not None
                    else "",
                }
                for r in task_rows
            ]
            self.reviews = [
                {
                    "id": int(r[0]),
                    "reviewer": str(r[1] or ""),
                    "reviewee": str(r[2] or ""),
                    "direction_label": "Poster → helper"
                    if str(r[3]) == "poster_to_helper"
                    else "Helper → poster",
                    "rating": int(r[4] or 0),
                    "comment": str(r[5] or ""),
                    "kindness_flag": bool(r[6]),
                    "created": r[7].strftime("%b %d, %Y")
                    if r[7] is not None
                    else "",
                }
                for r in review_rows
            ]
            self.is_loading = False
