import reflex as rx

import ast
import inspect
from pathlib import Path
import unittest

from app.app import index, theme_overrides
from app.components import (
    chat_controls,
    contacts_panel,
    messages_panel,
    noncontact_panel,
    unified_inbox,
)
from app.components.chat_safety import chat_safety
from app.components.block_dialog import BLOCK_BUTTON_CLASS
from app.components.report_dialog import REPORT_BUTTON_CLASS


class InboxChatRefinementTests(unittest.TestCase):
    def test_bubble_geometry_and_history(self):
        source = inspect.getsource(chat_controls._correspondence_bubble)
        self.assertNotIn("rx.el.details", source)
        self.assertNotIn("Show original", source)
        self.assertEqual(source.count("rx.el.p("), 1)
        for token in (
            "w-fit max-w-[85%]",
            "mt-1 max-w-full",
            "flex-col items-end",
            "report_button",
            'msg["sent_at"]',
        ):
            self.assertIn(token, source)
        for factory in (
            messages_panel.message_history,
            contacts_panel.message_history,
            noncontact_panel.thread_history,
        ):
            self.assertIn("gap-1 w-full min-w-0", inspect.getsource(factory))

    def test_confirmation_and_actions(self):
        source = inspect.getsource(messages_panel.job_conversation_panel)
        self.assertIn(
            "You have confirmed. Awaiting confirmation from {MessagingState.selected_thread['other_name']}.",
            source,
        )
        self.assertIn(
            "You have confirmed. {MessagingState.selected_thread['other_name']} has confirmed.",
            source,
        )
        self.assertIn(
            "w-full text-center text-sm font-medium leading-relaxed", source
        )
        self.assertIn("Help not yet confirmed", source)
        self.assertEqual(BLOCK_BUTTON_CLASS, REPORT_BUTTON_CLASS)
        safety = inspect.getsource(chat_safety)
        for token in (
            '"Add contact"',
            "text-[#e08b12]",
            "px-3 py-1.5 text-xs font-semibold",
            "on_click=ContactsState.send_request",
        ):
            self.assertIn(token, safety)
        actions = ast.parse(inspect.getsource(messages_panel.job_chat_actions))
        safety_calls = [
            node
            for node in ast.walk(actions)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "chat_safety"
        ]
        self.assertEqual(len(safety_calls), 1)
        self.assertIn(
            "text-[#fba922]", inspect.getsource(messages_panel.completion_card)
        )
        css = inspect.getsource(theme_overrides)
        self.assertIn("0 0 10px rgba(17,24,39,.12)", css)

    def test_fallbacks(self):
        root = Path(__file__).parent
        for folder in ("components", "states"):
            for path in (root / folder).glob("*.py"):
                source = path.read_text()
                self.assertNotIn("/notionists/svg", source, path.name)
                self.assertNotIn("api.dicebear.com", source, path.name)
        self.assertIn(
            "animal_avatar",
            (root / "states" / "discovery_state.py").read_text(),
        )

    def test_stack_scope(self):
        css = inspect.getsource(theme_overrides)
        for token in (
            ".gah-edge-stack > :is(article,li,button,details,section,div)",
            ":first-child",
            ":last-child",
            "border-top: 1px solid #e5e7eb",
            ".gah-edge-stack { gap: 0;",
            ":first-child { border-top-left-radius: 14px !important; border-top-right-radius: 14px !important; }",
            ":last-child { border-bottom-left-radius: 14px !important; border-bottom-right-radius: 14px !important; }",
            "box-shadow: var(--gah-surface-shadow);",
        ):
            self.assertIn(token, css)
        for factory in (
            messages_panel.compose_area,
            messages_panel.offers_block,
            messages_panel.helpee_requests_block,
        ):
            self.assertNotIn("gah-main-card", inspect.getsource(factory))
        for factory in (
            messages_panel.offers_block,
            messages_panel.helpee_requests_block,
        ):
            self.assertIn(
                "gah-edge-stack flex flex-col gap-0", inspect.getsource(factory)
            )

    def test_inline_helper_and_unframed_rows(self):
        label = unified_inbox.HELPER_BADGE.split()
        self.assertIn("text-xs", label)
        self.assertIn("inline-flex", label)
        for token in label:
            self.assertFalse(
                token.startswith(("border", "rounded", "bg-", "px-", "py-"))
            )
        badge = inspect.getsource(unified_inbox.type_badge)
        for token in (
            '"hand"',
            '"hand-helping"',
            '"users-round"',
            "aria_label",
            "type_label",
        ):
            self.assertIn(token, badge)
        row = inspect.getsource(unified_inbox.conversation_card)
        for token in (
            "corner_activity_dot",
            "avatar_with_tick",
            'item["other_avatar"]',
            'item["other_verified"]',
            'item["unread_count"] > 0',
            "type_badge(item)",
            'item["job_title"]',
            'item["preview"]',
            '"No messages yet"',
            'UnifiedInboxState.selected_key == item["key"]',
            "aria_current",
            "open_item",
            "gah-conversation-toggle",
            "relative flex flex-1 min-w-0",
            "flex w-full min-w-0",
        ):
            self.assertIn(token, row)
        self.assertIn("text-lg font-semibold", row)
        self.assertIn("text-sm font-medium leading-relaxed", row)
        self.assertNotIn('"mail-open"', row)
        self.assertEqual(row.count("avatar_with_tick("), 1)
        source = inspect.getsource(unified_inbox.unified_conversation_list)
        self.assertNotIn("gah-edge-stack", source)
        self.assertNotIn("overflow-hidden", source)
        self.assertIn("gap-3 bg-transparent", source)
        self.assertNotIn("divide-y", source)
        self.assertIn(
            ":not(.gah-conversation-toggle)", inspect.getsource(theme_overrides)
        )

    def test_editorial_headings_and_empty_copy(self):
        compose = messages_panel.compose_area()
        row = compose.children[0]
        self.assertIn("grid-cols-", str(row.class_name))
        self.assertEqual(row.children[0].tag, "button")
        heading = row.children[1]
        self.assertEqual(heading.tag, "h3")
        self.assertIn("Write a message", str(heading))
        for token in (
            "text-center",
            "text-base",
            "sm:text-lg",
            "font-semibold",
        ):
            self.assertIn(token, str(heading.class_name))
        self.assertEqual(len(heading.children), 2)
        self.assertIn(
            "envelope_star()", inspect.getsource(messages_panel.compose_area)
        )
        for factory, target, opened, toggle in (
            (
                messages_panel.offers_block,
                "inbox-offers",
                "offers_open",
                "toggle_offers",
            ),
            (
                messages_panel.helpee_requests_block,
                "inbox-requests",
                "requests_open",
                "toggle_requests",
            ),
        ):
            section = factory()
            heading = section.children[0]
            self.assertEqual(heading.tag, "h3")
            self.assertIn("w-full", str(heading.class_name))
            self.assertEqual(len(heading.children), 1)
            button = heading.children[0]
            self.assertEqual(button.tag, "button")
            for token in (
                "w-full",
                "py-3",
                "gap-3",
                "font-bold",
                "gah-conversation-toggle",
                "focus-visible:ring-[#fba922]",
            ):
                self.assertIn(token, str(button.class_name))
            self.assertEqual(button.children[0].tag, "span")
            self.assertEqual(button.children[1].tag, "span")
            self.assertIn("text-[#e08b12]", str(button.children[0]))
            for token in (
                "bg-transparent",
                "text-center",
                "text-xl",
                "sm:text-2xl",
            ):
                self.assertIn(token, str(button.class_name))
            self.assertNotIn("bg-white", str(button.class_name))
            self.assertNotIn("rounded", str(section.class_name))
            source = inspect.getsource(factory)
            self.assertIn(
                "rounded-2xl bg-white shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
                source,
            )
            self.assertIn("section_skeleton()", source)
            self.assertIn("hub_empty(", source)
            self.assertIn("aria-expanded", str(button))
            self.assertIn("aria-controls", str(button))
            self.assertIn(target, str(button))
            self.assertIn(opened, str(button))
            self.assertIn(toggle, str(button))
            self.assertIn(f'id="{target}"', inspect.getsource(factory))
        disclosure = inspect.getsource(messages_panel.inbox_disclosure)
        grammar_branches = [
            node
            for node in ast.walk(ast.parse(disclosure))
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.cond"
            and ast.unparse(node.args[0]) == "count == 1"
        ]
        self.assertCountEqual(
            [
                tuple(ast.literal_eval(arg) for arg in node.args[1:])
                for node in grammar_branches
            ],
            [
                ("Offer to help you", "Offers to help you"),
                ("Request for your help", "Requests for your help"),
                ("Message from contacts", "Messages from contacts"),
            ],
        )
        self.assertLess(
            disclosure.index("rx.el.span(count"), disclosure.index("rx.match(")
        )
        for token in (
            'type="button"',
            "aria_expanded=opened",
            "aria_controls=target",
            "on_click=toggle",
            "disclosure_arrow(opened)",
        ):
            self.assertIn(token, disclosure)
        source = inspect.getsource(messages_panel.compact_heading)
        self.assertNotIn("rx.icon", source)
        self.assertIn(
            "HelpHubState.help_offers.length()",
            inspect.getsource(messages_panel.offers_block),
        )
        self.assertIn(
            "MessagingState.direct_request_count",
            inspect.getsource(messages_panel.helpee_requests_block),
        )
        for icon in ("inbox", "hand-helping"):
            empty = messages_panel.hub_empty("Empty", "Description", icon)
            self.assertIn("text-[#fba922]", str(empty.children[0].class_name))
            self.assertIn(
                "text-sm font-medium leading-relaxed",
                str(empty.children[2].class_name),
            )
            self.assertIn("text-center", str(empty.class_name))
        self.assertIn(
            '"Confirm a contact in Community, then message them",\n                        class_name="mt-1 text-sm font-medium leading-relaxed',
            inspect.getsource(messages_panel.compose_area),
        )

    def test_paper_bubbles_secondary_times_and_compact_actions(self):
        source = inspect.getsource(chat_controls._correspondence_bubble)
        self.assertEqual(
            source.count("shadow-[0_2px_4px_rgba(17,24,39,0.10)]"), 2
        )
        timestamp_and_outer = source[source.index('msg["sent_at"]') :]
        self.assertNotIn("shadow", timestamp_and_outer)
        self.assertEqual(timestamp_and_outer.count("text-xs text-[#4b5563]"), 2)
        self.assertIn("text-right", timestamp_and_outer)
        self.assertIn("text-left", timestamp_and_outer)
        self.assertNotIn("shadow", chat_controls.HISTORY_CLASS)
        self.assertIn("text-xs", REPORT_BUTTON_CLASS.split())
        self.assertEqual(REPORT_BUTTON_CLASS, BLOCK_BUTTON_CLASS)
        self.assertNotIn("text-[11px]", REPORT_BUTTON_CLASS)
        self.assertIn("[&_button]:text-xs", source)
        for factory in (
            chat_safety,
            messages_panel.completion_card,
        ):
            self.assertIn("text-xs font-semibold", inspect.getsource(factory))

    def test_inbox_conditional_branches_compile(self):
        from app.states.unified_inbox_state import UnifiedInboxState

        pane = messages_panel.reading_pane()
        populated = rx.foreach(
            UnifiedInboxState.items,
            lambda item: unified_inbox.conversation_card(item, pane),
        )
        for component in (
            unified_inbox.empty_state(),
            unified_inbox.list_skeleton(),
            populated,
            unified_inbox.unified_conversation_list(pane),
            messages_panel.compose_area(),
            messages_panel.offers_block(),
            messages_panel.helpee_requests_block(),
            messages_panel.job_conversation_panel(),
            contacts_panel.conversation_panel(True),
            noncontact_panel.noncontact_conversation_view(True),
        ):
            self.assertTrue(component.render())
            self.assertTrue(str(component))
        rendered = str(populated)
        self.assertNotIn("reader-", rendered)
        self.assertIn("aria-current", rendered)
        self.assertNotIn("Confirm job is done", rendered)
        self.assertIn(
            "Confirm job is done", str(messages_panel.inbox_thread_view())
        )

    def test_full_component_trees(self):
        for factory in (
            messages_panel.messages_panel,
            messages_panel.job_conversation_panel,
            contacts_panel.conversation_panel,
            noncontact_panel.noncontact_conversation_view,
            index,
        ):
            with self.subTest(factory=factory.__name__):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
