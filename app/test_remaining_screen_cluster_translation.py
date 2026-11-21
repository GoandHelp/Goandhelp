import reflex as rx

import ast
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from app.interface_i18n import CATALOGS, translate, ui_template
from app.models import LANGUAGE_OPTIONS, SETTINGS_LANGUAGE_OPTIONS
from app.scripts.audit_interface_copy import audit_paths
from app.states.auth_state import AuthState

SCREEN_PATHS = [
    Path("app/components/admin_panel.py"),
    Path("app/components/find_people_panel.py"),
    Path("app/components/paywall.py"),
    Path("app/components/saved_items.py"),
]


def fixture_expression(value: rx.Var[str]) -> str:
    return (
        str(value)
        .replace(str(AuthState.interface_text), "interfaceTextFixture")
        .replace(str(AuthState.preferred_language), "languageFixture")
    )


class RemainingScreenClusterTests(unittest.TestCase):
    def test_base_language_set_and_existing_native_variants_remain_stable(self):
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(SETTINGS_LANGUAGE_OPTIONS), 39)
        self.assertEqual(translate("fr", "Continue"), "Continuer")
        self.assertEqual(translate("ar", "Continue"), "متابعة")
        self.assertEqual(translate("de", "Continue"), "Weiter")
        self.assertEqual(translate("en", "Saved {date}"), "Saved {date}")

    def test_four_live_screen_component_roots_construct(self):
        from app.components.admin_panel import admin_panel
        from app.components.find_people_panel import find_people_panel
        from app.components.paywall import (
            membership_notices_panel,
            membership_status_card,
            paywall_modal,
        )
        from app.components.saved_items import (
            saved_requests_section,
            saved_searches_section,
        )

        components = (
            admin_panel(),
            find_people_panel(),
            paywall_modal(),
            membership_status_card(),
            membership_notices_panel(),
            saved_searches_section(),
            saved_requests_section(),
        )
        for component in components:
            self.assertTrue(component.render())

    def test_selected_source_files_have_no_unwrapped_audited_copy(self):
        findings = audit_paths(SCREEN_PATHS)
        raw = [finding for finding in findings if finding["kind"] == "raw copy"]
        self.assertEqual(
            {str(finding["source"]) for finding in raw},
            {
                "Name",
                "who are you looking for?",
                "City",
                "where in the world?",
                "Say hello",
                "optional — a line about why you're reaching out",
            },
        )

    def test_display_lookup_templates_preserve_original_member_values(self):
        node = shutil.which("node")
        self.assertIsNotNone(node)
        source = "Open the profile of {name}"
        member_name = "ليلى {title} 東京 {name}"
        name_var = rx.Var(_js_expr="memberNameFixture", _var_type=str).to(str)
        expression = fixture_expression(ui_template(source, "name", name_var))
        for locale in ("fr", "ar", "en"):
            catalog = {source: translate(locale, source)}
            payload = {
                "expression": expression,
                "catalog": catalog,
                "locale": locale,
                "name": member_name,
            }
            script = """
const fs = require('fs');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const interfaceTextFixture = payload.catalog;
const languageFixture = payload.locale;
const memberNameFixture = payload.name;
const isTrue = Boolean;
process.stdout.write(JSON.stringify(eval(payload.expression)));
"""
            result = subprocess.run(
                [node, "-e", script],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout),
                translate(locale, source).replace("{name}", member_name),
            )

    def test_checkout_and_profile_form_actions_are_display_only(self):
        paywall = ast.parse(Path("app/components/paywall.py").read_text())
        calls = {
            node.func.attr
            for node in ast.walk(paywall)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        bound_actions = {
            (keyword.value.value.id, keyword.value.attr)
            for node in ast.walk(paywall)
            if isinstance(node, ast.Call)
            for keyword in node.keywords
            if keyword.arg == "on_click"
            and isinstance(keyword.value, ast.Attribute)
            and isinstance(keyword.value.value, ast.Name)
        }
        self.assertIn(("MembershipState", "start_checkout"), bound_actions)
        self.assertIn(("MembershipState", "open_billing_portal"), bound_actions)
        self.assertIn("select_plan", calls)

        saved = ast.parse(Path("app/components/saved_items.py").read_text())
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "save_note"
                for node in ast.walk(saved)
            )
        )
        self.assertTrue(all(path.exists() for path in SCREEN_PATHS))
        self.assertGreater(len(CATALOGS), 0)


if __name__ == "__main__":
    unittest.main()
