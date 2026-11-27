import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_gujarati as agreement_data
from app import policy_catalog_howto_gujarati as howto_data
from app import policy_catalog_privacy_gujarati as privacy_data
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
from app.policy_catalog_agreement_gujarati import AGREEMENT_GUJARATI_ROWS
from app.policy_catalog_howto_gujarati import HOWTO_GUJARATI_ROWS
from app.policy_catalog_privacy_gujarati import PRIVACY_GUJARATI_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_GUJARATI_ROWS", HOWTO_GUJARATI_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_GUJARATI_ROWS",
        PRIVACY_GUJARATI_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_GUJARATI_ROWS",
        AGREEMENT_GUJARATI_ROWS,
        51,
    ),
)
GUJARATI = re.compile(r"[\u0a80-\u0aff]")
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")
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


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["gu"], strict=True))


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


class GujaratiPolicyTranslationTests(unittest.TestCase):
    def test_literal_rows_are_full_native_gujarati_fields(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"gu"})
                self.assertIsInstance(rows["gu"], tuple)
                self.assertEqual(len(rows["gu"]), count)
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
                    "gu"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["gu"])
                for source, value in entries.items():
                    with self.subTest(source=source[:65]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        self.assertRegex(value, GUJARATI)
                        self.assertNotIn("\ufffd", value)
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
        howto = mapped("howto", HOWTO_GUJARATI_ROWS)
        privacy = mapped("privacy", PRIVACY_GUJARATI_ROWS)
        agreement = mapped("agreement", AGREEMENT_GUJARATI_ROWS)
        date_source = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {date_source}), 174)
        date_translation = "1 જૂન 2024ના રોજ અપડેટ થયેલ અને અમલમાં"
        self.assertEqual(
            sum(row["gu"].count(date_translation) for *_, row, _ in BATCH), 3
        )
        self.assertEqual(
            howto["How to use Go and Help"], "Go and Help નો ઉપયોગ કેવી રીતે કરવો"
        )
        self.assertEqual(howto["Reviews"], "સમીક્ષાઓ")
        self.assertEqual(howto["Emergencies"], "કટોકટી")
        self.assertEqual(
            privacy["Privacy and cookies policy"], "ગોપનીયતા અને કુકી નીતિ"
        )
        self.assertEqual(agreement["User agreement"], "વપરાશકર્તા કરાર")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("માસિક ટિકિટ", membership)
        self.assertIn("વાર્ષિક પાસ", membership)

    def test_complete_coverage_frozen_credits_and_progress(self):
        authored = POLICY_CATALOGS["gu"]
        effective = catalog("gu")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "gu"), ())
        self.assertEqual(missing_policy_sources(effective, "gu"), ())
        credits_sources = set(DOCUMENT_SOURCE_KEYS["credits"])
        for source in SOURCE_KEYS:
            with self.subTest(source=source[:65]):
                self.assertNotEqual(authored[source], source)
                self.assertNotEqual(effective[source], source)
                self.assertRegex(effective[source], GUJARATI)
                if source not in credits_sources:
                    self.assertEqual(effective[source], authored[source])
        self.assertEqual(CREDITS_ROWS["gu"][0], "આભાર અને સ્વીકાર")
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["gu"], strict=True
            )
        )
        self.assertEqual(effective["Credits"], "આભારવિધિ")
        self.assertEqual(credits["Credits"], "આભાર અને સ્વીકાર")
        for source in credits_sources - {"Credits"}:
            self.assertEqual(effective[source], credits[source])
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
        self.assertGreaterEqual(authored_total, 5350)
        self.assertGreaterEqual(effective_total, 5395)
        self.assertEqual(effective_total + missing_total, 6916)
        self.assertEqual(gaps["gu"], 0)
        self.assertGreaterEqual(sum(not gap for gap in gaps.values()), 29)

    def test_merged_safety_and_source_bound_safeguards(self):
        howto = mapped("howto", HOWTO_GUJARATI_ROWS)
        privacy = mapped("privacy", PRIVACY_GUJARATI_ROWS)
        agreement = mapped("agreement", AGREEMENT_GUJARATI_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        for source in safety_fields:
            self.assertRegex(howto[source], GUJARATI)

        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "બરાબર 3 વિકલ્પો છે, વચ્ચેનો કોઈ વિકલ્પ નથી",
                    "સાચવેલા નિર્દેશાંક તમારા ખાતામાં ખાનગી રહે છે, પરંતુ કોઈ નિર્દેશાંક ક્યાંય મોકલાતો નથી",
                    "Approximate તમારું ચોક્કસ સ્થાન ખાનગી રાખે છે",
                    "500m થી 1km દૂરનું બિંદુ",
                    "Live તમારું ચોક્કસ સ્થાન બધા વપરાશકર્તાઓ સમક્ષ મૂકે છે",
                    "તમે Refresh my position દબાવો ત્યારે તેને ફરી તાજું કરે છે",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Off મૂળભૂત પસંદગી છે",
                    "તમારા સાચવેલા નિર્દેશાંક કોઈને દેખાતા નથી",
                    "કોઈ નિર્દેશાંક મોકલાતો નથી",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "અમે તમારું સાચવેલું બિંદુ ક્યારેય પ્રકાશિત કરતા નથી",
                    "500m થી 1km દૂરનું જમીન-સુરક્ષિત સ્થિર બિંદુ",
                    "સાચવેલા નિર્દેશાંક કાઢ્યા વિના વહેંચણી તરત અટકે છે",
                ),
            ),
            (
                howto,
                "howto",
                "In an emergency, contact your local emergency services first. Go and Help is not an emergency service",
                (
                    "કટોકટીમાં પહેલાં તમારી સ્થાનિક કટોકટી સેવાઓનો સંપર્ક કરો",
                    "Go and Help કટોકટી સેવા નથી અને ઘટનાસ્થળે હસ્તક્ષેપ કરી શકતું નથી",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                ("112 ચાલે છે", "999, 911, 000 અને બીજા નંબર વપરાય છે"),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "ખાતું બનાવવા તમારી ઉંમર ઓછામાં ઓછી 16 વર્ષ હોવી જોઈએ",
                    "અમે જાણતા હોઈએ ત્યારે બાળકોની માહિતી એકત્રિત કરતા નથી",
                ),
            ),
            (
                agreement,
                "agreement",
                "You must be at least 16 years old",
                ("તમારી ઉંમર ઓછામાં ઓછી 16 વર્ષ હોવી",),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "માસિક સભ્યપદ દર મહિને અને વાર્ષિક સભ્યપદ દર વર્ષે આપમેળે નવીનીકૃત થાય છે, જ્યાં સુધી તમે રદ ન કરો",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "બિલિંગ પોર્ટલમાંથી ગમે ત્યારે રદ કરી શકો છો",
                    "તમે પહેલેથી ચૂકવેલા સમયગાળાના અંત સુધી ચાલુ રહે છે",
                    "સ્થાનિક કાયદો અન્યથા કહેતો હોય તે સિવાય",
                    "ઉપાડવા કે રદ કરવાનો કોઈ કાનૂની અધિકાર હોય તો તે લાગુ રહે છે",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent, we are not liable for indirect",
                (
                    "આ બેમાંથી જે વધુ હોય તેટલી રહેશે",
                    "દાવા પહેલાંના 12 મહિનામાં તમે ચૂકવેલી સભ્યપદ ફી અથવા 50 અમેરિકી ડૉલર",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "આ કરારમાં કંઈપણ એવી જવાબદારી દૂર કે મર્યાદિત કરતું નથી જેને કાયદો દૂર કે મર્યાદિત કરવાની મંજૂરી આપતો નથી",
                    "બેદરકારીથી થયેલા મૃત્યુ કે શારીરિક ઈજા",
                    "છેતરપિંડી અથવા કપટપૂર્ણ ખોટી રજૂઆત",
                    "ફરજિયાત ગ્રાહક અધિકારોનો સમાવેશ થાય છે",
                    "તમારા ફરજિયાત સ્થાનિક અધિકારો અપ્રભાવિત રહેશે",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "તમે ગ્રાહક હો તો",
                    "જ્યાં સામાન્ય રીતે રહો છો તે દેશના ફરજિયાત ગ્રાહક કાયદાની સુરક્ષા",
                    "સ્થાનિક અદાલતમાં દાવો કરવાનો અધિકાર",
                    "ફરજિયાત નિયમ જ પ્રાધાન્ય પામે છે",
                ),
            ),
        )
        for values, document, prefix, phrases in clauses:
            value = lookup(values, document, prefix)
            for phrase in phrases:
                with self.subTest(source=prefix, phrase=phrase):
                    self.assertIn(phrase, value)

    def test_frozen_english_sources_and_unique_emergency_notice(self):
        emergency_prefix = (
            "In an emergency, contact your local emergency services first. "
            "Go and Help is not an emergency service"
        )
        howto = mapped("howto", HOWTO_GUJARATI_ROWS)
        emergency = lookup(howto, "howto", emergency_prefix)
        self.assertIn("Go and Help કટોકટી સેવા નથી", emergency)
        self.assertIn("સ્થાનિક કટોકટી સેવાઓનો સંપર્ક કરો", emergency)
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
