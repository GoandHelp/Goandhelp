import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_chinese as agreement_data
from app import policy_catalog_howto_chinese as howto_data
from app import policy_catalog_privacy_chinese as privacy_data
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
from app.policy_catalog_agreement_chinese import AGREEMENT_CHINESE_ROWS
from app.policy_catalog_howto_chinese import HOWTO_CHINESE_ROWS
from app.policy_catalog_privacy_chinese import PRIVACY_CHINESE_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_CHINESE_ROWS", HOWTO_CHINESE_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_CHINESE_ROWS", PRIVACY_CHINESE_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_CHINESE_ROWS",
        AGREEMENT_CHINESE_ROWS,
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
# Established Chinese technical loanword already used in the existing title.
LATIN_LOANWORDS = frozenset({"Cookie"})
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
CHINESE_CREDITS = (
    "致谢",
    "绘制每一张 Go and Help 地图的开放地图和开源项目。",
    "更新并生效于2024年6月1日",
    "Go and Help 的地图基于世界各地志愿者制作的开放数据绘制。这些致谢是许可条款的一部分，我们乐于遵守这些条款。",
    "地图与地图数据",
    "地图瓦片由 OpenFreeMap 提供，数据 © OpenStreetMap 贡献者，依据 Open Database License (ODbL)。",
    "OpenStreetMap 根据 Open Database License (ODbL) 提供地图数据。",
    "OpenFreeMap 建立在多个出色的开源项目之上，其中包括 MapLibre、Planetiler 和 OpenMapTiles 等工具。",
)
CHINESE_DATE = "更新并生效于2024年6月1日"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["zh"], strict=True))


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


class ChinesePolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_and_full_length(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"zh"})
                self.assertIsInstance(rows["zh"], tuple)
                self.assertEqual(len(rows["zh"]), count)
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
                    "zh"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["zh"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, CJK)
                        self.assertNotIn("\ufffd", value)
                        self.assertTrue(
                            set(latin_residue(value)) <= LATIN_LOANWORDS,
                            msg=f"English prose residue: {value[:80]}",
                        )
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(
                            normalized_numbers(source)
                            <= normalized_numbers(value),
                            msg=f"Lost numeric fact: {source[:100]}",
                        )
                        # Character-based bound for compact CJK script; no
                        # whitespace word segmentation is assumed.
                        if len(source) >= 280:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.25
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["zh"].count(CHINESE_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_CHINESE_ROWS)
        privacy = mapped("privacy", PRIVACY_CHINESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_CHINESE_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "如何使用 Go and Help"
        )
        self.assertEqual(howto["Reviews"], "评价")
        self.assertEqual(howto["Emergencies"], "紧急情况")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "隐私与 Cookie 政策"
        )
        self.assertEqual(agreement["User agreement"], "用户协议")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("按月计费的“月票”和按年计费的“年票”", membership)
        self.assertIn("两者解锁的权益完全相同", membership)
        self.assertIn("付款由 Stripe 处理", membership)

    def test_chinese_coverage_frozen_credits_and_global_progress(self):
        authored = POLICY_CATALOGS["zh"]
        effective = catalog("zh")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "zh"), ())
        self.assertEqual(missing_policy_sources(effective, "zh"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:75]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], CJK)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        self.assertEqual(CREDITS_ROWS["zh"], CHINESE_CREDITS)
        credits = dict(
            zip(DOCUMENT_SOURCE_KEYS["credits"], CHINESE_CREDITS, strict=True)
        )
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(
                effective[source], {"Credits": "鸣谢"}.get(source, value)
            )
        self.assertEqual(authored["Credits"], "致谢")
        self.assertEqual(effective["Credits"], "鸣谢")
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
        self.assertGreaterEqual(authored_total, 5002)
        self.assertGreaterEqual(effective_total, 5057)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["zh"], 0)
        self.assertGreaterEqual(
            sum(not locale_gaps for locale_gaps in gaps.values()), 27
        )

    def test_merged_safety_and_source_bound_policy_safeguards(self):
        howto = mapped("howto", HOWTO_CHINESE_ROWS)
        privacy = mapped("privacy", PRIVACY_CHINESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_CHINESE_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], CJK)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "“设置我的位置”只提供三种选项，没有任何中间选项",
                    "您保存的坐标会保留在您的账户中，但不会向任何地方发送任何坐标",
                    "“大致”会将您的确切位置保密",
                    "只公布一个距离该位置 500m 至 1km、位于陆地上的安全点",
                    "“实时”会向所有用户公布您的准确位置",
                ),
            ),
            (
                howto,
                "howto",
                "Live location depends on your browser",
                (
                    "安全的 https:// 地址",
                    "都会先征求您的许可",
                    "未登录的人永远不会收到任何形式的成员坐标",
                ),
            ),
            (
                privacy,
                "privacy",
                "Location sharing is off until you switch it on",
                (
                    "在您开启之前，位置分享一直处于关闭状态",
                    "其他已登录的成员就可以在成员地图上看到您的确切坐标",
                    "您可以随时切换回“隐藏”",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "“关闭”是每个账户的默认设置",
                    "您保存的坐标不会向任何人显示",
                    "也不会传输任何坐标",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "从您的浏览器读取一次您的位置",
                    "连同获取时间一起私密存储",
                    "没有后台跟踪，也不会持续监视您的设备",
                    "都会征求您的许可",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "我们从不公布您存储的位置点",
                    "距离您 500m 至 1km，并只公布该点",
                    "会立即停止分享，而不会删除您保存的坐标",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "距离真实地点 0.5–1 km 的大致区域",
                    "您输入的地址永远不会被公布",
                    "确切的见面地点只会与您确认的帮助者分享",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112 在整个欧盟以及许多其他国家都可以使用",
                    "999、911、000 以及其他号码则在其他地方使用",
                    "不需要手机有电或数据连接",
                ),
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go",
                (
                    "请首先联系当地的紧急服务",
                    "Go and Help 不是紧急服务，无法在现场进行干预",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help 面向 16 岁及以上的人士",
                    "您必须年满 16 岁才能创建账户",
                    "我们不会在知情的情况下收集儿童的信息",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("您必须年满 16 岁", "您不得使用 Go and Help"),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "由我们的支付处理方 Stripe 收费",
                    "月度会员每月自动续订，年度会员每年自动续订，直到您取消为止",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "您可以随时通过账单门户取消",
                    "您的权益随后将持续到您已付费期间结束为止",
                    "除非当地法律另有要求，否则不足一个计费周期的部分不予退款",
                    "任何法定撤回权或取消权将继续适用",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "我们对您的全部责任以下列两者中较高者为限",
                    "您在索赔前 12 个月内向我们支付的会员费用，或 50 美元",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "都不排除或限制法律不允许排除或限制的责任",
                    "对因过失造成的死亡或人身伤害的责任",
                    "对欺诈或欺诈性虚假陈述的责任",
                    "以及强制性消费者权利",
                    "您在当地享有的强制性权利也不受影响",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "本协议受 Go and Help 网站上所述法律管辖",
                    "如果您是消费者",
                    "惯常居住国家的强制性消费者法律所给予的保护",
                    "在当地法院提起诉讼的权利",
                    "则以该强制性规定为准",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertNotIn("较低者", maximum)
        self.assertNotIn("较少者", maximum)

    def test_frozen_english_source_and_canonical_source_inventory(self):
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
