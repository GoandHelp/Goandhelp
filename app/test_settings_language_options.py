import ast
import inspect
import string
import unittest
from pathlib import Path

from test_utils import run_event

from app.components.profile_tabs import app_language_field
from app.interface_catalog_settings_extra_languages import (
    ADDITIONAL_SETTINGS_CATALOGS,
)
from app.interface_i18n import CORE_KEYS, CATALOGS, catalog, translate
from app.models import (
    LANGUAGE_CODES,
    LANGUAGE_LABELS,
    LANGUAGE_OPTIONS,
    SETTINGS_LANGUAGE_CODES,
    SETTINGS_LANGUAGE_LABELS,
    SETTINGS_LANGUAGE_OPTIONS,
)
from app.states.auth_state import AuthState
from app.states.onboarding_state import OnboardingState


class SettingsLanguageOptionTests(unittest.TestCase):
    def test_settings_registry_extends_without_changing_the_37_language_list(
        self,
    ):
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(LANGUAGE_CODES), 37)
        self.assertEqual(len(LANGUAGE_LABELS), 37)
        self.assertEqual(len(SETTINGS_LANGUAGE_OPTIONS), 39)
        self.assertEqual(len(set(SETTINGS_LANGUAGE_OPTIONS)), 39)
        self.assertEqual(
            SETTINGS_LANGUAGE_OPTIONS,
            sorted(SETTINGS_LANGUAGE_OPTIONS, key=lambda option: option[1]),
        )
        self.assertEqual(
            [
                option
                for option in SETTINGS_LANGUAGE_OPTIONS
                if option in LANGUAGE_OPTIONS
            ],
            LANGUAGE_OPTIONS,
        )
        self.assertEqual(SETTINGS_LANGUAGE_LABELS["ru"], "Russian")
        self.assertEqual(SETTINGS_LANGUAGE_LABELS["ur"], "Urdu")
        self.assertIn("ru", SETTINGS_LANGUAGE_CODES)
        self.assertIn("ur", SETTINGS_LANGUAGE_CODES)
        labels = dict(SETTINGS_LANGUAGE_OPTIONS)
        self.assertLess(labels["ro"], labels["ru"])
        self.assertLess(labels["ru"], labels["es"])
        self.assertLess(labels["tr"], labels["ur"])
        self.assertLess(labels["ur"], labels["vi"])

    def test_settings_picker_is_bound_to_the_extended_registry(self):
        picker = app_language_field()
        select = picker.children[1].children[1]
        self.assertEqual(select.id, "settings-interface-language")
        self.assertEqual(str(select.value), str(AuthState.preferred_language))
        self.assertEqual(str(select.disabled), str(AuthState.language_saving))
        self.assertIn(
            "app_language_option", inspect.getsource(app_language_field)
        )
        self.assertIn(
            "SETTINGS_LANGUAGE_OPTIONS", inspect.getsource(app_language_field)
        )
        self.assertIn(
            "AuthState.update_language", inspect.getsource(app_language_field)
        )
        self.assertTrue(select.children)

    def test_russian_and_urdu_catalog_entries_are_native_and_fallback_is_honest(
        self,
    ):
        self.assertEqual(len(CORE_KEYS), 32)
        for language in ("ru", "ur"):
            entries = ADDITIONAL_SETTINGS_CATALOGS[language]
            self.assertEqual(len(entries), len(CORE_KEYS) + 2)
            self.assertEqual(
                set(entries),
                set(CORE_KEYS)
                | {
                    "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language.",
                    "Could not save language. Please try again.",
                },
            )
            self.assertTrue(
                entries[
                    "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language."
                ]
            )
            self.assertTrue(
                entries["Could not save language. Please try again."]
            )
            self.assertTrue(all(value.strip() for value in entries.values()))
            for source, translated in entries.items():
                source_slots = {
                    field
                    for _, field, _, _ in string.Formatter().parse(source)
                    if field
                }
                translated_slots = {
                    field
                    for _, field, _, _ in string.Formatter().parse(translated)
                    if field
                }
                self.assertEqual(translated_slots, source_slots)
            copied = catalog(language)
            self.assertEqual(copied, entries)
            copied["Settings"] = "changed"
            self.assertNotEqual(catalog(language)["Settings"], "changed")
            self.assertEqual(
                translate(language, "Untranslated source"),
                "Untranslated source",
            )

        self.assertEqual(translate("ru", "Settings"), "Настройки")
        self.assertEqual(translate("ru", "App Language"), "Язык приложения")
        self.assertEqual(translate("ur", "Settings"), "ترتیبات")
        self.assertEqual(translate("ur", "App Language"), "ایپ کی زبان")
        self.assertEqual(translate("unknown", "Settings"), "Settings")
        self.assertEqual(
            translate("fr", "Settings"), CATALOGS["fr"]["Settings"]
        )

    def test_locale_label_and_direction_support(self):
        auth = AuthState(_reflex_internal_init=True)
        for language, label, direction in (
            ("ru", "Russian", "ltr"),
            ("ur", "Urdu", "rtl"),
            ("ar", "Arabic", "rtl"),
            ("he", "Hebrew", "rtl"),
            ("fa", "Persian", "rtl"),
        ):
            auth.preferred_language = language
            self.assertEqual(auth.language_label, label)
            self.assertEqual(auth.interface_direction, direction)

    def test_language_save_contract_keeps_existing_storage_paths(self):
        source = Path("app/states/auth_state.py").read_text()
        tree = ast.parse(source)
        update_language = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "update_language"
        )
        body = ast.unparse(update_language)
        self.assertIn("SETTINGS_LANGUAGE_CODES", body)
        self.assertIn("goandhelp_interface_language", source)
        self.assertIn("sync=True", source)
        self.assertIn(
            "UPDATE skillkind_subscriber SET preferred_language", body
        )
        self.assertIn("UPDATE skillkind_onboarding_progress", body)
        self.assertTrue(
            any(
                isinstance(key, ast.Constant)
                and key.value == "preferred_language"
                and isinstance(value, ast.Name)
                and value.id == "language"
                for node in ast.walk(update_language)
                if isinstance(node, ast.Dict)
                for key, value in zip(node.keys, node.values)
            )
        )
        self.assertIn("onboarding.interface_language = language", body)
        self.assertIn("self.preferred_language = previous", body)


