import reflex as rx

import inspect
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from app.app import theme_overrides
from app.components import (
    bottom_nav,
    guest_map,
    header,
    map_utilities,
    member_map,
)
from app.components import membership_info, profile_tabs as profile
from app.states.profile_state import ProfileState
from app.states.notification_state import NotificationState


class MapProfileFollowupTests(unittest.TestCase):
    def test_contextual_brand(self):
        self.assertIn("text-[#fba922]", header.MAP_BRAND_TEXT_CLASS)
        self.assertNotIn("gradient", header.MAP_BRAND_TEXT_CLASS)
        for token in (
            "bg-linear-to-r",
            "from-[#23de49]",
            "to-[#fba922]",
            "bg-clip-text",
            "text-transparent",
        ):
            self.assertIn(token, header.BRAND_TEXT_CLASS)
        self.assertIn("text-[#111827]", header.PAGE_TITLE_CLASS)
        for factory in (
            guest_map.guest_map_brand_lockup,
            member_map.member_brand_lockup,
        ):
            self.assertNotIn("MAP_BRAND_TEXT_CLASS", inspect.getsource(factory))

    def test_notifications_and_dock(self):
        source = inspect.getsource(map_utilities.sheet_header)
        self.assertIn('title == "Notifications"', source)
        self.assertIn('"bell"', source)
        self.assertIn("text-[#fba922]", source)
        self.assertIn(
            '"bell", class_name="size-6 text-[#fba922]"',
            inspect.getsource(map_utilities.notification_feed),
        )
        nav = inspect.getsource(bottom_nav.nav_button)
        self.assertIn("stroke_width=1.75", nav)
        self.assertNotIn("stroke_width=rx.cond", nav)
        avatar = inspect.getsource(bottom_nav.profile_button)
        for token in (
            "aspect-square",
            "min-w-[36px]",
            "min-h-[36px]",
            "rounded-full",
            "object-cover",
            "overflow-visible",
            "outline-[#fba922]",
            "activity_dot(NotificationState.reviews_unread)",
        ):
            self.assertIn(token, avatar)
        slot = bottom_nav.profile_button().children[0]
        self.assertIn("size-[36px]", str(slot.class_name))

    def test_membership_left_alignment(self):
        comparison = membership_info.membership_information_section().children[
            1
        ]
        for column in comparison.children:
            heading = column.children[0]
            self.assertEqual(len(heading.children), 2)
            row, price = heading.children
            for token in ("flex", "w-full", "items-center", "justify-start"):
                self.assertIn(token, str(row.class_name))
            self.assertEqual(len(row.children), 3)
            icon, title, tier = row.children
            self.assertEqual(len(icon.children), 1)
            self.assertEqual(title.tag, "h4")
            self.assertIn("text-left", str(title.class_name))
            self.assertIn("Your tier", str(tier))
            self.assertEqual(price.tag, "p")
            self.assertIn("text-left", str(price.class_name))
            self.assertNotIn("Your tier", str(price))
        header_source = inspect.getsource(membership_info.comparison_column)
        self.assertLess(
            header_source.index("rx.icon(icon"),
            header_source.index("rx.el.h4("),
        )
        self.assertLess(
            header_source.index("rx.el.h4("), header_source.index("is_current,")
        )
        self.assertLess(
            header_source.index("is_current,"),
            header_source.index('"Your tier"'),
        )
        self.assertLess(
            header_source.index('"Your tier"'), header_source.index("rx.el.p(")
        )
        source = inspect.getsource(
            membership_info.membership_information_section
        )
        self.assertLess(
            source.index('"Premium members"'), source.index('"Free members"')
        )
        premium, free = comparison.children
        self.assertIn("UserRoundCheck", str(premium))
        self.assertNotIn("Ticket", str(premium))
        self.assertIn("text-[#fba922]", str(premium.children[0]))
        self.assertIn("User", str(free.children[0]))
        self.assertIn("text-[#22c55e]", str(free.children[0]))
        self.assertIn("bg-[#dcfce7]", str(free.children[0]))
        self.assertIn(
            "text-[#22c55e]",
            str(membership_info.free_line(rx.Var.create("Benefit"))),
        )
        self.assertIn("coffee_price_label", source)
        self.assertIn("$49 annually", source)

    def test_save_borders_and_existing_handlers(self):
        css = inspect.getsource(theme_overrides)
        self.assertIn(":not(.gah-orange-control)", css)
        for factory in (
            profile.save_changes_button,
            profile.skills_knowledge_section,
        ):
            source = inspect.getsource(factory)
            self.assertIn("gah-profile-save gah-orange-control", source)
            self.assertIn("border border-[#fba922] border-solid", source)
            self.assertIn("disabled=ProfileState.is_saving", source)
        for factory, handler in (
            (profile.details_tab, "save_details"),
            (profile.skills_knowledge_section, "save_skills"),
        ):
            self.assertIn(
                f"on_submit=ProfileState.{handler}", inspect.getsource(factory)
            )

    def test_location_privacy_and_spacing(self):
        self.assertNotIn("My location", str(profile.profile_screen()))
        self.assertIn(
            'name="home_country"', inspect.getsource(profile.details_tab)
        )
        css = inspect.getsource(theme_overrides)
        self.assertIn(":not(.gah-segment-control)", css)
        self.assertIn(
            ".gah-segment-group { box-shadow: var(--gah-control-shadow); }", css
        )
        self.assertIn(
            "w-full text-center text-sm",
            inspect.getsource(profile.skills_knowledge_section),
        )
        note = inspect.getsource(profile.blocked_members_section)
        self.assertIn("text-black", note)
        self.assertIn("text-[#e08b12]", note)
        self.assertIn(
            "bg-white", str(profile.blocked_members_section().class_name)
        )
        self.assertIn(
            'class_name="text-xs font-medium leading-relaxed text-black"', note
        )
        self.assertRegex(
            note,
            r'"lock",\s+class_name="[^"]*text\-\[#e08b12\][^"]*"',
        )
        self.assertEqual(
            note.count(
                'class_name="animate-pulse h-16 w-full rounded-2xl bg-[#fff7e8]"'
            ),
            2,
        )
        self.assertIn("on_mount=BlockState.load_blocked_members", note)

    def test_component_render_smoke(self):
        for opened in (False, True):
            with ExitStack() as stack:
                for field in (
                    "information_open",
                    "skills_open",
                    "location_open",
                    "blocked_open",
                ):
                    stack.enter_context(
                        patch.object(ProfileState, field, rx.Var.create(opened))
                    )
                stack.enter_context(
                    patch.object(
                        NotificationState, "panel_open", rx.Var.create(opened)
                    )
                )
                for factory in (
                    guest_map.guest_map_experience,
                    member_map.member_map_experience,
                    map_utilities.map_utility_sheets,
                    profile.profile_screen,
                    profile.my_information_section,
                    profile.skills_knowledge_section,
                    profile.blocked_members_section,
                    membership_info.membership_information_section,
                ):
                    with self.subTest(
                        opened=opened, component=factory.__name__
                    ):
                        component = factory()
                        self.assertIsInstance(component, rx.Component)
                        self.assertTrue(component.render())
                        self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
