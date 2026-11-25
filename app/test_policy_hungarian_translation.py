import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_hungarian as agreement_data
from app import policy_catalog_howto_hungarian as howto_data
from app import policy_catalog_privacy_hungarian as privacy_data
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
from app.policy_catalog_agreement_hungarian import AGREEMENT_HUNGARIAN_ROWS
from app.policy_catalog_howto_hungarian import HOWTO_HUNGARIAN_ROWS
from app.policy_catalog_privacy_hungarian import PRIVACY_HUNGARIAN_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_HUNGARIAN_ROWS", HOWTO_HUNGARIAN_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_HUNGARIAN_ROWS",
        PRIVACY_HUNGARIAN_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_HUNGARIAN_ROWS",
        AGREEMENT_HUNGARIAN_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["hu"], strict=True))


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


class HungarianPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_hungarian_rows_are_complete_native_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"hu"})
                self.assertIsInstance(rows["hu"], tuple)
                self.assertEqual(len(rows["hu"]), count)
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
                    "hu"
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
                        msg=f"Lost numeric fact in source: {source[:90]}",
                    )
                    if len(source) >= 280:
                        self.assertGreaterEqual(len(value), len(source) * 0.60)
                        self.assertGreaterEqual(
                            len(value.split()), len(source.split()) * 0.35
                        )
                    self.assertNotIn("This ", value)
                    self.assertNotIn("We do not ", value)
                total += count

        self.assertEqual(total, 177)
        self.assertEqual(
            HOWTO_HUNGARIAN_ROWS["hu"][0], "A Go and Help használata"
        )
        self.assertEqual(
            PRIVACY_HUNGARIAN_ROWS["hu"][0],
            "Adatvédelmi és sütikezelési szabályzat",
        )
        self.assertEqual(
            AGREEMENT_HUNGARIAN_ROWS["hu"][0], "Felhasználói megállapodás"
        )
        plans = lookup(
            mapped("howto", HOWTO_HUNGARIAN_ROWS), "There are two options"
        )
        self.assertIn("Havi jegy", plans)
        self.assertIn("Éves bérlet", plans)

    def test_hungarian_sources_are_native_and_credits_remain_intact(self):
        authored = POLICY_CATALOGS["hu"]
        effective = catalog("hu")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "hu"), ())
        self.assertEqual(missing_policy_sources(effective, "hu"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("hu", source), effective[source])
            self.assertEqual(translate("en", source), source)

        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["hu"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        self.assertEqual(authored["Credits"], "Köszönetnyilvánítás")
        self.assertEqual(effective["Credits"], "Köszönetnyilvánítás")
        self.assertEqual(translate("hu", "Credits"), "Köszönetnyilvánítás")
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != POLICY_DOCUMENTS["credits"]["title"]:
                self.assertEqual(effective[source], value)

        distinct_sources: set[str] = set()
        row_total = 0
        for document, _, _, rows, expected in BATCH:
            entries = mapped(document, rows)
            row_total += len(rows["hu"])
            distinct_sources.update(entries)
            self.assertEqual(
                entries[POLICY_DOCUMENTS[document]["updated"]],
                "Frissítve és hatályos 2024. június 1-től",
            )
            for source, value in entries.items():
                self.assertEqual(authored[source], value)
            self.assertEqual(len(rows["hu"]), expected)
        self.assertEqual(row_total, 177)
        self.assertEqual(len(distinct_sources), 175)
        self.assertEqual(len(distinct_sources - set(credits)), 174)

        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 2740)
        self.assertGreaterEqual(effective_total, 2860)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["hu"], 0)
        for locale in (
            "cs",
            "da",
            "de",
            "es",
            "fi",
            "fr",
            "it",
            "nl",
            "pl",
            "pt",
            "ru",
            "sv",
            "ur",
        ):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_source_bound_privacy_and_agreement_clauses(self):
        howto = mapped("howto", HOWTO_HUNGARIAN_ROWS)
        privacy = mapped("privacy", PRIVACY_HUNGARIAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_HUNGARIAN_ROWS)
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
                    "három lehetőséget kínál, köztes mód nélkül",
                    "a mentett koordinátáid a fiókodban maradnak",
                    "koordinátát nem küldünk sehova",
                    "500 m és 1 km közötti távolságra",
                    "a pontos helyedtől; ez utóbbi privát marad",
                ),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Európai Unió egész területén"),
            ),
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "Nem felügyeljük, kísérjük vagy látogatjuk a találkozókat",
                    "személyazonosító okmányait",
                    "a saját ítélőképességed",
                ),
            ),
            (
                privacy,
                "Off is the default for every account",
                (
                    "a mentett koordinátáidat senkinek sem mutatjuk meg",
                    "nem jelensz meg térképeken",
                    "egyetlen koordinátádat sem továbbítjuk",
                ),
            ),
            (
                privacy,
                "We never publish your stored point",
                (
                    "A mentett pontodat soha nem tesszük közzé",
                    "500 m és 1 km közötti távolságra",
                    "a megosztás azonnal leáll",
                    "a mentett koordináták nem törlődnek",
                ),
            ),
            (
                privacy,
                "Help requests work the same way",
                (
                    "0,5–1 km",
                    "a megadott címed pedig soha nem kerül nyilvánosságra",
                    "kizárólag az általad megerősített segítővel",
                ),
            ),
            (
                privacy,
                "Go and Help is for people aged",
                (
                    "legalább 16 évesnek kell lenned",
                    "Gyermekek adatait tudatosan nem gyűjtjük",
                ),
            ),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "A havi tagság havonta, az éves tagság évente automatikusan megújul",
                    "évente automatikusan megújul, amíg le nem mondod",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "az előre kifizetett időszak végéig megmaradnak",
                    "A helyi jogszabályban előírt esetek kivételével",
                    "nem térítjük vissza",
                    "nem érinti a lakóhelyed szerinti törvényes elállási vagy lemondási jogodat",
                ),
            ),
            (
                agreement,
                "To the same extent",
                (
                    "az alábbi két összeg közül a nagyobb",
                    "a követelést megelőző 12 hónapban",
                    "50 amerikai dollár",
                ),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                (
                    "A megállapodás egyetlen rendelkezése sem zár ki vagy korlátoz olyan felelősséget",
                    "nem lehet kizárni vagy korlátozni",
                    "gondatlanság miatt",
                    "csalásért",
                    "a kötelező fogyasztói jogokat",
                    "a kötelező helyi jogaid változatlanul megilletnek",
                ),
            ),
            (
                agreement,
                "This agreement is governed",
                (
                    "ha fogyasztó vagy",
                    "kötelező fogyasztóvédelmi jogának védelmétől",
                    "helyi bíróságodhoz fordulj",
                    "a kötelező szabály az irányadó",
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
        self.assertIn("az alábbi két összeg közül a nagyobb", cap)
        self.assertIn("12 hónapban", cap)
        self.assertIn("50 amerikai dollár", cap)

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
