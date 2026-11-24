import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_danish as agreement_data
from app import policy_catalog_howto_danish as howto_data
from app import policy_catalog_privacy_danish as privacy_data
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
from app.policy_catalog_agreement_danish import AGREEMENT_DANISH_ROWS
from app.policy_catalog_howto_danish import HOWTO_DANISH_ROWS
from app.policy_catalog_privacy_danish import PRIVACY_DANISH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_DANISH_ROWS", HOWTO_DANISH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_DANISH_ROWS", PRIVACY_DANISH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_DANISH_ROWS",
        AGREEMENT_DANISH_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["da"], strict=True))


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


class DanishPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_danish_rows_are_full_native_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"da"})
                self.assertIsInstance(rows["da"], tuple)
                self.assertEqual(len(rows["da"]), count)
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
                    "da"
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
                            len(value.split()), len(source.split()) * 0.60
                        )
                total += count
        self.assertEqual(total, 177)
        self.assertEqual(
            HOWTO_DANISH_ROWS["da"][0], "Sådan bruger du Go and Help"
        )
        self.assertEqual(
            PRIVACY_DANISH_ROWS["da"][0], "Politik om privatliv og cookies"
        )
        self.assertEqual(AGREEMENT_DANISH_ROWS["da"][0], "Brugeraftale")
        self.assertEqual(HOWTO_DANISH_ROWS["da"][24], "Medlemskab")
        plans = lookup(
            mapped("howto", HOWTO_DANISH_ROWS), "There are two options"
        )
        self.assertIn("Månedskort", plans)
        self.assertIn("Årspas", plans)

    def test_complete_authored_effective_sources_and_preserved_credits(self):
        authored = POLICY_CATALOGS["da"]
        effective = catalog("da")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "da"), ())
        self.assertEqual(missing_policy_sources(effective, "da"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("da", source), effective[source])
            self.assertEqual(translate("en", source), source)

        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["da"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)
        self.assertEqual(
            credits["Updated and effective 1 June 2024"],
            "Opdateret og gældende fra 1. juni 2024",
        )
        self.assertEqual(credits["Credits"], "Anerkendelser")
        self.assertEqual(translate("da", "Credits"), "Tak til bidragyderne")
        self.assertNotEqual(translate("da", "Credits"), credits["Credits"])

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
        self.assertGreaterEqual(authored_total, 2044)
        self.assertGreaterEqual(effective_total, 2184)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["da"], 0)
        for locale in ("de", "es", "fr", "it", "nl", "pt", "ru", "sv", "ur"):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_inventory_and_representative_full_clauses(self):
        howto = mapped("howto", HOWTO_DANISH_ROWS)
        privacy = mapped("privacy", PRIVACY_DANISH_ROWS)
        agreement = mapped("agreement", AGREEMENT_DANISH_ROWS)
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
                ("500 m", "1 km", "ingen koordinater", "alle brugere"),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Den Europæiske Union"),
            ),
            (
                privacy,
                "Off is the default for every account",
                (
                    "Fra",
                    "vises dine gemte koordinater ikke for nogen",
                    "ingen koordinater overføres",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "500 m",
                    "1 km",
                    "med det samme",
                    "uden at de koordinater, du har gemt, bliver slettet",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                ("0,5–1 km", "offentliggøres aldrig", "kun med den hjælper"),
            ),
            (
                privacy,
                "Go and Help is for people aged",
                ("16 år", "bevidst", "mindreårig"),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                ("Stripe", "hver måned", "hvert år", "indtil du opsiger"),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "udgangen af den periode",
                    "lokal lovgivning kræver andet",
                    "refunderes",
                    "gælder fortsat",
                ),
            ),
            (
                agreement,
                "To the same extent",
                ("det højeste af", "12 måneder", "50 amerikanske dollar"),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "uagtsomhed",
                    "bedrageri",
                    "ufravigelige forbrugerrettigheder",
                    "påvirkes ikke",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "forbruger",
                    "ufravigelige forbrugerregler",
                    "lokale domstole",
                    "forrang",
                ),
            ),
        )
        for values, prefix, tokens in fixtures:
            value = lookup(values, prefix)
            for token in tokens:
                with self.subTest(prefix=prefix, token=token):
                    self.assertIn(token, value)
        cap = lookup(agreement, "To the same extent")
        self.assertGreater(len(cap.split()), 30)
        self.assertIn("12 måneder", cap)
        self.assertIn("50 amerikanske dollar", cap)
        self.assertIn("og 50 amerikanske dollar", cap)

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
