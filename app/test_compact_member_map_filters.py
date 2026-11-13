import inspect
import unittest

import reflex as rx

from app.components import (
    advanced_filters,
    discover_panel,
    map_utility_icon,
    member_map,
)


class CompactMemberMapFilterTests(unittest.TestCase):
    def test_compact_sheet_layout_keeps_existing_search_actions(self):
        sheet = inspect.getsource(member_map.member_filter_sheet)
        drawer = inspect.getsource(discover_panel.filter_drawer)
        for token in (
            "fixed right-2",
            "bottom-[calc(3.875rem+env(safe-area-inset-bottom))]",
            "w-[calc(100vw-1rem)]",
            "max-w-[23.75rem]",
            "overflow-y-auto overscroll-contain",
            "bg-[#f4f7ff]",
            "compact=True",
        ):
            self.assertIn(token, sheet)
        for token in (
            'sheet_mode_button(\n                            "Go"',
            "sheet_view_toggle()",
            'aria_label="Close Search filters"',
            'name="world_search"',
            "category_multiselect(compact)",
            "DiscoveryState.reward_filter_options",
            "show_my_location_block(compact=compact)",
            "distance_filter_block(compact=compact)",
            "SavedSearchState.save_current_search",
            "DiscoveryState.clear_filters",
            "WorldSearchState.submit",
            "results_panel()",
        ):
            self.assertIn(token, drawer)
        self.assertLess(
            drawer.index('"Go"'), drawer.index("sheet_view_toggle()")
        )
        self.assertLess(
            drawer.index("sheet_view_toggle()"),
            drawer.index('aria_label="Close Search filters"'),
        )
        self.assertTrue(member_map.member_filter_sheet().render())

    def test_advanced_filters_are_secondary_without_changing_access(self):
        source = inspect.getsource(advanced_filters.advanced_filters_block)
        self.assertLess(
            source.index("advanced_disclosure_bar()"),
            source.index("advanced_controls()"),
        )
        self.assertIn("DiscoveryState.advanced_expanded", source)
        self.assertIn("MembershipState.is_premium", source)
        self.assertIn("subscribe_shield()", source)
        self.assertTrue(advanced_filters.advanced_filters_block().render())

    def test_map_utility_glyphs_and_unread_indicator(self):
        bell = inspect.getsource(map_utility_icon.filled_bell_icon)
        cog = inspect.getsource(map_utility_icon.filled_settings_icon)
        controls = inspect.getsource(member_map.member_control_stack)
        self.assertIn('fill="#fba922"', bell)
        self.assertIn('fill="#fba922"', cog)
        self.assertIn("size-[36px]", bell)
        self.assertIn("size-[36px]", cog)
        self.assertIn("C13.5 29 13.6 29.8 13.9 30.5", bell)
        self.assertIn('fill_rule="evenodd"', cog)
        self.assertIn("A5.5 5.5 0 1 0 18 23.5", cog)
        for tooth_profile in (
            "M15 2 H21",
            "L28.1 4.9 L31.1 7.9",
            "L34 15 V21",
            "L31.1 28.1",
            "L21 34",
            "L4.9 28.1",
            "L2 21 V15",
            "L4.9 7.9",
        ):
            self.assertIn(tooth_profile, cog)
        self.assertNotIn("bg-white", cog)
        self.assertNotIn('rx.icon("bell"', bell)
        self.assertNotIn('rx.icon("settings"', cog)
        self.assertIn("NotificationState.total_unread > 0", controls)
        self.assertIn("right-[7px] top-[6px] size-2", controls)
        self.assertTrue(map_utility_icon.map_utility_icon("bell").render())
        self.assertTrue(map_utility_icon.map_utility_icon("cog").render())


if __name__ == "__main__":
    unittest.main()
