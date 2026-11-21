import reflex as rx

import ast
import json
import re
import shutil
import subprocess
import unittest
from collections import Counter
from pathlib import Path
from string import Formatter

from app.interface_catalog_remaining_ui_entry import (
    REMAINING_ENTRY_CATALOGS,
    REMAINING_ENTRY_KEYS,
    REMAINING_ENTRY_ROWS,
)
from app.interface_catalog_remaining_ui_discovery import (
    REMAINING_DISCOVERY_CATALOGS,
    REMAINING_DISCOVERY_KEYS,
    REMAINING_DISCOVERY_ROWS,
)
from app.interface_catalog_remaining_ui_ledger import (
    REMAINING_LEDGER_CATALOGS,
    REMAINING_LEDGER_KEYS,
    REMAINING_LEDGER_ROWS,
)
from app.interface_catalog_remaining_ui_counts import (
    REMAINING_COUNT_CATALOGS,
    REMAINING_COUNT_KEYS,
    REMAINING_COUNT_ROWS,
)
from app.interface_catalog_remaining_ui_stars import (
    REMAINING_STARS_CATALOGS,
    REMAINING_STARS_KEYS,
    REMAINING_STARS_ROWS,
)
from app.interface_catalog_remaining_ui_actions import (
    REMAINING_ACTIONS_CATALOGS,
    REMAINING_ACTIONS_KEYS,
    REMAINING_ACTIONS_ROWS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template,
    ui_template_multi,
)
from app.models import LANGUAGE_OPTIONS, SETTINGS_LANGUAGE_OPTIONS
from app.scripts.audit_interface_copy import audit_paths, analyze_source
from app.states.auth_state import AuthState

GROUPS = (
    (
        "entry",
        REMAINING_ENTRY_KEYS,
        REMAINING_ENTRY_ROWS,
        REMAINING_ENTRY_CATALOGS,
    ),
    (
        "discovery",
        REMAINING_DISCOVERY_KEYS,
        REMAINING_DISCOVERY_ROWS,
        REMAINING_DISCOVERY_CATALOGS,
    ),
    (
        "ledger",
        REMAINING_LEDGER_KEYS,
        REMAINING_LEDGER_ROWS,
        REMAINING_LEDGER_CATALOGS,
    ),
    (
        "counts",
        REMAINING_COUNT_KEYS,
        REMAINING_COUNT_ROWS,
        REMAINING_COUNT_CATALOGS,
    ),
    (
        "stars",
        REMAINING_STARS_KEYS,
        REMAINING_STARS_ROWS,
        REMAINING_STARS_CATALOGS,
    ),
    (
        "actions",
        REMAINING_ACTIONS_KEYS,
        REMAINING_ACTIONS_ROWS,
        REMAINING_ACTIONS_CATALOGS,
    ),
)
EXPECTED_KEYS = (
    "Loading Go and Help…",
    "Loading Go and Help",
    "Opening the map…",
    "Confirming your payment with Stripe…",
    "Premium Membership",
    "We couldn't confirm that membership",
    "Open this page from your Stripe checkout to confirm a membership.",
    "Back to the map",
    "Go and Help main navigation",
    "New activity",
    "Choose whether to give help or get help",
    "Give — choose a job and give your help to a neighbour who asked for it.",
    "Get — find a person you can get help from, and open their profile.",
    "A Go and Help neighbour you could get help from",
    "Open the profile of {name}",
    "No helpers nearby",
    "1 helper nearby",
    "{count} helpers nearby",
    "No helpers to show yet.",
    "Move the map to find more neighbours in view.",
    "Waiting for the map to locate visible neighbours.",
    "Skills and knowledge",
    "No results match your filters",
    "Joined {date}",
    "About {name}",
    "Open the details for {title}",
    "Review from {name} for {title}",
    "{rating} · {count} review",
    "{rating} · {count} reviews",
    "Help posts written",
    "Still open",
    "Offers you sent",
    "Offers accepted",
    "Times you helped",
    "Times you were helped",
    "Messages sent",
    "Reviews received",
    "Rating as a helper",
    "Rating as a traveller",
    "No reviews yet — your first completed task starts the story.",
    "Your kindness ledger",
    "Everything you've posted, offered and completed on Go and Help.",
    "Recent journal entries",
    "Your journal is still blank.",
    "Once help posts start flowing, they'll be listed here.",
    "{count} kindness point",
    "{count} kindness points",
    "with {name}",
    "{count} review",
    "{count} reviews",
    "{score} out of 5 stars",
    "Sending request…",
    "Send contact request",
    "Turn off",
)


