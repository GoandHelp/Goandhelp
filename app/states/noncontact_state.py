"""Replyable messaging between members who are not contacts.

Backed by `skillkind_noncontact_conversation` and
`skillkind_noncontact_message`. Every read and write re-checks server-side that
the signed-in member is one of the two participants.
"""

import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text
from app.message_photos import decode_message, message_preview

from app.member_blocks import BLOCK_UNAVAILABLE_MESSAGE, are_members_blocked
from app.models import (
    NONCONTACT_CONVERSATION_STATUS_LABELS,
    NONCONTACT_STATUS_OPEN,
    NONCONTACT_STATUS_REPLIED,
)
from app.states.auth_state import AuthState

MAX_MESSAGE_LENGTH = 2000
PREVIEW_LENGTH = 255


class NonContactItem(TypedDict):
    conv_id: int
    other_id: int
    other_name: str
    other_avatar_seed: str
    other_avatar: str
    other_handle: str
    other_verified: bool
    status: str
    status_label: str
    message_count: int
    last_preview: str
    last_at: str
    unread_count: int
    i_started: bool


class NonContactMessageItem(TypedDict):
    id: int
    sender_id: int
    sender_name: str
    body: str
    photos: list[str]
    sent_at: str
    mine: bool


EMPTY_CONVERSATION: NonContactItem = {
    "conv_id": 0,
    "other_id": 0,
    "other_name": "",
    "other_avatar_seed": "",
    "other_avatar": "",
    "other_handle": "",
    "other_verified": False,
    "status": "",
    "status_label": "",
    "message_count": 0,
    "last_preview": "",
    "last_at": "",
    "unread_count": 0,
    "i_started": False,
}


def _fmt_stamp(value) -> str:
    return value.strftime("%b %d, %Y · %H:%M") if value is not None else ""


