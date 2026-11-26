import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_arabic as agreement_data
from app import policy_catalog_howto_arabic as howto_data
from app import policy_catalog_privacy_arabic as privacy_data
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
from app.policy_catalog_agreement_arabic import AGREEMENT_ARABIC_ROWS
from app.policy_catalog_howto_arabic import HOWTO_ARABIC_ROWS
from app.policy_catalog_privacy_arabic import PRIVACY_ARABIC_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_ARABIC_ROWS", HOWTO_ARABIC_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_ARABIC_ROWS", PRIVACY_ARABIC_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_ARABIC_ROWS",
        AGREEMENT_ARABIC_ROWS,
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
ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
CREDITS_DATE = "تم التحديث وأصبح ساريًا في 1 يونيو 2024"
FROZEN_CREDITS = (
    "الشكر والتقدير",
    "الخرائط المفتوحة والمشاريع مفتوحة المصدر التي ترسم كل خريطة في Go and Help.",
    "تم التحديث وأصبح ساريًا في 1 يونيو 2024",
    "تُرسم Go and Help على بيانات مفتوحة أنشأها متطوعون من جميع أنحاء العالم. هذه الإشادات جزء من شروط الترخيص التي نلتزم بها بكل سرور.",
    "الخرائط وبيانات الخرائط",
    "بلاطات الخرائط من OpenFreeMap، والبيانات © مساهمو OpenStreetMap، بموجب Open Database License (ODbL).",
    "يتيح OpenStreetMap بيانات الخرائط بموجب Open Database License (ODbL).",
    "يستند OpenFreeMap إلى عدة مشاريع رائعة مفتوحة المصدر، بما فيها أدوات مثل MapLibre وPlanetiler وOpenMapTiles.",
)


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["ar"], strict=True))


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


class ArabicPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_arabic_rows_are_complete_and_native(self):
        total_rows = 0
        all_sources: set[str] = set()
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"ar"})
                self.assertIsInstance(rows["ar"], tuple)
                self.assertEqual(len(rows["ar"]), count)
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
                    "ar"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["ar"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertNotIn("\ufffd", value)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, ARABIC)
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
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["ar"].count(CREDITS_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_ARABIC_ROWS)
        privacy = mapped("privacy", PRIVACY_ARABIC_ROWS)
        agreement = mapped("agreement", AGREEMENT_ARABIC_ROWS)
        self.assertEqual(howto[credits_date], CREDITS_DATE)
        self.assertEqual(
            howto["How to use Go and Help"], "كيفية استخدام Go and Help"
        )
        self.assertEqual(howto["Reviews"], "التقييمات")
        self.assertEqual(howto["Emergencies"], "الطوارئ")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "سياسة الخصوصية وملفات تعريف الارتباط",
        )
        self.assertEqual(agreement["User agreement"], "اتفاقية المستخدم")
        membership = lookup(howto, "howto", "There are two options")
        for token in ("«تذكرة شهرية»", "«اشتراك سنوي»", "Stripe"):
            self.assertIn(token, membership)

    def test_arabic_sources_credits_and_global_coverage(self):
        authored = POLICY_CATALOGS["ar"]
        effective = catalog("ar")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "ar"), ())
        self.assertEqual(missing_policy_sources(effective, "ar"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertRegex(effective[source], ARABIC)
        self.assertEqual(CREDITS_ROWS["ar"], FROZEN_CREDITS)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], FROZEN_CREDITS, strict=True)
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
        differing = {
            source: effective[source]
            for source in SOURCE_KEYS
            if effective[source] != authored[source]
        }
        self.assertEqual(differing, {"Credits": "شكر وتقدير"})
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
        self.assertGreaterEqual(authored_total, 4132)
        self.assertGreaterEqual(effective_total, 4212)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["ar"], 0)

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_ARABIC_ROWS)
        privacy = mapped("privacy", PRIVACY_ARABIC_ROWS)
        agreement = mapped("agreement", AGREEMENT_ARABIC_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], ARABIC)
            self.assertNotEqual(howto[source], source)
        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "ثلاثة أوضاع",
                    "تبقى إحداثياتك المحفوظة في حسابك",
                    "لا يتم إرسال أي إحداثيات إلى أي مكان",
                    "بين 500m و1km",
                    "على خصوصية نقطتك الدقيقة",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                ("112", "999", "911", "000", "في جميع أنحاء الاتحاد الأوروبي"),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "الإعداد الافتراضي لكل حساب",
                    "لا يتم عرض إحداثياتك المحفوظة لأي شخص",
                    "ولا تظهر على الخرائط أو في البحث عن الأشخاص",
                    "ولا يتم نقل أي إحداثيات",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "مرة واحدة فقط",
                    "ويخزن تلك النقطة بشكل خاص",
                    "لا يوجد تتبع في الخلفية",
                    "سيطلب متصفحك إذنك",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "نحن لا ننشر أبدًا نقطتك المخزنة",
                    "بين 500m و1km",
                    "يوقف المشاركة فورًا",
                    "دون حذف الإحداثيات التي حفظتها",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "ولا يتم نشر العنوان الذي تكتبه أبدًا",
                    "إلا مع المساعد الذي تؤكده",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help مخصصة للأشخاص الذين تبلغ أعمارهم 16 عامًا فأكثر",
                    "يجب ألا يقل عمرك عن 16 عامًا",
                    "نحن لا نجمع عن علم معلومات من الأطفال",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("يجب ألا يقل عمرك عن 16 عامًا", "Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "تتجدد العضوية الشهرية تلقائيًا كل شهر",
                    "وتتجدد العضوية السنوية تلقائيًا كل سنة",
                    "إلى أن تلغيها",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "يمكنك الإلغاء في أي وقت",
                    "حتى نهاية الفترة التي دفعت ثمنها بالفعل",
                    "باستثناء ما يقتضيه القانون المحلي خلاف ذلك",
                    "لا يتم رد المبالغ عن الفترات الجزئية",
                    "حق قانوني في الانسحاب أو الإلغاء",
                    "ساريًا",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "المبلغ الأكبر",
                    "خلال الأشهر الـ 12 السابقة للمطالبة",
                    "50 دولارًا أمريكيًا",
                    "أيهما أكبر",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "لا شيء في هذه الاتفاقية",
                    "التي لا يسمح القانون باستبعادها أو تحديدها",
                    "الوفاة أو الإصابة الشخصية الناجمة عن الإهمال",
                    "التضليل الاحتيالي",
                    "الحقوق الإلزامية للمستهلك",
                    "ولا تتأثر حقوقك المحلية الإلزامية",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "إذا كنت مستهلكًا",
                    "قانون المستهلك الإلزامي في البلد الذي تقيم فيه عادة",
                    "حقك في رفع دعوى أمام محاكمك المحلية",
                    "فإن القاعدة الإلزامية هي التي تسري",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertNotIn("أيهما أقل", maximum)
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
