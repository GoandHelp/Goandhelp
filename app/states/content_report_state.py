"""Reporting unsafe content anywhere in Go and Help.

Backed by `skillkind_content_report`. The completed-job `SafetyReport` flow is
untouched. Every field the reporter cannot be trusted with — who is being
reported, what the content says — is resolved server-side from the target row.
"""

from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text
from app.message_photos import message_preview

from app.models import (
    CONTENT_REPORT_TARGET_LABELS,
    CONTENT_REPORT_TARGET_TYPES,
    REPORT_TARGET_COMMUNITY_COMMENT,
    REPORT_TARGET_COMMUNITY_TOPIC,
    REPORT_TARGET_CONTACT_MESSAGE,
    REPORT_TARGET_NONCONTACT_MESSAGE,
    REPORT_TARGET_PROFILE,
    REPORT_TARGET_JOB_MESSAGE,
    SAFETY_REPORT_CATEGORIES,
    SAFETY_REPORT_CATEGORY_LABELS,
    SAFETY_STATUS_OPEN,
)
from app.states.auth_state import AuthState

DETAILS_MIN_LENGTH = 20
DETAILS_MAX_LENGTH = 2000

REPORT_TITLE_SOURCES: dict[str, str] = {
    REPORT_TARGET_JOB_MESSAGE: "Report this help request",
    REPORT_TARGET_PROFILE: "Report this profile",
    REPORT_TARGET_COMMUNITY_TOPIC: "Report this community topic",
    REPORT_TARGET_COMMUNITY_COMMENT: "Report this community comment",
    REPORT_TARGET_CONTACT_MESSAGE: "Report this direct message",
    REPORT_TARGET_NONCONTACT_MESSAGE: "Report this non-contact message",
    "": "Report this content",
}

# target type -> (SQL returning author id + excerpt, needs recipient check)
_TARGET_QUERIES: dict[str, str] = {
    REPORT_TARGET_JOB_MESSAGE: """
        SELECT author_id, LEFT(COALESCE(title, ''), 500)
        FROM skillkind_help_post WHERE id = :tid
    """,
    REPORT_TARGET_PROFILE: """
        SELECT s.id, COALESCE(s.display_name, '')
        FROM skillkind_subscriber s
        WHERE s.id = :tid AND s.is_active = TRUE
    """,
    REPORT_TARGET_COMMUNITY_TOPIC: """
        SELECT author_id, LEFT(COALESCE(title, ''), 500)
        FROM skillkind_community_topic WHERE id = :tid
    """,
    REPORT_TARGET_COMMUNITY_COMMENT: """
        SELECT author_id, LEFT(COALESCE(body, ''), 500)
        FROM skillkind_community_comment WHERE id = :tid
    """,
    REPORT_TARGET_CONTACT_MESSAGE: """
        SELECT sender_id, COALESCE(body, '')
        FROM skillkind_contact_message
        WHERE id = :tid AND recipient_id = :sid
    """,
    REPORT_TARGET_NONCONTACT_MESSAGE: """
        SELECT sender_id, LEFT(COALESCE(body, ''), 500)
        FROM skillkind_noncontact_message
        WHERE id = :tid AND recipient_id = :sid
    """,
}


class CategoryOption(TypedDict):
    value: str
    label: str


CATEGORY_OPTIONS: list[CategoryOption] = [
    {"value": key, "label": SAFETY_REPORT_CATEGORY_LABELS.get(key, key)}
    for key in SAFETY_REPORT_CATEGORIES
]


