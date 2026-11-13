import reflex as rx

import ast
import inspect
import unittest

from app.components import (
    advanced_filters,
    discover_panel,
    event_cards,
    help_hub_panel,
    location_selection,
    map_utilities,
    member_map,
    saved_items,
)
from app.states.notification_state import NotificationState


class FinalChecklistTests(unittest.TestCase):
    def test_three_paper_metric_cards(self):
        summary = help_hub_panel.counts_summary()
        self.assertEqual(len(summary.children), 3)
        self.assertIn("grid-cols-3", str(summary.class_name))
        source = inspect.getsource(help_hub_panel.counts_summary)
        self.assertIn('role="status"', source)
        self.assertIn('aria_label="Your help request totals"', source)
        for card, label in zip(
            summary.children, ("Requested", "Open", "Upcoming"), strict=True
        ):
            classes = str(card.class_name)
            for token in (
                "w-full",
                "rounded-xl",
                "bg-white",
                "text-center",
                "justify-center",
                "text-[#b86e08]",
                "shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
            ):
                self.assertIn(token, classes)
            self.assertIn(label, str(card))
        for token in (
            "rounded-full",
            "bg-[#fff7e8]",
            "w-fit",
            "text-left",
            "text-right",
            "bg-white/",
        ):
            self.assertNotIn(token, source)
        self.assertTrue(summary.render())

    def test_exact_request_copy_and_artwork(self):
        requests_tree = str(help_hub_panel.help_hub_panel().render())
        self.assertNotIn("Completed jobs", requests_tree)
        self.assertNotIn("Past helpers", requests_tree)
        self.assertNotIn(
            "— up to 60, newest first.", inspect.getsource(help_hub_panel)
        )
        requests = inspect.getsource(help_hub_panel.recent_requests_section)
        self.assertNotIn("No help requested yet", requests)
        self.assertIn("rx.fragment()", requests)
        self.assertIn("HelpPostState.recent_posts.length() > 0", requests)
        self.assertIn("HelpPostState.recent_posts", requests)
        self.assertIn("own_request_record", requests)
        self.assertNotIn("No help requests posted yet", requests)
        self.assertNotIn("Fill in Ask for Help above", requests)
        ask_heading = inspect.getsource(help_hub_panel.post_help_section)
        self.assertNotIn(
            "disclosure_arrow(HelpHubState.form_open)", ask_heading
        )
        self.assertIn(
            "aria_expanded=rx.cond(HelpHubState.form_open", ask_heading
        )
        self.assertIn("on_click=HelpHubState.toggle_form", ask_heading)
        self.assertTrue(help_hub_panel.post_help_section().render())

    def test_remaining_requests_sections_hide_empty_states(self):
        sections = (
            (
                help_hub_panel.upcoming_help_section,
                "upcoming_help",
                "No confirmed help today",
            ),
            (
                help_hub_panel.upcoming_helpees_section,
                "confirmed_helpers",
                "No offers to help you",
            ),
            (
                event_cards.others_events_section,
                "joined_events",
                "No confirmed events yet",
            ),
            (
                event_cards.hosted_events_section,
                "hosted_events",
                "You are not hosting an event yet",
            ),
            (
                help_hub_panel.recent_requests_section,
                "recent_posts",
                "No help requested yet",
            ),
            (
                saved_items.saved_searches_section,
                "alerts",
                "No saved searches yet",
            ),
            (
                saved_items.saved_requests_section,
                "saved_requests",
                "No bookmarked help requests yet",
            ),
        )
        for factory, collection, empty_copy in sections:
            with self.subTest(section=factory.__name__):
                source = inspect.getsource(factory)
                self.assertNotIn(empty_copy, source)
                self.assertIn("rx.fragment()", source)
                self.assertIn(f"{collection}.length() > 0", source)
                self.assertIn(collection, source)
                self.assertIn("rx.foreach", source)
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())

    def test_compact_search_card_field_order_and_accessibility(self):
        source = inspect.getsource(discover_panel.filter_drawer)
        self.assertNotIn("centered_search_label", source)
        self.assertNotIn('"Search Everything"', source)
        self.assertNotIn('"Type of Help"', source)
        self.assertNotIn('"Reward"', source)
        order = [
            source.index('name="world_search"'),
            source.index("category_multiselect(compact)"),
            source.index("DiscoveryState.reward_filter_options"),
            source.index("show_my_location_block(compact=compact)"),
            source.index("distance_filter_block(compact=compact)"),
        ]
        self.assertEqual(order, sorted(order))
        for token in (
            'aria_label="Search people, jobs and places"',
            'aria_label="Filter by reward"',
            '"data-tour-target": "filters-label"',
            'class_name="sr-only"',
        ):
            self.assertIn(token, source)
        self.assertIn(
            'aria_label="Show my location"',
            inspect.getsource(location_selection.location_selection),
        )
        self.assertIn(
            'aria_label="Distance in kilometres, zero means any distance"',
            inspect.getsource(discover_panel.distance_filter_block),
        )
        self.assertIn(
            'aria_label="Choose one or more help categories"',
            inspect.getsource(discover_panel.category_multiselect),
        )
        self.assertEqual(source.count("sheet_view_toggle()"), 1)
        self.assertIn(
            "location_selection(compact=True)",
            inspect.getsource(discover_panel.show_my_location_block),
        )
        self.assertIn(
            "location_selection()",
            inspect.getsource(discover_panel.show_my_location_block),
        )
        self.assertNotIn(
            "text-center", inspect.getsource(advanced_filters.small_label)
        )
        self.assertIn(
            "text-center",
            inspect.getsource(discover_panel.distance_filter_block),
        )
        component = discover_panel.filter_drawer("w-full", compact=True)
        self.assertIsInstance(component, rx.Component)
        self.assertTrue(component.render())

    def test_warning_centered_and_accessible(self):
        tree = ast.parse(
            inspect.getsource(discover_panel.show_my_location_block)
        )
        warning = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.el.p"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "Turn on your Approximate location first"
        )
        props = {kw.arg: kw.value for kw in warning.keywords}
        self.assertEqual(ast.literal_eval(props["role"]), "status")
        self.assertEqual(ast.literal_eval(props["aria_live"]), "polite")
        for token in ("w-full", "text-center", "text-[#e08b12]", "opacity-100"):
            self.assertIn(token, ast.literal_eval(props["class_name"]))
        script = ast.unparse(props["on_mount"])
        self.assertIn("prefers-reduced-motion: reduce", script)
        self.assertIn("el.animate", script)
        self.assertIn("distance_reset_token", ast.unparse(props["key"]))

    def test_glass_surfaces_and_geometry(self):
        classes = map_utilities.SHEET_CLASS.split()
        for token in (
            "bg-white/60",
            "backdrop-blur-md",
            "fixed",
            "top-0",
            "right-0",
            "overflow-hidden",
            "flex-col",
            "border-l",
        ):
            self.assertIn(token, classes)
        self.assertNotIn("overflow-y-auto", classes)
        self.assertNotIn("bg-white", classes)
        self.assertNotIn("bg-white/97", classes)
        header = map_utilities.sheet_header(
            "Settings", NotificationState.toggle_map_settings
        )
        notification_header = map_utilities.sheet_header(
            "Notifications", NotificationState.close_panel
        )
        for title, sheet_header in (
            ("Settings", header),
            ("Notifications", notification_header),
        ):
            with self.subTest(header=title):
                header_classes = str(sheet_header.class_name).strip('"').split()
                for token in (
                    "relative",
                    "z-10",
                    "shrink-0",
                    "bg-transparent",
                ):
                    self.assertIn(token, header_classes)
                self.assertNotIn("bg-white", header_classes)
                self.assertNotIn("overflow-y-auto", header_classes)
                self.assertFalse(
                    any("backdrop" in token for token in header_classes)
                )
                self.assertFalse(
                    any(
                        token.startswith("bg-white/")
                        for token in header_classes
                    )
                )
        self.assertIn("LucideBell", str(notification_header.children[0]))

        sheets_tree = ast.parse(
            inspect.getsource(map_utilities.map_utility_sheets)
        )
        sheets = [
            node
            for node in ast.walk(sheets_tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.el.section"
        ]
        self.assertEqual(len(sheets), 2)
        for sheet, title, content in zip(
            sheets,
            ("Settings", "Notifications"),
            ("settings_content", "notification_feed"),
            strict=True,
        ):
            with self.subTest(sheet=title):
                props = {kw.arg: kw.value for kw in sheet.keywords}
                self.assertEqual(
                    ast.unparse(props["class_name"]), "SHEET_CLASS"
                )
                self.assertEqual(ast.literal_eval(props["aria_label"]), title)
                self.assertEqual(len(sheet.args), 2)
                pinned_header, scroll_body = sheet.args
                self.assertEqual(
                    ast.unparse(pinned_header.func), "sheet_header"
                )
                self.assertEqual(ast.literal_eval(pinned_header.args[0]), title)
                self.assertEqual(ast.unparse(scroll_body.func), "rx.el.div")
                body_props = {kw.arg: kw.value for kw in scroll_body.keywords}
                body_classes = ast.literal_eval(
                    body_props["class_name"]
                ).split()
                for token in (
                    "min-h-0",
                    "flex-1",
                    "overflow-y-auto",
                    "overscroll-contain",
                ):
                    self.assertIn(token, body_classes)
                self.assertNotIn("overflow-hidden", body_classes)
                self.assertEqual(ast.unparse(scroll_body.args[0].func), content)
        tree = ast.parse(inspect.getsource(discover_panel.map_panel))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "filter_drawer"
        ]
        self.assertEqual(len(calls), 1)
        for call in calls:
            outer = ast.literal_eval(call.args[0]).split()
            self.assertIn("bg-white/60", outer)
            self.assertIn("backdrop-blur-sm", outer)
            self.assertNotIn("bg-white/97", outer)
            component = discover_panel.filter_drawer(
                ast.literal_eval(call.args[0])
            )
            self.assertIsInstance(component, rx.Component)
            self.assertTrue(component.render())
        member_source = inspect.getsource(member_map.member_filter_sheet)
        self.assertIn("bg-[#f4f7ff]", member_source)
        self.assertIn("max-w-[23.75rem]", member_source)
        self.assertIn(
            "max-h-[calc(100dvh-5rem-env(safe-area-inset-bottom))]",
            member_source,
        )
        self.assertIn("fixed right-2", member_source)
        self.assertIn("backdrop-blur-sm", member_source)
        self.assertIn("compact=True", member_source)
        self.assertTrue(member_map.member_filter_sheet().render())
        self.assertIn("bg-white", advanced_filters.SMALL_INPUT_CLASS.split())
        self.assertIn("bg-white", advanced_filters.SMALL_SELECT_CLASS.split())
        self.assertEqual(
            inspect.getsource(map_utilities.map_utility_sheets).count(
                "class_name=SHEET_CLASS"
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
