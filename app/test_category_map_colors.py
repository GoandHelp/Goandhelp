import reflex as rx

import colorsys
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.components.help_post_panel import category_icon, category_card
from app.components.onboarding import category_card as onboarding_category_card
from app.states.help_post_state import HelpPostState
from app.states.onboarding_state import OnboardingState
from app.states.profile_state import ProfileState

from app.components.discover_panel import (
    category_choice_row,
    category_multiselect,
)
from app.components.openfreemap import _MAP_COMPONENT, open_free_map
from app.filter_categories import FILTER_CATEGORIES, expand_category_tokens
from app.models import LEGACY_CATEGORY_ALIASES, TASK_CATEGORIES
from app.skill_categories import (
    CATEGORY_COLORS,
    CATEGORY_CHOICES,
    CATEGORY_BLURBS,
    category_label,
    join_categories,
    normalize_categories,
    split_categories,
    canonical_category,
    category_color,
    category_icon_name,
    category_ink,
    CATEGORY_GRADIENT,
    post_categories,
    primary_category,
)
from app.states.discovery_state import DiscoveryState, EMPTY_HELPER, EMPTY_POST
from app.states.guest_map_state import GuestMapState


def rgb(color: str) -> tuple[float, float, float]:
    return tuple(int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))


def luminance(color: str) -> float:
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in rgb(color)
    ]
    return sum(
        value * weight
        for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
    )


