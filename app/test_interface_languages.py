import reflex as rx

import json
import unittest
from pathlib import Path

from app.models import LANGUAGE_OPTIONS
from app.help_languages import LANGUAGE_CHOICES
from app.interface_i18n import CORE_KEYS, CATALOGS, catalog, translate
from app.states.onboarding_state import OnboardingState, TOTAL_STEPS


class InterfaceLanguageTests(unittest.TestCase):
    def test_exact_sorted_spoken_catalog_subset(self):
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        codes, names = zip(*LANGUAGE_OPTIONS)
        self.assertEqual(len(set(codes)), 37)
        self.assertEqual(len(set(names)), 37)
        self.assertEqual(list(names), sorted(names))
        spoken = {(row["code"], row["name"]) for row in LANGUAGE_CHOICES}
        self.assertTrue(set(LANGUAGE_OPTIONS) <= spoken)
        initial = {"en", "es", "fr", "pt", "de", "it", "ar", "hi", "zh", "ja"}
        self.assertTrue(initial <= set(codes))
        self.assertEqual(len(set(codes) - initial), 27)

    def test_every_non_english_choice_has_real_core_translations(self):
        for code, _ in LANGUAGE_OPTIONS:
            if code != "en":
                self.assertTrue(set(CORE_KEYS) <= set(CATALOGS[code]))
                self.assertNotEqual(translate(code, "Continue"), "Continue")
                self.assertNotEqual(
                    translate(code, "Welcome to Go and Help"),
                    "Welcome to Go and Help",
                )

    def test_fixed_copy_and_fallback(self):
        self.assertEqual(
            translate("es", "Choose your username:"),
            "Elige tu nombre de usuario:",
        )
        self.assertEqual(
            translate("es", "Job description"), "Descripción de la tarea"
        )
        self.assertEqual(translate("fr", "Requests"), "Demandes")
        self.assertEqual(translate("de", "Inbox"), "Posteingang")
        for code in ("en", "es", "unknown"):
            self.assertEqual(
                translate(code, "Untranslated fixed text"),
                "Untranslated fixed text",
            )
        first = catalog("es")
        first["Continue"] = "changed"
        self.assertEqual(translate("es", "Continue"), "Continuar")

    def test_answer_restoration_is_independent_of_matching(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._apply_answers(
            {
                "preferred_language": "fr",
                "interface_language_confirmed": True,
                "languages": ["Spanish"],
                "username": "tester",
            },
            {},
        )
        self.assertEqual(state.interface_language, "fr")
        self.assertEqual(state.languages, ["Spanish"])
        self.assertTrue(state.language_confirmed)
        payload = json.loads(json.dumps(state._answers()))
        self.assertEqual(payload["preferred_language"], "fr")
        self.assertTrue(payload["interface_language_confirmed"])
        state._apply_answers({"preferred_language": "invalid"}, {})
        self.assertEqual(state.interface_language, "en")
        self.assertEqual(TOTAL_STEPS, 13)

    def test_pre_screen_does_not_renumber_progress(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._apply_progress_row(
            (1, "", json.dumps({"setup_version": 3}), "{}", None, 0, None)
        )
        self.assertFalse(state.language_confirmed)
        state._apply_progress_row(
            (
                8,
                "1,2,3,4,5,6,7",
                json.dumps(
                    {
                        "setup_version": 3,
                        "username": "tester",
                        "home_country": "France",
                    }
                ),
                "{}",
                None,
                0,
                None,
            )
        )
        self.assertEqual(state.current_step, 8)
        self.assertTrue(state.language_confirmed)

    def test_persistence_and_render_contracts(self):
        auth = Path("app/states/auth_state.py").read_text()
        self.assertIn('name="goandhelp_interface_language"', auth)
        self.assertIn(
            "UPDATE skillkind_subscriber SET preferred_language", auth
        )
        self.assertIn('"preferred_language": language', auth)
        self.assertIn(
            "onboarding.interface_language = self.preferred_language", auth
        )
        onboarding = Path("app/components/onboarding.py").read_text()
        self.assertIn("interface_language_screen()", onboarding)
        self.assertIn(
            'language_control("onboarding-interface-language")', onboarding
        )
        self.assertNotIn(
            'language_control("onboarding-change-language")', onboarding
        )
        self.assertIn('ui(OnboardingState.screen["title"])', onboarding)
        self.assertIn("ui(OnboardingState.continue_label)", onboarding)
        self.assertIn(
            "ui(label)", Path("app/components/bottom_nav.py").read_text()
        )
        self.assertNotIn(
            '"translate": "yes"',
            Path("app/components/language_control.py").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
