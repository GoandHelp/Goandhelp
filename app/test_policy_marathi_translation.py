import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_marathi as agreement_data
from app import policy_catalog_howto_marathi as howto_data
from app import policy_catalog_privacy_marathi as privacy_data
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
from app.policy_catalog_agreement_marathi import AGREEMENT_MARATHI_ROWS
from app.policy_catalog_howto_marathi import HOWTO_MARATHI_ROWS
from app.policy_catalog_privacy_marathi import PRIVACY_MARATHI_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_MARATHI_ROWS", HOWTO_MARATHI_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_MARATHI_ROWS", PRIVACY_MARATHI_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_MARATHI_ROWS",
        AGREEMENT_MARATHI_ROWS,
        51,
    ),
)
MARATHI = re.compile(r"[\u0900-\u097f]")
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
PROPER_NAMES = (
    "Open Database License",
    "Go and Help",
    "OpenStreetMap",
    "OpenFreeMap",
    "OpenMapTiles",
    "Planetiler",
    "MapLibre",
    "Stripe",
    "Resend",
    "SHA-256",
    "https://",
    "ODbL",
    "USD",
    "©",
    "IP",
    "PIN",
)
MARATHI_DATE = "1 जून 2024 रोजी अद्ययावत आणि लागू"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["mr"], strict=True))


