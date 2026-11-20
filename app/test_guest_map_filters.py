import reflex as rx

import ast
import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace

from test_utils import run_event
from app.components import guest_map, guest_filters, filter_layout
from app.components.openfreemap import _MAP_COMPONENT
from app.filter_categories import expand_category_tokens
from app.models import HELP_MODE_OFFER, HELP_MODE_BOTH, TASK_CATEGORIES
from app.states.guest_map_state import (
    GuestMapState,
    GuestJob,
    GuestHelper,
    GUEST_CATEGORIES,
    GUEST_REWARDS,
    PAGE_SIZE,
    MAX_QUERY_LENGTH,
    _reference_code,
    _helper_reference_code,
    _public_job,
    _public_helper,
    guest_preview_query,
    fetch_guest_preview,
)


class GuestMapFilterTests(unittest.IsolatedAsyncioTestCase):
    async def test_filters_open_close_without_joining_and_list_is_impossible(
        self,
    ):
        state = GuestMapState()
        await run_event(state.expand_search)
        self.assertTrue(state.search_expanded)
        self.assertFalse(state.wall_open)
        for mode in ("list", "map", "arbitrary"):
            await run_event(state.set_view_mode, mode)
            self.assertEqual(state.view_mode, "map")
            self.assertFalse(GuestMapState.is_list_view.fget(state))
        state.view_mode = "list"
        self.assertFalse(GuestMapState.is_list_view.fget(state))
        await run_event(state.collapse_search)
        self.assertFalse(state.search_expanded)
        self.assertFalse(state.wall_open)
        button = inspect.getsource(guest_map.guest_filters_button)
        self.assertIn("on_click=GuestMapState.expand_search", button)
        self.assertNotIn("open_join_prompt", button)
        canvas = inspect.getsource(guest_map.guest_map_canvas)
        self.assertNotIn("guest_list_view", canvas)
        self.assertNotIn("is_list_view", canvas)
        self.assertIn("guest_filter_drawer()", canvas)
        self.assertIn(
            "on_interaction_start=GuestMapState.collapse_search", canvas
        )

    async def test_real_filter_callbacks_reload_without_modifying_account_drafts(
        self,
    ):
        state = GuestMapState()
        state.browse_mode = "give"
        state.reward_filter = "all"
        state.category_filters = []
        state.wall_open = False
        from app.states.auth_state import AuthState

        auth = await state.get_state(AuthState)
        auth.email = "unsent@example.test"
        await run_event(state.toggle_category_list)
        self.assertTrue(state.category_list_open)
        generation = state._preview_generation
        event = await run_event(state.toggle_category_choice, "construction")
        self.assertEqual(state.category_filters, ["construction"])
        self.assertIsNotNone(event)
        self.assertGreater(state._preview_generation, generation)
        await run_event(state.toggle_category_choice, "events")
        self.assertEqual(state.category_filters, ["construction"])
        await run_event(state.set_reward_filter, "money")
        self.assertEqual(state.reward_filter, "money")
        await run_event(state.submit_search, {"guest_search": "x" * 500})
        self.assertEqual(len(state.search_query), MAX_QUERY_LENGTH)
        await run_event(state.set_browse_mode, "get")
        self.assertEqual(state.browse_mode, "get")
        await run_event(state.set_reward_filter, "lunch")
        self.assertEqual(state.reward_filter, "money")
        await run_event(state.set_browse_mode, "give")
        self.assertEqual(state.reward_filter, "money")
        await run_event(state.clear_filters)
        self.assertEqual(state.search_query, "")
        self.assertEqual(state.category_filters, [])
        self.assertEqual(state.reward_filter, "all")
        self.assertEqual(auth.email, "unsent@example.test")
        self.assertFalse(state.wall_open)
        await run_event(state.open_join_prompt)
        self.assertTrue(state.wall_open)

    async def test_helper_click_clears_job_preview_and_both_modes_are_distinct(
        self,
    ):
        state = GuestMapState()
        state.jobs = [
            {
                "code": _reference_code(1),
                "title": "Member's original title",
                "description": "Preview",
                "lat": 51.51,
                "lng": -0.13,
            }
        ]
        state.helpers = [
            {"code": _helper_reference_code(1), "lat": 51.52, "lng": -0.14}
        ]
        jobs = GuestMapState.map_markers.fget(state)
        self.assertEqual(jobs[0]["kind"], "job")
        await run_event(state.open_wall_for_marker, jobs[0]["id"])
        self.assertEqual(state.preview_title, "Member's original title")
        state.browse_mode = "get"
        helpers = GuestMapState.map_markers.fget(state)
        self.assertEqual(helpers[0]["kind"], "helper")
        self.assertEqual(helpers[0]["image_url"], "")
        self.assertNotEqual(jobs[0]["id"], helpers[0]["id"])
        await run_event(state.open_wall_for_marker, helpers[0]["id"])
        self.assertEqual(state.preview_title, "")
        self.assertEqual(state.preview_description, "")
        self.assertTrue(state.wall_open)

    def test_payloads_and_projections_fail_closed(self):
        self.assertEqual(
            set(GuestJob.__annotations__),
            {"code", "title", "description", "lat", "lng"},
        )
        self.assertEqual(
            set(GuestHelper.__annotations__), {"code", "lat", "lng"}
        )
        for latitude, longitude in (
            (None, None),
            (float("nan"), 1.0),
            (91.0, 1.0),
            (1.0, 181.0),
        ):
            self.assertIsNone(
                _public_job((1, "Title", "Description", latitude, longitude))
            )
            self.assertIsNone(_public_helper((1, latitude, longitude)))
        self.assertEqual(_helper_reference_code(8), _helper_reference_code(8))
        self.assertEqual(
            len({_helper_reference_code(i) for i in range(1000)}), 1000
        )
        self.assertFalse(
            {_helper_reference_code(i) for i in range(1000)}
            & {_reference_code(i) for i in range(1000)}
        )
        helper_source = inspect.getsource(_public_helper)
        self.assertIn("profile_approximate", helper_source)
        self.assertIn("if point is None:", helper_source)
        self.assertIn("return None", helper_source)

    def test_parameterized_query_eligibility_aliases_and_limits(self):
        hostile = "%' OR TRUE; --_"
        sql, params = guest_preview_query(
            "give",
            hostile,
            ["construction", "carer", "events", hostile],
            "money",
        )
        self.assertNotIn(hostile, sql)
        self.assertEqual(params["page_size"], PAGE_SIZE)
        self.assertIn("\\%", params["keyword"])
        self.assertIn("\\_", params["keyword"])
        self.assertEqual(params["reward"], "money")
        self.assertIn("p.reward_type = :reward", sql)
        self.assertIn("p.reward_types", sql)
        for token in expand_category_tokens(["construction", "carer"]):
            self.assertIn(token, params["categories"])
        self.assertNotIn("events", params["categories"])
        for clause in (
            "s.is_active = TRUE",
            "p.status = 'open'",
            "p.expires_at > now()",
            "ca.status = 'accepted'",
            "GREATEST(COALESCE(p.helpers_needed, 1), 1)",
            "NOT EXISTS",
            "skillkind_completed_task",
            "p.location_mode IN",
            "p.latitude BETWEEN -90 AND 90",
            "LIMIT :page_size",
        ):
            self.assertIn(clause, sql)
        sql, params = guest_preview_query(
            "get", "London", ["teaching"], "money"
        )
        self.assertEqual(params["offer_mode"], HELP_MODE_OFFER)
        self.assertEqual(params["both_mode"], HELP_MODE_BOTH)
        self.assertNotIn("reward", sql)
        self.assertNotIn("reward", params)
        self.assertIn("COALESCE(pr.show_location, FALSE) = TRUE", sql)
        self.assertIn("('approximate', 'live', 'fixed')", sql)
        self.assertIn("pr.preferred_categories", sql)
        self.assertIn("~* :categories", sql)
        self.assertIn("(^|[,;|[:space:]])", params["categories"])
        projection = sql.split("SELECT", 1)[1].split("FROM", 1)[0]
        self.assertEqual(projection.strip(), "s.id, pr.latitude, pr.longitude")
        self.assertEqual(
            {item["value"] for item in GUEST_CATEGORIES}, set(TASK_CATEGORIES)
        )
        self.assertIn({"value": "money", "label": "Money"}, GUEST_REWARDS)

    def test_background_read_only_generation_and_identity_guards(self):
        source = inspect.getsource(GuestMapState.load_preview.fn)
        self.assertGreaterEqual(
            source.count("await self.get_state(AuthState)"), 2
        )
        self.assertIn("generation != self._preview_generation", source)
        self.assertEqual(source.count("self.helpers = []"), 2)
        fetch_source = inspect.getsource(fetch_guest_preview)
        self.assertIn("MAX_DB_ATTEMPTS + 1", fetch_source)
        self.assertIn("async with rx.asession()", fetch_source)
        self.assertIn(
            "asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)", fetch_source
        )
        self.assertIn("asyncio.to_thread", fetch_source)
        self.assertNotIn("commit", fetch_source)
        self.assertNotIn("DiscoveryState", source)
        self.assertNotIn("self.map_center =", source)
        self.assertNotIn("self.map_zoom =", source)
        for mode in ("give", "get"):
            sql, _ = guest_preview_query(mode)
            for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "CREATE "):
                self.assertNotIn(forbidden, sql.upper())

    def test_actual_drawer_constructs_with_accessible_controls(self):
        for component in (
            guest_filters.guest_filter_drawer(),
            guest_map.guest_map_canvas(),
            guest_map.guest_map_experience(),
        ):
            self.assertIsInstance(component, rx.Component)
            self.assertTrue(component.render())
        source = inspect.getsource(guest_filters)
        for token in (
            "GuestMapState.set_browse_mode",
            "GuestMapState.toggle_category_choice",
            "on_submit=GuestMapState.submit_search",
            "on_change=GuestMapState.set_reward_filter",
            "on_click=GuestMapState.clear_filters",
            "on_click=GuestMapState.open_join_prompt",
            "GuestMapState.gate_distance_filter.throttle(100)",
            "gah-guest-filter-close",
            "gah-guest-filter-open",
            "Escape",
            "removeEventListener",
            "pointer-events-auto",
            "overflow-y-auto",
            "3.875rem",
            "max-w-[23.75rem]",
            "bg-white/80",
        ):
            self.assertIn(token, f"{source} {filter_layout.DRAWER_CLASS}")
        self.assertNotIn("DiscoveryState", source)
        self.assertNotIn("geolocation", source)
        self.assertNotIn("guest-map-language", source)
        self.assertNotIn("guest-auth-language", source)
        self.assertNotIn("dragPan.disable", _MAP_COMPONENT)
        self.assertNotIn("scrollZoom.disable", _MAP_COMPONENT)
        ast.parse(Path("app/states/guest_map_state.py").read_text())


if __name__ == "__main__":
    unittest.main()
