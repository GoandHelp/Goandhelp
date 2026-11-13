import reflex as rx

import datetime
import inspect
import unittest
from types import SimpleNamespace

from app.models import EVENT_REQUEST_CATEGORIES
from app.states.event_state import (
    _decode_details,
    _encode_details,
    _two_year_ceiling,
)
from app.filter_categories import (
    FILTER_CATEGORIES,
    category_label,
    expand_category_tokens,
)
from app.models import TASK_CATEGORIES
from app.components import discover_panel, event_cards, member_map
from app.states.discovery_state import DiscoveryState


class EventDiscoveryTests(unittest.TestCase):
    def test_categories_round_trip(self):
        for category in EVENT_REQUEST_CATEGORIES:
            details = "Bring gloves.\nEveryone is welcome — thank you!"
            encoded = _encode_details(category, details)
            self.assertEqual(encoded, _encode_details(category, details))
            self.assertEqual(
                _decode_details(encoded, "teamwork"), (category, details)
            )

    def test_legacy_details(self):
        for category in ("gathering", "teamwork"):
            self.assertEqual(
                _decode_details("Original details", category),
                (category, "Original details"),
            )

    def test_leap_year_ceiling(self):
        now = datetime.datetime(2024, 2, 29, tzinfo=datetime.UTC)
        self.assertEqual(
            _two_year_ceiling(now),
            datetime.datetime(2026, 2, 28, tzinfo=datetime.UTC),
        )

    def test_filter_order_and_events_filter_vocabulary(self):
        values = [item["value"] for item in FILTER_CATEGORIES]
        labels = [item["label"].casefold() for item in FILTER_CATEGORIES]
        self.assertEqual(values[0], "events")
        self.assertEqual(FILTER_CATEGORIES[0]["label"], "Events")
        self.assertEqual(FILTER_CATEGORIES[0]["icon"], "calendar-days")
        self.assertEqual(
            values[1:-1],
            sorted(
                set(TASK_CATEGORIES) - {"other"},
                key=lambda value: next(
                    item["label"].casefold()
                    for item in FILTER_CATEGORIES
                    if item["value"] == value
                ),
            ),
        )
        self.assertEqual(FILTER_CATEGORIES[-1]["label"], "Other")
        self.assertEqual(category_label("events"), "Events")
        self.assertEqual(expand_category_tokens(["events"]), [])
        self.assertEqual(
            expand_category_tokens(["events", "arts"]), ["arts", "artist"]
        )
        self.assertEqual(set(values[1:]), set(TASK_CATEGORIES))

    def test_event_and_task_visibility_by_mode_and_selection(self):
        def visibility(
            mode: str, filters: list[str]
        ) -> tuple[bool, bool, bool]:
            state = SimpleNamespace(map_mode=mode, category_filters=filters)
            return (
                DiscoveryState.show_jobs.fget(state),
                DiscoveryState.show_helpers.fget(state),
                DiscoveryState.show_events.fget(state),
            )

        def events_only(filters: list[str]) -> bool:
            state = SimpleNamespace(category_filters=filters)
            return DiscoveryState.events_only.fget(state)

        self.assertEqual(visibility("give", []), (True, False, True))
        self.assertEqual(visibility("get", []), (False, True, False))
        self.assertEqual(visibility("give", ["events"]), (False, False, True))
        self.assertEqual(visibility("get", ["events"]), (False, False, True))
        self.assertEqual(visibility("give", ["arts"]), (True, False, False))
        self.assertEqual(visibility("get", ["arts"]), (False, True, False))
        self.assertEqual(
            visibility("give", ["events", "arts"]), (True, False, True)
        )
        self.assertEqual(
            visibility("get", ["events", "arts"]), (False, True, True)
        )
        self.assertTrue(events_only(["events"]))
        self.assertFalse(events_only([]))
        self.assertFalse(events_only(["arts"]))
        self.assertFalse(events_only(["events", "arts"]))
        self.assertFalse(events_only(["arts", "events"]))
        self.assertEqual(
            DiscoveryState.category_summary_label.fget(
                SimpleNamespace(category_filters=["events"])
            ),
            "Events",
        )

    def test_map_and_list_apply_event_visibility_and_empty_state(self):
        member_canvas = inspect.getsource(member_map.member_map_canvas)
        member_list = inspect.getsource(member_map.member_list_view)
        legacy_map = inspect.getsource(discover_panel.map_panel)
        legacy_list = inspect.getsource(discover_panel.discover_panel)
        self.assertIn("DiscoveryState.show_events", member_canvas)
        self.assertIn("DiscoveryState.show_jobs", member_canvas)
        self.assertIn("DiscoveryState.show_helpers", member_canvas)
        self.assertIn("EventState.map_markers", member_canvas)
        self.assertIn(
            "discovery_event_list(show_empty=DiscoveryState.events_only)",
            member_list,
        )
        self.assertIn("DiscoveryState.show_events", legacy_map)
        self.assertIn("EventState.map_markers", legacy_map)
        self.assertIn(
            "discovery_event_list(show_empty=DiscoveryState.events_only)",
            " ".join(legacy_list.split()),
        )
        self.assertIn(
            "No events match your filters",
            inspect.getsource(event_cards.discovery_event_list),
        )


if __name__ == "__main__":
    unittest.main()
