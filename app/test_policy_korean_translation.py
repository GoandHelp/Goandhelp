import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_korean as agreement_data
from app import policy_catalog_howto_korean as howto_data
from app import policy_catalog_privacy_korean as privacy_data
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
from app.policy_catalog_agreement_korean import AGREEMENT_KOREAN_ROWS
from app.policy_catalog_howto_korean import HOWTO_KOREAN_ROWS
from app.policy_catalog_privacy_korean import PRIVACY_KOREAN_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_KOREAN_ROWS", HOWTO_KOREAN_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_KOREAN_ROWS", PRIVACY_KOREAN_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_KOREAN_ROWS",
        AGREEMENT_KOREAN_ROWS,
        51,
    ),
)
HANGUL = re.compile(r"[\uac00-\ud7a3]")
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
PROPER_NAMES = (
    "Go and Help",
    "Open Database License",
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
    "©",
    "IP",
    "PIN",
)
LATIN_ALLOWED = tuple(sorted(PROPER_NAMES, key=len, reverse=True))
KOREAN_DATE = "2024년 6월 1일 업데이트 및 발효"
EMERGENCY_NOTICE_PREFIX = (
    "In an emergency, contact your local emergency services first. "
    "Go and Help is not an emergency service"
)


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["ko"], strict=True))


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
    for name in LATIN_ALLOWED:
        text = text.replace(name, " ")
    return LATIN_WORD.findall(text)


class KoreanPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_korean_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"ko"})
                self.assertIsInstance(rows["ko"], tuple)
                self.assertEqual(len(rows["ko"]), count)
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
                    "ko"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["ko"])
                for source, value in entries.items():
                    with self.subTest(source=source[:65]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, HANGUL)
                        self.assertNotIn("\ufffd", value)
                        self.assertFalse(latin_residue(value), value)
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(number_set(source) <= number_set(value))
                        if len(source) >= 280:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.30
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        self.assertEqual(
            len(all_sources - {POLICY_DOCUMENTS["credits"]["updated"]}), 174
        )
        self.assertEqual(
            sum(row["ko"].count(KOREAN_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_KOREAN_ROWS)
        privacy = mapped("privacy", PRIVACY_KOREAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_KOREAN_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help 사용 방법"
        )
        self.assertEqual(howto["Reviews"], "리뷰")
        self.assertEqual(howto["Emergencies"], "긴급 상황")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "개인정보 및 쿠키 정책"
        )
        self.assertEqual(agreement["User agreement"], "이용 약관")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("월간 승차권", membership)
        self.assertIn("연간 패스", membership)

    def test_complete_coverage_frozen_credits_and_progress(self):
        authored = POLICY_CATALOGS["ko"]
        effective = catalog("ko")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "ko"), ())
        self.assertEqual(missing_policy_sources(effective, "ko"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:65]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], HANGUL)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["ko"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != "Credits":
                self.assertEqual(effective[source], value)
        self.assertEqual(credits["Credits"], "감사의 글")
        self.assertEqual(authored["Credits"], "감사의 글")
        self.assertEqual(effective["Credits"], "기여자 안내")
        self.assertEqual(
            credits[POLICY_DOCUMENTS["credits"]["updated"]], KOREAN_DATE
        )
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
        self.assertGreaterEqual(authored_total, 5_872)
        self.assertGreaterEqual(effective_total, 5_902)
        self.assertEqual(effective_total + missing_total, 6_916)
        self.assertLessEqual(missing_total, 1_014)
        self.assertEqual(gaps["ko"], 0)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 32)

    def test_merged_safety_and_source_bound_privacy_and_legal_clauses(self):
        howto = mapped("howto", HOWTO_KOREAN_ROWS)
        privacy = mapped("privacy", PRIVACY_KOREAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_KOREAN_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], HANGUL)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "내 위치 설정에는 3가지 선택지만 있으며 중간 선택지는 없습니다.",
                    "저장된 좌표는 계정에 남지만 어떤 좌표도 어디로든 전송되지 않습니다.",
                    "대략적 위치는 정확한 지점을 비공개로 유지하고, 500m에서 1km 떨어진 육지의 안전한 지점만 모든 사용자에게 공개합니다.",
                    "실시간 위치는 정확한 위치를 모든 사용자에게 공개하며, 내 위치 새로 고침을 누를 때마다 갱신됩니다.",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "끄기는 모든 계정의 기본 설정입니다.",
                    "저장된 좌표가 누구에게도 표시되지 않고 지도나 사람 검색에 나타나지 않으며 어떤 좌표도 전송되지 않습니다.",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "저장된 지점을 공개하지 않습니다.",
                    "그 지점에서 500m에서 1km 떨어진 육지의 안전하고 안정적인 지점을 계산해 그 지점만 공개합니다.",
                    "저장된 좌표를 삭제하지 않고 공유가 즉시 중단되므로 나중에 다시 켤 수 있습니다.",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "실제 장소에서 0.5–1 km 떨어진 대략적인 구역만 표시되며 입력한 주소는 공개되지 않습니다.",
                    "정확한 만남 장소는 본인이 확정한 도움 제공자에게만 공유됩니다.",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112는 유럽연합 전역과 여러 국가에서 사용됩니다.",
                    "다른 지역에서는 999, 911, 000 및 기타 번호를 사용합니다.",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help는 16세 이상을 위한 서비스입니다.",
                    "계정을 만들려면 만 16세 이상이어야 합니다.",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                (
                    "만 16세 이상이어야 하며 이 약관을 체결할 법적 능력이 있어야 합니다.",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "월간 회원권은 매월 자동 갱신되고 연간 회원권은 매년 자동 갱신되며 취소할 때까지 계속됩니다.",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "결제 포털에서 언제든지 취소할 수 있으며 혜택은 이미 결제한 기간이 끝날 때까지 유지됩니다.",
                    "현지 법률에서 달리 요구하지 않는 한 기간 중 남은 부분은 환불되지 않습니다.",
                    "거주 지역에서 보장되는 법정 철회권이나 취소권은 계속 적용됩니다.",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                (
                    "총 책임 한도는 청구 전 12개월 동안 본인이 지불한 회원권 요금 또는 미화 50달러 중 더 큰 금액입니다.",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "이 약관의 어떤 내용도 법률상 면제하거나 제한할 수 없는 책임을 배제하거나 제한하지 않습니다.",
                    "여기에는 많은 국가에서 과실로 인한 사망 또는 신체 상해, 사기 또는 사기성 허위 진술에 대한 책임과 강행 소비자 권리가 포함됩니다.",
                    "본인의 현지 강행 권리는 영향을 받지 않습니다.",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "평소 거주하는 국가의 강행 소비자법이 보장하는 보호와 현지 법원에 청구할 권리를 이 약관이 박탈하지 않습니다.",
                    "약관이 그러한 강행 규정과 충돌하면 강행 규정이 우선합니다.",
                ),
            ),
        )
        for values, document, prefix, phrases in clauses:
            value = lookup(values, document, prefix)
            for phrase in phrases:
                with self.subTest(source=prefix, phrase=phrase):
                    self.assertIn(phrase, value)

    def test_frozen_english_sources_and_handbook_emergency_notice(self):
        howto = mapped("howto", HOWTO_KOREAN_ROWS)
        emergency = lookup(howto, "howto", EMERGENCY_NOTICE_PREFIX)
        self.assertIn("먼저 현지 응급 서비스에 연락하세요", emergency)
        self.assertIn(
            "Go and Help는 응급 서비스가 아니며 현장에 개입할 수 없습니다",
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
