import reflex as rx

import ast
import inspect
import unittest
from types import SimpleNamespace, MethodType
from unittest.mock import AsyncMock

from app.components import discover_panel, help_hub_panel, paywall
from app.states.discovery_state import (
    DiscoveryState,
    EMPTY_HELPER,
    inline_recipient_name,
)
from app.states.help_hub_state import HelpHubState


class OfferFormLayoutTests(unittest.TestCase):
    def test_display_name_only_exact_full_sequence(self):
        for original, expected in [
            ("Test User 2 Test User 2", "Test User 2"),
            ("Mary Jane Mary Jane", "Mary Jane"),
            ("Test User 2", "Test User 2"),
            ("Test User Test Other", "Test User Test Other"),
            ("John John", "John John"),
            ("Mary Ann Ann", "Mary Ann Ann"),
            ("", ""),
            (" Test User ", " Test User "),
        ]:
            with self.subTest(original=original):
                self.assertEqual(inline_recipient_name(original), expected)
        source = inspect.getsource(DiscoveryState)
        self.assertEqual(source.count("= inline_recipient_name("), 2)

    def test_offer_copy_and_flat_detail(self):
        body = inspect.getsource(discover_panel.detail_body)
        self.assertIn('f"Message to {DiscoveryState.thread_with}"', body)
        self.assertNotIn("Conversation #", body)
        self.assertIn(
            "Your offer is waiting for a response",
            str(discover_panel.accept_section()),
        )
        panel = inspect.getsource(discover_panel.detail_panel)
        self.assertIn('class_name="flex flex-col gap-4 w-full"', panel)
        self.assertNotIn("gap-4 w-full rounded-xl bg-white p-3", panel)
        self.assertIn('role="dialog"', panel)
        self.assertEqual(
            str(discover_panel.direct_help_section()).count(
                "Post a help request"
            ),
            1,
        )
        direct_tree = ast.parse(
            inspect.getsource(discover_panel.direct_help_section)
        )
        direct_labels = [
            node.value
            for node in ast.walk(direct_tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        self.assertEqual(direct_labels.count("Post a help request"), 1)
        self.assertNotIn("Ask for Help", direct_labels)

    def test_duration_order_defaults_and_controls(self):
        tree = ast.parse(inspect.getsource(help_hub_panel.duration_field))
        clocks = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and ast.unparse(n.func) == "clock_select"
        ]
        self.assertEqual(
            [ast.literal_eval(n.args[0]) for n in clocks],
            ["duration_hours", "duration_minutes_part"],
        )
        self.assertEqual(
            [ast.literal_eval(n.args[3]) for n in clocks], ["0", "0"]
        )
        source = inspect.getsource(help_hub_panel.duration_field)
        tokens = [
            '"duration_hours"',
            '"Hours"',
            '"duration_minutes_part"',
            '"Minutes"',
            '"For"',
            'name="duration_period_count"',
            "duration_period_select()",
        ]
        positions = [source.index(token) for token in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("flex-nowrap items-start", source)
        self.assertIn("overflow-x-auto", source)
        self.assertIn("disabled=HelpHubState.duration_quote_allowed", source)
        self.assertNotIn("bg-[#fff7e8]", source)
        self.assertNotIn("border border-[#e08b12]", source)
        state_source = inspect.getsource(HelpHubState)
        self.assertIn("range(1, 8)", state_source)
        self.assertIn("duration_period_count: int = 1", state_source)
        self.assertIn('duration_period_unit: str = "day"', state_source)
        self.assertTrue(str(help_hub_panel.duration_field()))

    def test_reward_and_label_layout(self):
        for component in (
            help_hub_panel.help_day_field,
            help_hub_panel.start_time_field,
            help_hub_panel.duration_field,
        ):
            self.assertIn(
                "justify-start text-left", inspect.getsource(component)
            )
        source = inspect.getsource(help_hub_panel.rewards_field)
        self.assertIn("ml-auto text-right", source)
        self.assertLess(
            source.index("conditional_reward_fields()"),
            source.index("money_details_field()"),
        )
        self.assertIn(
            "Other reward details",
            str(help_hub_panel.conditional_reward_fields()),
        )

    def test_paywall_reason_and_checkout_preserved(self):
        source = inspect.getsource(paywall.paywall_modal)
        subtitle_conditions = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.cond"
            and node.args
            and ast.unparse(node.args[0])
            == "MembershipState.upgrade_reason == CATEGORY_UPGRADE_REASON"
        ]
        self.assertEqual(len(subtitle_conditions), 1)
        self.assertEqual(
            [
                ast.literal_eval(branch)
                for branch in subtitle_conditions[0].args[1:]
            ],
            [
                "Unlock multiple categories to your help request and increase your chances of receiving help",
                "Select Monthly or Yearly. Both unlock all benefits",
            ],
        )
        self.assertIn("on_click=MembershipState.start_checkout", source)
        for component in (
            paywall.ticket_to_ride_choice,
            paywall.annual_pass_choice,
        ):
            self.assertIn(
                "Unlock all benefits, cancel anytime", str(component())
            )
            self.assertIn(
                "MembershipState.select_plan", inspect.getsource(component)
            )


class DirectNavigationTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_cta_opens_full_screen_form_without_redirect(self):
        profile = SimpleNamespace(active_tab="discover")
        hub = SimpleNamespace(form_open=False)
        state = SimpleNamespace(
            selected_helper={**EMPTY_HELPER, "id": 7},
            direct_open=True,
            direct_post_id=42,
            direct_draft="Draft",
            is_loading_direct=True,
            get_state=AsyncMock(side_effect=[profile, hub]),
        )
        state._reset_direct_composer = MethodType(
            DiscoveryState._reset_direct_composer, state
        )
        result = await DiscoveryState.go_to_ask_for_help.fn(state)
        self.assertIsNone(result)
        self.assertEqual(profile.active_tab, "help")
        self.assertTrue(hub.form_open)
        self.assertEqual(state.selected_helper, EMPTY_HELPER)
        self.assertFalse(
            state.direct_open
            or state.is_loading_direct
            or state.is_sending_direct
        )
        self.assertEqual(state.direct_post_id, 0)
        self.assertEqual(state.direct_draft, "")
        self.assertEqual(state.direct_requests, [])


if __name__ == "__main__":
    unittest.main()
