import inspect
import unittest

import reflex as rx

from app.components import bottom_nav
from app.interface_i18n import ui


class BottomNavLabelTests(unittest.TestCase):
    def test_navigation_icons_precede_translated_labels(self):
        nav_source = inspect.getsource(bottom_nav.nav_button)
        profile_source = inspect.getsource(bottom_nav.profile_button)
        for source, label_expression in (
            (nav_source, "ui(label)"),
            (profile_source, 'ui("Profile")'),
        ):
            with self.subTest(label=label_expression):
                icon_slot = source.index("rx.el.span(")
                translated_label = source.index(label_expression)
                self.assertLess(icon_slot, translated_label)
                self.assertIn("max-w-full shrink-0 whitespace-nowrap", source)
                self.assertIn(
                    "text-center text-[0.6875rem] leading-[12px]", source
                )
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(ui),
        )

    def test_dock_labels_exclude_map_and_preserve_geometry(self):
        nav_source = inspect.getsource(bottom_nav.nav_button)
        profile_source = inspect.getsource(bottom_nav.profile_button)
        logo_source = inspect.getsource(bottom_nav.logo_button)
        dock_source = inspect.getsource(bottom_nav.bottom_nav)
        self.assertIn('"h-[33px] w-[33px] shrink-0"', nav_source)
        self.assertIn('"size-[36px]', profile_source)
        self.assertIn('"h-[36px] w-[36px] shrink-0"', profile_source)
        self.assertIn('"size-[59px]', logo_source)
        self.assertIn('title=ui("Map")', logo_source)
        self.assertIn('aria_label=ui("Map")', logo_source)
        center = bottom_nav.logo_button().children[0].children[0]
        self.assertEqual(len(center.children), 1)
        self.assertIn(str(bottom_nav.LOGO_SRC), str(center.children[0].src))
        self.assertIn("grid-cols-5", dock_source)
        self.assertIn("env(safe-area-inset-bottom)", dock_source)
        self.assertIn("gap-[2px]", bottom_nav.ITEM_BASE)
        self.assertNotIn('"text-[11px]"', bottom_nav.ITEM_BASE)

    def test_existing_navigation_bindings_remain(self):
        nav_source = inspect.getsource(bottom_nav.nav_button)
        profile_source = inspect.getsource(bottom_nav.profile_button)
        for source, token in (
            (
                nav_source,
                "ProfileState.navigate_from_bottom_nav(value, reason)",
            ),
            (
                nav_source,
                'custom_attrs={"data-tour-target": f"{tour_target}{value}"}',
            ),
            (
                profile_source,
                'ProfileState.navigate_from_bottom_nav("profile", "")',
            ),
            (profile_source, 'custom_attrs={"data-tour-target": "profile"}'),
            (
                profile_source,
                'aria_current=rx.cond(is_active("profile"), "page", "false")',
            ),
        ):
            self.assertIn(token, source)
        for component in (
            bottom_nav.nav_button("help", "Requests", "heart-handshake", ""),
            bottom_nav.nav_button("community", "Community", "users-round", ""),
            bottom_nav.nav_button("inbox", "Inbox", "mail", ""),
            bottom_nav.profile_button(),
            bottom_nav.logo_button(),
            bottom_nav.bottom_nav(),
        ):
            with self.subTest(component=component):
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())


if __name__ == "__main__":
    unittest.main()