class CategoryMapColorTests(unittest.TestCase):
    def test_complete_unique_palette_and_legible_ink(self):
        self.assertEqual(set(CATEGORY_COLORS), set(TASK_CATEGORIES))
        self.assertEqual(len(CATEGORY_COLORS), 23)
        self.assertEqual(len(set(CATEGORY_COLORS.values())), 23)
        for category, fill in CATEGORY_COLORS.items():
            with self.subTest(category=category):
                self.assertRegex(fill, r"^#[0-9a-f]{6}$")
                ink = category_ink(category)
                self.assertEqual(ink, "#ffffff")
                self.assertGreaterEqual(1.05 / (luminance(fill) + 0.05), 3.0)

    def test_ordered_shared_choices_and_new_category_glyphs(self):
        expected = sorted(
            TASK_CATEGORIES,
            key=lambda value: (
                value == "other",
                category_label(value).casefold(),
            ),
        )
        self.assertEqual([item["value"] for item in CATEGORY_CHOICES], expected)
        self.assertEqual(
            [item["value"] for item in FILTER_CATEGORIES],
            ["events", *expected],
        )
        self.assertEqual(set(CATEGORY_BLURBS), set(TASK_CATEGORIES))
        request = HelpPostState(_reflex_internal_init=True)
        profile = ProfileState(_reflex_internal_init=True)
        onboarding = OnboardingState(_reflex_internal_init=True)
        self.assertEqual(request.categories, CATEGORY_CHOICES)
        self.assertEqual(set(profile.category_options), set(expected))
        for category, icon in (("mechanic", "car"), ("music", "music")):
            with self.subTest(category=category):
                self.assertEqual(category_icon_name(category), icon)
                self.assertIn(f"  {icon}: [", _MAP_COMPONENT)
                choice = next(
                    item
                    for item in CATEGORY_CHOICES
                    if item["value"] == category
                )
                self.assertTrue(choice["blurb"])
                self.assertTrue(category_card(choice).render())
                self.assertTrue(onboarding_category_card(choice).render())
                self.assertTrue(category_icon(category, "h-4 w-4").render())
                profile.toggle_category(category)
                onboarding.toggle_category(category)
        self.assertEqual(profile.selected_categories, ["mechanic", "music"])
        self.assertEqual(onboarding.categories, ["mechanic", "music"])

    def test_legacy_mechanic_is_not_workshop_and_selection_order_survives(self):
        self.assertEqual(canonical_category(" MECHANIC "), "mechanic")
        self.assertEqual(category_label("mechanic"), "Mechanic")
        self.assertEqual(post_categories("", "mechanic"), ["mechanic"])
        self.assertEqual(expand_category_tokens(["mechanic"]), ["mechanic"])
        self.assertEqual(expand_category_tokens(["workshop"]), ["workshop"])
        self.assertNotEqual(
            category_color("mechanic"), category_color("workshop")
        )
        chosen = ["music", "mechanic", "workshop", "music"]
        expected = ["music", "mechanic", "workshop"]
        self.assertEqual(normalize_categories(chosen), expected)
        self.assertEqual(split_categories(join_categories(chosen)), expected)
        self.assertEqual(
            post_categories(join_categories(chosen), "workshop"), expected
        )
        self.assertEqual(primary_category(chosen), "music")

    def test_legacy_row_and_multicategory_request_marker_selection_and_pulse(
        self,
    ):
        row = [None] * 37
        row[0], row[1], row[3], row[14] = 1, "Repair needed", "mechanic", 7
        row[25], row[26] = 48.8, 2.3
        with patch(
            "app.states.discovery_state.post_member_approximate",
            return_value=(48.81, 2.31),
        ):
            legacy = DiscoveryState._row_to_post(
                SimpleNamespace(_quote_allowed=DiscoveryState._quote_allowed),
                row,
                [],
            )
            row[32] = "music,mechanic,workshop"
            multi = DiscoveryState._row_to_post(
                SimpleNamespace(_quote_allowed=DiscoveryState._quote_allowed),
                row,
                [],
            )
        self.assertEqual(legacy["category_label"], "Mechanic")
        self.assertEqual(legacy["categories"], ["mechanic"])
        self.assertEqual(multi["category"], "music")
        state = SimpleNamespace(
            posts=[multi],
            visible_post_ids=[1],
            map_pulse_post_id=1,
            map_pulse_token=8,
            group_poster_id=0,
            selected_post=multi,
        )
        marker = DiscoveryState.job_map_markers.fget(state)[0]
        self.assertEqual(marker["color"], category_color("music"))
        self.assertEqual(marker["ink"], category_ink("music"))
        self.assertEqual(marker["icon"], "music")
        self.assertTrue(marker["selected"])
        self.assertEqual(marker["pulse_token"], 8)
        state.posts.append({**legacy, "id": 2})
        state.map_pulse_post_id = 2
        marker = DiscoveryState.job_map_markers.fget(state)[0]
        self.assertEqual(marker["id"], "g7")
        self.assertEqual(marker["color"], category_color("mechanic"))
        self.assertEqual(marker["ink"], category_ink("mechanic"))
        self.assertTrue(marker["selected"])
        self.assertEqual(marker["pulse_token"], 8)

    def test_required_example_hues(self):
        agriculture = colorsys.rgb_to_hls(*rgb(category_color("agriculture")))
        arts = colorsys.rgb_to_hls(*rgb(category_color("arts")))
        carer = colorsys.rgb_to_hls(*rgb(category_color("carer")))
        cleaner = colorsys.rgb_to_hls(*rgb(category_color("cleaner")))
        self.assertTrue(0.2 < agriculture[0] < 0.4)
        self.assertGreater(agriculture[1], 0.3)
        self.assertLess(agriculture[1], 0.6)
        self.assertTrue(0.25 < arts[0] < 0.45)
        self.assertLess(arts[1], 0.3)
        self.assertTrue(0.45 < carer[0] < 0.55)
        self.assertTrue(0.55 < cleaner[0] < 0.7)
        self.assertEqual(category_ink("agriculture"), "#ffffff")
        self.assertEqual(category_ink("arts"), "#ffffff")
        self.assertEqual(category_ink("cleaner"), "#ffffff")
        self.assertIn("linear-gradient(180deg", CATEGORY_GRADIENT)
        self.assertIn("color-mix(in srgb", CATEGORY_GRADIENT)

    def test_alias_normalization_and_unknown_fallback(self):
        for alias, category in LEGACY_CATEGORY_ALIASES.items():
            with self.subTest(alias=alias):
                self.assertEqual(
                    category_color(alias), category_color(category)
                )
                self.assertEqual(category_ink(alias), category_ink(category))
                self.assertEqual(
                    category_icon_name(alias), category_icon_name(category)
                )
        for value in ("", "unknown category"):
            self.assertEqual(canonical_category(value), "")
            self.assertEqual(category_color(value), CATEGORY_COLORS["other"])
            self.assertEqual(category_ink(value), category_ink("other"))
        self.assertEqual(
            category_color("  AGRICULTURE  "), category_color("agriculture")
        )
        self.assertEqual(
            primary_category(post_categories("artist,cleaner", "agriculture")),
            "arts",
        )

    def test_filter_options_share_identity_and_render_accessibly(self):
        self.assertEqual(
            {option["value"] for option in FILTER_CATEGORIES},
            set(TASK_CATEGORIES) | {"events"},
        )
        self.assertEqual(FILTER_CATEGORIES[0]["value"], "events")
        self.assertEqual(FILTER_CATEGORIES[-1]["value"], "other")
        for option in FILTER_CATEGORIES:
            with self.subTest(category=option["value"]):
                if option["value"] == "events":
                    self.assertEqual(option["icon"], "calendar-days")
                    self.assertEqual(option["color"], "#c2410c")
                    self.assertEqual(option["ink"], "#ffffff")
                else:
                    self.assertIn(option["value"], TASK_CATEGORIES)
                    self.assertEqual(
                        option["color"], category_color(option["value"])
                    )
                    self.assertEqual(
                        option["ink"], category_ink(option["value"])
                    )
                component = category_choice_row(option)
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                rendered = str(component)
                self.assertIn(option["color"], rendered)
                self.assertEqual(option["ink"], "#ffffff")
                self.assertIn("text-white", rendered)
                self.assertIn(CATEGORY_GRADIENT, rendered)
                self.assertIn("checkbox", rendered)
                self.assertIn(option["label"], rendered)
        self.assertTrue(category_multiselect().render())
        self.assertEqual(
            expand_category_tokens(["arts", "carer"]),
            ["arts", "artist", "carer", "babysitter", "nanny"],
        )
        source = inspect.getsource(category_choice_row)
        self.assertIn(
            'DiscoveryState.toggle_category_choice(item["value"])', source
        )
        self.assertIn(
            'DiscoveryState.category_filters.contains(item["value"])', source
        )

    def test_single_and_grouped_marker_primary_category(self):
        state = SimpleNamespace(
            posts=[],
            visible_post_ids=[],
            map_pulse_post_id=0,
            map_pulse_token=0,
            group_poster_id=0,
            selected_post=EMPTY_POST,
        )
        for index, category in enumerate(TASK_CATEGORIES, start=1):
            state.posts = [
                {
                    **EMPTY_POST,
                    "id": index,
                    "poster_id": index,
                    "category": category,
                }
            ]
            marker = DiscoveryState.job_map_markers.fget(state)[0]
            self.assertEqual(marker["color"], category_color(category))
            self.assertEqual(marker["ink"], category_ink(category))
            self.assertEqual(marker["icon"], category_icon_name(category))
        state.posts = [
            {**EMPTY_POST, "id": 1, "poster_id": 7, "category": "agriculture"},
            {**EMPTY_POST, "id": 2, "poster_id": 7, "category": "arts"},
        ]
        marker = DiscoveryState.job_map_markers.fget(state)[0]
        self.assertEqual(marker["id"], "g7")
        self.assertEqual(marker["color"], category_color("agriculture"))
        state.visible_post_ids = [2]
        marker = DiscoveryState.job_map_markers.fget(state)[0]
        self.assertEqual(marker["color"], category_color("arts"))
        self.assertEqual(marker["ink"], category_ink("arts"))
        state.map_pulse_post_id = 1
        state.map_pulse_token = 5
        marker = DiscoveryState.job_map_markers.fget(state)[0]
        self.assertEqual(marker["color"], category_color("agriculture"))
        self.assertEqual(marker["ink"], category_ink("agriculture"))
        self.assertEqual(marker["pulse_token"], 5)

    def test_renderer_color_ink_signature_and_unchanged_marker_styles(self):
        job = _MAP_COMPONENT.split('} else if (marker.kind === "job") {')[
            1
        ].split("} else if")[0]
        self.assertIn("marker.color", job)
        self.assertIn('" + jobGradient', job)
        self.assertIn("width:39px;height:39px", job)
        self.assertIn('goAndHelpIconSvg(marker.icon, 27, "#ffffff")', job)
        self.assertIn("linear-gradient(180deg", job)
        self.assertIn("jobGradient", job)
        self.assertIn(' : "#fba922"', job)
        self.assertIn("border:0;", job)
        self.assertIn(
            'if (marker.selected) pin.style.outline = "2px solid #e08b12"', job
        )
        signature = _MAP_COMPONENT.split("const signature = [")[1].split(
            "].join"
        )[0]
        self.assertIn('marker.color || ""', signature)
        self.assertIn('marker.ink || ""', signature)
        self.assertIn("marker.pulse_token || 0", signature)
        self.assertIn(
            "const stroke = /^#[0-9a-f]{6}$/i.test(ink)", _MAP_COMPONENT
        )
        self.assertIn("iterations: 5", _MAP_COMPONENT)
        helper = _MAP_COMPONENT.split('} else if (marker.kind === "helper") {')[
            1
        ].split('} else if (marker.kind === "job")')[0]
        self.assertIn("background:#fba922", helper)
        self.assertIn("width:45px;height:45px", helper)
        self.assertIn('goAndHelpIconSvg("hand-helping", 30)', helper)
        self.assertIn("photo.src = marker.image_url", helper)
        self.assertNotIn("marker.ink", helper)
        profile = _MAP_COMPONENT.split(
            'marker.id === "onboarding-private-profile"'
        )[1].split('} else if (marker.kind === "helper")')[0]
        self.assertIn("width:48px;height:48px", profile)
        self.assertIn('goAndHelpIconSvg("hand-helping", 23)', profile)
        state = SimpleNamespace(
            helpers=[{**EMPTY_HELPER, "id": 8, "image_url": "/photo.png"}],
            selected_helper=EMPTY_HELPER,
        )
        helper_marker = DiscoveryState.helper_map_markers.fget(state)[0]
        self.assertEqual(helper_marker["image_url"], "/photo.png")
        self.assertNotIn("ink", helper_marker)
        component = open_free_map(
            markers=[
                {
                    "id": "p1",
                    "lat": 50.0,
                    "lng": 2.0,
                    "kind": "job",
                    "color": category_color("agriculture"),
                    "ink": category_ink("agriculture"),
                }
            ]
        )
        self.assertTrue(component.render())

    def test_guest_payload_keeps_generic_orange_and_no_category(self):
        state = SimpleNamespace(
            jobs=[
                {
                    "code": "ABCD",
                    "title": "Request",
                    "description": "Preview",
                    "lat": 48.8,
                    "lng": 2.3,
                }
            ]
        )
        marker = GuestMapState.map_markers.fget(state)[0]
        self.assertEqual(marker["color"], "#fba922")
        self.assertEqual(marker["icon"], "hand-helping")
        self.assertNotIn("ink", marker)
        self.assertNotIn("category", marker)
        self.assertNotIn("description", marker)


if __name__ == "__main__":
    unittest.main()
