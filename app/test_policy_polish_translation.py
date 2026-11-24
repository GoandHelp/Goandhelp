import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_polish as agreement_data
from app import policy_catalog_howto_polish as howto_data
from app import policy_catalog_privacy_polish as privacy_data
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
from app.policy_catalog_agreement_polish import AGREEMENT_POLISH_ROWS
from app.policy_catalog_howto_polish import HOWTO_POLISH_ROWS
from app.policy_catalog_privacy_polish import PRIVACY_POLISH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_POLISH_ROWS", HOWTO_POLISH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_POLISH_ROWS", PRIVACY_POLISH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_POLISH_ROWS",
        AGREEMENT_POLISH_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["pl"], strict=True))


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


class PolishPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_polish_rows_are_complete_native_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"pl"})
                self.assertIsInstance(rows["pl"], tuple)
                self.assertEqual(len(rows["pl"]), count)
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
                    "pl"
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
                        normalized_numbers(source) <= normalized_numbers(value),
                        msg=f"Lost numeric fact in source: {source[:90]}",
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
        self.assertEqual(
            HOWTO_POLISH_ROWS["pl"][0], "Jak korzystać z Go and Help"
        )
        self.assertEqual(
            PRIVACY_POLISH_ROWS["pl"][0],
            "Polityka prywatności i plików cookie",
        )
        self.assertEqual(AGREEMENT_POLISH_ROWS["pl"][0], "Umowa użytkownika")
        plans = lookup(
            mapped("howto", HOWTO_POLISH_ROWS), "There are two options"
        )
        self.assertIn("Bilet miesięczny", plans)
        self.assertIn("Karnet roczny", plans)

    def test_polish_sources_are_native_and_credits_remain_intact(self):
        authored = POLICY_CATALOGS["pl"]
        effective = catalog("pl")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "pl"), ())
        self.assertEqual(missing_policy_sources(effective, "pl"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("pl", source), effective[source])
            self.assertEqual(translate("en", source), source)

        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["pl"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        self.assertEqual(authored["Credits"], "Podziękowania")
        self.assertEqual(effective["Credits"], "Podziękowania")
        self.assertEqual(translate("pl", "Credits"), "Podziękowania")
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)

        fresh: set[str] = set()
        for document, _, _, rows, _ in BATCH:
            entries = mapped(document, rows)
            fresh.update(entries)
            self.assertEqual(
                entries[POLICY_DOCUMENTS[document]["updated"]],
                "Zaktualizowano; obowiązuje od 1 czerwca 2024",
            )
            for source, value in entries.items():
                self.assertEqual(authored[source], value)
        self.assertEqual(len(fresh), 175)
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
        self.assertGreaterEqual(authored_total, 2566)
        self.assertGreaterEqual(effective_total, 2691)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["pl"], 0)
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

    def test_merged_safety_and_source_bound_privacy_and_agreement_clauses(self):
        howto = mapped("howto", HOWTO_POLISH_ROWS)
        privacy = mapped("privacy", PRIVACY_POLISH_ROWS)
        agreement = mapped("agreement", AGREEMENT_POLISH_ROWS)
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
                    "500 m–1 km",
                    "zapisane współrzędne pozostają na twoim koncie",
                    "żadne współrzędne nie są nigdzie wysyłane",
                    "twojego dokładnego położenia, które pozostaje prywatne",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Unii Europejskiej"),
            ),
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "nie sprawdzamy niczyich dokumentów tożsamości",
                    "karalności",
                    "nigdy gwarancją bezpieczeństwa",
                    "twój własny rozsądek",
                ),
            ),
            (
                privacy,
                "Off is the default for every account",
                (
                    "zapisane współrzędne nie są nikomu pokazywane",
                    "nie pojawiasz się na mapach",
                    "żadne współrzędne nie są przesyłane",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "Nigdy nie publikujemy zapisanego przez ciebie punktu",
                    "500 m–1 km",
                    "natychmiast zatrzymuje udostępnianie",
                    "nie usuwa zapisanych współrzędnych",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                (
                    "0,5–1 km",
                    "adres nigdy nie jest publikowany",
                    "tylko potwierdzonej przez ciebie osobie pomagającej",
                ),
            ),
            (
                privacy,
                "Go and Help is for people aged",
                ("co najmniej 16 lat", "Nie zbieramy świadomie danych dzieci"),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "odnawia się automatycznie co miesiąc",
                    "roczne — co rok, dopóki go nie anulujesz",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "do końca opłaconego już okresu",
                    "lokalne prawo wymaga zwrotu",
                    "nie podlega zwrotowi",
                    "Nie narusza to przysługującego ci",
                ),
            ),
            (
                agreement,
                "To the same extent",
                (
                    "większej z dwóch kwot",
                    "12 miesięcy poprzedzających roszczenie",
                    "50 dolarów amerykańskich",
                ),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "nie wyłącza ani nie ogranicza odpowiedzialności",
                    "nie wolno wyłączyć ani ograniczyć",
                    "niedbalstwem",
                    "oszustwo",
                    "bezwzględnie obowiązujących praw konsumenta",
                    "prawa lokalne pozostają nienaruszone",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "jeśli jesteś konsumentem",
                    "bezwzględnie obowiązujących przepisów konsumenckich",
                    "lokalnego sądu",
                    "pierwszeństwo ma ta zasada",
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
        self.assertIn("większej z dwóch kwot", cap)
        self.assertIn("12 miesięcy", cap)
        self.assertIn("50 dolarów amerykańskich", cap)

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
