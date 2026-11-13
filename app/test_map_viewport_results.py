import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import reflex as rx

from app.components import discover_panel as ui
from app.components import find_people_panel
from app.components import member_map, openfreemap
from app.states.auth_state import AuthState
from app.states.discovery_state import DiscoveryState, EMPTY_HELPER, EMPTY_POST
from app.states.onboarding_state import OnboardingState
from app.states.profile_state import ProfileState
from test_utils import run_event


class MapViewportResultsTests(unittest.TestCase):
    def test_projection_lifecycle_and_optional_callback(self):
        script = openfreemap._MAP_COMPONENT
        for token in (
            "map.project([point.lng, point.lat])",
            "canvas.clientWidth",
            "canvas.clientHeight",
            'map.on("load", handleViewportLoad)',
            'map.on("moveend", handleViewportChange)',
            'map.on("resize", handleViewportChange)',
            'map.off("moveend", handleViewportChange)',
            'map.off("resize", handleViewportChange)',
            "[viewportPoints]",
            ".sort()",
            "visibleSignatureRef.current",
            "!viewportReadyRef.current",
        ):
            self.assertIn(token, script)
        self.assertIn(
            "viewport_points=DiscoveryState.viewport_points",
            inspect.getsource(member_map.member_map_canvas),
        )
        self.assertIn(
            "on_visible_points_change=DiscoveryState.update_visible_points",
            inspect.getsource(member_map.member_map_canvas),
        )
        self.assertIn(
            "viewport_points=DiscoveryState.viewport_points",
            inspect.getsource(ui.map_panel),
        )
        self.assertIsInstance(ui.job_list(), rx.Component)
        self.assertIsInstance(ui.helper_list(), rx.Component)

    def test_individual_post_and_helper_visibility(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.posts = [
            {**EMPTY_POST, "id": 11, "poster_id": 3, "lat": 51.2, "lng": -0.3},
            {**EMPTY_POST, "id": 12, "poster_id": 3, "lat": 52.1, "lng": -0.7},
        ]
        state.helpers = [{**EMPTY_HELPER, "id": 7, "lat": 48.2, "lng": 1.8}]
        self.assertEqual(state.visible_posts, [])
        self.assertEqual(state.visible_helpers, [])
        self.assertEqual(
            {point["id"] for point in state.viewport_points},
            {"p11", "p12", "h7"},
        )
        state.visible_post_ids = [12]
        state.visible_helper_ids = [7]
        state.viewport_ready = True
        self.assertEqual([post["id"] for post in state.visible_posts], [12])
        self.assertEqual(
            [helper["id"] for helper in state.visible_helpers], [7]
        )
        state.posts = [{**EMPTY_POST, "id": 11, "poster_id": 3}]
        self.assertEqual(state.visible_posts, [])

    def test_list_and_privacy_contract(self):
        for component in (ui.job_list, ui.helper_list):
            source = inspect.getsource(component)
            self.assertIn("DiscoveryState.visible_", source)
            self.assertNotIn("DiscoveryState.open_total", source)
            self.assertNotIn("DiscoveryState.helper_total", source)
        handler = inspect.getsource(DiscoveryState.update_visible_points.fn)
        for token in (
            "auth.is_signed_in",
            "onboarding.needs_onboarding",
            "profile.on_map",
            "re.fullmatch",
            "post_ids",
            "helper_ids",
        ):
            self.assertIn(token, handler)
        state_source = inspect.getsource(DiscoveryState._load_helpers)
        for token in (
            "s.is_active = TRUE",
            "VISIBLE_LOCATION_SQL",
            "pr.show_location",
            "profile_approximate(",
            "not_blocked_author_sql",
            "DISCOVERY_RESULT_CAP",
        ):
            self.assertIn(token, state_source)
        self.assertNotIn("s.help_mode IN ('offer_help', 'both')", state_source)
        self.assertNotIn("mode_label", inspect.getsource(ui.helper_row))
        self.assertNotIn(
            "mode_label", inspect.getsource(find_people_panel.person_card)
        )
        self.assertNotIn("Given ", inspect.getsource(ui.helper_detail))
        self.assertIn("detail_rating(", inspect.getsource(ui.helper_detail))
        self.assertIn(
            "justify-center", inspect.getsource(ui.offer_help_section)
        )
        self.assertIn(
            "DiscoveryState.is_list_view", inspect.getsource(ui.detail_body)
        )


class ViewportCallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_authorized_ids_and_list_transition(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.posts = [
            {**EMPTY_POST, "id": 11, "poster_id": 5},
            {**EMPTY_POST, "id": 12, "poster_id": 5},
        ]
        state.helpers = [{**EMPTY_HELPER, "id": 7}]
        auth = SimpleNamespace(is_signed_in=True)
        onboarding = SimpleNamespace(needs_onboarding=False)
        profile = SimpleNamespace(on_map=True)
        with patch.object(
            DiscoveryState,
            "get_state",
            AsyncMock(side_effect=[auth, onboarding, profile]),
        ):
            await DiscoveryState.update_visible_points.fn(
                state,
                ["p12", "h7", "p999", "g5", "e2", "h-1", "p0", "p1oops", "p12"],
            )
        self.assertEqual(state.visible_post_ids, [12])
        self.assertEqual(state.visible_helper_ids, [7])
        self.assertTrue(state.viewport_ready)
        DiscoveryState.set_view_mode.fn(state, "list")
        self.assertEqual(state.visible_post_ids, [12])
        self.assertEqual([post["id"] for post in state.visible_posts], [12])
        state.posts = [state.posts[0]]
        self.assertEqual(state.visible_posts, [])

    async def test_guest_and_onboarding_cannot_update_viewport(self):
        for scenario in ("guest", "onboarding"):
            with self.subTest(scenario=scenario):
                state = DiscoveryState(_reflex_internal_init=True)
                state.viewport_ready = False
                state.visible_post_ids = []
                state.visible_helper_ids = []
                state.posts = [{**EMPTY_POST, "id": 11}]
                auth = await state.get_state(AuthState)
                onboarding = await state.get_state(OnboardingState)
                profile = await state.get_state(ProfileState)
                auth.subscriber_id = "15" if scenario == "onboarding" else ""
                auth.email = (
                    "member@example.invalid" if scenario == "onboarding" else ""
                )
                onboarding.has_row = scenario == "onboarding"
                onboarding.progress_loaded = True
                onboarding.is_complete = False
                profile.active_tab = "discover"
                if scenario == "onboarding":
                    self.assertTrue(auth.is_signed_in)
                    self.assertTrue(onboarding.needs_onboarding)
                else:
                    self.assertFalse(auth.is_signed_in)
                self.assertTrue(profile.on_map)
                await run_event(state.update_visible_points, ["p11"])
                self.assertFalse(state.viewport_ready)
                self.assertEqual(state.visible_post_ids, [])
                self.assertEqual(state.visible_helper_ids, [])


if __name__ == "__main__":
    unittest.main()
