import reflex as rx

import ast
import inspect
import json
import string
from collections import Counter
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.components import advanced_filters, discover_panel, location_selection
from app.filter_categories import FILTER_CATEGORIES
from app.interface_catalog_search_filters import (
    SEARCH_FILTER_CATALOGS,
    SEARCH_FILTER_CONTROL_KEYS,
    SEARCH_FILTER_CONTROL_ROWS,
    SEARCH_FILTER_KEYS,
    SEARCH_FILTER_ROWS,
    SEARCH_FILTER_SUMMARY_KEYS,
    SEARCH_FILTER_SUMMARY_ROWS,
    SEARCH_FILTER_UI_KEYS,
    SEARCH_FILTER_UI_ROWS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template,
)
from app.scripts.capture_screenshots import BROWSER_ARGS, resolve_executable
from app.models import CATEGORY_LABELS, LANGUAGE_OPTIONS, TASK_CATEGORIES
from app.states.discovery_state import DiscoveryState, LANGUAGE_FILTER_CODES


class SearchFilterTranslationTests(unittest.TestCase):
    def test_exact_offered_locale_and_canonical_option_coverage(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(set(SEARCH_FILTER_CATALOGS), offered)
        self.assertNotIn("ha", SEARCH_FILTER_CATALOGS)
        self.assertEqual(len(SEARCH_FILTER_KEYS), len(set(SEARCH_FILTER_KEYS)))
        self.assertEqual(
            set(SEARCH_FILTER_KEYS[:24]),
            {"Events", *(CATEGORY_LABELS[value] for value in TASK_CATEGORIES)},
        )
        self.assertTrue(
            {
                "Any reward",
                "Money",
                "Lunch",
                "Dinner",
                "Accommodation",
                "Guided tours",
                "Workshops",
                "Lessons",
                "Other",
            }
            <= set(SEARCH_FILTER_KEYS)
        )
        self.assertEqual(
            {
                label
                for code, label in LANGUAGE_OPTIONS
                if code
                in {"en", "es", "fr", "pt", "de", "it", "ar", "hi", "zh", "ja"}
            },
            set(SEARCH_FILTER_KEYS[32:42]),
        )
        self.assertEqual(
            set(SEARCH_FILTER_KEYS[42:46]),
            {
                "Any time",
                "Online today",
                "Online this week",
                "Online this month",
            },
        )
        self.assertTrue(set(SEARCH_FILTER_KEYS) <= set(COMPLETE_KEYS))
        self.assertTrue(set(SEARCH_FILTER_UI_KEYS) <= set(COMPLETE_KEYS))
        self.assertTrue(set(SEARCH_FILTER_SUMMARY_KEYS) <= set(COMPLETE_KEYS))
        self.assertEqual(
            set(SEARCH_FILTER_KEYS),
            set(SEARCH_FILTER_CATALOGS["fr"]),
        )
        self.assertEqual(
            set(SEARCH_FILTER_KEYS),
            set(SEARCH_FILTER_CATALOGS["ar"]),
        )
        self.assertTrue(set(SEARCH_FILTER_CONTROL_KEYS) <= set(COMPLETE_KEYS))
        required_control_sources = (
            "Go — filter people requesting help and their jobs",
            "Get — filter people offering help",
            "Filter people requesting help, or people offering help",
            "Choose one or more search categories, including Events",
            "Search categories and Events",
            "Clear every selected category",
            "Distance in kilometres, zero means any distance",
            "Turn on your Approximate location first",
            "Show results on the map",
            "Show results as a list",
            "Switch between map view and list view",
            "Dismiss Search filters",
            "Filter by reward",
            "Subscribe to unlock the advanced help search options",
            "Filter by when a person was last online",
            "Minimum combined rating percentage",
            "Maximum combined rating percentage",
            "Filter by people who speak {language}",
            "Premium feature",
        )
        self.assertEqual(
            SEARCH_FILTER_CONTROL_KEYS[:19], required_control_sources
        )
        self.assertEqual(set(SEARCH_FILTER_CONTROL_ROWS), offered)
        for locale, row in SEARCH_FILTER_CONTROL_ROWS.items():
            self.assertEqual(
                len(row.split("|")), len(SEARCH_FILTER_CONTROL_KEYS), locale
            )
        for locale, entries in SEARCH_FILTER_CATALOGS.items():
            with self.subTest(locale=locale):
                self.assertEqual(set(entries), set(SEARCH_FILTER_KEYS))
                self.assertEqual(
                    set(entries),
                    set(CATALOGS[locale]) & set(SEARCH_FILTER_KEYS),
                )
                for source in SEARCH_FILTER_KEYS:
                    self.assertTrue(entries[source].strip())
                    self.assertTrue(CATALOGS[locale].get(source, "").strip())

    def test_rows_are_literal_and_template_slots_are_preserved(self):
        source = Path("app/interface_catalog_search_filters.py").read_text()
        tree = ast.parse(source)
        assignments: dict[str, ast.expr] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and value is not None:
                    assignments[target.id] = value
        for name, expected_rows in (
            ("SEARCH_FILTER_ROWS", SEARCH_FILTER_ROWS),
            ("SEARCH_FILTER_UI_ROWS", SEARCH_FILTER_UI_ROWS),
            ("SEARCH_FILTER_SUMMARY_ROWS", SEARCH_FILTER_SUMMARY_ROWS),
            ("SEARCH_FILTER_CONTROL_ROWS", SEARCH_FILTER_CONTROL_ROWS),
        ):
            with self.subTest(rows=name):
                self.assertEqual(
                    ast.literal_eval(assignments[name]), expected_rows
                )
        formatter = string.Formatter()
        for locale, entries in SEARCH_FILTER_CATALOGS.items():
            for source_key in SEARCH_FILTER_KEYS:
                expected = Counter(
                    name
                    for _, name, _, _ in formatter.parse(source_key)
                    if name
                )
                actual = Counter(
                    name
                    for _, name, _, _ in formatter.parse(entries[source_key])
                    if name
                )
                self.assertEqual(actual, expected, (locale, source_key))
            for source_key in SEARCH_FILTER_CONTROL_KEYS[:19]:
                value = entries[source_key]
                self.assertTrue(value.strip(), (locale, source_key))
                self.assertNotIn("todo", value.casefold(), (locale, source_key))
                self.assertNotEqual(value, source_key, (locale, source_key))
        member_value = "$& {$&} {value} Ålesund 日本"
        template_var = ui_template("Place: {value}", "value", member_value)
        serialized_template = str(template_var)
        self.assertIn('.split("{value}").join(', serialized_template)
        self.assertIn("$&", serialized_template)
        self.assertIn(r"\u00c5lesund", serialized_template)
        self.assertIn(r"\u65e5\u672c", serialized_template)
        self.assertNotIn('").replace(', serialized_template)
        self.assertNotIn("CODETEXT", serialized_template)

    def test_template_values_compile_as_expressions_for_static_and_reactive_keys(
        self,
    ):
        member_value = "$& {$&} {value} Ålesund 日本"
        rating_value = (
            f"{DiscoveryState.rating_min}–{DiscoveryState.rating_max}"
        )
        self.assertIsInstance(rating_value, str)
        self.assertIsInstance(DiscoveryState.city_filter, rx.Var)
        reactive_source = rx.cond(
            DiscoveryState.rating_min > 0,
            "Rating {value}%",
            "Place: {value}",
        )
        for source in ("Rating {value}%", reactive_source):
            for label, value in (
                ("literal", member_value),
                ("state_var", DiscoveryState.city_filter),
                ("encoded_fstring", rating_value),
            ):
                with self.subTest(source=str(source), value=label):
                    expression = ui_template(source, "value", value)
                    serialized = str(expression)
                    self.assertIsInstance(expression, rx.Var)
                    self.assertIs(expression._var_type, str)
                    self.assertIn(str(ui(source)), serialized)
                    template_data = ui(source)._get_all_var_data()
                    replacement_data = rx.Var.create(value)._get_all_var_data()
                    expression_data = expression._get_all_var_data()
                    self.assertIsNotNone(expression_data)
                    for dependency_data in (template_data, replacement_data):
                        if dependency_data is not None:
                            self.assertTrue(
                                set(dependency_data.hooks)
                                <= set(expression_data.hooks)
                            )
                    self.assertIn('.split("{value}").join(', serialized)
                    self.assertFalse(serialized.startswith('"'), serialized)
                    self.assertNotIn(".json(", serialized)
                    self.assertNotIn(".replace(", serialized)
                    self.assertNotIn(".replaceAll(", serialized)
                    self.assertNotIn("JSON.stringify", serialized)
                    self.assertNotIn("CODETEXT", serialized)
                    self.assertNotIn("<reflex.Var>", serialized)
                    self.assertTrue(rx.el.span(expression).render())
                    if label == "literal":
                        self.assertIn(
                            r'.join("$& {$&} {value} \u00c5lesund \u65e5\u672c")',
                            serialized,
                        )
                    elif label == "state_var":
                        self.assertIn(
                            f".join({DiscoveryState.city_filter!s})",
                            serialized,
                        )
                    else:
                        self.assertIn(
                            str(DiscoveryState.rating_min), serialized
                        )
                        self.assertIn(
                            str(DiscoveryState.rating_max), serialized
                        )
        helper_source = inspect.getsource(ui_template)
        for forbidden in (
            ".json(",
            ".replace(",
            ".replaceAll(",
            ".to_string(",
            "JSON.stringify",
            "CODETEXT",
        ):
            self.assertNotIn(forbidden, helper_source)
        helper_tree = ast.parse(helper_source)
        create_calls = [
            node
            for node in ast.walk(helper_tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.Var.create"
        ]
        self.assertEqual(len(create_calls), 1)
        self.assertEqual(len(create_calls[0].args), 1)
        self.assertEqual(ast.unparse(create_calls[0].args[0]), "value")
        self.assertFalse(create_calls[0].keywords)
        constructors = [
            node
            for node in ast.walk(helper_tree)
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "rx.Var"
        ]
        self.assertEqual(len(constructors), 1)
        constructor_keywords = {
            keyword.arg: keyword.value for keyword in constructors[0].keywords
        }
        self.assertIsInstance(constructor_keywords["_js_expr"], ast.JoinedStr)
        self.assertEqual(ast.unparse(constructor_keywords["_var_type"]), "str")
        self.assertEqual(ast.unparse(constructor_keywords["_var_data"]), "data")

    def test_template_browser_semantics_preserve_all_slots_and_literal_values(
        self,
    ):
        member_value = "$& {$&} {value} Ålesund 日本"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=resolve_executable(
                    playwright.chromium.executable_path
                ),
                headless=True,
                args=list(BROWSER_ARGS),
            )
            try:
                context = browser.new_context()
                try:
                    page = context.new_page()
                    self.assertEqual(page.url, "about:blank")
                    for locale in ("en", "fr", "ar"):
                        for source in (
                            "Place: {value}",
                            "{value} then {value}",
                            "No placeholder",
                        ):
                            with self.subTest(locale=locale, source=source):
                                expression = ui_template(
                                    source, "value", member_value
                                )
                                self.assertTrue(rx.el.span(expression).render())
                                localized = translate(locale, source)
                                compiled = str(expression).replace(
                                    str(ui(source)), json.dumps(localized)
                                )
                                actual = page.evaluate(
                                    "(expr)=>{const isTrue=(x)=>Boolean(x);return eval(expr)}",
                                    compiled,
                                )
                                self.assertEqual(
                                    actual,
                                    localized.replace("{value}", member_value),
                                )
                finally:
                    context.close()
            finally:
                browser.close()

    def test_affected_filter_components_render_with_reactive_rating_template(
        self,
    ):
        with self.subTest(component="advanced_controls"):
            self.assertTrue(advanced_filters.advanced_controls().render())
        with self.subTest(component="filter_drawer"):
            self.assertTrue(
                discover_panel.filter_drawer(
                    class_name="test-filter-drawer", compact=True
                ).render()
            )

    def test_summary_preserves_user_values_and_localizes_only_metadata(self):
        state = DiscoveryState(_reflex_internal_init=True)
        city = "Ålesund {clear}"
        nationality = "Clear categories 日本"
        state.category_filters = ["arts"]
        state.reward_filter = "lunch"
        state.city_filter = city
        state.nationality_filter = nationality
        state.language_filters = ["english"]
        state.rating_min = 15
        state.rating_max = 85
        items = state.active_filter_summary_items
        indexed = {item["source"]: item for item in items}
        self.assertEqual(indexed["Place: {value}"]["value"], city)
        self.assertEqual(state.city_filter, city)
        self.assertFalse(indexed["Place: {value}"]["localize_value"])
        self.assertEqual(indexed["Nationality: {value}"]["value"], nationality)
        self.assertFalse(indexed["Nationality: {value}"]["localize_value"])
        self.assertEqual(indexed["Category: {value}"]["value"], "Arts")
        self.assertTrue(indexed["Category: {value}"]["localize_value"])
        self.assertEqual(indexed["Reward: {value}"]["value"], "Lunch")
        self.assertEqual(indexed["Speaks {value}"]["value"], "English")
        self.assertEqual(indexed["Rating {value}%"]["value"], "15–85")
        self.assertEqual(
            state.active_filter_summary,
            [
                "Category: Arts",
                "Reward: Lunch",
                f"Place: {city}",
                "Rating 15–85%",
                f"Nationality: {nationality}",
                "Speaks English",
            ],
        )

    def test_filter_ui_uses_reactive_catalog_lookups_and_preserves_codes(self):
        filter_helpers = (
            discover_panel.option_item,
            discover_panel.sheet_mode_button,
            discover_panel.category_choice_row,
            discover_panel.category_multiselect,
            discover_panel.distance_filter_label,
            discover_panel.distance_filter_block,
            discover_panel.sheet_view_button,
            discover_panel.show_my_location_block,
            discover_panel.sheet_view_toggle,
            discover_panel.filter_dismiss_layer,
            discover_panel.filter_drawer,
            advanced_filters.small_label,
            advanced_filters.summary_chip,
            advanced_filters.localized_language_name,
            advanced_filters.language_chip,
            advanced_filters.subscribe_shield,
            advanced_filters.advanced_controls,
            advanced_filters.advanced_disclosure_bar,
            advanced_filters.advanced_filters_block,
            location_selection.location_tap,
            location_selection.location_selection,
        )
        sources = {inspect.getsource(helper) for helper in filter_helpers}
        ui_source_keys: set[str] = set()
        for helper_source in sources:
            helper_tree = ast.parse(helper_source)
            for call in ast.walk(helper_tree):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id in {"ui", "ui_template"}
                    and call.args
                    and isinstance(call.args[0], ast.Constant)
                    and isinstance(call.args[0].value, str)
                ):
                    ui_source_keys.add(call.args[0].value)
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertTrue(ui_source_keys)
        for locale in offered:
            with self.subTest(locale=locale):
                self.assertTrue(ui_source_keys <= set(CATALOGS[locale]))
        self.assertTrue(
            all(
                "ui(" in source or "ui_template(" in source
                for source in sources
            )
        )
        self.assertEqual(
            LANGUAGE_FILTER_CODES,
            [
                "english",
                "spanish",
                "french",
                "portuguese",
                "german",
                "italian",
                "arabic",
                "hindi",
                "chinese",
                "japanese",
            ],
        )
        self.assertIn(
            "DiscoveryState.toggle_language_filter(language)",
            inspect.getsource(advanced_filters.language_chip),
        )
        self.assertIn(
            "DiscoveryState.language_filters.contains(language)",
            inspect.getsource(advanced_filters.language_chip),
        )
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(
                __import__("app.interface_i18n", fromlist=["ui"]).ui
            ),
        )
        self.assertTrue(discover_panel.category_multiselect().render())
        self.assertTrue(discover_panel.distance_filter_block().render())
        self.assertTrue(advanced_filters.advanced_filters_block().render())
        self.assertTrue(location_selection.location_selection().render())

    def test_filter_taxonomy_and_sql_contracts_are_unchanged(self):
        state = DiscoveryState(_reflex_internal_init=True)
        self.assertEqual(
            [option["value"] for option in FILTER_CATEGORIES],
            [option["value"] for option in state.filter_category_options],
        )
        source = inspect.getsource(DiscoveryState._advanced_clause)
        for token in (
            "LAST_ONLINE_INTERVALS.get",
            ":rating_min",
            ":rating_max",
            ":nationality",
            "language_{index}",
        ):
            self.assertIn(token, source)
        self.assertEqual(
            [option["value"] for option in state.reward_filter_options],
            [
                "all",
                "money",
                "lunch",
                "dinner",
                "accommodation",
                "guided_tours",
                "workshops",
                "lessons",
                "other",
            ],
        )


if __name__ == "__main__":
    unittest.main()
