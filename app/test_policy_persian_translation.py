import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_persian as agreement_data
from app import policy_catalog_howto_persian as howto_data
from app import policy_catalog_privacy_persian as privacy_data
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
from app.policy_catalog_agreement_persian import AGREEMENT_PERSIAN_ROWS
from app.policy_catalog_howto_persian import HOWTO_PERSIAN_ROWS
from app.policy_catalog_privacy_persian import PRIVACY_PERSIAN_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_PERSIAN_ROWS", HOWTO_PERSIAN_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_PERSIAN_ROWS", PRIVACY_PERSIAN_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_PERSIAN_ROWS",
        AGREEMENT_PERSIAN_ROWS,
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
PERSIAN = re.compile(r"[\u0600-\u06FF]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
PERSIAN_CREDITS = (
    "قدردانی‌ها",
    "نقشه‌های باز و پروژه‌های متن‌بازی که همهٔ نقشه‌های Go and Help را ترسیم می‌کنند.",
    "به‌روزرسانی و لازم‌الاجرا از 1 ژوئن 2024",
    "Go and Help بر پایهٔ داده‌های بازی ترسیم می‌شود که داوطلبان سراسر جهان ساخته‌اند. این قدردانی‌ها بخشی از شرایط مجوزهایی هستند که با خوشحالی رعایت می‌کنیم.",
    "نقشه‌ها و داده‌های نقشه",
    "کاشی‌های نقشه از OpenFreeMap، داده‌ها © مشارکت‌کنندگان OpenStreetMap، تحت Open Database License (ODbL).",
    "داده‌های نقشه توسط OpenStreetMap تحت Open Database License (ODbL) در دسترس قرار می‌گیرند.",
    "OpenFreeMap بر چندین پروژهٔ عالی متن‌باز بنا شده است، از جمله ابزارهایی مانند MapLibre، Planetiler و OpenMapTiles.",
)
PERSIAN_DATE = "به‌روزرسانی و لازم‌الاجرا از 1 ژوئن 2024"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["fa"], strict=True))


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


class PersianPolicyTranslationTests(unittest.TestCase):
    def test_literal_persian_rows_are_complete_native_and_full_length(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"fa"})
                self.assertIsInstance(rows["fa"], tuple)
                self.assertEqual(len(rows["fa"]), count)
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
                    "fa"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["fa"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertNotIn("\ufffd", value)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, PERSIAN)
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
            sum(row["fa"].count(PERSIAN_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_PERSIAN_ROWS)
        privacy = mapped("privacy", PRIVACY_PERSIAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_PERSIAN_ROWS)
        self.assertEqual(howto[credits_date], PERSIAN_DATE)
        self.assertEqual(
            howto["How to use Go and Help"], "روش استفاده از Go and Help"
        )
        self.assertEqual(howto["Reviews"], "دیدگاه‌ها")
        self.assertEqual(howto["Emergencies"], "وضعیت اضطراری")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "سیاست حریم خصوصی و کوکی‌ها"
        )
        self.assertEqual(agreement["User agreement"], "توافق‌نامه کاربر")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("بلیت ماهانه", membership)
        self.assertIn("اشتراک سالانه", membership)
        self.assertIn("Stripe", membership)

    def test_complete_persian_coverage_credits_and_progress_totals(self):
        authored = POLICY_CATALOGS["fa"]
        effective = catalog("fa")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "fa"), ())
        self.assertEqual(missing_policy_sources(effective, "fa"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertRegex(effective[source], PERSIAN)
        self.assertEqual(CREDITS_ROWS["fa"], PERSIAN_CREDITS)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], PERSIAN_CREDITS, strict=True)
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
        self.assertGreaterEqual(authored_total, 4306)
        self.assertGreaterEqual(effective_total, 4381)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["fa"], 0)
        self.assertGreaterEqual(
            sum(not locale_gaps for locale_gaps in gaps.values()), 23
        )

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_PERSIAN_ROWS)
        privacy = mapped("privacy", PRIVACY_PERSIAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_PERSIAN_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], PERSIAN)
            self.assertNotEqual(howto[source], source)
        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "سه حالت دارد",
                    "مختصات ذخیره‌شده‌تان در حساب شما می‌ماند",
                    "هیچ مختصاتی به جایی ارسال نمی‌شود",
                    "500m تا 1km",
                    "نقطهٔ دقیق شما را خصوصی نگه می‌دارد",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "حالت پیش‌فرض همهٔ حساب‌هاست",
                    "مختصات ذخیره‌شدهٔ شما به هیچ‌کس نشان داده نمی‌شود",
                    "در نقشه‌ها یا جست‌وجوی افراد ظاهر نمی‌شوید",
                    "هیچ مختصاتی ارسال نمی‌شود",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "فقط یک‌بار",
                    "به‌صورت خصوصی ذخیره می‌کند",
                    "ردیابی پس‌زمینه‌ای وجود ندارد",
                    "مرورگر پیش از اشتراک‌گذاری هر چیزی اجازهٔ شما را می‌پرسد",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "هرگز نقطهٔ ذخیره‌شدهٔ شما را منتشر نمی‌کنیم",
                    "500m تا 1km",
                    "بی‌درنگ متوقف می‌شود",
                    "مختصاتی را که ذخیره کرده‌اید حذف کند",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "نشانی‌ای که وارد می‌کنید هرگز منتشر نمی‌شود",
                    "فقط با کمک‌کننده‌ای به اشتراک گذاشته می‌شود که تأییدش می‌کنید",
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
                    "اتحادیهٔ اروپا",
                    "تلفن شارژشده یا اتصال داده",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help برای افراد 16 ساله و بالاتر است",
                    "باید دست‌کم 16 سال داشته باشید",
                    "اطلاعات کودکان را گردآوری نمی‌کنیم",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("دست‌کم 16 سال داشته باشید", "Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "عضویت ماهانه هر ماه",
                    "عضویت سالانه هر سال",
                    "به‌طور خودکار تمدید می‌شود",
                    "مگر آنکه آن را لغو کنید",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "هر زمان می‌توانید",
                    "تا پایان دوره‌ای که هزینه‌اش را قبلاً پرداخته‌اید",
                    "جز در مواردی که قانون محلی خلاف آن را مقرر کند",
                    "هزینهٔ بخش باقی‌ماندهٔ دوره بازپرداخت نمی‌شود",
                    "حق قانونی انصراف یا لغویی",
                    "همچنان برقرار است",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "به بیشترینِ این دو مقدار",
                    "دوازده ماه پیش از ادعا",
                    "50 دلار آمریکا",
                    "هرکدام بیشتر باشد",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "هیچ‌چیز در این توافق‌نامه مسئولیتی را",
                    "اجازهٔ حذف یا محدودکردنش را نمی‌دهد",
                    "مرگ یا آسیب جسمی ناشی از سهل‌انگاری",
                    "اظهار خلاف واقعِ متقلبانه",
                    "حقوق اجباری مصرف‌کننده",
                    "حقوق اجباری محلی شما دست‌نخورده است",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "اگر مصرف‌کننده باشید",
                    "حمایت قانون اجباری مصرف‌کننده",
                    "حق طرح دعوا در دادگاه‌های محلی‌تان",
                    "قاعدهٔ اجباری حاکم است",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertNotIn("هرکدام کمتر باشد", maximum)
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
