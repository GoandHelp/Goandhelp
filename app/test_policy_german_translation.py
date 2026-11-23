import reflex as rx

import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app.interface_i18n import catalog, translate
from app.policies import POLICY_DOCUMENTS, SAFETY_PRECAUTIONS
from app.policy_catalog import (
    CREDITS_ROWS,
    DOCUMENT_SOURCE_KEYS,
    POLICY_CATALOGS,
    POLICY_LOCALES,
    SOURCE_KEYS,
    missing_policy_sources,
    placeholders,
    validate_rows,
)
from app import policy_catalog_howto_german as howto_data
from app import policy_catalog_privacy_german as privacy_data
from app.policy_catalog_agreement_german import AGREEMENT_GERMAN_ROWS
from app.policy_catalog_howto_german import HOWTO_GERMAN_ROWS
from app.policy_catalog_privacy_german import PRIVACY_GERMAN_ROWS


class GermanPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_rows_and_native_validated_entries(self):
        total = 0
        for document, module, name, rows, count in (
            ("howto", howto_data, "HOWTO_GERMAN_ROWS", HOWTO_GERMAN_ROWS, 85),
            (
                "privacy",
                privacy_data,
                "PRIVACY_GERMAN_ROWS",
                PRIVACY_GERMAN_ROWS,
                41,
            ),
        ):
            self.assertEqual(set(rows), {"de"})
            self.assertIsInstance(rows["de"], tuple)
            self.assertEqual(len(rows["de"]), count)
            tree = ast.parse(
                Path(inspect.getfile(module)).read_text(encoding="utf-8")
            )
            assignments = [
                node for node in tree.body if isinstance(node, ast.AnnAssign)
            ]
            self.assertEqual(len(assignments), 1)
            self.assertEqual(assignments[0].target.id, name)
            self.assertEqual(ast.literal_eval(assignments[0].value), rows)
            self.assertFalse(
                any(
                    isinstance(
                        node,
                        (
                            ast.Call,
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                            ast.ClassDef,
                            ast.Import,
                            ast.ImportFrom,
                            ast.For,
                            ast.ListComp,
                            ast.DictComp,
                        ),
                    )
                    for node in ast.walk(tree)
                )
            )
            validated = validate_rows(DOCUMENT_SOURCE_KEYS[document], rows)[
                "de"
            ]
            for source, value in zip(
                DOCUMENT_SOURCE_KEYS[document], rows["de"], strict=True
            ):
                with self.subTest(document=document, source=source):
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertNotIn(source, value)
                    self.assertEqual(placeholders(source), placeholders(value))
                    self.assertEqual(validated[source], value)
                    self.assertNotRegex(
                        value, r"\b(?:du|dein|deine|deinen|dir|dich)\b"
                    )
                    for name in (
                        "Go and Help",
                        "Stripe",
                        "Resend",
                        "OpenFreeMap",
                        "OpenStreetMap",
                        "MapLibre",
                        "Planetiler",
                        "OpenMapTiles",
                        "Open Database License",
                        "ODbL",
                        "©",
                        "SHA-256",
                        "https://",
                    ):
                        if name in source:
                            self.assertIn(name, value)
                    if len(source.split()) >= 35:
                        self.assertGreaterEqual(len(value), len(source) * 0.60)
                        words = re.findall(r"[A-Za-z]+", source)
                        for index in range(len(words) - 5):
                            self.assertNotIn(
                                " ".join(words[index : index + 6]), value
                            )
            total += len(rows["de"])
        self.assertEqual(total, 126)
        self.assertEqual(
            HOWTO_GERMAN_ROWS["de"][2],
            "Aktualisiert und gültig ab 1. Juni 2024",
        )
        self.assertEqual(
            PRIVACY_GERMAN_ROWS["de"][2], HOWTO_GERMAN_ROWS["de"][2]
        )

    def test_complete_german_sources_and_computed_batch_progress(self):
        sources = set(SOURCE_KEYS)
        authored = POLICY_CATALOGS["de"]
        effective = catalog("de")
        self.assertEqual(len(sources & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "de"), ())
        self.assertEqual(missing_policy_sources(effective, "de"), ())
        for source in SOURCE_KEYS:
            self.assertEqual(translate("de", source), effective[source])
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("en", source), source)
        previous = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["de"], strict=True
            )
        )
        previous.update(
            zip(
                DOCUMENT_SOURCE_KEYS["agreement"],
                AGREEMENT_GERMAN_ROWS["de"],
                strict=True,
            )
        )
        self.assertEqual(len(sources & set(previous)), 58)
        new_sources = set(DOCUMENT_SOURCE_KEYS["howto"]) | set(
            DOCUMENT_SOURCE_KEYS["privacy"]
        )
        self.assertEqual(len(new_sources - set(previous)), 124)
        authored_total = sum(
            len(sources & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 1000)
        self.assertGreaterEqual(effective_total, 1170)
        self.assertEqual(effective_total + sum(gaps.values()), 38 * 182)
        self.assertLessEqual(sum(gaps.values()), 5746)
        for locale in ("fr", "de", "ru", "ur"):
            self.assertEqual(gaps[locale], 0)

    def test_entire_merged_safety_and_full_privacy_paragraphs(self):
        howto = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["howto"],
                HOWTO_GERMAN_ROWS["de"],
                strict=True,
            )
        )
        privacy = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["privacy"],
                PRIVACY_GERMAN_ROWS["de"],
                strict=True,
            )
        )
        safety_sources = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_sources.append(section["heading"])
            safety_sources.extend(section["paragraphs"])
        self.assertEqual(len(safety_sources), 51)
        self.assertTrue(set(safety_sources) <= set(howto))
        self.assertEqual(len(privacy), 41)
        fixtures = (
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "Ausweisdokumente",
                    "Strafregister",
                    "berufliche Qualifikationen",
                    "Urteilsvermögen",
                ),
            ),
            (
                howto,
                "Do not take on work",
                (
                    "Hauptleitungen",
                    "Baumfällungen",
                    "schutzbedürftiger Erwachsener",
                    "Elektrowerkzeugen",
                    "Hilfsbereitschaft ist keine Qualifikation",
                ),
            ),
            (
                howto,
                "Go and Help is used all over",
                (
                    "Visa- oder Einwanderungsregeln",
                    "kein Geld fließt",
                    "nicht wir",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Europäischen Union"),
            ),
            (
                howto,
                "Set my location offers",
                ("500m", "1km", "keinerlei Koordinaten", "alle Nutzer"),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "500m",
                    "1km",
                    "sofort",
                    "ohne Ihre gespeicherten Koordinaten zu löschen",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                ("0.5–1 km", "niemals veröffentlicht", "nur mit dem Helfer"),
            ),
            (
                privacy,
                "When you ask us to close",
                (
                    "gesetzliche Pflicht",
                    "Streit beizulegen",
                    "Missbrauch",
                    "zitiert oder beantwortet",
                ),
            ),
            (
                privacy,
                "Go and Help is used by people",
                (
                    "Datenschutzregeln",
                    "vertragliche Schutzmaßnahmen",
                    "nicht versprechen",
                ),
            ),
            (
                privacy,
                "Depending on where you live",
                (
                    "berichtigen oder löschen",
                    "einzuschränken",
                    "widersprechen",
                    "Datenschutzbehörde",
                    "von Ihnen stammt",
                ),
            ),
            (
                privacy,
                "Go and Help is for people",
                ("16", "nicht wissentlich", "Minderjähriger"),
            ),
        )
        for entries, prefix, tokens in fixtures:
            value = next(
                value
                for source, value in entries.items()
                if source.startswith(prefix)
            )
            for token in tokens:
                self.assertIn(token, value)

    def test_existing_agreement_and_credits_remain_effective_unchanged(self):
        for document, rows in (
            ("agreement", AGREEMENT_GERMAN_ROWS),
            ("credits", CREDITS_ROWS),
        ):
            for source, original in zip(
                DOCUMENT_SOURCE_KEYS[document], rows["de"], strict=True
            ):
                self.assertEqual(POLICY_CATALOGS["de"][source], original)
                self.assertEqual(catalog("de")[source], original)
        self.assertEqual(len(AGREEMENT_GERMAN_ROWS["de"]), 51)
        self.assertEqual(
            CREDITS_ROWS["de"],
            (
                "Danksagungen",
                "Die offenen Karten und Open-Source-Projekte, die jede Go and Help-Karte zeichnen.",
                "Aktualisiert und gültig ab 1. Juni 2024",
                "Go and Help wird mit offenen Daten gezeichnet, die Freiwillige aus aller Welt erstellen. Diese Danksagungen sind Teil der Lizenzbedingungen, die wir gerne einhalten.",
                "Karten und Kartendaten",
                "Kartenkacheln von OpenFreeMap, Daten © OpenStreetMap-Mitwirkende, unter der Open Database License (ODbL).",
                "Kartendaten werden von OpenStreetMap unter der Open Database License (ODbL) bereitgestellt.",
                "OpenFreeMap baut auf mehreren großartigen Open-Source-Projekten auf, darunter Werkzeuge wie MapLibre, Planetiler und OpenMapTiles.",
            ),
        )
        self.assertEqual(
            AGREEMENT_GERMAN_ROWS["de"][
                DOCUMENT_SOURCE_KEYS["agreement"].index(
                    next(
                        source
                        for source in DOCUMENT_SOURCE_KEYS["agreement"]
                        if source.startswith("You agree to indemnify")
                    )
                )
            ],
            "Du erklärst dich bereit, Go and Help von Ansprüchen, Forderungen, Verlusten und angemessenen Kosten Dritter freizustellen und schadlos zu halten, die aus deinen Inhalten, deinem Verhalten, deinen Vereinbarungen mit anderen Nutzern oder deinem Verstoß gegen diese Vereinbarung entstehen — außer soweit das Recht deines Wohnorts dies nicht erlaubt oder der Anspruch aus unserem eigenen Fehlverhalten resultiert.",
        )

    def test_canonical_english_checksum_and_inventory_unchanged(self):
        frozen = json.dumps(
            POLICY_DOCUMENTS,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        self.assertEqual(
            hashlib.sha256(frozen).hexdigest(),
            "404ee59a08a5b8fc3f5238768659a8df32b7ff7eda9279353cb86110ff575f3d",
        )
        self.assertEqual(len(SOURCE_KEYS), 182)
        self.assertEqual(
            {key: len(row) for key, row in DOCUMENT_SOURCE_KEYS.items()},
            {"howto": 85, "privacy": 41, "agreement": 51, "credits": 8},
        )


if __name__ == "__main__":
    unittest.main()
