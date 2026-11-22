import reflex as rx

import ast
import inspect
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from app.interface_i18n import catalog, translate, ui
from app.policies import EFFECTIVE_DATE, POLICY_LINKS, SAFETY_PRECAUTIONS
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
    validate_rows,
)
from app import policy_catalog_agreement_russian_urdu as agreement_data
from app import policy_catalog_howto_russian_urdu as howto_data
from app.policy_catalog_agreement_russian_urdu import (
    AGREEMENT_RUSSIAN_URDU_ROWS,
)
from app.policy_catalog_howto_russian_urdu import HOWTO_RUSSIAN_URDU_ROWS
from app.policy_catalog_privacy import PRIVACY_ROWS
from app.states.auth_state import AuthState


class RussianUrduPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_rows_and_stable_canonical_inventory(self):
        self.assertEqual(len(SOURCE_KEYS), 182)
        self.assertEqual(len(set(SOURCE_KEYS)), 182)
        self.assertEqual(
            POLICY_DOCUMENT_KEYS, ("howto", "privacy", "agreement", "credits")
        )
        self.assertEqual(
            [item["key"] for item in POLICY_LINKS], list(POLICY_DOCUMENT_KEYS)
        )
        self.assertEqual(SOURCE_COINCIDENCES, frozenset({("nl", "Credits")}))
        self.assertEqual(EFFECTIVE_DATE, "Updated and effective 1 June 2024")
        self.assertEqual(
            {key: len(row) for key, row in DOCUMENT_SOURCE_KEYS.items()},
            {"howto": 85, "privacy": 41, "agreement": 51, "credits": 8},
        )
        total = 0
        for doc, module, name, rows, count in (
            (
                "howto",
                howto_data,
                "HOWTO_RUSSIAN_URDU_ROWS",
                HOWTO_RUSSIAN_URDU_ROWS,
                85,
            ),
            (
                "agreement",
                agreement_data,
                "AGREEMENT_RUSSIAN_URDU_ROWS",
                AGREEMENT_RUSSIAN_URDU_ROWS,
                51,
            ),
        ):
            self.assertEqual(document_sources(doc), DOCUMENT_SOURCE_KEYS[doc])
            self.assertEqual(set(rows), {"ru", "ur"})
            parsed = ast.parse(
                Path(inspect.getfile(module)).read_text(encoding="utf-8")
            )
            assignments = [
                node for node in parsed.body if isinstance(node, ast.AnnAssign)
            ]
            self.assertEqual(len(assignments), 1)
            self.assertEqual(assignments[0].target.id, name)
            self.assertEqual(ast.literal_eval(assignments[0].value), rows)
            self.assertFalse(
                any(
                    isinstance(
                        node,
                        (ast.Call, ast.FunctionDef, ast.Import, ast.ImportFrom),
                    )
                    for node in ast.walk(parsed)
                )
            )
            for locale, row in rows.items():
                with self.subTest(document=doc, locale=locale):
                    self.assertIsInstance(row, tuple)
                    self.assertEqual(len(row), count)
                    self.assertTrue(
                        all(
                            isinstance(text, str) and text.strip()
                            for text in row
                        )
                    )
                    total += len(row)
            validate_rows(DOCUMENT_SOURCE_KEYS[doc], rows)
        self.assertEqual(total, 272)

    def test_complete_authored_and_effective_coverage_and_relative_gain(self):
        for locale in ("ru", "ur"):
            previous = dict(
                zip(
                    DOCUMENT_SOURCE_KEYS["credits"],
                    CREDITS_ROWS[locale],
                    strict=True,
                )
            )
            previous.update(
                zip(
                    DOCUMENT_SOURCE_KEYS["privacy"],
                    PRIVACY_ROWS[locale],
                    strict=True,
                )
            )
            for doc, rows in (
                ("howto", HOWTO_RUSSIAN_URDU_ROWS),
                ("agreement", AGREEMENT_RUSSIAN_URDU_ROWS),
            ):
                previous[DOCUMENT_SOURCE_KEYS[doc][0]] = rows[locale][0]
            # Previous dedicated document data covered 50 sources; effective
            # interface catalogs covered 51 (131 gaps), not 50 (132 gaps).
            self.assertEqual(len(set(previous) & set(SOURCE_KEYS)), 50)
            authored = dict(previous)
            for doc, rows in (
                ("howto", HOWTO_RUSSIAN_URDU_ROWS),
                ("agreement", AGREEMENT_RUSSIAN_URDU_ROWS),
            ):
                authored.update(
                    validate_rows(
                        DOCUMENT_SOURCE_KEYS[doc], {locale: rows[locale]}
                    )[locale]
                )
            self.assertEqual(len(set(authored) - set(previous)), 132)
            self.assertEqual(len(authored), 182)
            self.assertEqual(missing_policy_sources(authored, locale), ())
            self.assertEqual(
                missing_policy_sources(POLICY_CATALOGS[locale], locale), ()
            )
            effective = catalog(locale)
            self.assertEqual(missing_policy_sources(effective, locale), ())
            for source in SOURCE_KEYS:
                self.assertIn(source, effective)
                self.assertNotEqual(effective[source], source)
                self.assertEqual(translate(locale, source), effective[source])
                self.assertEqual(translate("en", source), source)

    def test_preserved_privacy_credits_attribution_and_slots(self):
        names = (
            "Go and Help",
            "Stripe",
            "OpenFreeMap",
            "OpenStreetMap",
            "MapLibre",
            "Planetiler",
            "OpenMapTiles",
            "Open Database License",
            "ODbL",
            "©",
        )
        for locale in ("ru", "ur"):
            for doc, rows in (
                ("privacy", PRIVACY_ROWS),
                ("credits", CREDITS_ROWS),
            ):
                for source, original in zip(
                    DOCUMENT_SOURCE_KEYS[doc], rows[locale], strict=True
                ):
                    self.assertEqual(POLICY_CATALOGS[locale][source], original)
                    self.assertEqual(catalog(locale)[source], original)
            for source in SOURCE_KEYS:
                value = catalog(locale)[source]
                self.assertEqual(placeholders(source), placeholders(value))
                for name in names:
                    if name in source:
                        self.assertIn(name, value)
            for rows in (HOWTO_RUSSIAN_URDU_ROWS, AGREEMENT_RUSSIAN_URDU_ROWS):
                self.assertEqual(rows[locale][2], PRIVACY_ROWS[locale][2])
                self.assertIn("1", rows[locale][2])
                self.assertIn("2024", rows[locale][2])
                self.assertIn(
                    "июня" if locale == "ru" else "جون", rows[locale][2]
                )

    def test_complete_merged_safety_and_full_paragraphs_not_summaries(self):
        safety_sources = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_sources.append(section["heading"])
            safety_sources.extend(section["paragraphs"])
        self.assertEqual(len(safety_sources), 51)
        for locale in ("ru", "ur"):
            authored = dict(
                zip(
                    DOCUMENT_SOURCE_KEYS["howto"],
                    HOWTO_RUSSIAN_URDU_ROWS[locale],
                    strict=True,
                )
            )
            self.assertTrue(set(safety_sources) <= set(authored))
            for doc, rows in (
                ("howto", HOWTO_RUSSIAN_URDU_ROWS),
                ("agreement", AGREEMENT_RUSSIAN_URDU_ROWS),
            ):
                for source, value in zip(
                    DOCUMENT_SOURCE_KEYS[doc], rows[locale], strict=True
                ):
                    with self.subTest(locale=locale, source=source):
                        self.assertNotEqual(value, source)
                        self.assertNotIn(source, value)
                        self.assertRegex(
                            value,
                            r"[А-Яа-яЁё]"
                            if locale == "ru"
                            else r"[\u0600-\u06ff]",
                        )
                        if len(source.split()) >= 35:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.60
                            )
                            words = re.findall(r"[A-Za-z]+", source)
                            for index in range(len(words) - 5):
                                phrase = " ".join(words[index : index + 6])
                                self.assertNotIn(phrase, value)

    def test_numeric_facts_and_representative_legal_exceptions(self):
        # ASCII numerals are intentional for ages, dates, distances and phone
        # numbers. The liability cap uses native words: twelve months/fifty USD.
        for locale in ("ru", "ur"):
            howto = dict(
                zip(
                    DOCUMENT_SOURCE_KEYS["howto"],
                    HOWTO_RUSSIAN_URDU_ROWS[locale],
                    strict=True,
                )
            )
            agreement = dict(
                zip(
                    DOCUMENT_SOURCE_KEYS["agreement"],
                    AGREEMENT_RUSSIAN_URDU_ROWS[locale],
                    strict=True,
                )
            )
            location = next(
                value
                for source, value in howto.items()
                if source.startswith("Set my location offers")
            )
            for token in ("500m", "1km"):
                self.assertIn(token, location)
            emergency = next(
                value
                for source, value in howto.items()
                if source.startswith("Learn the emergency number")
            )
            for number in ("112", "999", "911", "000"):
                self.assertIn(number, emergency)
            age = next(
                value
                for source, value in agreement.items()
                if source.startswith("You must be at least")
            )
            self.assertIn("16", age)
            cap = next(
                value
                for source, value in agreement.items()
                if source.startswith("To the same extent")
            )
            renewal = next(
                value
                for source, value in agreement.items()
                if source.startswith("Using Go and Help")
            )
            cancellation = next(
                value
                for source, value in agreement.items()
                if source.startswith("You can cancel at any time")
            )
            exception = next(
                value
                for source, value in agreement.items()
                if source.startswith("Nothing in this agreement excludes")
            )
            indemnity = next(
                value
                for source, value in agreement.items()
                if source.startswith("You agree to indemnify")
            )
            local = next(
                value
                for source, value in agreement.items()
                if source.startswith("This agreement is governed")
            )
            expected = {
                "ru": (
                    (
                        cap,
                        (
                            "двенадцать месяцев",
                            "пятьюдесятью долларами США",
                            "большей",
                        ),
                    ),
                    (
                        renewal,
                        ("каждый месяц", "каждый год", "Stripe", "отмените"),
                    ),
                    (
                        cancellation,
                        (
                            "уже оплаченного периода",
                            "местный закон",
                            "не возвращается",
                            "право на отказ",
                        ),
                    ),
                    (
                        exception,
                        (
                            "не исключает",
                            "небрежностью",
                            "мошенничество",
                            "права потребителей",
                        ),
                    ),
                    (indemnity, ("кроме", "наших собственных неправомерных")),
                    (
                        local,
                        ("местных судах", "преимущество", "обязательная норма"),
                    ),
                ),
                "ur": (
                    (cap, ("بارہ مہینوں", "پچاس امریکی ڈالر", "زیادہ")),
                    (renewal, ("ہر ماہ", "ہر سال", "Stripe", "منسوخ")),
                    (
                        cancellation,
                        (
                            "مدت کے اختتام",
                            "مقامی قانون",
                            "واپس نہیں",
                            "دستبرداری",
                        ),
                    ),
                    (
                        exception,
                        (
                            "خارج یا محدود نہیں",
                            "غفلت",
                            "دھوکا دہی",
                            "لازمی حقوق",
                        ),
                    ),
                    (indemnity, ("سوائے", "ہماری اپنی غلط کاری")),
                    (local, ("مقامی عدالتوں", "لازمی قاعدہ غالب")),
                ),
            }
            for value, tokens in expected[locale]:
                for token in tokens:
                    self.assertIn(token, value)

    def test_partial_global_counts_not_a_waiver_of_release_gate(self):
        authored_counts = {
            locale: len(set(POLICY_CATALOGS[locale]) & set(SOURCE_KEYS))
            for locale in POLICY_LOCALES
        }
        self.assertEqual(sum(authored_counts.values()), 876)
        self.assertEqual(authored_counts["fr"], 182)
        self.assertEqual(authored_counts["de"], 58)
        self.assertEqual(authored_counts["ru"], 182)
        self.assertEqual(authored_counts["ur"], 182)
        other = POLICY_LOCALES - {"fr", "de", "ru", "ur"}
        self.assertEqual(len(other), 34)
        self.assertTrue(all(authored_counts[locale] == 8 for locale in other))
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        self.assertEqual(
            {locale for locale, count in gaps.items() if not count},
            {"fr", "ru", "ur"},
        )
        self.assertEqual(gaps["de"], 120)
        self.assertTrue(all(gaps[locale] == 169 for locale in other))
        self.assertEqual(sum(gaps.values()), 5866)
        self.assertEqual(
            len(POLICY_LOCALES) * len(SOURCE_KEYS) - sum(gaps.values()), 1050
        )

    def test_compiled_dynamic_lookup_switches_full_paragraph_fixture(self):
        node = shutil.which("node")
        self.assertIsNotNone(
            node, "Node is required for compiled lookup validation"
        )
        sources = [
            SAFETY_PRECAUTIONS["notice"],
            SAFETY_PRECAUTIONS["sections"][3]["paragraphs"][1],
            DOCUMENT_SOURCE_KEYS["agreement"][40],
            DOCUMENT_SOURCE_KEYS["agreement"][-1],
        ]
        source_var = rx.Var(_js_expr="policySourceFixture", _var_type=str).to(
            str
        )
        expression = str(ui(source_var)).replace(
            str(AuthState.interface_text), "policyTextFixture"
        )
        locales = ["ru", "ur", "en", "ur", "ru"]
        payload = {
            "expression": expression,
            "sources": sources,
            "locales": locales,
            "catalogs": {
                locale: {
                    source: translate(locale, source) for source in sources
                }
                for locale in set(locales)
            },
        }
        script = """
const fs = require('fs');
const fixture = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = Boolean;
let policyTextFixture = {};
let policySourceFixture = '';
const results = [];
for (const locale of fixture.locales) {
  policyTextFixture = fixture.catalogs[locale];
  for (const source of fixture.sources) {
    policySourceFixture = source;
    results.push(eval(fixture.expression));
  }
}
process.stdout.write(JSON.stringify(results));
"""
        result = subprocess.run(
            [node, "-e", script],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        self.assertEqual(
            json.loads(result.stdout),
            [
                translate(locale, source)
                for locale in locales
                for source in sources
            ],
        )


if __name__ == "__main__":
    unittest.main()
