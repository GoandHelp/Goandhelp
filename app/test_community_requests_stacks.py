import reflex as rx

import ast
import inspect
import unittest

from app.app import theme_overrides
from app.components import community_panel, event_cards, help_hub_panel
from app.components import (
    disclosure,
    messages_panel,
    reviews_section,
    saved_items,
)


class CommunityRequestsStackTests(unittest.TestCase):
    def test_all_named_lists(self):
        factories = (
            community_panel.topic_feed,
            event_cards.events_feed,
            event_cards.host_queue_block,
            reviews_section.received_reviews_section,
            messages_panel.review_section,
            help_hub_panel.upcoming_help_section,
            help_hub_panel.upcoming_helpees_section,
            event_cards.others_events_section,
            event_cards.hosted_events_section,
            help_hub_panel.recent_requests_section,
            saved_items.saved_searches_section,
            saved_items.saved_requests_section,
        )
        for factory in factories:
            with self.subTest(section=factory.__name__):
                source = inspect.getsource(factory)
                self.assertIn("gah-edge-stack", source)
                self.assertIn("gap-0", source)
                self.assertNotIn("gah-main-card", source)
                self.assertNotIn("class_name=SHELL", source)
                self.assertNotIn(".reverse()", source)
                self.assertNotIn("sorted(", source)
        for shell in (
            event_cards._help_shell,
            help_hub_panel.inbox_style_shell,
        ):
            source = inspect.getsource(shell)
            self.assertNotIn("gah-main-card", source)
            self.assertNotIn("rounded", source)
            self.assertIn("w-full bg-transparent", source)
        self.assertIn(
            "rx.foreach(CommunityState.topics, topic_card)",
            inspect.getsource(community_panel.topic_feed),
        )
        self.assertIn(
            "section_shell(",
            inspect.getsource(help_hub_panel.post_help_section),
        )

    def test_records_and_direct_only_geometry(self):
        for factory in (
            community_panel.topic_card,
            event_cards.event_card,
            event_cards.pending_request_card,
            messages_panel.pending_review_card,
            reviews_section.received_review_card,
            saved_items.alert_card,
        ):
            source = inspect.getsource(factory)
            self.assertIn("rounded-none border-0", source)
        css = inspect.getsource(theme_overrides)
        self.assertIn(":not(.gah-edge-stack > *)", css)
        self.assertIn("> :is(article,li,button,details,section,div)", css)
        self.assertIn("border-top: 1px solid #e5e7eb", css)
        self.assertIn("border-radius: 0 !important", css)
        self.assertIn(":first-child", css)
        self.assertIn(":last-child", css)
        self.assertIn("> details > summary", css)
        self.assertIn("box-shadow: none !important", css)
        for factory in (
            help_hub_panel.upcoming_help_card,
            help_hub_panel.confirmed_helper_record,
            help_hub_panel.own_request_record,
            event_cards.others_event_record,
            event_cards.hosted_event_block,
            saved_items.saved_request_card,
        ):
            self.assertIn("record_disclosure(", inspect.getsource(factory))
        self.assertIn(
            "rx.el.details(", inspect.getsource(disclosure.record_disclosure)
        )
        self.assertIn(
            "saved_request_note_form(request)",
            inspect.getsource(saved_items.saved_request_body),
        )
        self.assertIn(
            'alert["chips"]', inspect.getsource(saved_items.alert_card)
        )

    def test_empty_surfaces_and_review_outer_shell(self):
        for factory in (event_cards.events_empty,):
            source = inspect.getsource(factory)
            self.assertIn("gah-edge-stack", source)
            self.assertIn("w-full", source)
            self.assertIn("bg-white", source)
        outer = reviews_section.community_reviews_section()
        self.assertNotIn("rounded", str(outer.class_name))
        outer_classes = str(outer.class_name).split()
        self.assertNotIn("p-4", outer_classes)
        self.assertNotIn("sm:p-6", outer_classes)
        self.assertIn("bg-[#ffffff]", outer_classes)
        self.assertIn(
            "No discussions pinned yet",
            inspect.getsource(community_panel.topic_feed),
        )
        self.assertIn(
            "Your first review is still waiting",
            inspect.getsource(reviews_section.received_reviews_section),
        )

    def test_orange_accents_and_handlers(self):
        planner = inspect.getsource(event_cards.planner_control)
        for token in (
            "text-[#fba922]",
            "text-black",
            "bg-white",
            "border-[#fba922]",
            '"Plan an event"',
            "EventState.toggle_composer",
            "aria_expanded=EventState.composer_open",
        ):
            self.assertIn(token, planner)
        stars = inspect.getsource(reviews_section.review_rating_star)
        self.assertNotIn("#2362ef", stars)
        self.assertIn("stroke-[#fba922]", stars)
        self.assertIn("fill-[#fba922]", stars)
        for factory in (
            reviews_section.your_reviews_header,
            reviews_section.received_review_card,
        ):
            tree = ast.parse(inspect.getsource(factory))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and ast.unparse(node.func) == "rx.icon"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value == "star"
                ):
                    self.assertIn("text-[#fba922]", ast.unparse(node))
        header = inspect.getsource(reviews_section.your_reviews_header)
        self.assertIn("ProfileState.combined_star_states", header)
        header_tree = ast.parse(header)
        rating_uses = [
            node
            for node in ast.walk(header_tree)
            if isinstance(node, ast.Attribute)
            and ast.unparse(node) == "ProfileState.combined_rating_label"
        ]
        accessibility_uses = [
            keyword
            for node in ast.walk(header_tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.el.div"
            and any(
                keyword.arg == "role"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "img"
                for keyword in node.keywords
            )
            for keyword in node.keywords
            if keyword.arg in ("title", "aria_label")
            and ast.unparse(keyword.value)
            == "ProfileState.combined_rating_label"
        ]
        self.assertEqual(len(rating_uses), 2)
        self.assertCountEqual(
            [keyword.arg for keyword in accessibility_uses],
            ["title", "aria_label"],
        )
        self.assertNotIn(
            'class_name="text-[11px] font-bold text-black"', header
        )
        metric = inspect.getsource(help_hub_panel.help_summary_card)
        self.assertNotIn("bg-[#fff7e8]", metric)
        self.assertIn("rounded-xl", metric)
        self.assertIn("shadow-", metric)
        self.assertIn("text-[#e08b12]", metric)
        for wording in (
            " help given",
            " help received",
            "Helped",
            "Received help",
            "time",
            "times",
        ):
            self.assertIn(wording, metric)
        self.assertIn("text-base sm:text-lg", metric)
        summary_row = inspect.getsource(help_hub_panel.help_summary_row)
        self.assertIn("grid-cols-2", summary_row)
        self.assertIn("gap-x-6", summary_row)
        self.assertIn("sm:gap-x-12", summary_row)
        self.assertNotIn("border-[#e08b12]", summary_row)
        self.assertIn("bg-transparent", summary_row)
        self.assertIn("bg-white", metric)
        self.assertNotIn("grid-cols-1", summary_row)

    def test_component_compilation(self):
        for factory in (
            community_panel.community_section,
            event_cards.events_section,
            reviews_section.community_reviews_section,
            help_hub_panel.help_hub_panel,
        ):
            with self.subTest(component=factory.__name__):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
