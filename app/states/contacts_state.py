"""Contact requests and direct contact messaging for Go and Help.

Database-backed workflow only — no UI is wired to this state yet. Everything
here talks to `skillkind_contact_link` and `skillkind_contact_message` with raw
SQL through `rx.asession()`.
"""

import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text
from app.message_photos import decode_message, message_preview

from app.countries import ISO2_NAMES, resolve_nationality
from app.member_blocks import BLOCK_UNAVAILABLE_MESSAGE, are_members_blocked
from app.models import (
    CONTACT_ACCEPTED,
    CONTACT_DECLINED,
    CONTACT_PENDING,
    CONTACT_REMOVED,
)
from app.states.auth_state import AuthState

MAX_NOTE_LENGTH = 500
MAX_MESSAGE_LENGTH = 2000
PREVIEW_LENGTH = 255


class PersonResult(TypedDict):
    """A neighbour found through the people search, with our link to them."""

    id: int
    name: str
    avatar_seed: str
    username: str
    handle: str
    nationality: str
    avatar_path: str
    headline: str
    city: str
    languages: str
    skills: str
    availability: str
    mode_label: str
    kindness: int
    rating: float
    reviews: int
    joined: str
    link_id: int
    link_status: str
    status_label: str
    i_requested: bool
    can_request: bool
    can_respond: bool
    is_contact: bool
    # True only when the subscriber confirmed their email address.
    verified: bool


class ContactItem(TypedDict):
    """A contact link seen from the signed-in traveller's point of view."""

    link_id: int
    other_id: int
    other_name: str
    other_avatar_seed: str
    other_username: str
    other_handle: str
    other_avatar: str
    other_headline: str
    other_city: str
    status: str
    status_label: str
    direction: str
    direction_label: str
    intro_note: str
    message_count: int
    last_preview: str
    last_at: str
    unread_count: int
    requested_at: str
    accepted_at: str
    can_message: bool
    other_verified: bool
    nationality: str
    country_code: str
    country_flag: str


class ContactMessageItem(TypedDict):
    source_kind: str
    id: int
    sender_id: int
    sender_name: str
    sender_avatar_seed: str
    body: str
    photos: list[str]
    sent_at: str
    mine: bool
    read: bool


EMPTY_CONTACT: ContactItem = {
    "link_id": 0,
    "other_id": 0,
    "other_name": "",
    "other_avatar_seed": "",
    "other_username": "",
    "other_handle": "",
    "other_avatar": "",
    "other_headline": "",
    "other_city": "",
    "status": "",
    "status_label": "",
    "direction": "",
    "direction_label": "",
    "intro_note": "",
    "message_count": 0,
    "last_preview": "",
    "last_at": "",
    "unread_count": 0,
    "requested_at": "",
    "accepted_at": "",
    "can_message": False,
    "other_verified": False,
    "nationality": "",
    "country_code": "",
    "country_flag": "",
}

STATUS_LABELS: dict[str, str] = {
    CONTACT_PENDING: "Request pending",
    CONTACT_ACCEPTED: "Contacts",
    CONTACT_DECLINED: "Request declined",
    CONTACT_REMOVED: "Contact removed",
}


# Canonical country names offered as nationality suggestions.
COUNTRY_SUGGESTIONS: list[str] = sorted(ISO2_NAMES.values())


def canonical_country(raw: str) -> str:
    """Canonical country name for typed text, or '' when unrecognised."""
    _, iso2, _ = resolve_nationality(raw)
    return ISO2_NAMES[iso2] if iso2 else ""


def _fmt_day(value) -> str:
    return value.strftime("%b %d, %Y") if value is not None else ""


def _fmt_stamp(value) -> str:
    return value.strftime("%b %d · %H:%M") if value is not None else ""