class ContentReportState(rx.State):
    """One shared, compact report dialog reused across every surface."""

    is_open: bool = False
    target_type: str = ""
    target_id: int = 0
    target_label: str = ""
    target_hint: str = ""
    category: str = ""
    is_sending: bool = False
    error: str = ""
    success: str = ""

    category_options: list[CategoryOption] = CATEGORY_OPTIONS

    @rx.var
    def dialog_title(self) -> str:
        label = CONTENT_REPORT_TARGET_LABELS.get(self.target_type, "content")
        return f"Report this {label.lower()}"

    @rx.var
    async def localized_dialog_title(self) -> str:
        from app.interface_i18n import translate

        auth = await self.get_state(AuthState)
        source = REPORT_TITLE_SOURCES.get(
            self.target_type, "Report this content"
        )
        return translate(auth.preferred_language, source)

    @rx.event
    def open_report(
        self, target_type: str, target_id: int, target_hint: str = ""
    ):
        if target_type not in CONTENT_REPORT_TARGET_TYPES or target_id <= 0:
            return
        self.is_open = True
        self.target_type = target_type
        self.target_id = int(target_id)
        self.target_label = CONTENT_REPORT_TARGET_LABELS.get(
            target_type, "Content"
        )
        self.target_hint = (target_hint or "")[:160]
        self.category = ""
        self.error = ""
        self.success = ""

    @rx.event
    def close_report(self):
        self.is_open = False
        self.target_type = ""
        self.target_id = 0
        self.target_hint = ""
        self.category = ""
        self.error = ""

    @rx.event
    def set_category(self, value: str):
        self.category = value
        self.error = ""

    @rx.event(background=True)
    async def submit_report(self, form_data: dict[str, Any]):
        details = str(form_data.get("details", "") or "").strip()
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            target_type = self.target_type
            target_id = self.target_id
            category = self.category
        problem = ""
        if not sid.isdigit():
            problem = "Please sign in to report content."
        elif target_type not in _TARGET_QUERIES or target_id <= 0:
            problem = "We couldn't tell what you're reporting."
        elif category not in SAFETY_REPORT_CATEGORIES:
            problem = "Choose what kind of problem this is."
        elif len(details) < DETAILS_MIN_LENGTH:
            problem = (
                f"Please describe what happened in at least "
                f"{DETAILS_MIN_LENGTH} characters."
            )
        elif len(details) > DETAILS_MAX_LENGTH:
            problem = f"Please keep it under {DETAILS_MAX_LENGTH} characters."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_sending = True
            self.error = ""
            self.success = ""

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(_TARGET_QUERIES[target_type]),
                    {"tid": int(target_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.is_sending = False
                    self.error = (
                        "That content is no longer available to report."
                    )
                return
            reported_id = int(row[0])
            excerpt = str(row[1] or "")[:500]
            if target_type in {
                REPORT_TARGET_CONTACT_MESSAGE,
                REPORT_TARGET_NONCONTACT_MESSAGE,
            }:
                excerpt = message_preview(row[1])[:500]
            if reported_id == int(sid):
                async with self:
                    self.is_sending = False
                    self.error = "You can't report your own content."
                return
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM skillkind_content_report
                        WHERE reporter_id = :sid
                          AND target_type = :ttype
                          AND target_id = :tid
                        """
                    ),
                    {
                        "sid": int(sid),
                        "ttype": target_type,
                        "tid": int(target_id),
                    },
                )
            ).first()
            if existing is not None:
                async with self:
                    self.is_sending = False
                    self.error = (
                        "You've already reported this — our team can see it."
                    )
                return
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_content_report
                        (reporter_id, reported_id, target_type, target_id,
                         target_excerpt, category, details, status)
                    VALUES
                        (:sid, :reported, :ttype, :tid, :excerpt, :category,
                         :details, :status)
                    """
                ),
                {
                    "sid": int(sid),
                    "reported": reported_id,
                    "ttype": target_type,
                    "tid": int(target_id),
                    "excerpt": excerpt,
                    "category": category,
                    "details": details,
                    "status": SAFETY_STATUS_OPEN,
                },
            )
            await asession.commit()
        async with self:
            self.is_sending = False
            self.is_open = False
            self.target_type = ""
            self.target_id = 0
            self.category = ""
            self.success = (
                "Thank you — your report is private and with our safety team."
            )
        async with self:
            language = (await self.get_state(AuthState)).preferred_language
        from app.interface_i18n import translate

        yield rx.toast(
            translate(
                language,
                "Report sent privately to the Go and Help safety team.",
            ),
            duration=5000,
        )
