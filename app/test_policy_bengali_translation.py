import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_bengali as agreement_data
from app import policy_catalog_howto_bengali as howto_data
from app import policy_catalog_privacy_bengali as privacy_data
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
from app.policy_catalog_agreement_bengali import AGREEMENT_BENGALI_ROWS
from app.policy_catalog_howto_bengali import HOWTO_BENGALI_ROWS
from app.policy_catalog_privacy_bengali import PRIVACY_BENGALI_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_BENGALI_ROWS", HOWTO_BENGALI_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_BENGALI_ROWS", PRIVACY_BENGALI_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_BENGALI_ROWS",
        AGREEMENT_BENGALI_ROWS,
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
    "IP",
    "PIN",
)
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
BENGALI = re.compile(r"[\u0980-\u09ff]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["bn"], strict=True))


def lookup(values: dict[str, str], document: str, prefix: str) -> str:
    matches = [
        values[source]
        for source in DOCUMENT_SOURCE_KEYS[document]
        if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def numbers(text: str) -> set[str]:
    return {number.replace(",", ".") for number in NUMBERS.findall(text)}


class BengaliPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_full_native_bengali_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"bn"})
                self.assertIsInstance(rows["bn"], tuple)
                self.assertEqual(len(rows["bn"]), count)
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
                    "bn"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["bn"])
                for source, value in entries.items():
                    with self.subTest(source=source[:70]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, BENGALI)
                        self.assertNotIn("\ufffd", value)
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(numbers(source) <= numbers(value))
                        if len(source) >= 280:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.35
                            )
                            self.assertGreaterEqual(
                                len(value.split()), len(source.split()) * 0.40
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        date = CREDITS_ROWS["bn"][2]
        self.assertEqual(
            len(all_sources - {POLICY_DOCUMENTS["credits"]["updated"]}), 174
        )
        self.assertEqual(sum(row["bn"].count(date) for *_, row, _ in BATCH), 3)
        howto = mapped("howto", HOWTO_BENGALI_ROWS)
        privacy = mapped("privacy", PRIVACY_BENGALI_ROWS)
        agreement = mapped("agreement", AGREEMENT_BENGALI_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help কীভাবে ব্যবহার করবেন"
        )
        self.assertEqual(howto["Reviews"], "পর্যালোচনা")
        self.assertEqual(howto["Emergencies"], "জরুরি অবস্থা")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "গোপনীয়তা ও কুকি নীতি"
        )
        self.assertEqual(agreement["User agreement"], "ব্যবহারকারী চুক্তি")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("মাসিক টিকিট", membership)
        self.assertIn("বার্ষিক পাস", membership)

    def test_bengali_coverage_credits_and_progress(self):
        authored = POLICY_CATALOGS["bn"]
        effective = catalog("bn")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "bn"), ())
        self.assertEqual(missing_policy_sources(effective, "bn"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:70]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], BENGALI)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        self.assertEqual(CREDITS_ROWS["bn"][0], "কৃতজ্ঞতা স্বীকার")
        for source in credits_sources:
            self.assertEqual(effective[source], authored[source])
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
        self.assertGreaterEqual(authored_total, 5176)
        self.assertGreaterEqual(effective_total, 5226)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["bn"], 0)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 28)

    def test_merged_safety_and_source_bound_policy_safeguards(self):
        howto = mapped("howto", HOWTO_BENGALI_ROWS)
        privacy = mapped("privacy", PRIVACY_BENGALI_ROWS)
        agreement = mapped("agreement", AGREEMENT_BENGALI_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], BENGALI)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "ঠিক 3টি বিকল্প আছে, মাঝামাঝি কিছু নেই",
                    "সংরক্ষিত স্থানাঙ্ক আপনার অ্যাকাউন্টে থাকবে, কিন্তু কোনো স্থানাঙ্ক কোথাও পাঠানো হবে না",
                    "‘আনুমানিক’ আপনার সঠিক অবস্থান গোপন রাখে",
                    "500m থেকে 1km দূরের ভূমি-নিরাপদ একটি বিন্দু",
                    "‘সরাসরি’ আপনার সঠিক অবস্থান সব ব্যবহারকারীর কাছে প্রকাশ করে",
                    "‘আমার অবস্থান হালনাগাদ করুন’ চাপলে তা আবার হালনাগাদ হয়",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "‘বন্ধ’ই পূর্বনির্ধারিত",
                    "আপনার সংরক্ষিত স্থানাঙ্ক কাউকে দেখানো হয় না",
                    "কোনো স্থানাঙ্ক পাঠানো হয় না",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "আপনার সংরক্ষিত বিন্দু আমরা কখনো প্রকাশ করি না",
                    "500m থেকে 1km দূরে ভূমি-নিরাপদ একটি স্থিতিশীল বিন্দু",
                    "আপনার সংরক্ষিত স্থানাঙ্ক না মুছেই সঙ্গে সঙ্গে ভাগ করা থামে",
                ),
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                (
                    "প্রথমে আপনার স্থানীয় জরুরি সেবার সঙ্গে যোগাযোগ করুন",
                    "Go and Help জরুরি পরিষেবা নয় এবং ঘটনাস্থলে হস্তক্ষেপ করতে পারে না",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112 চলে",
                    "999, 911, 000 ও অন্যান্য নম্বর ব্যবহৃত হয়",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "অ্যাকাউন্ট তৈরি করতে আপনার বয়স অন্তত 16 বছর হতে হবে",
                    "আমরা জেনেশুনে শিশুদের তথ্য সংগ্রহ করি না",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("আপনার বয়স অন্তত 16 বছর হতে হবে",),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "মাসিক সদস্যপদ প্রতি মাসে এবং বার্ষিক সদস্যপদ প্রতি বছরে স্বয়ংক্রিয়ভাবে নবায়ন হয়, যতক্ষণ না আপনি বাতিল করেন",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "যেকোনো সময় বাতিল করতে পারেন",
                    "আগে থেকে পরিশোধ করা মেয়াদের শেষ পর্যন্ত চলবে",
                    "স্থানীয় আইন অন্য কিছু না বললে, মেয়াদের অবশিষ্ট অংশের টাকা ফেরত দেওয়া হয় না",
                    "প্রত্যাহার বা বাতিলের যে বিধিবদ্ধ অধিকার আছে, তা বহাল থাকবে",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                (
                    "নিচের দুটির মধ্যে যেটি বেশি",
                    "দাবির আগের 12 মাসে আপনি আমাদের যে সদস্যপদ ফি দিয়েছেন, অথবা 50 মার্কিন ডলার",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "এমন দায় বাদ দেয় বা সীমিত করে না, যা আইন অনুযায়ী বাদ দেওয়া বা সীমিত করা যায় না",
                    "অবহেলার কারণে মৃত্যু বা শারীরিক আঘাত",
                    "প্রতারণা বা প্রতারণামূলক ভুল বিবৃতি",
                    "বাধ্যতামূলক ভোক্তা-অধিকার",
                    "আপনার স্থানীয় বাধ্যতামূলক অধিকার অক্ষুণ্ণ থাকবে",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "আপনি ভোক্তা হলে",
                    "যেখানে সাধারণত বসবাস করেন সেই দেশের বাধ্যতামূলক ভোক্তা-আইনের সুরক্ষা",
                    "স্থানীয় আদালতে দাবি করার অধিকার",
                    "বাধ্যতামূলক নিয়মই প্রাধান্য পাবে",
                ),
            ),
        )
        for values, document, prefix, phrases in clauses:
            value = lookup(values, document, prefix)
            for phrase in phrases:
                with self.subTest(source=prefix, phrase=phrase):
                    self.assertIn(phrase, value)

    def test_frozen_english_sources(self):
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
