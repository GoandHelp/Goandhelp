import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_amharic as agreement_data
from app import policy_catalog_howto_amharic as howto_data
from app import policy_catalog_privacy_amharic as privacy_data
from app.interface_i18n import catalog
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
from app.policy_catalog_agreement_amharic import AGREEMENT_AMHARIC_ROWS
from app.policy_catalog_howto_amharic import HOWTO_AMHARIC_ROWS
from app.policy_catalog_privacy_amharic import PRIVACY_AMHARIC_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_AMHARIC_ROWS", HOWTO_AMHARIC_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_AMHARIC_ROWS", PRIVACY_AMHARIC_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_AMHARIC_ROWS",
        AGREEMENT_AMHARIC_ROWS,
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
LATIN_ALLOWED = tuple(sorted(PROPER_NAMES, key=len, reverse=True))
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
ETHIOPIC = re.compile(r"[\u1200-\u137F]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
ENGLISH_FUNCTION_WORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "and",
        "any",
        "are",
        "because",
        "before",
        "between",
        "but",
        "can",
        "could",
        "did",
        "does",
        "each",
        "for",
        "from",
        "have",
        "her",
        "here",
        "him",
        "his",
        "how",
        "into",
        "its",
        "may",
        "more",
        "most",
        "must",
        "not",
        "our",
        "out",
        "over",
        "she",
        "should",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "under",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "will",
        "with",
        "without",
        "would",
        "you",
        "your",
    }
)
AMHARIC_CREDITS = (
    "ምስጋናዎች",
    "እያንዳንዱን የGo and Help ካርታ የሚስሉ ክፍት ካርታዎችና ክፍት ምንጭ ፕሮጀክቶች።",
    "በ1 ጁን 2024 ተዘምኗል እና ተፈጻሚ ሆኗል",
    "Go and Help በዓለም ዙሪያ ባሉ በጎ ፈቃደኞች በተዘጋጀ ክፍት ውሂብ ላይ ይሳላል። እነዚህ ምስጋናዎች በደስታ የምናከብራቸው የፈቃድ ውሎች አካል ናቸው።",
    "ካርታዎችና የካርታ ውሂብ",
    "የካርታ ንጣፎች በOpenFreeMap፣ ውሂብ © የOpenStreetMap አበርካቾች፣ በOpen Database License (ODbL) ሥር።",
    "የካርታ ውሂብ በOpenStreetMap በOpen Database License (ODbL) ሥር ይቀርባል።",
    "OpenFreeMap እንደ MapLibre፣ Planetiler እና OpenMapTiles ያሉ መሣሪያዎችን ጨምሮ በብዙ ድንቅ ክፍት ምንጭ ፕሮጀክቶች ላይ የተመሠረተ ነው።",
)
AMHARIC_DATE = "በ1 ጁን 2024 ተዘምኗል እና ተፈጻሚ ሆኗል"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["am"], strict=True))


