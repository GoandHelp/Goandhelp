import ast
import re
import string
import unittest
import unicodedata
from pathlib import Path

from app.components.auth_panel import (
    LEGAL_SECTIONS,
    legal_dialog,
    legal_section,
)
from app.interface_catalog_legal import LEGAL_CATALOGS, LEGAL_KEYS, LEGAL_ROWS
from app.interface_catalog_legal_east_asian import LEGAL_EAST_ASIAN_ROWS
from app.interface_catalog_legal_european_a import LEGAL_EUROPEAN_A_ROWS
from app.interface_catalog_legal_european_b import LEGAL_EUROPEAN_B_ROWS
from app.interface_catalog_legal_south_asian_a import LEGAL_SOUTH_ASIAN_A_ROWS
from app.interface_catalog_legal_south_asian_b import LEGAL_SOUTH_ASIAN_B_ROWS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS

ROOT = Path(__file__).parent


def _decimal_runs(value: str) -> list[str]:
    return re.findall(r"\d+", value)


class AuthLegalTranslationTests(unittest.TestCase):
    def test_canonical_english_policy_sections_and_exact_sources(self):
        expected = [
            "Go and Help connects members who offer help with members who need it. You must be 16 or over, give accurate details and keep your account to yourself. Agree tasks, rewards and meeting points inside the platform, turn up when you say you will, and treat every member with respect. Go and Help is not an employer and does not supervise work: you remain responsible for your own safety, permits, tax and insurance. Illegal requests, harassment, discrimination, spam and attempts to move payment or identity checks off-platform lead to removal. Ratings must reflect real, completed work.",
            "We store the details you give us — first and family name, email, phone number, date of birth and profile content — to run your account, confirm your email and match you with nearby requests. Your date of birth is private account-verification data: we use it only to confirm you are 16 or over and never show it, or an age derived from it, to other members or guests. Guests only ever see job titles, categories and a rough area; exact meeting points, contact details and identities are unlocked for confirmed members involved in a task. We never sell your data and only share it with the services that deliver our emails and host the platform. You can update your profile, change your language, or ask us to delete your account and its data at any time.",
            "Go and Help uses a small number of essential cookies and local storage entries to keep you signed in, remember your language and protect the sign-in form from abuse. We use privacy-friendly, aggregated measurement to understand which features members use, and no advertising or cross-site tracking cookies. Clearing your browser storage signs you out and resets these preferences.",
        ]
        self.assertEqual(
            [section["body"] for section in LEGAL_SECTIONS], expected
        )
        self.assertEqual(tuple(LEGAL_KEYS[4:]), tuple(expected))
        self.assertEqual(len(LEGAL_KEYS), 7)
        self.assertTrue(set(LEGAL_KEYS) <= set(COMPLETE_KEYS))

    def test_catalog_is_static_and_exact_for_every_locale(self):
        expected_parts = (
            (
                "interface_catalog_legal_european_a.py",
                "LEGAL_EUROPEAN_A_ROWS",
                LEGAL_EUROPEAN_A_ROWS,
                {"cs", "da", "el", "fi", "hu", "it"},
            ),
            (
                "interface_catalog_legal_european_b.py",
                "LEGAL_EUROPEAN_B_ROWS",
                LEGAL_EUROPEAN_B_ROWS,
                {"nl", "pl", "pt", "ro", "sv", "tr"},
            ),
            (
                "interface_catalog_legal_south_asian_a.py",
                "LEGAL_SOUTH_ASIAN_A_ROWS",
                LEGAL_SOUTH_ASIAN_A_ROWS,
                {"bn", "gu", "kn", "ml", "mr", "ne"},
            ),
            (
                "interface_catalog_legal_south_asian_b.py",
                "LEGAL_SOUTH_ASIAN_B_ROWS",
                LEGAL_SOUTH_ASIAN_B_ROWS,
                {"am", "fa", "he", "sw", "ta", "te"},
            ),
            (
                "interface_catalog_legal_east_asian.py",
                "LEGAL_EAST_ASIAN_ROWS",
                LEGAL_EAST_ASIAN_ROWS,
                {"id", "ko", "my", "th", "vi"},
            ),
        )
        all_parts: list[dict[str, tuple[str, ...]]] = []
        combined_part_locales: set[str] = set()
        for filename, variable, part, expected_locales in expected_parts:
            with self.subTest(part=variable):
                tree = ast.parse((ROOT / filename).read_text())
                rows = next(
                    node.value
                    for node in tree.body
                    if isinstance(node, ast.AnnAssign)
                    and getattr(node.target, "id", "") == variable
                )
                self.assertEqual(ast.literal_eval(rows), part)
                self.assertEqual(set(part), expected_locales)
                self.assertFalse(combined_part_locales & set(part))
                combined_part_locales.update(part)
                all_parts.append(part)

        main_tree = ast.parse((ROOT / "interface_catalog_legal.py").read_text())
        legacy_rows = next(
            node.value
            for node in main_tree.body
            if isinstance(node, ast.AnnAssign)
            and getattr(node.target, "id", "") == "_EXISTING_LEGAL_ROWS"
        )
        legacy_literal = ast.literal_eval(legacy_rows)
        self.assertEqual(
            legacy_literal,
            {
                locale: row
                for locale, row in LEGAL_ROWS.items()
                if locale not in combined_part_locales
            },
        )
        self.assertEqual(
            set(legacy_literal),
            {"es", "fr", "de", "ar", "zh", "hi", "ja", "ha"},
        )
        offered = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
        expected_locales = offered | {"ha"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(set(LEGAL_ROWS), expected_locales)
        self.assertEqual(set(LEGAL_CATALOGS), expected_locales)
        self.assertEqual(combined_part_locales, offered - set(legacy_literal))
        self.assertEqual(
            LEGAL_ROWS,
            {
                **legacy_literal,
                **{
                    locale: row
                    for part in all_parts
                    for locale, row in part.items()
                },
            },
        )

        for locale, row in LEGAL_ROWS.items():
            with self.subTest(locale=locale):
                self.assertEqual(len(row), 7)
                self.assertEqual(set(LEGAL_CATALOGS[locale]), set(LEGAL_KEYS))
                self.assertEqual(
                    set(LEGAL_KEYS), set(COMPLETE_KEYS) & set(LEGAL_KEYS)
                )
                for source, value in zip(LEGAL_KEYS, row, strict=True):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertFalse(
                        value.startswith((f"[{locale}]", f"{locale}:"))
                    )
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                    self.assertTrue(CATALOGS[locale][source].strip())
                    source_slots = {
                        field
                        for _, field, _, _ in string.Formatter().parse(source)
                        if field
                    }
                    value_slots = {
                        field
                        for _, field, _, _ in string.Formatter().parse(value)
                        if field
                    }
                    self.assertEqual(value_slots, source_slots)
                self.assertTrue(
                    any(
                        "".join(
                            str(unicodedata.decimal(char)) for char in match
                        )
                        == "16"
                        for match in _decimal_runs(
                            LEGAL_CATALOGS[locale][LEGAL_KEYS[4]]
                        )
                    )
                )

    def test_full_policy_meaning_in_representative_translations(self):
        terms_fi = LEGAL_CATALOGS["fi"][LEGAL_KEYS[4]]
        privacy_fi = LEGAL_CATALOGS["fi"][LEGAL_KEYS[5]]
        cookies_fi = LEGAL_CATALOGS["fi"][LEGAL_KEYS[6]]
        with self.subTest(locale="fi"):
            for phrase in (
                "vähintään 16-vuotias",
                "oikeat tiedot",
                "Sopikaa tehtävistä, palkkioista ja tapaamispaikoista alustalla",
                "Go and Help ei ole työnantaja eikä valvo työtä",
                "turvallisuudestasi, luvista, veroista ja vakuutuksista",
                "Laittomat pyynnöt, häirintä, syrjintä, roskaposti",
                "todelliseen, valmiiksi tehtyyn työhön",
            ):
                self.assertIn(phrase, terms_fi)
            for phrase in (
                "etu- ja sukunimen",
                "sähköpostin, puhelinnumeron, syntymäajan ja profiilisisällön",
                "vain vahvistaaksemme, että olet vähintään 16-vuotias",
                "emmekä koskaan näytä päivämäärää tai siitä laskettua ikää",
                "Vieraat näkevät vain tehtävien otsikot, luokat ja suuntaa-antavan alueen",
                "tarkat tapaamispaikat, yhteystiedot ja henkilöllisyydet",
                "Emme koskaan myy tietojasi",
                "Voit milloin tahansa päivittää profiilisi, vaihtaa kielen",
            ):
                self.assertIn(phrase, privacy_fi)
            for phrase in (
                "välttämättömiä evästeitä ja paikallisen tallennustilan tietoja",
                "pitämiseen, kielen muistamiseen",
                "yksityisyyttä kunnioittavaa koottua mittausta",
                "emme käytä mainoksia emmekä sivustojen välisiä seurantaevästeitä",
                "Selaimen tallennustilan tyhjentäminen kirjaa sinut ulos",
                "palauttaa nämä asetukset",
            ):
                self.assertIn(phrase, cookies_fi)

        terms_zh = LEGAL_CATALOGS["zh"][LEGAL_KEYS[4]]
        privacy_zh = LEGAL_CATALOGS["zh"][LEGAL_KEYS[5]]
        cookies_zh = LEGAL_CATALOGS["zh"][LEGAL_KEYS[6]]
        with self.subTest(locale="zh"):
            self.assertIn("年满16岁", terms_zh)
            self.assertIn("不是雇主，也不监督工作", terms_zh)
            self.assertIn("许可证、税务和保险负责", terms_zh)
            self.assertIn("非法请求、骚扰、歧视、垃圾信息", terms_zh)
            self.assertIn(
                "名字和姓氏、电子邮箱、电话号码、出生日期及个人资料内容",
                privacy_zh,
            )
            self.assertIn("仅用于确认你已满16岁", privacy_zh)
            self.assertIn(
                "绝不向其他会员或访客展示该日期或推算年龄", privacy_zh
            )
            self.assertIn("绝不出售数据", privacy_zh)
            self.assertIn("必要 Cookie 和本地存储", cookies_zh)
            self.assertIn("不使用广告或跨网站跟踪 Cookie", cookies_zh)
            self.assertIn("退出登录并重置这些偏好", cookies_zh)

        terms_am = LEGAL_CATALOGS["am"][LEGAL_KEYS[4]]
        privacy_am = LEGAL_CATALOGS["am"][LEGAL_KEYS[5]]
        cookies_am = LEGAL_CATALOGS["am"][LEGAL_KEYS[6]]
        with self.subTest(locale="am"):
            self.assertIn("ቢያንስ 16 ዓመት", terms_am)
            self.assertIn("አሠሪ አይደለም፣ ሥራንም አይቆጣጠርም", terms_am)
            self.assertIn("ፈቃዶችዎ፣ ግብርዎ እና መድንዎ", terms_am)
            self.assertIn("ቀኑንም ሆነ ከእሱ የተገመተውን ዕድሜ", privacy_am)
            self.assertIn("መረጃዎን ፈጽሞ አንሸጥም", privacy_am)
            self.assertIn("የአካባቢ ማከማቻን", cookies_am)
            self.assertIn("ማስታወቂያም ሆነ", cookies_am)

    def test_legal_copy_uses_reactive_lookups_and_modal_language(self):
        component_tree = ast.parse(
            (ROOT / "components/auth_panel.py").read_text()
        )
        functions = {
            node.name: node
            for node in ast.walk(component_tree)
            if isinstance(node, ast.FunctionDef)
        }
        section = ast.unparse(functions["legal_section"])
        dialog = ast.unparse(functions["legal_dialog"])
        self.assertIn("ui(item['title'])", section)
        self.assertIn("ui(item['body'])", section)
        self.assertIn("ui('Go and Help legal policies')", dialog)
        self.assertIn("lang=AuthState.preferred_language", dialog)
        self.assertIn("dir=AuthState.interface_direction", dialog)
        self.assertTrue(legal_dialog())
        self.assertTrue(legal_section(LEGAL_SECTIONS[0]))

    def test_every_offered_and_legacy_locale_is_registered_in_the_shared_catalog(
        self,
    ):
        expected = {
            code for code, _label in LANGUAGE_OPTIONS if code != "en"
        } | {"ha"}
        self.assertEqual(set(LEGAL_CATALOGS), expected)
        for locale in expected:
            with self.subTest(locale=locale):
                self.assertTrue(set(LEGAL_KEYS) <= set(CATALOGS[locale]))
                self.assertTrue(set(LEGAL_KEYS) <= set(COMPLETE_KEYS))
                for source in LEGAL_KEYS:
                    self.assertTrue(CATALOGS[locale][source].strip())
                    self.assertNotEqual(translate(locale, source), source)
