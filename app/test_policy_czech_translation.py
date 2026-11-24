import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_czech as agreement_data
from app import policy_catalog_howto_czech as howto_data
from app import policy_catalog_privacy_czech as privacy_data
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
from app.policy_catalog_agreement_czech import AGREEMENT_CZECH_ROWS
from app.policy_catalog_howto_czech import HOWTO_CZECH_ROWS
from app.policy_catalog_privacy_czech import PRIVACY_CZECH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_CZECH_ROWS", HOWTO_CZECH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_CZECH_ROWS", PRIVACY_CZECH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_CZECH_ROWS",
        AGREEMENT_CZECH_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["cs"], strict=True))


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


class CzechPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_czech_rows_are_complete_native_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"cs"})
                self.assertIsInstance(rows["cs"], tuple)
                self.assertEqual(len(rows["cs"]), count)
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
                    "cs"
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
                    if len(source) >= 280:
                        self.assertGreaterEqual(len(value), len(source) * 0.60)
                        self.assertGreaterEqual(
                            len(value.split()), len(source.split()) * 0.50
                        )
                total += count
        self.assertEqual(total, 177)
        self.assertEqual(HOWTO_CZECH_ROWS["cs"][0], "Jak používat Go and Help")
        self.assertEqual(
            PRIVACY_CZECH_ROWS["cs"][0],
            "Zásady ochrany soukromí a cookies",
        )
        self.assertEqual(AGREEMENT_CZECH_ROWS["cs"][0], "Uživatelská smlouva")
        plans = lookup(
            mapped("howto", HOWTO_CZECH_ROWS), "There are two options"
        )
        self.assertIn("Měsíční jízdenka", plans)
        self.assertIn("Roční pas", plans)

    def test_all_czech_sources_are_effective_and_credits_remain_intact(self):
        authored = POLICY_CATALOGS["cs"]
        effective = catalog("cs")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "cs"), ())
        self.assertEqual(missing_policy_sources(effective, "cs"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("cs", source), effective[source])
            self.assertEqual(translate("en", source), source)

        original_credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["cs"], strict=True
            )
        )
        self.assertEqual(len(original_credits), 8)
        for source, value in original_credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)
        self.assertEqual(effective["Credits"], "Poděkování")

        fresh: set[str] = set()
        for document, _, _, rows, _ in BATCH:
            entries = mapped(document, rows)
            fresh.update(entries)
            self.assertEqual(
                entries[POLICY_DOCUMENTS[document]["updated"]],
                original_credits[POLICY_DOCUMENTS["credits"]["updated"]],
            )
            for source, value in entries.items():
                self.assertEqual(authored[source], value)
        self.assertEqual(len(fresh - set(original_credits)), 174)

        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 2392)
        self.assertGreaterEqual(effective_total, 2522)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["cs"], 0)
        for locale in (
            "cs",
            "da",
            "de",
            "es",
            "fi",
            "fr",
            "it",
            "nl",
            "pt",
            "ru",
            "sv",
            "ur",
        ):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_source_bound_privacy_and_agreement_guards(self):
        howto = mapped("howto", HOWTO_CZECH_ROWS)
        privacy = mapped("privacy", PRIVACY_CZECH_ROWS)
        agreement = mapped("agreement", AGREEMENT_CZECH_ROWS)
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
                    "500 m až 1 km",
                    "uložené souřadnice zůstávají v tvém účtu",
                    "žádné souřadnice se nikam neodesílají",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Evropské unii"),
            ),
            (
                privacy,
                "Off is the default for every account",
                (
                    "Vypnutá poloha je výchozím nastavením",
                    "tvoje uložené souřadnice nikdo neuvidí",
                    "žádné souřadnice se nikam neodesílají",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "Uložený bod nikdy nezveřejňujeme",
                    "500 m až 1 km",
                    "sdílení se okamžitě zastaví",
                    "uložené souřadnice se nesmažou",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                (
                    "0,5–1 km",
                    "zadaná adresa se nikdy nezveřejní",
                    "pouze s pomocníkem, kterého potvrdíš",
                ),
            ),
            (
                privacy,
                "Go and Help is for people aged",
                ("alespoň 16 let", "vědomě neshromažďujeme", "nezletilá osoba"),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "automaticky obnovuje každý měsíc",
                    "každý rok, dokud ho nezrušíš",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "do konce již zaplaceného období",
                    "místní zákon stanoví jinak",
                    "se nevyužitá část období nevrací",
                    "zůstává nedotčeno",
                ),
            ),
            (
                agreement,
                "To the same extent",
                (
                    "vyšší z částek",
                    "členské poplatky",
                    "dvanáct měsíců",
                    "50 amerických dolarů",
                ),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "Nic v této smlouvě nevylučuje ani neomezuje odpovědnost",
                    "nedbalostí",
                    "podvod",
                    "závazná práva spotřebitelů",
                    "závazná místní práva tím nejsou dotčena",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "spotřebitel",
                    "závazných spotřebitelských zákonů",
                    "místního soudu",
                    "přednost má toto pravidlo",
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
        self.assertIn("členské poplatky", liability)
        self.assertIn("dvanáct měsíců", liability)
        self.assertIn("50 amerických dolarů", liability)

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
