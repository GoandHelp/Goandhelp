import reflex as rx

import inspect
import unittest
from pathlib import Path

from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState
from app.states.contacts_state import ContactsState, EMPTY_CONTACT
from app.states.message_attachment_state import MessageAttachmentState
from app.states.unified_inbox_state import UnifiedInboxState, TYPE_FILTERS


class InboxWorkspaceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state = UnifiedInboxState(_reflex_internal_init=True)
        self.contacts = await self.state.get_state(ContactsState)
        self.profile = await self.state.get_state(ProfileState)
        self.auth = await self.state.get_state(AuthState)
        self.state.view = "inbox"
        self.state.search = ""
        self.state.filters_open = False
        self.contacts.contacts = []
        self.contacts.is_sending = False
        self.contacts.compose_link_id = ""
        self.contacts.compose_search = ""

    def accepted(self):
        return {
            **EMPTY_CONTACT,
            "link_id": 7,
            "other_id": 8,
            "other_name": "Test Recipient",
            "other_username": "recipient_handle",
            "other_handle": "@recipient_handle",
            "status": "accepted",
            "can_message": True,
        }

    async def test_filters_and_clear_reset_search(self):
        self.assertEqual(
            [x["value"] for x in TYPE_FILTERS],
            ["helper", "helpee", "contact"],
        )
        self.state.search = "needle"
        before = self.state.search_generation
        for value in [x["value"] for x in TYPE_FILTERS]:
            UnifiedInboxState.set_type_filter.fn(self.state, value)
            self.assertEqual(self.state.type_filter, value)
        UnifiedInboxState.set_type_filter.fn(self.state, "sent")
        self.assertEqual(self.state.type_filter, "all")
        UnifiedInboxState.set_type_filter.fn(self.state, "received")
        self.assertEqual(self.state.type_filter, "all")
        UnifiedInboxState.toggle_filters.fn(self.state)
        self.assertTrue(self.state.filters_open)
        UnifiedInboxState.toggle_filters.fn(self.state)
        self.assertFalse(self.state.filters_open)
        UnifiedInboxState.toggle_filters.fn(self.state)
        event = UnifiedInboxState.clear_filters.fn(self.state)
        self.assertTrue(self.state.filters_open)
        self.assertEqual(self.state.type_filter, "all")
        self.assertEqual(self.state.search, "")
        self.assertEqual(self.state.search_generation, before + 1)
        self.assertIsNotNone(event)

    async def test_guarded_workspace_events(self):
        self.profile.active_tab = "profile"
        await UnifiedInboxState.open_compose.fn(self.state, 0)
        await UnifiedInboxState.open_contacts.fn(self.state)
        self.assertEqual(self.state.view, "inbox")
        self.profile.active_tab = "inbox"
        self.contacts.contacts = [self.accepted()]
        await UnifiedInboxState.open_compose.fn(self.state, 999)
        self.assertEqual(self.state.view, "inbox")
        self.assertEqual(self.profile.active_tab, "inbox")

    async def test_recipient_selection_and_edit(self):
        self.contacts.contacts = [self.accepted()]
        ContactsState.set_compose_search.fn(self.contacts, "@recipient")
        self.assertEqual(len(self.contacts.compose_options), 1)
        ContactsState.set_compose_search.fn(self.contacts, "Test Rec")
        self.assertEqual(len(self.contacts.compose_options), 1)
        ContactsState.set_compose_target.fn(self.contacts, "7")
        self.assertTrue(self.contacts.compose_ready)
        self.assertEqual(self.contacts.compose_search, "Test Recipient")
        ContactsState.set_compose_search.fn(self.contacts, "missing")
        self.assertFalse(self.contacts.compose_ready)
        self.assertEqual(len(self.contacts.compose_options), 0)
        ContactsState.set_compose_target.fn(self.contacts, "999")
        self.assertFalse(self.contacts.compose_ready)

    async def test_subject_validation_and_existing_send_path(self):
        self.contacts.contacts = [self.accepted()]
        ContactsState.set_compose_target.fn(self.contacts, "7")
        for data in (
            {"subject": "", "body": "hello"},
            {"subject": "x" * 121, "body": "hello"},
            {"subject": "Hello", "body": " "},
            {"subject": "Hello", "body": "x" * 2000},
        ):
            self.assertIsNone(
                ContactsState.compose_and_send.fn(self.contacts, data)
            )
            self.assertTrue(self.contacts.error)
        event = ContactsState.compose_and_send.fn(
            self.contacts,
            {"subject": "  A friendly\nhello ", "body": "How are you?"},
        )
        self.assertIsNotNone(event)
        self.assertIn("Subject: A friendly hello", str(event))
        self.assertIn("How are you?", str(event))
        self.assertEqual(self.contacts.selected_contact["link_id"], 7)

    async def test_country_defaults_and_resolution(self):
        row = [
            7,
            1,
            8,
            "accepted",
            "",
            0,
            "",
            None,
            None,
            8,
            "Recipient",
            "member-8",
            "",
            "",
            0,
            None,
            None,
            False,
            "recipient",
            "",
        ]
        old = self.contacts._row_to_contact(row, 1)
        self.assertEqual(old["country_flag"], "")
        current = self.contacts._row_to_contact([*row, "British"], 1)
        self.assertEqual(current["nationality"], "United Kingdom")
        self.assertEqual(current["country_code"], "GB")
        self.assertEqual(current["country_flag"], "🇬🇧")

    def test_source_contracts(self):
        index = Path("app/states/unified_inbox_state.py").read_text()
        self.assertEqual(index.count('"direction": "sent"'), 3)
        self.assertIn("EXISTS (SELECT 1 FROM skillkind_message d", index)
        for ordering in (
            "cm.sent_at DESC, cm.id DESC",
            "m.created_at DESC, m.id DESC",
            "m.sent_at DESC, m.id DESC",
        ):
            self.assertIn(ordering, index)
        self.assertIn("skillkind_member_block", index)
        self.assertIn("await profile.return_to_map()", index)
        self.assertIn(
            'DiscoveryState.open_member_profile(contact["other_id"])', index
        )
        ui = Path("app/components/unified_inbox.py").read_text()
        for token in (
            '"mail-plus"',
            '"hand"',
            '"hand-helping"',
            '"users-round"',
            'item["job_title"]',
            'item["preview"]',
            "gap-3 bg-transparent",
            "mt-2 flex w-full min-w-0",
        ):
            self.assertIn(token, ui)
        safety = Path("app/components/chat_safety.py").read_text()
        for token in (
            "ContactsState.send_request",
            "report_button",
            "block_member_button",
            "Already a contact",
            "Contact request pending",
        ):
            self.assertIn(token, safety)
        send = inspect.getsource(ContactsState.send_contact_message.fn)
        for token in (
            "await self.get_state(MessageAttachmentState)",
            "await attachments._persist(",
            '"contact",',
            'contact["link_id"],',
            "bool(compose_id)",
            "await unified._clear_selections()",
            'unified.view = "thread"',
            'self.compose_search = ""',
            "unified.selected_key = f\"contact:{contact['link_id']}\"",
        ):
            self.assertIn(token, send)
        self.assertLess(
            send.index("await attachments._persist("),
            send.index('unified.view = "thread"'),
        )
        persist = inspect.getsource(MessageAttachmentState._persist)
        for token in (
            "not auth.is_signed_in or not sid.isdigit()",
            'accepted = "AND p.status = \'accepted\'" if kind == "contact" else ""',
            "s.id = :sid AND s.is_active",
            "FOR UPDATE OF p",
            "if row is None:",
            "if inserted.first() is None:",
            "await session.commit()",
        ):
            self.assertIn(token, persist)
        authorization, record = persist.split(
            "inserted = await session.execute(", 1
        )
        record = record.split("updates = (", 1)[0]
        for guarded_sql in (authorization, record):
            for token in (
                "WHERE p.id = :ref AND :sid IN (p.{first}, p.{second}) {accepted}",
                "AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b",
                "b.blocker_id = p.{first} AND b.blocked_id = p.{second}",
                "b.blocker_id = p.{second} AND b.blocked_id = p.{first}",
            ):
                self.assertIn(token, guarded_sql)
        self.assertIn("INSERT INTO {table}", record)
        self.assertIn("RETURNING id", record)

    def test_bubble_accepts_legacy_dicts_and_vars(self):
        from app.components.chat_controls import correspondence_bubble

        legacy = {
            "id": 1,
            "body": "A legacy message",
            "mine": True,
            "sent_at": "Today",
        }
        original = dict(legacy)
        normalized = {"photos": [], **legacy}
        self.assertEqual(
            str(correspondence_bubble(legacy)),
            str(correspondence_bubble(rx.Var.create(normalized))),
        )
        self.assertEqual(legacy, original)
        with_photos = {**legacy, "photos": ["message_example.webp"]}
        self.assertEqual(
            str(correspondence_bubble(with_photos)),
            str(
                correspondence_bubble(
                    rx.Var.create({"photos": [], **with_photos})
                )
            ),
        )

    def test_component_builds(self):
        from app.components.messages_panel import messages_panel
        from app.components.unified_inbox import inbox_contacts_view

        for factory in (messages_panel, inbox_contacts_view):
            self.assertIsInstance(factory(), rx.Component)


if __name__ == "__main__":
    unittest.main()
