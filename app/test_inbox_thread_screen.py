import reflex as rx

import inspect
import unittest

from app.components import (
    chat_controls,
    contacts_panel,
    feedback,
    messages_panel,
    noncontact_panel,
    profile_tabs,
    unified_inbox,
)
from app.states.auth_state import AuthState
from app.states.contacts_state import ContactsState, EMPTY_CONTACT
from app.states.messaging_state import MessagingState, EMPTY_THREAD
from app.states.noncontact_state import (
    NonContactMessagingState,
    EMPTY_CONVERSATION,
)
from app.states.profile_state import ProfileState
from app.states.unified_inbox_state import UnifiedInboxState


class InboxThreadScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_open_and_back_preserve_each_kind_and_filters(self):
        state = UnifiedInboxState(_reflex_internal_init=True)
        auth = await state.get_state(AuthState)
        auth.subscriber_id = "41"
        auth.email = "member@example.com"
        profile = await state.get_state(ProfileState)
        profile.active_tab = "inbox"
        state.search = "saved search"
        state.type_filter = "helper"
        state.filters_open = True
        for kind in ("contact", "noncontact", "job"):
            event = await state._open_item(kind, 7)
            self.assertIsNotNone(event)
            self.assertEqual(state.view, "thread")
            self.assertEqual(state.selected_key, f"{kind}:7")
            contacts = await state.get_state(ContactsState)
            messaging = await state.get_state(MessagingState)
            direct = await state.get_state(NonContactMessagingState)
            contacts.selected_contact = {**EMPTY_CONTACT, "link_id": 7}
            messaging.selected_thread = {**EMPTY_THREAD, "id": 7}
            direct.selected = {**EMPTY_CONVERSATION, "conv_id": 7}
            generation = messaging.composer_generation
            await UnifiedInboxState.back_to_inbox.fn(state)
            self.assertEqual(state.view, "inbox")
            self.assertEqual(state.selected_key, f"{kind}:7")
            self.assertEqual(contacts.selected_contact["link_id"], 7)
            self.assertEqual(messaging.selected_thread["id"], 7)
            self.assertEqual(direct.selected["conv_id"], 7)
            self.assertEqual(messaging.composer_generation, generation)
            self.assertEqual(
                (state.search, state.type_filter), ("saved search", "helper")
            )
            self.assertTrue(state.filters_open)

    async def test_clear_and_preserved_deep_link(self):
        state = UnifiedInboxState(_reflex_internal_init=True)
        state.search = "query"
        state.type_filter = "contact"
        state.filters_open = True
        generation = state.search_generation
        UnifiedInboxState.clear_filters.fn(state)
        self.assertEqual((state.search, state.type_filter), ("", "all"))
        self.assertEqual(state.search_generation, generation + 1)
        self.assertTrue(state.filters_open)
        state.selected_key = "job:7"
        state.preserve_next_mount = True
        await UnifiedInboxState.reset_disclosures.fn(state)
        self.assertEqual((state.view, state.selected_key), ("thread", "job:7"))

    def test_toolbar_and_rows(self):
        toolbar = unified_inbox.inbox_toolbar()
        search, funnel, new = toolbar.children[0].children
        self.assertIn("flex-1", str(search.class_name))
        self.assertIn("gah-inbox-search", str(search))
        self.assertIn("aria-expanded", str(funnel))
        self.assertIn("aria-controls", str(funnel))
        self.assertIn("Filters", str(funnel))
        self.assertEqual(len(funnel.children), 1)
        self.assertIn("New", str(new))
        self.assertNotIn("Refresh conversations", str(toolbar))
        self.assertIn("hidden", str(toolbar.children[1].class_name))
        self.assertIn("clear_filters", str(toolbar.children[1]))
        row = inspect.getsource(unified_inbox.conversation_card)
        self.assertIn("size-16", row)
        self.assertIn("truncate", row)
        self.assertIn("open_item", row)
        self.assertNotIn("reader-", row)
        self.assertNotIn("rounded-2xl", row)
        self.assertNotIn("pane,", row)

    def test_dedicated_layout_and_original_send_controls(self):
        view = messages_panel.inbox_thread_view()
        self.assertIsInstance(view, rx.Component)
        self.assertTrue(view.render())
        source = inspect.getsource(messages_panel.inbox_thread_view)
        for token in (
            "back_to_inbox()",
            "flex-1 min-h-0",
            "overflow-y-auto",
            "shrink-0",
            "visualViewport",
            "gah-bottom-dock",
            "reading_pane(True)",
        ):
            self.assertIn(token, source)
        self.assertNotIn("max-h-96", chat_controls.HISTORY_CLASS)
        for component, event in (
            (messages_panel.composer, "send_message"),
            (contacts_panel.composer, "send_contact_message"),
            (noncontact_panel.reply_composer, "send_reply"),
        ):
            self.assertIn(event, inspect.getsource(component))
            self.assertTrue(component().render())
        self.assertIn(
            "dedicated", inspect.getsource(contacts_panel.conversation_panel)
        )
        self.assertIn(
            "dedicated",
            inspect.getsource(noncontact_panel.noncontact_conversation_view),
        )
        self.assertIn(
            "job_chat_actions()",
            inspect.getsource(messages_panel.job_conversation_panel),
        )
        self.assertIn(
            "safety_report_card()",
            inspect.getsource(messages_panel.job_conversation_panel),
        )

    def test_only_profile_success_requests_centering(self):
        self.assertIn(
            "success_banner(ProfileState.success, centered=True)",
            inspect.getsource(profile_tabs.profile_screen),
        )
        self.assertIn(
            "centered: bool = False", inspect.getsource(feedback.success_banner)
        )
        self.assertIn(
            "justify-center text-center",
            str(feedback.success_banner("Photo updated", centered=True)),
        )


if __name__ == "__main__":
    unittest.main()
