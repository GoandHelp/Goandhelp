import inspect
import unittest

import reflex as rx
from test_utils import run_event

from app.components import (
    guest_map,
    header,
    member_map,
    messages_panel,
    unified_inbox,
)
from app.states.auth_state import AuthState
from app.states.block_state import BlockState
from app.states.content_report_state import ContentReportState
from app.states.discovery_state import DiscoveryState, EMPTY_HELPER, EMPTY_POST
from app.states.guest_map_state import GuestMapState
from app.states.membership_state import MembershipState
from app.states.policy_state import PolicyState
from app.states.profile_state import ProfileState
from app.states.unified_inbox_state import UnifiedInboxState


class InboxGlobalNavigationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.inbox = UnifiedInboxState(_reflex_internal_init=True)
        self.auth = await self.inbox.get_state(AuthState)
        self.profile = await self.inbox.get_state(ProfileState)
        self.auth.subscriber_id = "41"
        self.auth.email = "member@example.com"
        self.inbox.visited_account = "41"

    async def test_clear_resets_both_controls_and_input_identity(self):
        self.inbox.search = "hello"
        self.inbox.type_filter = "helper"
        self.inbox.filters_open = True
        before = self.inbox.search_generation
        self.assertIsNotNone(UnifiedInboxState.clear_filters.fn(self.inbox))
        self.assertEqual(
            (self.inbox.search, self.inbox.type_filter), ("", "all")
        )
        self.assertEqual(self.inbox.search_generation, before + 1)
        self.assertTrue(self.inbox.filters_open)
        toolbar = unified_inbox.inbox_toolbar()
        search = toolbar.children[0].children[0].children[1]
        self.assertEqual(search.id, "gah-inbox-search")
        self.assertEqual(len(toolbar.children[1].children), 2)
        clear = toolbar.children[1].children[1]
        self.assertEqual(clear.tag, "button")
        self.assertIn("clear", str(clear))
        self.assertIn("clear_filters", str(clear))
        toolbar_source = inspect.getsource(unified_inbox.inbox_toolbar)
        self.assertRegex(
            toolbar_source,
            r"on_click\s*=\s*\[\s*UnifiedInboxState\.clear_filters\s*,\s*rx\.call_script\(",
        )
        self.assertIn(
            "document.getElementById('gah-inbox-search').value = ''",
            toolbar_source,
        )
        empty_source = inspect.getsource(unified_inbox.empty_state)
        self.assertRegex(
            empty_source,
            r"on_click\s*=\s*\[\s*UnifiedInboxState\.clear_search\s*,\s*rx\.call_script\(",
        )
        self.assertIn(
            "document.getElementById('gah-inbox-search').value = ''",
            empty_source,
        )

    async def test_visited_bookkeeping_and_avatar_row(self):
        self.inbox.selected_key = "contact:8"
        await run_event(self.inbox.mark_opened, "contact:8", "wrong-account")
        self.assertEqual(self.inbox.visited_keys, [])
        await run_event(self.inbox.mark_opened, "contact:8", "41")
        self.assertEqual(self.inbox.visited_keys, ["contact:8"])
        await run_event(self.inbox.mark_opened, "contact:8", "41")
        self.assertEqual(self.inbox.visited_keys, ["contact:8"])
        self.inbox.selected_key = ""
        await run_event(self.inbox.mark_opened, "job:9", "41")
        self.assertEqual(self.inbox.visited_keys, ["contact:8"])
        self.inbox._sync_visited_account("42")
        self.assertEqual(self.inbox.visited_keys, [])
        card = inspect.getsource(unified_inbox.conversation_card)
        self.assertNotIn('"mail-open"', card)
        self.assertNotIn('"mail"', card)
        self.assertEqual(card.count("avatar_with_tick("), 1)
        self.assertIn('item["other_avatar"]', card)
        self.assertIn('item["other_verified"]', card)
        self.assertIn('item["key"]', card)
        self.assertIn('item["unread_count"] > 0', card)

    async def test_dock_closes_transient_surfaces_without_touching_filters(
        self,
    ):
        discovery = await self.profile.get_state(DiscoveryState)
        discovery.selected_post = {**EMPTY_POST, "id": 9}
        discovery.selected_helper = {**EMPTY_HELPER, "id": 3}
        discovery.group_poster_id = 4
        discovery.filter_panel_open = True
        self.inbox.search = "saved query"
        self.inbox.type_filter = "contact"
        self.inbox.view = "compose"
        self.inbox.selected_key = "job:4"
        (await self.profile.get_state(MembershipState)).paywall_open = True
        (await self.profile.get_state(PolicyState)).open_key = "privacy"
        (await self.profile.get_state(ContentReportState)).is_open = True
        (await self.profile.get_state(BlockState)).is_open = True
        (await self.profile.get_state(GuestMapState)).wall_open = True
        await run_event(self.profile.navigate_from_bottom_nav, "community", "")
        self.assertEqual(self.profile.active_tab, "community")
        self.assertEqual(discovery.selected_post["id"], 0)
        self.assertEqual(discovery.selected_helper["id"], 0)
        self.assertEqual(discovery.group_poster_id, 0)
        self.assertFalse(discovery.filter_panel_open)
        self.assertEqual(
            (self.inbox.view, self.inbox.selected_key), ("inbox", "")
        )
        self.assertEqual(
            (self.inbox.search, self.inbox.type_filter),
            ("saved query", "contact"),
        )
        self.assertFalse(
            (await self.profile.get_state(MembershipState)).paywall_open
        )
        self.assertEqual(
            (await self.profile.get_state(PolicyState)).open_key, ""
        )
        self.assertFalse(
            (await self.profile.get_state(ContentReportState)).is_open
        )
        self.assertFalse((await self.profile.get_state(BlockState)).is_open)
        self.assertFalse(
            (await self.profile.get_state(GuestMapState)).wall_open
        )
        await run_event(self.profile.return_to_map)
        self.assertEqual(self.profile.active_tab, "discover")
        self.assertEqual(discovery.view_mode, "map")

    def test_visual_contracts(self):
        toolbar = unified_inbox.inbox_toolbar()
        self.assertEqual(len(toolbar.children[0].children), 3)
        self.assertIn("open_compose", str(toolbar.children[0].children[2]))
        self.assertNotIn("My contacts", str(toolbar.children[1]))
        self.assertIn(
            "My contacts", str(unified_inbox.inbox_contacts_view().children[0])
        )
        self.assertIn(
            "Write a message", str(messages_panel.compose_area().children[0])
        )
        self.assertNotIn(
            "gah-edge-stack",
            inspect.getsource(unified_inbox.unified_conversation_list),
        )
        self.assertNotIn(
            "rounded-2xl", inspect.getsource(unified_inbox.conversation_card)
        )
        self.assertIn(
            "-translate-y-[2px]", inspect.getsource(header.page_title_icon)
        )
        for canvas in (
            member_map.member_map_canvas,
            guest_map.guest_map_canvas,
        ):
            self.assertIn("map_loading_logo()", inspect.getsource(canvas))
            self.assertIsInstance(canvas(), rx.Component)


if __name__ == "__main__":
    unittest.main()
