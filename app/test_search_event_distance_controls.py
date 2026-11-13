import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import reflex as rx

from app.components import discover_panel, event_cards, location_selection
from app.states.discovery_state import DiscoveryState
from app.states.event_state import EventState
from app.states.profile_state import ProfileState
from app.states.world_search_state import WorldSearchState


class SearchDistanceComponentTests(unittest.TestCase):
    def test_global_search_is_first_and_city_filter_is_removed(self):
        source = inspect.getsource(discover_panel.filter_drawer)
        self.assertLess(
            source.index('name="world_search"'),
            source.index("category_multiselect()"),
        )
        self.assertLess(
            source.index("category_multiselect()"),
            source.index("DiscoveryState.reward_filter_options"),
        )
        self.assertNotIn("centered_search_label", source)
        self.assertNotIn('"Search Everything"', source)
        self.assertNotIn("set_city_filter", source)
        for token in (
            'placeholder="People, jobs, places..."',
            'name="world_search"',
            "WorldSearchState.submit",
            "WorldSearchState.expand",
            "WorldSearchState.show_panel",
            "results_panel()",
            '"data-tour-target": "search"',
            '"data-tour-target-compact": "search-compact"',
            "text-[#6b7280]",
            "justify-center gap-2",
            'aria_label="Search people, jobs and places"',
            'aria_label="Filter by reward"',
        ):
            self.assertIn(token, source)
        self.assertIn(
            'aria_label="Choose one or more help categories"',
            inspect.getsource(discover_panel.category_multiselect),
        )
        self.assertEqual(source.count("sheet_view_toggle()"), 1)
        self.assertNotIn('type="submit"', source)
        self.assertNotIn("gah-search-submit gah-inverse-text", source)
        self.assertTrue(
            location_selection.location_selection(compact=True).render()
        )
        self.assertIsInstance(
            discover_panel.filter_drawer("w-full"), rx.Component
        )
        self.assertIn(
            'if kind == "place"', inspect.getsource(WorldSearchState.choose.fn)
        )

    def test_distance_label_live_and_slider_still_commits(self):
        row, slider = discover_panel.distance_filter_block().children
        label = str(row.children[1])
        source = inspect.getsource(discover_panel.distance_filter_block)
        self.assertIn("1 km", str(row.children[0]))
        self.assertIn("Any", str(row.children[2]))
        self.assertIn("Distance", label)
        self.assertIn("distance_label", label)
        self.assertIn("text-center", label)
        self.assertIn("whitespace-nowrap", source)
        self.assertIn("min-w-0 flex-1", source)
        self.assertNotIn("Distance –", source)
        self.assertIn('aria_live="polite"', source)
        self.assertIn("set_distance_filter.throttle(100)", source)
        self.assertIn("commit_distance_filter.debounce(150)", source)
        self.assertIn("aria_valuetext=DiscoveryState.distance_label", source)
        self.assertTrue(slider.render())

    def test_money_reward_works_for_legacy_and_multi_reward_posts(self):
        state = DiscoveryState(_reflex_internal_init=True)
        self.assertIn(
            {"value": "money", "label": "Money"}, state.reward_filter_options
        )
        self.assertEqual(
            DiscoveryState.set_reward_filter.fn(state, "money"),
            DiscoveryState.refresh_board,
        )
        self.assertEqual(state.reward_filter, "money")
        self.assertIn("Reward: Money", state.active_filter_summary)
        source = inspect.getsource(DiscoveryState._load_jobs)
        self.assertIn(
            'if reward == "money" or reward in REWARD_LABELS:', source
        )
        self.assertIn("p.reward_type = :reward", source)
        self.assertIn("COALESCE(p.reward_types, '')", source)
        self.assertIn("LIKE :reward_token", source)
        self.assertIn('params["reward_token"] = f"%,{reward},%"', source)
        self.assertIn("owned_where", source)

    def test_location_status_and_toast_placement(self):
        expected = (
            "Your Approximate location is shown between 500m and 1km away."
        )
        mode = inspect.getsource(ProfileState.set_location_mode.fn)
        fix = inspect.getsource(ProfileState.save_live_position.fn)
        for source in (mode, fix):
            self.assertIn(expected, source)
            self.assertNotIn("yield rx.toast", source)
            self.assertNotIn("accuracy about", source)
        self.assertNotIn(
            'rx.toast("Location details saved.',
            inspect.getsource(ProfileState.save_area.fn),
        )
        app_source = Path("app/app.py").read_text()
        self.assertIn("app = rx.App(", app_source)
        self.assertIn('rx.toast.provider(position="top-center")', app_source)
        self.assertNotIn("overlay_component=", app_source)

    def test_shared_location_controls_and_single_outer_shadow(self):
        control = location_selection.location_selection()
        self.assertIn("Show my location", str(control))
        self.assertIn("gah-segment-group", str(control))
        self.assertIn("gah-segment-control", location_selection.LOCATION_TAP_ON)
        self.assertIn(
            "gah-segment-control", location_selection.LOCATION_TAP_OFF
        )
        self.assertNotIn("shadow-", location_selection.LOCATION_TAP_ON)
        self.assertNotIn("shadow-", location_selection.LOCATION_TAP_OFF)
        compact_source = inspect.getsource(
            discover_panel.show_my_location_block
        )
        self.assertIn("location_selection(compact=True)", compact_source)
        self.assertIn("location_selection()", compact_source)
        standard = location_selection.location_selection()
        compact = location_selection.location_selection(compact=True)
        self.assertIn("flex flex-col", str(standard.children[1].class_name))
        self.assertIn(
            "items-center justify-start", str(compact.children[1].class_name)
        )
        self.assertTrue(control.render())

    def test_events_use_private_location_control(self):
        source = inspect.getsource(event_cards.event_distance_control)
        control = inspect.getsource(event_cards.events_location_control)
        self.assertIn('"Event distance"', source)
        self.assertIn("events_location_control()", source)
        self.assertNotIn("location_selection()", source)
        self.assertIn('"Enable my location"', control)
        self.assertIn('role="switch"', control)
        self.assertIn("EventState.events_position_found", control)
        self.assertIn("EventState.events_position_failed", control)
        self.assertIn("set_event_distance_km.throttle(100)", source)
        self.assertTrue(event_cards.event_distance_control().render())


class EventDistanceStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_hidden_attempt_prompts_without_blocking_distance_refresh(
        self,
    ):
        state = EventState(_reflex_internal_init=True)
        with patch.object(
            EventState,
            "get_state",
            AsyncMock(
                return_value=SimpleNamespace(
                    location_mode="hidden", show_location=False
                )
            ),
        ) as getter:
            followup = await EventState.set_event_distance_km.fn(state, 250)
        getter.assert_awaited_once_with(ProfileState)
        self.assertTrue(state.distance_location_prompt)
        self.assertEqual(state.event_distance_km, 250)
        self.assertEqual(state.event_distance_label, "250 km")
        self.assertEqual(followup, EventState.load_events)

    async def test_approximate_attempt_dismisses_prompt_and_keeps_clamps(self):
        state = EventState(_reflex_internal_init=True)
        state.distance_location_prompt = True
        with patch.object(
            EventState,
            "get_state",
            AsyncMock(
                return_value=SimpleNamespace(
                    location_mode="approximate", show_location=True
                )
            ),
        ):
            followup = await EventState.set_event_distance_km.fn(state, 2000)
        self.assertFalse(state.distance_location_prompt)
        self.assertEqual(state.event_distance_km, 1000)
        self.assertEqual(followup, EventState.load_events)


if __name__ == "__main__":
    unittest.main()
