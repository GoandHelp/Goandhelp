import ast
import inspect
import json
import re
import shutil
import subprocess
import unicodedata
import unittest
from collections import Counter
from string import Formatter

import reflex as rx

from app.components.paywall import (
    COFFEE_PLAN,
    DINNER_PLAN,
    annual_pass_choice,
    ticket_to_ride_choice,
    paywall_modal,
)
from app.interface_catalog_paywall import (
    BASE_PAYWALL_CODES,
    BASE_PAYWALL_KEYS,
    BASE_PAYWALL_ROWS,
    PAYWALL_CATALOGS,
    PAYWALL_KEYS,
    PAYWALL_SOURCE_COINCIDENCES,
    RU_UR_PAYWALL_CATALOGS,
)
from app.interface_catalog_profile_membership import PROFILE_MEMBERSHIP_CATALOGS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, catalog, translate, ui
from app.membership import (
    FREE_BENEFITS,
    PLAN_PRICE_CENTS,
    PLAN_PRICE_LABEL,
    PREMIUM_BENEFITS,
)
from app.models import LANGUAGE_OPTIONS, SETTINGS_LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.membership_state import MembershipState

BASE_SOURCES = (
    "Become a Premium Member",
    "Unlock multiple categories to your help request and increase your chances of receiving help",
    "TICKET",
    "Monthly Ticket",
    "Unlock all benefits, cancel anytime",
    "PASS",
    "Annual pass",
    "Close membership panel",
    "Choose the Monthly Ticket, $5 monthly",
    "Choose the Annual pass, $49 annually",
    "Select Monthly or Yearly. Both unlock all benefits",
    "Choose your membership",
    "Premium members get",
    "Free stays free",
    "Opening secure checkout…",
    "Start My Subscription",
    "Start My Subscription — continue to secure Stripe checkout",
    "Payments are handled by Stripe.",
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
EXPECTED_FRENCH = {
    "Become a Premium Member": "Devenez membre Premium",
    BASE_SOURCES[
        1
    ]: "Débloquez plusieurs catégories pour votre demande d’aide et augmentez vos chances d’obtenir de l’aide",
    "TICKET": "BILLET",
    "Monthly Ticket": "Billet mensuel",
    "Unlock all benefits, cancel anytime": "Profitez de tous les avantages, résiliez à tout moment",
    "PASS": "PASS",
    "Annual pass": "Pass annuel",
    "$5 monthly": "$5 par mois",
    "$49 annually": "$49 par an",
}


def placeholders(text: str) -> Counter[str]:
    return Counter(name for _, name, _, _ in Formatter().parse(text) if name)


def numbers(text: str) -> list[int]:
    normalized = "".join(
        str(unicodedata.decimal(char)) if char.isdecimal() else char
        for char in text
    )
    return [int(value) for value in re.findall(r"\d+", normalized)]


class PaywallTranslationTests(unittest.TestCase):
    def test_complete_offline_catalog_coverage_without_fallback_fillers(self):
        offered = {code for code, _ in SETTINGS_LANGUAGE_OPTIONS} - {"en"}
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(SETTINGS_LANGUAGE_OPTIONS), 39)
        self.assertEqual(set(BASE_PAYWALL_CODES), set(BASE_PAYWALL_ROWS))
        self.assertEqual(set(BASE_PAYWALL_CODES), offered - {"ru", "ur"})
        self.assertEqual(set(PAYWALL_CATALOGS), offered)
        self.assertEqual(set(RU_UR_PAYWALL_CATALOGS), {"ru", "ur"})
        self.assertEqual(len(PAYWALL_KEYS), 37)
        self.assertEqual(len(BASE_PAYWALL_KEYS), 18)
        self.assertEqual(BASE_PAYWALL_KEYS, BASE_SOURCES)
        self.assertTrue(set(PAYWALL_KEYS) <= set(COMPLETE_KEYS))
        self.assertNotIn("ha", PAYWALL_CATALOGS)
        self.assertNotIn("en", PAYWALL_CATALOGS)

        for locale in sorted(offered):
            values = catalog(locale)
            with self.subTest(locale=locale):
                self.assertTrue(set(PAYWALL_KEYS) <= set(values))
                for source in PAYWALL_KEYS:
                    translated = values[source]
                    self.assertTrue(translated.strip(), source)
                    self.assertEqual(
                        placeholders(source), placeholders(translated)
                    )
                    self.assertNotIn("TODO", translated)
                    self.assertNotIn("{source}", translated)
                    if translated == source:
                        self.assertIn(
                            (locale, source), PAYWALL_SOURCE_COINCIDENCES
                        )
                    else:
                        self.assertNotIn(
                            (locale, source), PAYWALL_SOURCE_COINCIDENCES
                        )
                    if "Stripe" in source:
                        self.assertIn("Stripe", translated)
                self.assertEqual(
                    translate("en", PAYWALL_KEYS[0]), PAYWALL_KEYS[0]
                )
        self.assertEqual(
            PAYWALL_SOURCE_COINCIDENCES, frozenset({("fr", "PASS")})
        )

        for locale, row in BASE_PAYWALL_ROWS.items():
            self.assertEqual(len(row), len(BASE_PAYWALL_KEYS), locale)
            self.assertEqual(tuple(PAYWALL_CATALOGS[locale]), BASE_PAYWALL_KEYS)
            self.assertEqual(
                PAYWALL_CATALOGS[locale],
                dict(zip(BASE_PAYWALL_KEYS, row, strict=True)),
            )
        for locale, entries in RU_UR_PAYWALL_CATALOGS.items():
            self.assertEqual(set(entries), set(PAYWALL_KEYS), locale)
            self.assertEqual(PAYWALL_CATALOGS[locale], entries)

    def test_catalog_merge_preserves_existing_price_and_benefit_translations(
        self,
    ):
        for locale in BASE_PAYWALL_CODES:
            with self.subTest(locale=locale):
                self.assertEqual(
                    catalog(locale)["$5 monthly"],
                    PROFILE_MEMBERSHIP_CATALOGS[locale]["$5 monthly"],
                )
                self.assertEqual(
                    catalog(locale)["$49 annually"],
                    PROFILE_MEMBERSHIP_CATALOGS[locale]["$49 annually"],
                )
                for key in (*EXPECTED_PREMIUM, *EXPECTED_FREE):
                    self.assertEqual(
                        catalog(locale)[key],
                        PROFILE_MEMBERSHIP_CATALOGS[locale][key],
                    )
        for source, expected in EXPECTED_FRENCH.items():
            self.assertEqual(translate("fr", source), expected)
        self.assertEqual(translate("unknown", PAYWALL_KEYS[0]), PAYWALL_KEYS[0])

    def test_native_price_amounts_benefit_limits_and_canonical_plan_data(self):
        self.assertEqual(tuple(PREMIUM_BENEFITS), EXPECTED_PREMIUM)
        self.assertEqual(tuple(FREE_BENEFITS), EXPECTED_FREE)
        self.assertEqual(
            PLAN_PRICE_LABEL,
            {"coffee_monthly": "$5 monthly", "dinner_annual": "$49 annually"},
        )
        self.assertEqual(
            PLAN_PRICE_CENTS, {"coffee_monthly": 500, "dinner_annual": 4900}
        )
        self.assertEqual(COFFEE_PLAN, "coffee_monthly")
        self.assertEqual(DINNER_PLAN, "dinner_annual")

        for locale in set(BASE_PAYWALL_CODES) | {"ru", "ur"}:
            entries = catalog(locale)
            with self.subTest(locale=locale):
                for source, amount in (("$5 monthly", 5), ("$49 annually", 49)):
                    self.assertEqual(numbers(entries[source]), [amount])
                    self.assertIn("$", entries[source])
                for source, amount in (
                    (EXPECTED_PREMIUM[6], 10),
                    (EXPECTED_FREE[0], 1),
                    (EXPECTED_FREE[1], 2),
                    (EXPECTED_FREE[5], 1),
                    (EXPECTED_FREE[6], 10),
                ):
                    japanese_daily_offer = (
                        locale == "ja" and source == "1 help offer a day"
                    )
                    expected_numbers = (
                        [1, 1] if japanese_daily_offer else [amount]
                    )
                    self.assertEqual(
                        numbers(entries[source]), expected_numbers, source
                    )
                    if japanese_daily_offer:
                        normalized = unicodedata.normalize(
                            "NFKC", entries[source]
                        )
                        self.assertRegex(normalized, r"1\s*日.*1\s*件")
                self.assertIn("UTC", entries[EXPECTED_FREE[5]])
                self.assertIn("UTC", entries[EXPECTED_FREE[6]])

    def test_actual_paywall_uses_reactive_prices_and_rtl_dialog_metadata(self):
        self.assertTrue(ticket_to_ride_choice().render())
        self.assertTrue(annual_pass_choice().render())
        self.assertTrue(paywall_modal().render())
        monthly_source = ast.unparse(
            ast.parse(inspect.getsource(ticket_to_ride_choice))
        )
        annual_source = ast.unparse(
            ast.parse(inspect.getsource(annual_pass_choice))
        )
        self.assertIn("ui(MembershipState.coffee_price_label)", monthly_source)
        self.assertIn("ui(MembershipState.dinner_price_label)", annual_source)
        self.assertIn("ps-[5.75rem]", monthly_source)
        self.assertIn("ps-[5.75rem]", annual_source)
        modal_source = ast.unparse(ast.parse(inspect.getsource(paywall_modal)))
        self.assertIn("dir=AuthState.interface_direction", modal_source)
        self.assertIn("lang=AuthState.preferred_language", modal_source)
        self.assertIn("text-start", modal_source)
        self.assertIn("ui('Become a Premium Member')", modal_source)
        ticket_tree = ast.parse(
            inspect.getsource(
                __import__(
                    "app.components.paywall", fromlist=["transit_ticket"]
                ).transit_ticket
            )
        )
        ticket_labels = {
            node.value
            for node in ast.walk(ticket_tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        self.assertTrue({"TICKET", "PASS"} <= ticket_labels)

    def test_compiled_ui_lookup_changes_with_live_catalog_and_price_fixtures(
        self,
    ):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required for the reactive UI check")
        expressions = {
            "title": str(ui("Become a Premium Member")),
            "description": str(
                ui(
                    "Unlock multiple categories to your help request and increase your chances of receiving help"
                )
            ),
            "monthly": str(ui(MembershipState.coffee_price_label)),
            "annual": str(ui(MembershipState.dinner_price_label)),
        }
        compiled = {
            name: expression.replace(
                str(AuthState.interface_text), "paywallInterfaceFixture"
            )
            .replace(
                str(MembershipState.coffee_price_label), "monthlyPriceFixture"
            )
            .replace(
                str(MembershipState.dinner_price_label), "annualPriceFixture"
            )
            for name, expression in expressions.items()
        }
        locales = ["en", "fr", "de", "ru", "ur", "en"]
        sources = {
            "title": "Become a Premium Member",
            "description": BASE_SOURCES[1],
            "monthly": "$5 monthly",
            "annual": "$49 annually",
        }
        payload = {
            "expressions": compiled,
            "sources": sources,
            "locales": locales,
            "catalogs": {
                locale: {
                    key: value
                    for key, value in catalog(locale).items()
                    if key in sources.values()
                }
                for locale in set(locales)
            },
        }
        script = """
const fs = require('fs');
const paywallFixture = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = value => Boolean(value);
let paywallInterfaceFixture = {};
let monthlyPriceFixture = '$5 monthly';
let annualPriceFixture = '$49 annually';
const values = [];
for (const locale of paywallFixture.locales) {
  paywallInterfaceFixture = paywallFixture.catalogs[locale];
  monthlyPriceFixture = '$5 monthly';
  annualPriceFixture = '$49 annually';
  values.push(Object.fromEntries(Object.entries(paywallFixture.expressions).map(
    ([name, expression]) => [name, eval(expression)]
  )));
}
process.stdout.write(JSON.stringify(values));
"""
        result = subprocess.run(
            [node, "-e", script],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        actual = json.loads(result.stdout)
        expected = [
            {
                name: translate(locale, source)
                for name, source in sources.items()
            }
            for locale in locales
        ]
        self.assertEqual(actual, expected)
        for dependency in (
            ui("Become a Premium Member"),
            ui(MembershipState.coffee_price_label),
            ui(MembershipState.dinner_price_label),
        ):
            metadata = dependency._get_all_var_data()
            self.assertIsNotNone(metadata)
            self.assertTrue(
                set(AuthState.interface_text._get_all_var_data().hooks)
                <= set(metadata.hooks)
            )


if __name__ == "__main__":
    unittest.main()
