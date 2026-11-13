"""One unified, server-backed conversation index for the Inbox.

It combines three existing conversation sources into a single feed:

* accepted contact conversations       -> type `contact`
* direct / non-contact conversations   -> type `contact`
* job message threads                 -> helper when I posted the request,
  helpee when I am helping; message direction is tracked separately.

Every query respects the same authorization the individual screens use and
excludes any pair with a member block in EITHER direction. Nothing is written
when opening an item: selection delegates to the existing events. Inbox removal
is a private, persistent dismissal and never deletes shared conversation history.
"""

import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text
from app.message_photos import message_preview, last_message_photo

from app.states.auth_state import AuthState

TYPE_FILTERS: list[dict[str, str]] = [
    {"value": "helper", "label": "Helpers", "icon": "hand"},
    {"value": "helpee", "label": "Helpees", "icon": "hand-helping"},
    {"value": "contact", "label": "Contacts", "icon": "users-round"},
]

TYPE_LABELS: dict[str, str] = {
    "contact": "Contact",
    "helper": "Helper",
    "helpee": "Helpee",
}


class UnifiedItem(TypedDict):
    """One collapsed conversation card in the unified feed."""

    key: str
    kind: str  # contact | noncontact | job
    conv_type: str  # contact | helper | helpee
    type_label: str
    ref_id: int
    other_id: int
    other_name: str
    other_initial: str
    other_avatar_seed: str
    other_avatar: str
    other_handle: str
    other_verified: bool
    preview: str
    last_photo: str
    last_at: str
    unread_count: int
    message_count: int
    context: str
    job_title: str
    job_status: str
    direction: str
    has_sent: bool
    has_received: bool


def safe_initial(name: str) -> str:
    value = name.strip()
    return value[0].upper()[:1] if value and value[0].isalnum() else "?"


def job_summary_copy(conv_type: str, title: str) -> str:
    if conv_type == "helper":
        return f"Offering you help for: “{title}”"
    return f"Asking you for help with: “{title}”"


def direction_flags(
    sent: bool, received: bool, count: int, initiated: bool
) -> tuple[bool, bool]:
    return sent or (count == 0 and initiated), received or (
        count == 0 and not initiated
    )


def job_type(i_posted: bool) -> str:
    return "helper" if i_posted else "helpee"


def _stamp(value) -> str:
    return value.strftime("%b %d · %H:%M") if value is not None else ""


def _sort_value(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value.timestamp())
    except Exception:
        logging.exception("Unexpected error")
        return 0.0


