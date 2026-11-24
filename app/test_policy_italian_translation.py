import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_italian as agreement_data
from app import policy_catalog_howto_italian as howto_data
from app import policy_catalog_privacy_italian as privacy_data
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
from app.policy_catalog_agreement_italian import AGREEMENT_ITALIAN_ROWS
from app.policy_catalog_howto_italian import HOWTO_ITALIAN_ROWS
from app.policy_catalog_privacy_italian import PRIVACY_ITALIAN_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_ITALIAN_ROWS", HOWTO_ITALIAN_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_ITALIAN_ROWS", PRIVACY_ITALIAN_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_ITALIAN_ROWS",
        AGREEMENT_ITALIAN_ROWS,
        51,
    ),
)
PROPER_NAMES = (
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
)


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["it"], strict=True))


def lookup(values: dict[str, str], prefix: str) -> str:
    matches = [
        value for source, value in values.items() if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


class ItalianPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_rows_validate_and_keep_canonical_field_counts(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"it"})
                self.assertIsInstance(rows["it"], tuple)
                self.assertEqual(len(rows["it"]), count)
                self.assertEqual(len(DOCUMENT_SOURCE_KEYS[document]), count)
                tree = ast.parse(
                    Path(inspect.getfile(module)).read_text(encoding="utf-8")
                )
                assignments = [
                    node
                    for node in tree.body
                    if isinstance(node, ast.AnnAssign)
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
                    "it"
                ]
                for source, value in mapped(document, rows).items():
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertEqual(placeholders(source), placeholders(value))
                    self.assertEqual(validated[source], value)
                    for proper in PROPER_NAMES:
                        if proper in source:
                            self.assertIn(proper, value)
                    for number in re.findall(r"\d+(?:[.,]\d+)?", source):
                        self.assertIn(number, value)
                    if len(source.split()) >= 35:
                        self.assertGreaterEqual(
                            len(value.split()), len(source.split()) * 0.68
                        )
                        words = re.findall(r"[A-Za-z]+", source)
                        for index in range(len(words) - 5):
                            self.assertNotIn(
                                " ".join(words[index : index + 6]), value
                            )
                total += count
        self.assertEqual(total, 177)

    def test_all_italian_document_sources_are_authored_and_effective(self):
        authored = POLICY_CATALOGS["it"]
        effective = catalog("it")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "it"), ())
        self.assertEqual(missing_policy_sources(effective, "it"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("it", source), effective[source])
            self.assertEqual(translate("en", source), source)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["it"], strict=True
            )
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
        batch_sources: set[str] = set()
        for document, _, _, rows, _ in BATCH:
            entries = mapped(document, rows)
            batch_sources.update(entries)
            self.assertEqual(
                entries[POLICY_DOCUMENTS[document]["updated"]],
                credits[POLICY_DOCUMENTS[document]["updated"]],
            )
            for source, value in entries.items():
                self.assertEqual(authored[source], value)
        self.assertEqual(len(batch_sources - set(credits)), 174)
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 1348)
        self.assertGreaterEqual(effective_total, 1508)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        for locale in ("de", "es", "fr", "it", "ru", "ur"):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_representative_full_legal_fields(self):
        howto = mapped("howto", HOWTO_ITALIAN_ROWS)
        privacy = mapped("privacy", PRIVACY_ITALIAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_ITALIAN_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        fixtures = (
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "documenti d'identità",
                    "precedenti penali",
                    "mai una garanzia",
                    "giudizio personale",
                ),
            ),
            (
                howto,
                "Set my location offers",
                ("500m", "1km", "nessuna coordinata", "tutti gli utenti"),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Unione Europea"),
            ),
            (
                howto,
                "Do not take on work",
                (
                    "adulti vulnerabili",
                    "abbattimento di alberi",
                    "non è una qualifica",
                ),
            ),
            (
                howto,
                "Go and Help is used all over",
                ("visti", "responsabilità tua, non nostra"),
            ),
            (
                howto,
                "There are two options",
                ("Biglietto mensile", "Pass annuale", "Stripe"),
            ),
            (
                privacy,
                "We never publish your stored point",
                ("500m", "1km", "subito", "senza eliminare"),
            ),
            (
                privacy,
                "Help requests work the same way",
                ("0.5–1 km", "non viene mai pubblicato"),
            ),
            (
                privacy,
                "Go and Help is for people",
                ("16 anni", "consapevolmente", "minori"),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "si rinnova ogni mese",
                    "ogni anno",
                    "finché non la disdici",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "periodo già pagato",
                    "Salvo che la legge locale",
                    "non vengono rimborsati",
                    "recesso",
                ),
            ),
            (
                agreement,
                "To the same extent",
                ("maggiore", "dodici mesi", "cinquanta dollari statunitensi"),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                ("negligenza", "frode", "diritti inderogabili"),
            ),
            (
                agreement,
                "This agreement is governed",
                ("consumatore", "prevale la norma inderogabile"),
            ),
        )
        for values, prefix, tokens in fixtures:
            value = lookup(values, prefix)
            for token in tokens:
                with self.subTest(prefix=prefix, token=token):
                    self.assertIn(token, value)
        full_liability = lookup(agreement, "To the same extent")
        self.assertGreater(len(full_liability.split()), 30)
        self.assertIn("o cinquanta dollari statunitensi", full_liability)

    def test_canonical_english_source_checksum_is_unchanged(self):
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


if __name__ == "__main__":
    unittest.main()
