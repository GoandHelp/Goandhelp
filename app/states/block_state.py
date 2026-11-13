"""Private member blocking: the Block / Unblock workflow.

Backed by `skillkind_member_block` (directional `blocker_id` -> `blocked_id`).

Nothing here ever notifies or informs the blocked member: there is no message,
no notification row, and no state the other side can read. The private list is
strictly directional — it only ever returns rows the signed-in member created,
never rows where somebody blocked them.
"""

from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.interface_i18n import translate
from app.member_blocks import is_valid_block_pair, normalize_member_id
from app.states.auth_state import AuthState


class BlockedMember(TypedDict):
    """One row of the signed-in member's own private block list."""

    id: int
    name: str
    handle: str
    avatar: str
    avatar_seed: str
    verified: bool
    blocked_on: str


def _fmt_date(value) -> str:
    return value.strftime("%b %d, %Y") if value is not None else ""


BLOCK_SUCCESS_COPY = (
    "Blocked. Their posts and comments are hidden from you, your "
    "conversations with them are closed, and neither of you can send "
    "contact requests or messages. They are not told about this."
)

UNBLOCK_SUCCESS_COPY = (
    "Unblocked. You'll see their posts again and you can both send contact "
    "requests and messages. Nothing deleted comes back."
)


class BlockState(rx.State):
    """One shared confirmation dialog plus the private Profile block list."""

    # Confirmation dialog.
    is_open: bool = False
    target_id: int = 0
    target_name: str = ""
    is_blocking: bool = False
    error: str = ""
    success: str = ""

    # Private list (Profile › Blocked members).
    blocked: list[BlockedMember] = []
    is_loading: bool = False
    list_error: str = ""
    list_success: str = ""
    unblocking_id: int = 0

    @rx.var
    def blocked_count_label(self) -> str:
        total = len(self.blocked)
        if total == 0:
            return "Private list — only you can see this."
        if total == 1:
            return "1 blocked member · private list — only you can see this."
        return (
            f"{total} blocked members · private list — only you can see this."
        )

    @rx.var
    def confirm_question(self) -> str:
        name = self.target_name.strip() or "this member"
        return f"Block {name}?"

    @rx.var
    async def localized_blocked_count_label(self) -> str:
        auth = await self.get_state(AuthState)
        total = len(self.blocked)
        if total == 0:
            source = "Private list — only you can see this."
            return translate(auth.preferred_language, source)
        if total == 1:
            source = "1 blocked member · private list — only you can see this."
            return translate(auth.preferred_language, source)
        source = (
            "{count} blocked members · private list — only you can see this."
        )
        return translate(auth.preferred_language, source).format(count=total)

    # ------------------------------------------------------------------
    # Confirmation dialog
    # ------------------------------------------------------------------

    @rx.event
    async def open_block(self, target_id: int, target_name: str = ""):
        member_id = normalize_member_id(target_id)
        me = normalize_member_id(
            (await self.get_state(AuthState)).subscriber_id
        )
        if not is_valid_block_pair(me, member_id):
            return
        self.is_open = True
        self.target_id = member_id
        self.target_name = (target_name or "").strip()[:120]
        self.error = ""
        self.success = ""

    @rx.event
    def close_block(self):
        self.is_open = False
        self.target_id = 0
        self.target_name = ""
        self.error = ""
        self.is_blocking = False

    @rx.event
    def clear_feedback(self):
        self.error = ""
        self.success = ""
        self.list_error = ""
        self.list_success = ""

    @rx.event(background=True)
    async def confirm_block(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            target_id = normalize_member_id(self.target_id)
        me = normalize_member_id(sid)
        problem = ""
        if not me:
            problem = "Please sign in to block someone."
        elif not is_valid_block_pair(me, target_id):
            problem = "We couldn't tell who to block."
        if problem:
            async with self:
                self.error = problem
                self.is_blocking = False
            return

        async with self:
            self.is_blocking = True
            self.error = ""
            self.success = ""

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM skillkind_subscriber
                        WHERE id = :tid AND is_active = TRUE
                        """
                    ),
                    {"tid": target_id},
                )
            ).first()
            if row is None:
                async with self:
                    self.is_blocking = False
                    self.error = "That member is no longer available."
                return
            # Conflict-safe: blocking twice is a no-op, never an error.
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_block
                        (blocker_id, blocked_id)
                    VALUES (:sid, :tid)
                    ON CONFLICT (blocker_id, blocked_id) DO NOTHING
                    """
                ),
                {"sid": me, "tid": target_id},
            )
            await asession.commit()

        async with self:
            self.is_blocking = False
            self.is_open = False
            self.target_id = 0
            self.target_name = ""
            self.success = BLOCK_SUCCESS_COPY
            self.list_success = ""
            await self._clear_stale_selections()
            language = (await self.get_state(AuthState)).preferred_language

        for event in self._refresh_events():
            yield event
        yield BlockState.load_blocked_members
        yield rx.toast(translate(language, BLOCK_SUCCESS_COPY), duration=6000)

    # ------------------------------------------------------------------
    # Shared helpers (never event handlers, never exposed to the frontend)
    # ------------------------------------------------------------------

    async def _clear_stale_selections(self):
        """Close anything on screen that pointed at the blocked member."""
        from app.states.community_state import EMPTY_TOPIC, CommunityState
        from app.states.contacts_state import EMPTY_CONTACT, ContactsState
        from app.states.discovery_state import (
            EMPTY_HELPER,
            EMPTY_POST,
            DiscoveryState,
        )
        from app.states.messaging_state import EMPTY_THREAD, MessagingState
        from app.states.noncontact_state import (
            EMPTY_CONVERSATION,
            NonContactMessagingState,
        )

        discovery = await self.get_state(DiscoveryState)
        discovery.selected_post = EMPTY_POST
        discovery.selected_helper = EMPTY_HELPER
        discovery.group_poster_id = 0

        community = await self.get_state(CommunityState)
        community.selected_topic = EMPTY_TOPIC
        community.comments = []

        contacts = await self.get_state(ContactsState)
        contacts.selected_contact = EMPTY_CONTACT
        contacts.contact_messages = []

        messaging = await self.get_state(MessagingState)
        messaging.selected_thread = EMPTY_THREAD

        noncontact = await self.get_state(NonContactMessagingState)
        noncontact.selected = EMPTY_CONVERSATION
        noncontact.messages = []
        noncontact.compose_target_id = 0
        noncontact.compose_target_name = ""

    def _refresh_events(self) -> list:
        """Reload every list that could still be showing hidden content."""
        from app.states.community_state import CommunityState
        from app.states.contacts_state import ContactsState
        from app.states.discovery_state import DiscoveryState
        from app.states.help_hub_state import HelpHubState
        from app.states.messaging_state import MessagingState
        from app.states.noncontact_state import NonContactMessagingState

        return [
            DiscoveryState.refresh_board,
            CommunityState.load_topics,
            ContactsState.load_contacts,
            NonContactMessagingState.load_conversations,
            MessagingState.load_threads,
            HelpHubState.load_help_hub,
        ]

    # ------------------------------------------------------------------
    # The private list
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_blocked_members(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        me = normalize_member_id(sid)
        if not me:
            async with self:
                self.blocked = []
                self.is_loading = False
            return
        async with self:
            self.is_loading = True
            self.list_error = ""

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT b.blocked_id,
                               COALESCE(s.display_name, ''),
                               COALESCE(pr.username, ''),
                               COALESCE(pr.avatar_path, ''),
                               CONCAT('member-', s.id),
                               COALESCE(s.is_verified, FALSE),
                               b.created_at
                        FROM skillkind_member_block b
                        JOIN skillkind_subscriber s ON s.id = b.blocked_id
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = s.id
                        WHERE b.blocker_id = :sid
                        ORDER BY b.created_at DESC, b.blocked_id DESC
                        LIMIT 200
                        """
                    ),
                    {"sid": me},
                )
            ).all()

        loaded: list[BlockedMember] = [
            {
                "id": int(r[0]),
                "name": str(r[1] or "A Go and Help member"),
                "handle": f"@{r[2]}" if str(r[2] or "") else "",
                "avatar": str(r[3] or ""),
                "avatar_seed": str(r[4] or ""),
                "verified": bool(r[5]),
                "blocked_on": _fmt_date(r[6]),
            }
            for r in rows
        ]
        async with self:
            self.blocked = loaded
            self.is_loading = False

    @rx.event(background=True)
    async def unblock_member(self, target_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        me = normalize_member_id(sid)
        member_id = normalize_member_id(target_id)
        if not is_valid_block_pair(me, member_id):
            async with self:
                self.list_error = "We couldn't tell who to unblock."
            return
        async with self:
            self.unblocking_id = member_id
            self.list_error = ""
            self.list_success = ""

        async with rx.asession() as asession:
            result = await asession.execute(
                text(
                    """
                    DELETE FROM skillkind_member_block
                    WHERE blocker_id = :sid AND blocked_id = :tid
                    """
                ),
                {"sid": me, "tid": member_id},
            )
            await asession.commit()
        removed = int(result.rowcount or 0)

        async with self:
            self.unblocking_id = 0
            if removed:
                self.list_success = UNBLOCK_SUCCESS_COPY
                language = (await self.get_state(AuthState)).preferred_language
            else:
                self.list_error = "That member wasn't on your blocked list."
                language = "en"

        yield BlockState.load_blocked_members
        if removed:
            for event in self._refresh_events():
                yield event
            yield rx.toast(
                translate(language, UNBLOCK_SUCCESS_COPY), duration=6000
            )
