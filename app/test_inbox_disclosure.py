import reflex as rx

import unittest

from test_utils import run_event

from app.states.unified_inbox_state import UnifiedInboxState
from app.states.messaging_state import MessagingState, EMPTY_THREAD
from app.states.contacts_state import ContactsState, EMPTY_CONTACT
from app.states.noncontact_state import (
    NonContactMessagingState,
    EMPTY_CONVERSATION,
)


class InboxDisclosureTests(unittest.IsolatedAsyncioTestCase):
    async def test_toggle_each_kind_and_close_all_selections(self):
        state = UnifiedInboxState()
        messaging = await state.get_state(MessagingState)
        contacts = await state.get_state(ContactsState)
        direct = await state.get_state(NonContactMessagingState)
        for kind, handler in (
            ("job", MessagingState.select_thread),
            ("contact", ContactsState.select_contact),
            ("noncontact", NonContactMessagingState.select_conversation),
        ):
            with self.subTest(kind=kind):
                event = await state._open_item(kind, 7)
                self.assertEqual(event.handler, handler)
                await run_event(state.close_item)
                generation = messaging.composer_generation
                await run_event(state.toggle_item, kind, 7)
                self.assertEqual(state.selected_key, f"{kind}:7")
                self.assertEqual(messaging.composer_generation, generation + 1)
                messaging.selected_thread = {**EMPTY_THREAD, "id": 7}
                contacts.selected_contact = {**EMPTY_CONTACT, "link_id": 7}
                direct.selected = {**EMPTY_CONVERSATION, "conv_id": 7}
                messaging.review_target_open = True
                await run_event(state.toggle_item, kind, 7)
                self.assertEqual(messaging.composer_generation, generation + 2)
                self.assertEqual(state.selected_key, "")
                self.assertEqual(messaging.selected_thread, EMPTY_THREAD)
                self.assertEqual(contacts.selected_contact, EMPTY_CONTACT)
                self.assertEqual(direct.selected, EMPTY_CONVERSATION)
                self.assertFalse(messaging.review_target_open)
                self.assertEqual(messaging.messages, [])
                self.assertEqual(contacts.contact_messages, [])
                self.assertEqual(direct.messages, [])

    async def test_switch_kinds_and_explicit_close(self):
        state = UnifiedInboxState()
        messaging = await state.get_state(MessagingState)
        contacts = await state.get_state(ContactsState)
        direct = await state.get_state(NonContactMessagingState)
        for kind in ("job", "contact", "noncontact", "job"):
            messaging.selected_thread = {**EMPTY_THREAD, "id": 11}
            contacts.selected_contact = {**EMPTY_CONTACT, "link_id": 12}
            direct.selected = {**EMPTY_CONVERSATION, "conv_id": 13}
            await run_event(state.toggle_item, kind, 9)
            self.assertEqual(state.selected_key, f"{kind}:9")
            self.assertEqual(messaging.selected_thread, EMPTY_THREAD)
            self.assertEqual(contacts.selected_contact, EMPTY_CONTACT)
            self.assertEqual(direct.selected, EMPTY_CONVERSATION)
        await run_event(state.close_item)
        await run_event(state.close_item)
        self.assertEqual(state.selected_key, "")
        self.assertEqual(messaging.selected_thread, EMPTY_THREAD)
        self.assertEqual(contacts.selected_contact, EMPTY_CONTACT)
        self.assertEqual(direct.selected, EMPTY_CONVERSATION)

    async def test_public_open_each_kind_does_not_toggle_closed(self):
        state = UnifiedInboxState()
        messaging = await state.get_state(MessagingState)
        for kind in ("job", "contact", "noncontact"):
            with self.subTest(kind=kind):
                for _ in range(2):
                    generation = messaging.composer_generation
                    await run_event(state.open_item, kind, 7)
                    self.assertEqual(state.selected_key, f"{kind}:7")
                    self.assertEqual(
                        messaging.composer_generation, generation + 1
                    )

    async def test_invalid_target_does_not_change_selection(self):
        state = UnifiedInboxState()
        messaging = await state.get_state(MessagingState)
        contacts = await state.get_state(ContactsState)
        direct = await state.get_state(NonContactMessagingState)
        messaging.selected_thread = {**EMPTY_THREAD, "id": 9}
        contacts.selected_contact = {**EMPTY_CONTACT, "link_id": 9}
        direct.selected = {**EMPTY_CONVERSATION, "conv_id": 9}
        messaging.review_target_open = True
        generation = messaging.composer_generation
        for handler in (state.open_item, state.toggle_item):
            for kind, ref_id in (
                ("invalid", 8),
                ("", 8),
                ("job", 0),
                ("contact", -1),
                ("noncontact", 0),
            ):
                for selected_key in ("job:9", f"{kind}:{ref_id}"):
                    with self.subTest(
                        kind=kind, ref_id=ref_id, selected=selected_key
                    ):
                        state.selected_key = selected_key
                        state.error = "Existing feedback"
                        await run_event(handler, kind, ref_id)
                        self.assertEqual(state.selected_key, selected_key)
                        self.assertEqual(state.error, "Existing feedback")
                        self.assertEqual(messaging.selected_thread["id"], 9)
                        self.assertEqual(
                            contacts.selected_contact["link_id"], 9
                        )
                        self.assertEqual(direct.selected["conv_id"], 9)
                        self.assertTrue(messaging.review_target_open)
                        self.assertEqual(
                            messaging.composer_generation, generation
                        )

    def test_component_trees(self):
        from app.components.messages_panel import messages_panel
        from app.components.member_map import member_map_experience
        from app.components.guest_map import guest_map_experience
        from app.components.header import (
            header,
            minimal_header,
            contextual_header,
        )

        for factory in (
            messages_panel,
            member_map_experience,
            guest_map_experience,
            header,
            minimal_header,
            contextual_header,
        ):
            with self.subTest(component=factory.__name__):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