def lookup(values: dict[str, str], document: str, prefix: str) -> str:
    matches = [
        values[source]
        for source in DOCUMENT_SOURCE_KEYS[document]
        if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def number_set(text: str) -> set[str]:
    return {number.replace(",", ".") for number in NUMBERS.findall(text)}


def latin_residue(text: str) -> list[str]:
    for name in sorted(PROPER_NAMES, key=len, reverse=True):
        text = text.replace(name, " ")
    return re.findall(r"[A-Za-z]{3,}", text)


class MarathiPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_marathi_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"mr"})
                self.assertIsInstance(rows["mr"], tuple)
                self.assertEqual(len(rows["mr"]), count)
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
                    "mr"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["mr"])
                for source, value in entries.items():
                    with self.subTest(source=source[:65]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, MARATHI)
                        self.assertNotIn("\ufffd", value)
                        self.assertFalse(latin_residue(value), value)
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(number_set(source) <= number_set(value))
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
            sum(row["mr"].count(MARATHI_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_MARATHI_ROWS)
        privacy = mapped("privacy", PRIVACY_MARATHI_ROWS)
        agreement = mapped("agreement", AGREEMENT_MARATHI_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help कसे वापरावे"
        )
        self.assertEqual(howto["Reviews"], "पुनरावलोकने")
        self.assertEqual(howto["Emergencies"], "आणीबाणी")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "गोपनीयता आणि कुकी धोरण"
        )
        self.assertEqual(agreement["User agreement"], "वापरकर्ता करार")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn(
            "मासिक तिकीट आणि वार्षिक पास असे दोन पर्याय आहेत; दोन्हींतून अगदी तेच लाभ मिळतात.",
            membership,
        )

    def test_complete_coverage_frozen_credits_and_progress(self):
        authored = POLICY_CATALOGS["mr"]
        effective = catalog("mr")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "mr"), ())
        self.assertEqual(missing_policy_sources(effective, "mr"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["mr"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
        self.assertEqual(credits["Credits"], "आभार")
        self.assertEqual(authored["Credits"], "आभार")
        self.assertEqual(effective["Credits"], "आभार")
        credits_hash = hashlib.sha256(
            json.dumps(
                CREDITS_ROWS,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        self.assertEqual(
            credits_hash,
            "dc6b8e680d18008a7b182612049ac85590879fb6c160bf1ff3a47a348ccee897",
        )
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
        self.assertGreaterEqual(authored_total, 6_220)
        self.assertGreaterEqual(effective_total, 6_240)
        self.assertEqual(effective_total + missing_total, 6_916)
        self.assertLessEqual(missing_total, 676)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 34)
        self.assertEqual(len(credits_sources), 8)

    def test_merged_safety_and_source_bound_privacy_and_legal_clauses(self):
        howto = mapped("howto", HOWTO_MARATHI_ROWS)
        privacy = mapped("privacy", PRIVACY_MARATHI_ROWS)
        agreement = mapped("agreement", AGREEMENT_MARATHI_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], MARATHI)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                "बंद निवडल्यास तुम्ही सर्व नकाशांवरून आणि लोकांच्या शोधातून हटता: जतन केलेले निर्देशांक तुमच्या खात्यात राहतात, पण एकही निर्देशांक कुठेही पाठवला जात नाही.",
            ),
            (
                howto,
                "howto",
                "Set my location offers three positions",
                "अंदाजे निवडल्यास तुमचे अचूक स्थान खाजगी राहते आणि त्यापासून 500m ते 1km अंतरावरील जमिनीवर सुरक्षित असा बिंदूच सर्व वापरकर्त्यांना दाखवला जातो.",
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                "माझे स्थान ठरवा येथे बंद निवडल्यास तुमचे जतन केलेले निर्देशांक कोणालाही दाखवले जात नाहीत, तुम्ही नकाशावर किंवा लोकांच्या शोधात दिसत नाही आणि एकही निर्देशांक पाठवला जात नाही.",
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                "त्यापासून 500m ते 1km अंतरावरचा स्थिर, जमिनीवरील सुरक्षित बिंदू काढून फक्त तोच प्रसिद्ध करतो.",
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                "प्रत्यक्ष ठिकाणापासून 0.5–1 km अंतरावरील अंदाजे परिसर म्हणून दाखवल्या जातात",
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                "आणीबाणीच्या वेळी आधी तुमच्या परिसरातील आपत्कालीन सेवांशी संपर्क साधा. Go and Help ही आपत्कालीन सेवा नाही",
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                "Go and Help ही आपत्कालीन सेवा नाही आणि घटनास्थळी हस्तक्षेप करू शकत नाही.",
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                "112 चालतो; इतरत्र 999, 911, 000 आणि वेगवेगळे क्रमांक वापरले जातात.",
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                "Go and Help हे 16 वर्षे आणि त्याहून अधिक वयाच्या लोकांसाठी आहे",
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                "तुमचे वय किमान 16 वर्षे असले पाहिजे",
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                "मासिक सदस्यत्व दर महिन्याला आणि वार्षिक सदस्यत्व दरवर्षी आपोआप नूतनीकरण होते; तुम्ही रद्द करेपर्यंत ते सुरू राहते.",
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                "आधीच पैसे दिलेल्या कालावधीच्या अखेरपर्यंत तुमचे लाभ सुरू राहतात.",
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                "स्थानिक कायद्याने वेगळे सांगितले नसेल तर कालावधीच्या उरलेल्या भागाचे पैसे परत मिळत नाहीत.",
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                "तुमच्याप्रती आमची एकूण जबाबदारी दाव्यापूर्वीच्या मागील 12 महिन्यांत तुम्ही भरलेल्या सदस्यत्व शुल्काची रक्कम किंवा 50 USD—या दोन्हींपैकी जी अधिक असेल, तितकीच मर्यादित राहील.",
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                "कायद्याने वगळण्यास किंवा मर्यादित करण्यास मनाई असलेली कोणतीही जबाबदारी हा करार वगळत किंवा मर्यादित करत नाही",
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                "बंधकारक ग्राहक हक्क यांसाठीची जबाबदारी समाविष्ट आहे.",
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                "तुम्ही ग्राहक असल्यास, तुम्ही नेहमीच्या वास्तव्यास असलेल्या देशाच्या बंधनकारक ग्राहक-कायद्याने मिळणारे संरक्षण किंवा स्थानिक न्यायालयात दावा करण्याचा हक्क यांपैकी काहीही येथे काढून घेतले जात नाही.",
            ),
        )
        for values, document, prefix, phrase in clauses:
            with self.subTest(source=prefix, phrase=phrase):
                self.assertIn(phrase, lookup(values, document, prefix))
        membership = lookup(
            howto, "howto", "There are two options — a monthly Ticket"
        )
        self.assertIn(
            "मासिक तिकीट आणि वार्षिक पास असे दोन पर्याय आहेत; दोन्हींतून अगदी तेच लाभ मिळतात.",
            membership,
        )

    def test_frozen_english_sources_and_existing_marathi_credits(self):
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
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["mr"], strict=True
            )
        )
        self.assertEqual(
            credits[POLICY_DOCUMENTS["credits"]["updated"]], MARATHI_DATE
        )
        self.assertEqual(credits["Credits"], "आभार")
        self.assertEqual(POLICY_CATALOGS["mr"]["Credits"], "आभार")
        self.assertEqual(catalog("mr")["Credits"], "आभार")
        for document in ("howto", "privacy", "agreement"):
            self.assertIn(
                MARATHI_DATE,
                mapped(
                    document,
                    {
                        "mr": tuple(
                            POLICY_CATALOGS["mr"][source]
                            for source in DOCUMENT_SOURCE_KEYS[document]
                        )
                    },
                ).values(),
            )


if __name__ == "__main__":
    unittest.main()