class SettingsLanguageSaveEventTests(unittest.IsolatedAsyncioTestCase):
    async def test_register_rejects_missing_first_name_before_storage(self):
        root = OnboardingState(_reflex_internal_init=True)
        auth = await root.get_state(AuthState)
        await run_event(auth.register, {})
        self.assertEqual(auth.error, "Please add your first name.")
        self.assertEqual(auth.subscriber_id, "")

    async def test_update_language_runs_on_state_tree_without_database_writes(
        self,
    ):
        root = OnboardingState(_reflex_internal_init=True)
        auth = await root.get_state(AuthState)
        auth.subscriber_id = ""
        await run_event(auth.update_language, "ru")
        self.assertEqual(auth.preferred_language, "ru")
        self.assertEqual(root.interface_language, "ru")
        self.assertFalse(auth.language_saving)
        self.assertEqual(auth.language_error, "")
        self.assertEqual(auth.language_label, "Russian")

        await run_event(auth.update_language, "ur")
        self.assertEqual(auth.preferred_language, "ur")
        self.assertEqual(root.interface_language, "ur")
        self.assertEqual(auth.interface_direction, "rtl")
        self.assertFalse(auth.language_saving)

        await run_event(auth.update_language, "xx")
        self.assertEqual(auth.preferred_language, "ur")
        self.assertEqual(root.interface_language, "ur")
        self.assertFalse(auth.language_saving)


if __name__ == "__main__":
    unittest.main()