def lookup(values: dict[str, str], document: str, prefix: str) -> str:
    matches = [
        values[source]
        for source in DOCUMENT_SOURCE_KEYS[document]
        if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def normalized_numbers(text: str) -> set[str]:
    return {number.replace(",", ".") for number in NUMBERS.findall(text)}


def latin_residue(text: str) -> list[str]:
    for name in LATIN_ALLOWED:
        text = text.replace(name, " ")
    return LATIN_WORD.findall(text)


class AmharicPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_and_full_length(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"am"})
                self.assertIsInstance(rows["am"], tuple)
                self.assertEqual(len(rows["am"]), count)
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
                    "am"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["am"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, ETHIOPIC)
                        residue = {
                            word.lower() for word in latin_residue(value)
                        }
                        self.assertFalse(residue & ENGLISH_FUNCTION_WORDS)
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(
                            normalized_numbers(source)
                            <= normalized_numbers(value),
                            msg=f"Lost numeric fact: {source[:100]}",
                        )
                        if len(source) >= 280:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.35
                            )
                            self.assertGreaterEqual(
                                len(value.split()), len(source.split()) * 0.40
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["am"].count(AMHARIC_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_AMHARIC_ROWS)
        privacy = mapped("privacy", PRIVACY_AMHARIC_ROWS)
        agreement = mapped("agreement", AGREEMENT_AMHARIC_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help እንዴት እንደሚጠቀሙ"
        )
        self.assertEqual(howto["Reviews"], "ግምገማዎች")
        self.assertEqual(howto["Emergencies"], "ድንገተኛ ሁኔታዎች")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "የግላዊነት እና የኩኪዎች ፖሊሲ",
        )
        self.assertEqual(agreement["User agreement"], "የተጠቃሚ ስምምነት")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("ወርሃዊ ትኬት", membership)
        self.assertIn("ዓመታዊ ፓስ", membership)
        self.assertIn("Stripe", membership)

    def test_amharic_coverage_frozen_credits_and_global_progress(self):
        authored = POLICY_CATALOGS["am"]
        effective = catalog("am")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "am"), ())
        self.assertEqual(missing_policy_sources(effective, "am"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        self.assertEqual(CREDITS_ROWS["am"], AMHARIC_CREDITS)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], AMHARIC_CREDITS, strict=True)
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(
                effective[source], {"Credits": "ምስጋና"}.get(source, value)
            )
        self.assertEqual(authored["Credits"], "ምስጋናዎች")
        self.assertEqual(effective["Credits"], "ምስጋና")
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        missing_total = sum(gaps.values())
        self.assertEqual(len(POLICY_LOCALES), 38)
        self.assertGreaterEqual(authored_total, 4828)
        self.assertGreaterEqual(effective_total, 4888)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["am"], 0)
        self.assertGreaterEqual(
            sum(not locale_gaps for locale_gaps in gaps.values()), 26
        )

    def test_merged_safety_and_source_bound_policy_safeguards(self):
        howto = mapped("howto", HOWTO_AMHARIC_ROWS)
        privacy = mapped("privacy", PRIVACY_AMHARIC_ROWS)
        agreement = mapped("agreement", AGREEMENT_AMHARIC_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], ETHIOPIC)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "ሦስት አማራጮች ብቻ",
                    "ያስቀመጧቸው መጋጠሚያዎች በመለያዎ ውስጥ ይቆያሉ",
                    "ምንም መጋጠሚያ ወደ ማንኛውም ቦታ አይላክም",
                    "500m እስከ 1km",
                    "ትክክለኛውን ቦታዎን በግል ይጠብቃል",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "ነባሪው ጠፍቷል ነው",
                    "ያስቀመጧቸው መጋጠሚያዎች ለማንም አይታዩም",
                    "ምንም መጋጠሚያ አይተላለፍም",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "አንድ ጊዜ ብቻ",
                    "በግል ያስቀምጣል",
                    "ከጀርባ ክትትል የለም",
                    "ፈቃድዎን ይጠይቃል",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "ያስቀመጡትን ቦታ ፈጽሞ አናሳይም",
                    "500m እስከ 1km",
                    "ማጋራቱን ወዲያውኑ ያቆማል",
                    "ያስቀመጡትን መጋጠሚያዎች ሳይሰርዝ",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "አድራሻም ፈጽሞ አይታተምም",
                    "እርስዎ ካረጋገጡት ረዳት ጋር ብቻ",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112",
                    "999",
                    "911",
                    "000",
                    "አውሮፓ ሕብረት",
                    "የዳታ ግንኙነት በማይፈልግ",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help 16 ዓመትና ከዚያ በላይ",
                    "ቢያንስ 16 ዓመት",
                    "ስለ ሕፃናት መረጃ እያወቅን አንሰበስብም",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("ቢያንስ 16 ዓመት", "Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "ወርሃዊ አባልነት በየወሩ፣ ዓመታዊ አባልነትም በየዓመቱ በራስ-ሰር ይታደሳሉ",
                    "በየዓመቱ በራስ-ሰር ይታደሳሉ",
                    "እስኪሰርዙ ድረስ",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "በክፍያ ፖርታሉ በማንኛውም ጊዜ መሰረዝ ይችላሉ",
                    "የከፈሉበት ጊዜ እስኪያበቃ ድረስ",
                    "የአካባቢ ሕግ በሌላ ሁኔታ ካስገደደ",
                    "የጊዜ ክፍል ክፍያ አይመለስም",
                    "በሕግ የተሰጠ የማቋረጥ ወይም የመሰረዝ መብት",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "ከሁለቱ የበለጠው",
                    "ከጥያቄው በፊት ባሉት 12 ወራት",
                    "50 የአሜሪካ ዶላር",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "ሕጉ ማግለል ወይም መገደብ የማይፈቅደውን ኃላፊነት",
                    "በቸልተኝነት ለሚመጣ ሞት ወይም የአካል ጉዳት",
                    "ለማጭበርበር ወይም ለማታለያ የተሳሳተ መግለጫ",
                    "ለግዴታ የሸማች መብቶች",
                    "የግዴታ የአካባቢ መብቶችዎም አይነኩም",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "ሸማች ከሆኑ",
                    "የግዴታ የሸማች ሕግ",
                    "በአካባቢዎ ፍርድ ቤቶች ክስ የማቅረብ መብትዎ",
                    "የግዴታው ደንብ ይተገበራል",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertNotIn("ከሁለቱ ያነሰው", maximum)
        self.assertGreaterEqual(len(maximum.split()), 30)

    def test_frozen_english_source_and_canonical_source_inventory(self):
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
