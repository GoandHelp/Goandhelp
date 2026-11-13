import reflex as rx

import inspect
import re
import unittest
from pathlib import Path

from app.components import community_panel, profile_tabs
from app.components.header import minimal_header


class CommunityStickyBackingTests(unittest.TestCase):
    def test_backing_covers_scroll_padding_without_changing_geometry(self):
        header = community_panel.community_header()
        classes = str(header.class_name).strip('"').split()
        for token in (
            "gah-community-sticky-header",
            "sticky",
            "top-0",
            "z-30",
            "w-full",
            "shrink-0",
            "bg-white",
            "pb-2",
            "before:content-['']",
            "before:absolute",
            "before:inset-x-0",
            "before:bottom-full",
            "before:h-5",
            "before:bg-inherit",
            "before:pointer-events-none",
        ):
            self.assertIn(token, classes)
        self.assertNotIn("pointer-events-none", classes)
        self.assertNotIn("overflow-hidden", classes)
        self.assertNotIn("backdrop", str(header.class_name))
        self.assertEqual(len(header.children), 1)
        self.assertTrue(header.render())
        shell = inspect.getsource(profile_tabs.profile_tabs)
        self.assertIn("pt-5", shell)
        self.assertIn(
            "min-h-0 flex-1 overflow-y-auto overscroll-contain", shell
        )
        self.assertIn("flex-col min-h-0 w-full flex-1 overflow-hidden", shell)
        self.assertIn("z-40", inspect.getsource(minimal_header))
        self.assertEqual(
            community_panel.FOLDER_ROW_WRAP,
            "flex w-full items-center bg-white py-2",
        )

    def test_dark_backing_inherits_opaque_sheet_color_not_translucent_rules(
        self,
    ):
        css = (
            Path(__file__).resolve().parent.parent / "assets" / "dark_mode.css"
        ).read_text(encoding="utf-8")
        rule = re.search(
            r"html\.dark \.gah-community-sticky-header::before\s*\{([^}]+)\}",
            css,
        )
        self.assertIsNotNone(rule)
        declarations = rule.group(1)
        for token in (
            "background: inherit !important;",
            "background-image: none !important;",
            "backdrop-filter: none !important;",
            "opacity: 1 !important;",
            "mask-image: none !important;",
            "-webkit-mask-image: none !important;",
        ):
            self.assertIn(token, declarations)
        white_rule = re.search(
            r'html\.dark #root \[class~="bg-white"\][^{]+\{([^}]+)\}', css
        )
        self.assertIsNotNone(white_rule)
        self.assertIn(
            "background-color: #15191f !important;", white_rule.group(1)
        )
        self.assertNotIn("rgb(", declarations)
        self.assertNotIn("blur(", declarations)

    def test_localized_read_more_preserves_whole_card_button_and_navigation(
        self,
    ):
        source = inspect.getsource(community_panel.topic_card)
        self.assertIn('ui("Read more")', source)
        self.assertNotIn("Open discussion", source)
        self.assertIn("return rx.el.button(", source)
        self.assertIn('type="button"', source)
        self.assertIn(
            'on_click=lambda: CommunityState.open_topic(topic["id"])', source
        )
        self.assertEqual(source.count("rx.el.button("), 1)
        for field in ("title", "preview", "author_name", "subject"):
            self.assertNotIn(f'ui(topic["{field}"])', source)
        self.assertIn(
            "aria_current=", inspect.getsource(community_panel.folder_tab)
        )
        self.assertIn(
            "CommunityState.set_section",
            inspect.getsource(community_panel.folder_tab),
        )
        self.assertIsInstance(community_panel.community_header(), rx.Component)


if __name__ == "__main__":
    unittest.main()
