import reflex as rx

import inspect
import unittest
from decimal import Decimal
from unittest.mock import patch

from app.components import discover_panel as ui
from app.components import member_map
from app.states.discovery_state import (
    DiscoveryState,
    EMPTY_POST,
    VIEW_LIST,
    VIEW_MAP,
)


class RequestPassportTests(unittest.TestCase):
    def test_public_reward_labels_and_masked_location(self):
        state = DiscoveryState(_reflex_internal_init=True)
        row = [None] * 37
        row[0], row[1], row[3], row[14] = 7, "Moving boxes", "labour", 12
        row[6], row[7], row[25], row[26] = (
            "Private street 2",
            "Porto",
            41.15,
            -8.61,
        )
        row[4], row[34], row[35], row[36] = (
            "money",
            "money",
            Decimal("500.00"),
            "USD",
        )
        with patch(
            "app.states.discovery_state.post_member_approximate",
            return_value=(41.16, -8.62),
        ):
            post = state._row_to_post(tuple(row), [])
            self.assertEqual(post["reward_label"], "Reward: 500USD")
            self.assertEqual(post["category_label"], "Labour")
            self.assertEqual(post["location"], "Porto")
            self.assertEqual(post["location_name"], "")
            self.assertEqual((post["lat"], post["lng"]), (41.16, -8.62))
            row[35], row[5] = 0, "Helper quote requested"
            self.assertEqual(
                state._row_to_post(tuple(row), [])["reward_label"],
                "Reward: Quote requested (USD)",
            )
            row[4], row[34], row[5] = "dinner", "dinner", "A warm meal"
            self.assertEqual(
                state._row_to_post(tuple(row), [])["reward_label"],
                "Reward: Dinner",
            )

    def test_map_action_uses_loaded_public_point_only(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.map_pulse_token = 0
        starting_token = state.map_pulse_token
        state.view_mode = VIEW_LIST
        post = {
            **EMPTY_POST,
            "id": 8,
            "poster_id": 12,
            "lat": 41.16,
            "lng": -8.62,
        }
        state.posts = [post]
        DiscoveryState.show_post_on_map.fn(state, 99)
        self.assertEqual(state.view_mode, VIEW_LIST)
        self.assertEqual(state.map_pulse_token, starting_token)
        DiscoveryState.show_post_on_map.fn(state, 8)
        self.assertEqual(state.view_mode, VIEW_MAP)
        self.assertEqual(state.map_center, [-8.62, 41.16])
        self.assertEqual(state.selected_post["id"], 0)
        self.assertEqual(state.map_pulse_token, starting_token + 1)
        self.assertEqual(
            state.job_map_markers[0]["pulse_token"], starting_token + 1
        )
        DiscoveryState.show_post_on_map.fn(state, 8)
        self.assertEqual(state.map_pulse_token, starting_token + 2)
        other = {
            **EMPTY_POST,
            "id": 9,
            "poster_id": 12,
            "lat": 41.2,
            "lng": -8.7,
        }
        state.posts = [other, post]
        self.assertEqual(state.job_map_markers[0]["id"], "g12")
        self.assertEqual(state.job_map_markers[0]["lng"], -8.62)
        self.assertEqual(
            state.job_map_markers[0]["pulse_token"], starting_token + 2
        )

    def test_quote_period_and_validation(self):
        post = {
            **EMPTY_POST,
            "allow_price_quote": True,
            "allow_duration_estimate": True,
        }
        self.assertEqual(
            DiscoveryState._offer_quote_lines(
                post, "12", "2", "30", "3", "weeks"
            ),
            "Price quote: 12 USD\nDuration estimate: 2 hours 30 minutes for 3 weeks",
        )
        for count, unit in [
            ("0", "days"),
            ("-1", "days"),
            ("1000", "weeks"),
            ("2", "years"),
        ]:
            with (
                self.subTest(count=count, unit=unit),
                self.assertRaisesRegex(ValueError, "Choose 1–999"),
            ):
                DiscoveryState._offer_quote_lines(
                    post, "12", "1", "0", count, unit
                )
        with self.assertRaisesRegex(ValueError, "Choose 0–10 hours"):
            DiscoveryState._offer_quote_lines(post, "12", "1", "60")
        with self.assertRaisesRegex(ValueError, "at least one minute"):
            DiscoveryState._offer_quote_lines(post, "12", "0", "0")

    def test_component_contracts(self):
        listing = inspect.getsource(ui.job_list)
        self.assertIn("in your selected area", listing)
        row = inspect.getsource(ui.job_row)
        self.assertIn('group["post"]["poster_verified"]', row)
        self.assertIn("detail_body()", row)
        self.assertIn("count_label", row)
        self.assertNotIn("job_row_button", row)
        request = inspect.getsource(ui.detail_body)
        self.assertIn('"Category"', request)
        self.assertIn('DiscoveryState.selected_post["category_label"]', request)
        self.assertLess(
            request.index('"Category"'), request.index("request_where_row()")
        )
        self.assertNotIn("urgency_pill(", request)
        self.assertNotIn("original_language_disclosure(", request)
        self.assertIn("request_where_row()", request)
        self.assertIn(
            "show_post_on_map", inspect.getsource(ui.request_where_row)
        )
        self.assertIn(
            'category_icon(post["category"]',
            inspect.getsource(member_map.group_post_button),
        )
        self.assertIn(
            "avatar_with_tick(",
            inspect.getsource(member_map.member_group_sheet),
        )
        self.assertIn(
            "prefers-reduced-motion: reduce",
            inspect.getsource(
                __import__(
                    "app.components.openfreemap", fromlist=["_MAP_COMPONENT"]
                )
            ),
        )
        self.assertIsInstance(ui.job_list(), rx.Component)
        self.assertIsInstance(member_map.member_group_sheet(), rx.Component)
        self.assertIsInstance(ui.offer_estimates(), rx.Component)


if __name__ == "__main__":
    unittest.main()
