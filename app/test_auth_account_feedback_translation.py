import ast
import datetime
import re
import unittest
from collections import Counter
from pathlib import Path

import reflex as rx

from app.components.verify_panel import problem_actions
from app.interface_catalog_auth_feedback import (
    AUTH_FEEDBACK_CATALOGS,
    AUTH_FEEDBACK_KEYS,
    AUTH_FEEDBACK_ROWS,
    EXPECTED_AUTH_FEEDBACK_LOCALES,
)
from app.interface_catalog_welcome import STORY_CATALOGS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import (
    FAMILY_NAME_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    LANGUAGE_OPTIONS,
)
from app.states.auth_state import (
    LOCAL_PREVIEW_ONLY_NOTE,
    RESET_GENERIC_NOTE,
    AuthState,
    compose_display_name,
    normalized_name,
    parse_birth_parts,
    parse_date_of_birth,
)
from app.countries import (
    compose_phone,
    is_plausible_phone_number,
    national_digits,
)

ROOT = Path(__file__).parent


class AuthAccountFeedbackTranslationTests(unittest.TestCase):
    def test_static_catalog_has_exact_locales_keys_and_named_slots(self):
        catalog_path = ROOT / "interface_catalog_auth_feedback.py"
        tree = ast.parse(catalog_path.read_text())
        rows_node = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and getattr(node.target, "id", "") == "AUTH_FEEDBACK_ROWS"
        )
        self.assertEqual(ast.literal_eval(rows_node), AUTH_FEEDBACK_ROWS)
        offered = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(EXPECTED_AUTH_FEEDBACK_LOCALES, offered | {"ha"})
        self.assertEqual(set(AUTH_FEEDBACK_ROWS), offered | {"ha"})
        self.assertEqual(set(AUTH_FEEDBACK_CATALOGS), offered | {"ha"})
        self.assertEqual(len(AUTH_FEEDBACK_KEYS), 22)
        self.assertEqual(len(set(AUTH_FEEDBACK_KEYS)), 22)
        for locale, entries in AUTH_FEEDBACK_CATALOGS.items():
            with self.subTest(locale=locale):
                self.assertEqual(set(entries), set(AUTH_FEEDBACK_KEYS))
                for source, value in entries.items():
                    self.assertTrue(value.strip(), source)
                    self.assertNotEqual(value, source)
                    self.assertEqual(
                        Counter(re.findall(r"\{([^{}]+)\}", source)),
                        Counter(re.findall(r"\{([^{}]+)\}", value)),
                        source,
                    )
                    self.assertIn(source, COMPLETE_KEYS)
                    self.assertEqual(CATALOGS[locale][source], value)

    def test_story_catalogs_remain_authoritative_for_every_locale(self):
        self.assertEqual(len(STORY_CATALOGS), 36)
        for locale, entries in STORY_CATALOGS.items():
            with self.subTest(locale=locale):
                for source, value in entries.items():
                    self.assertEqual(CATALOGS[locale][source], value)

    def test_previous_account_feedback_keys_are_preserved_not_recreated(self):
        already_complete = (
            "Account created. Temporary access is active while email confirmation remains optional.",
            "That reset link is incomplete. Please request a new one from the sign-in panel.",
            "This reset link has already been used or has expired. Request a fresh one from the sign-in panel.",
        )
        for source in already_complete:
            with self.subTest(source=source):
                self.assertNotIn(source, AUTH_FEEDBACK_KEYS)
                for locale in EXPECTED_AUTH_FEEDBACK_LOCALES:
                    self.assertTrue(CATALOGS[locale][source].strip())
                    self.assertNotEqual(translate(locale, source), source)

    def test_error_translation_is_exact_and_keeps_original_validation_state(
        self,
    ):
        state = AuthState(_reflex_internal_init=True)
        state.preferred_language = "fr"
        state.error = (
            f"First name must be {FIRST_NAME_MAX_LENGTH} characters or fewer."
        )
        first_source = state.error
        self.assertEqual(
            state.localized_error,
            translate(
                "fr", "First name must be {limit} characters or fewer."
            ).format(limit=80),
        )
        self.assertEqual(state.error, first_source)
        state.error = (
            f"Family name must be {FAMILY_NAME_MAX_LENGTH} characters or fewer."
        )
        family_source = state.error
        self.assertEqual(
            state.localized_error,
            translate(
                "fr", "Family name must be {limit} characters or fewer."
            ).format(limit=80),
        )
        self.assertEqual(state.error, family_source)
        state.error = "We couldn't match that email and password."
        self.assertEqual(state.localized_error, translate("fr", state.error))
        state.error = "First name must be 79 characters or fewer."
        self.assertEqual(state.localized_error, state.error)
        self.assertEqual(
            (FIRST_NAME_MAX_LENGTH, FAMILY_NAME_MAX_LENGTH), (80, 80)
        )

    def test_preview_template_preserves_original_name_and_existing_successes(
        self,
    ):
        state = AuthState(_reflex_internal_init=True)
        state.display_name = "ليلى {QA}"
        state.email = "member@example.test"
        preview = (
            "Local preview only — signed in as "
            f"{state.display_name} without changing any account."
        )
        state.success = preview
        for locale, _label in LANGUAGE_OPTIONS:
            state.preferred_language = locale
            expected = translate(
                locale,
                "Local preview only — signed in as {name} without changing any account.",
            ).format(name="ليلى {QA}")
            with self.subTest(locale=locale):
                self.assertEqual(state.localized_success, expected)
                self.assertEqual(state.success, preview)
                self.assertEqual(state.display_name, "ليلى {QA}")
                self.assertEqual(state.email, "member@example.test")
        state.preferred_language = "es"
        state.success = "Good to see you again, ليلى {QA}."
        self.assertEqual(
            state.localized_success,
            translate("es", "Good to see you again, {name}.").format(
                name="ليلى {QA}"
            ),
        )
        state.success = "Account created. Temporary access is active while email confirmation remains optional."
        self.assertEqual(
            state.localized_success,
            translate("es", state.success),
        )

    def test_existing_birth_phone_and_name_validation_behavior_is_unchanged(
        self,
    ):
        self.assertEqual(
            parse_birth_parts("", "", ""),
            (None, "Please add your full date of birth."),
        )
        self.assertEqual(
            parse_birth_parts("x", "1", "1990"),
            (None, "Use numbers only for your date of birth."),
        )
        self.assertEqual(
            parse_birth_parts("31", "2", "1990"),
            (None, "That date of birth doesn't exist on the calendar."),
        )
        self.assertEqual(
            parse_birth_parts("1", "1", "90"),
            (None, "Enter your birth year as four digits."),
        )
        self.assertEqual(
            parse_date_of_birth(""), (None, "Please add your date of birth.")
        )
        self.assertEqual(
            parse_date_of_birth("not-a-date"),
            (None, "Enter your date of birth as YYYY-MM-DD."),
        )
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self.assertEqual(
            parse_date_of_birth(tomorrow.isoformat()),
            (None, "That date of birth is in the future."),
        )
        self.assertEqual(normalized_name("  Ana   María  "), "Ana María")
        self.assertEqual(compose_display_name("Ana", "María"), "Ana María")
        self.assertEqual(national_digits("(415) 555-0132"), "4155550132")
        self.assertTrue(is_plausible_phone_number("415-555-0132"))
        self.assertFalse(is_plausible_phone_number("123"))
        self.assertEqual(
            compose_phone("US:+1", "415-555-0132"), "+1 4155550132"
        )

    def test_feedback_events_localize_display_only_and_keep_generic_reset_reply(
        self,
    ):
        auth_tree = ast.parse((ROOT / "states/auth_state.py").read_text())
        functions = {
            node.name: node
            for node in ast.walk(auth_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        reset = ast.unparse(functions["request_password_reset"])
        preview = ast.unparse(functions["preview_as_local_member"])
        help_mode = ast.unparse(functions["update_help_mode"])
        self.assertIn(
            "self.forgot_note = RESET_THROTTLED_NOTE if throttled else RESET_GENERIC_NOTE",
            reset,
        )
        self.assertIn(
            "translate(self.preferred_language, RESET_GENERIC_NOTE)", reset
        )
        self.assertIn("rx.toast(notification, duration=6000)", reset)
        self.assertIn(
            "translate(self.preferred_language, LOCAL_PREVIEW_ONLY_NOTE)",
            preview,
        )
        self.assertIn(
            "Local preview only: production email verification is unchanged.",
            preview,
        )
        self.assertIn("translate(", preview)
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "translate"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "Participation mode updated."
                for node in ast.walk(functions["update_help_mode"])
            )
        )
        self.assertIn("rx.toast(notification, duration=2500)", help_mode)
        self.assertIn("if not is_local_host(router_url):", preview)
        self.assertIn(
            "SELECT id, email, display_name, phone, help_mode", preview
        )
        self.assertNotIn("INSERT INTO", preview.upper())
        self.assertNotIn("UPDATE ", preview.upper())
        self.assertNotIn("DELETE FROM", preview.upper())
        self.assertIn("await asession.execute", help_mode)
        self.assertEqual(
            RESET_GENERIC_NOTE,
            "If that email belongs to a Go and Help account, a password reset link is on its way. Check your inbox and spam folder.",
        )
        self.assertIn("RESET_GENERIC_NOTE", reset)
        self.assertNotIn(
            "translate(self.preferred_language, error_note)", reset
        )

    def test_verification_navigation_is_a_single_whole_phrase_lookup(self):
        source = (ROOT / "components/verify_panel.py").read_text()
        tree = ast.parse(source)
        function = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "problem_actions"
        )
        source_text = ast.unparse(function)
        self.assertIn("ui('Back to map')", source_text)
        self.assertNotIn("ui('Back')", source_text)
        self.assertNotIn("ui('Map')", source_text)
        self.assertIn("href='/'", source_text)
        self.assertIn("arrow-left", source_text)
        self.assertIn("Back to map", AUTH_FEEDBACK_KEYS)
        component = problem_actions()
        self.assertIsInstance(component, rx.Component)
        self.assertTrue(component.render())


if __name__ == "__main__":
    unittest.main()
