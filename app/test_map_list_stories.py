import reflex as rx

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components import discover_panel as ui
from app.components.member_map import member_map_experience
from app.components.help_hub_panel import duration_field
from app.components.paywall import ticket_to_ride_choice, annual_pass_choice
from app.states.discovery_state import (
    DiscoveryState,
    EMPTY_POST,
    VIEW_LIST,
    VIEW_MAP,
)
from app.states.notification_state import NotificationState


class StoryLayoutTests(unittest.TestCase):
    def test_global_and_inline_gates(self):
        panel = inspect.getsource(ui.detail_panel)
        self.assertIn("DiscoveryState.drawer_open", panel)
        self.assertNotIn("max-w-", panel)
        self.assertIn('aria_label="Close details"', panel)
        self.assertIn("selected_poster_requests", panel)
        self.assertIn("group_request_choice", panel)
        fullscreen = next(
            line for line in panel.splitlines() if "fixed inset-0" in line
        )
        for token in ("h-dvh", "w-full", "overflow-y-auto", "rounded-none"):
            self.assertIn(token, fullscreen)
        self.assertNotIn("max-w-", fullscreen)
        self.assertNotIn("rounded-bl", fullscreen)
        row = inspect.getsource(ui.job_row)
        self.assertNotIn("detail_body()", row)
        self.assertIn("aria_expanded=", row)
        self.assertNotIn("job_row_button", row)
        self.assertNotIn('post["description"]', row)
        for token in (
            'group["post"]["title"]',
            'group["post"]["poster_name"]',
            'group["post"]["poster_languages"]',
            'group["post"]["poster_image"]',
        ):
            self.assertIn(token, row)
        self.assertNotIn("detail_body()", inspect.getsource(ui.helper_row))
        self.assertIsInstance(ui.detail_panel(), rx.Component)

    def test_counts_and_photos(self):
        listing = inspect.getsource(ui.job_list)
        for text in (
            "No people need help nearby",
            " person who needs help",
            " people who need help",
            "DiscoveryState.visible_posts.length()",
            "w-full bg-transparent",
        ):
            self.assertIn(text, listing)
        body = inspect.getsource(ui.detail_body)
        self.assertLess(
            body.index('selected_post["description"]'),
            body.index("passport_photos()"),
        )
        self.assertLess(
            body.index("passport_photos()"), body.index("request_where_row()")
        )
        photos = inspect.getsource(ui.passport_photos)
        for token in (
            "length() > 0",
            "rx.fragment()",
            "rx.foreach",
            "overflow-x-auto",
            "touch-pan-x",
            "snap-x snap-mandatory",
            "[scrollbar-width:none]",
        ):
            self.assertIn(token, photos)
        slide = inspect.getsource(ui.passport_photo)
        for token in (
            "min-w-full",
            "aspect-square",
            "object-cover",
            "rx.get_upload_url",
            "alt=",
        ):
            self.assertIn(token, slide)
        self.assertIsInstance(ui.passport_photos(), rx.Component)

    def test_actions_and_alignment(self):
        helper = inspect.getsource(ui.helper_detail)
        for token in (
            "direct_help_section()",
            "report_button(",
            "block_member_button(",
            "ContactsState.send_request(",
            "original_language_disclosure(",
        ):
            self.assertIn(token, helper)
        self.assertNotIn("Given ", helper)
        self.assertNotIn("Got ", helper)
        self.assertLess(
            helper.index('selected_helper["handle"]'), helper.index("Joined ")
        )
        self.assertLess(helper.index("Joined "), helper.index("detail_rating("))
        self.assertNotIn("Gave ", helper)
        direct = inspect.getsource(ui.direct_help_section)
        self.assertIn("Your active requests – required", direct)
        self.assertIn('html_for="direct-help-request"', direct)
        self.assertIn("DiscoveryState.send_direct_help", direct)
        self.assertIn(
            "DiscoveryState.send_offer",
            inspect.getsource(ui.offer_help_section),
        )
        for card in (ticket_to_ride_choice, annual_pass_choice):
            self.assertIn("pl-[5.75rem] text-left", inspect.getsource(card))
        duration = inspect.getsource(duration_field)
        for token in (
            "justify-center-safe",
            "overflow-x-auto",
            "disabled=HelpHubState.duration_quote_allowed",
            '"Hours"',
            '"Minutes"',
        ):
            self.assertIn(token, duration)

    def test_dismiss_layer(self):
        layer = inspect.getsource(ui.filter_dismiss_layer)
        for token in (
            "pointerdown",
            "wheel",
            "touchmove",
            "on_scroll",
            "DiscoveryState.close_filters",
            "fixed inset-0 z-[25]",
        ):
            self.assertIn(token, layer)
        self.assertIn(
            "filter_dismiss_layer()", inspect.getsource(member_map_experience)
        )
        self.assertIsInstance(ui.filter_dismiss_layer(), rx.Component)


class StoryStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_collapse_does_not_count_a_view(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.view_mode = VIEW_LIST
        state.selected_post = {**EMPTY_POST, "id": 4}
        with patch(
            "reflex.asession",
            side_effect=AssertionError("No database on collapse"),
        ):
            async for _ in DiscoveryState.select_post.fn(state, 4):
                pass
        self.assertEqual(state.selected_post["id"], 0)

    async def test_new_row_and_map_reselection_count_views(self):
        for mode in (VIEW_MAP, VIEW_LIST):
            state = DiscoveryState(_reflex_internal_init=True)
            state.view_mode = mode
            state.posts = [{**EMPTY_POST, "id": 4, "poster_id": 8}]
            state.selected_post = {
                **EMPTY_POST,
                "id": 4 if mode == VIEW_MAP else 3,
            }
            session = AsyncMock()
            context = AsyncMock()
            context.__aenter__.return_value = session
            with (
                patch.object(
                    DiscoveryState,
                    "get_state",
                    AsyncMock(return_value=SimpleNamespace(subscriber_id="9")),
                ),
                patch("reflex.asession", return_value=context),
            ):
                async for _ in DiscoveryState.select_post.fn(state, 4):
                    pass
            self.assertEqual(state.selected_post["id"], 4)
            session.execute.assert_awaited_once()
            session.commit.assert_awaited_once()

    async def test_mode_switch_preserves_selection(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.view_mode = VIEW_LIST
        state.selected_post = {**EMPTY_POST, "id": 4}
        state.visible_post_ids = [4]
        state.viewport_ready = True
        DiscoveryState.set_view_mode.fn(state, VIEW_MAP)
        self.assertEqual(state.selected_post["id"], 4)
        self.assertEqual(state.visible_post_ids, [4])

    async def test_direct_filters_and_utilities_are_exclusive(self):
        discovery = DiscoveryState(_reflex_internal_init=True)
        notifications = SimpleNamespace(panel_open=True)
        profile = SimpleNamespace(settings_open=True)
        search = SimpleNamespace(expanded=True)
        with patch.object(
            DiscoveryState,
            "get_state",
            AsyncMock(side_effect=[notifications, profile, search]),
        ):
            await DiscoveryState.toggle_filter_panel.fn(discovery)
        self.assertTrue(discovery.filter_panel_open)
        self.assertFalse(
            notifications.panel_open or profile.settings_open or search.expanded
        )
        for handler in (
            NotificationState.open_panel,
            NotificationState.toggle_map_settings,
            NotificationState.toggle_map_filters,
        ):
            source = inspect.getsource(handler.fn)
            self.assertIn("WorldSearchState", source)
            self.assertIn("DiscoveryState", source)
            self.assertIn("ProfileState", source)
        DiscoveryState.close_filters.fn(discovery)
        self.assertFalse(discovery.filter_panel_open)


if __name__ == "__main__":
    unittest.main()
