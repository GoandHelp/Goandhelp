import ast
import json
import re
import shutil
import subprocess
import unittest
import unicodedata
from collections import Counter
from pathlib import Path

import reflex as rx

from app.components.help_hub_feedback import (
    _MISSING_FIELD_LABELS,
    localized_missing_field,
    localized_request_error,
    localized_request_success,
)
from app.components.help_hub_panel import post_help_form, post_help_section
from app.interface_catalog_help_hub_feedback import (
    HELP_HUB_FEEDBACK_CATALOGS,
    HELP_HUB_FEEDBACK_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.help_hub_state import HelpHubState


OWNED_ERROR_SOURCES = (
    *HELP_HUB_FEEDBACK_KEYS[:25],
    "Your session expired — please sign in again.",
    "Pick at least one category so helpers know what kind of task this is.",
    "Number of people required must be a whole number from 1 to 500.",
)
MONEY_SOURCES = HELP_HUB_FEEDBACK_KEYS[25:27]
SUCCESS_SOURCE = HELP_HUB_FEEDBACK_KEYS[27]


class HelpHubFeedbackTranslationTests(unittest.TestCase):
    def test_catalogs_are_literal_complete_native_rows_with_safe_slots(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(HELP_HUB_FEEDBACK_KEYS), 29)
        self.assertEqual(len(set(HELP_HUB_FEEDBACK_KEYS)), 29)
        self.assertEqual(set(HELP_HUB_FEEDBACK_CATALOGS), locales)
        self.assertTrue(set(HELP_HUB_FEEDBACK_KEYS) <= set(COMPLETE_KEYS))
        for locale in locales:
            catalog = HELP_HUB_FEEDBACK_CATALOGS[locale]
            self.assertEqual(set(catalog), set(HELP_HUB_FEEDBACK_KEYS), locale)
            for source in HELP_HUB_FEEDBACK_KEYS:
                value = catalog[source]
                self.assertTrue(value.strip(), (locale, source))
                self.assertNotEqual(value, source, (locale, source))
                self.assertEqual(
                    Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)),
                    Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", value)),
                    (locale, source),
                )
                self.assertIn(source, CATALOGS[locale], (locale, source))
                self.assertEqual(
                    translate(locale, source), CATALOGS[locale][source]
                )
                if source == HELP_HUB_FEEDBACK_KEYS[28]:
                    self.assertEqual(CATALOGS[locale][source], value)
                self.assertTrue(CATALOGS[locale][source].strip())
                self.assertNotEqual(CATALOGS[locale][source], source)
        for source in HELP_HUB_FEEDBACK_KEYS:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unsupported", source), source)

    def test_existing_missing_field_labels_and_feedback_are_preserved(self):
        self.assertEqual(
            _MISSING_FIELD_LABELS,
            (
                "Job title",
                "Job description",
                "Job category",
                "Date",
                "Address",
                "City",
                "Country",
                "Rewards",
                "Number of nights",
                "Guided tour details",
                "Activity details",
                "Other reward details",
                "Enter your budget",
            ),
        )
        for locale, _label in LANGUAGE_OPTIONS:
            for source in _MISSING_FIELD_LABELS:
                self.assertTrue(CATALOGS[locale][source], (locale, source))
                self.assertEqual(
                    translate(locale, source), CATALOGS[locale][source]
                )
            for source in OWNED_ERROR_SOURCES[25:]:
                self.assertTrue(CATALOGS[locale][source], (locale, source))

    def test_amharic_feedback_uses_ethiopic_script(self):
        amharic = HELP_HUB_FEEDBACK_CATALOGS["am"]
        for source, value in amharic.items():
            without_slots = re.sub(r"\{[A-Za-z][A-Za-z0-9_]*\}", "", value)
            without_technical = re.sub(r"USD|[0-9.,–—+ ]", "", without_slots)
            for character in without_technical:
                if character.isalpha():
                    self.assertTrue(
                        unicodedata.name(character, "").startswith("ETHIOPIC"),
                        (source, character, unicodedata.name(character, "")),
                    )
        self.assertIn("ከ0.01 እስከ 99999999.99", amharic[MONEY_SOURCES[1]])

    def test_translated_constraints_retain_original_meanings(self):
        duration = HELP_HUB_FEEDBACK_CATALOGS["fr"][HELP_HUB_FEEDBACK_KEYS[11]]
        self.assertIn("0–10", duration)
        self.assertIn("5", duration)
        self.assertIn("1 à 7", duration)
        arabic_budget = HELP_HUB_FEEDBACK_CATALOGS["ar"][MONEY_SOURCES[1]]
        self.assertIn("0.01", arabic_budget)
        self.assertIn("99999999.99", arabic_budget)
        japanese_title = HELP_HUB_FEEDBACK_CATALOGS["ja"][
            HELP_HUB_FEEDBACK_KEYS[12]
        ]
        self.assertIn("4", japanese_title)
        self.assertIn("文字", japanese_title)
        indonesian_photo = HELP_HUB_FEEDBACK_CATALOGS["id"][
            HELP_HUB_FEEDBACK_KEYS[19]
        ]
        self.assertIn("lima", indonesian_photo)

    def test_actual_request_forms_still_render_and_keep_field_names(self):
        components = (post_help_form(), post_help_section())
        self.assertTrue(all(component is not None for component in components))
        panel_path = Path("app/components/help_hub_panel.py")
        tree = ast.parse(panel_path.read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertIn(
            "localized_missing_field", ast.unparse(functions["post_help_form"])
        )
        section_source = ast.unparse(functions["post_help_section"])
        self.assertIn("localized_request_error", section_source)
        self.assertIn("localized_request_success", section_source)
        names: set[str] = set()
        for node in ast.walk(functions["post_help_form"]):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "name" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        names.add(str(keyword.value.value))
        self.assertTrue(
            {
                "title",
                "description",
                "address",
                "city",
                "country",
                "money_budget",
                "accommodation_nights",
                "guided_tour_details",
                "activity_details",
                "other_reward_details",
            }
            <= names
        )

    def test_creation_validation_and_transaction_sources_are_unchanged(self):
        state_path = Path("app/states/help_hub_state.py")
        tree = ast.parse(state_path.read_text(encoding="utf-8"))
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "create_help_request"
        )
        source = ast.get_source_segment(
            state_path.read_text(encoding="utf-8"), method
        )
        for message in HELP_HUB_FEEDBACK_KEYS[:25]:
            self.assertIn(message, source)
        self.assertIn("async with asession.begin()", source)
        self.assertIn("notify_field_helpers", source)
        self.assertIn("help_post_photo", source)
        self.assertIn("notification_language", source)
        self.assertIn(
            'translate(notification_language, "Help request posted.")', source
        )
        self.assertNotIn("httpx", source)
        self.assertNotIn("requests.", source)
        self.assertEqual(HelpHubState._money_details.__name__, "_money_details")

    def test_creation_success_toast_uses_locale_after_commit_without_side_effects(
        self,
    ):
        state_path = Path("app/states/help_hub_state.py")
        tree = ast.parse(state_path.read_text(encoding="utf-8"))
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "create_help_request"
        )
        transactions = [
            node
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "begin"
        ]
        toast = next(
            node
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "toast"
        )
        self.assertTrue(transactions)
        self.assertEqual(
            ast.unparse(toast.args[0]),
            'translate(notification_language, "Help request posted.")',
        )
        self.assertTrue(
            any(
                isinstance(node, ast.Attribute)
                and node.attr == "preferred_language"
                for node in ast.walk(method)
            )
        )
        self.assertEqual(
            next(
                keyword.value.value
                for keyword in toast.keywords
                if keyword.arg == "duration"
            ),
            4000,
        )
        method_source = ast.get_source_segment(
            state_path.read_text(encoding="utf-8"), method
        )
        self.assertLess(
            method_source.index("async with asession.begin()"),
            method_source.index(
                'translate(notification_language, "Help request posted.")'
            ),
        )
        self.assertEqual(
            method_source.count("yield HelpHubState.load_help_hub"), 1
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_compiled_helpers_translate_owned_copy_and_preserve_dynamic_text(
        self,
    ):
        locales = [code for code, _label in LANGUAGE_OPTIONS]
        fixtures: list[dict[str, str]] = []
        self.assertIn(
            str(AuthState.interface_text),
            str(localized_request_error(OWNED_ERROR_SOURCES[0])),
        )
        self.assertIn(
            str(AuthState.interface_text),
            str(localized_missing_field(_MISSING_FIELD_LABELS[0])),
        )
        self.assertIn(
            str(AuthState.interface_text),
            str(
                localized_request_success(
                    '"A title" is live — helpers nearby can offer their hands now.'
                )
            ),
        )
        catalog_before = dict(CATALOGS["fr"])
        for locale in locales:
            errors = (*OWNED_ERROR_SOURCES, *MONEY_SOURCES)
            for source in errors:
                expected = translate(locale, source)
                expression = self._localized_expression(
                    localized_request_error(source), locale
                )
                fixtures.append(
                    {"expression": expression, "expected": expected}
                )
            for template in MONEY_SOURCES:
                for currency in ("USD", "EUR", "JPY"):
                    source = template.format(currency=currency)
                    expected = translate(locale, template).replace(
                        "{currency}", currency
                    )
                    expression = self._localized_expression(
                        localized_request_error(source), locale
                    )
                    fixtures.append(
                        {"expression": expression, "expected": expected}
                    )
            for label in _MISSING_FIELD_LABELS:
                expression = self._localized_expression(
                    localized_missing_field(label), locale
                )
                fixtures.append(
                    {
                        "expression": expression,
                        "expected": translate(locale, label),
                    }
                )
            for title in (
                "Local help request",
                'line one\nline "two" — 你好 $& $1 {title} {currency} Cancel Delete',
            ):
                source = f'"{title}" is live — helpers nearby can offer their hands now.'
                expected = translate(locale, SUCCESS_SOURCE).replace(
                    "{title}", title
                )
                expression = self._localized_expression(
                    localized_request_success(source), locale
                )
                fixtures.append(
                    {"expression": expression, "expected": expected}
                )
            for source in (
                "",
                "member-authored error: Cancel Delete",
                "Enter your budget in usd with at most two decimal places, or allow a Helper quote.",
                "Enter your budget in USD with at most two decimal places, or allow a Helper quote!",
                "Cancel",
                "Delete",
                "__proto__",
            ):
                expression = self._localized_expression(
                    localized_request_error(source), locale
                )
                fixtures.append({"expression": expression, "expected": source})
                success_expression = self._localized_expression(
                    localized_request_success(source), locale
                )
                fixtures.append(
                    {"expression": success_expression, "expected": source}
                )
            for source in (
                "Cancel",
                "Delete",
                "member-authored field",
                "__proto__",
            ):
                expression = self._localized_expression(
                    localized_missing_field(source), locale
                )
                fixtures.append({"expression": expression, "expected": source})

        script = (
            "const items = JSON.parse(require('fs').readFileSync(0, 'utf8')); "
            "const failures = []; items.forEach((item, index) => { "
            "let value; try { value = eval(item.expression); } catch (error) { "
            "failures.push({index, error: String(error), expression: item.expression}); return; } "
            "if (value !== item.expected) failures.push({index, value, expected: item.expected, expression: item.expression}); }); "
            "if (failures.length) { console.error(JSON.stringify(failures.slice(0, 5))); process.exit(1); } "
            "console.log(items.length);"
        )
        result = subprocess.run(
            ["node", "-e", script],
            input=json.dumps(fixtures, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(int(result.stdout.strip()), len(fixtures))
        self.assertEqual(CATALOGS["fr"], catalog_before)

    @staticmethod
    def _localized_expression(value: rx.Var[str], locale: str) -> str:
        expression = str(value)
        translations = {
            source: translate(locale, source)
            for source in (
                *HELP_HUB_FEEDBACK_KEYS,
                *OWNED_ERROR_SOURCES[25:],
                *_MISSING_FIELD_LABELS,
            )
        }
        for source in sorted(translations, key=len, reverse=True):
            expression = expression.replace(
                str(ui(source)),
                json.dumps(translations[source], ensure_ascii=False),
            )
        return expression


if __name__ == "__main__":
    unittest.main()
