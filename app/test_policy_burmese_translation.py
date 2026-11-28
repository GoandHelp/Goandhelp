import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_burmese as agreement_data
from app import policy_catalog_howto_burmese as howto_data
from app import policy_catalog_privacy_burmese as privacy_data
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
from app.policy_catalog_agreement_burmese import AGREEMENT_BURMESE_ROWS
from app.policy_catalog_howto_burmese import HOWTO_BURMESE_ROWS
from app.policy_catalog_privacy_burmese import PRIVACY_BURMESE_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_BURMESE_ROWS", HOWTO_BURMESE_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_BURMESE_ROWS", PRIVACY_BURMESE_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_BURMESE_ROWS",
        AGREEMENT_BURMESE_ROWS,
        51,
    ),
)
MYANMAR = re.compile(r"[\u1000-\u109f]")
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
PROPER_NAMES = (
    "Open Database License",
    "Go and Help",
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
    "USD",
    "©",
    "IP",
    "PIN",
)
MYANMAR_DATE = "2024 ခုနှစ် ဇွန်လ 1 ရက်တွင် ပြင်ဆင်မွမ်းမံပြီး အကျိုးသက်ရောက်သည်"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["my"], strict=True))


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
    for name in sorted(PROPER_NAMES, key=len, reverse=True):
        text = text.replace(name, " ")
    return re.findall(r"[A-Za-z]{2,}", text)


class BurmesePolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_burmese_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"my"})
                self.assertIsInstance(rows["my"], tuple)
                self.assertEqual(len(rows["my"]), count)
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
                    "my"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["my"])
                for source, value in entries.items():
                    with self.subTest(source=source[:55]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, MYANMAR)
                        self.assertNotIn("\ufffd", value)
                        self.assertFalse(latin_residue(value), value)
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(number_set(source) <= number_set(value))
                        if len(source) >= 280:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.35
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["my"].count(MYANMAR_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_BURMESE_ROWS)
        privacy = mapped("privacy", PRIVACY_BURMESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_BURMESE_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help အသုံးပြုနည်း"
        )
        self.assertEqual(howto["Reviews"], "သုံးသပ်ချက်များ")
        self.assertEqual(howto["Emergencies"], "အရေးပေါ်အခြေအနေများ")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "ကိုယ်ရေးလုံခြုံမှုနှင့် ကွတ်ကီးမူဝါဒ",
        )
        self.assertEqual(agreement["User agreement"], "အသုံးပြုသူသဘောတူညီချက်")

    def test_complete_coverage_frozen_credits_and_progress(self):
        authored = POLICY_CATALOGS["my"]
        effective = catalog("my")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "my"), ())
        self.assertEqual(missing_policy_sources(effective, "my"), ())
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["my"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
        self.assertEqual(credits["Credits"], "ကျေးဇူးတင်အသိအမှတ်ပြုမှုများ")
        self.assertEqual(authored["Credits"], "ကျေးဇူးတင်အသိအမှတ်ပြုမှုများ")
        self.assertEqual(effective["Credits"], "ကျေးဇူးတင်လွှာ")
        for source, value in credits.items():
            if source != "Credits":
                self.assertEqual(effective[source], value)
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
        self.assertGreaterEqual(authored_total, 6394)
        self.assertGreaterEqual(effective_total, 6409)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertLessEqual(missing_total, 507)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 35)

    def test_merged_safety_and_source_bound_privacy_and_legal_clauses(self):
        howto = mapped("howto", HOWTO_BURMESE_ROWS)
        privacy = mapped("privacy", PRIVACY_BURMESE_ROWS)
        agreement = mapped("agreement", AGREEMENT_BURMESE_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], MYANMAR)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                "ပိတ်ထားသည်ကို ရွေးလျှင် မြေပုံအားလုံးနှင့် လူရှာဖွေမှုတို့မှ သင်ပျောက်ကွယ်မည်။ သိမ်းဆည်းထားသော ကိုဩဒိနိတ်များသည် သင့်အကောင့်ထဲတွင် ကျန်နေမည်ဖြစ်သော်လည်း ကိုဩဒိနိတ်တစ်ခုမျှ မည်သည့်နေရာသို့မျှ ပို့မည်မဟုတ်ပါ။",
            ),
            (
                howto,
                "howto",
                "Set my location offers three positions",
                "အနီးစပ်ဆုံးကို ရွေးလျှင် သင့်တိကျသောနေရာကို လျှို့ဝှက်ထားပြီး 500m မှ 1km အကွာရှိ ကုန်းမြေပေါ် လုံခြုံသော နေရာတစ်ခုကိုသာ အသုံးပြုသူအားလုံးထံ ဖော်ပြမည်။",
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                "ကျွန်ုပ်၏တည်နေရာ သတ်မှတ်ရန်တွင် ပိတ်ထားသည်ကို ရွေးလျှင် သိမ်းဆည်းထားသော သင့်ကိုဩဒိနိတ်များကို မည်သူမျှ မမြင်ရ၊ သင်သည် မြေပုံ သို့မဟုတ် လူရှာဖွေမှုတွင် မပေါ်လာဘဲ ကိုဩဒိနိတ်တစ်ခုမျှ ပေးပို့ခြင်း မရှိပါ။",
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                "ထိုနေရာမှ 500m မှ 1km အကွာရှိ တည်ငြိမ်ပြီး ကုန်းမြေပေါ်လုံခြုံသော နေရာတစ်ခုကို တွက်ချက်ကာ ထိုနေရာကိုသာ ဖော်ပြသည်။",
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                "အမှန်တကယ်ရှိသောနေရာမှ 0.5–1 km အကွာအဝေးကို ခန့်မှန်းပြသပြီး သင်ရေးထည့်သော လိပ်စာကို မည်သည့်အခါမျှ မဖော်ပြပါ။",
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                "အရေးပေါ်အခြေအနေတွင် သင့်ဒေသရှိ အရေးပေါ်ဝန်ဆောင်မှုများကို အရင်ဆက်သွယ်ပါ။ Go and Help သည် အရေးပေါ်ဝန်ဆောင်မှု မဟုတ်သလို ဖြစ်ပွားရာနေရာတွင်လည်း ဝင်ရောက်ကူညီနိုင်ခြင်း မရှိပါ။",
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first — not us",
                "အရေးပေါ်အခြေအနေတွင် ကျွန်ုပ်တို့ကိုမဟုတ်ဘဲ သင့်ဒေသရှိ အရေးပေါ်ဝန်ဆောင်မှုများကို အရင်ဆက်သွယ်ပါ။ Go and Help တွင် အရေးပေါ်ဖုန်းလိုင်း၊ လုံခြုံရေးအဖွဲ့ သို့မဟုတ် သင့်ကိုယ်စား မည်သူ့ထံ ဆက်သွယ်ပေးနိုင်သည့်နည်းလမ်း မရှိပါ။",
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                "112 ကို ဥရောပသမဂ္ဂနှင့် အခြားနိုင်ငံများစွာတွင် သုံးနိုင်သည်။ အခြားနေရာများတွင် 999၊ 911၊ 000 နှင့် အခြားနံပါတ်များကို သုံးသည်။",
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                "Go and Help ကို အသက် 16 နှစ်နှင့်အထက်သူများအတွက် ရည်ရွယ်သည်။ အကောင့်ဖွင့်ရန် အသက်အနည်းဆုံး 16 နှစ် ရှိရမည်။",
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                "သင်သည် အသက်အနည်းဆုံး 16 နှစ်ရှိပြီး ဤသဘောတူညီချက်ကို ဝင်ရောက်ချုပ်ဆိုရန် ဥပဒေအရ အရည်အချင်းရှိရမည်။",
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                "လစဉ်အသင်းဝင်မှုသည် လတိုင်း အလိုအလျောက်သက်တမ်းတိုးပြီး နှစ်စဉ်အသင်းဝင်မှုသည် နှစ်တိုင်း အလိုအလျောက်သက်တမ်းတိုးကာ သင်ပယ်ဖျက်သည်အထိ ဆက်လက်လည်ပတ်မည်။",
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                "ထိုသို့ပယ်ဖျက်ပြီးနောက် သင်ပေးချေပြီးသားကာလ ကုန်ဆုံးသည်အထိ အကျိုးခံစားခွင့်များ ဆက်ရှိမည်။",
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                "ဒေသန္တရဥပဒေက ပြန်အမ်းရန် သတ်မှတ်ထားသည့်အခါမှအပ ကာလတစ်စိတ်တစ်ပိုင်းအတွက် ငွေပြန်မအမ်းပါ။",
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                "သင့်အပေါ်ရှိ ကျွန်ုပ်တို့၏ စုစုပေါင်းတာဝန်ကို တောင်းဆိုချက်မတိုင်မီ ယခင် 12 လအတွင်း သင်ပေးခဲ့သော အသင်းဝင်ကြေး သို့မဟုတ် 50 USD တို့အနက် ပိုများသည့်ပမာဏအထိ ကန့်သတ်ထားသည်။",
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                "ဖယ်ရှားခြင်း သို့မဟုတ် ကန့်သတ်ခြင်းကို ဥပဒေက ခွင့်မပြုသော တာဝန်ကို ဤသဘောတူညီချက်ပါ မည်သည့်အချက်မျှ ဖယ်ရှားခြင်း သို့မဟုတ် ကန့်သတ်ခြင်း မပြုပါ။",
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                "တရားရုံးက ဤအပိုင်းတစ်ခုကို အာဏာသက်ရောက်မှုမရှိဟု ဆုံးဖြတ်သော်လည်း ကျန်အချက်များ ဆက်လက်သက်ရောက်မည်ဖြစ်ပြီး သင့်ဒေသဆိုင်ရာ မဖြစ်မနေအခွင့်အရေးများကို မထိခိုက်စေပါ။",
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                "သင်သည် စားသုံးသူဖြစ်ပါက သင်ပုံမှန်နေထိုင်ရာနိုင်ငံ၏ မဖြစ်မနေလိုက်နာရသော စားသုံးသူဥပဒေကပေးသည့် ကာကွယ်မှု သို့မဟုတ် သင့်ဒေသတရားရုံးတွင် တောင်းဆိုခွင့်ကို ဤနေရာတွင် မည်သည့်အရာမျှ မဖယ်ရှားပါ။",
            ),
        )
        for values, document, prefix, phrase in clauses:
            with self.subTest(source=prefix, phrase=phrase):
                self.assertIn(phrase, lookup(values, document, prefix))
        membership = lookup(
            howto, "howto", "There are two options — a monthly Ticket"
        )
        self.assertIn(
            "ရွေးချယ်စရာနှစ်မျိုးမှာ လစဉ်လက်မှတ်နှင့် နှစ်စဉ်အသင်းဝင်ခွင့်ဖြစ်ပြီး နှစ်မျိုးစလုံးက အကျိုးခံစားခွင့်တူညီစွာ ပေးသည်။",
            membership,
        )

    def test_frozen_english_sources_and_shared_burmese_date(self):
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
        for document in ("howto", "privacy", "agreement"):
            translated = mapped(
                document,
                {
                    "my": tuple(
                        POLICY_CATALOGS["my"][source]
                        for source in DOCUMENT_SOURCE_KEYS[document]
                    )
                },
            )
            self.assertEqual(
                translated[POLICY_DOCUMENTS[document]["updated"]], MYANMAR_DATE
            )
        self.assertEqual(
            sum(row["my"].count(MYANMAR_DATE) for *_, row, _ in BATCH), 3
        )
        self.assertEqual(CREDITS_ROWS["my"][2], MYANMAR_DATE)


if __name__ == "__main__":
    unittest.main()
