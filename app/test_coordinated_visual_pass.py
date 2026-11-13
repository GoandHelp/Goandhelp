import reflex as rx

import ast
import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

from app.states.auth_state import AuthState
from app.states.guest_map_state import GuestMapState
from app.components.openfreemap import OpenFreeMap, _MAP_COMPONENT

from app.components import (
    auth_panel,
    guest_map,
    help_hub_panel,
    membership_info,
)
from app.components import messages_panel, policy_screens, verification_notice
from app.components import (
    map_picker,
    unified_inbox,
    event_cards,
    contacts_panel,
)
from app.components.request_heading import request_heading
from app.membership import PREMIUM_BENEFITS, FREE_BENEFITS


class CoordinatedVisualPassTests(unittest.TestCase):
    def test_membership_order_and_benefits(self):
        self.assertEqual(
            PREMIUM_BENEFITS[:2],
            ["Full Access to the Community Forum", "Unlimited help offers"],
        )
        self.assertEqual(
            FREE_BENEFITS[:2],
            ["1 help offer a day", "2 simultaneous help requests"],
        )
        source = inspect.getsource(
            membership_info.membership_information_section
        )
        self.assertLess(
            source.index('"Premium members"'), source.index('"Free members"')
        )
        self.assertIn("bg-[#fba922] hover:bg-[#e08b12]", source)
        self.assertNotIn("from-[#22c55e] to-[#fba922]", source)
        self.assertNotIn("bg-linear-", source)
        self.assertNotIn("bg-gradient-", source)
        self.assertIn('"user-round-check"', source)
        self.assertNotIn('"ticket"', source)
        premium, free = (
            membership_info.membership_information_section()
            .children[1]
            .children
        )
        self.assertIn("UserRoundCheck", str(premium))
        self.assertIn("text-[#fba922]", str(premium.children[0]))
        self.assertIn("User", str(free.children[0]))
        self.assertIn("text-[#22c55e]", str(free.children[0]))

    def test_count_grammar_branches_build(self):
        expected = {
            "Confirmed Help": (
                " upcoming jobs",
                "Confirmed job",
                "Confirmed jobs",
            ),
            "Confirmed Helpers": (
                "Confirmed helpers",
                "Confirmed helper",
                "Confirmed helpers",
            ),
            "Events": ("Events", "Event", "Events"),
            "Hosted events": ("Hosted events", "Hosted event", "Hosted events"),
            "Your help requests": (
                "Help requests",
                "Help request",
                "Help requests",
            ),
            "Saved search alerts": (
                "Search alerts",
                "search alert",
                "search alerts",
            ),
            "Bookmarked help requests": (
                "Bookmarked help requests",
                "Bookmarked help request",
                "Bookmarked help requests",
            ),
            "Offers to help you": (
                "Offers to help you",
                "Offer to help you",
                "Offers to help you",
            ),
            "Requests for your help": (
                "Requests for your help",
                "Request for your help",
                "Requests for your help",
            ),
        }
        source = inspect.getsource(request_heading)
        self.assertNotIn("rx.icon", source)
        self.assertNotIn("absolute right", source)
        for title, labels in expected.items():
            for count, label in zip((0, 1, 2), labels):
                with self.subTest(title=title, count=count):
                    self.assertIn(
                        label, str(request_heading(title, rx.Var.create(count)))
                    )
        self.assertIn('class_name="text-[#e08b12]"', source)

    def test_map_and_loading_contracts(self):
        sheet = Path("app/components/map_utilities.py").read_text()
        self.assertIn("fixed top-0 right-0", sheet)
        self.assertIn("rounded-bl-2xl", sheet)
        picker = inspect.getsource(map_picker.map_picker)
        options = inspect.getsource(map_picker._map_options)
        self.assertIn('picker_key == "help-request"', options)
        self.assertIn('"bottom-left"', options)
        self.assertIn("attribution_visible=False", picker)
        self.assertLess(
            picker.index("open_free_map("),
            picker.index('"Use my current location"'),
        )
        self.assertIn("order-2 mx-auto", picker)
        self.assertIn(
            "attributionControl: attributionVisible ? { compact: true } : false",
            _MAP_COMPONENT,
        )
        self.assertIn(
            'navigation_position: rx.Var[str] = "top-left"',
            inspect.getsource(OpenFreeMap),
        )
        help_map = str(
            map_picker.map_picker("help-request", "Help location", True)
        )
        other_map = str(
            map_picker.map_picker("profile", "Profile location", True)
        )
        self.assertIn("gah-help-request-map", help_map)
        self.assertRegex(
            help_map,
            r'className:\(true \? "gah-help-request-map [^"]*" : "h-64 sm:h-72 w-full"\)',
        )
        # Static rx.cond values retain both branches in serialized JavaScript.
        self.assertRegex(
            other_map,
            r'className:\(false \? "gah-help-request-map [^"]*" : "h-64 sm:h-72 w-full"\)',
        )
        self.assertIn(
            "maplibregl-ctrl-attrib:not([open]):not(.maplibregl-compact-show)",
            help_map,
        )
        self.assertIn("maplibregl-ctrl-attrib-inner]:hidden!", help_map)
        self.assertNotIn("maplibregl-ctrl-attrib-button]:hidden", help_map)
        self.assertIn("bottom-left", help_map)
        self.assertIn(
            'navigationPosition:(true ? "bottom-left" : "top-left")',
            help_map,
        )
        self.assertIn(
            'navigationPosition:(false ? "bottom-left" : "top-left")',
            other_map,
        )
        self.assertIn("top-left", other_map)
        profile_options = map_picker._map_options("profile")
        self.assertRegex(
            str(profile_options["class_name"]),
            r'^\(false \? "gah-help-request-map [^"]*" : "h-64 sm:h-72 w-full"\)$',
        )
        self.assertEqual(
            str(profile_options["navigation_position"]),
            '(false ? "bottom-left" : "top-left")',
        )
        source = Path("app/app.py").read_text()
        for token in (
            "from-[#ffe2bd] to-[#d9e9d4]",
            "h-[100px] w-[100px]",
            "prefers-reduced-motion",
            "duration: 3000",
            'role="status"',
        ):
            self.assertIn(token, source)

    def test_inbox_feedback_and_guest_privacy_controls(self):
        self.assertNotIn(
            "ContactsState.success",
            inspect.getsource(messages_panel.compose_area),
        )
        self.assertIn(
            "success_banner(ContactsState.success, white_text=True)",
            inspect.getsource(messages_panel.job_chat_actions),
        )
        self.assertIn(
            "gap-3 bg-transparent",
            inspect.getsource(unified_inbox.unified_conversation_list),
        )
        source = inspect.getsource(guest_map.guest_utility_button)
        self.assertIn("GuestMapState.open_wall", source)
        self.assertNotIn("NotificationState", source)
        self.assertNotIn(
            "By signing up you agree", inspect.getsource(auth_panel)
        )
        self.assertIn(
            'name="terms_consent"', inspect.getsource(auth_panel.register_form)
        )
        self.assertIn(
            "text-xs", Path("app/components/chat_controls.py").read_text()
        )

    def test_confirmation_popup_orange_controls(self):
        with (
            patch.object(GuestMapState, "wall_open", rx.Var.create(True)),
            patch.object(
                AuthState, "awaiting_verification", rx.Var.create(True)
            ),
        ):
            popup = str(guest_map.sign_up_wall())
        tree = ast.parse(inspect.getsource(guest_map.sign_up_wall))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        badge = next(
            node
            for node in calls
            if ast.unparse(node.func) == "rx.cond"
            and ast.unparse(node.args[0]) == "AuthState.awaiting_verification"
            and any(
                isinstance(value, ast.Constant)
                and value.value == "One step left"
                for value in ast.walk(node.args[1])
            )
        ).args[1]
        close = next(
            node
            for node in calls
            if ast.unparse(node.func) == "rx.el.button"
            and any(
                keyword.arg == "aria_label"
                and ast.literal_eval(keyword.value) == "Close sign-up panel"
                for keyword in node.keywords
            )
        )
        scroll = next(
            keyword.value.args[1]
            for node in calls
            for keyword in node.keywords
            if keyword.arg == "class_name"
            and isinstance(keyword.value, ast.Call)
            and ast.unparse(keyword.value.func) == "rx.cond"
            and isinstance(keyword.value.args[1], ast.Constant)
            and keyword.value.args[1].value.startswith("membership-scroll ")
        )
        active_parts = {
            "badge": ast.unparse(badge),
            "close": ast.unparse(close),
            "scroll": ast.literal_eval(scroll),
            "notice and back control": inspect.getsource(
                verification_notice.verification_notice
            ),
            "resend control": inspect.getsource(
                verification_notice.resend_form
            ),
        }
        for name, source in active_parts.items():
            with self.subTest(component=name):
                self.assertRegex(source, r"#(?:e08b12|b86e08|fba922)")
                for blue in (
                    "#2362ef",
                    "#1a4bc4",
                    "#eef3ff",
                    "#e0ebff",
                    "#d8e2fb",
                    "gah-auth-scroll",
                    "blue-",
                ):
                    self.assertNotIn(blue, source)
        self.assertIn("bg-[#fff7e8]", active_parts["badge"])
        self.assertIn("border-[#e08b12]", active_parts["close"])
        self.assertIn("GuestMapState.close_wall", active_parts["close"])
        self.assertIn("membership-scroll", active_parts["scroll"])
        self.assertIn("bg-[#e08b12]", active_parts["resend control"])
        self.assertIn(
            "AuthState.resend_verification", active_parts["resend control"]
        )
        self.assertIn(
            "AuthState.back_to_sign_in", active_parts["notice and back control"]
        )
        self.assertIn("text-[#e08b12]", active_parts["notice and back control"])
        for token in (
            "Confirm your email",
            "membership-scroll",
            "bg-[#fff7e8]",
            "text-[#b86e08]",
        ):
            self.assertIn(token, popup)

    def test_component_trees_render(self):
        factories = (
            membership_info.membership_information_section,
            help_hub_panel.required_languages_field,
            help_hub_panel.counts_summary,
            messages_panel.compose_area,
            messages_panel.job_chat_actions,
            guest_map.guest_control_stack,
            guest_map.sign_up_wall,
            auth_panel.register_form,
            auth_panel.sign_in_form,
            policy_screens.policy_screen,
            verification_notice.verification_notice,
            event_cards.planner_block,
            contacts_panel.conversation_panel,
        )
        for factory in factories:
            with self.subTest(component=factory.__name__):
                self.assertTrue(str(factory()))

    def test_community_and_profile_refinements(self):
        self.assertIn(
            "flex w-full flex-col items-center justify-center",
            inspect.getsource(event_cards.planner_block),
        )
        self.assertIn(
            "event_distance_km: float = 100.0",
            Path("app/states/event_state.py").read_text(),
        )
        self.assertIn(
            "requested = 100", Path("app/states/event_state.py").read_text()
        )
        self.assertIn(
            "-translate-y-[1px]", Path("app/components/header.py").read_text()
        )
        self.assertNotIn("#2362ef", inspect.getsource(policy_screens))
        self.assertIn(
            "Get notified with matching help requests",
            Path("app/components/saved_items.py").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
