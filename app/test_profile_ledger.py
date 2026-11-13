import reflex as rx

import inspect
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.app import index, theme_overrides
from app.components import feedback, header, membership_info, policy_screens
from app.components import profile_metrics, profile_tabs
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState


class ProfileLedgerTests(unittest.TestCase):
    def test_profile_stack_and_nested_content(self):
        screen = profile_tabs.profile_screen()
        stack = screen.children[3]
        self.assertIn("gah-edge-stack", str(stack.class_name))
        self.assertEqual(len(stack.children), 4)
        self.assertIn(
            "gah-profile-membership", str(screen.children[4].class_name)
        )
        for factory in (
            profile_tabs.my_information_section,
            profile_tabs.skills_knowledge_section,
            profile_tabs.blocked_members_section,
        ):
            classes = str(factory().class_name)
            self.assertIn("gah-profile-row", classes)
            self.assertIn("bg-white", classes)
            for token in ("gah-main-card", "rounded", "shadow", "border"):
                self.assertNotIn(token, classes)
        metrics = inspect.getsource(profile_metrics.metrics_section)
        self.assertIn("gah-profile-row", metrics)
        self.assertIn("MembershipState.is_premium", metrics)
        self.assertIn("metrics_body()", metrics)
        self.assertNotIn("My location", str(stack))
        self.assertIn(
            "ProfileState.save_skills",
            inspect.getsource(profile_tabs.skills_knowledge_section),
        )
        self.assertIn(
            "blocked_member_row",
            inspect.getsource(profile_tabs.blocked_members_section),
        )
        css = inspect.getsource(theme_overrides)
        self.assertIn(
            ".gah-edge-stack > :is(article,li,button,details,section,div)", css
        )
        self.assertNotIn(".gah-edge-stack *", css)
        self.assertIn("border-top: 1px solid #e5e7eb", css)

    def test_verification_semantics_and_photo(self):
        for factory in (
            feedback.verified_badge,
            feedback.verified_tick,
            feedback.verified_chip,
        ):
            source = inspect.getsource(factory)
            self.assertIn("#22c55e", source)
            self.assertIn("text-white", source)
            self.assertIn("Email verified", source)
            self.assertNotIn("#fba922", source)
            self.assertTrue(factory(True).render())
            self.assertTrue(factory(False).render())
        photo = inspect.getsource(profile_tabs.identity_portrait)
        self.assertIn(
            '"camera", class_name="h-3.5 w-3.5 text-[#fba922]"', photo
        )
        self.assertIn("animate-spin text-[#fba922]", photo)
        self.assertIn("border-[#fba922] bg-white", photo)
        self.assertIn("ProfileState.handle_avatar_upload", photo)
        for factory in (
            profile_tabs.disclosure_header,
            profile_metrics.metrics_disclosure_header,
        ):
            source = inspect.getsource(factory)
            self.assertIn("text-[#fba922]", source)
            self.assertIn("gah-profile-disclosure", source)
            self.assertIn("aria_expanded", source)

    def test_membership_comparison(self):
        component = membership_info.membership_information_section()
        heading = component.children[0]
        self.assertNotIn("ticket", str(heading))
        self.assertIn("Membership information", str(heading))
        source = inspect.getsource(
            membership_info.membership_information_section
        )
        self.assertIn("Always free", source)
        self.assertIn(
            'f"{MembershipState.coffee_price_label} / $49 annually"', source
        )
        self.assertNotIn("$5 monthly or $49 annually", source)
        self.assertIn("MembershipState.open_paywall", source)
        self.assertIn("md:grid-cols-2", source)
        self.assertNotIn("md:gap-3", source)
        column = inspect.getsource(membership_info.comparison_column)
        self.assertNotIn("pl-12", column)
        self.assertIn("md:border-t-0 md:border-l", column)
        self.assertNotIn("rounded", column)
        self.assertNotIn("shadow", column)
        self.assertIn(
            "justify-start gap-4",
            inspect.getsource(membership_info.benefit_line),
        )

    def test_policy_and_sign_out(self):
        for factory in (
            policy_screens.policy_links_row,
            policy_screens.policy_link_card,
            policy_screens.policy_section,
            policy_screens.policy_screen,
        ):
            self.assertIn("text-[#fba922]", inspect.getsource(factory))
        self.assertIn(
            "PolicyState.open_policy",
            inspect.getsource(policy_screens.policy_link_card),
        )
        self.assertIn(
            "PolicyState.close_policy",
            inspect.getsource(policy_screens.policy_screen),
        )
        for factory in (header.sign_out_button, profile_tabs.sign_out_action):
            source = inspect.getsource(factory)
            for token in (
                "bg-[#fba922]",
                "text-black",
                "hover:bg-[#e08b12]",
                "AuthState.sign_out",
                "aria_label",
            ):
                self.assertIn(token, source)

    def test_brand_shell(self):
        self.assertEqual(header.BRAND_LOGO_SRC, "/GO%20AND%20HELP%20LOGO.png")
        for token in ("border", "ring", "shadow", "bg-"):
            self.assertNotIn(token, header.BRAND_MARK_CLASS)
        self.assertIn("rounded-full", header.BRAND_MARK_CLASS)
        for factory in (header.minimal_header, header.header):
            source = inspect.getsource(factory)
            self.assertIn("gah-brand-home", source)
            self.assertIn(
                "rounded-none border-0 bg-transparent shadow-none", source
            )
            self.assertIn("ProfileState.return_to_map", source)
            self.assertIn("hover:opacity-90", source)
            self.assertIn("focus-visible:outline-2", source)
        css = inspect.getsource(theme_overrides)
        self.assertIn(":not(.gah-brand-home)", css)
        self.assertIn("button.gah-brand-home", css)
        self.assertIn("box-shadow: none !important", css)

    def test_component_compilation(self):
        for factory in (
            profile_tabs.profile_screen,
            membership_info.membership_information_section,
            policy_screens.policy_overlay,
            header.minimal_header,
            header.header,
            index,
        ):
            with self.subTest(component=factory.__name__):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


class AvatarUploadErrorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.state = SimpleNamespace(
            avatar_busy=False,
            avatar_error="",
            avatar_path="existing.webp",
            success="",
            get_state=AsyncMock(
                return_value=SimpleNamespace(
                    subscriber_id="42", is_signed_in=True
                )
            ),
        )
        self.storage = self.enterContext(
            patch("app.states.profile_state.rx.get_upload_dir")
        )
        self.database = self.enterContext(
            patch("app.states.profile_state.rx.asession")
        )
        self.processing = self.enterContext(
            patch("app.states.profile_state.process_avatar_bytes")
        )

    def assert_safe_rejection(self, result):
        self.assertIsNone(result)
        self.assertIs(self.state.avatar_busy, False)
        self.assertEqual(
            self.state.avatar_error,
            "Use a static JPEG/JPG, PNG or WebP photo no larger than 3 MB. No video.",
        )
        self.assertEqual(self.state.avatar_path, "existing.webp")
        self.assertEqual(self.state.success, "")
        self.state.get_state.assert_awaited_once_with(AuthState)
        self.processing.assert_not_called()
        self.storage.assert_not_called()
        self.database.assert_not_called()

    async def test_oversized_avatar_rejected_without_read_or_error_log(self):
        upload = SimpleNamespace(
            name="large-avatar.jpg",
            content_type="image/jpeg",
            size=3_000_001,
            read=AsyncMock(return_value=b""),
        )
        with self.assertNoLogs(level=logging.ERROR):
            result = await ProfileState.handle_avatar_upload.fn(
                self.state, [upload]
            )
        self.assert_safe_rejection(result)
        self.assertNotIn("Source photo exceeds 3 MB", self.state.avatar_error)
        upload.read.assert_not_called()
        upload.read.assert_not_awaited()

    async def test_unexpected_avatar_read_failure_logs_traceback(self):
        failure = OSError("internal upload read failure sentinel")
        upload = SimpleNamespace(
            name="avatar.jpg",
            content_type="image/jpeg",
            size=100,
            read=AsyncMock(side_effect=failure),
        )
        with self.assertLogs(level=logging.ERROR) as captured:
            result = await ProfileState.handle_avatar_upload.fn(
                self.state, [upload]
            )
        self.assert_safe_rejection(result)
        self.assertNotIn(str(failure), self.state.avatar_error)
        upload.read.assert_awaited_once_with(3_000_001)
        self.assertTrue(
            any(
                record.levelno >= logging.ERROR
                and record.exc_info
                and record.exc_info[1] is failure
                and record.exc_info[2] is not None
                for record in captured.records
            )
        )


if __name__ == "__main__":
    unittest.main()
