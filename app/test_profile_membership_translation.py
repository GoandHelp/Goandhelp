import reflex as rx

import ast
import inspect
import json
import re
import shutil
import subprocess
import unittest
import unicodedata
from collections import Counter
from copy import deepcopy
from pathlib import Path
from string import Formatter

from app.components.membership_info import (
    benefit_line,
    comparison_column,
    membership_information_section,
)
from app.components.policy_screens import (
    policy_header,
    policy_link_card,
    policy_links_row,
    policy_screen,
    policy_section,
)
from app.interface_catalog_profile_membership import (
    PROFILE_MEMBERSHIP_KEYS,
    PROFILE_MEMBERSHIP_ROWS,
    PROFILE_MEMBERSHIP_CATALOGS,
    PROFILE_MEMBERSHIP_SOURCE_COINCIDENCES,
)
from app.interface_catalog_shared import SHARED_CATALOGS
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    catalog,
    translate,
    ui,
    ui_template,
)
from app.membership import (
    PREMIUM_BENEFITS,
    FREE_BENEFITS,
    PLAN_PRICE_CENTS,
    PLAN_INTERVAL,
    PLAN_PRICE_LABEL,
)
from app.models import LANGUAGE_OPTIONS
from app.policies import POLICY_LINKS, POLICY_DOCUMENTS, PolicySection
from app.states.auth_state import AuthState
from app.states.membership_state import MembershipState
from app.states.policy_state import PolicyState
from test_utils import run_event

EXPECTED_KEYS = (
    "Membership information",
    "Unlock more as a Premium Member",
    "Your tier",
    "Premium members",
    "Free members",
    "Always free",
    "Premium is active on this account, including the Metrics Information section on this page.",
    "See premium membership",
    "See premium membership options",
    "$5 monthly",
    "$49 annually",
    "More information",
    "How to use Go and Help",
    "Privacy and cookies policy",
    "User agreement",
    "Credits",
    "Back to your profile",
    "Section {count}",
    "This screen is part of the Go and Help app. It is written for adults everywhere and is not legal advice for any particular country.",
    "Unlimited community forum topics and comments",
    "Unlimited help offers",
    "Request multiple helpers for events",
    "Priority view help requests",
    "Metrics for increased responses",
    "Advanced Search Options",
    "10 simultaneous help requests",
    "Custom themes and modes",
    "1 help offer a day",
    "2 simultaneous help requests",
    "One-month post visibility",
    "Offer and give help anywhere, always free",
    "Read the community forum",
    "1 forum topic per UTC calendar month",
    "10 forum comments per UTC calendar month across all discussions",
    "Basic search by job category and reward",
)
EXPECTED_PREMIUM = (
    "Unlimited community forum topics and comments",
    "Unlimited help offers",
    "Request multiple helpers for events",
    "Priority view help requests",
    "Metrics for increased responses",
    "Advanced Search Options",
    "10 simultaneous help requests",
    "Custom themes and modes",
)
EXPECTED_FREE = (
    "1 help offer a day",
    "2 simultaneous help requests",
    "One-month post visibility",
    "Offer and give help anywhere, always free",
    "Read the community forum",
    "1 forum topic per UTC calendar month",
    "10 forum comments per UTC calendar month across all discussions",
    "Basic search by job category and reward",
)
EXPECTED_LINKS = [
    {"key": "howto", "label": "How to use Go and Help", "icon": "compass"},
    {
        "key": "privacy",
        "label": "Privacy and cookies policy",
        "icon": "shield-check",
    },
    {"key": "agreement", "label": "User agreement", "icon": "scroll-text"},
    {"key": "credits", "label": "Credits", "icon": "heart-handshake"},
]
EXPECTED_LOCALES = {
    "am",
    "ar",
    "bn",
    "my",
    "zh",
    "cs",
    "da",
    "nl",
    "fi",
    "fr",
    "de",
    "el",
    "gu",
    "he",
    "hi",
    "hu",
    "id",
    "it",
    "ja",
    "kn",
    "ko",
    "ml",
    "mr",
    "ne",
    "fa",
    "pl",
    "pt",
    "ro",
    "es",
    "sw",
    "sv",
    "ta",
    "te",
    "th",
    "tr",
    "vi",
}


def slots(text: str) -> Counter:
    return Counter(name for _, name, _, _ in Formatter().parse(text) if name)


def numbers(text: str) -> list[int]:
    normalized = "".join(
        str(unicodedata.decimal(char)) if char.isdecimal() else char
        for char in text
    )
    return [int(value) for value in re.findall(r"\d+", normalized)]


