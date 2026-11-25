import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_hindi as agreement_data
from app import policy_catalog_howto_hindi as howto_data
from app import policy_catalog_privacy_hindi as privacy_data
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
from app.policy_catalog_agreement_hindi import AGREEMENT_HINDI_ROWS
from app.policy_catalog_howto_hindi import HOWTO_HINDI_ROWS
from app.policy_catalog_privacy_hindi import PRIVACY_HINDI_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_HINDI_ROWS", HOWTO_HINDI_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_HINDI_ROWS", PRIVACY_HINDI_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_HINDI_ROWS",
        AGREEMENT_HINDI_ROWS,
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
LATIN_ALLOWED = tuple(
    sorted(PROPER_NAMES + ("OpenMapTiles",), key=len, reverse=True)
)
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
DEVANAGARI = re.compile(r"[\u0900-\u097F]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["hi"], strict=True))


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


class HindiPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_hindi_rows_are_complete_and_native(self):
        total_rows = 0
        all_sources: set[str] = set()
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        localized_date = "1 जून 2024 को अद्यतन और प्रभावी"
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"hi"})
                self.assertIsInstance(rows["hi"], tuple)
                self.assertEqual(len(rows["hi"]), count)
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
                    "hi"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["hi"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, DEVANAGARI)
                        self.assertEqual(latin_residue(value), [])
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
                                len(value.split()), len(source.split()) * 0.50
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["hi"].count(localized_date) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_HINDI_ROWS)
        privacy = mapped("privacy", PRIVACY_HINDI_ROWS)
        agreement = mapped("agreement", AGREEMENT_HINDI_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help का उपयोग कैसे करें"
        )
        self.assertEqual(howto["Reviews"], "समीक्षाएँ")
        self.assertEqual(howto["Emergencies"], "आपात स्थितियाँ")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "गोपनीयता और कुकी नीति"
        )
        self.assertEqual(agreement["User agreement"], "उपयोगकर्ता समझौता")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("मासिक टिकट", membership)
        self.assertIn("वार्षिक पास", membership)
        self.assertIn("Stripe", membership)

    def test_hindi_sources_credits_and_global_coverage(self):
        authored = POLICY_CATALOGS["hi"]
        effective = catalog("hi")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "hi"), ())
        self.assertEqual(missing_policy_sources(effective, "hi"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        frozen_credits = (
            "आभार",
            "खुले मानचित्र और ओपन सोर्स परियोजनाएँ जो हर Go and Help मानचित्र को बनाती हैं।",
            "1 जून 2024 को अद्यतन और प्रभावी",
            "Go and Help दुनिया भर के स्वयंसेवकों द्वारा बनाए गए खुले डेटा पर चित्रित है। यह आभार उन लाइसेंस शर्तों का हिस्सा है जिनका हम खुशी से पालन करते हैं।",
            "मानचित्र और मानचित्र डेटा",
            "मानचित्र टाइलें OpenFreeMap द्वारा, डेटा © OpenStreetMap योगदानकर्ता, Open Database License (ODbL) के अंतर्गत।",
            "OpenStreetMap मानचित्र डेटा को Open Database License (ODbL) के अंतर्गत उपलब्ध कराता है।",
            "OpenFreeMap कई शानदार ओपन सोर्स परियोजनाओं पर आधारित है, जिनमें MapLibre, Planetiler और OpenMapTiles जैसे उपकरण शामिल हैं।",
        )
        self.assertEqual(CREDITS_ROWS["hi"], frozen_credits)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], frozen_credits, strict=True)
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
        self.assertEqual(authored["Credits"], "आभार")
        self.assertEqual(effective["Credits"], "आभार")
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
        self.assertGreaterEqual(authored_total, 3958)
        self.assertGreaterEqual(effective_total, 4043)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["hi"], 0)

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_HINDI_ROWS)
        privacy = mapped("privacy", PRIVACY_HINDI_ROWS)
        agreement = mapped("agreement", AGREEMENT_HINDI_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], DEVANAGARI)
        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "तीन विकल्प",
                    "आपके सहेजे गए निर्देशांक आपके खाते में बने रहते हैं",
                    "कोई भी निर्देशांक कहीं नहीं भेजा जाता",
                    "500m से 1km",
                    "आपके सटीक बिंदु को निजी रखता है",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                ("112", "999", "911", "000", "पूरे यूरोपीय संघ में"),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "हर खाते के लिए",
                    "किसी को नहीं दिखाए जाते",
                    "लोगों की खोज में दिखाई नहीं देते",
                    "कोई भी निर्देशांक प्रेषित नहीं किया जाता",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "केवल एक बार पढ़ता है",
                    "निजी रूप से संग्रहीत करता है",
                    "कोई पृष्ठभूमि ट्रैकिंग नहीं होती",
                    "आपकी अनुमति माँगेगा",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "हम आपका संग्रहीत बिंदु कभी प्रकाशित नहीं करते",
                    "500m से 1km",
                    "साझा करना तुरंत रुक जाता है",
                    "आपके सहेजे गए निर्देशांक मिटाए बिना",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "टाइप किया गया पता कभी प्रकाशित नहीं किया जाता",
                    "उसी मददगार के साथ साझा की जाती है जिसकी आप पुष्टि करते हैं",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help 16 वर्ष और उससे अधिक आयु के लोगों के लिए है",
                    "कम से कम 16 वर्ष",
                    "हम जानबूझकर बच्चों से जानकारी एकत्र नहीं करते",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("कम से कम 16 वर्ष", "Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "मासिक सदस्यता हर महीने अपने-आप नवीनीकृत होती है",
                    "वार्षिक सदस्यता हर साल अपने-आप नवीनीकृत होती है",
                    "जब तक आप रद्द नहीं करते",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "किसी भी समय रद्द कर सकते हैं",
                    "जिसका भुगतान आप पहले ही कर चुके हैं",
                    "अन्यथा अपेक्षित करता है",
                    "अधूरी अवधियों के लिए धनवापसी नहीं की जाती",
                    "अनुबंध से हटने या रद्द करने का",
                    "वैधानिक अधिकार लागू रहता है",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "इन दोनों में से जो अधिक हो",
                    "दावे से पहले के 12 महीनों में",
                    "50 अमेरिकी डॉलर",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "इस समझौते की कोई भी बात",
                    "बाहर या सीमित करने की अनुमति नहीं देता",
                    "लापरवाही से हुई मृत्यु या व्यक्तिगत चोट",
                    "कपटपूर्ण मिथ्या प्रस्तुति",
                    "अनिवार्य उपभोक्ता अधिकार",
                    "आपके अनिवार्य स्थानीय अधिकार अप्रभावित रहते हैं",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "अगर आप उपभोक्ता हैं",
                    "देश के अनिवार्य उपभोक्ता",
                    "अपनी स्थानीय अदालतों में दावा करने का आपका अधिकार",
                    "अनिवार्य नियम ही मान्य होता है",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertGreaterEqual(len(maximum.split()), 30)

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
