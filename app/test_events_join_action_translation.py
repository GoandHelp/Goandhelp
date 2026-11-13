from collections import Counter
from string import Formatter
import unittest

from app.interface_catalog_events import EVENT_TRANSLATIONS
from app.interface_catalog_events_join_actions import (
    EVENT_JOIN_ACTION_KEYS,
    EVENT_JOIN_ACTION_LOCALES,
    EVENT_JOIN_ACTION_ROWS,
    EVENT_JOIN_ACTION_TRANSLATIONS,
)
from app.interface_i18n import CATALOGS, translate
from app.models import LANGUAGE_OPTIONS


EXPECTED_SOURCES = (
    "{count} request to review",
    "{count} requests to review",
    "Open event {title}",
    "Ask to join {title}",
    "Withdraw your request to join {title}",
    "Confirm {name} for this event",
    "Decline {name} for this event",
    "Remove {name} from this event",
    "Reward / what is provided: {details}",
    "Please sign in to plan an event.",
    "Please sign in to see community events.",
    "Please sign in to ask to join an event.",
    "That event is no longer open.",
    "This event is full. There is no waiting list.",
    "You are hosting this event already.",
    "This event is not available to you.",
    "You already asked to join this event.",
    "Your request is with the host — you will hear back soon.",
    "Request sent to the host.",
    "Please sign in first.",
    "Your request was withdrawn.",
    "There is no pending request to withdraw.",
    "Attendee confirmed.",
    "Request declined.",
)


class EventsJoinActionTranslationTests(unittest.TestCase):
    def test_exact_sources_and_locale_coverage(self):
        offered_non_english = {
            code for code, _label in LANGUAGE_OPTIONS if code != "en"
        }
        self.assertEqual(EVENT_JOIN_ACTION_KEYS, EXPECTED_SOURCES)
        self.assertEqual(len(EVENT_JOIN_ACTION_KEYS), 24)
        self.assertEqual(len(set(EVENT_JOIN_ACTION_KEYS)), 24)
        self.assertEqual(len(offered_non_english), 36)
        self.assertEqual(
            EVENT_JOIN_ACTION_LOCALES, offered_non_english | {"ha"}
        )
        self.assertEqual(set(EVENT_JOIN_ACTION_ROWS), EVENT_JOIN_ACTION_LOCALES)
        self.assertEqual(
            set(EVENT_JOIN_ACTION_TRANSLATIONS), EVENT_JOIN_ACTION_LOCALES
        )

    def test_every_locale_has_all_exact_authored_phrases_merged(self):
        for locale in EVENT_JOIN_ACTION_LOCALES:
            with self.subTest(locale=locale):
                entries = EVENT_JOIN_ACTION_TRANSLATIONS[locale]
                self.assertEqual(set(entries), set(EVENT_JOIN_ACTION_KEYS))
                self.assertEqual(
                    len(EVENT_JOIN_ACTION_ROWS[locale].split("|")), 24
                )
                for source in EVENT_JOIN_ACTION_KEYS:
                    value = entries[source]
                    self.assertTrue(value.strip(), source)
                    self.assertNotEqual(value, source)
                    self.assertNotIn(
                        value,
                        {
                            "Events",
                            "Requests",
                            "Cancel",
                            "Description",
                            "Rewards",
                            "Sign in",
                        },
                    )
                    self.assertNotIn("\\ufffd", value)
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                    self.assertEqual(EVENT_TRANSLATIONS[locale][source], value)
                    self.assertEqual(CATALOGS[locale][source], value)
                    self.assertEqual(translate(locale, source), value)

    def test_named_slots_and_multiplicities_are_preserved(self):
        formatter = Formatter()
        parameterized = (
            "{count} request to review",
            "{count} requests to review",
            "Open event {title}",
            "Ask to join {title}",
            "Withdraw your request to join {title}",
            "Confirm {name} for this event",
            "Decline {name} for this event",
            "Remove {name} from this event",
            "Reward / what is provided: {details}",
        )
        substitutions = {
            "count": "17",
            "title": "Member's event {original}",
            "name": "Maya De Silva",
            "details": "tea and lunch {unchanged}",
        }
        for locale in EVENT_JOIN_ACTION_LOCALES:
            for source in parameterized:
                localized = EVENT_JOIN_ACTION_TRANSLATIONS[locale][source]
                expected = Counter(
                    field for _, field, _, _ in formatter.parse(source) if field
                )
                actual = Counter(
                    field
                    for _, field, _, _ in formatter.parse(localized)
                    if field
                )
                self.assertEqual(actual, expected, (locale, source))
                result = localized.format(**substitutions)
                for field in expected:
                    self.assertIn(substitutions[field], result)

    def test_shared_reward_context_keys_remain_untouched(self):
        shared_values = {
            "am": ("ገንዘብ", "ሌላ", "መሪ ጉብኝት"),
            "fr": ("Argent", "Autre", "Visite guidée"),
            "ha": ("Kuɗi", "Sauran", "Yawon jagora"),
        }
        for locale, expected in shared_values.items():
            with self.subTest(locale=locale):
                self.assertEqual(
                    tuple(
                        EVENT_TRANSLATIONS[locale][key]
                        for key in ("Money", "Other", "Guided tour")
                    ),
                    expected,
                )
                self.assertNotIn(
                    "Money", EVENT_JOIN_ACTION_TRANSLATIONS[locale]
                )
                self.assertNotIn(
                    "Other", EVENT_JOIN_ACTION_TRANSLATIONS[locale]
                )
                self.assertNotIn(
                    "Guided tour", EVENT_JOIN_ACTION_TRANSLATIONS[locale]
                )

    def test_english_remains_the_source(self):
        for source in EVENT_JOIN_ACTION_KEYS:
            self.assertEqual(translate("en", source), source)


if __name__ == "__main__":
    unittest.main()
