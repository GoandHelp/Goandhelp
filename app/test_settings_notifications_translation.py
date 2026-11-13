import string
import unittest
from pathlib import Path

from app.field_requests import (
    FIELD_RADIUS,
    FIELD_SWITCH,
    field_preferences,
    validate_field_radius,
)
from app.interface_catalog_settings_notifications import (
    SETTINGS_NOTIFICATION_CATALOGS,
    SETTINGS_NOTIFICATION_KEYS,
    SETTINGS_NOTIFICATION_ROWS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS


class SettingsNotificationsTranslationTests(unittest.TestCase):
    def test_exact_sources_and_all_offered_locale_coverage(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        expected_locales = offered | {"ha"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(len(SETTINGS_NOTIFICATION_KEYS), 16)
        self.assertEqual(len(set(SETTINGS_NOTIFICATION_KEYS)), 16)
        self.assertEqual(set(SETTINGS_NOTIFICATION_ROWS), expected_locales)
        self.assertEqual(set(SETTINGS_NOTIFICATION_CATALOGS), expected_locales)
        self.assertTrue(set(SETTINGS_NOTIFICATION_KEYS) <= set(COMPLETE_KEYS))

        for locale in expected_locales:
            with self.subTest(locale=locale):
                catalog = SETTINGS_NOTIFICATION_CATALOGS[locale]
                self.assertEqual(set(catalog), set(SETTINGS_NOTIFICATION_KEYS))
                self.assertEqual(len(SETTINGS_NOTIFICATION_ROWS[locale]), 16)
                for source in SETTINGS_NOTIFICATION_KEYS:
                    value = catalog[source]
                    self.assertTrue(value.strip(), source)
                    self.assertNotIn("\ufffd", value)
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                    if source != "{radius} km":
                        self.assertNotEqual(value, source)
                    self.assertEqual(CATALOGS[locale][source], value)
                    self.assertEqual(translate("en", source), source)

    def test_named_slots_are_exactly_preserved(self):
        formatter = string.Formatter()
        templated = (
            "Notification radius: {radius} km",
            "{radius} kilometres",
            "{radius} km",
            "Dates are shown as {date}.",
        )
        for locale, catalog in SETTINGS_NOTIFICATION_CATALOGS.items():
            for source in templated:
                with self.subTest(locale=locale, source=source):
                    expected = {
                        name
                        for _, name, _, _ in formatter.parse(source)
                        if name
                    }
                    actual = {
                        name
                        for _, name, _, _ in formatter.parse(catalog[source])
                        if name
                    }
                    self.assertEqual(actual, expected)
        self.assertIn(
            "{radius}", SETTINGS_NOTIFICATION_CATALOGS["fr"]["{radius} km"]
        )
        self.assertEqual(
            SETTINGS_NOTIFICATION_CATALOGS["fr"]["{radius} km"], "{radius} km"
        )
        self.assertIn(
            "km",
            SETTINGS_NOTIFICATION_CATALOGS["fr"][
                "Notification radius: {radius} km"
            ],
        )

    def test_private_location_copy_does_not_require_map_visibility(self):
        source = (
            "New requests matching your saved skills and private location. "
            "Your location need not be visible on the map."
        )
        for locale, catalog in SETTINGS_NOTIFICATION_CATALOGS.items():
            with self.subTest(locale=locale):
                value = catalog[source]
                self.assertNotEqual(value, source)
                self.assertTrue(value.strip())
        semantic_fixtures = {
            "fr": "Votre position n’a pas besoin d’être visible sur la carte.",
            "de": "Dein Standort muss auf der Karte nicht sichtbar sein.",
            "es": "No es necesario que tu ubicación aparezca en el mapa.",
            "zh": "你的所在位置无需显示在地图上。",
            "ha": "Ba lallai wurinka ya bayyana a taswira ba.",
        }
        for locale, phrase in semantic_fixtures.items():
            with self.subTest(locale=locale):
                self.assertIn(
                    phrase, SETTINGS_NOTIFICATION_CATALOGS[locale][source]
                )

    def test_radius_bounds_and_existing_preference_contract_are_unchanged(self):
        self.assertEqual(FIELD_RADIUS, "requests_in_my_field_radius_km")
        self.assertEqual(FIELD_SWITCH, "notify_requests_in_my_field")
        self.assertEqual(validate_field_radius(1), 1)
        self.assertEqual(validate_field_radius(1000), 1000)
        for value in (0, 1001, 1.5, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_field_radius(value)
        self.assertEqual(field_preferences({}), (True, 20))
        self.assertEqual(
            field_preferences({FIELD_SWITCH: False, FIELD_RADIUS: 1000}),
            (False, 1000),
        )

        profile_state = Path("app/states/profile_state.py").read_text()
        for preserved in (
            "validate_field_radius(value)",
            "self.requests_in_my_field_radius_km = radius",
            "permissions[key] = not preferences[key]",
            '"Notification radius saved."',
            '"Notification preferences saved."',
            '"We couldn\'t save that change. Please try again."',
        ):
            self.assertIn(preserved, profile_state)
        self.assertIn("FIELD_RADIUS", profile_state)
        self.assertNotIn(
            "show_location",
            profile_state.split("def load_notification_preferences", 1)[
                1
            ].split("def set_field_request_radius", 1)[0],
        )

    def test_settings_rendering_translates_only_fixed_ui_copy(self):
        source = Path("app/components/profile_tabs.py").read_text()
        notification_switch = source.split("def notification_switch(", 1)[
            1
        ].split("def notification_settings(", 1)[0]
        notification_settings = source.split("def notification_settings(", 1)[
            1
        ].split("def settings_content(", 1)[0]
        settings_content = source.split("def settings_content(", 1)[1].split(
            "def blocked_member_row(", 1
        )[0]
        phone_notice = source.split("def phone_privacy_notice(", 1)[1].split(
            "def save_changes_button(", 1
        )[0]

        self.assertIn("aria_label=ui(label)", notification_switch)
        self.assertIn("break-words", notification_switch)
        self.assertIn(
            '"Notification radius: {radius} km"', notification_settings
        )
        self.assertIn(
            '"Requests in my field notification radius in kilometres"',
            notification_settings,
        )
        self.assertIn('"{radius} kilometres"', notification_settings)
        self.assertIn(
            'ui_template("{radius} km", "radius", "1")', notification_settings
        )
        self.assertIn(
            'ui_template("{radius} km", "radius", "1000")',
            notification_settings,
        )
        self.assertRegex(
            notification_settings,
            r'\bui\(\s*"New requests matching your saved skills and private location\. Your location need not be visible on the map\."\s*\)',
        )
        self.assertIn(
            "ui(ProfileState.notification_preferences_notice)",
            notification_settings,
        )
        self.assertIn(
            "ui(ProfileState.notification_preferences_error)",
            notification_settings,
        )
        self.assertIn('"Dates are shown as {date}."', settings_content)
        self.assertIn(
            'ui("Your number is not shared with other users")', phone_notice
        )
        self.assertIn('min="1"', notification_settings)
        self.assertIn('max="1000"', notification_settings)
        self.assertIn('step="1"', notification_settings)
        self.assertIn(
            "ProfileState.toggle_notification_preference(key)",
            notification_switch,
        )
        self.assertIn(
            "ProfileState.set_field_request_radius.throttle(100)",
            notification_settings,
        )
        blocked_row = source.split("def blocked_member_row(", 1)[1].split(
            "def blocked_members_section(", 1
        )[0]
        application_card = source.split("def pending_application_card(", 1)[
            1
        ].split("def detail_line(", 1)[0]
        journal_row = source.split("def journal_row(", 1)[1].split(
            "def activity_tab(", 1
        )[0]
        self.assertNotIn('ui(member["name"])', blocked_row)
        self.assertNotIn('ui(app["helper_name"])', application_card)
        self.assertNotIn('ui(entry["title"])', journal_row)


if __name__ == "__main__":
    unittest.main()
