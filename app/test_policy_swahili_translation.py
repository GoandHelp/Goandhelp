import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_swahili as agreement_data
from app import policy_catalog_howto_swahili as howto_data
from app import policy_catalog_privacy_swahili as privacy_data
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
from app.policy_catalog_agreement_swahili import AGREEMENT_SWAHILI_ROWS
from app.policy_catalog_howto_swahili import HOWTO_SWAHILI_ROWS
from app.policy_catalog_privacy_swahili import PRIVACY_SWAHILI_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_SWAHILI_ROWS", HOWTO_SWAHILI_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_SWAHILI_ROWS", PRIVACY_SWAHILI_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_SWAHILI_ROWS",
        AGREEMENT_SWAHILI_ROWS,
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
    "Premium",
    "IP",
    "PIN",
)
LATIN_ALLOWED = tuple(sorted(PROPER_NAMES, key=len, reverse=True))
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
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
CREDITS_SWAHILI = (
    "Shukrani",
    "Ramani huria na miradi ya msimbo huria inayochora kila ramani ya Go and Help.",
    "Imesasishwa na kuanza kutumika tarehe 1 Juni 2024",
    "Go and Help imechorwa kwenye data huria iliyotengenezwa na watu wa kujitolea duniani kote. Shukrani hizi ni sehemu ya masharti ya leseni tunayoyafuata kwa furaha.",
    "Ramani na data za ramani",
    "Vigae vya ramani kutoka OpenFreeMap, data © wachangiaji wa OpenStreetMap, chini ya Open Database License (ODbL).",
    "Data za ramani zinatolewa na OpenStreetMap chini ya Open Database License (ODbL).",
    "OpenFreeMap imejengwa juu ya miradi kadhaa bora ya msimbo huria, ikiwa ni pamoja na zana kama MapLibre, Planetiler na OpenMapTiles.",
)
SWAHILI_DATE = "Imesasishwa na kuanza kutumika tarehe 1 Juni 2024"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["sw"], strict=True))


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


class SwahiliPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_and_full_length(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"sw"})
                self.assertIsInstance(rows["sw"], tuple)
                self.assertEqual(len(rows["sw"]), count)
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
                    "sw"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["sw"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertNotIn("\ufffd", value)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, LATIN_WORD)
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
                                len(value), len(source) * 0.60
                            )
                            self.assertGreaterEqual(
                                len(value.split()), len(source.split()) * 0.40
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["sw"].count(SWAHILI_DATE) for *_, row, _ in BATCH), 3
        )
        self.assertEqual(
            mapped("howto", HOWTO_SWAHILI_ROWS)["How to use Go and Help"],
            "Jinsi ya kutumia Go and Help",
        )
        self.assertEqual(
            mapped("howto", HOWTO_SWAHILI_ROWS)["Reviews"], "Maoni"
        )
        self.assertEqual(
            mapped("howto", HOWTO_SWAHILI_ROWS)["Emergencies"], "Dharura"
        )
        self.assertEqual(
            mapped("privacy", PRIVACY_SWAHILI_ROWS)[
                "Privacy and cookies policy"
            ],
            "Sera ya faragha na vidakuzi",
        )
        self.assertEqual(
            mapped("agreement", AGREEMENT_SWAHILI_ROWS)["User agreement"],
            "Makubaliano ya mtumiaji",
        )
        membership = lookup(
            mapped("howto", HOWTO_SWAHILI_ROWS),
            "howto",
            "There are two options",
        )
        self.assertIn("Tiketi ya kila mwezi", membership)
        self.assertIn("Pasi ya kila mwaka", membership)
        self.assertIn("Stripe", membership)

    def test_swahili_sources_coverage_credits_and_progress(self):
        authored = POLICY_CATALOGS["sw"]
        effective = catalog("sw")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "sw"), ())
        self.assertEqual(missing_policy_sources(effective, "sw"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        self.assertEqual(CREDITS_ROWS["sw"], CREDITS_SWAHILI)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], CREDITS_SWAHILI, strict=True)
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
        self.assertEqual(authored["Credits"], "Shukrani")
        self.assertEqual(effective["Credits"], "Shukrani")
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
        self.assertGreaterEqual(authored_total, 4654)
        self.assertGreaterEqual(effective_total, 4719)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["sw"], 0)
        self.assertGreaterEqual(
            sum(not locale_gaps for locale_gaps in gaps.values()), 25
        )

    def test_merged_safety_and_full_source_bound_safeguards(self):
        howto = mapped("howto", HOWTO_SWAHILI_ROWS)
        privacy = mapped("privacy", PRIVACY_SWAHILI_ROWS)
        agreement = mapped("agreement", AGREEMENT_SWAHILI_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertNotEqual(howto[source], source)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "bila nafasi za katikati",
                    "koordinati ulizohifadhi hubaki kwenye akaunti yako",
                    "hakuna koordinati inayotumwa popote",
                    "kati ya 500m na 1km",
                    "sehemu yako halisi kuwa ya faragha",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Hali ya Zima ndiyo chaguo-msingi",
                    "koordinati ulizohifadhi hazionyeshwi kwa mtu yeyote",
                    "hakuna koordinati inayotumwa",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "mara moja",
                    "huhifadhi sehemu hiyo kwa faragha",
                    "Hakuna ufuatiliaji wa chinichini",
                    "kitaomba ruhusa yako",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "Hatuwahi kuchapisha sehemu uliyohifadhi",
                    "kati ya 500m na 1km",
                    "hukomesha kushiriki mara moja",
                    "bila kufuta koordinati ulizohifadhi",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "anwani unayoandika haichapishwi kamwe",
                    "hushirikiwa tu na msaidizi uliyemthibitisha",
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
                    "Umoja wa Ulaya",
                    "haihitaji simu yenye chaji wala muunganisho wa data",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help ni ya watu wenye umri wa miaka 16 na zaidi",
                    "umri wa angalau miaka 16",
                    "Hatukusanyi taarifa za watoto tukijua",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("umri wa angalau miaka 16", "Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "hujisasisha kiotomatiki kila mwezi",
                    "hujisasisha kiotomatiki kila mwaka",
                    "hadi uughairi",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "Unaweza kughairi wakati wowote",
                    "hadi mwisho wa kipindi ambacho tayari umelipia",
                    "Isipokuwa pale sheria ya eneo lako inapohitaji vinginevyo",
                    "fedha za sehemu ya kipindi hazirejeshwi",
                    "Haki yoyote ya kisheria ya kujiondoa au kughairi",
                    "inaendelea kutumika",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "kiasi kilicho kikubwa zaidi kati ya ada za uanachama",
                    "katika miezi 12 kabla ya dai",
                    "dola 50 za Marekani",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "Hakuna jambo katika makubaliano haya linaloondoa au kuweka kikomo",
                    "sheria hairuhusu iondolewe au iwekwe kikomo",
                    "kifo au jeraha la mwili lililosababishwa na uzembe",
                    "ulaghai au upotoshaji wa udanganyifu",
                    "haki za lazima za watumiaji",
                    "haki zako za lazima za eneo lako hazitaathiriwa",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "ikiwa wewe ni mtumiaji",
                    "sheria za lazima za watumiaji",
                    "mahakama za eneo lako",
                    "sharti la lazima ndilo litakalotumika",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertNotIn("kiasi kilicho kidogo zaidi", maximum)
        self.assertGreaterEqual(len(maximum.split()), 30)

    def test_frozen_english_source_and_source_inventory(self):
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