def parsed(function) -> str:
    return ast.unparse(ast.parse(inspect.getsource(function)))


class ProfileMembershipTranslationTests(unittest.TestCase):
    def test_independent_manifest_and_every_offered_locale(self):
        self.assertEqual(
            {code for code, _ in LANGUAGE_OPTIONS}, EXPECTED_LOCALES | {"en"}
        )
        self.assertEqual(PROFILE_MEMBERSHIP_KEYS, EXPECTED_KEYS)
        self.assertEqual(len(set(EXPECTED_KEYS)), 35)
        self.assertEqual(set(PROFILE_MEMBERSHIP_ROWS), EXPECTED_LOCALES)
        self.assertEqual(set(PROFILE_MEMBERSHIP_CATALOGS), EXPECTED_LOCALES)
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))
        self.assertNotIn("en", PROFILE_MEMBERSHIP_CATALOGS)
        self.assertNotIn("ha", PROFILE_MEMBERSHIP_CATALOGS)
        self.assertIn("ha", CATALOGS)
        for locale, entries in PROFILE_MEMBERSHIP_CATALOGS.items():
            self.assertEqual(tuple(entries), EXPECTED_KEYS)
            self.assertEqual(
                len(PROFILE_MEMBERSHIP_ROWS[locale].split("|")), 35
            )
            for source, value in entries.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertEqual(slots(value), slots(source))
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("{source}", value)
                    if value == source:
                        self.assertIn(
                            (locale, source),
                            PROFILE_MEMBERSHIP_SOURCE_COINCIDENCES,
                        )
                    if len(source) > 30:
                        self.assertNotEqual(value, source)
                    self.assertTrue(translate(locale, source).strip())
                    self.assertEqual(translate("en", source), source)
                    self.assertEqual(translate("unknown", source), source)
                    if source != "User agreement":
                        self.assertEqual(CATALOGS[locale][source], value)
        self.assertEqual(
            PROFILE_MEMBERSHIP_SOURCE_COINCIDENCES,
            frozenset({("nl", "Credits")}),
        )
        self.assertEqual(
            PROFILE_MEMBERSHIP_CATALOGS["nl"]["Credits"], "Credits"
        )

    def test_literal_rows_are_offline_full_phrases(self):
        names = {
            "app/interface_catalog_profile_membership.py": "PROFILE_MEMBERSHIP_EUROPEAN_ROWS",
            "app/interface_catalog_profile_membership_global.py": "PROFILE_MEMBERSHIP_GLOBAL_ROWS",
            "app/interface_catalog_profile_membership_asian.py": "PROFILE_MEMBERSHIP_ASIAN_ROWS",
        }
        literal_rows = {}
        for path, name in names.items():
            tree = ast.parse(Path(path).read_text())
            definition = next(
                node
                for node in tree.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == name
            )
            self.assertIsInstance(definition.value, ast.Dict)
            self.assertTrue(
                all(
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    for value in definition.value.values
                )
            )
            group = ast.literal_eval(definition.value)
            self.assertFalse(set(group) & set(literal_rows))
            literal_rows.update(group)
            imported_roots = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(
                        alias.name.split(".")[0] for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])
            for forbidden in (
                "httpx",
                "requests",
                "urllib",
                "openai",
                "translate",
                "subprocess",
            ):
                self.assertNotIn(forbidden, imported_roots, path)
        self.assertEqual(literal_rows, PROFILE_MEMBERSHIP_ROWS)
        for value in PROFILE_MEMBERSHIP_CATALOGS["am"].values():
            self.assertTrue(
                any("\u1200" <= char <= "\u137f" for char in value), value
            )
            self.assertFalse(
                any("\u10a0" <= char <= "\u10ff" for char in value), value
            )

    def test_plan_amounts_allowances_and_semantic_periods(self):
        for locale, entries in PROFILE_MEMBERSHIP_CATALOGS.items():
            for key, amount in (("$5 monthly", 5), ("$49 annually", 49)):
                self.assertEqual(numbers(entries[key]), [amount], locale)
                self.assertIn(f"${amount}", entries[key], locale)
            for source, amount in (
                (EXPECTED_PREMIUM[6], 10),
                (EXPECTED_FREE[0], 1),
                (EXPECTED_FREE[1], 2),
                (EXPECTED_FREE[5], 1),
                (EXPECTED_FREE[6], 10),
            ):
                if locale == "ja" and source == "1 help offer a day":
                    self.assertEqual(
                        numbers(entries[source]), [1, 1], (locale, source)
                    )
                    self.assertIn("1 日に 1 件", entries[source])
                else:
                    self.assertEqual(
                        numbers(entries[source]), [amount], (locale, source)
                    )
            for source in EXPECTED_FREE[5:7]:
                self.assertIn("UTC", entries[source], locale)
        semantic_terms = {
            "fr": (
                "mois civil",
                "toutes discussions",
                "par jour",
                "par mois",
                "par an",
                "illimité",
            ),
            "ar": (
                "شهر تقويمي",
                "جميع المناقشات",
                "يوميًا",
                "شهريًا",
                "سنويًا",
                "غير محدود",
            ),
            "ja": ("暦月", "すべての議論", "1 日", "月額", "年額", "無制限"),
            "id": (
                "bulan kalender",
                "seluruh diskusi",
                "per hari",
                "per bulan",
                "per tahun",
                "tanpa batas",
            ),
            "am": (
                "የቀን መቁጠሪያ ወር",
                "በሁሉም ውይይቶች",
                "በቀን",
                "በወር",
                "በዓመት",
                "ያልተገደቡ",
            ),
        }
        for locale, (
            calendar,
            all_discussions,
            daily,
            monthly,
            annual,
            unlimited,
        ) in semantic_terms.items():
            entries = PROFILE_MEMBERSHIP_CATALOGS[locale]
            for source in EXPECTED_FREE[5:7]:
                self.assertIn(calendar, entries[source])
            self.assertIn(all_discussions, entries[EXPECTED_FREE[6]])
            self.assertIn(daily, entries[EXPECTED_FREE[0]])
            self.assertIn(monthly, entries["$5 monthly"])
            self.assertIn(annual, entries["$49 annually"])
            for source in EXPECTED_PREMIUM[:2]:
                self.assertIn(unlimited, entries[source])
        footer_terms = {
            "fr": (
                "adultes",
                "monde entier",
                "ne constitue pas",
                "juridique",
                "pays",
            ),
            "ar": ("للبالغين", "كل مكان", "ولا", "قانونية", "بلد"),
            "ja": ("世界中", "成人", "法的助言ではありません", "特定の国"),
            "id": (
                "orang dewasa",
                "di mana pun",
                "bukan nasihat hukum",
                "negara tertentu",
            ),
            "am": ("አዋቂዎች", "በሁሉም ቦታ", "የሕግ ምክር አይደለም", "አገር"),
        }
        for locale, terms in footer_terms.items():
            for term in terms:
                self.assertIn(
                    term, PROFILE_MEMBERSHIP_CATALOGS[locale][EXPECTED_KEYS[18]]
                )

    def test_canonical_data_and_existing_shared_precedence(self):
        self.assertEqual(tuple(PREMIUM_BENEFITS), EXPECTED_PREMIUM)
        self.assertEqual(tuple(FREE_BENEFITS), EXPECTED_FREE)
        self.assertEqual(
            PLAN_PRICE_CENTS, {"coffee_monthly": 500, "dinner_annual": 4900}
        )
        self.assertEqual(
            PLAN_INTERVAL, {"coffee_monthly": "month", "dinner_annual": "year"}
        )
        self.assertEqual(
            PLAN_PRICE_LABEL,
            {"coffee_monthly": "$5 monthly", "dinner_annual": "$49 annually"},
        )
        self.assertEqual(POLICY_LINKS, EXPECTED_LINKS)
        for locale in EXPECTED_LOCALES:
            self.assertEqual(
                CATALOGS[locale]["Back"], translate(locale, "Back")
            )
            self.assertNotEqual(translate(locale, "Back"), "Back")
            if "User agreement" in SHARED_CATALOGS[locale]:
                self.assertEqual(
                    CATALOGS[locale]["User agreement"],
                    SHARED_CATALOGS[locale]["User agreement"],
                )
        manifest = Path("app/interface_i18n.py").read_text()
        tree = ast.parse(manifest)
        merge = next(
            node
            for node in tree.body
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Tuple)
            and any(
                isinstance(item, ast.Name)
                and item.id == "PROFILE_MEMBERSHIP_CATALOGS"
                for item in node.iter.elts
            )
        )
        self.assertIn(
            "CATALOGS[_language].setdefault(_key, _value)", ast.unparse(merge)
        )
        self.assertNotIn(".update(", ast.unparse(merge))
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(ui),
        )
        self.assertIn(
            "return catalog(self.preferred_language)",
            Path("app/states/auth_state.py").read_text(),
        )

    def test_actual_components_render_and_only_owned_metadata_is_localized(
        self,
    ):
        components = (
            membership_information_section(),
            policy_links_row(),
            policy_screen(),
            policy_header(),
            policy_link_card(rx.Var.create(EXPECTED_LINKS[0])),
            policy_section(
                rx.Var.create(POLICY_DOCUMENTS["credits"]["sections"][0]).to(
                    PolicySection
                ),
                rx.Var.create(0),
            ),
        )
        for component in components:
            self.assertTrue(component.render())
        membership = str(components[0])
        for key in (
            EXPECTED_KEYS[0],
            EXPECTED_KEYS[1],
            EXPECTED_KEYS[2],
            EXPECTED_KEYS[3],
            EXPECTED_KEYS[4],
            EXPECTED_KEYS[5],
            EXPECTED_KEYS[6],
            EXPECTED_KEYS[7],
            EXPECTED_KEYS[8],
            EXPECTED_KEYS[10],
        ):
            self.assertIn(str(ui(key)), membership)
        self.assertIn(str(ui(MembershipState.coffee_price_label)), membership)
        self.assertIn(str(ui("More information")), str(components[1]))
        self.assertIn(str(ui(EXPECTED_KEYS[18])), str(components[2]))
        self.assertIn(str(ui("Back to your profile")), str(components[2]))
        self.assertIn(str(ui("Back")), str(components[3]))
        self.assertIn("ui(line)", parsed(benefit_line))
        self.assertIn("ui(title)", parsed(comparison_column))
        self.assertIn("rx.foreach(lines, renderer)", parsed(comparison_column))
        card = parsed(policy_link_card)
        self.assertIn("ui(item['label'])", card)
        self.assertIn("aria_label=ui(item['label'])", card)
        self.assertIn("PolicyState.open_policy(item['key'])", card)
        self.assertIn("PolicyState.close_policy", parsed(policy_header))
        self.assertIn("PolicyState.close_policy", parsed(policy_screen))
        self.assertIn(
            "ui_template('Section {count}', 'count', (index + 1).to_string())",
            parsed(policy_section),
        )
        membership_source = ast.parse(
            inspect.getsource(
                __import__(
                    "app.components.membership_info", fromlist=["benefit_line"]
                )
            )
        )
        policy_source = ast.parse(
            inspect.getsource(
                __import__(
                    "app.components.policy_screens", fromlist=["policy_section"]
                )
            )
        )
        for tree in (membership_source, policy_source):
            for call in ast.walk(tree):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id in {"ui", "ui_template"}
                ):
                    first = ast.unparse(call.args[0])
                    self.assertTrue(
                        isinstance(call.args[0], ast.Constant)
                        or first
                        in {
                            "line",
                            "title",
                            "MembershipState.coffee_price_label",
                            "item['label']",
                        },
                        first,
                    )
        for field in ("title", "subtitle", "updated", "notice"):
            self.assertIn(f"PolicyState.{field}", parsed(policy_screen))
            self.assertNotIn(f"ui(PolicyState.{field})", parsed(policy_screen))
        self.assertNotIn("ui(section['heading'])", parsed(policy_section))
        policy_state_source = Path("app/states/policy_state.py").read_text()
        self.assertNotIn("interface_i18n", policy_state_source)
        for field in ("title", "subtitle", "updated", "notice"):
            self.assertIn(
                f"self.{field} = document['{field}']",
                ast.unparse(ast.parse(policy_state_source)),
            )
        self.assertIn(
            "self.sections = list(document['sections'])",
            ast.unparse(ast.parse(policy_state_source)),
        )
        profile_tree = ast.parse(
            Path("app/components/profile_tabs.py").read_text()
        )
        calls = {
            node.func.id
            for node in ast.walk(profile_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("membership_information_section", calls)
        self.assertIn("policy_links_row", calls)
        self.assertIn("md:grid-cols-2", membership)
        self.assertIn("text-start", membership)
        self.assertIn("break-words", membership)

    def test_compiled_reactive_expressions_in_node_for_all_37_languages(self):
        node = shutil.which("node")
        self.assertIsNotNone(
            node,
            "Node is required to evaluate the actual compiled UI expressions",
        )
        expression_cases = [
            (str(ui(key)), key, "") for key in (*EXPECTED_KEYS, "Back")
        ]
        expression_cases.extend(
            (
                str(
                    ui(rx.Var(_js_expr="benefitSource", _var_type=str).to(str))
                ),
                source,
                source,
            )
            for source in (*EXPECTED_PREMIUM, *EXPECTED_FREE)
        )
        expression_cases.append(
            (str(ui(MembershipState.coffee_price_label)), "$5 monthly", "")
        )
        expression_cases.append(
            (
                str(
                    rx.Var.create(
                        f"{ui(MembershipState.coffee_price_label)} / {ui('$49 annually')}"
                    )
                ),
                "price",
                "",
            )
        )
        for count in (1, 2, 10, 123):
            expression_cases.append(
                (
                    str(
                        ui_template(
                            "Section {count}",
                            "count",
                            rx.Var.create(count).to_string(),
                        )
                    ),
                    "Section {count}",
                    str(count),
                )
            )
        cases = []
        for locale in ("en", *sorted(EXPECTED_LOCALES)):
            for expression, key, value in expression_cases:
                compiled = expression.replace(
                    str(AuthState.interface_text), "interfaceText"
                ).replace(
                    str(MembershipState.coffee_price_label), "priceSource"
                )
                expected = (
                    f"{translate(locale, '$5 monthly')} / {translate(locale, '$49 annually')}"
                    if key == "price"
                    else translate(locale, key)
                )
                if key == "Section {count}" and value:
                    expected = expected.replace("{count}", value)
                cases.append(
                    {
                        "locale": locale,
                        "expression": compiled,
                        "benefit": value,
                        "expected": expected,
                    }
                )
        payload = {
            "catalogs": {
                locale: {
                    key: value
                    for key, value in catalog(locale).items()
                    if key in (*EXPECTED_KEYS, "Back")
                }
                for locale in ("en", *sorted(EXPECTED_LOCALES))
            },
            "cases": cases,
            "priceSource": "$5 monthly",
        }
        script = """
const fs = require('fs');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = value => Boolean(value);
const priceSource = payload.priceSource;
const results = payload.cases.map(item => {
  const interfaceText = payload.catalogs[item.locale];
  const benefitSource = item.benefit;
  return eval(item.expression);
});
process.stdout.write(JSON.stringify(results));
"""
        result = subprocess.run(
            [node, "-e", script],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        self.assertEqual(
            json.loads(result.stdout), [case["expected"] for case in cases]
        )
        metadata = ui(MembershipState.coffee_price_label)._get_all_var_data()
        self.assertIsNotNone(metadata)
        for dependency in (
            ui("Membership information"),
            MembershipState.coffee_price_label,
        ):
            data = dependency._get_all_var_data()
            self.assertIsNotNone(data)
            self.assertTrue(set(data.hooks) <= set(metadata.hooks))


class ProfileMembershipReactiveStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_open_panels_switch_language_without_changing_source_data(
        self,
    ):
        membership = MembershipState(_reflex_internal_init=True)
        auth = await membership.get_state(AuthState)
        policy = await membership.get_state(PolicyState)
        documents = deepcopy(POLICY_DOCUMENTS)
        original_language = auth.preferred_language
        try:
            for tier, premium in (
                ("free", False),
                ("coffee_monthly", True),
                ("dinner_annual", True),
            ):
                membership.tier = tier
                membership.is_premium = premium
                for link in EXPECTED_LINKS:
                    await run_event(policy.open_policy, link["key"])
                    snapshot = (
                        membership.tier,
                        membership.is_premium,
                        deepcopy(membership.free_benefits),
                        deepcopy(membership.premium_benefits),
                        membership.coffee_price_label,
                        membership.dinner_price_label,
                        policy.open_key,
                        policy.title,
                        policy.subtitle,
                        policy.updated,
                        policy.notice,
                        deepcopy(policy.sections),
                    )
                    for locale in ("fr", "ar", "en", "fr"):
                        auth.preferred_language = locale
                        current = auth.interface_text
                        for key in (*EXPECTED_KEYS, "Back"):
                            self.assertEqual(
                                current.get(key, key), translate(locale, key)
                            )
                        self.assertEqual(
                            (
                                membership.tier,
                                membership.is_premium,
                                membership.free_benefits,
                                membership.premium_benefits,
                                membership.coffee_price_label,
                                membership.dinner_price_label,
                                policy.open_key,
                                policy.title,
                                policy.subtitle,
                                policy.updated,
                                policy.notice,
                                policy.sections,
                            ),
                            snapshot,
                        )
            self.assertEqual(POLICY_DOCUMENTS, documents)
            self.assertEqual(POLICY_LINKS, EXPECTED_LINKS)
        finally:
            auth.preferred_language = original_language
            await run_event(policy.close_policy)


if __name__ == "__main__":
    unittest.main()
