import reflex as rx

import ast
from pathlib import Path
from string import Formatter
import unittest

from app.interface_catalog_welcome import STORY_KEYS, STORY_CATALOGS
from app.interface_catalog_entry import ENTRY_KEYS, ENTRY_CATALOGS
from app.interface_catalog_confirmation import (
    CONFIRMATION_KEYS,
    CONFIRMATION_CATALOGS,
)
from app.interface_catalog_entry_feedback import (
    ENTRY_FEEDBACK_KEYS,
    ENTRY_FEEDBACK_CATALOGS,
)
from app.interface_catalog_entry_templates import (
    ENTRY_TEMPLATE_KEYS,
    ENTRY_TEMPLATE_CATALOGS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import (
    AuthState,
    CHECK_EMAIL_NOTE,
    UNVERIFIED_BYPASS_NOTE,
)


GROUPS = (
    (STORY_KEYS, STORY_CATALOGS),
    (ENTRY_KEYS, ENTRY_CATALOGS),
    (CONFIRMATION_KEYS, CONFIRMATION_CATALOGS),
    (ENTRY_FEEDBACK_KEYS, ENTRY_FEEDBACK_CATALOGS),
    (ENTRY_TEMPLATE_KEYS, ENTRY_TEMPLATE_CATALOGS),
)


class EntryTranslationCoverageTests(unittest.TestCase):
    def test_exact_keys_for_every_offered_non_english_locale(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(offered), 36)
        for keys, catalogs in GROUPS:
            self.assertEqual(len(keys), len(set(keys)))
            expected_locales = (
                offered | {"ha"}
                if catalogs is ENTRY_FEEDBACK_CATALOGS
                else offered
            )
            self.assertEqual(set(catalogs), expected_locales)
            self.assertTrue(set(keys) <= set(COMPLETE_KEYS))
            for code in expected_locales:
                with self.subTest(locale=code, group=keys[0]):
                    self.assertEqual(set(catalogs[code]), set(keys))
                    for key in keys:
                        value = catalogs[code][key]
                        self.assertTrue(value.strip(), key)
                        self.assertEqual(CATALOGS[code][key], value)
                        self.assertNotIn("\ufffd", value)
                        self.assertNotIn("TODO", value)
                        self.assertNotIn("TRANSLATE_ME", value)
                        self.assertFalse(
                            value.startswith((f"[{code}]", f"{code}:"))
                        )
                        # Natural borrowed short labels may coincide, not paragraphs.
                        if len(key) > 30:
                            self.assertNotEqual(value, key)
                        self.assertEqual(translate("en", key), key)

    def test_exact_story_and_safety_source_inventory(self):
        source = ast.parse(Path("app/states/onboarding_state.py").read_text())
        commitments = next(
            ast.literal_eval(node.value)
            for node in source.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SAFETY_COMMITMENTS"
        )
        topics = next(
            ast.literal_eval(node.value)
            for node in source.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PERMISSION_TOPICS"
        )
        for record in commitments:
            self.assertIn(record["title"], STORY_KEYS)
            self.assertIn(record["body"], STORY_KEYS)
        for record in topics:
            self.assertIn(record["title"], COMPLETE_KEYS)
            self.assertIn(record["body"], STORY_KEYS)
        tree = ast.parse(Path("app/components/onboarding.py").read_text())
        story = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "story_screen"
        )
        for node in ast.walk(story):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "copy_panel"
            ):
                self.assertIn(ast.literal_eval(node.args[0]), STORY_KEYS)

    def test_template_fields_exact_and_member_substitutions_untouched(self):
        formatter = Formatter()
        name = "ليلى {original} De Silva"
        email = "member+original@example.org"
        for code, _ in LANGUAGE_OPTIONS:
            for key in ENTRY_TEMPLATE_KEYS:
                expected = {
                    field for _, field, _, _ in formatter.parse(key) if field
                }
                localized = translate(code, key)
                actual = {
                    field
                    for _, field, _, _ in formatter.parse(localized)
                    if field
                }
                self.assertEqual(actual, expected, (code, key))
                formatted = localized.format(name=name, email=email)
                if "name" in expected:
                    self.assertIn(name, formatted)
                if "email" in expected:
                    self.assertIn(email, formatted)

    def test_success_switches_reactively_without_rewriting_sources(self):
        state = AuthState(_reflex_internal_init=True)
        state.display_name = "ليلى {original} De Silva"
        greeting = f"Good to see you again, {state.display_name}."
        state.success = f"{greeting} {UNVERIFIED_BYPASS_NOTE}"
        original = state.success
        for code, _ in LANGUAGE_OPTIONS:
            state.preferred_language = code
            expected = f"{translate(code, 'Good to see you again, {name}.').format(name=state.display_name)} {translate(code, UNVERIFIED_BYPASS_NOTE)}"
            self.assertEqual(state.localized_success, expected)
            self.assertEqual(state.success, original)
            self.assertEqual(state.display_name, "ليلى {original} De Silva")
        state.pending_email = "member+original@example.org"
        state.success = CHECK_EMAIL_NOTE.format(email=state.pending_email)
        for code, _ in LANGUAGE_OPTIONS:
            state.preferred_language = code
            self.assertEqual(
                state.localized_success,
                translate(code, CHECK_EMAIL_NOTE).format(
                    email=state.pending_email
                ),
            )
            self.assertEqual(state.pending_email, "member+original@example.org")

    def test_accessibility_titles_and_placeholders_are_not_raw_english(self):
        examples = {"", "you@example.com", "Maya", "De Silva", "••••••"}
        for name in (
            "onboarding",
            "auth_panel",
            "guest_map",
            "verification_notice",
            "verify_panel",
            "reset_password_panel",
        ):
            tree = ast.parse(Path(f"app/components/{name}.py").read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.keyword):
                    continue
                if (
                    node.arg in {"title", "aria_label", "placeholder"}
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    self.assertIn(
                        node.value.value,
                        examples,
                        (name, node.arg, node.value.value),
                    )

    def test_copy_wiring_and_original_matching_values(self):
        contracts = {
            "onboarding": (
                'ui(item["title"])',
                'ui(item["body"])',
                'ui("Close tour")',
                'ui("Hide the tour")',
            ),
            "auth_panel": (
                "AuthState.localized_success",
                "ui(AuthState.forgot_note)",
                'ui("Forgot password?")',
            ),
            "guest_map": (
                "ui(line)",
                "ui(GuestMapState.wall_reason)",
                "ui(GuestMapState.load_message)",
            ),
            "verification_notice": (
                "ui(RESEND_HELPER_TEXT)",
                "ui(button_label)",
                "ui(AuthState.resend_note)",
            ),
            "verify_panel": (
                "ui(VerifyState.headline)",
                "ui(VerifyState.detail)",
            ),
            "reset_password_panel": (
                "ui(PasswordResetState.error)",
                "ui(PasswordResetState.success)",
            ),
        }
        for name, fragments in contracts.items():
            source = Path(f"app/components/{name}.py").read_text()
            for fragment in fragments:
                self.assertIn(fragment, source)
        onboarding = Path("app/components/onboarding.py").read_text()
        self.assertIn("rx.el.option(name, value=name", onboarding)
        self.assertIn("OnboardingState.toggle_language(label)", onboarding)
        auth = Path("app/components/auth_panel.py").read_text()
        self.assertIn("value=item[0]", auth)
        self.assertIn('name="first_name"', auth)
        self.assertIn('name="terms_consent"', auth)
        self.assertIn('default_value="accepted"', auth)

    def test_entry_components_construct(self):
        from app.components.onboarding import permissions_screen, tour_controls
        from app.components.verification_notice import verification_notice
        from app.components.verify_panel import verify_panel
        from app.components.reset_password_panel import reset_password_panel
        from app.components.guest_map import sign_up_wall

        for component in (
            permissions_screen(),
            tour_controls(),
            verification_notice(),
            verify_panel(),
            reset_password_panel(),
            sign_up_wall(),
        ):
            self.assertIsInstance(component, rx.Component)
            self.assertIsInstance(component.render(), dict)

    def test_incomplete_notice_not_removed(self):
        notice = "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language."
        for path in (
            "app/components/onboarding.py",
            "app/components/profile_tabs.py",
        ):
            self.assertIn(notice, Path(path).read_text())
        for code, _ in LANGUAGE_OPTIONS:
            if code != "en":
                self.assertNotEqual(translate(code, notice), notice)


if __name__ == "__main__":
    unittest.main()
