import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_dutch as agreement_data
from app import policy_catalog_howto_dutch as howto_data
from app import policy_catalog_privacy_dutch as privacy_data
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
from app.policy_catalog_agreement_dutch import AGREEMENT_DUTCH_ROWS
from app.policy_catalog_howto_dutch import HOWTO_DUTCH_ROWS
from app.policy_catalog_privacy_dutch import PRIVACY_DUTCH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_DUTCH_ROWS", HOWTO_DUTCH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_DUTCH_ROWS", PRIVACY_DUTCH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_DUTCH_ROWS",
        AGREEMENT_DUTCH_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["nl"], strict=True))


def lookup(values: dict[str, str], prefix: str) -> str:
    matches = [
        value for source, value in values.items() if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def normalized_numbers(text: str) -> set[str]:
    return {
        number.replace(",", ".")
        for number in re.findall(r"\d+(?:[.,]\d+)?", text)
    }


class DutchPolicyTranslationTests(unittest.TestCase):
    def test_exact_dutch_literal_rows_validate_and_are_complete(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"nl"})
                self.assertIsInstance(rows["nl"], tuple)
                self.assertEqual(len(rows["nl"]), count)
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
                    "nl"
                ]
                for source, value in mapped(document, rows).items():
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertEqual(placeholders(source), placeholders(value))
                    self.assertEqual(validated[source], value)
                    for proper in PROPER_NAMES:
                        if proper in source:
                            self.assertIn(proper, value)
                    self.assertTrue(
                        normalized_numbers(source) <= normalized_numbers(value)
                    )
                    if len(source.split()) >= 35:
                        self.assertGreaterEqual(
                            len(value.split()), len(source.split()) * 0.68
                        )
                total += count
        self.assertEqual(total, 177)

    def test_all_sources_are_native_and_credits_remain_unchanged(self):
        authored = POLICY_CATALOGS["nl"]
        effective = catalog("nl")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "nl"), ())
        self.assertEqual(missing_policy_sources(effective, "nl"), ())
        for source in SOURCE_KEYS:
            if source == "Credits":
                self.assertEqual(authored[source], source)
                self.assertEqual(effective[source], source)
                self.assertEqual(translate("nl", source), source)
            else:
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertEqual(translate("nl", source), effective[source])
            self.assertEqual(translate("en", source), source)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["nl"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)
        self.assertEqual(credits["Credits"], "Credits")
        fresh: set[str] = set()
        for document, _, _, rows, _ in BATCH:
            entries = mapped(document, rows)
            fresh.update(entries)
            self.assertEqual(
                entries[POLICY_DOCUMENTS[document]["updated"]],
                credits[POLICY_DOCUMENTS["credits"]["updated"]],
            )
            for source, value in entries.items():
                self.assertEqual(authored[source], value)
        self.assertEqual(len(fresh - set(credits)), 174)
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 1696)
        self.assertGreaterEqual(effective_total, 1846)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["nl"], 0)
        for locale in ("de", "es", "fr", "it", "pt", "ru", "ur"):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_representative_full_legal_fields(self):
        howto = mapped("howto", HOWTO_DUTCH_ROWS)
        privacy = mapped("privacy", PRIVACY_DUTCH_ROWS)
        agreement = mapped("agreement", AGREEMENT_DUTCH_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        fixtures = (
            (
                howto,
                "Set my location offers",
                (
                    "500 m",
                    "1 km",
                    "geen enkele coördinaat verzonden",
                    "alle gebruikers",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Europese Unie"),
            ),
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "identiteitsbewijzen",
                    "strafblad",
                    "nooit een garantie",
                    "eigen oordeel",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "500 m",
                    "1 km",
                    "onmiddellijk",
                    "zonder de opgeslagen coördinaten te verwijderen",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                ("0,5–1 km", "nooit gepubliceerd"),
            ),
            (
                privacy,
                "Go and Help is for people",
                ("16 jaar", "niet bewust", "minderjarige"),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "elke maand automatisch",
                    "elk jaar",
                    "totdat je opzegt",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "tot het einde",
                    "Tenzij de lokale wet anders vereist",
                    "niet terugbetaald",
                    "blijft van toepassing",
                ),
            ),
            (
                agreement,
                "To the same extent",
                ("hoogste van", "twaalf maanden", "vijftig Amerikaanse dollar"),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "nalatigheid",
                    "fraude",
                    "dwingende consumentenrechten",
                    "onaangetast",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "consument",
                    "dwingend consumentenrecht",
                    "lokale rechtbank",
                    "gaat die dwingende regel voor",
                ),
            ),
        )
        for values, prefix, tokens in fixtures:
            value = lookup(values, prefix)
            for token in tokens:
                with self.subTest(prefix=prefix, token=token):
                    self.assertIn(token, value)
        liability = lookup(agreement, "To the same extent")
        self.assertGreater(len(liability.split()), 30)
        self.assertIn("twaalf maanden", liability)
        self.assertIn("vijftig Amerikaanse dollar", liability)

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
