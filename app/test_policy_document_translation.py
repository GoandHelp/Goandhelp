import reflex as rx

import ast
import inspect
import json
import shutil
import subprocess
import unittest
from copy import deepcopy

from app.components.policy_screens import (
    policy_paragraph,
    policy_screen,
    policy_section,
)
from app.interface_i18n import COMPLETE_KEYS, catalog, translate, ui
from app.models import LANGUAGE_OPTIONS, SETTINGS_LANGUAGE_OPTIONS
from app.policies import (
    EFFECTIVE_DATE,
    POLICY_DOCUMENTS,
    POLICY_LINKS,
    SAFETY_PRECAUTIONS,
)
from app.policy_catalog import (
    CREDITS_ROWS,
    DOCUMENT_SOURCE_KEYS,
    POLICY_CATALOGS,
    POLICY_DOCUMENT_KEYS,
    POLICY_LOCALES,
    SOURCE_COINCIDENCES,
    SOURCE_KEYS,
    document_sources,
    missing_policy_sources,
    placeholders,
)
from app.states.auth_state import AuthState
from app.states.policy_state import PolicyState
from test_utils import run_event


class PolicyDocumentTranslationTests(unittest.TestCase):
    def test_complete_inventory_includes_runtime_merged_safety(self):
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(SETTINGS_LANGUAGE_OPTIONS), 39)
        self.assertEqual(
            {code for code, _ in SETTINGS_LANGUAGE_OPTIONS},
            POLICY_LOCALES | {"en"},
        )
        self.assertEqual(len(SOURCE_KEYS), 182)
        self.assertEqual(len(set(SOURCE_KEYS)), 182)
        self.assertEqual(tuple(DOCUMENT_SOURCE_KEYS), POLICY_DOCUMENT_KEYS)
        self.assertEqual(
            {key: len(texts) for key, texts in DOCUMENT_SOURCE_KEYS.items()},
            {"howto": 85, "privacy": 41, "agreement": 51, "credits": 8},
        )
        self.assertEqual(EFFECTIVE_DATE, "Updated and effective 1 June 2024")
        self.assertIn(SAFETY_PRECAUTIONS["notice"], SOURCE_KEYS)
        self.assertIn(
            "Safety and precautions — read this before you meet anyone",
            SOURCE_KEYS,
        )
        for section in SAFETY_PRECAUTIONS["sections"]:
            self.assertIn(section["heading"], SOURCE_KEYS)
            for paragraph in section["paragraphs"]:
                self.assertIn(paragraph, SOURCE_KEYS)
        for source in SOURCE_KEYS:
            self.assertEqual(translate("en", source), source)
        self.assertTrue(set(SOURCE_KEYS) <= set(COMPLETE_KEYS))
        self.assertEqual(
            [item["key"] for item in POLICY_LINKS], list(POLICY_DOCUMENT_KEYS)
        )

    def test_literal_entries_and_attribution_are_valid(self):
        self.assertEqual(set(CREDITS_ROWS), POLICY_LOCALES)
        self.assertEqual(set(POLICY_CATALOGS), POLICY_LOCALES)
        self.assertEqual(SOURCE_COINCIDENCES, frozenset({("nl", "Credits")}))
        for locale, entries in POLICY_CATALOGS.items():
            for source, value in entries.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertEqual(placeholders(source), placeholders(value))
                    if source == value:
                        self.assertIn((locale, source), SOURCE_COINCIDENCES)
                    for name in (
                        "Go and Help",
                        "OpenFreeMap",
                        "OpenStreetMap",
                        "MapLibre",
                        "Planetiler",
                        "OpenMapTiles",
                        "Open Database License",
                        "ODbL",
                        "©",
                    ):
                        if name in source:
                            self.assertIn(name, value)
                    self.assertTrue(catalog(locale).get(source, "").strip())
        for locale in POLICY_LOCALES:
            entries = catalog(locale)
            for source in DOCUMENT_SOURCE_KEYS["credits"]:
                self.assertIn(source, entries)
                self.assertNotEqual(entries[source], source) if (
                    locale,
                    source,
                ) not in SOURCE_COINCIDENCES else None
        for locale in ("ru", "ur", "fr"):
            self.assertFalse(
                set(DOCUMENT_SOURCE_KEYS["privacy"]) - set(catalog(locale))
            )
        for locale in ("fr", "de"):
            self.assertFalse(
                set(DOCUMENT_SOURCE_KEYS["agreement"]) - set(catalog(locale))
            )
        self.assertFalse(missing_policy_sources(catalog("fr"), "fr"))

    def test_all_38_non_english_locales_have_all_182_sources(self):
        # This is the release gate, not a fallback-filled or title-only coverage check.
        gaps = {
            locale: missing_policy_sources(catalog(locale), locale)
            for locale in sorted(POLICY_LOCALES)
        }
        missing = {
            locale: len(sources) for locale, sources in gaps.items() if sources
        }
        self.assertEqual(
            missing,
            {},
            f"Full-document translation deliverable remains incomplete: {missing}",
        )

    def test_six_reader_fields_use_reactive_ui_and_rtl_root(self):
        screen_source = ast.unparse(ast.parse(inspect.getsource(policy_screen)))
        for field in ("title", "subtitle", "updated", "notice"):
            self.assertIn(f"ui(PolicyState.{field})", screen_source)
        self.assertIn(
            "ui(section['heading'])",
            ast.unparse(ast.parse(inspect.getsource(policy_section))),
        )
        self.assertIn(
            "ui(text)",
            ast.unparse(ast.parse(inspect.getsource(policy_paragraph))),
        )
        self.assertIn("dir=AuthState.interface_direction", screen_source)
        self.assertIn("lang=AuthState.preferred_language", screen_source)
        self.assertIn("max-w-3xl", screen_source)
        self.assertIn("overflow-y-auto", screen_source)
        self.assertTrue(policy_screen().render())
        state_source = ast.unparse(ast.parse(inspect.getsource(PolicyState)))
        self.assertNotIn("translate(", state_source)
        self.assertNotIn("interface_i18n", state_source)
        for field in ("title", "subtitle", "updated", "notice"):
            self.assertIn(f"self.{field} = document['{field}']", state_source)

    def test_compiled_dynamic_lookup_switches_small_external_node_fixture(self):
        node = shutil.which("node")
        self.assertIsNotNone(
            node, "Node is required for the reactive expression check"
        )
        sources = [
            POLICY_DOCUMENTS["howto"]["title"],
            POLICY_DOCUMENTS["privacy"]["title"],
            POLICY_DOCUMENTS["privacy"]["sections"][4]["paragraphs"][0],
            *POLICY_DOCUMENTS["credits"]["sections"][0]["paragraphs"],
        ]
        source_var = rx.Var(
            _js_expr="policyDocumentSourceFixture", _var_type=str
        ).to(str)
        compiled = str(ui(source_var)).replace(
            str(AuthState.interface_text), "policyInterfaceTextFixture"
        )
        locales = ["ru", "ur", "fr", "en", "ur", "fr", "ru", "en"]
        payload = {
            "expression": compiled,
            "sources": sources,
            "locales": locales,
            "catalogs": {
                locale: {
                    source: value
                    for source, value in catalog(locale).items()
                    if source in sources
                }
                for locale in set(locales)
            },
        }
        script = """
const fs = require('fs');
const policyExternalFixture = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = Boolean;
let policyInterfaceTextFixture = {};
let policyDocumentSourceFixture = '';
const policyResults = [];
for (const locale of policyExternalFixture.locales) {
  policyInterfaceTextFixture = policyExternalFixture.catalogs[locale];
  for (const source of policyExternalFixture.sources) {
    policyDocumentSourceFixture = source;
    policyResults.push(eval(policyExternalFixture.expression));
  }
}
process.stdout.write(JSON.stringify(policyResults));
"""
        result = subprocess.run(
            [node, "-e", script],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        expected = [
            translate(locale, source)
            for locale in locales
            for source in sources
        ]
        self.assertEqual(json.loads(result.stdout), expected)
        for locale in ("ru", "ur", "fr"):
            for source in sources:
                self.assertNotEqual(translate(locale, source), source)
        metadata = ui(source_var)._get_all_var_data()
        self.assertIsNotNone(metadata)
        self.assertTrue(
            set(AuthState.interface_text._get_all_var_data().hooks)
            <= set(metadata.hooks)
        )


class CanonicalPolicyEventTests(unittest.IsolatedAsyncioTestCase):
    async def test_open_language_switch_and_close_preserve_canonical_documents(
        self,
    ):
        state = PolicyState(_reflex_internal_init=True)
        auth = await state.get_state(AuthState)
        original_documents = deepcopy(POLICY_DOCUMENTS)
        original_links = deepcopy(POLICY_LINKS)
        original_language = auth.preferred_language
        try:
            for key in POLICY_DOCUMENT_KEYS:
                await run_event(state.open_policy, key)
                document = original_documents[key]
                snapshot = (
                    state.open_key,
                    state.title,
                    state.subtitle,
                    state.icon,
                    state.updated,
                    state.notice,
                    deepcopy(state.sections),
                )
                self.assertEqual(
                    snapshot,
                    (
                        document["key"],
                        document["title"],
                        document["subtitle"],
                        document["icon"],
                        document["updated"],
                        document["notice"],
                        document["sections"],
                    ),
                )
                for locale in ("ru", "ur", "fr", "de", "en", "ur"):
                    auth.preferred_language = locale
                    self.assertEqual(
                        auth.interface_direction,
                        "rtl" if locale == "ur" else "ltr",
                    )
                    self.assertEqual(auth.interface_text, catalog(locale))
                    self.assertEqual(
                        snapshot,
                        (
                            state.open_key,
                            state.title,
                            state.subtitle,
                            state.icon,
                            state.updated,
                            state.notice,
                            state.sections,
                        ),
                    )
                await run_event(state.open_policy, "not-a-document")
                self.assertEqual(state.open_key, key)
                await run_event(state.close_policy)
                self.assertFalse(state.is_open)
                self.assertEqual(state.sections, [])
                self.assertEqual(state.title, "")
            self.assertEqual(POLICY_DOCUMENTS, original_documents)
            self.assertEqual(POLICY_LINKS, original_links)
            for key in POLICY_DOCUMENT_KEYS:
                self.assertEqual(
                    document_sources(key), DOCUMENT_SOURCE_KEYS[key]
                )
        finally:
            auth.preferred_language = original_language
            await run_event(state.close_policy)


if __name__ == "__main__":
    unittest.main()
