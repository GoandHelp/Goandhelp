import reflex as rx

import ast
import inspect
import unittest

from app.app import session_skeleton, theme_overrides
from app.components import discover_panel as ui


class MapPassportRefinementTests(unittest.TestCase):
    def test_loading_and_close_palette(self):
        loading = inspect.getsource(session_skeleton)
        for token in (
            "from-[#ffe2bd] to-[#d9e9d4]",
            "duration: 3000",
            "shadow-[0_2px_10px_rgba(70,55,38,0.10)]",
            "prefers-reduced-motion: reduce",
            "pulse.cancel()",
            'role="status"',
            'aria_live="polite"',
        ):
            self.assertIn(token, loading)
        self.assertNotIn("duration: 1000", loading)
        css = inspect.getsource(theme_overrides)
        close_rule = next(
            line
            for line in css.splitlines()
            if ':is(button,a)[aria-label^="Close"] {' in line
        )
        for token in ("#fff7e8", "#f7d9a0", "#b86e08", "!important"):
            self.assertIn(token, close_rule)
        self.assertNotIn("gah-inverse-text", close_rule)
        self.assertIn('[aria-label^="Close"] :is(svg,span)', css)
        self.assertIn(
            ':is([aria-label^="Back"],.gah-close-back):not(.gah-inverse-text)',
            css,
        )
        self.assertIn(".gah-helper-hand { transform: rotate(45deg); }", css)
        self.assertNotIn(".gah-helpee-hand { transform: rotate", css)
        self.assertIsInstance(session_skeleton(), rx.Component)

    def test_helper_sheet_and_send_position(self):
        sheet = inspect.getsource(ui.detail_panel)
        for token in (
            "absolute right-3 top-2",
            "px-3 pb-6 pt-3",
            "bottom-[calc(3.875rem+env(safe-area-inset-bottom))]",
            "pb-[calc(1.5rem+env(safe-area-inset-bottom))]",
            "overflow-y-auto overscroll-contain",
        ):
            self.assertIn(token, sheet)
        direct = inspect.getsource(ui.direct_help_section)
        self.assertIn("disabled=~DiscoveryState.direct_can_send", direct)
        self.assertIn("| DiscoveryState.is_sending_direct", direct)
        self.assertIn("on_click=DiscoveryState.send_direct_help", direct)
        self.assertIn('class_name="flex w-full justify-end pt-2"', direct)
        tree = ast.parse(direct)
        send_button = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.el.button"
            and any(
                isinstance(value, ast.Constant)
                and value.value == "Send request"
                for value in ast.walk(node)
            )
        )
        self.assertTrue(
            any(kw.arg == "disabled" for kw in send_button.keywords)
        )
        self.assertIn("rounded-xl border border-[#f7d9a0] bg-white p-2", direct)
        helper = inspect.getsource(ui.helper_detail)
        self.assertLess(
            helper.index('selected_helper["headline"]'),
            helper.index("ContactsState.send_request("),
        )
        self.assertLess(
            helper.index("original_language_disclosure("),
            helper.index("report_button("),
        )
        self.assertIn("block_member_button(", helper)
        self.assertIn("items-center justify-center", helper)

    def test_request_header_metadata_and_actions(self):
        body = inspect.getsource(ui.detail_body)
        identity = inspect.getsource(ui.poster_card)
        self.assertIn("avatar_with_tick(", identity)
        for field in (
            "poster_image",
            "poster_verified",
            "poster_id",
            "poster_name",
            "poster_headline",
            "poster_languages",
        ):
            self.assertIn(field, identity)
        self.assertLess(
            identity.index('selected_post["title"]'),
            identity.index('selected_post["poster_name"]'),
        )
        self.assertNotIn("category_icon(", body)
        self.assertNotIn('selected_post["category_chips"]', body)
        self.assertIn(
            'selected_post["location"]', inspect.getsource(ui.request_where_row)
        )
        self.assertIn('selected_post["category_label"]', body)
        self.assertIn('selected_post["scheduled_full"]', body)
        self.assertLess(
            body.index("poster_card()"),
            body.index('selected_post["description"]'),
        )
        self.assertLess(
            body.index("accept_section()"),
            body.index("request_footer_actions()"),
        )
        meta = inspect.getsource(ui.detail_meta_row)
        self.assertIn('f"{label} – "', meta)
        self.assertIn('class_name="min-w-0 flex-1 leading-snug"', meta)
        self.assertNotIn("flex-col", meta)
        stack = inspect.getsource(ui.request_action_stack)
        self.assertLess(
            stack.index("help_share("), stack.index("bookmark_tab(")
        )
        self.assertIn("flex flex-col items-end gap-2", stack)
        self.assertIn('request_action_stack("list-detail")', body)
        sheet = inspect.getsource(ui.detail_panel)
        self.assertIn('request_action_stack("detail")', sheet)
        self.assertIn("relative z-50", stack)
        self.assertIn("relative z-40", stack)
        self.assertNotIn("help_share(", body[body.index("accept_section()") :])
        footer = inspect.getsource(ui.request_footer_actions)
        self.assertIn("detail_contact(", footer)
        self.assertIn("REPORT_TARGET_JOB_MESSAGE", footer)
        self.assertIn("justify-center", footer)
        offer = inspect.getsource(ui.offer_help_section)
        self.assertEqual(offer.count("Offer how you can help"), 2)
        self.assertNotIn("Your message to the poster", offer)
        self.assertNotIn("Introduce yourself", offer)
        self.assertIn("disabled=~DiscoveryState.offer_can_send", offer)
        self.assertIsInstance(ui.detail_body(), rx.Component)
        self.assertIsInstance(ui.detail_panel(), rx.Component)


if __name__ == "__main__":
    unittest.main()
