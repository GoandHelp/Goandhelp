import reflex as rx

import ast
import inspect
import unittest
from types import SimpleNamespace

from app.components import (
    discover_panel,
    help_hub_panel,
    help_post_panel,
    location_selection,
    map_utilities,
    map_utility_icon,
    member_map,
)
from app.filter_categories import FILTER_CATEGORIES
from app.skill_categories import (
    CATEGORY_CHOICES,
    CATEGORY_GRADIENT,
    category_color,
    category_ink,
)
from app.states.help_hub_state import HelpHubState
from app.app import theme_overrides


class TenUIRefinementsTests(unittest.TestCase):
    def test_cog_has_only_orange_glyph(self):
        cog = map_utility_icon.filled_settings_icon()
        self.assertEqual(len(cog.children), 1)
        source = inspect.getsource(map_utility_icon.filled_settings_icon)
        self.assertIn('fill="#fba922"', source)
        self.assertIn('fill_rule="evenodd"', source)
        self.assertIn("A5.5 5.5 0 1 0 18 23.5", source)
        self.assertIn('view_box="0 0 36 36"', source)
        self.assertNotIn("bg-white", source)
        self.assertNotIn('rx.icon("settings"', source)
        self.assertTrue(cog.render())

    def test_matched_filter_fields_and_centered_header(self):
        source = inspect.getsource(discover_panel.filter_drawer)
        category = inspect.getsource(discover_panel.category_multiselect)
        self.assertGreaterEqual(source.count("gah-filter-field"), 2)
        for text in (source, category):
            self.assertIn("h-9", text)
            self.assertIn("h-10", text)
            self.assertIn("text-sm font-medium text-[#404040]", text)
        self.assertNotIn("style=INDENT_STYLE", category)
        self.assertIn("absolute left-1/2 top-1/2", source)
        self.assertIn(
            "h-[31px]", inspect.getsource(discover_panel.sheet_mode_button)
        )
        self.assertEqual(source.count("sheet_view_toggle()"), 1)
        self.assertIn("event.key !== 'Escape'", source)

    def test_flush_overlays_and_translucency(self):
        source = inspect.getsource(discover_panel.map_panel)
        calls = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "filter_drawer"
        ]
        self.assertEqual(len(calls), 1)
        classes = ast.literal_eval(calls[0].args[0]).split()
        for token in (
            "absolute",
            "bottom-0",
            "right-0",
            "max-h-full",
            "bg-white/60",
            "backdrop-blur-sm",
        ):
            self.assertIn(token, classes)
        member = inspect.getsource(member_map.member_filter_sheet)
        self.assertIn("fixed right-2", member)
        self.assertNotIn("0.75rem", member)
        self.assertIn("bg-[#f4f7ff]", member)
        self.assertIn(
            "max-h-[calc(100dvh-5rem-env(safe-area-inset-bottom))]", member
        )
        self.assertIn("bg-white/60", map_utilities.SHEET_CLASS)
        self.assertIn(".gah-search-drawer", inspect.getsource(theme_overrides))

    def test_natural_width_location_modes(self):
        source = inspect.getsource(location_selection.location_tap)
        self.assertNotIn("truncate", source)
        self.assertIn("whitespace-nowrap", source)
        layout = inspect.getsource(location_selection.location_selection)
        self.assertIn("min-w-fit flex-1", layout)
        self.assertIn("flex-wrap", layout)
        self.assertIn('role="radiogroup"', layout)
        self.assertIn("ProfileState.set_location_mode", source)

    def test_exact_shared_category_colors(self):
        from app.components.onboarding import (
            category_card as onboarding_category_card,
        )

        filters = {item["value"]: item for item in FILTER_CATEGORIES}
        for item in CATEGORY_CHOICES:
            self.assertEqual(item["color"], category_color(item["value"]))
            self.assertEqual(item["ink"], category_ink(item["value"]))
            self.assertEqual(
                (item["color"], item["ink"]),
                (
                    filters[item["value"]]["color"],
                    filters[item["value"]]["ink"],
                ),
            )
            self.assertTrue(
                help_post_panel.category_card(
                    rx.Var.create(item).to(dict[str, str])
                ).render()
            )
        source = inspect.getsource(help_post_panel.category_card)
        onboarding = inspect.getsource(onboarding_category_card)
        self.assertIn('"background": CATEGORY_GRADIENT', source)
        self.assertIn('"size-4 text-white"', source)
        self.assertIn('"background": CATEGORY_GRADIENT', onboarding)
        self.assertIn('item["color"]', onboarding)
        self.assertIn("HelpPostState.set_category", source)

    def test_rewards_dropdown_keeps_multiple_selections_and_money(self):
        state = SimpleNamespace(
            selected_rewards=[],
            rewards_open=False,
            budget_quote_allowed=False,
            error="",
        )
        self.assertEqual(
            HelpHubState.rewards_summary.fget(state), "Choose rewards"
        )
        HelpHubState.toggle_rewards.fn(state)
        HelpHubState.toggle_reward.fn(state, "money")
        HelpHubState.toggle_reward.fn(state, "accommodation")
        self.assertTrue(state.rewards_open)
        self.assertEqual(
            HelpHubState.rewards_summary.fget(state), "Money, Accommodation"
        )
        HelpHubState.toggle_reward.fn(state, "guided_tour")
        self.assertEqual(
            HelpHubState.rewards_summary.fget(state), "3 rewards selected"
        )
        HelpHubState.close_rewards.fn(state)
        self.assertEqual(len(state.selected_rewards), 3)
        self.assertFalse(state.rewards_open)
        source = inspect.getsource(help_hub_panel.rewards_field)
        for token in (
            "aria_expanded=HelpHubState.rewards_open",
            'aria_controls="help-reward-options"',
            'id="help-reward-options"',
            "rx.foreach(HelpHubState.reward_choices, reward_checkbox)",
            "conditional_reward_fields()",
            "money_details_field()",
        ):
            self.assertIn(token, source)
        self.assertTrue(help_hub_panel.rewards_field().render())

    def test_ask_form_and_request_order(self):
        self.assertNotIn(
            "required_languages_field()",
            inspect.getsource(help_hub_panel.post_help_form),
        )
        self.assertEqual(
            HelpHubState(_reflex_internal_init=True).required_languages, []
        )
        trigger = inspect.getsource(help_hub_panel.post_help_section)
        self.assertNotIn("green_icon_tile", trigger)
        self.assertIn("bg-[#fba922]", trigger)
        self.assertIn("min-h-24 w-full", trigger)
        self.assertIn("aria_expanded", trigger)
        source = inspect.getsource(help_hub_panel.help_hub_panel)
        self.assertIn(
            "help_summary_row(),\n        recent_requests_section(),\n        upcoming_help_section(),",
            source,
        )
        self.assertEqual(source.count("recent_requests_section()"), 1)
        self.assertTrue(help_hub_panel.post_help_form().render())


if __name__ == "__main__":
    unittest.main()
