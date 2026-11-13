import inspect
import unittest

import reflex as rx

from app.components import header, messages_panel, unified_inbox
from app.states.unified_inbox_state import TYPE_FILTERS


class InboxNavigationPolishTests(unittest.TestCase):
    def test_shared_titles_and_mail_alignment(self):
        for token in ("text-lg", "font-semibold", "text-[#111827]"):
            self.assertIn(token, header.PAGE_TITLE_CLASS)
        self.assertNotIn("font-bold", header.PAGE_TITLE_CLASS)
        self.assertIn("text-[#111827]", header.PAGE_TITLE_ICON_CLASS)
        source = inspect.getsource(header.page_title_icon)
        self.assertIn('"mail"', source)
        self.assertIn("-translate-y-[2px] text-[#111827]", source)
        self.assertNotIn("translate-y-[3px]", source)
        self.assertIn(
            "page_title_icon()", inspect.getsource(header.page_title_block)
        )
        self.assertTrue(header.page_title_block().render())

    def test_filter_order_and_three_choices(self):
        self.assertEqual(
            [(item["value"], item["label"]) for item in TYPE_FILTERS],
            [
                ("helper", "Helpers"),
                ("helpee", "Helpees"),
                ("contact", "Contacts"),
            ],
        )
        filters = inspect.getsource(unified_inbox.filter_chip)
        self.assertNotIn("direction_arrow", filters)
        self.assertIn("unread_by_type", filters)
        self.assertIn("aria_pressed", filters)
        self.assertTrue(unified_inbox.filter_chip(TYPE_FILTERS[0]).render())

    def test_compact_new_shares_search_row_and_contacts_remain_reachable(self):
        toolbar = unified_inbox.inbox_toolbar()
        row = toolbar.children[0]
        search_box, funnel, new = row.children
        self.assertIn("New", str(new))
        self.assertIn(
            '"mail-plus"', inspect.getsource(unified_inbox.inbox_toolbar)
        )
        self.assertIn("open_compose", str(new))
        self.assertIn("min-h-12", str(new.class_name))
        self.assertIn("flex-1", str(search_box.class_name))
        self.assertIn("gah-inbox-search", str(search_box))
        self.assertIn("Filters", str(funnel))
        self.assertNotIn("Refresh conversations", str(toolbar))
        self.assertNotIn(
            "inbox_actions()", inspect.getsource(messages_panel.messages_panel)
        )
        self.assertEqual(len(toolbar.children[1].children), 2)
        self.assertNotIn("My contacts", str(toolbar.children[1]))

    def test_filter_disclosure_and_clear_action(self):
        toolbar = unified_inbox.inbox_toolbar()
        filter_row = toolbar.children[1]
        toggle = toolbar.children[0].children[1]
        clear = filter_row.children[1]
        self.assertIn("Filters", str(toggle))
        self.assertIn("aria-expanded", str(toggle))
        self.assertIn("gah-inbox-filters", str(toggle))
        self.assertIn("toggle_filters", str(toggle))
        self.assertIn(
            "filters_open", inspect.getsource(unified_inbox.inbox_toolbar)
        )
        self.assertNotIn("My contacts", str(filter_row))
        self.assertIn("clear", str(clear))
        self.assertIn("Clear filters", str(clear))
        self.assertIn("clear_filters", str(clear))
        self.assertIn(
            "mt-2 flex w-full min-w-0",
            inspect.getsource(unified_inbox.inbox_toolbar),
        )
        self.assertTrue(toolbar.render())

    def test_back_and_centered_subview_headings_keep_forms_and_links(self):
        back = unified_inbox.back_to_inbox()
        self.assertIn("Back", str(back))
        self.assertNotIn("Back to Inbox</", str(back))
        self.assertIn("back_to_inbox", str(back))
        for view, label in (
            (messages_panel.compose_area(), "Write a message"),
            (unified_inbox.inbox_contacts_view(), "My contacts"),
        ):
            row = view.children[0]
            self.assertIn(
                "grid-cols-[minmax(0,1fr)_minmax(0,2fr)_minmax(0,1fr)]",
                str(row.class_name),
            )
            self.assertEqual(len(row.children), 3)
            self.assertEqual(row.children[0].tag, "button")
            self.assertEqual(row.children[1].tag, "h3")
            self.assertEqual(row.children[2].tag, "span")
            self.assertIn(label, str(row.children[1]))
            self.assertIn("text-[#111827]", str(row.children[1].class_name))
            self.assertTrue(view.render())
        self.assertIn(
            "envelope_star()", inspect.getsource(messages_panel.compose_area)
        )
        self.assertIn(
            '"users-round"',
            inspect.getsource(unified_inbox.inbox_contacts_view),
        )
        compose = inspect.getsource(messages_panel.compose_area)
        for token in (
            "compose_and_send",
            "inbox-to",
            "inbox-subject",
            "inbox-compose-message",
        ):
            self.assertIn(token, compose)
        contacts = inspect.getsource(unified_inbox.inbox_contacts_view)
        self.assertIn("address_book_row", contacts)
        self.assertIn(
            "open_contact_passport",
            inspect.getsource(unified_inbox.address_book_row),
        )
        self.assertIsInstance(messages_panel.messages_panel(), rx.Component)


if __name__ == "__main__":
    unittest.main()
