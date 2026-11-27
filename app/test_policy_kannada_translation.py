import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_kannada as agreement_data
from app import policy_catalog_howto_kannada as howto_data
from app import policy_catalog_privacy_kannada as privacy_data
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
from app.policy_catalog_agreement_kannada import AGREEMENT_KANNADA_ROWS
from app.policy_catalog_howto_kannada import HOWTO_KANNADA_ROWS
from app.policy_catalog_privacy_kannada import PRIVACY_KANNADA_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_KANNADA_ROWS", HOWTO_KANNADA_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_KANNADA_ROWS", PRIVACY_KANNADA_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_KANNADA_ROWS",
        AGREEMENT_KANNADA_ROWS,
        51,
    ),
)
KANNADA = re.compile(r"[\u0c80-\u0cff]")
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
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
KANNADA_DATE = "1 ಜೂನ್ 2024ರಂದು ನವೀಕರಿಸಲಾಗಿದೆ ಮತ್ತು ಜಾರಿಗೆ ಬಂದಿದೆ"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["kn"], strict=True))


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


class KannadaPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_full_native_kannada_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"kn"})
                self.assertIsInstance(rows["kn"], tuple)
                self.assertEqual(len(rows["kn"]), count)
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
                    "kn"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["kn"])
                for source, value in entries.items():
                    with self.subTest(source=source[:65]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, KANNADA)
                        self.assertNotIn("\ufffd", value)
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
            sum(row["kn"].count(KANNADA_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_KANNADA_ROWS)
        privacy = mapped("privacy", PRIVACY_KANNADA_ROWS)
        agreement = mapped("agreement", AGREEMENT_KANNADA_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help ಬಳಸುವ ವಿಧಾನ"
        )
        self.assertEqual(howto["Reviews"], "ವಿಮರ್ಶೆಗಳು")
        self.assertEqual(howto["Emergencies"], "ತುರ್ತು ಪರಿಸ್ಥಿತಿಗಳು")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "ಗೌಪ್ಯತೆ ಮತ್ತು ಕುಕೀ ನೀತಿ"
        )
        self.assertEqual(agreement["User agreement"], "ಬಳಕೆದಾರರ ಒಪ್ಪಂದ")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("ಮಾಸಿಕ ಟಿಕೆಟ್", membership)
        self.assertIn("ವಾರ್ಷಿಕ ಪಾಸ್", membership)

    def test_complete_coverage_unchanged_credits_and_progress(self):
        authored = POLICY_CATALOGS["kn"]
        effective = catalog("kn")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "kn"), ())
        self.assertEqual(missing_policy_sources(effective, "kn"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:65]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], KANNADA)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["kn"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
        self.assertEqual(credits["Credits"], "ಕೃತಜ್ಞತೆಗಳು")
        self.assertEqual(authored["Credits"], "ಕೃತಜ್ಞತೆಗಳು")
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
        self.assertGreaterEqual(authored_total, 5698)
        self.assertGreaterEqual(effective_total, 5733)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["kn"], 0)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 31)

    def test_complete_merged_safety_and_source_bound_safeguards(self):
        howto = mapped("howto", HOWTO_KANNADA_ROWS)
        privacy = mapped("privacy", PRIVACY_KANNADA_ROWS)
        agreement = mapped("agreement", AGREEMENT_KANNADA_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], KANNADA)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "Set my location ನಲ್ಲಿ ಮೂರು ಆಯ್ಕೆಗಳಿವೆ; ಅವುಗಳ ನಡುವೆ ಬೇರೆ ಆಯ್ಕೆ ಇಲ್ಲ",
                    "ಉಳಿಸಿದ ನಿರ್ದೇಶಾಂಕಗಳು ನಿಮ್ಮ ಖಾತೆಯಲ್ಲಿ ಖಾಸಗಿಯಾಗಿ ಉಳಿಯುತ್ತವೆ, ಆದರೆ ಯಾವುದೇ ನಿರ್ದೇಶಾಂಕವನ್ನು ಎಲ್ಲಿಗೂ ಕಳುಹಿಸುವುದಿಲ್ಲ",
                    "Approximate ನಿಮ್ಮ ನಿಖರ ಸ್ಥಳವನ್ನು ಖಾಸಗಿಯಾಗಿರಿಸಿ",
                    "500m ಮತ್ತು 1km ನಡುವಿನ ದೂರದಲ್ಲಿರುವ ನೆಲಸುರಕ್ಷಿತ ಬಿಂದುವನ್ನು ಮಾತ್ರ ಎಲ್ಲ ಬಳಕೆದಾರರಿಗೆ ಪ್ರಕಟಿಸುತ್ತದೆ",
                    "Live ನಿಮ್ಮ ನಿಖರ ಸ್ಥಳವನ್ನು ಎಲ್ಲ ಬಳಕೆದಾರರಿಗೆ ಪ್ರಕಟಿಸುತ್ತದೆ; Refresh my position ಒತ್ತಿದಾಗ ಮಾತ್ರ ಅದನ್ನು ನವೀಕರಿಸಲಾಗುತ್ತದೆ",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Off ಪ್ರತಿಯೊಂದು ಖಾತೆಯಲ್ಲೂ ಪೂರ್ವನಿಯೋಜಿತ ಆಯ್ಕೆಯಾಗಿದೆ",
                    "ನಿಮ್ಮ ಉಳಿಸಿದ ನಿರ್ದೇಶಾಂಕಗಳು ಯಾರಿಗೂ ಕಾಣಿಸುವುದಿಲ್ಲ",
                    "ಯಾವುದೇ ನಿರ್ದೇಶಾಂಕವನ್ನು ರವಾನಿಸುವುದಿಲ್ಲ",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "ನಿಮ್ಮ ಉಳಿಸಿದ ಬಿಂದುವನ್ನು ನಾವು ಎಂದಿಗೂ ಪ್ರಕಟಿಸುವುದಿಲ್ಲ",
                    "ಅದರಿಂದ 500m ಮತ್ತು 1km ನಡುವಿನ ದೂರದಲ್ಲಿರುವ ನೆಲಸುರಕ್ಷಿತ ಬಿಂದುವನ್ನು ಲೆಕ್ಕಿಸಿ ಅದನ್ನಷ್ಟೇ ಪ್ರಕಟಿಸುತ್ತೇವೆ",
                    "ಉಳಿಸಿದ ನಿರ್ದೇಶಾಂಕಗಳನ್ನು ಅಳಿಸದೆ ಹಂಚಿಕೆ ತಕ್ಷಣ ನಿಲ್ಲುತ್ತದೆ",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km ದೂರದ ಅಂದಾಜು ಪ್ರದೇಶವಾಗಿ ತೋರಿಸಲಾಗುತ್ತದೆ",
                    "ನೀವು ನಮೂದಿಸಿದ ವಿಳಾಸ ಎಂದಿಗೂ ಪ್ರಕಟವಾಗುವುದಿಲ್ಲ",
                    "ನೀವು ದೃಢಪಡಿಸಿದ ಸಹಾಯಕರೊಂದಿಗೆ ಮಾತ್ರ ನಿಖರ ಭೇಟಿ ಸ್ಥಳವನ್ನು ಹಂಚಲಾಗುತ್ತದೆ",
                ),
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                (
                    "ತುರ್ತು ಪರಿಸ್ಥಿತಿಯಲ್ಲಿ ಮೊದಲು ನಿಮ್ಮ ಸ್ಥಳೀಯ ತುರ್ತು ಸೇವೆಗಳನ್ನು ಸಂಪರ್ಕಿಸಿ",
                    "Go and Help ತುರ್ತು ಸೇವೆಯಲ್ಲ ಮತ್ತು ಸ್ಥಳದಲ್ಲೇ ಮಧ್ಯಪ್ರವೇಶಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112 ಯುರೋಪಿಯನ್ ಒಕ್ಕೂಟದಾದ್ಯಂತ ಮತ್ತು ಇತರ ಹಲವು ದೇಶಗಳಲ್ಲಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ",
                    "999, 911, 000 ಮತ್ತು ಇತರ ಸಂಖ್ಯೆಗಳು ಬೇರೆಡೆ ಬಳಸಲಾಗುತ್ತವೆ",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help 16 ವರ್ಷ ಮತ್ತು ಅದಕ್ಕಿಂತ ಮೇಲ್ಪಟ್ಟವರಿಗೆ",
                    "ಖಾತೆ ತೆರೆಯಲು ನಿಮಗೆ ಕನಿಷ್ಠ 16 ವರ್ಷ ವಯಸ್ಸಾಗಿರಬೇಕು",
                    "ಮಕ್ಕಳ ಮಾಹಿತಿಯನ್ನು ನಾವು ತಿಳಿದೂ ಸಂಗ್ರಹಿಸುವುದಿಲ್ಲ",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("ನಿಮಗೆ ಕನಿಷ್ಠ 16 ವರ್ಷ ವಯಸ್ಸಾಗಿರಬೇಕು",),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "ಮಾಸಿಕ ಸದಸ್ಯತ್ವವು ಪ್ರತಿ ತಿಂಗಳು ಮತ್ತು ವಾರ್ಷಿಕ ಸದಸ್ಯತ್ವವು ಪ್ರತಿ ವರ್ಷ—ನೀವು ರದ್ದುಮಾಡುವವರೆಗೆ—ಸ್ವಯಂಚಾಲಿತವಾಗಿ ನವೀಕರಿಸುತ್ತದೆ",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "ಬಿಲ್ಲಿಂಗ್ ಪೋರ್ಟಲ್‌ನಿಂದ ಯಾವಾಗ ಬೇಕಾದರೂ ರದ್ದುಮಾಡಬಹುದು",
                    "ನೀವು ಈಗಾಗಲೇ ಪಾವತಿಸಿದ ಅವಧಿ ಮುಗಿಯುವವರೆಗೆ ಪ್ರಯೋಜನಗಳು ಮುಂದುವರಿಯುತ್ತವೆ",
                    "ಸ್ಥಳೀಯ ಕಾನೂನು ಬೇರೆ ವಿಧಿಸಿದರೆ ಹೊರತು, ಅವಧಿಯ ಉಳಿದ ಭಾಗಕ್ಕೆ ಮರುಪಾವತಿ ಇರುವುದಿಲ್ಲ",
                    "ಕಾನೂನಿನಡಿ ಹೊಂದಿರುವ ಹಿಂಪಡೆಯುವಿಕೆ ಅಥವಾ ರದ್ದತಿಯ ಹಕ್ಕುಗಳು ಎಂದಿನಂತೆ ಅನ್ವಯಿಸುತ್ತವೆ",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                (
                    "ನಿಮಗೆ ನಮ್ಮ ಒಟ್ಟು ಹೊಣೆಗಾರಿಕೆ ಎಂದರೆ ಹಕ್ಕು ಮಂಡಿಸುವುದಕ್ಕೂ ಮುಂಚಿನ 12 ತಿಂಗಳಲ್ಲಿ ನೀವು ಪಾವತಿಸಿದ ಸದಸ್ಯತ್ವ ಶುಲ್ಕಗಳು ಅಥವಾ 50 ಅಮೆರಿಕನ್ ಡಾಲರ್—ಇವೆರಡರಲ್ಲಿ ಯಾವುದು ಹೆಚ್ಚೋ ಅದಕ್ಕೆ ಮಿತಿಯಾಗಿರುತ್ತದೆ",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "ಕಾನೂನು ಹೊರತುಪಡಿಸಲು ಅಥವಾ ಮಿತಿಗೊಳಿಸಲು ಅನುಮತಿಸದ ಹೊಣೆಗಾರಿಕೆಯನ್ನು ಈ ಒಪ್ಪಂದದ ಯಾವುದೂ ಹೊರತುಪಡಿಸುವುದಿಲ್ಲ ಅಥವಾ ಮಿತಿಗೊಳಿಸುವುದಿಲ್ಲ",
                    "ನಿರ್ಲಕ್ಷ್ಯದಿಂದ ಉಂಟಾದ ಮರಣ ಅಥವಾ ದೈಹಿಕ ಗಾಯದ ಹೊಣೆಗಾರಿಕೆ",
                    "ವಂಚನೆ ಅಥವಾ ಮೋಸದ ತಪ್ಪು ನಿರೂಪಣೆ",
                    "ಕಡ್ಡಾಯ ಗ್ರಾಹಕ ಹಕ್ಕುಗಳು ಇದರಲ್ಲಿ ಸೇರಿವೆ",
                    "ನಿಮ್ಮ ಕಡ್ಡಾಯ ಸ್ಥಳೀಯ ಹಕ್ಕುಗಳಿಗೆ ಧಕ್ಕೆಯಾಗುವುದಿಲ್ಲ",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "ನೀವು ಗ್ರಾಹಕರಾಗಿದ್ದರೆ",
                    "ನೀವು ಸಾಮಾನ್ಯವಾಗಿ ವಾಸಿಸುವ ದೇಶದ ಕಡ್ಡಾಯ ಗ್ರಾಹಕ ಕಾನೂನಿನ ರಕ್ಷಣೆ",
                    "ನಿಮ್ಮ ಸ್ಥಳೀಯ ನ್ಯಾಯಾಲಯಗಳಲ್ಲಿ ದಾವೆ ಹೂಡುವ ಹಕ್ಕನ್ನು",
                    "ಕಡ್ಡಾಯ ನಿಯಮವೇ ಮೇಲುಗೈ ಸಾಧಿಸುತ್ತದೆ",
                ),
            ),
        )
        for values, document, prefix, phrases in clauses:
            value = lookup(values, document, prefix)
            for phrase in phrases:
                with self.subTest(source=prefix, phrase=phrase):
                    self.assertIn(phrase, value)

    def test_frozen_english_sources_and_unique_emergency_notice(self):
        howto = mapped("howto", HOWTO_KANNADA_ROWS)
        emergency = lookup(
            howto,
            "howto",
            "In an emergency, contact your local emergency services first. "
            "Go and Help is not an emergency service",
        )
        self.assertIn("ಮೊದಲು ನಿಮ್ಮ ಸ್ಥಳೀಯ ತುರ್ತು ಸೇವೆಗಳನ್ನು ಸಂಪರ್ಕಿಸಿ", emergency)
        self.assertIn(
            "Go and Help ತುರ್ತು ಸೇವೆಯಲ್ಲ ಮತ್ತು ಸ್ಥಳದಲ್ಲೇ ಮಧ್ಯಪ್ರವೇಶಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ",
            emergency,
        )
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
