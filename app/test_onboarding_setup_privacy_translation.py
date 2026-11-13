import re
import unicodedata
import unittest
from pathlib import Path

from app.interface_catalog_setup_privacy import (
    SETUP_PRIVACY_CATALOGS,
    SETUP_PRIVACY_KEYS,
    SETUP_PRIVACY_ROWS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS


class OnboardingSetupPrivacyTranslationTests(unittest.TestCase):
    def test_exact_sources_and_locale_coverage(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        expected_locales = offered | {"ha"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(len(SETUP_PRIVACY_KEYS), 26)
        self.assertEqual(len(set(SETUP_PRIVACY_KEYS)), 26)
        self.assertEqual(set(SETUP_PRIVACY_ROWS), expected_locales)
        self.assertEqual(set(SETUP_PRIVACY_CATALOGS), expected_locales)
        self.assertTrue(set(SETUP_PRIVACY_KEYS) <= set(COMPLETE_KEYS))

        for locale in expected_locales:
            with self.subTest(locale=locale):
                self.assertEqual(
                    set(SETUP_PRIVACY_CATALOGS[locale]),
                    set(SETUP_PRIVACY_KEYS),
                )
                self.assertEqual(
                    len(SETUP_PRIVACY_ROWS[locale].splitlines()), 26
                )
                for source in SETUP_PRIVACY_KEYS:
                    value = SETUP_PRIVACY_CATALOGS[locale][source]
                    self.assertTrue(value.strip(), source)
                    self.assertNotEqual(value, source)
                    self.assertNotIn("\ufffd", value)
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                    self.assertFalse(
                        value.startswith((f"[{locale}]", f"{locale}:"))
                    )
                    self.assertIn(source, CATALOGS[locale])
                    self.assertNotEqual(CATALOGS[locale][source], source)
                    self.assertEqual(translate("en", source), source)

    def test_username_constraints_and_privacy_distance_values_are_preserved(
        self,
    ):
        rules = (
            "3–30 lowercase letters, numbers, periods or underscores",
            "Use 3–30 lowercase letters, numbers, periods or underscores.",
        )
        distance = "When you request help, your location is shown approximately between 500m and 1km away from you."
        distance_units = {
            "am": ("ሜትር", "ኪ.ሜ."),
            "ar": ("م", "كم"),
            "bn": ("মিটার", "কিমি"),
            "my": ("မီတာ", "ကီလိုမီတာ"),
            "zh": ("米", "千米"),
            "cs": ("m", "km"),
            "da": ("m", "km"),
            "nl": ("m", "km"),
            "fi": ("metrin", "kilometrin"),
            "fr": ("m", "km"),
            "de": ("m", "km"),
            "el": ("μ.", "χλμ."),
            "gu": ("મીટર", "કિમી"),
            "ha": ("mita", "kilomita"),
            "he": ("מטר", "קילומטר"),
            "hi": ("मीटर", "किमी"),
            "hu": ("m", "km"),
            "id": ("m", "km"),
            "it": ("m", "km"),
            "ja": ("m", "km"),
            "kn": ("ಮೀಟರ್", "ಕಿಮೀ"),
            "ko": ("m", "km"),
            "ml": ("മീറ്റർ", "കിലോമീറ്റർ"),
            "mr": ("मीटर", "किमी"),
            "ne": ("मिटर", "किलोमिटर"),
            "fa": ("متر", "کیلومتر"),
            "pl": ("m", "km"),
            "pt": ("m", "km"),
            "ro": ("m", "km"),
            "es": ("m", "km"),
            "sw": ("mita", "kilomita"),
            "sv": ("m", "km"),
            "ta": ("மீட்டர்", "கிலோமீட்டர்"),
            "te": ("మీటర్", "కిలోమీటరు"),
            "th": ("เมตร", "กิโลเมตร"),
            "tr": ("m", "km"),
            "vi": ("m", "km"),
        }

        def normalize_decimal_digits(value):
            return "".join(
                str(unicodedata.decimal(character))
                if character.isdecimal()
                else character
                for character in value
            )

        for locale, entries in SETUP_PRIVACY_CATALOGS.items():
            with self.subTest(locale=locale):
                for source in rules:
                    digits = re.findall(
                        r"\d+", normalize_decimal_digits(entries[source])
                    )
                    self.assertIn("3", digits)
                    self.assertIn("30", digits)
                distance_text = entries[distance]
                distance_digits = re.findall(
                    r"\d+", normalize_decimal_digits(distance_text)
                )
                self.assertIn("500", distance_digits)
                if locale == "he":
                    self.assertIn("קילומטר אחד", distance_text)
                else:
                    self.assertIn("1", distance_digits)
                for unit in distance_units[locale]:
                    self.assertIn(unit, entries[distance])

    def test_earlier_explicit_setup_translations_are_preserved(self):
        preserved = {
            (
                "es",
                "3–30 lowercase letters, numbers, periods or underscores",
            ): "Entre 3 y 30 letras minúsculas, números, puntos o guiones bajos",
            (
                "es",
                "Select your Skills and Knowledge that you can help others with",
            ): "Selecciona las habilidades y conocimientos con los que puedes ayudar a otros",
            (
                "es",
                "Only a confirmed helper is shown your accurate job location",
            ): "Solo la persona confirmada para ayudarte ve la ubicación exacta de la tarea",
            ("fr", "Any more details?"): "D’autres précisions ?",
            (
                "de",
                "Choose your nationality:",
            ): "Wähle deine Staatsangehörigkeit:",
        }
        for (locale, source), value in preserved.items():
            with self.subTest(locale=locale, source=source):
                self.assertEqual(translate(locale, source), value)

    def test_privacy_meaning_fixtures(self):
        exact_location = (
            "Only a confirmed helper is shown your accurate job location"
        )
        helper_location = "As a helper, setting your location to 'Approximate' allows a helpee to send you direct help requests. Showing your location is not necessary for helping others."
        fixtures = {
            "es": (
                "Solo la persona que ha confirmado que te ayudará puede ver la ubicación exacta de la tarea.",
                "Como ayudante, configurar tu ubicación como «Aproximada» permite que quien necesita ayuda te envíe solicitudes directas. No hace falta mostrar tu ubicación para ayudar a otras personas.",
            ),
            "fr": (
                "Seule la personne qui vous aide et dont la candidature est confirmée voit l’emplacement exact de la tâche.",
                "En tant qu’aidant, choisir une position « approximative » permet à une personne aidée de vous envoyer des demandes directes. Il n’est pas nécessaire d’afficher votre position pour aider.",
            ),
            "ar": (
                "لا يظهر موقع المهمة الدقيق إلا للمساعد الذي تم تأكيده.",
                "بصفتك مساعدًا، يتيح ضبط موقعك على «تقريبي» لمتلقي المساعدة إرسال طلبات مباشرة إليك. لا يلزم إظهار موقعك لمساعدة الآخرين.",
            ),
            "zh": (
                "只有已确认的帮助者才能看到任务的准确位置。",
                "作为帮助者，将位置设为“近似”后，求助者便可直接向您发送帮助请求。帮助他人并不需要公开您的位置。",
            ),
            "hi": (
                "काम का सटीक स्थान केवल पुष्टि किया हुआ सहायक देख सकता है।",
                "सहायक के रूप में स्थान को ‘अनुमानित’ रखने से मदद पाने वाला आपको सीधे अनुरोध भेज सकता है। दूसरों की मदद करने के लिए अपना स्थान दिखाना ज़रूरी नहीं है।",
            ),
        }
        for locale, expected in fixtures.items():
            with self.subTest(locale=locale):
                self.assertEqual(
                    SETUP_PRIVACY_CATALOGS[locale][exact_location], expected[0]
                )
                self.assertEqual(
                    SETUP_PRIVACY_CATALOGS[locale][helper_location], expected[1]
                )

    def test_catalog_has_no_templates_or_generic_fallback_rows(self):
        for locale, entries in SETUP_PRIVACY_CATALOGS.items():
            for source, value in entries.items():
                self.assertNotIn("{", value, (locale, source))
                self.assertNotIn("}", value, (locale, source))
                self.assertNotIn("[", value, (locale, source))
                self.assertNotIn("TRANSLATE_ME", value, (locale, source))

    def test_celebration_uses_reactive_copy_and_onboarding_direction(self):
        source = Path("app/components/onboarding.py").read_text()
        celebration = source.split("def first_request_celebration()", 1)[1]
        self.assertIn(
            'ui(\n                        "Congratulations, your first help request is ready for the world"\n                    )',
            celebration,
        )
        self.assertIn("lang=AuthState.preferred_language", celebration)
        self.assertIn("dir=AuthState.interface_direction", celebration)
        self.assertIn(
            "ui(OnboardingState.username_feedback)",
            source,
        )
        self.assertIn("ui(OnboardingState.error)", source)

    def test_existing_source_validation_and_country_values_remain_unchanged(
        self,
    ):
        source = Path("app/states/onboarding_state.py").read_text()
        for unchanged in (
            're.fullmatch(r"[a-z0-9._]{3,30}", username)',
            '"Use 3–30 lowercase letters, numbers, periods or underscores."',
            '"That username is already taken."',
            '"Could not check your username. Try again."',
            '"Choose your nationality from the country list."',
            "value not in COUNTRY_OPTIONS",
        ):
            self.assertIn(unchanged, source)
        component_source = Path("app/components/onboarding.py").read_text()
        self.assertIn("rx.el.option(name, value=name", component_source)


if __name__ == "__main__":
    unittest.main()
