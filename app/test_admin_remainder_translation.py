import ast
import json
import shutil
import subprocess
import unittest
from collections import Counter
from pathlib import Path
from string import Formatter

import reflex as rx

from app.components.admin_panel import admin_panel, safety_table
from app.interface_catalog_admin_remainder import (
    ADMIN_REMAINDER_CATALOGS,
    ADMIN_REMAINDER_KEYS,
    ADMIN_REMAINDER_ROWS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, catalog, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.scripts.audit_interface_copy import audit_paths
from app.states.auth_state import AuthState

EXPECTED_KEYS = (
    "Admin note (optional) — saved with the next action you take",
    "Backend activity",
    "Ban",
    "Ban this member? The account is deactivated immediately.",
    "Ban this member? Their account will be deactivated.",
    "Banned",
    "Ban…",
    "Both",
    "Closed",
    "Confirm ban",
    "Deactivated",
    "Dismiss",
    "Dismissed",
    "Everything happening across Go and Help.",
    "Helper → poster",
    "Incident ledger",
    "Matched",
    "No content reports have been filed.",
    "No safety reports have been filed.",
    "One-star reviews received",
    "Poster → helper",
    "Private reports filed by the two people on a completed job. Nothing here is public, and no account is ever banned automatically — every decision below is yours.",
    "Receive help",
    "Reports appear here the moment someone tells us about a bad experience on a completed job.",
    "Resolve",
    "Resolved",
    "Reviewing",
    "Safety review",
    "Subscribers, help posts, accepted jobs, messages, completed tasks and the full review history — the ledger behind the journal.",
    "Warn",
    "Warned",
    "What did you check, and why this outcome?",
)
EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}


