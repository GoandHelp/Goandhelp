import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_romanian as agreement_data
from app import policy_catalog_howto_romanian as howto_data
from app import policy_catalog_privacy_romanian as privacy_data
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
from app.policy_catalog_agreement_romanian import AGREEMENT_ROMANIAN_ROWS
from app.policy_catalog_howto_romanian import HOWTO_ROMANIAN_ROWS
from app.policy_catalog_privacy_romanian import PRIVACY_ROMANIAN_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_ROMANIAN_ROWS", HOWTO_ROMANIAN_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_ROMANIAN_ROWS",
        PRIVACY_ROMANIAN_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_ROMANIAN_ROWS",
        AGREEMENT_ROMANIAN_ROWS,
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
    "Open Database License",
    "ODbL",
    "©",
    "SHA-256",
    "https://",
)


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["ro"], strict=True))


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


class RomanianPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_romanian_rows_are_complete_native_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"ro"})
                self.assertIsInstance(rows["ro"], tuple)
                self.assertEqual(len(rows["ro"]), count)
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
                    "ro"
                ]
                entries = mapped(document, rows)
                for source, value in entries.items():
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertEqual(placeholders(source), placeholders(value))
                    self.assertEqual(validated[source], value)
                    for proper in PROPER_NAMES:
                        if proper in source:
                            self.assertIn(proper, value)
                    self.assertTrue(
                        normalized_numbers(source) <= normalized_numbers(value),
                        msg=f"Lost numeric fact: {source[:90]}",
                    )
                    if len(source) >= 280:
                        self.assertGreaterEqual(len(value), len(source) * 0.60)
                        self.assertGreaterEqual(
                            len(value.split()), len(source.split()) * 0.50
                        )
                    self.assertNotIn("This ", value)
                    self.assertNotIn("We do not ", value)
                total += count
        self.assertEqual(total, 177)
        howto = mapped("howto", HOWTO_ROMANIAN_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Cum să folosești Go and Help"
        )
        plans = lookup(howto, "There are two options")
        self.assertIn("Bilet lunar", plans)
        self.assertIn("Abonament anual", plans)

    def test_all_romanian_sources_and_credits_are_native_and_complete(self):
        authored = POLICY_CATALOGS["ro"]
        effective = catalog("ro")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "ro"), ())
        self.assertEqual(missing_policy_sources(effective, "ro"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("ro", source), effective[source])
            self.assertEqual(translate("en", source), source)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["ro"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        self.assertEqual(authored["Credits"], "Mulțumiri")
        self.assertEqual(effective["Credits"], "Mulțumiri")
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)
        authored_sources: set[str] = set()
        row_count = 0
        for document, _, _, rows, expected in BATCH:
            entries = mapped(document, rows)
            authored_sources.update(entries)
            row_count += len(rows["ro"])
            self.assertEqual(len(rows["ro"]), expected)
            self.assertEqual(
                entries[POLICY_DOCUMENTS[document]["updated"]],
                "Actualizat și în vigoare de la 1 iunie 2024",
            )
            for source, value in entries.items():
                self.assertEqual(authored[source], value)
        self.assertEqual(
            (
                row_count,
                len(authored_sources),
                len(authored_sources - set(credits)),
            ),
            (177, 175, 174),
        )
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 2914)
        self.assertGreaterEqual(effective_total, 3029)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["ro"], 0)
        for locale in (
            "cs",
            "da",
            "de",
            "es",
            "fi",
            "fr",
            "hu",
            "it",
            "nl",
            "pl",
            "pt",
            "ru",
            "sv",
            "ur",
        ):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_source_bound_privacy_agreement_clauses(self):
        howto = mapped("howto", HOWTO_ROMANIAN_ROWS)
        privacy = mapped("privacy", PRIVACY_ROMANIAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_ROMANIAN_ROWS)
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
                    "trei poziții și nimic între ele",
                    "coordonatele salvate rămân în contul tău",
                    "nicio coordonată nu este transmisă nicăieri",
                    "distanță între 500 m și 1 km",
                    "poziția ta exactă",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Uniunea Europeană"),
            ),
            (
                howto,
                "Go and Help is an introduction tool",
                ("Nu supraveghem", "actele de identitate", "Judecata ta"),
            ),
            (
                privacy,
                "Off is the default for every account",
                (
                    "Dezactivarea este setarea implicită",
                    "nu sunt afișate nimănui",
                    "nu apari pe hărți",
                    "nicio coordonată nu este transmisă",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "Nu publicăm niciodată punctul salvat",
                    "500 m și 1 km",
                    "partajarea se oprește imediat",
                    "fără ștergerea coordonatelor salvate",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                (
                    "0,5–1 km",
                    "adresa pe care o introduci nu este publicată niciodată",
                    "numai ajutorului pe care îl confirmi",
                ),
            ),
            (
                privacy,
                "Go and Help is for people aged",
                (
                    "cel puțin 16 ani",
                    "Nu colectăm cu bună știință informații despre copii",
                ),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "Abonamentul lunar se reînnoiește lunar",
                    "cel anual se reînnoiește anual",
                    "până când îl anulezi",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "până la sfârșitul perioadei deja plătite",
                    "Cu excepția cazurilor în care legislația locală impune altfel",
                    "nu sunt rambursate",
                    "drept legal de retragere sau anulare",
                ),
            ),
            (
                agreement,
                "To the same extent",
                (
                    "cea mai mare dintre următoarele două sume",
                    "abonamentelor pe care ni le-ai plătit în cele 12 luni",
                    "50 de dolari americani",
                ),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "Nicio prevedere din acest acord nu exclude și nu limitează răspunderea",
                    "legea nu permite să o excluzi sau să o limitezi",
                    "cauzate de neglijență",
                    "pentru fraudă",
                    "drepturile obligatorii ale consumatorilor",
                    "drepturile tale locale obligatorii rămân neafectate",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "dacă ești consumator",
                    "normele obligatorii ale legislației privind consumatorii",
                    "instanțele locale",
                    "prevalează norma obligatorie",
                ),
            ),
        )
        for values, prefix, tokens in fixtures:
            value = lookup(values, prefix)
            for token in tokens:
                with self.subTest(prefix=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "To the same extent")
        self.assertGreater(len(maximum.split()), 30)
        self.assertIn("cea mai mare dintre următoarele două sume", maximum)
        self.assertIn("12 luni", maximum)
        self.assertIn("50 de dolari americani", maximum)

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
