import reflex as rx

import ast
import inspect
import unittest

from app.components import community_panel, event_cards, reviews_section
from app.components import messages_panel, unified_inbox, chat_controls, header
from app.components import contacts_panel, noncontact_panel
from app.states.messaging_state import MessagingState


class CommunityNoticeboardPolishTests(unittest.TestCase):
    def test_tabs_and_forum(self):
        self.assertIn(
            "border border-[#fba922]", community_panel.FOLDER_TAB_ACTIVE
        )
        self.assertNotIn("border-[3px]", community_panel.FOLDER_TAB_ACTIVE)
        feed = str(community_panel.topic_feed())
        self.assertIn("text-[#fba922]", feed)
        self.assertIn("No discussions pinned yet", feed)
        source = inspect.getsource(community_panel.community_section)
        self.assertIn("1 topic per month", source)
        self.assertIn("10 comments per month", source)
        self.assertIn("CommunityState.topic_allowance_available", source)
        self.assertIn("gah-orange-control", source)
        self.assertIn("CommunityState.toggle_composer", source)
        self.assertIn("CommunityState.toggle_composer", source)
        self.assertIn('"Monthly limit"', source)

    def test_open_topic_hierarchy_accessibility_badges_and_safety_actions(self):
        source = inspect.getsource(community_panel.topic_detail)
        title_position = source.index("rx.el.h2(")
        close_position = source.index('aria_label="Close discussion"')
        metadata_position = source.index(
            'class_name="mt-3 flex w-full flex-wrap items-center gap-2"'
        )
        body_position = source.index('CommunityState.selected_topic["body"]')
        composer_position = source.index("comment_composer()")
        owner_guard_position = source.index(
            'CommunityState.selected_topic["mine"]', composer_position
        )
        report_position = source.index('"Report discussion"')
        block_position = source.index('"Block member"')

        self.assertLess(title_position, close_position)
        self.assertLess(close_position, metadata_position)
        self.assertLess(metadata_position, body_position)
        self.assertLess(composer_position, owner_guard_position)
        self.assertLess(owner_guard_position, report_position)
        self.assertLess(report_position, block_position)
        for token in (
            'CommunityState.selected_topic["title"]',
            'title="Close discussion"',
            "on_click=CommunityState.close_topic",
            'class_name="flex size-11 shrink-0 items-center justify-center',
            "inline-flex min-h-7 shrink-0 items-center gap-1.5 whitespace-nowrap",
            "inline-flex min-h-7 shrink-0 items-center whitespace-nowrap",
            'class_name="mt-5 flex w-full flex-wrap items-center gap-2 border-t',
            'CommunityState.selected_topic["mine"],\n            rx.fragment(),',
            "REPORT_TARGET_COMMUNITY_TOPIC",
            'CommunityState.selected_topic["author_id"]',
        ):
            self.assertIn(token, source)
        self.assertTrue(community_panel.topic_detail().render())

    def test_centered_headings_and_event_order(self):
        for factory in (community_panel.topic_feed, event_cards.events_feed):
            heading = str(factory().children[0])
            self.assertIn("w-full text-center text-xl sm:text-2xl", heading)
            self.assertIn("absolute right-0 top-1/2", heading)
            self.assertNotIn("absolute left-0 h-4 w-4 text-[#fba922]", heading)
            self.assertIn("Refresh", heading)
        feed = event_cards.events_feed()
        self.assertIn("Select your dates", str(feed.children[1]))
        self.assertIn("Event distance", str(feed.children[2]))
        self.assertIn("text-xl font-bold leading-tight", str(feed.children[2]))
        self.assertIn("bg-[#fff7e8]", str(feed.children[2]))
        self.assertIn("border-[#e08b12]", str(feed.children[2]))
        self.assertIn("No events on the board yet", str(feed.children[3]))
        planner = str(event_cards.planner_control())
        for token in (
            "text-[#fba922]",
            "border border-[#fba922]",
            "bg-white",
            "toggle_composer",
            "Plan an event",
        ):
            self.assertIn(token, planner)

    def test_review_presentation(self):
        heading = str(reviews_section.your_reviews_header())
        self.assertIn("text-xl sm:text-2xl font-bold", heading)
        self.assertNotIn("text-base sm:text-lg", heading)
        self.assertIn(
            "pt-3", str(reviews_section.community_reviews_section().class_name)
        )
        identity = inspect.getsource(messages_panel.review_target_identity)
        for token in (
            "other_rating",
            "other_rating_count",
            "rating_values",
            "fill-none",
            "aria_label",
            "Unrated · 0 reviews",
        ):
            self.assertIn(token, identity)
        self.assertNotIn("New member", identity)
        identity_block = messages_panel.review_target_identity().children[1]
        self.assertEqual(len(identity_block.children), 3)
        name_rating_row, handle, title = identity_block.children
        self.assertIn(
            "flex flex-wrap items-center", str(name_rating_row.class_name)
        )
        self.assertNotIn("flex-col", str(name_rating_row.class_name))
        self.assertEqual(len(name_rating_row.children), 2)
        name, stars = name_rating_row.children
        self.assertIn("other_name", str(name))
        self.assertIn("rating_values", str(stars))
        self.assertIn("other_rating_count", str(stars))
        self.assertIn('role:"img"', str(stars))
        self.assertNotIn("mt-1", str(stars.class_name))
        self.assertIn("other_handle", str(handle))
        self.assertIn("post_title", str(title))
        pending = inspect.getsource(messages_panel.pending_review_card)
        self.assertIn('target["my_role"] == "poster"', pending)
        self.assertIn('"Helped you"', pending)
        self.assertIn('"Received your help"', pending)
        form = inspect.getsource(messages_panel.review_form)
        self.assertEqual(form.count("Score all four categories"), 1)
        self.assertNotIn("All four scores are required", form)
        self.assertNotIn("MessagingState.review_title", form)
        for token in (
            "I.e. Turned up",
            "bg-[#fff7e8]",
            "text-[#b86e08]",
            "border border-[#b86e08]",
            "MessagingState.is_reviewing | ~MessagingState.review_ready",
            "MessagingState.submit_review",
        ):
            self.assertIn(token, form)
        received = inspect.getsource(reviews_section.received_reviews_section)
        self.assertIn('"heart-handshake"', received)
        self.assertIn('class_name="h-6 w-6 text-[#fba922] mb-2"', received)

    def test_inbox_and_shared_alignment(self):
        tree = ast.parse(inspect.getsource(header.page_title_icon))
        match_call = tree.body[0].body[1].value
        branches = {
            branch.elts[0].value: branch.elts[1]
            for branch in match_call.args
            if isinstance(branch, ast.Tuple)
        }
        expected = {
            "profile": "circle-user-round",
            "help": "heart-handshake",
            "upcoming": "heart-handshake",
            "get_help": "heart-handshake",
            "inbox": "mail",
        }
        self.assertEqual(set(branches), {*expected, "community"})
        for tab, glyph in expected.items():
            with self.subTest(tab=tab):
                icon = branches[tab]
                self.assertEqual(ast.literal_eval(icon.args[0]), glyph)
                classes = next(
                    k.value for k in icon.keywords if k.arg == "class_name"
                )
                if tab == "profile":
                    self.assertEqual(classes.id, "PAGE_TITLE_ICON_CLASS")
                else:
                    self.assertIn(
                        "-translate-y-[2px]"
                        if tab == "inbox"
                        else "-translate-y-[1px]",
                        ast.literal_eval(classes),
                    )
        community = branches["community"]
        self.assertEqual(ast.literal_eval(community.args[0]), "users-round")
        classes = next(
            k.value for k in community.keywords if k.arg == "class_name"
        )
        self.assertIsInstance(classes, ast.Name)
        self.assertEqual(classes.id, "PAGE_TITLE_ICON_CLASS")
        self.assertEqual(
            header.PAGE_TITLE_ICON_CLASS,
            "h-5 w-5 shrink-0 text-[#111827]",
        )
        toolbar = inspect.getsource(unified_inbox.inbox_toolbar)
        self.assertIn("h-4 w-4 text-[#fba922]", toolbar)
        self.assertIn("flex w-full min-w-0 items-center gap-2", toolbar)
        self.assertNotIn("grid-cols-3", toolbar)
        self.assertIn("w-full", toolbar)
        self.assertIn('aria_label="Filter conversations by type"', toolbar)
        filters = inspect.getsource(unified_inbox.filter_chip)
        self.assertIn("flex-1", filters)
        self.assertIn("min-w-0", filters)
        self.assertIn("flex-col", filters)
        self.assertIn("items-center", filters)
        self.assertIn('class_name="size-6 text-[#e08b12]"', filters)
        filter_button = ast.parse(filters).body[0].body[0].value
        filter_classes = next(
            keyword.value
            for keyword in filter_button.keywords
            if keyword.arg == "class_name"
        )
        self.assertEqual(ast.unparse(filter_classes.func), "rx.cond")
        self.assertEqual(
            ast.unparse(filter_classes.args[0]),
            "UnifiedInboxState.type_filter == option['value']",
        )
        selected_classes = ast.literal_eval(filter_classes.args[1]).split()
        unselected_classes = ast.literal_eval(filter_classes.args[2]).split()
        for classes in (selected_classes, unselected_classes):
            self.assertIn("flex-1", classes)
            self.assertIn("min-w-0", classes)
            self.assertIn("flex-col", classes)
            self.assertIn("items-center", classes)
        self.assertIn("bg-[#fff7e8]", selected_classes)
        self.assertIn("bg-white", unselected_classes)
        self.assertIn("UnifiedInboxState.set_type_filter", filters)
        bubble = inspect.getsource(chat_controls.correspondence_bubble)
        self.assertIn("flex flex-col items-end w-full min-w-0", bubble)
        self.assertIn("mt-1 max-w-full", bubble)
        self.assertIn("text-right text-xs", bubble)
        self.assertNotIn("flex-row", bubble)
        self.assertIn("flex flex-col items-start", bubble)
        self.assertIn('msg["mine"] | (target == "")', bubble)
        self.assertGreater(
            bubble.index('msg["sent_at"]'), bubble.index("rounded-br-sm")
        )

    def test_compile_all_community_and_conversation_trees(self):
        factories = (
            community_panel.community_panel,
            community_panel.community_section,
            event_cards.events_section,
            reviews_section.community_reviews_section,
            messages_panel.review_target_identity,
            messages_panel.review_form,
            messages_panel.review_section,
            unified_inbox.inbox_toolbar,
            lambda: unified_inbox.unified_conversation_list(
                messages_panel.reading_pane()
            ),
            lambda: rx.el.div(
                rx.foreach(
                    MessagingState.review_targets,
                    messages_panel.pending_review_card,
                )
            ),
            messages_panel.job_conversation_panel,
            contacts_panel.conversation_panel,
            noncontact_panel.noncontact_conversation_view,
        )
        for factory in factories:
            with self.subTest(factory=factory):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
