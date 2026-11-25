import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_thai as agreement_data
from app import policy_catalog_howto_thai as howto_data
from app import policy_catalog_privacy_thai as privacy_data
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
from app.policy_catalog_agreement_thai import AGREEMENT_THAI_ROWS
from app.policy_catalog_howto_thai import HOWTO_THAI_ROWS
from app.policy_catalog_privacy_thai import PRIVACY_THAI_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_THAI_ROWS", HOWTO_THAI_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_THAI_ROWS", PRIVACY_THAI_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_THAI_ROWS",
        AGREEMENT_THAI_ROWS,
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
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["th"], strict=True))


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


class ThaiPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_thai_rows_are_complete_and_native(self):
        total_rows = 0
        all_sources: set[str] = set()
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        localized_date = "ปรับปรุงและมีผลตั้งแต่วันที่ 1 มิถุนายน 2024"
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"th"})
                self.assertIsInstance(rows["th"], tuple)
                self.assertEqual(len(rows["th"]), count)
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
                    "th"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["th"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertRegex(value, r"[\u0e00-\u0e7f]")
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
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
                        for canned_english in (
                            "This ",
                            "We do not ",
                            "You can ",
                            "The ",
                        ):
                            self.assertNotIn(canned_english, value)
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["th"].count(localized_date) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_THAI_ROWS)
        privacy = mapped("privacy", PRIVACY_THAI_ROWS)
        agreement = mapped("agreement", AGREEMENT_THAI_ROWS)
        self.assertEqual(howto["How to use Go and Help"], "วิธีใช้ Go and Help")
        self.assertEqual(howto["Reviews"], "รีวิว")
        self.assertEqual(howto["Emergencies"], "เหตุฉุกเฉิน")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "นโยบายความเป็นส่วนตัวและคุกกี้",
        )
        self.assertEqual(agreement["User agreement"], "ข้อตกลงผู้ใช้")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("ตั๋วรายเดือน", membership)
        self.assertIn("บัตรรายปี", membership)

    def test_thai_sources_credits_and_global_coverage(self):
        authored = POLICY_CATALOGS["th"]
        effective = catalog("th")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "th"), ())
        self.assertEqual(missing_policy_sources(effective, "th"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        frozen_credits = (
            "กิตติกรรมประกาศ",
            "แผนที่เปิดและโครงการโอเพนซอร์สที่วาดแผนที่ Go and Help ทุกแผนที่",
            "ปรับปรุงและมีผลตั้งแต่วันที่ 1 มิถุนายน 2024",
            "Go and Help วาดขึ้นบนข้อมูลเปิดที่อาสาสมัครทั่วโลกสร้างขึ้น กิตติกรรมประกาศเหล่านี้เป็นส่วนหนึ่งของเงื่อนไขใบอนุญาตที่เรายินดีปฏิบัติตาม",
            "แผนที่และข้อมูลแผนที่",
            "ไทล์แผนที่โดย OpenFreeMap ข้อมูล © ผู้ร่วมจัดทำ OpenStreetMap ภายใต้ Open Database License (ODbL)",
            "OpenStreetMap เผยแพร่ข้อมูลแผนที่ภายใต้ Open Database License (ODbL)",
            "OpenFreeMap สร้างขึ้นจากโครงการโอเพนซอร์สที่ยอดเยี่ยมหลายโครงการ รวมถึงเครื่องมืออย่าง MapLibre, Planetiler และ OpenMapTiles",
        )
        self.assertEqual(CREDITS_ROWS["th"], frozen_credits)
        self.assertEqual(authored["Credits"], "กิตติกรรมประกาศ")
        self.assertEqual(effective["Credits"], "ขอบคุณผู้มีส่วนร่วม")
        for source, value in zip(
            DOCUMENT_SOURCE_KEYS["credits"], frozen_credits, strict=True
        ):
            if source != "Credits":
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
        self.assertGreaterEqual(authored_total, 3784)
        self.assertGreaterEqual(effective_total, 3874)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["th"], 0)

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_THAI_ROWS)
        privacy = mapped("privacy", PRIVACY_THAI_ROWS)
        agreement = mapped("agreement", AGREEMENT_THAI_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "มีสามตำแหน่งเท่านั้น",
                    "พิกัดที่บันทึกไว้ยังคงอยู่ในบัญชีของคุณ",
                    "ไม่มีการส่งพิกัดไปที่ใด",
                    "ระหว่าง 500m ถึง 1km",
                    "เก็บจุดจริงเป็นส่วนตัว",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                ("112", "999", "911", "000", "ทั่วสหภาพยุโรป"),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "ปิดเป็นค่าเริ่มต้นของทุกบัญชี",
                    "จะไม่แสดงแก่ใคร",
                    "คุณจะไม่ปรากฏบนแผนที่หรือในการค้นหาผู้คน",
                    "ไม่มีการส่งพิกัดใด ๆ",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "อ่านตำแหน่งจากเบราว์เซอร์ของคุณหนึ่งครั้ง",
                    "เก็บจุดนั้นไว้เป็นส่วนตัว",
                    "ไม่มีการติดตามเบื้องหลัง",
                    "เบราว์เซอร์จะขออนุญาตจากคุณ",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "เราไม่เผยแพร่จุดที่คุณบันทึกไว้",
                    "ระหว่าง 500m ถึง 1km",
                    "หยุดการแชร์ทันที",
                    "โดยไม่ลบพิกัดที่คุณบันทึกไว้",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "จะไม่เผยแพร่ที่อยู่ที่คุณพิมพ์",
                    "ผู้ช่วยที่คุณยืนยันแล้ว",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help ให้บริการแก่ผู้มีอายุ 16 ปีขึ้นไป",
                    "อย่างน้อย 16 ปี",
                    "เราไม่เก็บข้อมูลเด็กโดยเจตนา",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "ต่ออายุอัตโนมัติทุกเดือน",
                    "ต่ออายุอัตโนมัติทุกปี",
                    "จนกว่าคุณจะยกเลิก",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "คุณยกเลิกได้ทุกเมื่อ",
                    "จนสิ้นสุดระยะเวลาที่คุณชำระเงินไว้แล้ว",
                    "เว้นแต่กฎหมายท้องถิ่นกำหนดเป็นอย่างอื่น",
                    "จะไม่มีการคืนเงินสำหรับระยะเวลาบางส่วน",
                    "สิทธิตามกฎหมายในการเพิกถอนหรือยกเลิก",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "จำนวนที่สูงกว่าระหว่าง",
                    "ช่วง 12 เดือนก่อนการเรียกร้อง",
                    "50 ดอลลาร์สหรัฐ",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "ไม่มีข้อความใดในข้อตกลงนี้ยกเว้นหรือจำกัดความรับผิด",
                    "กฎหมายไม่อนุญาตให้ยกเว้นหรือจำกัด",
                    "การเสียชีวิตหรือบาดเจ็บส่วนบุคคลที่เกิดจากความประมาทเลินเล่อ",
                    "การฉ้อโกงหรือการแถลงข้อความอันเป็นเท็จโดยฉ้อฉล",
                    "สิทธิผู้บริโภคที่กฎหมายกำหนด",
                    "สิทธิบังคับตามกฎหมายท้องถิ่นของคุณไม่ได้รับผลกระทบ",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "หากคุณเป็นผู้บริโภค",
                    "กฎหมายผู้บริโภคภาคบังคับ",
                    "สิทธิในการยื่นข้อเรียกร้องต่อศาลในท้องถิ่น",
                    "ให้ใช้กฎภาคบังคับนั้นเป็นหลัก",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertIn("จำนวนที่สูงกว่าระหว่าง", maximum)
        self.assertIn("ช่วง 12 เดือนก่อนการเรียกร้อง", maximum)
        self.assertIn("50 ดอลลาร์สหรัฐ", maximum)

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
