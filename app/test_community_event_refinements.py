import reflex as rx

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.components import (
    community_panel,
    event_cards,
    profile_tabs,
    reviews_section,
)
from app.states.auth_state import AuthState
from app.states.event_state import (
    EventState,
    EVENT_POINT_BAND,
    EVENT_POINT_SALT,
    _event_reward,
)
from app.states.help_hub_state import REWARD_CHOICES
from app.states.map_picker_state import MapPickerState
from app.test_event_planner import planner_state, form_data, session_mock


class CommunityPresentationTests(unittest.TestCase):
    def test_forum_required_limits_action_and_copy(self):
        source = inspect.getsource(community_panel.topic_composer)
        for removed in (
            "A subject, a title and a body are all needed",
            "CommunityState.subject_hint",
            "choose one pinned subject, or Other",
            "Pin discussion to the board",
        ):
            self.assertNotIn(removed, source)
        for retained in (
            "Post the discussion",
            "CommunityState.create_topic",
            "CommunityState.can_post_topic",
            "title_limit_label",
            "body_limit_label",
            '"required"',
        ):
            self.assertIn(retained, source)
        self.assertTrue(community_panel.topic_composer().render())

    def test_tabs_stay_in_bounded_community_scroll_and_below_planner(self):
        header = str(community_panel.community_header())
        for token in ("sticky", "top-0", "z-30", "bg-white", "pb-2"):
            self.assertIn(token, header)
        shell = inspect.getsource(profile_tabs.profile_tabs)
        self.assertIn('ProfileState.active_tab == "community"', shell)
        self.assertIn("flex-1 overflow-y-auto", shell)
        self.assertIn("flex-col min-h-0 w-full flex-1 overflow-hidden", shell)
        self.assertIn(
            "z-[60]", inspect.getsource(event_cards.event_planner_screen)
        )

    def test_combined_stars_precede_dynamic_heading(self):
        source = inspect.getsource(reviews_section.your_reviews_header)
        self.assertLess(
            source.index("combined_star_states"), source.index("rx.el.h3")
        )
        for token in (
            "combined_rating_label",
            'role="img"',
            "received_reviews.length()",
            "combined_rating_avg:.1f",
        ):
            self.assertIn(token, source)
        self.assertTrue(reviews_section.your_reviews_header().render())

    def test_reward_taxonomy_controls_and_map_render(self):
        state = EventState(_reflex_internal_init=True)
        self.assertEqual(state.reward_choices, REWARD_CHOICES)
        source = inspect.getsource(event_cards.event_reward_fields)
        for token in (
            "set_reward_choice",
            "set_reward_currency",
            "toggle_budget_quote",
            'name="money_budget"',
            'name="reward_details"',
            '== "other_reward"',
        ):
            self.assertIn(token, source)
        composer = inspect.getsource(event_cards.event_composer)
        self.assertIn(
            'map_picker("event-planner", "Location of this event", inline=True)',
            composer,
        )
        self.assertIn("exact pin stays private", composer)
        self.assertIn("reset_on_submit=False", composer)
        self.assertTrue(event_cards.event_composer().render())

    def test_reward_summaries_and_validation(self):
        self.assertEqual(_event_reward("", "", "", "USD", False), "")
        for item in REWARD_CHOICES:
            key = item["value"]
            details = "Museum tickets" if key == "other_reward" else ""
            summary = _event_reward(key, details, "25.50", "EUR", False)
            self.assertIn(item["label"], summary)
        self.assertEqual(
            _event_reward("money", "Per helper", "25.50", "eur", False),
            "Money (EUR 25.50 budget): Per helper",
        )
        self.assertIn(
            "Helper quote requested",
            _event_reward("money", "", "not a budget", "USD", True),
        )
        for budget in (
            "",
            "0",
            "-1",
            "NaN",
            "Infinity",
            "1e3",
            "12.345",
            "100000000",
            "1,00",
        ):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                _event_reward("money", "", budget, "USD", False)
        for args in (
            ("other_reward", "  ", "", "USD", False),
            ("invented", "", "", "USD", False),
            ("money", "", "25", "INVALID", False),
            ("meal", "a" * 1000, "", "USD", False),
        ):
            with self.assertRaises(ValueError):
                _event_reward(*args)


