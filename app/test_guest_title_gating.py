import reflex as rx

import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.components import guest_map, bottom_nav
from app.components.openfreemap import _MAP_COMPONENT
from app.states.guest_map_state import GuestJob, GuestMapState, _reference_code
from app.states.profile_state import ProfileState
from app.states.auth_state import AuthState
from app.states.discovery_state import DiscoveryState


class GuestTitleGatingTests(unittest.IsolatedAsyncioTestCase):
    def test_loading_circle(self):
        source = Path("app/app.py").read_text().split("def theme_overrides")[0]
        for token in (
            "h-[100px] w-[100px]",
            "overflow-hidden rounded-full",
            "h-full w-full rounded-full object-cover",
            "duration: 3000",
            "prefers-reduced-motion",
            "removeEventListener",
            "from-[#ffe2bd] to-[#d9e9d4]",
            'role="status"',
        ):
            self.assertIn(token, source)

    def test_query_and_state_are_title_only(self):
        self.assertEqual(
            set(GuestJob.__annotations__),
            {"code", "title", "description", "lat", "lng"},
        )
        source = Path("app/states/guest_map_state.py").read_text()
        self.assertIn("SELECT p.id, p.title", source)
        projection = source.split("SELECT p.id, p.title", 1)[1].split(
            "FROM skillkind_help_post", 1
        )[0]
        for field in (
            "p.reward",
            "p.category",
            "p.city",
            "p.country",
            "p.author_id",
        ):
            self.assertNotIn(field, projection)
        self.assertNotIn("selected_job", source)
        self.assertIn("LIMIT :page_size", source)
        self.assertIn("PAGE_SIZE = 100", source)
        self.assertIn("LEFT(COALESCE(p.description, ''), 100)", source)
        self.assertIn("post_guest_approximate", source)
        self.assertIn("p.status = 'open'", source)
        self.assertIn("ca.status = 'accepted'", source)
        self.assertIn("p.expires_at > now()", source)
        self.assertEqual(len({_reference_code(i) for i in range(1000)}), 1000)
        markers = source.split("def map_markers")[1].split("@rx.event")[0]
        self.assertIn('"icon": "hand-helping"', markers)
        self.assertIn('"color": "#fba922"', markers)
        self.assertIn('"label": job["title"]', markers)

    def test_redacted_rows_and_controls(self):
        row = inspect.getsource(guest_map.guest_job_row)
        self.assertIn('aria_hidden="true"', row)
        self.assertIn("blur-[3px]", row)
        self.assertIn("on_click=GuestMapState.open_wall_for_marker", row)
        self.assertNotIn("truncate", row)
        self.assertNotIn(
            "on_scroll", inspect.getsource(guest_map.guest_list_view)
        )
        self.assertIn("guest_job_detail", inspect.getsource(guest_map))
        canvas = inspect.getsource(guest_map.guest_map_canvas)
        self.assertIn(
            "on_marker_select=GuestMapState.open_wall_for_marker", canvas
        )
        self.assertIn(
            "on_interaction_start=GuestMapState.collapse_search", canvas
        )
        self.assertIn("on_guest_control=GuestMapState.open_join_prompt", canvas)
        self.assertNotIn("scrollZoom.disable", _MAP_COMPONENT)
        self.assertNotIn("dragPan.disable", _MAP_COMPONENT)
        self.assertIn(
            "GuestMapState.go_to_map",
            inspect.getsource(guest_map.guest_map_brand_lockup),
        )
        self.assertIn(
            "ProfileState.return_to_map",
            inspect.getsource(bottom_nav.logo_button),
        )
        self.assertIn(
            "AuthState.is_signed_in", inspect.getsource(bottom_nav.is_active)
        )
        self.assertIsInstance(guest_map.guest_map_experience(), rx.Component)

    def test_gated_events_and_passive_gestures(self):
        state = GuestMapState()
        for handler, args in (
            (state.go_to_map, ()),
            (state.open_wall_for_marker, ("anything",)),
            (state.submit_member_search, ({},)),
        ):
            state.wall_open = False
            handler(*args)
            self.assertTrue(state.wall_open)
        state.wall_open = False
        state.search_expanded = True
        state.collapse_search()
        self.assertFalse(state.search_expanded)
        self.assertFalse(state.wall_open)

    async def test_logo_member_branch_and_guest_branch(self):
        guest = SimpleNamespace(
            open_join_prompt=lambda: setattr(guest, "wall_open", True),
            wall_open=False,
        )
        auth = SimpleNamespace(is_signed_in=False)
        discovery = DiscoveryState(_reflex_internal_init=True)
        discovery.filter_panel_open = True
        discovery.view_mode = "list"
        discovery.group_poster_id = 9
        policy = SimpleNamespace(open_key="privacy")

        async def get_state(cls):
            if cls is AuthState:
                return auth
            if cls is GuestMapState:
                return guest
            if cls is DiscoveryState:
                return discovery
            return policy

        state = SimpleNamespace(
            get_state=AsyncMock(side_effect=get_state),
            active_tab="community",
            error="",
            success="",
        )
        await ProfileState.return_to_map.fn(state)
        self.assertTrue(guest.wall_open)
        self.assertEqual(state.active_tab, "community")
        self.assertEqual(discovery.view_mode, "list")
        auth.is_signed_in = True
        result = await ProfileState.return_to_map.fn(state)
        self.assertEqual(state.active_tab, "discover")
        self.assertEqual(discovery.view_mode, "map")
        self.assertFalse(discovery.filter_panel_open)
        self.assertEqual(discovery.group_poster_id, 0)
        self.assertIsNone(result)
        self.assertEqual(discovery.selected_helper["id"], 0)
        self.assertFalse(discovery.is_loading_direct)


if __name__ == "__main__":
    unittest.main()
