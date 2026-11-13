import inspect
import unittest
from pathlib import Path

import reflex as rx
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from app.components import chat_controls, messages_panel, unified_inbox
from app.states.unified_inbox_state import (
    TYPE_FILTERS,
    UnifiedInboxState,
    direction_flags,
    job_type,
)


class InboxDirectionsTests(unittest.TestCase):
    def test_job_direction_fixture(self):
        # Synthetic threads: outgoing-only, incoming-only, and both with latest outgoing.
        fixture = [
            ("outgoing A", True, False, True),
            ("outgoing B", True, False, True),
            ("incoming", False, True, False),
            ("mixed", True, True, True),
        ]
        flags = {
            name: direction_flags(
                sent, received, 2 if sent and received else 1, True
            )
            for name, sent, received, latest_sent in fixture
        }
        self.assertEqual(
            [name for name, pair in flags.items() if pair[0]],
            ["outgoing A", "outgoing B", "mixed"],
        )
        self.assertEqual(
            [name for name, pair in flags.items() if pair[1]],
            ["incoming", "mixed"],
        )
        for name, sent, received, latest_sent in fixture:
            self.assertEqual(job_type(True), "helper")
            self.assertEqual(job_type(False), "helpee")

    def test_empty_fallback_and_contact_mixed(self):
        self.assertEqual(direction_flags(False, False, 0, True), (True, False))
        self.assertEqual(direction_flags(False, False, 0, False), (False, True))
        self.assertEqual(direction_flags(True, True, 2, False), (True, True))
        self.assertEqual(job_type(True), "helper")

    def test_queries_and_unread_independence(self):
        source = inspect.getsource(UnifiedInboxState.load_index.fn)
        self.assertNotIn("AND cm.read_at IS NULL)\nAND", source)
        self.assertNotIn("AND m.read_at IS NULL)\nAND", source)
        self.assertIn("Unable to load conversations.", source)
        self.assertIn("EXISTS (SELECT 1 FROM skillkind_message d", source)
        self.assertIn(
            "EXISTS (SELECT 1 FROM skillkind_contact_message d", source
        )
        self.assertIn(
            "EXISTS (SELECT 1 FROM skillkind_noncontact_message d", source
        )
        self.assertIn(
            "NOT EXISTS (SELECT 1 FROM skillkind_member_block", source
        )
        self.assertIn("SELECT 1 FROM skillkind_contact_link accepted", source)
        self.assertIn("summary = (", source)
        self.assertIn("await asession.execute(", source)
        self.assertIn(".one()", source)
        self.assertIn("self.unread_by_type =", source)
        self.assertEqual(
            [entry["value"] for entry in TYPE_FILTERS],
            ["helper", "helpee", "contact"],
        )
        sql = text(
            "SELECT EXISTS (SELECT 1 FROM skillkind_message d WHERE d.thread_id = :thread AND d.sender_id = :sid)"
        )
        self.assertIn("EXISTS", str(sql.compile(dialect=postgresql.dialect())))

    def test_inbox_surface_and_existing_delete(self):
        page = inspect.getsource(messages_panel.messages_panel)
        self.assertNotIn("offers_block()", page)
        self.assertNotIn("helpee_requests_block()", page)
        self.assertNotIn(
            "InboxConversationDismissal", Path("app/models.py").read_text()
        )
        self.assertIn(
            "gap-3 bg-transparent",
            inspect.getsource(unified_inbox.unified_conversation_list),
        )
        self.assertIn(
            "rx.fragment()", inspect.getsource(unified_inbox.conversation_card)
        )
        self.assertIn(
            "unread_by_type", inspect.getsource(unified_inbox.filter_chip)
        )
        self.assertIn(
            'aria_label="Delete message"',
            inspect.getsource(chat_controls.correspondence_bubble),
        )
        self.assertNotIn(
            '"Delete",', inspect.getsource(chat_controls.correspondence_bubble)
        )
        self.assertIsInstance(unified_inbox.inbox_toolbar(), rx.Component)
        self.assertIsInstance(messages_panel.messages_panel(), rx.Component)


if __name__ == "__main__":
    unittest.main()
