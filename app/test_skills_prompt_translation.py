import ast
import inspect
import unittest
from pathlib import Path

from app.components.skills_prompt import skills_prompt
from app.interface_catalog_events import EVENT_KEYS
from app.interface_catalog_inbox_contacts import INBOX_CONTACT_KEYS
from app.interface_catalog_inbox_direct import INBOX_DIRECT_KEYS
from app.interface_catalog_inbox_feed import INBOX_FEED_KEYS
from app.interface_catalog_shared import SHARED_KEYS
from app.interface_catalog_shared_interface import SHARED_INTERFACE_KEYS
from app.interface_catalog_skills_prompt import (
    SKILLS_PROMPT_CATALOGS,
    SKILLS_PROMPT_KEYS,
    SKILLS_PROMPT_ROWS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState


class SkillsPromptTranslationTests(unittest.TestCase):
    def test_static_catalog_has_complete_locale_and_source_coverage(self):
        offered = {code for code, _label in LANGUAGE_OPTIONS}
        non_english = offered - {"en"}
        self.assertEqual(len(offered), 37)
        self.assertEqual(len(non_english), 36)
        self.assertEqual(set(SKILLS_PROMPT_ROWS), non_english)
        self.assertEqual(set(SKILLS_PROMPT_CATALOGS), non_english)
        self.assertEqual(len(SKILLS_PROMPT_KEYS), 3)
        self.assertEqual(len(set(SKILLS_PROMPT_KEYS)), 3)

        module = ast.parse(
            Path("app/interface_catalog_skills_prompt.py").read_text()
        )
        rows_node = next(
            node
            for node in module.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SKILLS_PROMPT_ROWS"
        )
        self.assertEqual(ast.literal_eval(rows_node.value), SKILLS_PROMPT_ROWS)
        self.assertIsInstance(rows_node.value, ast.Dict)
        self.assertTrue(
            all(
                isinstance(value, ast.Constant)
                for value in rows_node.value.values
            )
        )

        for locale in non_english:
            with self.subTest(locale=locale):
                self.assertEqual(
                    set(SKILLS_PROMPT_CATALOGS[locale]), set(SKILLS_PROMPT_KEYS)
                )
                self.assertEqual(len(SKILLS_PROMPT_ROWS[locale].split("|")), 3)
                for source in SKILLS_PROMPT_KEYS:
                    translated = SKILLS_PROMPT_CATALOGS[locale][source]
                    self.assertTrue(translated.strip())
                    self.assertNotEqual(translated, source)
                    self.assertEqual(CATALOGS[locale][source], translated)
                    self.assertEqual(translate(locale, source), translated)
                    self.assertEqual(translate("en", source), source)
                    self.assertEqual(
                        translate(locale, "Cancel"), CATALOGS[locale]["Cancel"]
                    )
                    self.assertNotEqual(CATALOGS[locale]["Cancel"], "Cancel")

    def test_catalog_integration_preserves_every_prior_group_and_existing_values(
        self,
    ):
        required_groups = (
            EVENT_KEYS,
            SHARED_KEYS,
            SHARED_INTERFACE_KEYS,
            INBOX_CONTACT_KEYS,
            INBOX_DIRECT_KEYS,
            INBOX_FEED_KEYS,
        )
        for keys in required_groups:
            with self.subTest(group=keys[0]):
                self.assertTrue(set(keys) <= set(COMPLETE_KEYS))
        self.assertTrue(set(SKILLS_PROMPT_KEYS) <= set(COMPLETE_KEYS))
        self.assertIn(
            "for _key, _value in _entries.items():\n            CATALOGS[_language].setdefault(_key, _value)",
            inspect.getsource(
                __import__("app.interface_i18n", fromlist=["ui"])
            ),
        )
        for locale in {
            code for code, _label in LANGUAGE_OPTIONS if code != "en"
        }:
            for keys in required_groups:
                self.assertTrue(set(keys) <= set(CATALOGS[locale]), locale)
            self.assertTrue(
                set(SKILLS_PROMPT_KEYS) <= set(CATALOGS[locale]), locale
            )

    def test_component_localizes_four_visible_strings_and_keeps_reactive_lookup(
        self,
    ):
        component = skills_prompt()
        self.assertTrue(component.render())
        rendered = str(component)
        component_source = inspect.getsource(skills_prompt)
        tree = ast.parse(component_source)
        localized_sources = {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ui"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        expected = {
            *SKILLS_PROMPT_KEYS,
            "Cancel",
        }
        self.assertEqual(localized_sources, expected)
        self.assertEqual(component_source.count("ui("), 4)
        for source in expected:
            with self.subTest(source=source):
                expression = ui(source)
                self.assertIsNotNone(expression._get_all_var_data())
                self.assertIn(str(expression), rendered)
        self.assertIn(
            f"{AuthState.__name__}.interface_text.get(source, source)",
            inspect.getsource(ui),
        )

    def test_profile_state_dialog_events_and_open_state_are_unchanged(self):
        state_source = inspect.getsource(ProfileState)
        self.assertIn("missing_skills_open: bool = False", state_source)
        self.assertIn(
            "self.missing_skills_open = False",
            inspect.getsource(ProfileState.close_missing_skills.fn),
        )
        open_source = inspect.getsource(ProfileState.open_required_skills.fn)
        self.assertIn("self.missing_skills_open = False", open_source)
        self.assertIn('self.active_tab = "profile"', open_source)
        self.assertIn("self.skills_open = True", open_source)

        component_source = inspect.getsource(skills_prompt)
        self.assertIn(
            "on_click=ProfileState.open_required_skills", component_source
        )
        self.assertIn(
            "on_click=ProfileState.close_missing_skills", component_source
        )
        self.assertIn("open=ProfileState.missing_skills_open", component_source)
        self.assertIn(
            "on_open_change=lambda opened: ProfileState.close_missing_skills()",
            component_source,
        )
        self.assertIn("dialog.title(", component_source)
        self.assertIn("dialog.description(", component_source)


if __name__ == "__main__":
    unittest.main()
