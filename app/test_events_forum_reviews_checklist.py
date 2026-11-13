import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components import (
    community_panel,
    event_calendar,
    event_cards,
    reviews_section,
)
from app.states.event_state import EventState
from app.states.profile_state import ProfileState


class EventDistanceChecklistTests(unittest.IsolatedAsyncioTestCase):
    async def test_slider_preserves_one_km_steps_and_clamps_to_endpoint(self):
        state = EventState(_reflex_internal_init=True)
        initial_slider_reset = state.distance_slider_reset
        with patch.object(
            EventState,
            "get_state",
            AsyncMock(
                return_value=SimpleNamespace(
                    location_mode="approximate", show_location=True
                )
            ),
        ):
            for distance, expected, label in (
                (1, 1, "1 km"),
                (2, 2, "2 km"),
                (250, 250, "250 km"),
                (1000, 1000, "1000 km+"),
                (3000, 1000, "1000 km+"),
                (-5, 1, "1 km"),
            ):
                with self.subTest(distance=distance):
                    self.assertEqual(
                        await EventState.set_event_distance_km.fn(
                            state, distance
                        ),
                        EventState.load_events,
                    )
                    self.assertEqual(state.event_distance_km, expected)
                    self.assertEqual(state.event_distance_label, label)
                    self.assertFalse(state.distance_location_prompt)
            self.assertEqual(state.distance_slider_reset, initial_slider_reset)

    async def test_endpoint_button_resets_thumb_and_refreshes_results(self):
        state = EventState(_reflex_internal_init=True)
        initial_slider_reset = state.distance_slider_reset
        state.event_distance_km = 12
        with patch.object(
            EventState,
            "get_state",
            AsyncMock(
                return_value=SimpleNamespace(
                    location_mode="hidden", show_location=False
                )
            ),
        ) as getter:
            self.assertEqual(
                await EventState.select_max_event_distance.fn(state),
                EventState.load_events,
            )
        getter.assert_awaited_once_with(ProfileState)
        self.assertEqual(state.event_distance_km, 1000)
        self.assertEqual(state.event_distance_label, "1000 km+")
        self.assertTrue(state.distance_location_prompt)
        self.assertEqual(state.distance_slider_reset, initial_slider_reset + 1)

    def test_slider_endpoint_and_status_accessibility(self):
        control = event_cards.event_distance_control()
        slider = control.children[1]
        endpoint = control.children[2].children[1]
        slider_source = inspect.getsource(event_cards.event_distance_control)
        for token in (
            'min="1"',
            'max="1000"',
            'step="1"',
            "default_value=EventState.event_distance_km.to_string()",
            "key=EventState.distance_slider_reset.to_string()",
            "aria_valuetext=EventState.event_distance_label",
            "set_event_distance_km.throttle(100)",
        ):
            self.assertIn(token, slider_source)
        self.assertNotIn(
            "value=EventState.event_distance_km.to_string()",
            slider_source.replace("default_value=", "default="),
        )
        self.assertIn('role="status"', slider_source)
        self.assertIn('"1000 km+"', str(endpoint))
        self.assertIn("select_max_event_distance", str(endpoint))
        self.assertIn("aria_pressed", slider_source)
        self.assertIn("min-h-10", str(endpoint.class_name))
        self.assertTrue(slider.render())
        self.assertTrue(endpoint.render())


class CommunityVisualChecklistTests(unittest.TestCase):
    def test_date_and_distance_cards_use_neutral_edges_and_soft_shadow(self):
        date = event_calendar.event_date_calendar()
        distance = event_cards.event_distance_control()
        for card in (date.children[0], distance):
            classes = str(card.class_name)
            self.assertIn("bg-white", classes)
            self.assertIn("border-[#e5e7eb]", classes)
            self.assertIn("shadow-sm", classes)
            self.assertNotIn("border-[#fba922]", classes)
            self.assertNotIn("border-[#f6c66f]", classes)
        self.assertTrue(date.render())
        self.assertTrue(distance.render())

    def test_forum_notice_matches_events_text_size_on_mobile_and_desktop(self):
        forum = inspect.getsource(community_panel.community_section)
        events = inspect.getsource(event_cards.planner_block)
        self.assertIn("1 topic per month · 10 comments per month", forum)
        self.assertIn('"Plan and join events for free"', events)
        notice_classes = (
            "min-w-0 text-center text-sm font-medium text-[#404040]"
        )
        self.assertIn(notice_classes, forum)
        self.assertIn(notice_classes, events)
        self.assertNotIn("text-xs sm:text-sm", forum)

    def test_pending_reviews_empty_matches_received_card(self):
        pending = inspect.getsource(reviews_section.community_reviews_section)
        received = inspect.getsource(reviews_section.received_reviews_section)
        self.assertIn('"No reviews waiting to be written."', pending)
        self.assertIn('"Your first review is still waiting"', received)
        for token in ("gah-edge-stack", "bg-white", "px-6 py-8", "text-center"):
            self.assertIn(token, pending)
            self.assertIn(token, received)
        self.assertIn("rounded-2xl", pending)
        self.assertIn("shadow-sm", pending)
        self.assertTrue(reviews_section.community_reviews_section().render())


if __name__ == "__main__":
    unittest.main()
