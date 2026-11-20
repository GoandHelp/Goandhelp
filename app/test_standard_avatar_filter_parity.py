import reflex as rx

import inspect
import unittest
from urllib.parse import unquote
from xml.etree import ElementTree

from test_utils import run_event
from app.avatars import USER_AVATAR, animal_avatar, member_avatar
from app.components import (
    discover_panel,
    guest_filters,
    member_map,
    filter_layout as layout,
)
from app.components.location_selection import location_selection, location_tap
from app.states.auth_state import AuthState
from app.states.guest_map_state import GuestMapState
from app.states.discovery_state import _avatar_image_url


class StandardAvatarTests(unittest.TestCase):
    def test_all_seeds_use_one_private_self_contained_silhouette(self):
        for seed in (
            "",
            "private@example.test",
            "fox",
            "猫",
            "🦉",
            "member-123",
        ):
            self.assertEqual(animal_avatar(seed), USER_AVATAR)
            self.assertEqual(_avatar_image_url("", seed), USER_AVATAR)
        reactive = animal_avatar(AuthState.subscriber_id)
        self.assertIsInstance(reactive, rx.Var)
        self.assertEqual(str(reactive), str(rx.Var.create(USER_AVATAR)))
        self.assertNotIn("subscriber_id", str(reactive))
        svg = unquote(USER_AVATAR.split(",", 1)[1])
        root = ElementTree.fromstring(svg)
        self.assertEqual(root.attrib["width"], "64")
        self.assertEqual(root.attrib["height"], "64")
        self.assertEqual(root.attrib["viewBox"], "0 0 64 64")
        circle = root.find("{http://www.w3.org/2000/svg}circle")
        self.assertEqual(circle.attrib["r"], "11")
        body = root.find("{http://www.w3.org/2000/svg}path")
        self.assertEqual(body.attrib["d"], "M10 56 A22 22 0 0 1 54 56 Z")
        for forbidden in (
            "face_",
            "fox",
            "owl",
            "cat",
            "dog",
            "image",
            "href",
            "script",
            "dicebear",
            "example.test",
        ):
            self.assertNotIn(forbidden, svg)
        self.assertTrue(rx.image(src=reactive, alt="Member").render())

    def test_uploaded_photos_keep_exact_precedence(self):
        self.assertEqual(
            member_avatar("photos/custom.webp", "any"),
            "/_upload/photos/custom.webp",
        )
        self.assertEqual(
            _avatar_image_url("photos/custom.webp", "any"),
            "/_upload/photos/custom.webp",
        )
        source = inspect.getsource(member_avatar)
        self.assertIn(
            "rx.cond(path, rx.get_upload_url(path), animal_avatar(seed))",
            source,
        )
        self.assertIn('return f"/_upload/{path}"', source)
        self.assertTrue(
            rx.image(
                src=member_avatar(
                    rx.Var.create("photos/custom.webp"), AuthState.subscriber_id
                ),
                alt="Uploaded photo",
            ).render()
        )


class FilterParityTests(unittest.IsolatedAsyncioTestCase):
    def test_shared_geometry_and_rendered_controls(self):
        member = str(
            discover_panel.filter_drawer(
                layout.DRAWER_CLASS, compact=True
            ).render()
        )
        guest = str(guest_filters.guest_filter_drawer().render())
        for rendered in (member, guest):
            for shared in (
                layout.DRAWER_CLASS,
                layout.CONTENT_CLASS,
                layout.HEADER_CLASS,
                layout.CLOSE_CLASS,
                layout.BODY_CLASS,
                layout.LOCATION_SPACING_CLASS,
                layout.DISTANCE_SPACING_CLASS,
                layout.FOOTER_CLASS,
                layout.RANGE_CLASS,
            ):
                self.assertIn(shared, rendered)
            self.assertNotIn("-mt-[6px]", rendered)
        for component in (
            member_map.member_filter_sheet(),
            discover_panel.filter_drawer(layout.DRAWER_CLASS, compact=False),
        ):
            self.assertTrue(component.render())
        source = inspect.getsource(discover_panel.filter_drawer)
        self.assertNotIn("absolute left-1/2", source)
        self.assertIn("layout.HEADER_TOGGLES_CLASS", source)
        self.assertIn("pr-10", layout.HEADER_CLASS)
        self.assertIn("flex-wrap", layout.HEADER_TOGGLES_CLASS)
        self.assertIn("right-0 top-0", layout.CLOSE_CLASS)
        self.assertIn("mt-2", layout.LOCATION_SPACING_CLASS)
        self.assertIn("mt-1", layout.DISTANCE_SPACING_CLASS)
        self.assertIn("gap-1.5", layout.BODY_CLASS)
        self.assertIn("h-10", layout.FIELD_CLASS)
        self.assertIn(
            "layout.LOCATION_ROW_CLASS", inspect.getsource(location_selection)
        )
        self.assertIn(
            "layout.LOCATION_ON_CLASS", inspect.getsource(location_tap)
        )

    def test_guest_gates_keep_public_filters_and_keyboard_navigation(self):
        source = inspect.getsource(guest_filters)
        for token in (
            "GuestMapState.submit_search",
            "GuestMapState.set_browse_mode",
            "GuestMapState.toggle_category_choice",
            "GuestMapState.set_reward_filter",
            "GuestMapState.open_join_prompt",
            "GuestMapState.gate_distance_filter.throttle(100)",
            "gah-guest-filter-close",
            "gah-guest-filter-open",
            "Escape",
            "removeEventListener",
        ):
            self.assertIn(token, source)
        self.assertNotIn('rx.icon("lock"', source)
        self.assertNotIn("ProfileState", source)
        self.assertIn(
            'disabled=GuestMapState.browse_mode == "get"',
            inspect.getsource(guest_filters.guest_rewards),
        )
        self.assertIn('title=ui("Register or sign in")', source)
        self.assertIn(
            'aria_checked="true"',
            inspect.getsource(guest_filters.guest_location_row),
        )
        self.assertIn(
            'default_value="0"',
            inspect.getsource(guest_filters.guest_distance_block),
        )

    async def test_distance_is_never_applied_and_only_nonzero_opens_prompt(
        self,
    ):
        state = GuestMapState()
        state.search_expanded = True
        state.search_query = "London"
        state.reward_filter = "money"
        await run_event(state.gate_distance_filter, "0")
        self.assertFalse(state.wall_open)
        self.assertTrue(state.search_expanded)
        await run_event(state.gate_distance_filter, "25")
        source = inspect.getsource(GuestMapState.gate_distance_filter.fn)
        self.assertIn("slider.value = '0'", source)
        self.assertIn("yield GuestMapState.open_join_prompt", source)
        await run_event(state.open_join_prompt)
        self.assertTrue(state.wall_open)
        self.assertFalse(state.search_expanded)
        self.assertEqual(state.view_mode, "map")
        self.assertFalse(GuestMapState.is_list_view.fget(state))
        self.assertEqual(state.search_query, "London")
        self.assertEqual(state.reward_filter, "money")


if __name__ == "__main__":
    unittest.main()
