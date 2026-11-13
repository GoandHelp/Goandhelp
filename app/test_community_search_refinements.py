import reflex as rx

import ast
import inspect
import unittest

from app.components import (
    advanced_filters,
    community_panel,
    discover_panel,
    event_cards,
    messages_panel,
    reviews_section,
)


class CommunitySearchRefinementTests(unittest.TestCase):
    def test_distance_endpoint_row_and_accessibility(self):
        block = discover_panel.distance_filter_block()
        row, slider = block.children
        for token in ("flex", "whitespace-nowrap", "gap-1"):
            self.assertIn(token, str(row.class_name).split())
        self.assertEqual(
            [child.tag for child in row.children], ["span", "label", "span"]
        )
        self.assertIn("1 km", str(row.children[0]))
        self.assertIn("Distance", str(row.children[1]))
        self.assertIn("Any", str(row.children[2]))
        for child, alignment in zip(
            row.children,
            ("text-left", "text-center", "text-right"),
            strict=True,
        ):
            self.assertIn(alignment, str(child.class_name))
        self.assertIn("gah-discover-distance", str(row.children[1]))
        self.assertIn("aria-valuetext", str(slider))
        source = inspect.getsource(discover_panel.distance_filter_block)
        for token in (
            "aria_valuetext=DiscoveryState.distance_label",
            "min=DiscoveryState.distance_min_km",
            "max=DiscoveryState.distance_max_km",
            "step=DiscoveryState.distance_step_km",
            "set_distance_filter.throttle(100)",
            "commit_distance_filter.debounce(150)",
        ):
            self.assertIn(token, source)
        self.assertTrue(block.render())

    def test_tab_surfaces_geometry_and_events(self):
        active = community_panel.FOLDER_TAB_ACTIVE
        inactive = community_panel.FOLDER_TAB_INACTIVE
        self.assertIn("bg-white", active)
        self.assertIn("border border-[#fba922]", active)
        self.assertIn("py-[5px]", active)
        self.assertIn("py-[5px]", inactive)
        self.assertIn("hover:border-[#fba922]", inactive)
        self.assertIn("py-2", community_panel.FOLDER_ROW_WRAP)
        self.assertNotIn("-mt-", community_panel.FOLDER_ROW_WRAP)
        for classes in (active, inactive):
            self.assertNotIn("bg-[#fba922]", classes)
            self.assertNotIn("border-[#2362ef]", classes)
            self.assertIn("flex-1 basis-0", classes)
            self.assertIn("lg:w-36", classes)
            self.assertIn("focus-visible:ring", classes)
        source = inspect.getsource(community_panel.folder_tab)
        self.assertIn("corner_activity_dot", source)
        self.assertIn("CommunityState.set_section", source)

    def test_compact_planner_and_membership_handlers(self):
        source = inspect.getsource(event_cards.planner_control)
        self.assertIn('"Plan an event"', source)
        self.assertNotIn('"Go premium"', source)
        self.assertIn("EventState.toggle_composer", source)
        self.assertNotIn("EventState.open_events_paywall", source)
        self.assertNotIn("MembershipState.is_premium", source)
        self.assertIn("gah-primary-outline", source)
        self.assertIn("bg-white", source)
        block = inspect.getsource(event_cards.planner_block)
        self.assertIn("Plan and join events for free", block)
        self.assertIn("event_planner_screen()", block)
        self.assertNotIn("gah-main-card", block)

    def test_clear_button_is_unconditional_and_disabled(self):
        source = inspect.getsource(discover_panel.filter_drawer)
        tree = ast.parse(source)
        parents = {
            child: node
            for node in ast.walk(tree)
            for child in ast.iter_child_nodes(node)
        }
        for label in ("Clear filters", "Save search"):
            literal = next(
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and node.value == label
            )
            button = parents[literal]
            self.assertEqual(ast.unparse(button.func), "rx.el.button")
            keywords = {kw.arg: kw.value for kw in button.keywords}
            self.assertIn(
                "rounded-lg", ast.literal_eval(keywords["class_name"])
            )
            self.assertIn(
                "text-[#6b7280]", ast.literal_eval(keywords["class_name"])
            )
            if label == "Clear filters":
                self.assertEqual(
                    ast.unparse(keywords["disabled"]),
                    "~(DiscoveryState.filters_active | DiscoveryState.distance_warning)",
                )
            ancestor = parents.get(button)
            while ancestor is not None:
                if isinstance(ancestor, ast.Call):
                    self.assertNotEqual(ast.unparse(ancestor.func), "rx.cond")
                ancestor = parents.get(ancestor)

    def test_search_spacing_and_advanced_focus(self):
        source = inspect.getsource(discover_panel.filter_drawer)
        self.assertIn("mt-2 grid grid-cols-1 gap-2.5", source)
        self.assertIn("-mt-[6px]", source)
        self.assertIn("focus-within:border-[#fba922]", source)
        self.assertIn("border-0 bg-transparent", source)
        self.assertIn(
            "-translate-y-1 h-10",
            inspect.getsource(discover_panel.distance_filter_block),
        )
        advanced = inspect.getsource(advanced_filters.advanced_disclosure_bar)
        self.assertIn("border-[#dce5f5]", advanced)
        self.assertIn("focus-visible:ring-[#e08b12]", advanced)

    def test_review_composition_preserves_real_data(self):
        source = inspect.getsource(reviews_section.community_reviews_section)
        self.assertLess(
            source.index("your_reviews_header()"),
            source.index("review_section()"),
        )
        self.assertLess(
            source.index("review_section()"),
            source.index("received_reviews_section()"),
        )
        self.assertIn("bg-[#ffffff]", source)
        self.assertIn(
            "ProfileState.combined_star_states",
            inspect.getsource(reviews_section.your_reviews_header),
        )
        self.assertIn(
            "disclosure_arrow(True",
            inspect.getsource(messages_panel.review_target_identity),
        )

    def test_component_compilation(self):
        components = (
            community_panel.community_header(),
            community_panel.community_panel(),
            event_cards.planner_control(),
            event_cards.planner_block(),
            event_cards.events_section(),
            discover_panel.filter_drawer("w-full"),
            advanced_filters.advanced_filters_block(),
            reviews_section.community_reviews_section(),
        )
        for component in components:
            with self.subTest(component=type(component).__name__):
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
