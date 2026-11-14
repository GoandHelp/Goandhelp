import ast
import inspect
import unittest
from pathlib import Path

import reflex as rx

from app.components.admin_panel import empty_note, safety_table
from app.components.map_loading import map_loading_logo
from app.interface_catalog_admin_ui import ADMIN_UI_CATALOGS, ADMIN_UI_KEYS
from app.interface_catalog_map_status import (
    MAP_STATUS_CATALOGS,
    MAP_STATUS_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.interface_catalog_events import EVENT_KEYS
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState


class AdminMapTranslationTests(unittest.TestCase):
    def test_catalogs_cover_each_offered_non_english_locale_and_source(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(set(ADMIN_UI_CATALOGS), offered)
        self.assertEqual(set(MAP_STATUS_CATALOGS), offered)
        expected = set(ADMIN_UI_KEYS) | set(MAP_STATUS_KEYS)
        self.assertTrue(expected.issubset(set(COMPLETE_KEYS)))
        for locale in offered:
            self.assertEqual(set(ADMIN_UI_CATALOGS[locale]), set(ADMIN_UI_KEYS))
            self.assertEqual(
                set(MAP_STATUS_CATALOGS[locale]), set(MAP_STATUS_KEYS)
            )
            for source in expected:
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(CATALOGS[locale][source].strip())
                    self.assertNotEqual(CATALOGS[locale][source], source)
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )

    def test_event_manifest_retains_every_event_source(self):
        self.assertTrue(set(EVENT_KEYS).issubset(set(COMPLETE_KEYS)))

    def test_language_lookup_remains_hydrated_and_reactive(self):
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(ui),
        )
        auth_source = Path("app/states/auth_state.py").read_text()
        self.assertIn("return catalog(self.preferred_language)", auth_source)
        source = auth_source.split("async def update_language", 1)[1]
        self.assertIn("self.preferred_language = language", source)

    def test_admin_and_map_status_components_construct_with_localized_sources(
        self,
    ):
        for component in (empty_note(), safety_table(), map_loading_logo()):
            self.assertIsInstance(component, rx.Component)
        admin_source = Path("app/components/admin_panel.py").read_text()
        map_source = Path("app/components/map_loading.py").read_text()
        ui_keys = {
            node.args[0].value
            for node in ast.walk(ast.parse(admin_source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ui"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        self.assertTrue(set(ADMIN_UI_KEYS).issubset(ui_keys))
        self.assertIn('ui("Updating map…")', map_source)
        self.assertIn('aria_label=ui("Updating map")', map_source)

    def test_map_accessibility_label_and_visible_status_share_selected_language(
        self,
    ):
        component_source = inspect.getsource(map_loading_logo)
        self.assertIn('ui("Updating map…")', component_source)
        self.assertIn('aria_label=ui("Updating map")', component_source)
        for locale, _ in LANGUAGE_OPTIONS:
            text = translate(locale, "Updating map…")
            aria = translate(locale, "Updating map")
            self.assertTrue(text)
            self.assertTrue(aria)


if __name__ == "__main__":
    unittest.main()
