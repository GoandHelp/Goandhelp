import unittest
from string import Formatter

from app.interface_catalog_events import EVENT_TRANSLATIONS
from app.interface_catalog_events_geolocation import (
    EVENT_GEOLOCATION_KEYS,
    EVENT_GEOLOCATION_LOCALES,
    EVENT_GEOLOCATION_ROWS,
    EVENT_GEOLOCATION_TRANSLATIONS,
    EXPECTED_EVENT_GEOLOCATION_LOCALES,
)
from app.models import LANGUAGE_OPTIONS


OFFERED_GEOLOCATION_LOCALES = {
    code for code, _label in LANGUAGE_OPTIONS if code != "en"
} | {"ha"}


class EventsGeolocationTranslationTests(unittest.TestCase):
    def test_exact_source_and_locale_coverage_is_merged(self):
        self.assertEqual(len(EVENT_GEOLOCATION_KEYS), 20)
        self.assertEqual(len(set(EVENT_GEOLOCATION_KEYS)), 20)
        self.assertEqual(
            EVENT_GEOLOCATION_LOCALES,
            OFFERED_GEOLOCATION_LOCALES,
        )
        self.assertEqual(
            EVENT_GEOLOCATION_LOCALES,
            EXPECTED_EVENT_GEOLOCATION_LOCALES,
        )
        self.assertEqual(
            set(EVENT_GEOLOCATION_ROWS), OFFERED_GEOLOCATION_LOCALES
        )
        self.assertEqual(
            set(EVENT_GEOLOCATION_TRANSLATIONS), OFFERED_GEOLOCATION_LOCALES
        )
        for locale, entries in EVENT_GEOLOCATION_TRANSLATIONS.items():
            with self.subTest(locale=locale):
                self.assertEqual(set(entries), set(EVENT_GEOLOCATION_KEYS))
                self.assertEqual(
                    len(EVENT_GEOLOCATION_ROWS[locale].split("|")),
                    len(EVENT_GEOLOCATION_KEYS),
                )
                self.assertEqual(
                    {key: entries[key] for key in EVENT_GEOLOCATION_KEYS},
                    {
                        key: EVENT_TRANSLATIONS[locale][key]
                        for key in EVENT_GEOLOCATION_KEYS
                    },
                )
                for source, translated in entries.items():
                    self.assertTrue(translated.strip(), source)
                    self.assertNotEqual(translated, source, source)
                    self.assertNotIn("TODO", translated)
                    self.assertNotIn("TRANSLATE_ME", translated)

    def test_placeholder_slot_and_occurrence_are_preserved(self):
        formatter = Formatter()
        for locale, entries in EVENT_GEOLOCATION_TRANSLATIONS.items():
            translated = entries[
                "Pin set from your browser (accuracy about {metres} m). Drag the pin or tap the map to fine-tune it."
            ]
            with self.subTest(locale=locale):
                source_slots = [
                    field
                    for _literal, field, _spec, _conversion in formatter.parse(
                        "Pin set from your browser (accuracy about {metres} m). Drag the pin or tap the map to fine-tune it."
                    )
                    if field
                ]
                translated_slots = [
                    field
                    for _literal, field, _spec, _conversion in formatter.parse(
                        translated
                    )
                    if field
                ]
                self.assertEqual(translated_slots, source_slots)
                self.assertIn("{metres}", translated)

    def test_private_exact_pin_and_public_approximate_area_stay_distinct(self):
        privacy_source = "Drag the pin or tap the map to place the exact point. It stays private: public maps only show an approximate area."
        fixtures = {
            "zh": ("精确", "私密", "公开地图", "大致区域"),
            "fr": ("point exact", "privé", "cartes publiques", "approximative"),
            "ha": ("ainihin", "na sirri", "taswirar jama'a", "kiyasta"),
            "am": ("ትክክለኛውን", "የግል", "የሕዝብ ካርታዎች", "ግምታዊ"),
        }
        for locale, required_phrases in fixtures.items():
            translated = EVENT_GEOLOCATION_TRANSLATIONS[locale][privacy_source]
            with self.subTest(locale=locale):
                for phrase in required_phrases:
                    self.assertIn(phrase, translated)

    def test_secure_context_and_permission_guidance_are_retained(self):
        secure_source = "This browser cannot share a location. Most browsers only allow it over a secure https:// address."
        permission_source = "Location permission was declined. Allow location for this site in your browser settings, then try again."
        for locale, entries in EVENT_GEOLOCATION_TRANSLATIONS.items():
            with self.subTest(locale=locale):
                self.assertIn("https://", entries[secure_source])
                self.assertTrue(
                    entries[permission_source].strip(),
                    (locale, permission_source),
                )
                self.assertNotEqual(
                    entries[permission_source], permission_source
                )


if __name__ == "__main__":
    unittest.main()