class EventPinTests(unittest.IsolatedAsyncioTestCase):
    async def test_pin_source_is_private_and_invalid_or_other_form_falls_back(
        self,
    ):
        for key, has_point, lat, lon, expected in (
            ("event-planner", True, 48.85, 2.35, (48.85, 2.35)),
            ("help-request", True, 48.85, 2.35, (41.2, -8.6)),
            ("event-planner", False, 48.85, 2.35, (41.2, -8.6)),
            ("event-planner", True, float("nan"), 2.35, (41.2, -8.6)),
            ("event-planner", True, 48.85, float("inf"), (41.2, -8.6)),
            ("event-planner", True, 91, 2.35, (41.2, -8.6)),
            ("event-planner", True, 48.85, -181, (41.2, -8.6)),
        ):
            with self.subTest(key=key, has_point=has_point, lat=lat, lon=lon):
                state, session = planner_state(), session_mock()
                picker = MapPickerState(_reflex_internal_init=True)
                picker.open_key, picker.has_point = key, has_point
                picker.latitude, picker.longitude = lat, lon
                state.get_state = AsyncMock(
                    side_effect=lambda cls: (
                        SimpleNamespace(subscriber_id="42", is_signed_in=True)
                        if cls is AuthState
                        else picker
                    )
                )
                data = {**form_data(), "latitude": "1", "longitude": "2"}
                with (
                    patch(
                        "app.states.event_state.rx.asession",
                        return_value=session,
                    ),
                    patch(
                        "app.states.event_state.approximate_point",
                        return_value=(40.1, -7.2),
                    ) as approximate,
                ):
                    updates = [
                        event
                        async for event in EventState.create_event.fn(
                            state, data
                        )
                    ]
                approximate.assert_called_once_with(
                    7, EVENT_POINT_SALT, *expected, EVENT_POINT_BAND
                )
                params = session.execute.call_args_list[2].args[1]
                self.assertEqual((params["lat"], params["lon"]), (40.1, -7.2))
                self.assertNotEqual((params["lat"], params["lon"]), expected)
                inserted = session.execute.call_args_list[0].args[1]
                self.assertNotIn("latitude", inserted)
                self.assertNotIn("longitude", inserted)
                if key == "event-planner":
                    self.assertFalse(picker.has_point)
                    self.assertEqual(picker.open_key, "")
                else:
                    self.assertTrue(picker.has_point)
                    self.assertEqual(picker.open_key, "help-request")
                self.assertEqual(
                    updates[-2:],
                    [EventState.load_events, EventState.load_my_events],
                )

    async def test_missing_profile_and_pin_saves_no_coordinates(self):
        state, session = planner_state(), session_mock()
        inserted, missing = MagicMock(), MagicMock()
        inserted.first.return_value = (7,)
        missing.first.return_value = None
        session.execute.side_effect = [inserted, missing]
        with (
            patch("app.states.event_state.rx.asession", return_value=session),
            patch("app.states.event_state.approximate_point") as approximate,
        ):
            _ = [
                event
                async for event in EventState.create_event.fn(
                    state, form_data()
                )
            ]
        approximate.assert_not_called()
        session.commit.assert_awaited_once()
        self.assertEqual(session.execute.await_count, 2)

    async def test_fresh_open_clears_pin_cancel_only_clears_event_key(self):
        state = EventState(_reflex_internal_init=True)
        picker = MapPickerState(_reflex_internal_init=True)
        picker.open_key, picker.has_point = "event-planner", True
        picker.latitude, picker.longitude = 48.85, 2.35
        auth = SimpleNamespace(subscriber_id="42", is_signed_in=True)
        with patch.object(
            EventState,
            "get_state",
            AsyncMock(
                side_effect=lambda cls: auth if cls is AuthState else picker
            ),
        ):
            await EventState.toggle_composer.fn(state)
            self.assertEqual(picker.open_key, "event-planner")
            self.assertFalse(picker.has_point)
            self.assertEqual(state.reward_choice, "")
            picker.has_point = True
            await EventState.close_composer.fn(state)
            self.assertFalse(picker.has_point)
            self.assertEqual(picker.open_key, "")
            picker.open_key, picker.has_point = "help-request", True
            await EventState.close_composer.fn(state)
            self.assertTrue(picker.has_point)
            self.assertEqual(picker.open_key, "help-request")

    async def test_failed_reward_validation_preserves_photos_pin_and_planner(
        self,
    ):
        state = planner_state()
        state.reward_choice = "other_reward"
        state.pending_photo_paths = [f"event_42_{'a' * 32}.webp"]
        picker = MapPickerState(_reflex_internal_init=True)
        picker.open_key, picker.has_point = "event-planner", True
        state.get_state = AsyncMock(
            side_effect=lambda cls: (
                SimpleNamespace(subscriber_id="42", is_signed_in=True)
                if cls is AuthState
                else picker
            )
        )
        with patch("app.states.event_state.rx.asession") as database:
            _ = [
                event
                async for event in EventState.create_event.fn(
                    state, {**form_data(), "reward_details": ""}
                )
            ]
        database.assert_not_called()
        self.assertIn("Other reward", state.error)
        self.assertTrue(state.composer_open)
        self.assertTrue(state.pending_photo_paths)
        self.assertTrue(picker.has_point)
        self.assertEqual(state.reward_choice, "other_reward")
        self.assertFalse(state.is_saving)


if __name__ == "__main__":
    unittest.main()
