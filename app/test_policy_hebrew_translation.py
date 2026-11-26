import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_hebrew as agreement_data
from app import policy_catalog_howto_hebrew as howto_data
from app import policy_catalog_privacy_hebrew as privacy_data
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
from app.policy_catalog_agreement_hebrew import AGREEMENT_HEBREW_ROWS
from app.policy_catalog_howto_hebrew import HOWTO_HEBREW_ROWS
from app.policy_catalog_privacy_hebrew import PRIVACY_HEBREW_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_HEBREW_ROWS", HOWTO_HEBREW_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_HEBREW_ROWS", PRIVACY_HEBREW_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_HEBREW_ROWS",
        AGREEMENT_HEBREW_ROWS,
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
HEBREW = re.compile(r"[\u0590-\u05FF]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
HEBREW_CREDITS = (
    "תודות",
    "המפות הפתוחות ומיזמי הקוד הפתוח שמציירים כל מפה של Go and Help.",
    "עודכן ונכנס לתוקף ב־1 ביוני 2024",
    "Go and Help מצויר על גבי נתונים פתוחים שיצרו מתנדבים מכל רחבי העולם. תודות אלו הן חלק מתנאי הרישיון שאנו מקיימים בשמחה.",
    "מפות ונתוני מפות",
    "אריחי מפה מאת OpenFreeMap, נתונים © תורמי OpenStreetMap, במסגרת Open Database License (ODbL).",
    "נתוני המפות זמינים מאת OpenStreetMap במסגרת Open Database License (ODbL).",
    "OpenFreeMap מבוסס על כמה מיזמי קוד פתוח נפלאים, ובכללם כלים כמו MapLibre, Planetiler ו־OpenMapTiles.",
)
HEBREW_DATE = "עודכן ונכנס לתוקף ב־1 ביוני 2024"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["he"], strict=True))


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


class HebrewPolicyTranslationTests(unittest.TestCase):
    def test_literal_hebrew_rows_are_complete_native_and_full_length(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"he"})
                self.assertIsInstance(rows["he"], tuple)
                self.assertEqual(len(rows["he"]), count)
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
                    "he"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["he"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertNotIn("\ufffd", value)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, HEBREW)
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
                                len(value.split()), len(source.split()) * 0.40
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["he"].count(HEBREW_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_HEBREW_ROWS)
        privacy = mapped("privacy", PRIVACY_HEBREW_ROWS)
        agreement = mapped("agreement", AGREEMENT_HEBREW_ROWS)
        self.assertEqual(howto[credits_date], HEBREW_DATE)
        self.assertEqual(
            howto["How to use Go and Help"], "איך להשתמש ב־Go and Help"
        )
        self.assertEqual(howto["Reviews"], "ביקורות")
        self.assertEqual(howto["Emergencies"], "מצבי חירום")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "מדיניות פרטיות וקובצי עוגיות",
        )
        self.assertEqual(agreement["User agreement"], "הסכם משתמש")
        monthly = lookup(howto, "howto", "There are two options")
        self.assertIn("כרטיס חודשי", monthly)
        self.assertIn("מנוי שנתי", monthly)
        self.assertIn("Stripe", monthly)

    def test_complete_hebrew_coverage_frozen_credits_and_progress_totals(self):
        authored = POLICY_CATALOGS["he"]
        effective = catalog("he")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "he"), ())
        self.assertEqual(missing_policy_sources(effective, "he"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertRegex(effective[source], HEBREW)
        self.assertEqual(CREDITS_ROWS["he"], HEBREW_CREDITS)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], HEBREW_CREDITS, strict=True)
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
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
        self.assertGreaterEqual(authored_total, 4480)
        self.assertGreaterEqual(effective_total, 4550)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["he"], 0)
        self.assertGreaterEqual(
            sum(not locale_gaps for locale_gaps in gaps.values()), 24
        )

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_HEBREW_ROWS)
        privacy = mapped("privacy", PRIVACY_HEBREW_ROWS)
        agreement = mapped("agreement", AGREEMENT_HEBREW_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], HEBREW)
            self.assertNotEqual(howto[source], source)
        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "שלושה מצבים בלבד",
                    "הקואורדינטות השמורות נשארות בחשבון",
                    "שום קואורדינטה אינה נשלחת לשום מקום",
                    "500m עד 1km",
                    "שומר על פרטיות הנקודה המדויקת",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "מצב ברירת המחדל בכל חשבון",
                    "הקואורדינטות השמורות אינן מוצגות לאיש",
                    "אינכם מופיעים במפות או בחיפוש אנשים",
                    "שום קואורדינטה אינה מועברת",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "פעם אחת",
                    "שומר את הנקודה באופן פרטי",
                    "אין מעקב ברקע",
                    "הדפדפן יבקש רשות לפני שיתוף מידע",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "לעולם לא מפרסמים את הנקודה השמורה",
                    "500m עד 1km",
                    "מפסיקה מיד את השיתוף",
                    "בלי למחוק את הקואורדינטות שנשמרו",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "הכתובת שמקלידים לעולם אינה מתפרסמת",
                    "נמסרת רק למי שאישרתם לעזור",
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
                    "האיחוד האירופי",
                    "בלי טלפון טעון או חיבור נתונים",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help מיועד לבני 16 ומעלה",
                    "יש להיות בני 16 לפחות",
                    "איננו אוספים ביודעין מידע על ילדים",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("בני 16 לפחות", "Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "חברות חודשית מתחדשת אוטומטית מדי חודש",
                    "חברות שנתית מתחדשת אוטומטית מדי שנה",
                    "עד לביטול",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "אפשר לבטל בכל עת",
                    "עד סוף התקופה שכבר שילמתם עליה",
                    "למעט במקרים שבהם החוק המקומי מחייב אחרת",
                    "לא ניתן החזר על חלק מתקופה",
                    "זכות חוקית לביטול או לנסיגה",
                    "ממשיכה לחול",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "מוגבלת לגבוה מבין הסכומים הבאים",
                    "במהלך 12 החודשים שקדמו לתביעה",
                    "50 דולר אמריקאי",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "שום דבר בהסכם זה אינו מחריג או מגביל אחריות",
                    "הדין אינו מתיר להחריג או להגביל",
                    "מוות או לפגיעה גופנית שנגרמו מרשלנות",
                    "מצג שווא במרמה",
                    "זכויות צרכניות מחייבות",
                    "זכויותיכם המקומיות המחייבות לא ייפגעו",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "אם אתם צרכנים",
                    "הדין הצרכני המקומי המחייב",
                    "להגיש תביעה בבתי המשפט המקומיים",
                    "הכלל המחייב גובר",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertNotIn("לנמוך מבין הסכומים", maximum)
        self.assertGreaterEqual(len(maximum.split()), 30)

    def test_canonical_english_source_checksum_and_source_inventory_unchanged(
        self,
    ):
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
