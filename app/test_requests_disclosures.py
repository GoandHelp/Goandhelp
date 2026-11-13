import reflex as rx

import inspect
import unittest

from app.components import (
    disclosure,
    event_cards,
    help_hub_panel,
    help_post_panel,
    saved_items,
)
from app.app import theme_overrides


class RequestsDisclosureTests(unittest.TestCase):
    def test_all_six_records_use_independent_disclosures(self):
        for factory in (
            help_hub_panel.upcoming_help_card,
            help_hub_panel.confirmed_helper_record,
            event_cards.others_event_record,
            event_cards.hosted_event_block,
            saved_items.saved_request_card,
            help_hub_panel.own_request_record,
        ):
            with self.subTest(record=factory.__name__):
                self.assertIn("record_disclosure(", inspect.getsource(factory))
        shell = disclosure.record_disclosure(
            disclosure.record_summary(
                rx.el.span("Icon"), "Title", "Date · Place", "Confirmed"
            ),
            rx.el.button("Expanded action"),
        )
        self.assertEqual(shell.tag, "details")
        self.assertEqual(shell.children[0].tag, "summary")
        source = inspect.getsource(disclosure.record_disclosure)
        self.assertNotIn("open=", source)
        self.assertNotIn("name=", source.replace("class_name=", ""))
        self.assertIn(
            "[&[open]>summary>span:last-child_svg]:rotate-180", source
        )
        summary = inspect.getsource(disclosure.record_summary)
        for control in ("rx.el.button", "rx.el.a(", "rx.el.form", "on_click"):
            self.assertNotIn(control, summary)
        self.assertIn("disclosure_arrow()", summary)
        self.assertIn("focus-visible", summary)

    def test_order_copy_and_counts(self):
        source = inspect.getsource(help_hub_panel.help_hub_panel)
        self.assertLess(
            source.index("recent_requests_section()"),
            source.index("saved_searches_section()"),
        )
        self.assertLess(
            source.index("saved_searches_section()"),
            source.index("saved_requests_section()"),
        )
        self.assertIn(
            '"Your help requests"',
            inspect.getsource(help_hub_panel.recent_requests_section),
        )
        self.assertNotIn(
            "Your recent help requests", inspect.getsource(help_hub_panel)
        )
        count_source = inspect.getsource(help_hub_panel.counts_summary)
        self.assertIn("} Requested", count_source)
        self.assertNotIn("Requests posted", count_source)

    def test_arrows_and_shadow(self):
        for factory in (
            help_hub_panel.help_day_field,
            help_hub_panel.required_languages_field,
        ):
            self.assertIn("disclosure_arrow(", inspect.getsource(factory))
        self.assertNotIn(
            "disclosure_arrow",
            inspect.getsource(help_hub_panel.post_help_section),
        )
        arrow = inspect.getsource(disclosure.disclosure_arrow)
        self.assertIn("rounded-full", arrow)
        self.assertIn("aria_hidden=True", arrow)
        self.assertIn("size-7", arrow)
        self.assertIn(
            "pointer-events-none",
            inspect.getsource(help_hub_panel.clock_select),
        )
        theme = inspect.getsource(theme_overrides)
        self.assertIn("0 2px 12px rgba(17,24,39,.10)", theme)
        self.assertNotIn("5px 5px 0", theme)
        self.assertIn("box-shadow: none !important", theme)

    def test_expanded_actions_and_community_preserved(self):
        self.assertIn(
            "directions_block(job)",
            inspect.getsource(help_hub_panel.upcoming_help_body),
        )
        self.assertIn(
            "MessagingState.focus_thread",
            inspect.getsource(help_hub_panel.confirmed_helper_card),
        )
        self.assertIn(
            "own_request_body(post)",
            inspect.getsource(help_hub_panel.own_request_record),
        )
        self.assertIn(
            "owner_delete_footer(post)",
            inspect.getsource(help_post_panel.post_card),
        )
        saved_body = inspect.getsource(saved_items.saved_request_body)
        for text in (
            "saved_request_note_form(request)",
            "BookmarkState.open_on_map",
            "BookmarkState.toggle_bookmark",
        ):
            self.assertIn(text, saved_body)
        host_body = inspect.getsource(event_cards.hosted_event_body)
        for text in (
            "pending_request_card(row)",
            "confirmed_attendee_card(row)",
        ):
            self.assertIn(text, host_body)
        self.assertNotIn(
            "record_disclosure", inspect.getsource(event_cards.event_card)
        )
        self.assertIn(
            "event_card(item", inspect.getsource(event_cards.events_feed)
        )

    def test_complete_requests_component_tree_compilation(self):
        component = help_hub_panel.help_hub_panel()
        self.assertIsInstance(component, rx.Component)
        self.assertTrue(component.render())
        self.assertTrue(str(component))
        self.assertTrue(str(event_cards.events_section()))


if __name__ == "__main__":
    unittest.main()
