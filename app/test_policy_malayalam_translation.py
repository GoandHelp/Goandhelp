import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_malayalam as agreement_data
from app import policy_catalog_howto_malayalam as howto_data
from app import policy_catalog_privacy_malayalam as privacy_data
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
from app.policy_catalog_agreement_malayalam import AGREEMENT_MALAYALAM_ROWS
from app.policy_catalog_howto_malayalam import HOWTO_MALAYALAM_ROWS
from app.policy_catalog_privacy_malayalam import PRIVACY_MALAYALAM_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_MALAYALAM_ROWS", HOWTO_MALAYALAM_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_MALAYALAM_ROWS",
        PRIVACY_MALAYALAM_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_MALAYALAM_ROWS",
        AGREEMENT_MALAYALAM_ROWS,
        51,
    ),
)
MALAYALAM = re.compile(r"[\u0d00-\u0d7f]")
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
MALAYALAM_DATE = "1 ജൂൺ 2024ന് പുതുക്കിയതും പ്രാബല്യത്തിൽ വന്നതും"


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["ml"], strict=True))


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
    return re.findall(r"[A-Za-z]{3,}", text)


class MalayalamPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_complete_native_malayalam_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"ml"})
                self.assertIsInstance(rows["ml"], tuple)
                self.assertEqual(len(rows["ml"]), count)
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
                    "ml"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["ml"])
                for source, value in entries.items():
                    with self.subTest(source=source[:65]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, MALAYALAM)
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
                            self.assertGreaterEqual(
                                len(value.split()), len(source.split()) * 0.40
                            )
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            sum(row["ml"].count(MALAYALAM_DATE) for *_, row, _ in BATCH), 3
        )
        howto = mapped("howto", HOWTO_MALAYALAM_ROWS)
        privacy = mapped("privacy", PRIVACY_MALAYALAM_ROWS)
        agreement = mapped("agreement", AGREEMENT_MALAYALAM_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help എങ്ങനെ ഉപയോഗിക്കാം"
        )
        self.assertEqual(howto["Reviews"], "അവലോകനങ്ങൾ")
        self.assertEqual(howto["Emergencies"], "അടിയന്തര സാഹചര്യങ്ങൾ")
        self.assertEqual(
            privacy["Privacy and cookies policy"],
            "സ്വകാര്യതയും കുക്കികളും സംബന്ധിച്ച നയം",
        )
        self.assertEqual(agreement["User agreement"], "ഉപയോക്തൃ കരാർ")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn(
            "രണ്ട് തിരഞ്ഞെടുപ്പുകളുണ്ട് — മാസ ടിക്കറ്റും വാർഷിക പാസും — രണ്ടും ഒരേ ആനുകൂല്യങ്ങൾ നൽകുന്നു.",
            membership,
        )

    def test_complete_coverage_frozen_credits_and_progress(self):
        authored = POLICY_CATALOGS["ml"]
        effective = catalog("ml")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "ml"), ())
        self.assertEqual(missing_policy_sources(effective, "ml"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:65]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], MALAYALAM)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["ml"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            if source != "Credits":
                self.assertEqual(effective[source], value)
        self.assertEqual(credits["Credits"], "കടപ്പാടുകൾ")
        self.assertEqual(authored["Credits"], "കടപ്പാടുകൾ")
        self.assertEqual(effective["Credits"], "നന്ദി രേഖപ്പെടുത്തൽ")
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
        self.assertGreaterEqual(authored_total, 6_046)
        self.assertGreaterEqual(effective_total, 6_071)
        self.assertEqual(effective_total + missing_total, 6_916)
        self.assertLessEqual(missing_total, 845)
        self.assertEqual(gaps["ml"], 0)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 33)

    def test_merged_safety_and_source_bound_privacy_and_legal_clauses(self):
        howto = mapped("howto", HOWTO_MALAYALAM_ROWS)
        privacy = mapped("privacy", PRIVACY_MALAYALAM_ROWS)
        agreement = mapped("agreement", AGREEMENT_MALAYALAM_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], MALAYALAM)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "എന്റെ സ്ഥാനം സജ്ജീകരിക്കുക എന്നതിൽ മൂന്ന് സ്ഥാനങ്ങളുണ്ട്; ഇടയ്ക്കൊരു നിലയില്ല. ഓഫ് തിരഞ്ഞെടുക്കുമ്പോൾ എല്ലാ ഭൂപടങ്ങളിൽനിന്നും ആളുകളെ തിരയുന്നതിൽനിന്നും നിങ്ങൾ ഒഴിവാകും: സംരക്ഷിച്ച കോർഡിനേറ്റുകൾ നിങ്ങളുടെ അക്കൗണ്ടിൽ തുടരും, പക്ഷേ ഒരു കോർഡിനേറ്റും എവിടേക്കും അയയ്ക്കില്ല. ഏകദേശം എന്ന നില നിങ്ങളുടെ കൃത്യമായ സ്ഥാനം സ്വകാര്യമായി സൂക്ഷിച്ച് 500m മുതൽ 1km അകലെയുള്ള കരയിൽ സുരക്ഷിതമായ ഒരു സ്ഥാനം മാത്രം എല്ലാ ഉപയോക്താക്കൾക്കും പ്രസിദ്ധീകരിക്കുന്നു. തത്സമയം എന്ന നില നിങ്ങളുടെ കൃത്യമായ സ്ഥാനം എല്ലാ ഉപയോക്താക്കൾക്കും പ്രസിദ്ധീകരിക്കുകയും എന്റെ സ്ഥാനം പുതുക്കുക അമർത്തുമ്പോഴെല്ലാം പുതുക്കുകയും ചെയ്യുന്നു.",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "എല്ലാ അക്കൗണ്ടുകൾക്കും ഓഫ് ആണ് തുടക്കത്തിലെ ക്രമീകരണം.",
                    "എന്റെ സ്ഥാനം സജ്ജീകരിക്കുക ഓഫ് ആക്കുമ്പോൾ നിങ്ങളുടെ സംരക്ഷിച്ച കോർഡിനേറ്റുകൾ ആരെയും കാണിക്കില്ല, നിങ്ങൾ ഭൂപടങ്ങളിലോ ആളുകളെ തിരയുന്നതിലോ പ്രത്യക്ഷപ്പെടില്ല, ഒരു കോർഡിനേറ്റും കൈമാറുകയുമില്ല.",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "സംരക്ഷിച്ച സ്ഥാനം ഞങ്ങൾ ഒരിക്കലും പ്രസിദ്ധീകരിക്കില്ല: അതിൽനിന്ന് 500m മുതൽ 1km അകലെയുള്ള കരയിൽ സുരക്ഷിതമായ ഒരു സ്ഥാനം കണക്കാക്കി അതുമാത്രം പ്രസിദ്ധീകരിക്കും. വീണ്ടും ഓഫ് തിരഞ്ഞെടുക്കുന്നത് നിങ്ങൾ സംരക്ഷിച്ച കോർഡിനേറ്റുകൾ മായ്ക്കാതെ പങ്കിടൽ ഉടൻ നിർത്തും; പിന്നീട് വീണ്ടും ഓൺ ചെയ്യാം.",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "യഥാർഥ സ്ഥലത്തുനിന്ന് 0.5–1 km അകലെയുള്ള ഏകദേശ പ്രദേശം മാത്രമാണ് കാണിക്കുന്നത്",
                    "നിങ്ങൾ നൽകുന്ന വിലാസം ഒരിക്കലും പ്രസിദ്ധീകരിക്കില്ല.",
                    "കൃത്യമായ കൂടിക്കാഴ്ച സ്ഥലം നിങ്ങൾ സ്ഥിരീകരിച്ച സഹായിയുമായി മാത്രം പങ്കിടും.",
                ),
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                (
                    "അടിയന്തര സാഹചര്യത്തിൽ ആദ്യം നിങ്ങളുടെ പ്രദേശത്തെ അടിയന്തര സേവനങ്ങളുമായി ബന്ധപ്പെടുക.",
                    "Go and Help അടിയന്തര സേവനമല്ല; സംഭവസ്ഥലത്ത് ഇടപെടാനും അതിന് കഴിയില്ല.",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "യൂറോപ്യൻ യൂണിയനിലും മറ്റു പല രാജ്യങ്ങളിലും 112 പ്രവർത്തിക്കുന്നു",
                    "മറ്റിടങ്ങളിൽ 999, 911, 000 തുടങ്ങിയ നമ്പറുകളാണ് ഉപയോഗിക്കുന്നത്.",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help 16 വയസ്സും അതിൽ കൂടുതലുമുള്ളവർക്കാണ്",
                    "അക്കൗണ്ട് സൃഷ്ടിക്കാൻ കുറഞ്ഞത് 16 വയസ്സുണ്ടായിരിക്കണം.",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                (
                    "നിങ്ങൾക്ക് കുറഞ്ഞത് 16 വയസ്സുണ്ടായിരിക്കണം; ഈ കരാറിൽ പ്രവേശിക്കാൻ നിയമപരമായ ശേഷിയും വേണം.",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "മാസ അംഗത്വം ഓരോ മാസവും സ്വയം പുതുക്കും; വാർഷിക അംഗത്വം ഓരോ വർഷവും സ്വയം പുതുക്കും; നിങ്ങൾ റദ്ദാക്കുന്നതുവരെ ഇത് തുടരും.",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "ബില്ലിങ് പോർട്ടലിൽനിന്ന് എപ്പോൾ വേണമെങ്കിലും റദ്ദാക്കാം; ഇതിനകം പണം നൽകിയ കാലയളവ് അവസാനിക്കുന്നതുവരെ ആനുകൂല്യങ്ങൾ തുടരും.",
                    "പ്രാദേശിക നിയമം മറ്റുവിധം ആവശ്യപ്പെടുന്നില്ലെങ്കിൽ കാലയളവിന്റെ ശേഷിച്ച ഭാഗത്തിന് പണം മടക്കിനൽകില്ല.",
                    "നിങ്ങൾ താമസിക്കുന്നിടത്ത് ബാധകമായ നിയമപരമായ പിൻവലിക്കൽ അല്ലെങ്കിൽ റദ്ദാക്കൽ അവകാശങ്ങൾ തുടർന്നും ബാധകമാണ്.",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                (
                    "അവകാശവാദം ഉന്നയിക്കുന്നതിന് മുമ്പുള്ള 12 മാസങ്ങളിൽ നിങ്ങൾ ഞങ്ങൾക്ക് നൽകിയ അംഗത്വ ഫീസും 50 USD-യും തമ്മിൽ ഏതാണ് കൂടുതലോ അതാണ്.",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "നിയമം ഒഴിവാക്കാനോ പരിമിതപ്പെടുത്താനോ അനുവദിക്കാത്ത ബാധ്യതയെ ഈ കരാറിലെ ഒന്നും ഒഴിവാക്കുകയോ പരിമിതപ്പെടുത്തുകയോ ചെയ്യുന്നില്ല",
                    "അനേകം രാജ്യങ്ങളിൽ അശ്രദ്ധമൂലമുള്ള മരണത്തിനോ വ്യക്തിപരമായ പരിക്കിനോ ഉള്ള ബാധ്യത, തട്ടിപ്പോ വഞ്ചനാപരമായ തെറ്റായ പ്രസ്താവനയോ, നിർബന്ധമായ ഉപഭോക്തൃ അവകാശങ്ങൾ എന്നിവ ഇതിൽ ഉൾപ്പെടുന്നു.",
                    "നിങ്ങളുടെ നിർബന്ധിത പ്രാദേശിക അവകാശങ്ങളെ ബാധിക്കില്ല.",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "നിങ്ങൾ ഉപഭോക്താവാണെങ്കിൽ",
                    "നിങ്ങൾ പതിവായി താമസിക്കുന്ന രാജ്യത്തെ നിർബന്ധിത ഉപഭോക്തൃനിയമത്തിന്റെ സംരക്ഷണമോ നിങ്ങളുടെ പ്രാദേശിക കോടതികളിൽ അവകാശവാദം ഉന്നയിക്കാനുള്ള അവകാശമോ ഇതിലൂടെ നഷ്ടപ്പെടുന്നില്ല.",
                    "ഈ കരാറിലെ നിബന്ധന നിർബന്ധിത നിയമവുമായി പൊരുത്തപ്പെടുന്നില്ലെങ്കിൽ ആ നിയമത്തിനാണ് മുൻഗണന.",
                ),
            ),
        )
        for values, document, prefix, phrases in clauses:
            value = lookup(values, document, prefix)
            for phrase in phrases:
                with self.subTest(source=prefix, phrase=phrase):
                    self.assertIn(phrase, value)

    def test_frozen_english_sources_and_unique_handbook_emergency_notice(self):
        howto = mapped("howto", HOWTO_MALAYALAM_ROWS)
        emergency = lookup(
            howto,
            "howto",
            "In an emergency, contact your local emergency services first. "
            "Go and Help is not an emergency service",
        )
        self.assertIn(
            "ആദ്യം നിങ്ങളുടെ പ്രദേശത്തെ അടിയന്തര സേവനങ്ങളുമായി ബന്ധപ്പെടുക",
            emergency,
        )
        self.assertIn(
            "Go and Help അടിയന്തര സേവനമല്ല; സംഭവസ്ഥലത്ത് ഇടപെടാനും അതിന് കഴിയില്ല",
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
