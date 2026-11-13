import reflex as rx

import inspect
import unittest
from decimal import Decimal

from app.components import discover_panel as ui
from app.components.openfreemap import _MAP_COMPONENT
from app.reward_display import reward_display
from app.states.discovery_state import DiscoveryState, EMPTY_POST


class RequestMapPresentationTests(unittest.TestCase):
    def test_grouped_list_shows_one_header_and_one_detail(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.posts = [
            {
                **EMPTY_POST,
                "id": 1,
                "poster_id": 12,
                "poster_name": "Neighbour",
            },
            {
                **EMPTY_POST,
                "id": 2,
                "poster_id": 12,
                "poster_name": "Neighbour",
            },
        ]
        state.visible_post_ids = [1, 2]
        state.viewport_ready = True
        groups = DiscoveryState.list_post_groups.fget(state)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["ids"], [1, 2])
        self.assertEqual(groups[0]["count_label"], "2 open requests")
        row = inspect.getsource(ui.job_row)
        self.assertEqual(row.count("detail_body()"), 1)
        self.assertNotIn("job_row_button", row)
        self.assertIn("aria_expanded=", row)
        self.assertIn("list_post_groups", inspect.getsource(ui.job_list))
        self.assertIsInstance(ui.job_list(), rx.Component)

    def test_currency_and_quote_display(self):
        self.assertEqual(
            reward_display("money", "money", Decimal("50.00"), "USD", ""),
            "Reward: 50USD",
        )
        self.assertEqual(
            reward_display("money", "money", Decimal("500.00"), "EUR", ""),
            "Reward: 500EUR",
        )
        self.assertEqual(
            reward_display(
                "money", "money", 0, "EUR", "Helper quote requested"
            ),
            "Reward: Quote requested (EUR)",
        )
        self.assertEqual(
            reward_display("other", "other", 0, "USD", "A home-cooked meal"),
            "Reward: A home-cooked meal",
        )

    def test_safe_map_target_and_five_pulses(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.posts = [
            {**EMPTY_POST, "id": 8, "poster_id": 3, "lat": 52.12, "lng": 4.22},
            {**EMPTY_POST, "id": 9, "poster_id": 3, "lat": 52.13, "lng": 4.23},
        ]
        state.selected_post = state.posts[0]
        DiscoveryState.show_post_on_map.fn(state, 9)
        self.assertEqual(state.selected_post["id"], 0)
        self.assertEqual(state.map_center, [4.23, 52.13])
        self.assertEqual(state.view_mode, "map")
        markers = DiscoveryState.job_map_markers.fget(state)
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["id"], "g3")
        self.assertEqual(markers[0]["pulse_token"], state.map_pulse_token)
        self.assertEqual((markers[0]["lng"], markers[0]["lat"]), (4.23, 52.13))
        self.assertIn("iterations: 5", _MAP_COMPONENT)
        self.assertIn("prefers-reduced-motion: reduce", _MAP_COMPONENT)
        self.assertIn("style.zIndex = '1000'", _MAP_COMPONENT)

    def test_own_actions_and_estimate_controls(self):
        self.assertIn(
            "AuthState.subscriber_id", inspect.getsource(ui.accept_section)
        )
        self.assertIn(
            "AuthState.subscriber_id",
            inspect.getsource(ui.request_footer_actions),
        )
        controls = inspect.getsource(ui.offer_estimates)
        self.assertIn('step="1"', controls)
        self.assertIn("rx.Var.range(0, 11)", controls)
        self.assertIn("rx.Var.range(0, 12)", controls)
        self.assertIn("appearance-none", controls)
        self.assertIn("shadow-[0_2px_10px", controls)
        self.assertIn('"For"', controls)
        self.assertIn("items-center", inspect.getsource(ui.request_where_row))
        self.assertIsInstance(ui.offer_estimates(), rx.Component)


if __name__ == "__main__":
    unittest.main()
