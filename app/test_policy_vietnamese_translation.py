import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_vietnamese as agreement_data
from app import policy_catalog_howto_vietnamese as howto_data
from app import policy_catalog_privacy_vietnamese as privacy_data
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
from app.policy_catalog_agreement_vietnamese import AGREEMENT_VIETNAMESE_ROWS
from app.policy_catalog_howto_vietnamese import HOWTO_VIETNAMESE_ROWS
from app.policy_catalog_privacy_vietnamese import PRIVACY_VIETNAMESE_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_VIETNAMESE_ROWS", HOWTO_VIETNAMESE_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_VIETNAMESE_ROWS",
        PRIVACY_VIETNAMESE_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_VIETNAMESE_ROWS",
        AGREEMENT_VIETNAMESE_ROWS,
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
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["vi"], strict=True))


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


class VietnamesePolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_vietnamese_rows_are_complete_and_native(self):
        total_rows = 0
        all_sources: set[str] = set()
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        localized_date = "Cập nhật và có hiệu lực từ ngày 1 tháng 6 năm 2024"
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"vi"})
                self.assertIsInstance(rows["vi"], tuple)
                self.assertEqual(len(rows["vi"]), count)
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
                    "vi"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["vi"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
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
                            self.assertGreaterEqual(
                                len(value.split()), len(source.split()) * 0.50
                            )
                        for canned_english in (
                            "This ",
                            "We do not ",
                            "You can ",
                        ):
                            self.assertNotIn(canned_english, value)
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["vi"].count(localized_date) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_VIETNAMESE_ROWS)
        privacy = mapped("privacy", PRIVACY_VIETNAMESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_VIETNAMESE_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Cách sử dụng Go and Help"
        )
        self.assertEqual(howto["Reviews"], "Đánh giá")
        self.assertEqual(howto["Emergencies"], "Trường hợp khẩn cấp")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "Chính sách quyền riêng tư và cookie",
        )
        self.assertEqual(agreement["User agreement"], "Thỏa thuận người dùng")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("Vé tháng", membership)
        self.assertIn("Vé năm", membership)

    def test_vietnamese_sources_credits_and_global_coverage(self):
        authored = POLICY_CATALOGS["vi"]
        effective = catalog("vi")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "vi"), ())
        self.assertEqual(missing_policy_sources(effective, "vi"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        frozen_credits = (
            "Ghi nhận đóng góp",
            "Các bản đồ mở và dự án mã nguồn mở vẽ nên mọi bản đồ Go and Help.",
            "Cập nhật và có hiệu lực từ ngày 1 tháng 6 năm 2024",
            "Go and Help được vẽ trên dữ liệu mở do các tình nguyện viên trên khắp thế giới tạo ra. Những ghi nhận đóng góp này là một phần của các điều khoản cấp phép mà chúng tôi vui lòng tuân thủ.",
            "Bản đồ và dữ liệu bản đồ",
            "Ô bản đồ do OpenFreeMap cung cấp, dữ liệu © những người đóng góp cho OpenStreetMap, theo Open Database License (ODbL).",
            "Dữ liệu bản đồ được OpenStreetMap cung cấp theo Open Database License (ODbL).",
            "OpenFreeMap được xây dựng dựa trên nhiều dự án mã nguồn mở tuyệt vời, bao gồm các công cụ như MapLibre, Planetiler và OpenMapTiles.",
        )
        self.assertEqual(CREDITS_ROWS["vi"], frozen_credits)
        self.assertEqual(authored["Credits"], "Ghi nhận đóng góp")
        self.assertEqual(effective["Credits"], "Ghi nhận đóng góp")
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
        self.assertGreaterEqual(authored_total, 3610)
        self.assertGreaterEqual(effective_total, 3705)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["vi"], 0)

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_VIETNAMESE_ROWS)
        privacy = mapped("privacy", PRIVACY_VIETNAMESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_VIETNAMESE_ROWS)
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
                    "ba lựa chọn",
                    "tọa độ đã lưu vẫn nằm trong tài khoản của bạn",
                    "không có tọa độ nào được gửi đi đâu cả",
                    "từ 500m đến 1km",
                    "giữ kín điểm chính xác",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                ("112", "999", "911", "000", "trên toàn Liên minh châu Âu"),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Tắt là mặc định cho mọi tài khoản",
                    "không hiển thị với bất kỳ ai",
                    "bạn không xuất hiện trên bản đồ hay trong tìm kiếm người dùng",
                    "không tọa độ nào được truyền đi",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "chỉ đọc vị trí từ trình duyệt một lần",
                    "lưu riêng điểm đó",
                    "Không có theo dõi nền",
                    "Trình duyệt sẽ xin phép",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "Chúng tôi không bao giờ công bố điểm đã lưu của bạn",
                    "từ 500m đến 1km",
                    "dừng chia sẻ ngay lập tức",
                    "không xóa tọa độ bạn đã lưu",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "địa chỉ bạn nhập không bao giờ được công bố",
                    "người giúp đỡ mà bạn xác nhận",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help dành cho người từ 16 tuổi trở lên",
                    "ít nhất 16 tuổi",
                    "không cố ý thu thập thông tin của trẻ em",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "tự động gia hạn mỗi tháng",
                    "tự động gia hạn mỗi năm",
                    "cho đến khi bạn hủy",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "Bạn có thể hủy bất cứ lúc nào",
                    "đến hết kỳ bạn đã thanh toán",
                    "Trừ khi luật địa phương yêu cầu khác",
                    "không được hoàn tiền",
                    "quyền rút lại hoặc hủy theo luật định",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "mức cao hơn giữa",
                    "trong 12 tháng trước khi khiếu nại phát sinh",
                    "50 đô la Mỹ",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "Không điều khoản nào trong thỏa thuận này",
                    "pháp luật không cho phép loại trừ hoặc giới hạn",
                    "tử vong hoặc thương tích do sơ suất",
                    "gian lận hoặc trình bày sai sự thật có chủ ý",
                    "các quyền bắt buộc của người tiêu dùng",
                    "các quyền bắt buộc của bạn theo luật địa phương không bị ảnh hưởng",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "nếu bạn là người tiêu dùng",
                    "luật người tiêu dùng bắt buộc",
                    "quyền khởi kiện tại tòa án địa phương",
                    "quy định bắt buộc sẽ được ưu tiên áp dụng",
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
        self.assertIn("trong 12 tháng", maximum)
        self.assertIn("50 đô la Mỹ", maximum)

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
