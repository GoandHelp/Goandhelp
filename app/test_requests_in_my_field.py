import reflex as rx

import inspect
import json
import math
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from app.field_requests import (
    FIELD_RADIUS,
    FIELD_SWITCH,
    HELPER_MATCH_SQL,
    DISTANCE_SQL,
    field_preferences,
    validate_field_radius,
    persist_preference,
    notify_field_helpers,
    owned_field_matches,
)
from app.states.discovery_state import DiscoveryState, EMPTY_POST
from app.states.notification_state import (
    NotificationState,
    NOTIFICATION_FILTER,
    notification_preferences,
)
from app.skill_categories import (
    categories_overlap,
    post_categories,
    split_categories,
)
from app.location_privacy import _distance_km


class FieldRequestTests(unittest.IsolatedAsyncioTestCase):
    def test_defaults_bounds_and_independence(self):
        for raw in (None, "{}", {}, "[]"):
            self.assertEqual(field_preferences(raw), (True, 20))
        self.assertEqual(
            field_preferences({FIELD_SWITCH: False, FIELD_RADIUS: 1000}),
            (False, 1000),
        )
        for value in (
            0,
            1001,
            -1,
            1.5,
            True,
            math.nan,
            math.inf,
            "bad",
            {},
            None,
        ):
            with self.assertRaises(ValueError):
                validate_field_radius(value)
        for value in (1, 20, 1000, "20", 20.0):
            self.assertEqual(validate_field_radius(value), int(value))
        preferences = notification_preferences({"notify_help_offers": False})
        self.assertTrue(preferences[FIELD_SWITCH])
        self.assertFalse(preferences["notify_help_offers"])
        self.assertIn(
            "WHEN kind = 'requests_in_my_field' THEN :notify_requests_in_my_field",
            NOTIFICATION_FILTER,
        )

    async def test_locked_merge_preserves_unrelated_json(self):
        session = SimpleNamespace(execute=AsyncMock())
        original = {
            "notify_messages": False,
            "permission_location": "hidden",
            "nested": {"keep": 1},
        }
        session.execute.side_effect = [
            None,
            SimpleNamespace(scalar_one=lambda: json.dumps(original)),
            None,
        ]
        merged = await persist_preference(session, 7, FIELD_RADIUS, 999)
        self.assertEqual(merged, {**original, FIELD_RADIUS: 999})
        self.assertIn(
            "FOR UPDATE", str(session.execute.await_args_list[1].args[0])
        )
        self.assertEqual(field_preferences(json.dumps(merged)), (True, 999))
        session.execute.side_effect = [
            None,
            SimpleNamespace(scalar_one=lambda: merged),
            None,
        ]
        toggled = await persist_preference(session, 7, FIELD_SWITCH, True)
        self.assertFalse(toggled[FIELD_SWITCH])
        self.assertEqual(toggled["nested"], original["nested"])

    def test_category_distance_and_private_eligibility(self):
        self.assertTrue(
            categories_overlap(
                split_categories("nanny,Music"),
                post_categories("carer,mechanic", "labour"),
            )
        )
        self.assertTrue(
            categories_overlap(
                split_categories("translation"),
                post_categories("", "translator"),
            )
        )
        self.assertFalse(categories_overlap(["music"], ["mechanic"]))
        self.assertLess(_distance_km(0, 179.99, 0, -179.99), 3)
        self.assertGreater(_distance_km(0, 0, 1, 0), 100)
        for clause in (
            "helper.is_verified=TRUE",
            "helper.is_active=TRUE",
            "helper.help_mode IN ('offer_help', 'both')",
            "helper.id<>p.author_id",
            "b.blocker_id=helper.id",
            "b.blocked_id=helper.id",
            "p.latitude BETWEEN -90 AND 90",
            "hp.latitude BETWEEN -90 AND 90",
            "p.category_tags",
            "hp.preferred_categories",
            "skillkind_completed_task",
        ):
            self.assertIn(clause, HELPER_MATCH_SQL)
        self.assertNotIn("show_location", HELPER_MATCH_SQL)
        self.assertNotIn("location_mode", HELPER_MATCH_SQL)
        self.assertIn("LEAST(1.0, GREATEST(-1.0", DISTANCE_SQL)

    async def test_delivery_radius_optout_and_dedupe(self):
        session = SimpleNamespace(execute=AsyncMock())
        candidates = [
            (2, "{}", 10),
            (3, json.dumps({FIELD_SWITCH: False}), 1),
            (4, "{}", 25),
            (5, json.dumps({FIELD_RADIUS: 1000}), 25),
        ]
        session.execute.side_effect = [
            None,
            SimpleNamespace(all=lambda: candidates),
            None,
            SimpleNamespace(all=lambda: []),
        ]
        await notify_field_helpers(session, 17)
        calls = session.execute.await_args_list
        self.assertIn("FOR UPDATE", str(calls[0].args[0]))
        self.assertIn("NOT EXISTS", str(calls[1].args[0]))
        self.assertEqual([p["recipient"] for p in calls[2].args[1]], [2, 5])
        self.assertNotIn("latitude", str(calls[2].args[0]))
        self.assertEqual(calls[3].args[1]["cursor"], 5)

    async def test_group_fetch_owned_unread_only(self):
        session = SimpleNamespace(execute=AsyncMock())
        session.execute.side_effect = [
            SimpleNamespace(scalar_one_or_none=lambda: "{}"),
            SimpleNamespace(all=lambda: [(17,), (18,)]),
            SimpleNamespace(all=lambda: [(101, 17), (102, 18)]),
        ]
        self.assertEqual(
            await owned_field_matches(session, 7), [(101, 17), (102, 18)]
        )
        call = session.execute.await_args_list[-1]
        self.assertEqual(call.args[1]["sid"], 7)
        self.assertEqual(call.args[1]["posts"], [17, 18])
        self.assertIn("recipient_id=:sid", str(call.args[0]))
        self.assertIn("is_read=FALSE", str(call.args[0]))
        self.assertIn("FOR UPDATE", str(call.args[0]))

    def test_map_group_pulses_and_outside_viewport_list(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.posts = [
            {**EMPTY_POST, "id": 1, "poster_id": 10, "lat": 40, "lng": 5},
            {**EMPTY_POST, "id": 2, "poster_id": 10, "lat": 41, "lng": 6},
            {**EMPTY_POST, "id": 3, "poster_id": 11, "lat": 42, "lng": 7},
            {**EMPTY_POST, "id": 4, "poster_id": 12, "has_map_point": False},
        ]
        state.map_pulse_post_ids = [2, 3, 4]
        state.map_pulse_token = 5
        markers = DiscoveryState.job_map_markers.fget(state)
        self.assertEqual({m["id"] for m in markers}, {"g10", "p3"})
        self.assertTrue(all(m["pulse_token"] == 5 for m in markers))
        state._field_priority_post_ids = [3, 4]
        state.view_mode = "list"
        state.visible_post_ids = [1]
        state.viewport_ready = True
        self.assertEqual(
            [p["id"] for p in DiscoveryState.visible_posts.fget(state)],
            [3, 4, 1],
        )
        source = inspect.getsource(NotificationState.open_field_group.fn)
        self.assertIn("owned_field_matches(session, int(sid))", source)
        self.assertIn("id=ANY(:notices)", source)
        self.assertIn("VIEW_MAP if visible else VIEW_LIST", source)
        self.assertIn("yield DiscoveryState.load_jobs", source)
        from app.components.profile_tabs import notification_settings
        from app.components.map_utilities import notification_feed

        self.assertIsInstance(notification_settings(), rx.Component)
        self.assertIsInstance(notification_feed(), rx.Component)


if __name__ == "__main__":
    unittest.main()