class UnifiedInboxState(rx.State):
    """Search, filter and open every conversation from one list."""

    view: str = "inbox"

    async def _workspace_allowed(self) -> bool:
        from app.states.profile_state import ProfileState

        auth = await self.get_state(AuthState)
        profile = await self.get_state(ProfileState)
        return auth.is_signed_in and profile.active_tab == "inbox"

    @rx.event
    async def open_compose(self, link_id: int = 0):
        from app.states.contacts_state import ContactsState

        if not await self._workspace_allowed():
            return
        contacts = await self.get_state(ContactsState)
        if contacts.is_sending:
            return
        if link_id and not any(
            c["link_id"] == link_id and c["status"] == "accepted"
            for c in contacts.contacts
        ):
            return
        contacts.set_compose_target(str(link_id) if link_id else "")
        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        self.view = "compose"
        return ContactsState.load_contacts

    @rx.event
    async def open_contacts(self):
        from app.states.contacts_state import ContactsState

        if not await self._workspace_allowed():
            return
        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        self.view = "contacts"
        return ContactsState.load_contacts

    @rx.event
    async def back_to_inbox(self):
        if not await self._workspace_allowed():
            return
        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        self.view = "inbox"
        return UnifiedInboxState.load_index

    @rx.event
    async def open_contact_passport(self, link_id: int):
        from app.states.contacts_state import ContactsState
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState

        if not await self._workspace_allowed():
            return
        contacts = await self.get_state(ContactsState)
        contact = next(
            (
                c
                for c in contacts.contacts
                if c["link_id"] == link_id and c["status"] == "accepted"
            ),
            None,
        )
        if contact is None:
            return
        profile = await self.get_state(ProfileState)
        await profile.return_to_map()
        self.view = "inbox"
        return DiscoveryState.open_member_profile(contact["other_id"])

    items: list[UnifiedItem] = []
    search: str = ""
    search_generation: int = 0
    type_filter: str = "all"
    filters_open: bool = False
    visited_keys: list[str] = []
    visited_account: str = ""
    selected_key: str = ""
    messages_open: bool = False
    open_offer_ids: list[int] = []
    offers_open: bool = False
    requests_open: bool = False
    preserve_next_mount: bool = False

    @rx.event
    async def reset_disclosures(self):
        self.view = "inbox"
        self.messages_open = False
        self.open_offer_ids = []
        self.offers_open = False
        self.requests_open = False
        if self.preserve_next_mount:
            self.preserve_next_mount = False
            if self.selected_key:
                self.view = "thread"
        else:
            await self._clear_selections()
            from app.states.messaging_state import MessagingState

            (await self.get_state(MessagingState)).pending_thread_id = 0

    @rx.event
    def toggle_messages(self):
        self.messages_open = not self.messages_open

    @rx.event
    def toggle_offer(self, offer_id: int):
        if offer_id <= 0:
            return
        if offer_id in self.open_offer_ids:
            self.open_offer_ids.remove(offer_id)
        else:
            self.open_offer_ids.append(offer_id)

    @rx.event
    def toggle_offers(self):
        self.offers_open = not self.offers_open

    @rx.event
    def toggle_requests(self):
        self.requests_open = not self.requests_open

    is_loading: bool = False
    index_generation: int = 0
    error: str = ""
    unread_by_type: dict[str, int] = {"helper": 0, "helpee": 0, "contact": 0}

    type_filters: list[dict[str, str]] = TYPE_FILTERS

    @rx.var
    def result_count(self) -> int:
        return len(self.items)

    @rx.var
    def result_count_label(self) -> str:
        total = len(self.items)
        return "1 conversation" if total == 1 else f"{total} conversations"

    @rx.var
    def unread_total(self) -> int:
        return sum(item["unread_count"] for item in self.items)

    @rx.var
    def has_search(self) -> bool:
        return bool(self.search.strip())

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    @rx.event
    def set_search(self, value: str):
        self.search = value
        return UnifiedInboxState.load_index

    @rx.event
    def clear_search(self):
        self.search = ""
        self.search_generation += 1
        return UnifiedInboxState.load_index

    @rx.event
    def toggle_filters(self):
        self.filters_open = not self.filters_open

    @rx.event
    def set_type_filter(self, value: str):
        self.type_filter = (
            value if value in ("all", "contact", "helper", "helpee") else "all"
        )
        return UnifiedInboxState.load_index

    @rx.event
    def clear_filters(self):
        self.type_filter = "all"
        self.search = ""
        self.search_generation += 1
        return UnifiedInboxState.load_index

    def _sync_visited_account(self, sid: str):
        if self.visited_account != sid:
            self.visited_keys = []
            self.visited_account = sid

    @rx.event
    def note_selected(self, key: str):
        """Keep the list highlight in step with a deep-link or focus event."""
        self.view = "thread"
        self.selected_key = key
        self.messages_open = True

    # ------------------------------------------------------------------
    # Opening one item: clear the other selection types first
    # ------------------------------------------------------------------

    @rx.event
    async def toggle_item(self, kind: str, ref_id: int):
        if kind not in ("job", "contact", "noncontact") or ref_id <= 0:
            return
        if self.selected_key == f"{kind}:{int(ref_id)}":
            await self._clear_selections()
            return
        return await self._open_item(kind, ref_id)

    @rx.event
    async def mark_opened(self, key: str, sid: str):
        current_sid = (await self.get_state(AuthState)).subscriber_id
        if not current_sid.isdigit() or current_sid != sid:
            return
        self._sync_visited_account(sid)
        if self.selected_key == key and key not in self.visited_keys:
            self.visited_keys.append(key)

    @rx.event
    async def close_item(self):
        await self._clear_selections()

    async def _clear_selections(self):
        from app.states.contacts_state import EMPTY_CONTACT, ContactsState
        from app.states.messaging_state import EMPTY_THREAD, MessagingState
        from app.states.noncontact_state import (
            EMPTY_CONVERSATION,
            NonContactMessagingState,
        )

        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        self.error = ""
        self.view = "inbox"
        self.selected_key = ""

        messaging = await self.get_state(MessagingState)
        contacts = await self.get_state(ContactsState)
        noncontact = await self.get_state(NonContactMessagingState)

        messaging.review_target_open = False
        messaging.selected_thread = dict(EMPTY_THREAD)
        messaging.messages = []
        messaging.reviews = []
        messaging.composer_generation += 1
        contacts.selected_contact = dict(EMPTY_CONTACT)
        contacts.contact_messages = []
        noncontact.selected = dict(EMPTY_CONVERSATION)
        noncontact.messages = []

    @rx.event
    async def open_item(self, kind: str, ref_id: int):
        return await self._open_item(kind, ref_id)

    async def _open_item(self, kind: str, ref_id: int):
        from app.states.contacts_state import ContactsState
        from app.states.messaging_state import MessagingState
        from app.states.noncontact_state import NonContactMessagingState

        if kind not in ("job", "contact", "noncontact") or ref_id <= 0:
            return
        sid = (await self.get_state(AuthState)).subscriber_id
        self._sync_visited_account(sid)
        key = f"{kind}:{int(ref_id)}"
        await self._clear_selections()
        self.view = "thread"
        self.selected_key = key
        self.messages_open = True
        if kind == "contact":
            return ContactsState.select_contact(int(ref_id))
        if kind == "noncontact":
            return NonContactMessagingState.select_conversation(int(ref_id))
        return MessagingState.select_thread(int(ref_id))

    @rx.event
    async def dismiss_thread(self, key: str):
        self.error = ""
        kind, separator, raw_ref = key.partition(":")
        sources = {
            "contact": (
                "skillkind_contact_link",
                "requester_id",
                "recipient_id",
                "skillkind_contact_message",
                "contact_link_id",
            ),
            "noncontact": (
                "skillkind_noncontact_conversation",
                "initiator_id",
                "recipient_id",
                "skillkind_noncontact_message",
                "conversation_id",
            ),
            "job": (
                "skillkind_message_thread",
                "poster_id",
                "helper_id",
                "skillkind_message",
                "thread_id",
            ),
        }
        if (
            kind not in sources
            or not separator
            or not raw_ref.isascii()
            or not raw_ref.isdigit()
            or len(raw_ref) > 10
        ):
            self.error = (
                "That conversation is not available. Please refresh your Inbox."
            )
            return
        ref_id = int(raw_ref)
        if ref_id <= 0 or ref_id > 2147483647:
            self.error = (
                "That conversation is not available. Please refresh your Inbox."
            )
            return
        auth = await self.get_state(AuthState)
        sid = auth.subscriber_id
        if (
            not auth.is_signed_in
            or not sid.isascii()
            or not sid.isdigit()
            or int(sid) <= 0
        ):
            self.error = (
                "Please sign in again to remove a conversation from your Inbox."
            )
            return
        parent, first, second, messages, foreign_key = sources[kind]
        accepted = " AND p.status = 'accepted'" if kind == "contact" else ""
        incoming = (
            "sender_id <> :sid" if kind == "job" else "recipient_id = :sid"
        )
        params = {"sid": int(sid), "kind": kind, "ref": ref_id}
        try:
            async with rx.asession() as session:
                try:
                    dismissed = (
                        await session.execute(
                            text(f"""
                                INSERT INTO skillkind_inbox_thread_dismissal
                                    (subscriber_id, kind, ref_id, dismissed_at)
                                SELECT :sid, :kind, p.id, now()
                                FROM {parent} p
                                JOIN skillkind_subscriber own
                                  ON own.id = :sid AND own.is_active = TRUE
                                WHERE p.id = :ref
                                  AND :sid IN (p.{first}, p.{second}){accepted}
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_member_block mb
                                      WHERE (mb.blocker_id = p.{first} AND mb.blocked_id = p.{second})
                                         OR (mb.blocker_id = p.{second} AND mb.blocked_id = p.{first})
                                  )
                                ON CONFLICT (subscriber_id, kind, ref_id)
                                DO UPDATE SET dismissed_at = EXCLUDED.dismissed_at
                                RETURNING id
                            """),
                            params,
                        )
                    ).first()
                    if dismissed is None:
                        await session.rollback()
                        self.error = "That conversation is no longer available, or your account cannot access it. Please refresh your Inbox."
                        return
                    await session.execute(
                        text(f"""
                            UPDATE {messages} SET read_at = now()
                            WHERE {foreign_key} = :ref AND {incoming}
                              AND read_at IS NULL
                        """),
                        params,
                    )
                    await session.commit()
                except Exception:
                    logging.exception("Unexpected error")
                    await session.rollback()
                    raise
        except Exception as exc:
            logging.exception(f"Inbox removal failed: {exc}")
            self.error = "We couldn't remove that conversation. Your messages are safe; please try again."
            return
        canonical_key = f"{kind}:{ref_id}"
        if self.selected_key == canonical_key:
            await self._clear_selections()
        self.visited_keys = [
            visited for visited in self.visited_keys if visited != canonical_key
        ]
        self.items = [
            item for item in self.items if item["key"] != canonical_key
        ]
        self.index_generation += 1
        return UnifiedInboxState.load_index

    # ------------------------------------------------------------------
    # The index itself
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_index(self):
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            self._sync_visited_account(sid)
            term = self.search.strip().lower()
            wanted = self.type_filter
            generation = self.index_generation
            if not sid.isdigit():
                self.items = []
                self.unread_by_type = {"helper": 0, "helpee": 0, "contact": 0}
                self.is_loading = False
                return
            self.is_loading = True
            self.error = ""

        params: dict[str, object] = {"sid": int(sid)}
        if term:
            params["q"] = f"%{term}%"
        rows: list[tuple[float, UnifiedItem]] = []

        try:
            async with rx.asession() as asession:
                if wanted in ("all", "contact", "sent", "received"):
                    contact_search = ""
                    noncontact_search = ""
                    contact_direction = ""
                    noncontact_direction = ""
                    if wanted in ("sent", "received"):
                        sender = "= :sid" if wanted == "sent" else "<> :sid"
                        contact_role = (
                            "cl.requester_id"
                            if wanted == "sent"
                            else "cl.recipient_id"
                        )
                        direct_role = (
                            "c.initiator_id"
                            if wanted == "sent"
                            else "c.recipient_id"
                        )
                        contact_direction = (
                            f" AND (EXISTS (SELECT 1 FROM skillkind_contact_message d WHERE d.contact_link_id = cl.id AND d.sender_id {sender})"
                            f" OR (NOT EXISTS (SELECT 1 FROM skillkind_contact_message d WHERE d.contact_link_id = cl.id) AND {contact_role} = :sid))"
                        )
                        noncontact_direction = (
                            f" AND (EXISTS (SELECT 1 FROM skillkind_noncontact_message d WHERE d.conversation_id = c.id AND d.sender_id {sender})"
                            f" OR (NOT EXISTS (SELECT 1 FROM skillkind_noncontact_message d WHERE d.conversation_id = c.id) AND {direct_role} = :sid))"
                        )
                    if term:
                        contact_search = (
                            " AND (LOWER(COALESCE(s.display_name, '')) LIKE :q"
                            " OR LOWER(COALESCE(pr.current_city, '')) LIKE :q"
                            " OR LOWER(COALESCE(pr.username, '')) LIKE :q"
                            " OR LOWER(COALESCE(pr.current_city, '')) LIKE :q"
                            " OR LOWER(COALESCE(cl.last_message_preview, ''))"
                            "    LIKE :q)"
                        )
                        noncontact_search = (
                            " AND (LOWER(COALESCE(s.display_name, '')) LIKE :q"
                            " OR LOWER(COALESCE(CONCAT('member-', s.id), '')) LIKE :q"
                            " OR LOWER(COALESCE(pr.username, '')) LIKE :q"
                            " OR LOWER(COALESCE(c.last_message_preview, ''))"
                            "    LIKE :q)"
                        )

                    contact_rows = (
                        await asession.execute(
                            text(
                                f"""
                                SELECT cl.id,
                                       CASE WHEN cl.requester_id = :sid
                                            THEN cl.recipient_id
                                            ELSE cl.requester_id END,
                                       s.display_name, CONCAT('member-', s.id), s.is_verified,
                                       COALESCE(pr.avatar_path, ''),
                                       COALESCE(pr.username, ''),
                                       COALESCE(pr.current_city, ''),
                                       COALESCE(cl.message_count, 0),
                                       COALESCE(cl.last_message_preview, ''),
                                       COALESCE(cl.last_message_at,
                                                cl.updated_at,
                                                cl.created_at),
                                       (SELECT COUNT(*)
                                          FROM skillkind_contact_message cm
                                         WHERE cm.contact_link_id = cl.id
                                           AND cm.recipient_id = :sid
                                           AND cm.read_at IS NULL),
                                       COALESCE((SELECT cm.sender_id FROM skillkind_contact_message cm
                                           WHERE cm.contact_link_id = cl.id
                                           ORDER BY cm.sent_at DESC, cm.id DESC LIMIT 1), cl.requester_id),
                                       EXISTS (SELECT 1 FROM skillkind_contact_message d WHERE d.contact_link_id = cl.id AND d.sender_id = :sid),
                                       EXISTS (SELECT 1 FROM skillkind_contact_message d WHERE d.contact_link_id = cl.id AND d.sender_id <> :sid),
                                       (SELECT latest.body FROM (
                                           SELECT cm.body, cm.sent_at, cm.id FROM skillkind_contact_message cm WHERE cm.contact_link_id = cl.id
                                           UNION ALL
                                           SELECT m.body, m.created_at, m.id FROM skillkind_noncontact_message m JOIN skillkind_noncontact_conversation c ON c.id = m.conversation_id
                                           WHERE (c.initiator_id = cl.requester_id AND c.recipient_id = cl.recipient_id) OR (c.initiator_id = cl.recipient_id AND c.recipient_id = cl.requester_id)
                                           UNION ALL
                                           SELECT m.body, m.sent_at, m.id FROM skillkind_message m JOIN skillkind_message_thread t ON t.id = m.thread_id
                                           WHERE ((t.poster_id = cl.requester_id AND t.helper_id = cl.recipient_id) OR (t.poster_id = cl.recipient_id AND t.helper_id = cl.requester_id))
                                             AND NOT (m.sender_id = t.poster_id AND m.id = (SELECT opener.id FROM skillkind_message opener WHERE opener.thread_id = t.id ORDER BY opener.sent_at, opener.id LIMIT 1))
                                       ) latest ORDER BY latest.sent_at DESC, latest.id DESC LIMIT 1)
                                FROM skillkind_contact_link cl
                                JOIN skillkind_subscriber s
                                  ON s.id = CASE WHEN cl.requester_id = :sid
                                                 THEN cl.recipient_id
                                                 ELSE cl.requester_id END
                                LEFT JOIN skillkind_profile pr
                                       ON pr.subscriber_id = s.id
                                WHERE (cl.requester_id = :sid
                                       OR cl.recipient_id = :sid)
                                  AND cl.status = 'accepted'
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_member_block mb
                                      WHERE (mb.blocker_id = cl.requester_id
                                             AND mb.blocked_id = cl.recipient_id)
                                         OR (mb.blocker_id = cl.recipient_id
                                             AND mb.blocked_id = cl.requester_id)
                                  )
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_inbox_thread_dismissal dismissed
                                      WHERE dismissed.subscriber_id = :sid
                                        AND dismissed.kind = 'contact' AND dismissed.ref_id = cl.id
                                        AND (cl.last_message_at IS NULL OR cl.last_message_at <= dismissed.dismissed_at)
                                  ){contact_direction}{contact_search}
                                ORDER BY COALESCE(cl.last_message_at, cl.updated_at, cl.created_at) DESC
                                LIMIT 60
                                """
                            ),
                            params,
                        )
                    ).all()

                    for r in contact_rows:
                        city = str(r[7] or "")
                        item: UnifiedItem = {
                            "key": f"contact:{int(r[0])}",
                            "kind": "contact",
                            "direction": "sent"
                            if int(r[12]) == int(sid)
                            else "received",
                            "has_sent": direction_flags(
                                bool(r[13]),
                                bool(r[14]),
                                int(r[8] or 0),
                                int(r[12]) == int(sid),
                            )[0],
                            "has_received": direction_flags(
                                bool(r[13]),
                                bool(r[14]),
                                int(r[8] or 0),
                                int(r[12]) == int(sid),
                            )[1],
                            "conv_type": "contact",
                            "type_label": TYPE_LABELS["contact"],
                            "ref_id": int(r[0]),
                            "other_id": int(r[1] or 0),
                            "other_name": str(r[2] or "A Go and Help member"),
                            "other_initial": safe_initial(str(r[2] or "")),
                            "other_avatar_seed": str(r[3] or ""),
                            "other_avatar": str(r[5] or ""),
                            "other_handle": (f"@{r[6]}" if r[6] else ""),
                            "other_verified": bool(r[4]),
                            "preview": message_preview(
                                r[15] if r[15] is not None else r[9]
                            ),
                            "last_photo": last_message_photo(r[15]),
                            "last_at": _stamp(r[10]),
                            "unread_count": int(r[11] or 0),
                            "message_count": int(r[8] or 0),
                            "context": (
                                f"Confirmed contact · {city}"
                                if city
                                else "Confirmed contact"
                            ),
                            "job_title": "",
                            "job_status": "",
                        }
                        rows.append((_sort_value(r[10]), item))

                    noncontact_rows = (
                        await asession.execute(
                            text(
                                f"""
                                SELECT c.id,
                                       CASE WHEN c.initiator_id = :sid
                                            THEN c.recipient_id
                                            ELSE c.initiator_id END,
                                       s.display_name, CONCAT('member-', s.id), s.is_verified,
                                       COALESCE(pr.avatar_path, ''),
                                       COALESCE(pr.username, ''),
                                       COALESCE(c.message_count, 0),
                                       COALESCE(c.last_message_preview, ''),
                                       c.last_message_at,
                                       (SELECT COUNT(*)
                                          FROM skillkind_noncontact_message m
                                         WHERE m.conversation_id = c.id
                                           AND m.recipient_id = :sid
                                           AND m.read_at IS NULL),
                                       COALESCE((SELECT m.sender_id FROM skillkind_noncontact_message m
                                           WHERE m.conversation_id = c.id
                                           ORDER BY m.created_at DESC, m.id DESC LIMIT 1), c.initiator_id),
                                       EXISTS (SELECT 1 FROM skillkind_noncontact_message d WHERE d.conversation_id = c.id AND d.sender_id = :sid),
                                       EXISTS (SELECT 1 FROM skillkind_noncontact_message d WHERE d.conversation_id = c.id AND d.sender_id <> :sid),
                                       (SELECT m.body FROM skillkind_noncontact_message m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC, m.id DESC LIMIT 1)
                                FROM skillkind_noncontact_conversation c
                                JOIN skillkind_subscriber s
                                  ON s.id = CASE WHEN c.initiator_id = :sid
                                                 THEN c.recipient_id
                                                 ELSE c.initiator_id END
                                LEFT JOIN skillkind_profile pr
                                       ON pr.subscriber_id = s.id
                                WHERE (c.initiator_id = :sid
                                       OR c.recipient_id = :sid)
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_contact_link accepted
                                      WHERE accepted.status = 'accepted'
                                        AND ((accepted.requester_id = c.initiator_id AND accepted.recipient_id = c.recipient_id)
                                          OR (accepted.recipient_id = c.initiator_id AND accepted.requester_id = c.recipient_id))
                                  )
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_member_block mb
                                      WHERE (mb.blocker_id = c.initiator_id
                                             AND mb.blocked_id = c.recipient_id)
                                         OR (mb.blocker_id = c.recipient_id
                                             AND mb.blocked_id = c.initiator_id)
                                  )
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_inbox_thread_dismissal dismissed
                                      WHERE dismissed.subscriber_id = :sid
                                        AND dismissed.kind = 'noncontact' AND dismissed.ref_id = c.id
                                        AND (c.last_message_at IS NULL OR c.last_message_at <= dismissed.dismissed_at)
                                  ){noncontact_direction}{noncontact_search}
                                ORDER BY c.last_message_at DESC NULLS LAST,
                                         c.id DESC
                                LIMIT 60
                                """
                            ),
                            params,
                        )
                    ).all()

                    for r in noncontact_rows:
                        item = {
                            "other_initial": safe_initial(str(r[2] or "")),
                            "key": f"noncontact:{int(r[0])}",
                            "kind": "noncontact",
                            "direction": "sent"
                            if int(r[11]) == int(sid)
                            else "received",
                            "has_sent": direction_flags(
                                bool(r[12]),
                                bool(r[13]),
                                int(r[7] or 0),
                                int(r[11]) == int(sid),
                            )[0],
                            "has_received": direction_flags(
                                bool(r[12]),
                                bool(r[13]),
                                int(r[7] or 0),
                                int(r[11]) == int(sid),
                            )[1],
                            "conv_type": "contact",
                            "type_label": TYPE_LABELS["contact"],
                            "ref_id": int(r[0]),
                            "other_id": int(r[1] or 0),
                            "other_name": str(r[2] or "A Go and Help member"),
                            "other_avatar_seed": str(r[3] or ""),
                            "other_avatar": str(r[5] or ""),
                            "other_handle": (f"@{r[6]}" if r[6] else ""),
                            "other_verified": bool(r[4]),
                            "preview": message_preview(r[8]),
                            "last_photo": last_message_photo(r[14]),
                            "last_at": _stamp(r[9]),
                            "unread_count": int(r[10] or 0),
                            "message_count": int(r[7] or 0),
                            "context": "Direct message · not a contact yet",
                            "job_title": "",
                            "job_status": "",
                        }
                        rows.append((_sort_value(r[9]), item))

                if wanted in ("all", "helper", "helpee", "sent", "received"):
                    job_search = ""
                    if term:
                        job_search = (
                            " AND (LOWER(COALESCE(ps.display_name, '')) LIKE :q"
                            " OR LOWER(COALESCE(hs.display_name, '')) LIKE :q"
                            " OR LOWER(COALESCE(pp.username, '')) LIKE :q"
                            " OR LOWER(COALESCE(hp.username, '')) LIKE :q"
                            " OR LOWER(COALESCE(p.title, '')) LIKE :q"
                            " OR LOWER(COALESCE(p.category, '')) LIKE :q"
                            " OR LOWER(COALESCE(p.city, '')) LIKE :q"
                            " OR LOWER(COALESCE(t.subject, '')) LIKE :q"
                            " OR EXISTS (SELECT 1 FROM skillkind_message ms"
                            "             WHERE ms.thread_id = t.id"
                            "               AND LOWER(ms.body) LIKE :q))"
                        )
                    role_clause = ""
                    if wanted == "helper":
                        role_clause = " AND t.poster_id = :sid"
                    elif wanted == "helpee":
                        role_clause = " AND t.helper_id = :sid"
                    elif wanted in ("sent", "received"):
                        sender = "= :sid" if wanted == "sent" else "<> :sid"
                        fallback = (
                            "t.poster_id" if wanted == "sent" else "t.helper_id"
                        )
                        role_clause = (
                            f" AND (EXISTS (SELECT 1 FROM skillkind_message d WHERE d.thread_id = t.id AND d.sender_id {sender})"
                            f" OR (NOT EXISTS (SELECT 1 FROM skillkind_message d WHERE d.thread_id = t.id) AND {fallback} = :sid))"
                        )

                    job_rows = (
                        await asession.execute(
                            text(
                                f"""
                                SELECT t.id, t.poster_id, t.helper_id,
                                       ps.display_name, CONCAT('member-', ps.id),
                                       ps.is_verified,
                                       hs.display_name, CONCAT('member-', hs.id),
                                       hs.is_verified,
                                       COALESCE(p.title, ''),
                                       COALESCE(p.status, ''),
                                       COALESCE(p.city, ''),
                                       COALESCE(t.last_message_at,
                                                t.created_at),
                                       (SELECT COUNT(*)
                                          FROM skillkind_message m
                                         WHERE m.thread_id = t.id),
                                       (SELECT m2.body FROM skillkind_message m2
                                         WHERE m2.thread_id = t.id
                                         ORDER BY m2.sent_at DESC, m2.id DESC LIMIT 1),
                                       (SELECT COUNT(*)
                                          FROM skillkind_message m3
                                         WHERE m3.thread_id = t.id
                                           AND m3.sender_id <> :sid
                                           AND m3.read_at IS NULL),
                                       COALESCE(pp.avatar_path, ''),
                                       COALESCE(hp.avatar_path, ''),
                                       COALESCE((SELECT m.sender_id FROM skillkind_message m
                                           WHERE m.thread_id = t.id
                                           ORDER BY m.sent_at DESC, m.id DESC LIMIT 1), t.helper_id),
                                       EXISTS (SELECT 1 FROM skillkind_message d WHERE d.thread_id = t.id AND d.sender_id = :sid),
                                       EXISTS (SELECT 1 FROM skillkind_message d WHERE d.thread_id = t.id AND d.sender_id <> :sid)
                                FROM skillkind_message_thread t
                                JOIN skillkind_help_post p ON p.id = t.post_id
                                JOIN skillkind_subscriber ps
                                     ON ps.id = t.poster_id
                                JOIN skillkind_subscriber hs
                                     ON hs.id = t.helper_id
                                LEFT JOIN skillkind_profile pp
                                       ON pp.subscriber_id = ps.id
                                LEFT JOIN skillkind_profile hp
                                       ON hp.subscriber_id = hs.id
                                WHERE (t.poster_id = :sid
                                       OR t.helper_id = :sid)
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_contact_link accepted
                                      WHERE accepted.status = 'accepted'
                                        AND ((accepted.requester_id = t.poster_id AND accepted.recipient_id = t.helper_id)
                                          OR (accepted.recipient_id = t.poster_id AND accepted.requester_id = t.helper_id))
                                  )
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_member_block mb
                                      WHERE (mb.blocker_id = t.poster_id
                                             AND mb.blocked_id = t.helper_id)
                                         OR (mb.blocker_id = t.helper_id
                                             AND mb.blocked_id = t.poster_id)
                                  )
                                  AND NOT EXISTS (
                                      SELECT 1 FROM skillkind_inbox_thread_dismissal dismissed
                                      WHERE dismissed.subscriber_id = :sid
                                        AND dismissed.kind = 'job' AND dismissed.ref_id = t.id
                                        AND (t.last_message_at IS NULL OR t.last_message_at <= dismissed.dismissed_at)
                                  ){role_clause}{job_search}
                                ORDER BY COALESCE(t.last_message_at,
                                                  t.created_at) DESC
                                LIMIT 60
                                """
                            ),
                            params,
                        )
                    ).all()

                    me = int(sid)
                    for r in job_rows:
                        i_posted = int(r[1] or 0) == me
                        has_sent, has_received = direction_flags(
                            bool(r[19]), bool(r[20]), int(r[13] or 0), i_posted
                        )
                        conv_type = job_type(i_posted)
                        if i_posted:
                            other_id = int(r[2] or 0)
                            other_name = str(r[6] or "A Go and Help member")
                            other_avatar_seed = str(r[7] or "")
                            other_verified = bool(r[8])
                            other_avatar = str(r[17] or "")
                            context = "They are helping you"
                        else:
                            other_id = int(r[1] or 0)
                            other_name = str(r[3] or "A Go and Help member")
                            other_avatar_seed = str(r[4] or "")
                            other_verified = bool(r[5])
                            other_avatar = str(r[16] or "")
                            context = "They asked for your help"
                        city = str(r[11] or "")
                        item = {
                            "key": f"job:{int(r[0])}",
                            "kind": "job",
                            "direction": "sent"
                            if int(r[18]) == me
                            else "received",
                            "has_sent": has_sent,
                            "has_received": has_received,
                            "conv_type": conv_type,
                            "type_label": TYPE_LABELS[conv_type],
                            "ref_id": int(r[0]),
                            "other_id": other_id,
                            "other_name": other_name,
                            "other_initial": safe_initial(other_name),
                            "other_avatar_seed": other_avatar_seed,
                            "other_avatar": other_avatar,
                            "other_handle": "",
                            "other_verified": other_verified,
                            "preview": message_preview(r[14]),
                            "last_photo": last_message_photo(r[14]),
                            "last_at": _stamp(r[12]),
                            "unread_count": int(r[15] or 0),
                            "message_count": int(r[13] or 0),
                            "context": job_summary_copy(
                                conv_type, str(r[9] or "")
                            ),
                            "job_title": str(r[9] or ""),
                            "job_status": str(r[10] or ""),
                        }
                        rows.append((_sort_value(r[12]), item))

                summary = (
                    await asession.execute(
                        text("""
                    SELECT
                      (SELECT COUNT(*) FROM skillkind_message m JOIN skillkind_message_thread t ON t.id = m.thread_id
                       WHERE m.sender_id <> :sid AND m.read_at IS NULL AND t.poster_id = :sid
                         AND NOT EXISTS (SELECT 1 FROM skillkind_contact_link a WHERE a.status = 'accepted' AND ((a.requester_id = t.poster_id AND a.recipient_id = t.helper_id) OR (a.recipient_id = t.poster_id AND a.requester_id = t.helper_id)))
                         AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b WHERE (b.blocker_id = t.poster_id AND b.blocked_id = t.helper_id) OR (b.blocker_id = t.helper_id AND b.blocked_id = t.poster_id))) AS helper,
                      (SELECT COUNT(*) FROM skillkind_message m JOIN skillkind_message_thread t ON t.id = m.thread_id
WHERE m.sender_id <> :sid AND m.read_at IS NULL AND t.helper_id = :sid
                         AND NOT EXISTS (SELECT 1 FROM skillkind_contact_link a WHERE a.status = 'accepted' AND ((a.requester_id = t.poster_id AND a.recipient_id = t.helper_id) OR (a.recipient_id = t.poster_id AND a.requester_id = t.helper_id)))
                         AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b WHERE (b.blocker_id = t.poster_id AND b.blocked_id = t.helper_id) OR (b.blocker_id = t.helper_id AND b.blocked_id = t.poster_id))) AS helpee,
                      ((SELECT COUNT(*) FROM skillkind_contact_message m JOIN skillkind_contact_link cl ON cl.id = m.contact_link_id
                        WHERE m.recipient_id = :sid AND m.read_at IS NULL AND cl.status = 'accepted' AND :sid IN (cl.requester_id, cl.recipient_id)
                          AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b WHERE (b.blocker_id = cl.requester_id AND b.blocked_id = cl.recipient_id) OR (b.blocker_id = cl.recipient_id AND b.blocked_id = cl.requester_id)))
                       + (SELECT COUNT(*) FROM skillkind_noncontact_message m JOIN skillkind_noncontact_conversation c ON c.id = m.conversation_id
                          WHERE m.recipient_id = :sid AND m.read_at IS NULL AND :sid IN (c.initiator_id, c.recipient_id)
                            AND NOT EXISTS (SELECT 1 FROM skillkind_contact_link a WHERE a.status = 'accepted' AND ((a.requester_id = c.initiator_id AND a.recipient_id = c.recipient_id) OR (a.recipient_id = c.initiator_id AND a.requester_id = c.recipient_id)))
                            AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b WHERE (b.blocker_id = c.initiator_id AND b.blocked_id = c.recipient_id) OR (b.blocker_id = c.recipient_id AND b.blocked_id = c.initiator_id)))) AS contact
                """),
                        params,
                    )
                ).one()
        except Exception as exc:
            logging.exception(f"Unified inbox index failed: {exc}")
            async with self:
                self.is_loading = False
                self.error = "Unable to load conversations."
            return

        rows.sort(key=lambda pair: pair[0], reverse=True)
        loaded = [pair[1] for pair in rows]
        async with self:
            current_sid = (await self.get_state(AuthState)).subscriber_id
            stale = (
                self.search.strip().lower() != term
                or self.type_filter != wanted
                or self.index_generation != generation
            )
            if current_sid == sid and not stale:
                self.items = loaded
                self.unread_by_type = {
                    "helper": int(summary[0] or 0),
                    "helpee": int(summary[1] or 0),
                    "contact": int(summary[2] or 0),
                }
            self.is_loading = False
        if stale:
            yield UnifiedInboxState.load_index
