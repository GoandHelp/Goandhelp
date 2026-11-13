import ast
import unittest
from pathlib import Path

from app.components.auth_panel import (
    LEGAL_SECTIONS,
    legal_dialog,
    legal_section,
)
from app.interface_catalog_legal import LEGAL_CATALOGS, LEGAL_KEYS, LEGAL_ROWS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS
from app.models import LANGUAGE_OPTIONS

ROOT = Path(__file__).parent


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

    def test_catalog_is_static_and_exact_per_present_locale(self):
        tree = ast.parse((ROOT / "interface_catalog_legal.py").read_text())
        rows = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and getattr(node.target, "id", "") == "LEGAL_ROWS"
        )
        self.assertEqual(ast.literal_eval(rows), LEGAL_ROWS)
        for locale, row in LEGAL_ROWS.items():
            with self.subTest(locale=locale):
                self.assertEqual(len(row), 7)
                self.assertEqual(set(LEGAL_CATALOGS[locale]), set(LEGAL_KEYS))
                self.assertTrue(
                    all(
                        value.strip()
                        for value in LEGAL_CATALOGS[locale].values()
                    )
                )
                self.assertTrue(
                    all(
                        value != source
                        for source, value in zip(LEGAL_KEYS, row, strict=True)
                    )
                )

    def test_privacy_and_cookie_semantics(self):
        for locale in ("es", "fr", "de", "ar", "zh", "hi", "ja", "ha"):
            privacy, cookies = (
                LEGAL_CATALOGS[locale][LEGAL_KEYS[5:7][0]],
                LEGAL_CATALOGS[locale][LEGAL_KEYS[6]],
            )
            with self.subTest(locale=locale):
                self.assertTrue(privacy and cookies)
                self.assertIn("16", privacy)
                self.assertTrue(cookies.strip())

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

    def test_existing_locale_rows_are_registered_in_the_shared_catalog(self):
        for locale, entries in LEGAL_CATALOGS.items():
            self.assertTrue(set(entries) <= set(CATALOGS[locale]))
            self.assertTrue(set(entries) <= set(COMPLETE_KEYS))
