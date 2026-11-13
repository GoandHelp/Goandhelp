import reflex as rx

import inspect
import unittest
from unittest.mock import patch

from app.app import theme_overrides
from app.components import (
    profile_tabs as profile,
    membership_info as membership,
)
from app.components.disclosure import disclosure_arrow
from app.states.profile_state import ProfileState


class MyProfilePolishTests(unittest.TestCase):
    def test_stars_and_arrows(self):
        stars = profile.inline_rating_stars()
        self.assertIn("gah-rating-stars", str(stars.class_name))
        self.assertNotIn("hover:bg-", str(stars.class_name))
        self.assertIn("open_reviews", str(stars))
        css = str(theme_overrides())
        self.assertIn(":not(.gah-rating-stars)", css)
        self.assertIn(
            "button.gah-rating-stars { background: transparent !important; border: 0 !important; box-shadow: none !important;",
            css,
        )
        self.assertIn("button.gah-rating-stars:focus-visible", css)
        self.assertIn(
            ".gah-profile-screen .gah-disclosure-arrow { background: white;",
            css,
        )
        for opened in (False, True):
            self.assertTrue(disclosure_arrow(opened).render())

    def test_stack_and_membership(self):
        screen = profile.profile_screen()
        self.assertIn("gap-[17px]", str(screen.class_name))
        stack = screen.children[3]
        self.assertEqual(len(stack.children), 4)
        self.assertIn("Blocked members", str(stack.children[-1]))
        self.assertNotIn("Membership information", str(stack))
        premium = screen.children[4]
        self.assertIn("gah-profile-membership", str(premium.class_name))
        self.assertIn("rounded-2xl", str(premium.class_name))
        heading = str(premium.children[0])
        for text in (
            "text-lg",
            "text-center",
            "Unlock more as a Premium Member",
        ):
            self.assertIn(text, heading)
        self.assertNotIn("tier_name", heading)
        self.assertNotIn("FREE MEMBER", heading)
        self.assertIn(
            "Your tier", inspect.getsource(membership.comparison_column)
        )
        self.assertNotIn(
            "pl-12", inspect.getsource(membership.comparison_column)
        )
        self.assertIn("gap-4", inspect.getsource(membership.benefit_line))
        self.assertIn("border border-[#fba922]", str(premium))
        self.assertIn("open_paywall", str(premium))
        self.assertIn("bg-[#fba922] hover:bg-[#e08b12]", str(premium))
        comparison = premium.children[1]
        self.assertIn("Premium members", str(comparison.children[0]))
        self.assertIn("Free members", str(comparison.children[1]))
        self.assertIn("text-[#22c55e]", str(comparison.children[1]))
        self.assertIn("0 -3px 12px", str(theme_overrides()))

    def test_copy_and_flat_forms(self):
        details = str(profile.details_tab())
        for text in (
            "Your number is not shared with other users",
            "unique, lowercase",
            "why you help, why you need help",
            "I.e. I'm a Photographer travelling Asia, happy to help others in exchange for a accommodation...",
        ):
            self.assertIn(text, details)
        notice = profile.phone_privacy_notice()
        for component in (notice, notice.children[0]):
            self.assertIn("bg-[#fff7e8]", str(component.class_name))
            self.assertNotIn("border", str(component.class_name))
        self.assertIn("text-[#e08b12]", str(notice.children[0].class_name))
        self.assertIn("size-6", str(notice.children[0].class_name))
        self.assertIn(
            "h-3.5 w-3.5", str(notice.children[0].children[0].class_name)
        )
        self.assertIn("font-normal", str(notice.children[1].class_name))
        self.assertIn("px-3 py-2", str(notice.class_name))
        blocked = inspect.getsource(profile.blocked_members_section)
        self.assertIn(
            "bg-white", str(profile.blocked_members_section().class_name)
        )
        self.assertIn(
            'class_name="text-xs font-medium leading-relaxed text-black"',
            blocked,
        )
        self.assertRegex(
            blocked,
            r'"lock",\s+class_name="[^"]*text\-\[#e08b12\][^"]*"',
        )
        self.assertEqual(
            blocked.count(
                'class_name="animate-pulse h-16 w-full rounded-2xl bg-[#fff7e8]"'
            ),
            2,
        )
        self.assertIn("text-black", blocked)
        self.assertIn("text-[#e08b12]", blocked)
        self.assertIn("Blocked members are never notified.", blocked)
        skills = inspect.getsource(profile.skills_knowledge_section)
        self.assertIn('"My Skills"', skills)
        self.assertNotIn("My skills and knowledge", skills)
        self.assertIn("My Skills", str(profile.skills_knowledge_section()))
        self.assertIn("Select what you can help with", skills)
        self.assertNotIn("bg-[#f7faff]", skills)
        for factory, handler in (
            (profile.details_tab, "save_details"),
            (profile.skills_knowledge_section, "save_skills"),
        ):
            rendered = str(factory())
            self.assertIn(
                f"on_submit=ProfileState.{handler}", inspect.getsource(factory)
            )
            self.assertIn("border border-[#fba922]", rendered)
            self.assertIn("disabled", rendered)
            self.assertIn("Saving", rendered)

    def test_location_and_spacing(self):
        self.assertNotIn("My location", str(profile.profile_screen()))
        self.assertIn(
            'name="home_country"', inspect.getsource(profile.details_tab)
        )
        css = str(theme_overrides())
        self.assertIn(
            "input.gah-location-input:is(:focus, :focus-visible)", css
        )
        self.assertIn(
            "border: 1px solid #fba922 !important; outline: none !important; box-shadow: none !important;",
            css,
        )
        self.assertIn("top-[10px]", str(profile.sign_out_action().class_name))
        self.assertIn(
            "6.5rem+env(safe-area-inset-bottom)",
            inspect.getsource(profile.profile_tabs),
        )

    def test_render_collapsed_and_expanded(self):
        for opened in (False, True):
            with (
                patch.object(
                    ProfileState, "information_open", rx.Var.create(opened)
                ),
                patch.object(
                    ProfileState, "skills_open", rx.Var.create(opened)
                ),
                patch.object(
                    ProfileState, "location_open", rx.Var.create(opened)
                ),
                patch.object(
                    ProfileState, "blocked_open", rx.Var.create(opened)
                ),
            ):
                for factory in (
                    profile.profile_screen,
                    membership.membership_information_section,
                    profile.details_tab,
                    profile.skills_knowledge_section,
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
