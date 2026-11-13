import reflex as rx

import ast
import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components import (
    guest_map,
    member_map,
    discover_panel,
    map_utility_icon,
)
from app.components.openfreemap import _MAP_COMPONENT
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState
from app.states.discovery_state import DiscoveryState, DISCOVERY_RESULT_CAP
from app.states.map_picker_state import MapPickerState
from app.states.onboarding_state import OnboardingState
from app.states.guest_map_state import GuestMapState, _public_job


class HomeMapRevisionTests(unittest.IsolatedAsyncioTestCase):
    async def test_map_interaction_dismisses_utilities_not_job(self):
        from app.states.discovery_state import EMPTY_HELPER, EMPTY_POST
        from app.states.notification_state import NotificationState
        from app.states.world_search_state import WorldSearchState

        state = DiscoveryState()
        search = await state.get_state(WorldSearchState)
        profile = await state.get_state(ProfileState)
        notifications = await state.get_state(NotificationState)
        state.selected_helper = {**EMPTY_HELPER, "id": 7}
        state.selected_post = {**EMPTY_POST, "id": 9}
        state.direct_open = True
        state.direct_post_id = 9
        state.direct_draft = "Unsent draft"
        state.direct_warning = "Warning"
        state.direct_notice = "Notice"
        state.is_loading_direct = True
        state.filter_panel_open = state.category_list_open = True
        search.expanded = profile.settings_open = notifications.panel_open = (
            True
        )
        for _ in range(2):
            await DiscoveryState.handle_map_interaction.fn(state)
            self.assertEqual(state.selected_helper, EMPTY_HELPER)
            self.assertEqual(state.selected_post["id"], 9)
            self.assertFalse(state.direct_open)
            self.assertEqual(state.direct_post_id, 0)
            self.assertEqual(state.direct_draft, "")
            self.assertEqual(state.direct_requests, [])
            self.assertEqual(state.direct_warning, "")
            self.assertEqual(state.direct_notice, "")
            self.assertFalse(state.is_loading_direct)
            self.assertFalse(state.filter_panel_open)
            self.assertFalse(state.category_list_open)
            self.assertFalse(search.expanded)
            self.assertFalse(profile.settings_open)
            self.assertFalse(notifications.panel_open)
        self.assertIn(
            "on_interaction_start=DiscoveryState.handle_map_interaction",
            inspect.getsource(member_map.member_map_canvas),
        )

    def test_helper_list_heading_and_flat_root(self):
        component = discover_panel.helper_list()
        self.assertEqual(
            str(component.class_name).strip('"'), "w-full bg-transparent"
        )
        heading = component.children[0]
        self.assertEqual(heading.tag, "h3")
        for token in ("text-center", "text-xl", "sm:text-2xl"):
            self.assertIn(token, str(heading.class_name))
        source = inspect.getsource(discover_panel.helper_list)
        for token in (
            "rx.match(",
            "DiscoveryState.visible_helpers.length()",
            '(0, rx.el.span("No helpers nearby"))',
            'rx.el.span("1", class_name="text-[#e08b12]")',
            '" helper nearby"',
            '" helpers nearby"',
            "text-[#e08b12]",
            "rx.foreach(DiscoveryState.visible_helpers, helper_row)",
            "DiscoveryState.is_loading",
        ):
            self.assertIn(token, source)
        self.assertRegex(source, r"\(\s*1,\s*rx\.el\.span\(")
        self.assertNotIn("Icon", str(heading))
        self.assertNotIn("People available to help", source)
        self.assertNotIn("rounded-full", str(heading))
        self.assertNotIn("users-round", str(heading))
        self.assertTrue(component.render())

    def test_crisp_shared_controls(self):
        icon = inspect.getsource(map_utility_icon.map_utility_icon)
        bell_icon = inspect.getsource(map_utility_icon.filled_bell_icon)
        settings_icon = inspect.getsource(map_utility_icon.filled_settings_icon)
        self.assertIn('fill="#fba922"', bell_icon)
        self.assertIn("C13.5 29 13.6 29.8 13.9 30.5", bell_icon)
        self.assertIn('("cog", filled_settings_icon())', icon)
        self.assertIn('("settings", filled_settings_icon())', icon)
        self.assertIn('fill_rule="evenodd"', settings_icon)
        self.assertIn("A5.5 5.5 0 1 0 18 23.5", settings_icon)
        self.assertNotIn("bg-white", settings_icon)
        self.assertNotIn('rx.icon("settings"', settings_icon)
        self.assertIn('aria_hidden="true"', icon)
        for factory in (
            member_map.member_filters_button,
            guest_map.guest_filters_button,
        ):
            self.assertIn("bg-white", str(factory().class_name).split())
            self.assertIn("text-[#fba922]", inspect.getsource(factory))
        css = Path("app/app.py").read_text()
        self.assertNotIn("radial-gradient", css)
        self.assertIn(":not(.gah-search-submit)", css)
        self.assertIn("gah-search-inner:is(:focus", css)
        form = inspect.getsource(discover_panel.filter_drawer)
        self.assertIn("border-gray-300", form)
        self.assertIn("focus-within:border-[#fba922]", form)

    def test_job_branch_and_camera(self):
        job = _MAP_COMPONENT.split('} else if (marker.kind === "job") {')[
            1
        ].split("} else if")[0]
        for token in (
            "border:0;",
            'background:" + jobGradient',
            "box-shadow:none",
            'goAndHelpIconSvg(marker.icon, 27, "#ffffff")',
            "border-radius:999px",
        ):
            self.assertIn(token, job)
        self.assertNotIn("theme.ring", job)
        self.assertNotIn("solid white", job)
        self.assertNotIn("solid #ffffff", job)
        self.assertIn("marker.color", job)
        self.assertIn('goAndHelpIconSvg(marker.icon, 27, "#ffffff")', job)
        self.assertIn(' : "#fba922"', job)
        self.assertIn(
            "[center[0], center[1], zoom, cameraUpdates, cameraDuration]",
            _MAP_COMPONENT,
        )
        self.assertIn("if (!map || !cameraUpdates) return;", _MAP_COMPONENT)
        self.assertIn(
            "const duration = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : cameraDuration;",
            _MAP_COMPONENT,
        )
        self.assertIn(
            "if (duration > 0) map.easeTo({center, zoom, duration});\n"
            "    else map.jumpTo({center, zoom});",
            _MAP_COMPONENT,
        )
        for path in (
            "app/components/map_picker.py",
            "app/components/onboarding.py",
        ):
            self.assertIn("camera_updates=False", Path(path).read_text())
        for handler in (
            MapPickerState.set_point,
            MapPickerState.position_found,
            OnboardingState.set_location_point,
        ):
            source = inspect.getsource(handler.fn)
            self.assertNotIn("self.center =", source)
            self.assertNotIn("self.zoom =", source)
            self.assertNotIn("self.map_center =", source)
            self.assertNotIn("self.map_zoom =", source)

    def test_mode_specific_markers_and_give_only_events(self):
        jobs = [{"id": f"p{i}"} for i in range(100)]
        helpers = [{"id": f"h{i}"} for i in range(100)]
        state = SimpleNamespace(
            job_map_markers=jobs, helper_map_markers=helpers, map_mode="give"
        )
        self.assertEqual(DiscoveryState.map_markers.fget(state), jobs)
        state.map_mode = "get"
        self.assertEqual(DiscoveryState.map_markers.fget(state), helpers)
        self.assertLessEqual(DISCOVERY_RESULT_CAP, 100)
        canvas = inspect.getsource(member_map.member_map_canvas)
        self.assertNotIn("home_map_markers", canvas)
        map_call = next(
            node
            for node in ast.walk(ast.parse(canvas))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open_free_map"
        )
        markers = next(
            kw.value for kw in map_call.keywords if kw.arg == "markers"
        )
        self.assertEqual(ast.unparse(markers.func), "rx.cond")
        self.assertEqual(
            [ast.unparse(arg) for arg in markers.args],
            [
                "DiscoveryState.is_give_mode",
                "DiscoveryState.map_markers + OnboardingState.celebration_map_markers + EventState.map_markers",
                "DiscoveryState.map_markers",
            ],
        )
        refresh = inspect.getsource(DiscoveryState.refresh_board.fn)
        self.assertEqual(refresh.count("yield EventState.load_events"), 1)
        self.assertIn("yield DiscoveryState.load_jobs", refresh)
        self.assertIn("yield DiscoveryState.load_helpers", refresh)
        self.assertIn(
            "self.map_mode = MODE_GIVE",
            inspect.getsource(DiscoveryState.select_post.fn),
        )
        self.assertIn(
            "DiscoveryState.open_member_profile(helper_id)",
            inspect.getsource(DiscoveryState.select_helper.fn),
        )
        self.assertIn(
            "self.map_mode = MODE_GIVE",
            inspect.getsource(DiscoveryState.open_poster_group.fn),
        )

    async def test_distance_requires_saved_approximate_point(self):
        profile = SimpleNamespace(location_mode="hidden")
        auth = SimpleNamespace(subscriber_id="12")

        async def get_state(cls):
            return profile if cls is ProfileState else auth

        state = SimpleNamespace(
            get_state=get_state,
            _viewer_point=AsyncMock(return_value=(51.5, -0.12, 25)),
            distance_km=0,
            distance_initialized=True,
            distance_reset_token=0,
            distance_warning=False,
            error="",
            success="",
        )
        for handler in (
            DiscoveryState.set_distance_filter,
            DiscoveryState.commit_distance_filter,
        ):
            state._accept_distance = lambda value: (
                DiscoveryState._accept_distance(state, value)
            )
            await handler.fn(state, 25)
            self.assertEqual(state.distance_km, 0)
            self.assertTrue(state.distance_warning)
        self.assertEqual(state.distance_reset_token, 2)
        profile.location_mode = "approximate"
        state._viewer_point.return_value = (None, None, 25)
        self.assertFalse(await DiscoveryState._accept_distance(state, 25))
        state._viewer_point.return_value = (51.5, -0.12, 25)
        self.assertTrue(await DiscoveryState._accept_distance(state, 25))
        self.assertEqual(state.distance_km, 25)
        self.assertFalse(state.distance_warning)
        warning = inspect.getsource(discover_panel.show_my_location_block)
        self.assertIn("Turn on your Approximate location first", warning)
        self.assertIn("prefers-reduced-motion: reduce", warning)
        self.assertIn(
            "[{opacity:0},{opacity:1},{opacity:0},{opacity:1}]", warning
        )
        self.assertLess(
            warning.index("Turn on your"),
            warning.index("location_selection()"),
        )

    def test_guest_redaction_and_withholding(self):
        with patch("app.location_privacy.is_land", return_value=False):
            self.assertIsNone(
                _public_job((12, "Title", "Description", 51.5, -0.12))
            )
        state = GuestMapState()
        state.jobs = [
            {
                "code": "opaque",
                "title": "Title",
                "description": "Short description",
                "lat": 51.51,
                "lng": -0.13,
            }
        ]
        state.open_wall_for_marker("opaque")
        self.assertTrue(state.wall_open)
        self.assertEqual(state.preview_title, "Title")
        self.assertEqual(
            state.wall_reason,
            "Sign up or login to Search for jobs, people or places around the world",
        )
        preview = inspect.getsource(guest_map.guest_job_detail)
        self.assertIn('aria_hidden="true"', preview)
        self.assertIn("blur-[3px]", preview)
        self.assertNotIn("poster", preview)
        self.assertNotIn(
            "Browse job titles. Details unlock",
            inspect.getsource(guest_map.guest_map_canvas),
        )
        state.close_wall()
        self.assertEqual(state.preview_title, "")

    def test_changed_components_render(self):
        for factory in (
            guest_map.guest_map_experience,
            member_map.member_map_experience,
            discover_panel.distance_filter_block,
            discover_panel.show_my_location_block,
        ):
            self.assertIsInstance(factory(), rx.Component)
        for path in (
            "app/states/discovery_state.py",
            "app/states/guest_map_state.py",
            "app/states/map_picker_state.py",
            "app/components/discover_panel.py",
        ):
            ast.parse(Path(path).read_text())


if __name__ == "__main__":
    unittest.main()