class AdminRemainderTranslationTests(unittest.TestCase):
    def test_exact_manifest_literal_rows_and_full_catalog_coverage(self):
        self.assertEqual(ADMIN_REMAINDER_KEYS, EXPECTED_KEYS)
        self.assertEqual(len(ADMIN_REMAINDER_KEYS), 32)
        self.assertEqual(len(set(ADMIN_REMAINDER_KEYS)), 32)
        self.assertEqual(set(ADMIN_REMAINDER_ROWS), EXPECTED_LOCALES)
        self.assertEqual(set(ADMIN_REMAINDER_CATALOGS), EXPECTED_LOCALES)
        self.assertNotIn("en", ADMIN_REMAINDER_CATALOGS)
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))

        source = Path("app/interface_catalog_admin_remainder.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        rows_definition = next(
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "ADMIN_REMAINDER_ROWS"
        )
        self.assertIsInstance(rows_definition.value, ast.Dict)
        self.assertEqual(
            ast.literal_eval(rows_definition.value), ADMIN_REMAINDER_ROWS
        )

        for locale in EXPECTED_LOCALES:
            self.assertEqual(len(ADMIN_REMAINDER_ROWS[locale].split("|")), 32)
            entries = ADMIN_REMAINDER_CATALOGS[locale]
            self.assertEqual(tuple(entries), EXPECTED_KEYS)
            self.assertEqual(set(entries), set(EXPECTED_KEYS))
            for source_key in EXPECTED_KEYS:
                with self.subTest(locale=locale, source=source_key):
                    value = entries[source_key]
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source_key)
                    self.assertEqual(
                        Counter(
                            name
                            for _, name, _, _ in Formatter().parse(source_key)
                            if name
                        ),
                        Counter(
                            name
                            for _, name, _, _ in Formatter().parse(value)
                            if name
                        ),
                    )
                    self.assertEqual(CATALOGS[locale][source_key], value)
                    self.assertEqual(translate(locale, source_key), value)
        for source_key in EXPECTED_KEYS:
            self.assertEqual(translate("en", source_key), source_key)
            self.assertEqual(translate("unsupported", source_key), source_key)
            self.assertEqual(
                Counter(
                    name
                    for _, name, _, _ in Formatter().parse(source_key)
                    if name
                ),
                Counter(),
            )

    def test_catalog_merge_preserves_existing_native_copy(self):
        for locale in EXPECTED_LOCALES:
            for source in ("Continue", "Back", "Next"):
                self.assertNotEqual(CATALOGS[locale][source], source)
                self.assertEqual(
                    translate(locale, source), CATALOGS[locale][source]
                )
        self.assertEqual(CATALOGS["fr"]["Continue"], "Continuer")
        self.assertEqual(CATALOGS["ar"]["Continue"], "متابعة")
        self.assertEqual(CATALOGS["de"]["Continue"], "Weiter")

    def test_privacy_moderation_status_direction_and_help_meanings(self):
        privacy_key = EXPECTED_KEYS[21]
        immediate_key = EXPECTED_KEYS[3]
        later_key = EXPECTED_KEYS[4]
        private_terms = {
            "fr": ("deux personnes", "privés", "public", "automatiquement"),
            "ar": ("الشخصين", "خاصة", "للعامة", "تلقائيًا"),
            "de": ("beiden Personen", "Private", "öffentlich", "automatisch"),
            "zh": ("两位", "私人", "公开", "自动"),
        }
        immediate_terms = {
            "fr": ("immédiatement", "désactivé"),
            "ar": ("فورًا", "سيُعطّل"),
            "de": ("sofort", "deaktiviert"),
            "zh": ("立即", "停用"),
        }
        for locale, terms in private_terms.items():
            privacy = ADMIN_REMAINDER_CATALOGS[locale][privacy_key]
            for term in terms:
                self.assertIn(term, privacy, (locale, term))
            immediate = ADMIN_REMAINDER_CATALOGS[locale][immediate_key]
            later = ADMIN_REMAINDER_CATALOGS[locale][later_key]
            self.assertIn(immediate_terms[locale][0], immediate, locale)
            self.assertIn(immediate_terms[locale][1], immediate, locale)
            self.assertNotIn(immediate_terms[locale][0], later, locale)
            self.assertIn(immediate_terms[locale][1], later, locale)

        self.assertIn(
            "une étoile", ADMIN_REMAINDER_CATALOGS["fr"][EXPECTED_KEYS[19]]
        )
        self.assertIn(
            "نجمة واحدة", ADMIN_REMAINDER_CATALOGS["ar"][EXPECTED_KEYS[19]]
        )
        self.assertIn(
            "Ein-Stern", ADMIN_REMAINDER_CATALOGS["de"][EXPECTED_KEYS[19]]
        )
        self.assertIn("一星", ADMIN_REMAINDER_CATALOGS["zh"][EXPECTED_KEYS[19]])
        self.assertIn(
            "Recevoir de l’aide",
            ADMIN_REMAINDER_CATALOGS["fr"][EXPECTED_KEYS[22]],
        )
        self.assertEqual(
            ADMIN_REMAINDER_CATALOGS["fr"][EXPECTED_KEYS[14]],
            "Aidant → demandeur",
        )
        self.assertEqual(
            ADMIN_REMAINDER_CATALOGS["fr"][EXPECTED_KEYS[20]],
            "Demandeur → aidant",
        )
        self.assertEqual(
            ADMIN_REMAINDER_CATALOGS["fr"][EXPECTED_KEYS[16]],
            "Correspondance trouvée",
        )

    def test_admin_panel_static_ui_sources_are_now_cataloged(self):
        panel_path = Path("app/components/admin_panel.py")
        tree = ast.parse(panel_path.read_text(encoding="utf-8"))
        static_ui_sources = {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ui"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        self.assertTrue(set(EXPECTED_KEYS) <= static_ui_sources)
        findings = audit_paths([panel_path])
        missing_static_sources = {
            str(item["source"]) for item in findings if item["missing"]
        }
        self.assertFalse(missing_static_sources, sorted(missing_static_sources))
        self.assertIsInstance(admin_panel(), rx.Component)
        self.assertIsInstance(safety_table(), rx.Component)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_compiled_ui_lookup_uses_each_small_locale_fixture(self):
        expressions = [str(ui(source)) for source in EXPECTED_KEYS]
        interface_var = str(AuthState.interface_text)
        cases: list[dict[str, str]] = []
        for locale in ("fr", "ar", "en"):
            for source, expression in zip(
                EXPECTED_KEYS, expressions, strict=True
            ):
                cases.append(
                    {
                        "locale": locale,
                        "source": source,
                        "expression": expression.replace(
                            interface_var, "interfaceText"
                        ),
                        "expected": translate(locale, source),
                    }
                )
        payload = {
            "catalogs": {
                locale: {
                    source: catalog(locale).get(source, source)
                    for source in EXPECTED_KEYS
                }
                for locale in ("fr", "ar", "en")
            },
            "cases": cases,
        }
        script = """
const fs = require('fs');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = value => Boolean(value);
const results = payload.cases.map(item => {
  const interfaceText = payload.catalogs[item.locale];
  return eval(item.expression);
});
process.stdout.write(JSON.stringify(results));
"""
        result = subprocess.run(
            [shutil.which("node") or "node", "-e", script],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        self.assertEqual(
            json.loads(result.stdout), [case["expected"] for case in cases]
        )


if __name__ == "__main__":
    unittest.main()
