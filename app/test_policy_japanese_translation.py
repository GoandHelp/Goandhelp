import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_japanese as agreement_data
from app import policy_catalog_howto_japanese as howto_data
from app import policy_catalog_privacy_japanese as privacy_data
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
from app.policy_catalog_agreement_japanese import AGREEMENT_JAPANESE_ROWS
from app.policy_catalog_howto_japanese import HOWTO_JAPANESE_ROWS
from app.policy_catalog_privacy_japanese import PRIVACY_JAPANESE_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_JAPANESE_ROWS", HOWTO_JAPANESE_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_JAPANESE_ROWS",
        PRIVACY_JAPANESE_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_JAPANESE_ROWS",
        AGREEMENT_JAPANESE_ROWS,
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
LATIN_ALLOWED = tuple(sorted(PROPER_NAMES, key=len, reverse=True))
# Established Japanese technical loanword already used in the existing title.
LATIN_LOANWORDS = frozenset({"Cookie"})
JAPANESE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
HIRAGANA = re.compile(r"[\u3041-\u309f]")
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
JAPANESE_DATE = "2024年6月1日更新・発効"
EMERGENCY_NOTICE_PREFIX = (
    "In an emergency, contact your local emergency services first. "
    "Go and Help is not an emergency service"
)


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["ja"], strict=True))


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


class JapanesePolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_full_native_japanese_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"ja"})
                self.assertIsInstance(rows["ja"], tuple)
                self.assertEqual(len(rows["ja"]), count)
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
                    "ja"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["ja"])
                for source, value in entries.items():
                    with self.subTest(source=source[:70]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, JAPANESE)
                        if len(source) >= 80:
                            self.assertRegex(value, HIRAGANA)
                        self.assertNotIn("\ufffd", value)
                        self.assertTrue(
                            set(latin_residue(value)) <= LATIN_LOANWORDS,
                            msg=f"English prose residue: {value[:80]}",
                        )
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(
                            number_set(source) <= number_set(value),
                            msg=f"Lost numeric fact: {source[:100]}",
                        )
                        # Character-based bound for compact Japanese script; no
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
            sum(row["ja"].count(JAPANESE_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_JAPANESE_ROWS)
        privacy = mapped("privacy", PRIVACY_JAPANESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_JAPANESE_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help の使い方"
        )
        self.assertEqual(howto["Reviews"], "レビュー")
        self.assertEqual(howto["Emergencies"], "緊急事態")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "プライバシーと Cookie のポリシー",
        )
        self.assertEqual(agreement["User agreement"], "利用規約")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("毎月の「月間乗車券」と毎年の「年間パス」", membership)
        self.assertIn("どちらもまったく同じ特典が利用できます", membership)
        self.assertIn("支払いは Stripe が処理し", membership)

    def test_complete_coverage_frozen_credits_and_progress(self):
        authored = POLICY_CATALOGS["ja"]
        effective = catalog("ja")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "ja"), ())
        self.assertEqual(missing_policy_sources(effective, "ja"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:70]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], JAPANESE)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["ja"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
        self.assertEqual(authored["Credits"], "謝辞")
        self.assertEqual(effective["Credits"], "謝辞")
        self.assertEqual(
            credits[POLICY_DOCUMENTS["credits"]["updated"]], JAPANESE_DATE
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
        self.assertGreaterEqual(authored_total, 5524)
        self.assertGreaterEqual(effective_total, 5564)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["ja"], 0)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 30)

    def test_merged_safety_and_source_bound_safeguards(self):
        howto = mapped("howto", HOWTO_JAPANESE_ROWS)
        privacy = mapped("privacy", PRIVACY_JAPANESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_JAPANESE_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], JAPANESE)
            if len(source) >= 80:
                self.assertRegex(howto[source], HIRAGANA)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "「位置を設定」には3つの選択肢があり、その中間はありません",
                    "保存済みの座標はアカウント内に残りますが、座標がどこかに送信されることは一切ありません",
                    "「おおよそ」では正確な地点は非公開のまま保たれ",
                    "500m から 1km 離れた陸上の安全な地点だけが公開され",
                    "「ライブ」では正確な位置がすべてのユーザーに公開され、「現在地を更新」を押すたびに更新されます",
                ),
            ),
            (
                howto,
                "howto",
                "Live location depends on your browser",
                (
                    "安全な https:// アドレス",
                    "どのブラウザも最初に許可を求めます",
                    "ログインしていない人が、どのような種類のメンバー座標も受け取ることはありません",
                ),
            ),
            (
                privacy,
                "privacy",
                "Location sharing is off until you switch it on",
                (
                    "位置情報の共有は、あなたがオンにするまでオフになっています",
                    "ログインしている他のメンバーがメンバー用の地図であなたの正確な座標を見ることができます",
                    "いつでも「非表示」に戻せます",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "「オフ」はすべてのアカウントの初期設定です",
                    "保存された座標は誰にも表示されず",
                    "座標が送信されることは一切ありません",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "ブラウザから現在地を一度読み取り",
                    "その地点を取得時刻とともに非公開で保存します",
                    "バックグラウンドでの追跡や、端末の継続的な監視は行いません",
                    "あなたの許可を求め",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "保存された地点を公開することは決してありません",
                    "500m から 1km 離れた、陸上の安全で安定した地点を算出し、その地点だけを公開します",
                    "保存した座標を削除することなく共有がただちに停止する",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "実際の地点から 0.5–1 km 離れたおおよその範囲",
                    "入力した住所が公開されることは決してありません",
                    "正確な待ち合わせ場所は、あなたが確定した手助けする人にだけ共有されます",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112 は欧州連合全域とその他の多くの国で使えます",
                    "999、911、000 などの番号が使われています",
                    "充電されたスマートフォンやデータ通信がなくても見られる場所",
                ),
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first \u2014 not us",
                (
                    "私たちではなく、まず地元の緊急サービスに連絡してください",
                    "あなたのもとに駆けつけられるのは、警察、救急、消防だけです",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help は16歳以上の方を対象としています",
                    "アカウントを作成するには、16歳以上である必要があります",
                    "子どもの情報を故意に収集することはありません",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                (
                    "16歳以上であり、本規約を締結する法的な能力を有している必要があります",
                    "Go and Help を利用してはなりません",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "決済代行会社である Stripe によって請求されます",
                    "月額メンバーシップは毎月、年額メンバーシップは毎年、あなたが解約するまで自動的に更新されます",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "請求ポータルからいつでも解約できます",
                    "特典はすでに支払い済みの期間の終わりまで継続します",
                    "現地の法律で別段の定めがある場合を除き、期間の途中分は返金されません",
                    "法定の撤回権または解約権は、引き続き適用されます",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                (
                    "請求の前12か月間にあなたが私たちに支払ったメンバーシップ料金、または50米ドルのいずれか高い方を上限とします",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "法律により免除または制限することが認められない責任を免除または制限するものではありません",
                    "過失によって生じた死亡または人身傷害に対する責任",
                    "詐欺または詐欺的な不実表示に対する責任",
                    "強行的な消費者の権利が含まれます",
                    "あなたの現地における強行的な権利は影響を受けません",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "本規約は Go and Help のウェブサイトに記載された法律に準拠します",
                    "あなたが消費者である場合",
                    "あなたが常居所を有する国の強行的な消費者法による保護",
                    "地元の裁判所に訴えを提起するあなたの権利",
                    "強行規定が優先します",
                ),
            ),
        )
        for values, document, prefix, phrases in clauses:
            value = lookup(values, document, prefix)
            for phrase in phrases:
                with self.subTest(source=prefix, phrase=phrase):
                    self.assertIn(phrase, value)
        maximum = lookup(
            agreement, "agreement", "To the same extent, we are not liable"
        )
        self.assertNotIn("低い方", maximum)

    def test_frozen_english_sources_and_unique_emergency_notice(self):
        howto = mapped("howto", HOWTO_JAPANESE_ROWS)
        emergency = lookup(howto, "howto", EMERGENCY_NOTICE_PREFIX)
        self.assertIn("まず地元の緊急サービスに連絡してください", emergency)
        self.assertIn(
            "Go and Help は緊急サービスではなく、現場に介入することはできません",
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
