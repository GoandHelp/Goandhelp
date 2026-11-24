import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_finnish as agreement_data
from app import policy_catalog_howto_finnish as howto_data
from app import policy_catalog_privacy_finnish as privacy_data
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
from app.policy_catalog_agreement_finnish import AGREEMENT_FINNISH_ROWS
from app.policy_catalog_howto_finnish import HOWTO_FINNISH_ROWS
from app.policy_catalog_privacy_finnish import PRIVACY_FINNISH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_FINNISH_ROWS", HOWTO_FINNISH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_FINNISH_ROWS", PRIVACY_FINNISH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_FINNISH_ROWS",
        AGREEMENT_FINNISH_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["fi"], strict=True))


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


class FinnishPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_finnish_rows_are_full_native_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"fi"})
                self.assertIsInstance(rows["fi"], tuple)
                self.assertEqual(len(rows["fi"]), count)
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
                    "fi"
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
                            len(value.split()), len(source.split()) * 0.35
                        )
                total += count
        self.assertEqual(total, 177)
        self.assertEqual(
            HOWTO_FINNISH_ROWS["fi"][0], "Go and Help -sovelluksen käyttö"
        )
        self.assertEqual(
            PRIVACY_FINNISH_ROWS["fi"][0], "Tietosuoja- ja evästekäytäntö"
        )
        self.assertEqual(AGREEMENT_FINNISH_ROWS["fi"][0], "Käyttäjäsopimus")
        plan_terms = lookup(
            mapped("howto", HOWTO_FINNISH_ROWS), "There are two options"
        )
        self.assertIn("Kuukausilippu", plan_terms)
        self.assertIn("Vuosipassi", plan_terms)

    def test_complete_finnish_sources_preserve_existing_credits(self):
        authored = POLICY_CATALOGS["fi"]
        effective = catalog("fi")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "fi"), ())
        self.assertEqual(missing_policy_sources(effective, "fi"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("fi", source), effective[source])
            self.assertEqual(translate("en", source), source)

        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["fi"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)
        self.assertEqual(credits["Credits"], "Kiitokset")
        self.assertEqual(translate("fi", "Credits"), "Kiitokset")

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
        self.assertGreaterEqual(authored_total, 2218)
        self.assertGreaterEqual(effective_total, 2353)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["fi"], 0)
        for locale in (
            "da",
            "de",
            "es",
            "fr",
            "it",
            "nl",
            "pt",
            "ru",
            "sv",
            "ur",
        ):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_source_bound_privacy_and_agreement_clauses(self):
        howto = mapped("howto", HOWTO_FINNISH_ROWS)
        privacy = mapped("privacy", PRIVACY_FINNISH_ROWS)
        agreement = mapped("agreement", AGREEMENT_FINNISH_ROWS)
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
                    "koordinaattisi säilyvät tililläsi",
                    "niitä ei lähetetä minnekään",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Euroopan unionissa"),
            ),
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "henkilöllisyystodistuksia",
                    "rikosrekisteriä",
                    "eivät koskaan tae",
                    "harkintasi",
                ),
            ),
            (
                privacy,
                "Off is the default for every account",
                (
                    "eivät näy kenellekään",
                    "et näy kartoilla",
                    "eikä koordinaatteja lähetetä eteenpäin",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "500 m",
                    "1 km",
                    "jakaminen päättyy heti",
                    "koordinaattejasi poisteta",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                (
                    "0,5–1 km",
                    "osoitetta koskaan julkaista",
                    "vain vahvistamallesi auttajalle",
                ),
            ),
            (
                privacy,
                "Go and Help is for people aged",
                ("vähintään 16-vuotias", "tietoisesti", "alaikäisellä"),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "kuukausittain",
                    "vuosittain",
                    "kunnes peruutat sen",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "maksamasi kauden loppuun",
                    "paikallinen laki edellyttää muuta",
                    "ei palauteta",
                    "pysyvät voimassa",
                ),
            ),
            (
                agreement,
                "To the same extent",
                (
                    "suurempi seuraavista",
                    "12 kuukauden",
                    "ja 50 Yhdysvaltain dollaria",
                ),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "ei sulje pois tai rajoita",
                    "huolimattomuudesta",
                    "petoksesta",
                    "pakottavista kuluttajanoikeuksista",
                    "heikkene",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "kuluttaja",
                    "pakottavan kuluttajalainsäädännön",
                    "paikallisessa tuomioistuimessa",
                    "ensisijainen",
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
        self.assertIn("12 kuukauden", liability)
        self.assertIn("50 Yhdysvaltain dollaria", liability)
        self.assertIn("jäsenmaksut ja 50 Yhdysvaltain dollaria", liability)

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