class NonContactMessagingState(rx.State):
    """Inline compose from search results, plus the Inbox reply thread."""

    # Which searched person currently has the inline compose form open.
    compose_target_id: int = 0
    compose_target_name: str = ""
    is_sending: bool = False

    conversations: list[NonContactItem] = []
    selected: NonContactItem = EMPTY_CONVERSATION
    messages: list[NonContactMessageItem] = []

    is_loading: bool = False
    is_loading_messages: bool = False
    error: str = ""
    success: str = ""

    @rx.var
    def has_selection(self) -> bool:
        return self.selected["conv_id"] > 0

    @rx.var
    def unread_total(self) -> int:
        return sum(item["unread_count"] for item in self.conversations)

    @rx.var
    def conversation_count_label(self) -> str:
        total = len(self.conversations)
        return "1 thread" if total == 1 else f"{total} threads"

    # ------------------------------------------------------------------
    # Inline compose from a search / profile card
    # ------------------------------------------------------------------

    @rx.event
    def open_compose(self, person_id: int, person_name: str = ""):
        self.error = ""
        self.success = ""
        if self.compose_target_id == person_id:
            self.compose_target_id = 0
            self.compose_target_name = ""
            return
        self.compose_target_id = person_id
        self.compose_target_name = person_name

    @rx.event
    def close_compose(self):
        self.compose_target_id = 0
        self.compose_target_name = ""
        self.error = ""

    @rx.event
    def clear_selection(self):
        from app.states.message_attachment_state import MessageAttachmentState

        self.selected = EMPTY_CONVERSATION
        self.messages = []
        return MessageAttachmentState.clear_pending

    @rx.event
    def clear_feedback(self):
        self.error = ""
        self.success = ""

    async def _resolve_pair(
        self, asession, sid: int, other_id: int
    ) -> int | None:
        """Return the conversation id for this unordered pair, creating it."""
        found = (
            await asession.execute(
                text(
                    """
                    SELECT id FROM skillkind_noncontact_conversation
                    WHERE least(initiator_id, recipient_id)
                              = least(:a, :b)
                      AND greatest(initiator_id, recipient_id)
                              = greatest(:a, :b)
                    """
                ),
                {"a": sid, "b": other_id},
            )
        ).first()
        if found is not None:
            return int(found[0])
        created = (
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_noncontact_conversation
                        (initiator_id, recipient_id, status, is_open,
                         message_count)
                    VALUES (:sid, :other, :status, TRUE, 0)
                    RETURNING id
                    """
                ),
                {
                    "sid": sid,
                    "other": other_id,
                    "status": NONCONTACT_STATUS_OPEN,
                },
            )
        ).first()
        return int(created[0]) if created is not None else None

    async def _post_message(
        self, asession, conv_id: int, sid: int, other_id: int, body: str
    ) -> None:
        """Insert one message and refresh the conversation's preview fields."""
        await asession.execute(
            text(
                """
                INSERT INTO skillkind_noncontact_message
                    (conversation_id, sender_id, recipient_id, body)
                VALUES (:cid, :sid, :other, :body)
                """
            ),
            {
                "cid": conv_id,
                "sid": sid,
                "other": other_id,
                "body": body,
            },
        )
        await asession.execute(
            text(
                """
                UPDATE skillkind_noncontact_conversation
                SET message_count = message_count + 1,
                    last_message_preview = :preview,
                    last_message_sender_id = :sid,
                    last_message_at = now(),
                    updated_at = now(),
                    status = CASE WHEN initiator_id = :sid
                                  THEN status ELSE :replied END
                WHERE id = :cid
                """
            ),
            {
                "cid": conv_id,
                "sid": sid,
                "preview": message_preview(body)[:PREVIEW_LENGTH],
                "replied": NONCONTACT_STATUS_REPLIED,
            },
        )
        await asession.execute(
            text(
                """
                INSERT INTO skillkind_member_notification
                    (recipient_id, kind, title, body, actor_id,
                     noncontact_conversation_id, target_route)
                VALUES (:other, 'inbox_message', :title, :body, :sid, :cid, '')
                """
            ),
            {
                "other": other_id,
                "sid": sid,
                "cid": conv_id,
                "title": "New message in your Inbox",
                "body": message_preview(body)[:PREVIEW_LENGTH],
            },
        )

    @rx.event(background=True)
    async def send_first_message(self, form_data: dict[str, Any]):
        """Write to a person found in search, without becoming contacts."""
        body = str(form_data.get("body", "") or "").strip()
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            other_id = self.compose_target_id
        problem = ""
        if not sid.isdigit():
            problem = "Please sign in to send a message."
        elif other_id <= 0:
            problem = "Choose someone to write to first."
        elif int(sid) == other_id:
            problem = "You can't message yourself."
        elif not body:
            problem = "Write a few words before sending."
        elif len(body) > MAX_MESSAGE_LENGTH:
            problem = (
                f"Messages are limited to {MAX_MESSAGE_LENGTH} characters."
            )
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_sending = True
            self.error = ""
            self.success = ""
        conv_id = 0
        async with rx.asession() as asession:
            person = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM skillkind_subscriber
                        WHERE id = :other AND is_active = TRUE
                        """
                    ),
                    {"other": int(other_id)},
                )
            ).first()
            if person is None:
                async with self:
                    self.is_sending = False
                    self.error = "That member is no longer on Go and Help."
                return
            # Symmetric check inside this session, before any insert.
            if await are_members_blocked(asession, int(sid), int(other_id)):
                await asession.rollback()
                async with self:
                    self.is_sending = False
                    self.compose_target_id = 0
                    self.compose_target_name = ""
                    self.error = BLOCK_UNAVAILABLE_MESSAGE
                return
            resolved = await self._resolve_pair(
                asession, int(sid), int(other_id)
            )
            if resolved is None:
                async with self:
                    self.is_sending = False
                    self.error = "We couldn't open that conversation."
                return
            conv_id = resolved
            await self._post_message(
                asession, conv_id, int(sid), int(other_id), body
            )
            await asession.commit()
        async with self:
            self.is_sending = False
            self.compose_target_id = 0
            self.compose_target_name = ""
            self.success = "Message sent — their reply lands in your Inbox."
        yield NonContactMessagingState.open_in_inbox(conv_id)

    @rx.event
    async def open_in_inbox(self, conv_id: int):
        """Jump to Inbox › Contacts with this non-contact thread selected."""
        from app.states.contacts_state import EMPTY_CONTACT, ContactsState
        from app.states.messaging_state import EMPTY_THREAD, MessagingState
        from app.states.profile_state import ProfileState
        from app.states.unified_inbox_state import UnifiedInboxState

        profile = await self.get_state(ProfileState)
        unified = await self.get_state(UnifiedInboxState)
        unified.preserve_next_mount = profile.active_tab != "inbox"
        unified.view = "thread"
        profile.active_tab = "inbox"
        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        unified.selected_key = f"noncontact:{int(conv_id)}"
        messaging = await self.get_state(MessagingState)
        messaging.selected_thread = EMPTY_THREAD
        messaging.messages = []
        contacts = await self.get_state(ContactsState)
        contacts.selected_contact = EMPTY_CONTACT
        contacts.contact_messages = []
        return NonContactMessagingState.select_conversation(conv_id)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_conversations(self):
        """Every non-contact thread I take part in, newest activity first."""
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            if not sid.isdigit():
                self.conversations = []
                self.selected = EMPTY_CONVERSATION
                self.messages = []
                self.is_loading = False
                return
            self.is_loading = True
            self.error = ""
        try:
            await self._load_conversations_data(sid)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                self.error = (
                    "We couldn't load your conversations. Please try again."
                )

    async def _load_conversations_data(self, sid: str) -> None:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id,
                               CASE WHEN c.initiator_id = :sid
                                    THEN c.recipient_id
                                    ELSE c.initiator_id END AS other_id,
                               s.display_name, CONCAT('member-', s.id), s.is_verified,
                               COALESCE(p.avatar_path, ''),
                               COALESCE(p.username, ''),
                               c.status, COALESCE(c.message_count, 0),
                               COALESCE(c.last_message_preview, ''),
                               c.last_message_at,
                               (SELECT COUNT(*)
                                  FROM skillkind_noncontact_message m
                                 WHERE m.conversation_id = c.id
                                   AND m.recipient_id = :sid
                                   AND m.read_at IS NULL) AS unread,
                               (c.initiator_id = :sid) AS i_started
                        FROM skillkind_noncontact_conversation c
                        JOIN skillkind_subscriber s
                          ON s.id = CASE WHEN c.initiator_id = :sid
                                         THEN c.recipient_id
                                         ELSE c.initiator_id END
                        LEFT JOIN skillkind_profile p
                          ON p.subscriber_id = s.id
                        WHERE (c.initiator_id = :sid OR c.recipient_id = :sid)
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = c.initiator_id
                                     AND mb.blocked_id = c.recipient_id)
                                 OR (mb.blocker_id = c.recipient_id
                                     AND mb.blocked_id = c.initiator_id)
                          )
                        ORDER BY c.last_message_at DESC NULLS LAST, c.id DESC
                        LIMIT 100
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
        loaded: list[NonContactItem] = [
            {
                "conv_id": int(r[0]),
                "other_id": int(r[1]),
                "other_name": str(r[2] or "A Go and Help member"),
                "other_avatar_seed": str(r[3] or ""),
                "other_verified": bool(r[4]),
                "other_avatar": str(r[5] or ""),
                "other_handle": (f"@{r[6]}" if r[6] else ""),
                "status": str(r[7] or ""),
                "status_label": NONCONTACT_CONVERSATION_STATUS_LABELS.get(
                    str(r[7] or ""), "Not a contact yet"
                ),
                "message_count": int(r[8] or 0),
                "last_preview": message_preview(r[9]),
                "last_at": _fmt_stamp(r[10]),
                "unread_count": int(r[11] or 0),
                "i_started": bool(r[12]),
            }
            for r in rows
        ]
        async with self:
            self.conversations = loaded
            current = self.selected["conv_id"]
            match = [c for c in loaded if c["conv_id"] == current]
            self.selected = match[0] if match else EMPTY_CONVERSATION
            if not match:
                self.messages = []
            self.is_loading = False

    @rx.event
    def select_conversation(self, conv_id: int):
        self.error = ""
        self.success = ""
        match = [c for c in self.conversations if c["conv_id"] == conv_id]
        self.selected = (
            match[0]
            if match
            else {**EMPTY_CONVERSATION, "conv_id": int(conv_id)}
        )
        self.messages = []
        return NonContactMessagingState.load_messages

    @rx.event(background=True)
    async def load_messages(self):
        """Load one thread's history and mark my incoming messages read."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            conv_id = self.selected["conv_id"]
        if not sid.isdigit() or conv_id <= 0:
            async with self:
                self.messages = []
            return
        async with self:
            self.is_loading_messages = True
        async with rx.asession() as asession:
            allowed = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM skillkind_noncontact_conversation c
                        WHERE c.id = :cid
                          AND (c.initiator_id = :sid OR c.recipient_id = :sid)
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = c.initiator_id
                                     AND mb.blocked_id = c.recipient_id)
                                 OR (mb.blocker_id = c.recipient_id
                                     AND mb.blocked_id = c.initiator_id)
                          )
                        """
                    ),
                    {"cid": int(conv_id), "sid": int(sid)},
                )
            ).first()
            if allowed is None:
                async with self:
                    self.is_loading_messages = False
                    self.messages = []
                    self.selected = EMPTY_CONVERSATION
                    self.error = "That conversation isn't available to you."
                return
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT m.id, m.sender_id, s.display_name, m.body,
                               m.created_at
                        FROM skillkind_noncontact_message m
                        JOIN skillkind_subscriber s ON s.id = m.sender_id
                        WHERE m.conversation_id = :cid
                        ORDER BY m.created_at ASC, m.id ASC
                        LIMIT 200
                        """
                    ),
                    {"cid": int(conv_id)},
                )
            ).all()
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_noncontact_message
                    SET read_at = now()
                    WHERE conversation_id = :cid
                      AND recipient_id = :sid
                      AND read_at IS NULL
                    """
                ),
                {"cid": int(conv_id), "sid": int(sid)},
            )
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_member_notification
                    SET is_read = true, read_at = now()
                    WHERE recipient_id = :sid
                      AND noncontact_conversation_id = :cid
                      AND is_read = false
                    """
                ),
                {"cid": int(conv_id), "sid": int(sid)},
            )
            await asession.commit()
        loaded: list[NonContactMessageItem] = [
            {
                "id": int(r[0]),
                "sender_id": int(r[1]),
                "sender_name": str(r[2] or ""),
                **decode_message(r[3]),
                "sent_at": _fmt_stamp(r[4]),
                "mine": int(r[1]) == int(sid),
            }
            for r in rows
        ]
        async with self:
            opened = (
                self.selected["conv_id"] == conv_id
                and (await self.get_state(AuthState)).subscriber_id == sid
            )
            if opened:
                self.messages = loaded
            self.is_loading_messages = False
        from app.states.notification_state import NotificationState
        from app.states.unified_inbox_state import UnifiedInboxState

        if opened:
            yield UnifiedInboxState.mark_opened(f"noncontact:{conv_id}", sid)
        yield NotificationState.load_notifications

    # ------------------------------------------------------------------
    # Replies
    # ------------------------------------------------------------------

    @rx.event
    async def send_reply(self, form_data: dict[str, Any]):
        from app.states.message_attachment_state import MessageAttachmentState
        from app.states.unified_inbox_state import UnifiedInboxState

        if self.is_sending:
            return
        body = str(form_data.get("body", "") or "").strip()
        attachments = await self.get_state(MessageAttachmentState)
        sid = (await self.get_state(AuthState)).subscriber_id
        problem = ""
        if not sid.isdigit():
            problem = "Please sign in to reply."
        elif self.selected["conv_id"] <= 0:
            problem = "Open a conversation first."
        elif not body and not attachments.pending:
            problem = "Write a few words before sending."
        elif len(body) > MAX_MESSAGE_LENGTH:
            problem = (
                f"Messages are limited to {MAX_MESSAGE_LENGTH} characters."
            )
        if problem:
            self.error = problem
            self.success = ""
            return
        self.is_sending = True
        self.error = ""
        self.success = ""
        try:
            await attachments._persist(
                "noncontact",
                self.selected["conv_id"],
                body,
                expected_key=str(form_data.get("conversation_key", "")),
            )
            self.success = "Reply sent."
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "We couldn't send your reply. Please try again."
            )
            return
        finally:
            self.is_sending = False
        yield NonContactMessagingState.load_messages
        yield NonContactMessagingState.load_conversations
        yield UnifiedInboxState.load_index
