import reflex as rx

import ast
import inspect
import unittest
from datetime import datetime
from pathlib import Path
from test_utils import run_event
from app.notification_content import (
    concise_text,
    review_task_id,
    REVIEW_REMINDER_SQL,
)
from app.states.unified_inbox_state import UnifiedInboxState, safe_initial
from app.states.notification_state import NotificationItem, NotificationState


class ActionableNotificationsTests(unittest.IsolatedAsyncioTestCase):
    async def test_disclosures_default_toggle_reset(self):
        state = UnifiedInboxState()
        self.assertEqual(state.selected_key, "")
        self.assertFalse(state.offers_open)
        self.assertFalse(state.requests_open)
        await run_event(state.toggle_offers)
        await run_event(state.toggle_requests)
        self.assertTrue(state.offers_open)
        self.assertTrue(state.requests_open)
        await run_event(state.reset_disclosures)
        self.assertFalse(state.offers_open)
        self.assertFalse(state.requests_open)
        self.assertEqual(state.selected_key, "")

    def test_initials(self):
        for raw, expected in [
            (" alice ", "A"),
            ("Émile", "É"),
            ("", "?"),
            ("   ", "?"),
            ("<script>", "?"),
        ]:
            self.assertEqual(safe_initial(raw), expected)

    def test_safe_fields_copy_and_dates(self):
        fields = NotificationItem.__annotations__
        for forbidden in ("email", "phone", "latitude", "longitude"):
            self.assertNotIn(forbidden, fields)
        self.assertEqual(
            concise_text("inbox_message", "Alex", "", "private body"),
            "Alex sent you a message",
        )
        self.assertEqual(
            concise_text("help_offer", "Alex", "", ""),
            "Alex sent you an offer to help",
        )
        self.assertEqual(
            concise_text(
                "community_like", "Alex", "community:reviews:7", "Review helper"
            ),
            "Review Alex's help",
        )
        self.assertEqual(
            concise_text(
                "community_like",
                "Alex",
                "community:reviews:7",
                "Review your help",
            ),
            "Review your help with Alex",
        )
        self.assertEqual(review_task_id("community:reviews:7"), 7)
        self.assertEqual(review_task_id("community:reviews:bad"), 0)
        self.assertEqual(
            datetime(2026, 9, 21, 14, 44).strftime("%d %B – %H:%M"),
            "21 September – 14:44",
        )

    def test_sql_contracts(self):
        source = Path("app/states/notification_state.py").read_text()
        self.assertIn("ORDER BY n.created_at DESC, n.id DESC", source)
        self.assertIn(
            "DELETE FROM skillkind_member_notification WHERE id=:nid AND recipient_id=:sid",
            source,
        )
        self.assertIn("FOR UPDATE", source)
        for fragment in (
            "poster_confirmed",
            "helper_confirmed",
            "poster.is_active",
            "helper.is_active",
            "skillkind_member_block",
            "skillkind_review",
            "NOT EXISTS",
            "ON CONFLICT DO NOTHING",
            "n.actor_id",
            "n.help_post_id",
            "n.recipient_id",
        ):
            self.assertIn(fragment, REVIEW_REMINDER_SQL)
        for fragment in (
            "contacts:request",
            "contacts:accepted",
            "INSERT INTO skillkind_member_notification",
            "FOR UPDATE OF cl",
        ):
            self.assertIn(
                fragment, Path("app/states/contacts_state.py").read_text()
            )

    def test_destinations_and_rendering(self):
        source = ast.unparse(
            ast.parse(Path("app/states/notification_state.py").read_text())
        )
        for fragment in (
            "UnifiedInboxState.open_item('contact', contact)",
            "UnifiedInboxState.open_item('noncontact', direct)",
            "UnifiedInboxState.open_item('job', thread)",
            "CommunityState.open_notification_topic(topic)",
            "EventState.load_events",
            "MessagingState.select_review_target(task)",
            "MessagingState.open_review_target",
            "profile.active_tab = 'help'",
            "HelpHubState.load_help_hub",
        ):
            self.assertIn(fragment, source)
        from app.components.unified_inbox import conversation_card
        from app.components.messages_panel import messages_panel
        from app.components.map_utilities import notification_feed

        card = inspect.getsource(conversation_card)
        self.assertIn("avatar_with_tick", card)
        for fragment in (
            'item["unread_count"] > 0',
            'item["job_title"]',
            'item["preview"]',
            '"No messages yet"',
            "type_badge(item)",
            'UnifiedInboxState.selected_key == item["key"]',
            "UnifiedInboxState.open_item",
            "aria_current",
        ):
            self.assertIn(fragment, card)
        self.assertNotIn("aria_expanded", card)
        for factory in (messages_panel, notification_feed):
            component = factory()
            self.assertIsInstance(component, rx.Component)
            self.assertTrue(component.render())
        self.assertIn(
            "animal_avatar",
            Path("app/components/unified_inbox.py").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
