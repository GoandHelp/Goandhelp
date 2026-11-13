import reflex as rx

import inspect
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from test_utils import run_event
from app.components import (
    messages_panel,
    chat_controls,
    discover_panel,
    help_hub_panel,
)
from app.states.auth_state import AuthState
from app.states.contacts_state import ContactsState, EMPTY_CONTACT
from app.states.messaging_state import MessagingState, EMPTY_THREAD
from app.states.noncontact_state import (
    NonContactMessagingState,
    EMPTY_CONVERSATION,
)
from app.states.message_deletion_state import MessageDeletionState
from app.states.unified_inbox_state import UnifiedInboxState


class CommunicationGroupsTests(unittest.IsolatedAsyncioTestCase):
    async def test_independent_disclosures_and_mount_reset(self):
        state = UnifiedInboxState()
        self.assertFalse(state.messages_open)
        self.assertFalse(state.offers_open)
        await run_event(state.toggle_messages)
        await run_event(state.toggle_offer, 4)
        await run_event(state.toggle_offer, 5)
        self.assertEqual(state.open_offer_ids, [4, 5])
        await run_event(state.toggle_offer, 4)
        self.assertEqual(state.open_offer_ids, [5])
        await run_event(state.reset_disclosures)
        self.assertFalse(state.messages_open)
        self.assertEqual(state.open_offer_ids, [])

    def test_cta_and_sections(self):
        cta = inspect.getsource(discover_panel.direct_help_section)
        self.assertIn('"Request Direct help"', cta)
        self.assertIn('class_name="mx-auto flex w-fit', cta)
        self.assertIn("on_click=DiscoveryState.open_direct_help", cta)
        page = inspect.getsource(messages_panel.messages_panel)
        self.assertIn("messages_block()", page)
        self.assertNotIn("offers_block()", page)
        self.assertNotIn("helpee_requests_block()", page)
        block = inspect.getsource(messages_panel.messages_block)
        self.assertIn("conversation_column()", block)
        self.assertIn('id="inbox-messages"', block)
        self.assertNotIn("UnifiedInboxState.result_count", block)
        self.assertNotIn("rx.cond(", block)
        self.assertNotIn("UnifiedInboxState.messages_open", block)
        self.assertNotIn("inbox_disclosure(", block)
        column = inspect.getsource(messages_panel.conversation_column)
        self.assertIn("unified_conversation_list(reading_pane())", column)
        self.assertNotIn("UnifiedInboxState.messages_open", column)
        for count, label in ((0, "Messages"), (1, "Message"), (2, "Messages")):
            component = messages_panel.inbox_disclosure(
                "Messages from contacts",
                rx.Var.create(count),
                rx.Var.create(False),
                UnifiedInboxState.toggle_messages,
                "inbox-messages",
            )
            self.assertIn(f"{label} from contacts", str(component))
            self.assertTrue(component.render())

    def test_offer_structure_and_actions(self):
        summary = inspect.getsource(messages_panel.offer_disclosure)
        self.assertLess(
            summary.index('offer["helper_name"]'), summary.index("Offered")
        )
        self.assertLess(
            summary.index("Offered"),
            summary.index("Helper offering you help for:"),
        )
        for token in (
            "aria_expanded",
            "aria_controls",
            "open_offer_ids.contains",
            "toggle_offer",
            "avatar_with_tick",
        ):
            self.assertIn(token, summary)
        details = inspect.getsource(help_hub_panel.help_offer_card)
        self.assertLess(
            details.index("confirm_application"),
            details.index('offer["pitch"]'),
        )
        self.assertLess(
            details.index("deny_application"), details.index('offer["pitch"]')
        )
        self.assertIn("This helper didn't add a message.", details)
        self.assertIn("detail_body", details)
        requests = inspect.getsource(messages_panel.helpee_request_card)
        self.assertIn("accept_direct_request", requests)
        self.assertIn("decline_direct_request", requests)

    def test_sql_contracts(self):
        from app.states import (
            contacts_state,
            help_hub_state,
            unified_inbox_state,
        )
        from app import models

        history = inspect.getsource(contacts_state)
        merge = history[
            history.index("WITH pair AS") : history.index("FROM history cm")
        ]
        self.assertEqual(merge.count("UNION ALL"), 2)
        for token in (
            "skillkind_contact_message",
            "skillkind_noncontact_message",
            "skillkind_message_thread",
            "status = 'accepted'",
            "m.sender_id = t.poster_id",
            "ORDER BY opener.sent_at ASC, opener.id ASC",
        ):
            self.assertIn(token, merge)
        self.assertIn(
            "ORDER BY cm.sent_at ASC, cm.source_kind ASC, cm.id ASC", history
        )
        self.assertIn("LIMIT 200", history)
        self.assertIn("UPDATE skillkind_contact_message", history)
        self.assertIn("yield NotificationState.load_notifications", history)
        index = inspect.getsource(unified_inbox_state)
        self.assertGreaterEqual(index.count("accepted.status = 'accepted'"), 2)
        offers = inspect.getsource(help_hub_state)
        self.assertIn("SELECT opener.sender_id", offers)
        self.assertIn(") = a.helper_id", offers)
        self.assertFalse(hasattr(models, "InboxMessageDismissal"))

    async def test_authorized_delete_queries_and_reload(self):
        for merged in (False, True):
            for kind in ("contact", "noncontact", "job"):
                with self.subTest(kind=kind, merged=merged):
                    state = MessageDeletionState()
                    (await state.get_state(AuthState)).subscriber_id = "12"
                    (await state.get_state(ContactsState)).selected_contact = {
                        **EMPTY_CONTACT,
                        "link_id": 3,
                    }
                    (
                        await state.get_state(NonContactMessagingState)
                    ).selected = {**EMPTY_CONVERSATION, "conv_id": 4}
                    (await state.get_state(MessagingState)).selected_thread = {
                        **EMPTY_THREAD,
                        "id": 5,
                    }
                    result = MagicMock()
                    result.first.return_value = (3,)
                    session = AsyncMock()
                    session.execute.return_value = result
                    context = AsyncMock()
                    context.__aenter__.return_value = session
                    with patch("reflex.asession", return_value=context):
                        events = []
                        async for event in state.delete_message(
                            kind, 42, merged
                        ):
                            events.append(event)
                    sql = str(session.execute.call_args_list[0].args[0])
                    params = session.execute.call_args_list[0].args[1]
                    self.assertIn("DELETE FROM", sql)
                    self.assertIn("m.id = :message_id", sql)
                    self.assertIn(":sid IN (p.", sql)
                    self.assertIn("skillkind_member_block", sql)
                    self.assertEqual(params["message_id"], 42)
                    self.assertEqual(params["sid"], 12)
                    if merged:
                        self.assertIn("cl.status = 'accepted'", sql)
                        self.assertIn("cl.id = :link_id", sql)
                    else:
                        self.assertIn("p.id = :selected", sql)
                    session.commit.assert_awaited_once()
                    self.assertEqual(state.success, "Message deleted.")
                    self.assertEqual(len(events), 2)
                    self.assertEqual(events[-1], UnifiedInboxState.load_index)

    def test_delete_before_report_and_render(self):
        bubble = inspect.getsource(chat_controls.correspondence_bubble)
        self.assertLess(
            bubble.index('aria_label="Delete message"'),
            bubble.index("report_button("),
        )
        self.assertIn("on_click=delete_event", bubble)
        for factory in (
            messages_panel.messages_panel,
            messages_panel.messages_block,
            messages_panel.offers_block,
        ):
            component = factory()
            self.assertIsInstance(component, rx.Component)
            self.assertTrue(component.render())


if __name__ == "__main__":
    unittest.main()