class ContactsState(rx.State):
    """Find people, exchange contact requests, and message confirmed contacts."""

    # People search
    search_query: str = ""
    search_username: str = ""
    search_country: str = ""
    # Canonical country resolved from `search_country`; '' means unusable.
    search_country_canonical: str = ""
    country_error: str = ""
    country_options: list[str] = COUNTRY_SUGGESTIONS
    search_city: str = ""
    search_results: list[PersonResult] = []
    is_searching: bool = False
    has_searched: bool = False

    # Contact lists
    contacts: list[ContactItem] = []
    incoming_requests: list[ContactItem] = []
    outgoing_requests: list[ContactItem] = []
    is_loading: bool = False

    # Conversation
    selected_contact: ContactItem = EMPTY_CONTACT
    contact_messages: list[ContactMessageItem] = []
    is_loading_messages: bool = False
    is_sending: bool = False

    # Inbox compose area (write to an accepted contact from the Inbox)
    compose_link_id: str = ""
    compose_search: str = ""
    compose_generation: int = 0

    # Action flags / feedback
    is_requesting: bool = False
    is_responding: bool = False
    error: str = ""
    success: str = ""

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_contact["link_id"] > 0

    @rx.var
    def can_message_selected(self) -> bool:
        return (
            self.selected_contact["link_id"] > 0
            and self.selected_contact["status"] == CONTACT_ACCEPTED
        )

    @rx.var
    def contact_count_heading(self) -> str:
        """`0 Contacts`, `1 Contacts`, `12 Contacts` — used as a heading."""
        return f"{len(self.contacts)} Contacts"

    @rx.var
    def compose_options(self) -> list[ContactItem]:
        """Accepted contacts, narrowed by the compose search box."""
        term = self.compose_search.strip().lower()
        pool = [
            contact
            for contact in self.contacts
            if contact["status"] == CONTACT_ACCEPTED
        ]
        if not term:
            return pool
        return [
            contact
            for contact in pool
            if term in contact["other_name"].lower()
            or term in contact["other_username"].lower()
            or term in contact["other_handle"].lower()
        ]

    @rx.var
    def has_message_contacts(self) -> bool:
        return any(
            contact["status"] == CONTACT_ACCEPTED for contact in self.contacts
        )

    @rx.var
    def compose_ready(self) -> bool:
        return any(
            str(c["link_id"]) == self.compose_link_id
            and c["status"] == CONTACT_ACCEPTED
            for c in self.contacts
        )

    @rx.var
    def accepted_member_ids(self) -> list[int]:
        return [
            c["other_id"]
            for c in self.contacts
            if c["status"] == CONTACT_ACCEPTED
        ]

    @rx.var
    def pending_member_ids(self) -> list[int]:
        return [
            c["other_id"]
            for c in [*self.incoming_requests, *self.outgoing_requests]
        ]

    @rx.var
    def contact_count_label(self) -> str:
        count = len(self.contacts)
        if count == 1:
            return "1 contact"
        return f"{count} contacts"

    @rx.var
    def incoming_count(self) -> int:
        return len(self.incoming_requests)

    @rx.var
    def outgoing_count(self) -> int:
        return len(self.outgoing_requests)

    @rx.var
    def unread_total(self) -> int:
        return sum(contact["unread_count"] for contact in self.contacts)

    # ------------------------------------------------------------------
    # Row builders
    # ------------------------------------------------------------------

    def _row_to_person(self, row, sid: int) -> PersonResult:
        link_id = int(row[13] or 0)
        status = str(row[14] or "")
        requester_id = int(row[15] or 0)
        i_requested = link_id > 0 and requester_id == sid
        can_request = link_id == 0 or status in (
            CONTACT_DECLINED,
            CONTACT_REMOVED,
        )
        can_respond = (
            link_id > 0 and status == CONTACT_PENDING and not i_requested
        )
        if status == CONTACT_PENDING:
            status_label = (
                "Request sent — waiting for a reply"
                if i_requested
                else "They'd like to connect with you"
            )
        elif status == CONTACT_ACCEPTED:
            status_label = "Already in your contacts"
        elif status == CONTACT_DECLINED:
            status_label = "Request was declined — you can ask again"
        elif status == CONTACT_REMOVED:
            status_label = "You were contacts before"
        else:
            status_label = "Not connected yet"
        mode = str(row[3] or "both")
        username = str(row[16] or "") if len(row) > 16 else ""
        return {
            "id": int(row[0]),
            "name": str(row[1] or "A Go and Help neighbour"),
            "avatar_seed": str(row[2] or ""),
            "username": username,
            "handle": f"@{username}" if username else "",
            "nationality": str(row[17] or "") if len(row) > 17 else "",
            "avatar_path": str(row[18] or "") if len(row) > 18 else "",
            "headline": str(row[4] or ""),
            "city": str(row[5] or ""),
            "languages": str(row[6] or ""),
            "skills": str(row[7] or ""),
            "availability": str(row[8] or ""),
            "mode_label": "Offers help"
            if mode == "offer_help"
            else (
                "Looking for help"
                if mode == "receive_help"
                else "Helps & receives"
            ),
            "kindness": int(row[9] or 0),
            "rating": float(row[10] or 0),
            "reviews": int(row[11] or 0),
            "joined": _fmt_day(row[12]),
            "link_id": link_id,
            "link_status": status,
            "status_label": status_label,
            "i_requested": i_requested,
            "can_request": can_request,
            "can_respond": can_respond,
            "is_contact": status == CONTACT_ACCEPTED,
            "verified": bool(row[19]) if len(row) > 19 else False,
        }

    def _row_to_contact(self, row, sid: int) -> ContactItem:
        requester_id = int(row[1])
        status = str(row[3] or "")
        direction = "outgoing" if requester_id == sid else "incoming"
        if status == CONTACT_ACCEPTED:
            direction_label = (
                "You reached out first"
                if direction == "outgoing"
                else "They reached out first"
            )
        elif status == CONTACT_PENDING:
            direction_label = (
                "Waiting for their reply"
                if direction == "outgoing"
                else "Waiting on your answer"
            )
        else:
            direction_label = STATUS_LABELS.get(status, "")
        nationality, country_code, country_flag = resolve_nationality(
            str(row[20] or "") if len(row) > 20 else ""
        )
        return {
            "nationality": nationality,
            "country_code": country_code,
            "country_flag": country_flag,
            "link_id": int(row[0]),
            "other_id": int(row[9]),
            "other_name": str(row[10] or "A Go and Help neighbour"),
            "other_avatar_seed": str(row[11] or ""),
            "other_username": str(row[18] or "") if len(row) > 18 else "",
            "other_handle": (
                f"@{row[18]}" if len(row) > 18 and str(row[18] or "") else ""
            ),
            "other_avatar": str(row[19] or "") if len(row) > 19 else "",
            "other_headline": str(row[12] or ""),
            "other_city": str(row[13] or ""),
            "status": status,
            "status_label": STATUS_LABELS.get(status, status.title()),
            "direction": direction,
            "direction_label": direction_label,
            "intro_note": str(row[4] or ""),
            "message_count": int(row[5] or 0),
            "last_preview": message_preview(row[6]),
            "last_at": _fmt_stamp(row[7]),
            "unread_count": int(row[14] or 0),
            "requested_at": _fmt_day(row[8]),
            "accepted_at": _fmt_day(row[16]),
            "can_message": status == CONTACT_ACCEPTED,
            "other_verified": bool(row[17]) if len(row) > 17 else False,
        }

    # ------------------------------------------------------------------
    # Simple setters
    # ------------------------------------------------------------------

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value
        return ContactsState.search_people

    @rx.event
    def set_search_city(self, value: str):
        self.search_city = value
        return ContactsState.search_people

    @rx.event
    def set_search_username(self, value: str):
        self.search_username = value.strip().lstrip("@")
        return ContactsState.search_people

    @rx.event
    def set_search_country(self, value: str):
        """Nationality must be a real country before anything is queried."""
        self.search_country = value
        typed = value.strip()
        if not typed:
            self.search_country_canonical = ""
            self.country_error = ""
            return ContactsState.search_people
        canonical = canonical_country(typed)
        if not canonical:
            self.search_country_canonical = ""
            self.country_error = (
                f"“{typed[:60]}” isn't a country we recognise — pick one from "
                "the suggestions."
            )
            return None
        self.search_country_canonical = canonical
        self.country_error = ""
        return ContactsState.search_people

    @rx.event
    def clear_search(self):
        self.search_query = ""
        self.search_username = ""
        self.search_country = ""
        self.search_country_canonical = ""
        self.country_error = ""
        self.search_city = ""
        self.search_results = []
        self.has_searched = False
        self.error = ""
        self.success = ""

    @rx.event
    def clear_feedback(self):
        self.error = ""
        self.success = ""

    @rx.event
    def clear_selection(self):
        from app.states.message_attachment_state import MessageAttachmentState

        self.selected_contact = EMPTY_CONTACT
        self.contact_messages = []
        return MessageAttachmentState.clear_pending

    @rx.event
    def set_compose_search(self, value: str):
        if self.is_sending:
            return
        self.compose_search = value
        self.compose_link_id = ""

    @rx.event
    def set_compose_target(self, value: str):
        if self.is_sending:
            return
        contact = next(
            (
                c
                for c in self.contacts
                if str(c["link_id"]) == value
                and c["status"] == CONTACT_ACCEPTED
            ),
            None,
        )
        self.compose_link_id = value if contact else ""
        self.compose_search = contact["other_name"] if contact else ""
        self.error = ""
        self.success = ""

    @rx.event
    def compose_and_send(self, form_data: dict[str, Any]):
        """Open a direct conversation from the Inbox and send the first note.

        Only accepted contacts can ever be chosen — the selection is matched
        against the loaded accepted contacts before anything is sent.
        """
        if self.is_sending:
            return
        subject = " ".join(str(form_data.get("subject", "")).split())
        message = str(form_data.get("body", "")).strip()
        if not subject or len(subject) > 120:
            self.error = "Enter a subject of 1–120 characters."
            return
        if not message:
            self.error = "Write a few words before sending."
            return
        body = f"Subject: {subject}\n\n{message}"
        if len(body) > MAX_MESSAGE_LENGTH:
            self.error = f"Keep the subject and message together under {MAX_MESSAGE_LENGTH} characters."
            return
        self.success = ""
        if not self.compose_link_id.isdigit():
            self.error = "Choose one of your contacts to write to."
            return None
        link_id = int(self.compose_link_id)
        match = [
            contact
            for contact in self.contacts
            if contact["link_id"] == link_id
            and contact["status"] == CONTACT_ACCEPTED
        ]
        if not match:
            self.error = (
                "You can only message confirmed contacts — pick someone from "
                "your contacts list."
            )
            return None
        if not body:
            self.error = "Write a few words before sending."
            return None
        self.error = ""
        self.selected_contact = match[0]
        self.contact_messages = []
        return ContactsState.send_contact_message(
            {"body": body, "compose_link_id": link_id}
        )

    @rx.event
    async def open_contact_in_inbox(self, link_id: int):
        """Open an accepted contact's conversation inside the Inbox screen."""
        from app.states.messaging_state import EMPTY_THREAD, MessagingState
        from app.states.noncontact_state import (
            EMPTY_CONVERSATION,
            NonContactMessagingState,
        )
        from app.states.profile_state import ProfileState
        from app.states.unified_inbox_state import UnifiedInboxState

        self.error = ""
        self.success = ""
        match = [
            contact
            for contact in self.contacts
            if contact["link_id"] == link_id
            and contact["status"] == CONTACT_ACCEPTED
        ]
        if not match:
            self.error = (
                "We couldn't open that conversation — try refreshing your "
                "contacts."
            )
            return None
        self.selected_contact = match[0]
        self.contact_messages = []
        self.compose_link_id = str(link_id)
        profile = await self.get_state(ProfileState)
        unified = await self.get_state(UnifiedInboxState)
        unified.preserve_next_mount = profile.active_tab != "inbox"
        profile.active_tab = "inbox"
        messaging = await self.get_state(MessagingState)
        messaging.selected_thread = EMPTY_THREAD
        messaging.messages = []
        messaging.reviews = []
        noncontact = await self.get_state(NonContactMessagingState)
        noncontact.selected = EMPTY_CONVERSATION
        noncontact.messages = []
        unified = await self.get_state(UnifiedInboxState)
        unified.view = "thread"
        unified.messages_open = True
        from app.states.message_attachment_state import MessageAttachmentState

        await (await self.get_state(MessageAttachmentState))._discard()
        unified.selected_key = f"contact:{int(link_id)}"
        return ContactsState.load_contact_messages

    @rx.event
    def select_contact(self, link_id: int):
        """Open a contact conversation from any of the three lists."""
        self.error = ""
        self.success = ""
        pools = [self.contacts, self.incoming_requests, self.outgoing_requests]
        for pool in pools:
            for contact in pool:
                if contact["link_id"] == link_id:
                    self.selected_contact = contact
                    return ContactsState.load_contact_messages
        self.selected_contact = EMPTY_CONTACT
        self.contact_messages = []
        self.error = (
            "We couldn't open that conversation — try refreshing your contacts."
        )

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def search_people(self):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            name_term = self.search_query.strip()
            city_term = self.search_city.strip()
            username_term = self.search_username.strip().lstrip("@")
            typed_country = self.search_country.strip()
            country_term = self.search_country_canonical.strip()
        if typed_country and not country_term:
            async with self:
                self.search_results = []
                self.has_searched = False
                self.is_searching = False
            return
        if not sid.isdigit():
            async with self:
                self.search_results = []
                self.has_searched = False
                self.error = "Please sign in to find fellow travellers."
            return
        if (
            not name_term
            and not city_term
            and not username_term
            and not country_term
        ):
            async with self:
                self.search_results = []
                self.has_searched = False
            return
        async with self:
            self.is_searching = True
            self.error = ""

        where = "WHERE s.is_active = TRUE AND s.id <> :sid"
        params: dict[str, str | int] = {"sid": int(sid)}
        if name_term:
            where += " AND LOWER(s.display_name) LIKE :name"
            params["name"] = f"%{name_term.lower()}%"
        if city_term:
            where += (
                " AND (LOWER(COALESCE(pr.current_city, '')) LIKE :city"
                " OR LOWER(COALESCE(pr.home_city, '')) LIKE :city)"
            )
            params["city"] = f"%{city_term.lower()}%"
        if username_term:
            where += " AND LOWER(COALESCE(pr.username, '')) LIKE :username"
            params["username"] = f"%{username_term.lower()}%"
        if country_term:
            where += (
                " AND (LOWER(COALESCE(pr.nationality, '')) LIKE :country"
                " OR LOWER(COALESCE(pr.home_country, '')) LIKE :country)"
            )
            params["country"] = f"%{country_term.lower()}%"

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT s.id, s.display_name, CONCAT('member-', s.id), s.help_mode,
                               COALESCE(pr.headline, ''),
                               COALESCE(pr.current_city, ''),
                               COALESCE(pr.languages, ''),
                               COALESCE(pr.skills, ''),
                               COALESCE(pr.availability_note, ''),
                               COALESCE(pr.kindness_points, 0),
                               COALESCE(pr.helper_rating_avg, 0),
                               COALESCE(pr.helper_rating_count, 0),
                               s.joined_at,
                               COALESCE(cl.id, 0),
                               COALESCE(cl.status, ''),
                               COALESCE(cl.requester_id, 0),
                               COALESCE(pr.username, ''),
                               COALESCE(pr.nationality, ''),
                               COALESCE(pr.avatar_path, ''),
                               s.is_verified
                        FROM skillkind_subscriber s
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = s.id
                        LEFT JOIN skillkind_contact_link cl
                               ON (cl.requester_id = :sid AND cl.recipient_id = s.id)
                               OR (cl.recipient_id = :sid AND cl.requester_id = s.id)
                        {where}
                        ORDER BY COALESCE(pr.kindness_points, 0) DESC,
                                 s.display_name ASC
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()

        loaded = [self._row_to_person(r, int(sid)) for r in rows]
        async with self:
            self.search_results = loaded
            self.has_searched = True
            self.is_searching = False

    @rx.event(background=True)
    async def load_contacts(self):
        """Load confirmed contacts plus pending incoming and outgoing requests."""
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            selected_id = self.selected_contact["link_id"]
            if not sid.isdigit():
                self.contacts = []
                self.incoming_requests = []
                self.outgoing_requests = []
                self.selected_contact = EMPTY_CONTACT
                self.contact_messages = []
                self.is_loading = False
                return
            self.is_loading = True
            self.error = ""
        try:
            match = await self._load_contacts_data(sid, selected_id)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                self.error = "We couldn't load your contacts. Please try again."
            return
        if match:
            yield ContactsState.load_contact_messages

    async def _load_contacts_data(self, sid: str, selected_id: int) -> bool:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT cl.id, cl.requester_id, cl.recipient_id, cl.status,
                               COALESCE(cl.intro_note, ''),
                               COALESCE(cl.message_count, 0),
                               COALESCE(cl.last_message_preview, ''),
                               cl.last_message_at, cl.created_at,
                               other.id, other.display_name, CONCAT('member-', other.id),
                               COALESCE(pr.headline, ''),
                               COALESCE(pr.current_city, ''),
                               (SELECT COUNT(*) FROM skillkind_contact_message cm
                                 WHERE cm.contact_link_id = cl.id
                                   AND cm.recipient_id = :sid
                                   AND cm.read_at IS NULL),
                               cl.responded_at, cl.accepted_at,
                               other.is_verified,
                               COALESCE(pr.username, ''),
                               COALESCE(pr.avatar_path, ''),
                               COALESCE(pr.nationality, '')
                        FROM skillkind_contact_link cl
                        JOIN skillkind_subscriber other
                          ON other.id = CASE WHEN cl.requester_id = :sid
                                             THEN cl.recipient_id
                                             ELSE cl.requester_id END
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = other.id
                        WHERE (cl.requester_id = :sid OR cl.recipient_id = :sid)
                          AND cl.status IN ('pending', 'accepted')
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = cl.requester_id
                                     AND mb.blocked_id = cl.recipient_id)
                                 OR (mb.blocker_id = cl.recipient_id
                                     AND mb.blocked_id = cl.requester_id)
                          )
                        ORDER BY COALESCE(cl.last_message_at, cl.created_at) DESC
                        LIMIT 100
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()

        loaded = [self._row_to_contact(r, int(sid)) for r in rows]
        accepted = [c for c in loaded if c["status"] == CONTACT_ACCEPTED]
        incoming = [
            c
            for c in loaded
            if c["status"] == CONTACT_PENDING and c["direction"] == "incoming"
        ]
        outgoing = [
            c
            for c in loaded
            if c["status"] == CONTACT_PENDING and c["direction"] == "outgoing"
        ]
        match = [c for c in loaded if c["link_id"] == selected_id]
        async with self:
            self.contacts = accepted
            self.incoming_requests = incoming
            self.outgoing_requests = outgoing
            self.selected_contact = match[0] if match else EMPTY_CONTACT
            if not match:
                self.contact_messages = []
            self.is_loading = False
        return bool(match)

    @rx.event(background=True)
    async def load_contact_messages(self):
        """Load the direct message history for the selected contact link."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            link_id = self.selected_contact["link_id"]
        if not sid.isdigit() or link_id <= 0:
            async with self:
                self.contact_messages = []
            return
        async with self:
            self.is_loading_messages = True

        async with rx.asession() as asession:
            # A blocked pair (either direction) never loads a conversation.
            allowed = (
                await asession.execute(
                    text(
                        """
                        SELECT 1 FROM skillkind_contact_link cl
                        WHERE cl.id = :link_id
                          AND (cl.requester_id = :sid
                               OR cl.recipient_id = :sid)
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = cl.requester_id
                                     AND mb.blocked_id = cl.recipient_id)
                                 OR (mb.blocker_id = cl.recipient_id
                                     AND mb.blocked_id = cl.requester_id)
                          )
                        """
                    ),
                    {"link_id": int(link_id), "sid": int(sid)},
                )
            ).first()
            if allowed is None:
                async with self:
                    self.contact_messages = []
                    self.selected_contact = EMPTY_CONTACT
                    self.is_loading_messages = False
                return
            rows = (
                await asession.execute(
                    text(
                        """
                        WITH pair AS (
                            SELECT id, requester_id, recipient_id FROM skillkind_contact_link
                            WHERE id = :link_id AND status = 'accepted'
                              AND :sid IN (requester_id, recipient_id)
                        ), history AS (
                            SELECT cm.id, cm.sender_id, cm.body, cm.sent_at, cm.read_at,
                                   'contact' AS source_kind
                            FROM skillkind_contact_message cm JOIN pair ON pair.id = cm.contact_link_id
                            UNION ALL
                            SELECT m.id, m.sender_id, m.body, m.created_at, m.read_at, 'noncontact'
                            FROM skillkind_noncontact_message m
                            JOIN skillkind_noncontact_conversation c ON c.id = m.conversation_id
                            JOIN pair ON (c.initiator_id = pair.requester_id AND c.recipient_id = pair.recipient_id)
                                      OR (c.initiator_id = pair.recipient_id AND c.recipient_id = pair.requester_id)
                            UNION ALL
                            SELECT m.id, m.sender_id, m.body, m.sent_at, m.read_at, 'job'
                            FROM skillkind_message m
                            JOIN skillkind_message_thread t ON t.id = m.thread_id
                            JOIN pair ON (t.poster_id = pair.requester_id AND t.helper_id = pair.recipient_id)
                                      OR (t.poster_id = pair.recipient_id AND t.helper_id = pair.requester_id)
                            WHERE NOT (m.sender_id = t.poster_id AND m.id = (
                                SELECT opener.id FROM skillkind_message opener
                                WHERE opener.thread_id = t.id
                                ORDER BY opener.sent_at ASC, opener.id ASC LIMIT 1
                            ))
                        )
                        SELECT cm.id, cm.sender_id, s.display_name, CONCAT('member-', s.id),
                               cm.body, cm.sent_at, cm.read_at, cm.source_kind
                        FROM history cm JOIN skillkind_subscriber s ON s.id = cm.sender_id
                        ORDER BY cm.sent_at ASC, cm.source_kind ASC, cm.id ASC
                        LIMIT 200
                        """
                    ),
                    {"link_id": int(link_id), "sid": int(sid)},
                )
            ).all()
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_contact_message
                    SET read_at = now()
                    WHERE contact_link_id = :link_id
                      AND recipient_id = :sid
                      AND read_at IS NULL
                    """
                ),
                {"link_id": int(link_id), "sid": int(sid)},
            )
            # Clear only the notices for this one contact conversation.
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_member_notification
                    SET is_read = true, read_at = now()
                    WHERE recipient_id = :sid
                      AND contact_link_id = :link_id
                      AND is_read = false
                    """
                ),
                {"link_id": int(link_id), "sid": int(sid)},
            )
            await asession.commit()

        loaded: list[ContactMessageItem] = [
            {
                "id": int(r[0]),
                "sender_id": int(r[1]),
                "sender_name": str(r[2] or ""),
                "sender_avatar_seed": str(r[3] or ""),
                **decode_message(r[4]),
                "sent_at": _fmt_stamp(r[5]),
                "mine": int(r[1]) == int(sid),
                "read": r[6] is not None,
                "source_kind": str(r[7]),
            }
            for r in rows
        ]
        async with self:
            if (
                self.selected_contact["link_id"] == link_id
                and (await self.get_state(AuthState)).subscriber_id == sid
            ):
                self.contact_messages = loaded
                opened = self.selected_contact["status"] == "accepted"
            else:
                opened = False
            self.is_loading_messages = False
        from app.states.notification_state import NotificationState
        from app.states.unified_inbox_state import UnifiedInboxState

        if opened:
            yield UnifiedInboxState.mark_opened(f"contact:{link_id}", sid)
        yield NotificationState.load_notifications

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def send_request(self, recipient_id: int, note: str = ""):
        """Ask another traveller to become a contact."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        intro = note.strip()
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif recipient_id <= 0:
            problem = "Pick the neighbour you'd like to connect with."
        elif sid.isdigit() and int(sid) == int(recipient_id):
            problem = "You're already the best company you have."
        elif len(intro) > MAX_NOTE_LENGTH:
            problem = f"Keep your hello under {MAX_NOTE_LENGTH} characters."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_requesting = True
            self.error = ""
            self.success = ""

        async with rx.asession() as asession:
            recipient = (
                await asession.execute(
                    text(
                        """
                        SELECT s.display_name,
                               COALESCE(pr.current_city, '')
                        FROM skillkind_subscriber s
                        LEFT JOIN skillkind_profile pr
                               ON pr.subscriber_id = s.id
                        WHERE s.id = :rid AND s.is_active = TRUE
                        """
                    ),
                    {"rid": int(recipient_id)},
                )
            ).first()
            if recipient is None:
                async with self:
                    self.is_requesting = False
                    self.error = "That traveller is no longer on Go and Help."
                return
            # Symmetric authorization before any contact-link write.
            if await are_members_blocked(asession, int(sid), int(recipient_id)):
                await asession.rollback()
                async with self:
                    self.is_requesting = False
                    self.error = BLOCK_UNAVAILABLE_MESSAGE
                return
            my_city_row = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(current_city, '')
                        FROM skillkind_profile
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
            my_city = str(my_city_row[0]) if my_city_row is not None else ""
            recipient_name = str(recipient[0] or "your neighbour")
            recipient_city = str(recipient[1] or "")

            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT id, status, requester_id
                        FROM skillkind_contact_link
                        WHERE (requester_id = :sid AND recipient_id = :rid)
                           OR (requester_id = :rid AND recipient_id = :sid)
                        FOR UPDATE
                        """
                    ),
                    {"sid": int(sid), "rid": int(recipient_id)},
                )
            ).first()

            if existing is not None:
                status = str(existing[1])
                mine = int(existing[2]) == int(sid)
                if status == CONTACT_ACCEPTED:
                    async with self:
                        self.is_requesting = False
                        self.error = (
                            f"You and {recipient_name} are already contacts."
                        )
                    return
                if status == CONTACT_PENDING and mine:
                    async with self:
                        self.is_requesting = False
                        self.error = (
                            f"Your request to {recipient_name} is already waiting "
                            "for a reply."
                        )
                    return
                if status == CONTACT_PENDING and not mine:
                    async with self:
                        self.is_requesting = False
                        self.error = (
                            f"{recipient_name} already asked to connect — accept "
                            "their request instead."
                        )
                    return
                # declined / removed: revive the link as a fresh request from us.
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_contact_link
                        SET requester_id = :sid,
                            recipient_id = :rid,
                            status = 'pending',
                            intro_note = :note,
                            requester_city = :my_city,
                            recipient_city = :their_city,
                            responded_at = NULL,
                            accepted_at = NULL,
                            declined_at = NULL,
                            removed_at = NULL,
                            removed_by_id = NULL,
                            updated_at = now()
                        WHERE id = :link_id
                        """
                    ),
                    {
                        "sid": int(sid),
                        "rid": int(recipient_id),
                        "note": intro,
                        "my_city": my_city,
                        "their_city": recipient_city,
                        "link_id": int(existing[0]),
                    },
                )
            else:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_contact_link
                            (requester_id, recipient_id, status, intro_note,
                             requester_city, recipient_city, message_count,
                             last_message_preview)
                        VALUES
                            (:sid, :rid, 'pending', :note,
                             :my_city, :their_city, 0, '')
                        """
                    ),
                    {
                        "sid": int(sid),
                        "rid": int(recipient_id),
                        "note": intro,
                        "my_city": my_city,
                        "their_city": recipient_city,
                    },
                )
            await asession.execute(
                text("""
                INSERT INTO skillkind_member_notification
                    (recipient_id, actor_id, kind, title, body, contact_link_id, target_route)
                SELECT :rid, :sid, 'inbox_message', 'Contact request', '', cl.id, 'contacts:request'
                FROM skillkind_contact_link cl
                WHERE cl.requester_id=:sid AND cl.recipient_id=:rid AND cl.status='pending'
                  AND NOT EXISTS (SELECT 1 FROM skillkind_member_notification n
                      WHERE n.recipient_id=:rid AND n.actor_id=:sid
                        AND n.contact_link_id=cl.id AND n.target_route='contacts:request')
                ON CONFLICT DO NOTHING
            """),
                {"sid": int(sid), "rid": int(recipient_id)},
            )
            await asession.commit()

        async with self:
            self.is_requesting = False
            self.success = (
                f"Contact request sent to {recipient_name} — we'll let you know "
                "when they say hello back."
            )
        yield rx.toast(
            f"Contact request sent to {recipient_name}.", duration=3500
        )
        yield ContactsState.load_contacts
        yield ContactsState.search_people

    @rx.event(background=True)
    async def accept_request(self, link_id: int):
        """Confirm an incoming contact request."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.is_responding = True
            self.error = ""
            self.success = ""

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT cl.status, s.display_name
                        FROM skillkind_contact_link cl
                        JOIN skillkind_subscriber s ON s.id = cl.requester_id
                        WHERE cl.id = :link_id AND cl.recipient_id = :sid
                        FOR UPDATE OF cl
                        """
                    ),
                    {"link_id": int(link_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.is_responding = False
                    self.error = (
                        "That contact request is no longer waiting for you."
                    )
                return
            if str(row[0]) != CONTACT_PENDING:
                async with self:
                    self.is_responding = False
                    self.error = "That request has already been answered."
                yield ContactsState.load_contacts
                return
            other_name = str(row[1] or "your neighbour")
            requester_row = (
                await asession.execute(
                    text(
                        """
                        SELECT requester_id FROM skillkind_contact_link
                        WHERE id = :link_id
                        """
                    ),
                    {"link_id": int(link_id)},
                )
            ).first()
            if requester_row is None or await are_members_blocked(
                asession, int(sid), int(requester_row[0])
            ):
                await asession.rollback()
                async with self:
                    self.is_responding = False
                    self.error = BLOCK_UNAVAILABLE_MESSAGE
                yield ContactsState.load_contacts
                return
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_contact_link
                    SET status = 'accepted',
                        responded_at = now(),
                        accepted_at = now(),
                        declined_at = NULL,
                        removed_at = NULL,
                        removed_by_id = NULL,
                        updated_at = now()
                    WHERE id = :link_id
                    """
                ),
                {"link_id": int(link_id)},
            )
            await asession.execute(
                text("""
                INSERT INTO skillkind_member_notification
                    (recipient_id, actor_id, kind, title, body, contact_link_id, target_route)
                SELECT requester_id, :sid, 'inbox_message', 'Contact accepted', '', id, 'contacts:accepted'
                FROM skillkind_contact_link cl
                WHERE id=:lid AND recipient_id=:sid AND status='accepted'
                  AND NOT EXISTS (SELECT 1 FROM skillkind_member_notification n
                      WHERE n.recipient_id=cl.requester_id AND n.actor_id=:sid
                        AND n.contact_link_id=cl.id AND n.target_route='contacts:accepted')
                ON CONFLICT DO NOTHING
            """),
                {"sid": int(sid), "lid": int(link_id)},
            )
            await asession.commit()

        async with self:
            self.is_responding = False
            self.success = (
                f"{other_name} is now one of your contacts — say hello whenever "
                "you're passing through."
            )
        yield rx.toast(f"{other_name} added to your contacts.", duration=3500)
        yield ContactsState.load_contacts
        yield ContactsState.search_people

    @rx.event(background=True)
    async def decline_request(self, link_id: int):
        """Politely decline an incoming contact request."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            selected_id = self.selected_contact["link_id"]
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.is_responding = True
            self.error = ""
            self.success = ""

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT cl.status, s.display_name
                        FROM skillkind_contact_link cl
                        JOIN skillkind_subscriber s ON s.id = cl.requester_id
                        WHERE cl.id = :link_id AND cl.recipient_id = :sid
                        """
                    ),
                    {"link_id": int(link_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.is_responding = False
                    self.error = (
                        "That contact request is no longer waiting for you."
                    )
                return
            if str(row[0]) != CONTACT_PENDING:
                async with self:
                    self.is_responding = False
                    self.error = "That request has already been answered."
                yield ContactsState.load_contacts
                return
            other_name = str(row[1] or "your neighbour")
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_contact_link
                    SET status = 'declined',
                        responded_at = now(),
                        declined_at = now(),
                        accepted_at = NULL,
                        updated_at = now()
                    WHERE id = :link_id
                    """
                ),
                {"link_id": int(link_id)},
            )
            await asession.commit()

        async with self:
            self.is_responding = False
            if selected_id == link_id:
                self.selected_contact = EMPTY_CONTACT
                self.contact_messages = []
            self.success = f"Request from {other_name} declined — no hard feelings on the road."
        yield rx.toast("Contact request declined.", duration=3000)
        yield ContactsState.load_contacts
        yield ContactsState.search_people

    @rx.event(background=True)
    async def remove_contact(self, link_id: int):
        """Remove a confirmed contact from your travelling circle."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            selected_id = self.selected_contact["link_id"]
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.is_responding = True
            self.error = ""
            self.success = ""

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT cl.status,
                               CASE WHEN cl.requester_id = :sid
                                    THEN recipient.display_name
                                    ELSE requester.display_name END
                        FROM skillkind_contact_link cl
                        JOIN skillkind_subscriber requester
                          ON requester.id = cl.requester_id
                        JOIN skillkind_subscriber recipient
                          ON recipient.id = cl.recipient_id
                        WHERE cl.id = :link_id
                          AND (cl.requester_id = :sid OR cl.recipient_id = :sid)
                        """
                    ),
                    {"link_id": int(link_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.is_responding = False
                    self.error = "We couldn't find that contact in your circle."
                return
            if str(row[0]) != CONTACT_ACCEPTED:
                async with self:
                    self.is_responding = False
                    self.error = "Only confirmed contacts can be removed."
                yield ContactsState.load_contacts
                return
            other_name = str(row[1] or "your neighbour")
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_contact_link
                    SET status = 'removed',
                        removed_at = now(),
                        removed_by_id = :sid,
                        updated_at = now()
                    WHERE id = :link_id
                    """
                ),
                {"link_id": int(link_id), "sid": int(sid)},
            )
            await asession.commit()

        async with self:
            self.is_responding = False
            if selected_id == link_id:
                self.selected_contact = EMPTY_CONTACT
                self.contact_messages = []
            self.success = (
                f"{other_name} is no longer in your contacts. You can always "
                "reconnect later."
            )
        yield rx.toast("Contact removed.", duration=3000)
        yield ContactsState.load_contacts
        yield ContactsState.search_people

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    @rx.event
    async def send_contact_message(self, form_data: dict[str, Any]):
        from app.states.message_attachment_state import MessageAttachmentState
        from app.states.unified_inbox_state import UnifiedInboxState

        if self.is_sending:
            return
        attachments = await self.get_state(MessageAttachmentState)
        compose_id = str(form_data.get("compose_link_id", ""))
        contact = dict(self.selected_contact)
        if compose_id:
            contact = next(
                (
                    dict(c)
                    for c in self.contacts
                    if str(c["link_id"]) == compose_id
                    and c["status"] == CONTACT_ACCEPTED
                ),
                dict(EMPTY_CONTACT),
            )
        body = str(form_data.get("body", "") or "").strip()
        sid = (await self.get_state(AuthState)).subscriber_id
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif contact["link_id"] <= 0:
            problem = "Open a contact conversation first."
        elif contact["status"] != CONTACT_ACCEPTED:
            problem = "You can only message confirmed contacts — wait until your request is accepted."
        elif not body and (compose_id or not attachments.pending):
            problem = "Write a few words before sending."
        elif len(body) > MAX_MESSAGE_LENGTH:
            problem = f"Keep messages under {MAX_MESSAGE_LENGTH} characters."
        if problem:
            self.error = problem
            self.success = ""
            return
        self.is_sending = True
        self.error = ""
        self.success = ""
        try:
            await attachments._persist(
                "contact",
                contact["link_id"],
                body,
                bool(compose_id),
                str(form_data.get("conversation_key", "")),
            )
            if compose_id:
                unified = await self.get_state(UnifiedInboxState)
                await unified._clear_selections()
                self.selected_contact = contact
                unified.view = "thread"
                unified.selected_key = f"contact:{contact['link_id']}"
                self.compose_search = ""
                self.compose_generation += 1
            self.success = f"Message sent to {contact['other_name']}."
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
        yield ContactsState.load_contact_messages
        yield ContactsState.load_contacts
        yield UnifiedInboxState.load_index
