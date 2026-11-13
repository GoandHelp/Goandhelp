import unittest

from app.interface_catalog_tour import TOUR_COPY_CATALOGS, TOUR_COPY_KEYS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS
from app.states.onboarding_state import TOUR_STEPS


class GuidedTourTranslationTests(unittest.TestCase):
    def test_exact_static_catalog_coverage(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        expected_locales = offered | {"ha"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(len(TOUR_COPY_KEYS), 13)
        self.assertEqual(len(set(TOUR_COPY_KEYS)), 13)
        self.assertEqual(set(TOUR_COPY_CATALOGS), expected_locales)
        self.assertTrue(set(TOUR_COPY_KEYS) <= set(COMPLETE_KEYS))

        for locale in expected_locales:
            with self.subTest(locale=locale):
                entries = TOUR_COPY_CATALOGS[locale]
                self.assertEqual(set(entries), set(TOUR_COPY_KEYS))
                for source in TOUR_COPY_KEYS:
                    value = entries[source]
                    self.assertTrue(value.strip(), source)
                    self.assertNotEqual(value, source)
                    self.assertEqual(CATALOGS[locale][source], value)
                    self.assertEqual(translate(locale, source), value)
                    self.assertNotIn("\ufffd", value)
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                self.assertEqual(
                    entries["Your Profile"],
                    CATALOGS[locale]["Your Profile"],
                )

    def test_every_tour_title_and_body_has_a_translation_record(self):
        for step in TOUR_STEPS:
            self.assertIn(step["title"], COMPLETE_KEYS)
            self.assertIn(step["body"], COMPLETE_KEYS)
        for locale, _ in LANGUAGE_OPTIONS:
            if locale == "en":
                for step in TOUR_STEPS:
                    self.assertEqual(
                        translate(locale, step["title"]), step["title"]
                    )
                    self.assertEqual(
                        translate(locale, step["body"]), step["body"]
                    )
                continue
            with self.subTest(locale=locale):
                for step in TOUR_STEPS:
                    self.assertIn(step["title"], CATALOGS[locale])
                    self.assertIn(step["body"], CATALOGS[locale])
                    self.assertNotEqual(
                        translate(locale, step["title"]), step["title"]
                    )
                    self.assertNotEqual(
                        translate(locale, step["body"]), step["body"]
                    )

    def test_safety_meaning_retains_joint_confirmation_and_no_agreement(self):
        source = TOUR_COPY_KEYS[9]
        fixtures = {
            "es": (
                "confirmad juntos la tarea, la hora, el lugar y la recompensa",
                "Una oferta por sí sola no es un acuerdo.",
            ),
            "fr": (
                "confirmez ensemble la tâche, l’heure, le lieu et la récompense",
                "Une offre seule ne constitue pas un accord.",
            ),
            "de": (
                "gemeinsam Aufgabe, Zeit, Ort und Belohnung",
                "Ein Angebot allein ist keine Vereinbarung.",
            ),
            "ar": (
                "اتفقوا معًا على المهمة والوقت والمكان والمكافأة",
                "فالعرض وحده ليس اتفاقًا.",
            ),
            "zh": (
                "双方要共同确认任务、时间、地点和报酬",
                "单方面的提议并不构成约定。",
            ),
        }
        for locale, (confirmation, no_agreement) in fixtures.items():
            with self.subTest(locale=locale):
                value = TOUR_COPY_CATALOGS[locale][source]
                self.assertIn(confirmation, value)
                self.assertIn(no_agreement, value)

    def test_shared_profile_translation_and_tour_records_are_unchanged(self):
        shared_profile = {
            "my": "သင့်ကိုယ်ရေးအချက်အလက်",
            "ha": "Bayananka",
            "mr": "तुमचे प्रोफाइल",
        }
        for locale, value in shared_profile.items():
            self.assertEqual(translate(locale, "Your Profile"), value)
        self.assertEqual(
            [step["target"] for step in TOUR_STEPS],
            [
                "profile",
                "skills",
                "filters",
                "help",
                "inbox",
                "community-community",
                "community-events",
                "community-reviews",
            ],
        )


if __name__ == "__main__":
    unittest.main()