def slots(value: str) -> Counter[str]:
    return Counter(name for _, name, _, _ in Formatter().parse(value) if name)


def fixture_expression(value: rx.Var[str]) -> str:
    return (
        str(value)
        .replace(str(AuthState.interface_text), "interfaceTextFixture")
        .replace(str(AuthState.preferred_language), "languageFixture")
    )


class RemainingVisibleTranslationTests(unittest.TestCase):
    def test_exact_bounded_manifest_and_all_base_locales(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(SETTINGS_LANGUAGE_OPTIONS), 39)
        self.assertEqual(
            tuple(key for _, keys, _, _ in GROUPS for key in keys),
            EXPECTED_KEYS,
        )
        self.assertEqual(len(set(EXPECTED_KEYS)), 54)
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))
        for group, keys, rows, catalogs in GROUPS:
            self.assertEqual(set(rows), offered, group)
            self.assertEqual(set(catalogs), offered, group)
            self.assertNotIn("ru", rows)
            self.assertNotIn("ur", rows)
            for locale, entries in catalogs.items():
                self.assertEqual(tuple(entries), keys, (group, locale))
                self.assertEqual(len(rows[locale].split("|")), len(keys))
                for source, value in entries.items():
                    with self.subTest(
                        group=group, locale=locale, source=source
                    ):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value.casefold(), source.casefold())
                        self.assertEqual(slots(value), slots(source))
                        self.assertIn(source, CATALOGS[locale])
                        self.assertTrue(CATALOGS[locale][source].strip())
                        self.assertEqual(
                            slots(CATALOGS[locale][source]), slots(source)
                        )
                        self.assertEqual(translate("en", source), source)

    def test_literal_offline_rows_and_no_provider_dependencies(self):
        for group, _, rows, _ in GROUPS:
            path = Path(f"app/interface_catalog_remaining_ui_{group}.py")
            tree = ast.parse(path.read_text())
            row_symbol = {
                "counts": "REMAINING_COUNT_ROWS",
                "actions": "REMAINING_ACTIONS_ROWS",
            }.get(group, f"REMAINING_{group.upper()}_ROWS")
            definition = next(
                node
                for node in tree.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == row_symbol
            )
            self.assertEqual(ast.literal_eval(definition.value), rows)
            self.assertIsInstance(definition.value, ast.Dict)
            self.assertTrue(
                all(
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    for value in definition.value.values
                )
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(
                        {alias.name.split(".")[0] for alias in node.names}
                        & {
                            "httpx",
                            "requests",
                            "urllib",
                            "openai",
                            "subprocess",
                        }
                    )
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(
                        node.module,
                        {"app.interface_i18n", "app.states.auth_state"},
                    )

    def test_prior_native_variants_are_not_overwritten(self):
        preserved = {
            ("fr", "Continue"): "Continuer",
            ("ar", "Continue"): "متابعة",
            ("de", "Continue"): "Weiter",
            ("fr", "Show original language"): "Afficher la langue d’origine",
            ("de", "Show original language"): "Originalsprache anzeigen",
        }
        for (locale, source), expected in preserved.items():
            self.assertEqual(translate(locale, source), expected)
        tree = ast.parse(Path("app/interface_i18n.py").read_text())
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "setdefault"
                for node in ast.walk(tree)
            )
        )

    def test_actual_changed_component_construction(self):
        from app.app import membership_result_card, session_skeleton, map_page
        from app.components.discover_panel import (
            discovery_controls,
            helper_list,
            detail_rating,
        )
        from app.components.profile_tabs import activity_tab
        from app.components.reviews_section import community_reviews_section
        from app.components.bottom_nav import bottom_nav
        from app.components.notification_badge import activity_dot
        from app.components.member_map import member_group_sheet

        for component in (
            membership_result_card(),
            session_skeleton(),
            map_page(),
            discovery_controls(),
            helper_list(),
            activity_tab(),
            community_reviews_section(),
            bottom_nav(),
            member_group_sheet(),
            detail_rating(rx.Var.create(4.5), rx.Var.create(2)),
            activity_dot(rx.Var.create(1)),
        ):
            self.assertTrue(component.render())

    def test_new_owned_literals_and_frames_are_lookup_backed(self):
        paths = sorted(Path("app/components").glob("*.py")) + [
            Path("app/app.py")
        ]
        for finding in audit_paths(paths):
            self.assertNotIn(
                finding["source"],
                EXPECTED_KEYS,
                f"New owned source remains raw or incomplete: {finding}",
            )
        expected_calls = {
            "app/components/discover_panel.py": {
                "Open the profile of {name}",
                "Joined {date}",
                "About {name}",
                "{count} helpers nearby",
            },
            "app/components/reviews_section.py": {
                "Review from {name} for {title}"
            },
            "app/components/member_map.py": {"Open the details for {title}"},
            "app/components/profile_tabs.py": {"with {name}"},
        }
        for path, expected in expected_calls.items():
            tree = ast.parse(Path(path).read_text())
            calls = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"ui_template", "ui_template_multi"}
            ]
            sources = {
                arg.value
                for node in calls
                for arg in node.args[:1]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            }
            self.assertTrue(expected <= sources, (path, expected - sources))
        self.assertEqual(
            analyze_source(
                'rx.el.button("New activity", aria_label="New activity")'
            )[0]["kind"],
            "raw copy",
        )
        self.assertEqual(
            analyze_source(
                'rx.el.button(ui("New activity"), aria_label=ui("New activity"))'
            ),
            [],
        )
        discovery = Path("app/components/discover_panel.py").read_text()
        for original in (
            'helper["name"]',
            'helper["headline"]',
            'helper["city"]',
            'DiscoveryState.selected_post["description"]',
        ):
            self.assertIn(original, discovery)
        self.assertIn("DiscoveryState.set_map_mode(value)", discovery)
        self.assertIn("DiscoveryState.set_view_mode(value)", discovery)
        help_post_tree = ast.parse(
            Path("app/components/help_post_panel.py").read_text()
        )
        for field, example in (("city", "Porto"), ("country", "Portugal")):
            inputs = [
                node
                for node in ast.walk(help_post_tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "input"
                and any(
                    keyword.arg == "name"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == field
                    for keyword in node.keywords
                )
            ]
            self.assertEqual(len(inputs), 1, field)
            placeholder = next(
                keyword.value
                for keyword in inputs[0].keywords
                if keyword.arg == "placeholder"
            )
            self.assertIsInstance(placeholder, ast.Constant)
            self.assertEqual(placeholder.value, example)
        self.assertEqual(
            analyze_source('rx.el.input(name="city", placeholder="Porto")'),
            [],
        )
        self.assertEqual(
            analyze_source(
                'rx.el.input(name="country", placeholder="Portugal")'
            ),
            [],
        )

    def test_audit_reduction_is_bounded_not_global_certification(self):
        findings = audit_paths(
            sorted(Path("app/components").glob("*.py")) + [Path("app/app.py")]
        )
        self.assertLess(len(findings), 409)
        self.assertGreater(len(findings), 0)
        counts = Counter(str(item["kind"]) for item in findings)
        print(
            f"Remaining UI audit: {len(findings)} candidates (supplied before: 409); kinds: {dict(counts)}"
        )
        self.assertFalse(
            any(
                item["path"] == "app/app.py" and item["kind"] == "raw copy"
                for item in findings
            )
        )

    def test_actual_node_lookup_and_literal_template_substitution(self):
        node = shutil.which("node")
        self.assertIsNotNone(
            node, "Node is required to validate compiled expressions"
        )
        source_var = rx.Var(_js_expr="sourceFixture", _var_type=str).to(str)
        name_var = rx.Var(_js_expr="memberNameFixture", _var_type=str).to(str)
        title_var = rx.Var(_js_expr="memberTitleFixture", _var_type=str).to(str)
        date_var = rx.Var(_js_expr="dateFixture", _var_type=str).to(str)
        count_var = rx.Var(_js_expr="countFixture", _var_type=int).to(int)
        expressions = {
            "lookup": fixture_expression(ui(source_var)),
            "profile": fixture_expression(
                ui_template("Open the profile of {name}", "name", name_var)
            ),
            "review": fixture_expression(
                ui_template_multi(
                    "Review from {name} for {title}",
                    {"name": name_var, "title": title_var},
                )
            ),
            "date": fixture_expression(
                ui_template("Joined {date}", "date", date_var)
            ),
            "helpers": fixture_expression(
                rx.cond(
                    count_var == 0,
                    ui("No helpers nearby"),
                    rx.cond(
                        count_var == 1,
                        ui("1 helper nearby"),
                        ui_template(
                            "{count} helpers nearby",
                            "count",
                            count_var.to_string(),
                        ),
                    ),
                )
            ),
        }
        member_name = "ليلى {title} 東京 {name}"
        member_title = "Repair {name} — الحديقة"
        original_date = "31–12–2026 {name}"
        for locale in ("fr", "ar", "en"):
            selected = {
                key: CATALOGS.get(locale, {}).get(key, key)
                for key in EXPECTED_KEYS
            }
            cases = [
                {
                    "kind": "lookup",
                    "source": key,
                    "count": 0,
                    "expected": translate(locale, key),
                }
                for key in EXPECTED_KEYS
            ]
            cases.extend(
                [
                    {
                        "kind": "profile",
                        "source": "",
                        "count": 0,
                        "expected": translate(
                            locale, "Open the profile of {name}"
                        ).replace("{name}", member_name),
                    },
                    {
                        "kind": "review",
                        "source": "",
                        "count": 0,
                        "expected": re.sub(
                            r"\{(name|title)\}",
                            lambda match: {
                                "name": member_name,
                                "title": member_title,
                            }[match[1]],
                            translate(locale, "Review from {name} for {title}"),
                        ),
                    },
                    {
                        "kind": "date",
                        "source": "",
                        "count": 0,
                        "expected": translate(locale, "Joined {date}").replace(
                            "{date}", original_date
                        ),
                    },
                ]
            )
            for count in (0, 1, 2, 11):
                source = (
                    "No helpers nearby"
                    if count == 0
                    else "1 helper nearby"
                    if count == 1
                    else "{count} helpers nearby"
                )
                cases.append(
                    {
                        "kind": "helpers",
                        "source": "",
                        "count": count,
                        "expected": translate(locale, source).replace(
                            "{count}", str(count)
                        ),
                    }
                )
            payload = {
                "expressions": expressions,
                "catalog": selected,
                "locale": locale,
                "name": member_name,
                "title": member_title,
                "date": original_date,
                "cases": cases,
            }
            script = """
const fs = require('fs');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = Boolean;
const interfaceTextFixture = payload.catalog;
const languageFixture = payload.locale;
const memberNameFixture = payload.name;
const memberTitleFixture = payload.title;
const dateFixture = payload.date;
const results = payload.cases.map(item => {
  const sourceFixture = item.source;
  const countFixture = item.count;
  return eval(payload.expressions[item.kind]);
});
process.stdout.write(JSON.stringify(results));
"""
            result = subprocess.run(
                [node, "-e", script],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=45,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout),
                [item["expected"] for item in cases],
                locale,
            )


if __name__ == "__main__":
    unittest.main()
