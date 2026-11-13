import reflex as rx

import inspect
import unittest

from app.app import index, theme_overrides
from app.components import (
    bottom_nav,
    member_map,
    guest_map,
    header,
    map_utility_icon,
    map_utilities,
    discover_panel,
)
from app.components.discover_panel import distance_filter_block, filter_drawer
from app.components.language_control import language_control
from app.components.profile_tabs import (
    app_language_field,
    settings_content,
    setting_choice,
    notification_settings,
)
from app.components import paywall


class DockUtilityRefinementsTests(unittest.TestCase):
    def test_dock_geometry_and_weightless_controls(self):
        self.assertIn("gah-dock-control", bottom_nav.ITEM_BASE)
        profile = inspect.getsource(bottom_nav.profile_button)
        self.assertIn("size-[36px]", profile)
        self.assertIn("h-[36px]", profile)
        logo = inspect.getsource(bottom_nav.logo_button)
        self.assertEqual(logo.count("rx.image("), 1)
        self.assertIn("border-[3px] border-white", logo)
        dock = inspect.getsource(bottom_nav.bottom_nav)
        self.assertIn("w-full border-0 bg-white", dock)
        self.assertNotIn("border-t", dock)
        self.assertNotIn("bg-white", logo)
        self.assertEqual(bottom_nav.LOGO_SRC, header.BRAND_LOGO_SRC)
        css = inspect.getsource(theme_overrides)
        self.assertIn("button.gah-dock-control", css)
        self.assertIn("box-shadow: none !important", css)
        self.assertIn("0 -3px 12px", css)
        self.assertNotIn("gah-dock-notch", css)
        self.assertNotIn(
            "gah-dock-notch", inspect.getsource(bottom_nav.bottom_nav)
        )
        self.assertNotIn("focus-visible:ring", bottom_nav.ITEM_BASE)
        self.assertNotIn("border-[#123f8f]", profile)
        self.assertNotIn("border-[#dbe3f2]", profile)
        self.assertIn("outline-[#fba922]", profile)
        self.assertIn("text-[#fba922]", bottom_nav.ITEM_ACTIVE)
        self.assertIn("text-[#404040]", bottom_nav.ITEM_IDLE)
        self.assertIn(
            "activity_dot(unread)", inspect.getsource(bottom_nav.nav_button)
        )
        self.assertIn("activity_dot(NotificationState.reviews_unread)", profile)
        self.assertIn("ProfileState.return_to_map", logo)
        self.assertIn("button.gah-dock-control:focus-visible", css)

    def test_map_controls(self):
        source = inspect.getsource(member_map.member_control_stack)
        self.assertLess(source.index('"bell"'), source.index('"cog"'))
        self.assertIn("fixed top-3", source)
        self.assertIn("flex-row", source)
        self.assertIn("map_utility_icon", source)
        self.assertNotIn("member_filters_button()", source)
        self.assertIn("size-[43px]", member_map.UTILITY_BUTTON)
        self.assertIn(
            "size-[43px]", inspect.getsource(guest_map.guest_utility_button)
        )
        glyph = map_utility_icon.map_utility_icon("bell")
        self.assertIn("size-[36px]", str(glyph.class_name))
        icon_source = inspect.getsource(map_utility_icon.map_utility_icon)
        self.assertIn('("bell", filled_bell_icon())', icon_source)
        self.assertIn('("cog", filled_settings_icon())', icon_source)
        self.assertIn('("settings", filled_settings_icon())', icon_source)
        filled_source = inspect.getsource(map_utility_icon.filled_settings_icon)
        self.assertIn('fill="#fba922"', filled_source)
        self.assertIn('fill_rule="evenodd"', filled_source)
        self.assertIn("A5.5 5.5 0 1 0 18 23.5", filled_source)
        self.assertIn('view_box="0 0 36 36"', filled_source)
        self.assertNotIn('rx.icon("settings"', filled_source)
        self.assertNotIn("bg-white", filled_source)
        bell_source = inspect.getsource(map_utility_icon.filled_bell_icon)
        self.assertIn('fill="#fba922"', bell_source)
        self.assertIn("C13.5 29 13.6 29.8 13.9 30.5", bell_source)
        self.assertNotIn('rx.icon("bell"', bell_source)
        self.assertIn("size-[36px]", filled_source)
        unread_dot = inspect.getsource(member_map.member_control_stack)
        self.assertIn(
            "right-[7px] top-[6px] size-2 rounded-full bg-[#ef4444] ring-1 ring-white",
            unread_dot,
        )
        self.assertIn("NotificationState.total_unread > 0", unread_dot)
        self.assertTrue(glyph.render())
        self.assertIn(
            "fixed top-3 right-3",
            inspect.getsource(guest_map.guest_control_stack),
        )
        self.assertNotIn("radial-gradient", inspect.getsource(theme_overrides))
        self.assertIn("content: none", inspect.getsource(theme_overrides))
        for factory in (
            member_map.member_filters_button,
            guest_map.guest_filters_button,
        ):
            source = inspect.getsource(factory)
            self.assertIn("bg-white", str(factory().class_name).split())
            self.assertIn("focus-visible:ring-[#fba922]", source)
            self.assertNotIn("hover:bg-[#15a835]", source)
        self.assertNotIn(
            "bg-[#2362ef]", inspect.getsource(member_map.member_filters_button)
        )
        self.assertIn("from-[#23de49] to-[#fba922]", header.BRAND_TEXT_CLASS)
        self.assertIn("text-[#fba922]", header.MAP_BRAND_TEXT_CLASS)
        for factory in (
            member_map.member_brand_lockup,
            guest_map.guest_map_brand_lockup,
        ):
            with self.subTest(component=factory.__name__):
                source = inspect.getsource(factory)
                self.assertNotIn("MAP_BRAND_TEXT_CLASS", source)
                self.assertEqual(source.count("gah-brand-home"), 2)
                self.assertEqual(
                    str(factory().class_name).count("gah-brand-home"), 2
                )

    def test_map_chrome_rules_and_grouped_selectors(self):
        css = inspect.getsource(theme_overrides)
        for marker in (
            "gah-map-utility",
            "gah-dock-control",
            "gah-segment-control",
        ):
            self.assertIn(f":not(.{marker})", css)
        self.assertIn(
            "button.gah-dock-control, .gah-app-shell button.gah-map-utility { background: transparent !important; border: 0 !important; box-shadow: none !important; }",
            css,
        )
        self.assertIn(
            "button.gah-segment-control { border: 0 !important; box-shadow: none !important; }",
            css,
        )
        self.assertIn(
            ".gah-segment-group { box-shadow: var(--gah-control-shadow); }", css
        )
        self.assertNotIn(".gah-nav-item:active", css)
        self.assertIn('gah-nav-item[aria-current="page"] { color: #fba922', css)
        for token in (
            "rounded-full",
            "border-0",
            "shadow-none",
            "bg-transparent",
        ):
            self.assertIn(token, member_map.UTILITY_BUTTON)
        utilities = inspect.getsource(member_map.member_control_stack)
        self.assertIn("NotificationState.toggle_panel", utilities)
        self.assertIn("NotificationState.toggle_map_settings", utilities)
        for factory, handler in (
            (discover_panel.sheet_mode_button, "set_map_mode"),
            (discover_panel.mode_toggle_button, "set_map_mode"),
            (discover_panel.sheet_view_button, "set_view_mode"),
            (discover_panel.view_toggle_button, "set_view_mode"),
        ):
            with self.subTest(component=factory.__name__):
                source = inspect.getsource(factory)
                self.assertEqual(source.count("gah-segment-control"), 2)
                self.assertIn("bg-[#fba922]", source)
                self.assertIn(handler, source)
                self.assertIn("aria_pressed", source)
        self.assertEqual(
            inspect.getsource(discover_panel.discovery_controls).count(
                "gah-segment-group"
            ),
            2,
        )
        self.assertEqual(
            inspect.getsource(filter_drawer).count("gah-segment-group"), 1
        )
        self.assertEqual(
            inspect.getsource(discover_panel.sheet_view_toggle).count(
                "gah-segment-group"
            ),
            1,
        )
        self.assertIn(
            'rx.icon("bell", class_name="h-4 w-4 text-[#fba922]")',
            inspect.getsource(notification_settings),
        )

    def test_scoped_close_and_range(self):
        css = inspect.getsource(theme_overrides)
        self.assertIn('[aria-label^="Close"]', css)
        self.assertIn('[aria-label^="Back"]', css)
        self.assertNotIn("lucide-x", css)
        for token in (
            "::-webkit-slider-runnable-track",
            "::-moz-range-track",
            "::-moz-range-progress",
            "border: 1px solid #d1d5db",
            "var(--distance-progress,0%)",
        ):
            self.assertIn(token, css)
        slider = inspect.getsource(distance_filter_block)
        self.assertIn("--distance-progress", slider)
        self.assertIn("distance_reset_token", slider)
        self.assertIn("throttle(100)", slider)

    def test_settings_language_notifications_and_paywall(self):
        self.assertIn(
            "border-2 border-[#fba922] bg-white",
            inspect.getsource(setting_choice),
        )
        for factory in (language_control, app_language_field):
            source = inspect.getsource(factory)
            self.assertIn("text-[#fba922]", source)
            self.assertIn("rounded-lg", source)
            self.assertIn("AuthState.update_language", source)
        self.assertIn(
            "gah-edge-stack", inspect.getsource(map_utilities.notification_feed)
        )
        self.assertIn(
            "gap-0", inspect.getsource(map_utilities.notification_feed)
        )
        feed = inspect.getsource(map_utilities.notification_feed)
        self.assertIn("bg-[#fba922]", feed)
        self.assertIn("hover:bg-[#e08b12]", feed)
        row = inspect.getsource(map_utilities.notification_row)
        self.assertEqual(
            row.count("focus-visible:ring-2 focus-visible:ring-[#fba922]"), 2
        )
        for token in (
            'item["is_read"]',
            '"flex w-full items-start gap-2 bg-white p-3"',
            '"flex w-full items-start gap-2 bg-[#fff7e8] p-3"',
            "on_click=NotificationState.open_notification(item)",
            'rx.icon("trash-2"',
            'aria_label="Delete notification"',
            'on_click=NotificationState.delete_notification(item["id"])',
        ):
            self.assertIn(token, row)
        self.assertNotIn("bg-[#fba922]", row)
        self.assertNotIn('"Mark read"', row)
        self.assertNotIn(
            "rounded-2xl", inspect.getsource(map_utilities.notification_row)
        )
        for factory in (paywall.benefit_marker, paywall.free_marker):
            self.assertIn("gap-4", inspect.getsource(factory))
        self.assertIn(
            "text-[#fba922]", inspect.getsource(paywall.benefit_marker)
        )
        self.assertIn(
            "pl-3 sm:pl-5", inspect.getsource(paywall.comparison_rail)
        )
        self.assertIn(
            "text-[#fba922]", inspect.getsource(paywall.annual_pass_choice)
        )
        self.assertEqual(
            inspect.getsource(paywall.annual_pass_choice).count(
                '"Annual pass"'
            ),
            1,
        )
        self.assertIn(
            "text-black", inspect.getsource(paywall.ticket_to_ride_choice)
        )

    def test_component_compile_smoke(self):
        def filter_drawer_with_classes():
            return filter_drawer("w-full")

        for factory in (
            index,
            member_map.member_map_experience,
            member_map.member_list_view,
            discover_panel.discovery_controls,
            discover_panel.sheet_view_toggle,
            guest_map.guest_map_experience,
            bottom_nav.bottom_nav,
            filter_drawer_with_classes,
            settings_content,
            language_control,
            app_language_field,
            map_utilities.map_utility_sheets,
            map_utilities.notification_feed,
            paywall.paywall_modal,
        ):
            with self.subTest(component=factory.__name__):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())


if __name__ == "__main__":
    unittest.main()
