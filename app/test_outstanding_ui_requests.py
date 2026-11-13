import reflex as rx

import inspect
import unittest
from pathlib import Path

from app.components import (
    advanced_filters,
    discover_panel,
    guest_map,
    member_map,
)
from app.components.help_hub_panel import post_help_section, help_summary_card
from app.components.map_utility_icon import (
    filled_settings_icon,
    filled_bell_icon,
)
from app.components.openfreemap import _MAP_COMPONENT
from app.components.request_heading import request_heading
from app.components.unified_inbox import inbox_toolbar
from app.states.discovery_state import DiscoveryState, EMPTY_POST
from app.states.profile_state import ProfileState


class OutstandingUIRequestsTests(unittest.TestCase):
    def test_request_button_and_motion(self):
        hero = post_help_section()
        self.assertEqual(hero.tag, "section")
        self.assertNotIn("rounded", str(hero.class_name))
        button = hero.children[0]
        self.assertEqual(button.tag, "button")
        button_classes = str(button.class_name).split()
        for token in (
            "mx-auto",
            "w-fit",
            "min-h-0",
            "justify-center",
            "bg-[#fba922]",
        ):
            self.assertIn(token, button_classes)
        for token in (
            "w-full",
            "min-h-24",
            "overflow-hidden",
            "w-screen",
            "h-24",
        ):
            self.assertNotIn(token, button_classes)
        button_rendered = str(button)
        self.assertIn("LucideArrowRight", button_rendered)
        self.assertNotIn(
            "Tell the community what you need, when, and what you can offer back.",
            button_rendered,
        )
        self.assertIn("text-center", button_rendered)
        self.assertIn("toggle_form", str(button.event_triggers))
        source = inspect.getsource(post_help_section)
        self.assertIn("aria_expanded", source)
        self.assertIn("aria_controls", source)
        css = Path("assets/map.css").read_text()
        self.assertNotIn("gah-ask-light-line", css)
        self.assertNotIn(".gah-request-ask::after", css)
        for title in ("help given", "help received"):
            rendered = str(help_summary_card(title, rx.Var.create(0)))
            self.assertIn("text-[#e08b12]", rendered)
            self.assertIn(title, rendered)
            self.assertNotIn("No help", rendered)
        zero = str(request_heading("Confirmed Help", rx.Var.create(0)))
        self.assertIn(" upcoming jobs", zero)
        self.assertNotIn("No upcoming jobs", zero)

    def test_map_controls_and_avatars(self):
        self.assertEqual(len(filled_bell_icon().children), 1)
        self.assertEqual(len(filled_settings_icon().children), 1)
        self.assertNotIn("bg-white", str(filled_settings_icon()))
        self.assertIn(
            'fill_rule="evenodd"', inspect.getsource(filled_settings_icon)
        )
        self.assertIn(
            "C13.5 29 13.6 29.8 13.9 30.5", inspect.getsource(filled_bell_icon)
        )
        self.assertTrue(filled_bell_icon().render())
        self.assertTrue(filled_settings_icon().render())
        for factory in (
            member_map.member_filters_button,
            guest_map.guest_filters_button,
        ):
            self.assertIn("bg-white", str(factory().class_name))
            self.assertIn("text-[#fba922]", str(factory()))
        for factory in (
            member_map.member_brand_lockup,
            guest_map.guest_map_brand_lockup,
        ):
            source = inspect.getsource(factory)
            self.assertIn("brand_mark()", source)
            self.assertIn("aria_label=", source)
            self.assertNotIn('rx.el.span("Go and Help"', source)
        helper = _MAP_COMPONENT.split('marker.kind === "helper"', 1)[1].split(
            'marker.kind === "job"', 1
        )[0]
        job = _MAP_COMPONENT.split('marker.kind === "job"', 1)[1].split(
            'marker.kind === "event"', 1
        )[0]
        for branch, dimensions in (
            (helper, "width:45px;height:45px"),
            (job, "width:39px;height:39px"),
        ):
            self.assertIn(dimensions, branch)
            self.assertIn("border:0;", branch)
            self.assertIn("2px solid #e08b12", branch)
            self.assertNotIn("solid white", branch)
        for path in Path("app/components").glob("*.py"):
            self.assertNotIn("9.x/adventurer-neutral/svg", path.read_text())
        self.assertIn(
            "animal_avatar", Path("app/states/discovery_state.py").read_text()
        )
        self.assertIn("shadow-[0_1px_6px", str(inbox_toolbar()))

    def test_fullscreen_and_gating(self):
        panel = inspect.getsource(discover_panel.detail_panel)
        self.assertIn("fixed inset-0", panel)
        self.assertNotIn("max-w-", panel)
        self.assertIn('aria_label="Close details"', panel)
        self.assertEqual(panel.count("detail_body()"), 1)
        self.assertNotIn(
            "detail_body()", inspect.getsource(discover_panel.job_row)
        )
        self.assertIn("selected_poster_requests", panel)
        block = inspect.getsource(advanced_filters.advanced_filters_block)
        self.assertLess(
            block.index("advanced_disclosure_bar()"),
            block.index("MembershipState.is_premium"),
        )
        self.assertIn("DiscoveryState.advanced_expanded", block)
        self.assertIn("advanced_controls()", block)
        self.assertIn("subscribe_shield()", block)
        status = inspect.getsource(ProfileState)
        self.assertNotIn(
            "Your location is hidden. Your saved coordinates", status
        )

    def test_message_validation_remains(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.selected_post = dict(EMPTY_POST)
        for draft, allowed in (
            ("", False),
            ("1234", False),
            ("12345", True),
            ("x" * 2000, True),
            ("x" * 2001, False),
        ):
            state.offer_draft = draft
            self.assertEqual(state.offer_can_send, allowed)
        state.selected_post = {**EMPTY_POST, "allow_price_quote": True}
        state.offer_draft = "I can help tomorrow."
        self.assertFalse(state.offer_can_send)
        self.assertIn("price quote", state.offer_validation)
        source = " ".join(
            inspect.getsource(discover_panel.offer_estimates).split()
        )
        self.assertIn(
            '(DiscoveryState.offer_validation != "") & ( DiscoveryState.offer_validation != "Write a message of 5–2000 characters." )',
            source,
        )
        self.assertIn('role="status"', source)


if __name__ == "__main__":
    unittest.main()
