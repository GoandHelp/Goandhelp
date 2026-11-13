import ast
import string
import unittest
from collections import Counter
from pathlib import Path

from app.components.auth_panel import MODE_CARDS, mode_card
from app.components.verify_panel import success_actions, problem_actions
from app.interface_catalog_guest_intro_verification import (
    GUEST_INTRO_VERIFICATION_CATALOGS,
    GUEST_INTRO_VERIFICATION_KEYS,
    GUEST_INTRO_VERIFICATION_ROWS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS

ROOT = Path(__file__).parent
EXPECTED_KEYS = (
    "Offer help",
    "Get help",
    "Both ways",
    "Lend a language, a car ride or a spare pair of hands to travellers nearby.",
    "Post what you need — translation, directions, luggage, paperwork — and meet a local.",
    "Trade skills as you travel and collect kindness points in your journal.",
    "Registration & profiles",
    "Trade a skill, keep a story.",
    "Create a Go and Help account to post the help you need, offer the skill you have, and keep a warm journal of every favour returned.",
    "Preview member experience",
    "Local development preview only — no account is verified and nothing is saved.",
    "Fifteen tap-first screens, no typing — then a short tour of the app.",
    "Enter the email you signed up with. Links last one hour, work once, and we never reveal whether an address is registered.",
    "Confirmation links are single-use and stored only as a hashed digest — we can never read your link back.",
)


def tree_for(relative: str) -> ast.Module:
    return ast.parse((ROOT / relative).read_text())


def function_node(
    tree: ast.AST, name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def ui_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "ui"
    ]


def ui_literal_sources(tree: ast.AST) -> set[str]:
    return {
        node.args[0].value
        for node in ui_calls(tree)
        if node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }


class GuestIntroVerificationTranslationTests(unittest.TestCase):
    def test_exact_sources_and_locale_coverage(self):
        offered = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
        expected_locales = offered | {"ha"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(tuple(GUEST_INTRO_VERIFICATION_KEYS), EXPECTED_KEYS)
        self.assertEqual(len(set(GUEST_INTRO_VERIFICATION_KEYS)), 14)
        self.assertEqual(set(GUEST_INTRO_VERIFICATION_ROWS), expected_locales)
        self.assertEqual(
            set(GUEST_INTRO_VERIFICATION_CATALOGS), expected_locales
        )
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))
        for locale, entries in GUEST_INTRO_VERIFICATION_CATALOGS.items():
            self.assertEqual(set(entries), set(EXPECTED_KEYS))
            self.assertEqual(
                len(GUEST_INTRO_VERIFICATION_ROWS[locale].split("|")), 14
            )
            for source, value in entries.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertIn(source, CATALOGS[locale])
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )
                    self.assertEqual(translate("en", source), source)
                    for marker in ("TODO", "TRANSLATE_ME", "\ufffd"):
                        self.assertNotIn(marker, value)

    def test_rows_are_literal_static_authored_strings_without_slots(self):
        tree = tree_for("interface_catalog_guest_intro_verification.py")
        rows_node = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "GUEST_INTRO_VERIFICATION_ROWS"
        )
        self.assertIsInstance(rows_node, ast.Dict)
        self.assertEqual(
            ast.literal_eval(rows_node), GUEST_INTRO_VERIFICATION_ROWS
        )
        self.assertTrue(
            all(isinstance(value, ast.Constant) for value in rows_node.values)
        )
        formatter = string.Formatter()
        for entries in GUEST_INTRO_VERIFICATION_CATALOGS.values():
            for source, value in entries.items():
                self.assertEqual(
                    Counter(
                        name
                        for _, name, _, _ in formatter.parse(source)
                        if name
                    ),
                    Counter(
                        name for _, name, _, _ in formatter.parse(value) if name
                    ),
                )
                self.assertNotIn("{", value)
                self.assertNotIn("}", value)

    def test_catalog_uses_setdefault_and_preserves_established_shared_values(
        self,
    ):
        for locale in GUEST_INTRO_VERIFICATION_CATALOGS:
            for source in EXPECTED_KEYS:
                self.assertTrue(CATALOGS[locale][source].strip())
                self.assertEqual(
                    translate(locale, source), CATALOGS[locale][source]
                )
        i18n_tree = tree_for("interface_i18n.py")
        merge = next(
            node
            for node in i18n_tree.body
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Attribute)
            and isinstance(node.iter.func.value, ast.Name)
            and node.iter.func.value.id == "GUEST_INTRO_VERIFICATION_CATALOGS"
        )
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "setdefault"
                for node in ast.walk(merge)
            )
        )
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))
        self.assertEqual(CATALOGS["es"]["Get help"], "Recibe ayuda")
        self.assertEqual(
            CATALOGS["ha"]["Offer help"],
            GUEST_INTRO_VERIFICATION_CATALOGS["ha"]["Offer help"],
        )

    def test_three_authored_mode_cards_remain_source_data_and_are_looked_up(
        self,
    ):
        auth_tree = tree_for("components/auth_panel.py")
        cards_node = next(
            node.value
            for node in auth_tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "MODE_CARDS"
        )
        cards = ast.literal_eval(cards_node)
        self.assertEqual(
            cards,
            [
                {
                    "icon": "hand-helping",
                    "title": "Offer help",
                    "blurb": "Lend a language, a car ride or a spare pair of hands to travellers nearby.",
                },
                {
                    "icon": "map-pin",
                    "title": "Get help",
                    "blurb": "Post what you need — translation, directions, luggage, paperwork — and meet a local.",
                },
                {
                    "icon": "users-round",
                    "title": "Both ways",
                    "blurb": "Trade skills as you travel and collect kindness points in your journal.",
                },
            ],
        )
        mode_card = function_node(auth_tree, "mode_card")
        dynamic_args = {
            ast.dump(call.args[0], include_attributes=False)
            for call in ui_calls(mode_card)
            if call.args
        }
        self.assertEqual(
            dynamic_args,
            {
                ast.dump(
                    ast.parse("item['title']", mode="eval").body,
                    include_attributes=False,
                ),
                ast.dump(
                    ast.parse("item['blurb']", mode="eval").body,
                    include_attributes=False,
                ),
            },
        )
        self.assertIn(
            "rx.foreach(MODE_CARDS, mode_card)",
            ast.unparse(function_node(auth_tree, "auth_panel")),
        )

    def test_auth_intro_brand_and_preview_copy_are_reactively_localized(self):
        auth_tree = tree_for("components/auth_panel.py")
        intro_sources = set(EXPECTED_KEYS[:9])
        auth_panel_literals = ui_literal_sources(
            function_node(auth_tree, "auth_panel")
        )
        preview_literals = ui_literal_sources(
            function_node(auth_tree, "local_preview_button")
        )
        self.assertTrue(
            {
                "Registration & profiles",
                "Trade a skill, keep a story.",
                EXPECTED_KEYS[8],
            }
            <= auth_panel_literals
        )
        self.assertTrue(
            {EXPECTED_KEYS[9], EXPECTED_KEYS[10]} <= preview_literals
        )
        self.assertTrue(intro_sources <= set(COMPLETE_KEYS))
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "span"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "el"
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "rx"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "Go and Help"
                for node in ast.walk(function_node(auth_tree, "auth_panel"))
            ),
            "The untranslated brand must be a literal argument to rx.el.span in auth_panel.",
        )
        self.assertIn(
            "AuthState.preferred_language",
            ast.unparse(function_node(auth_tree, "auth_panel")),
        )
        self.assertIn(
            "AuthState.interface_direction",
            ast.unparse(function_node(auth_tree, "auth_panel")),
        )

    def test_verification_explanations_are_ui_lookups_and_flows_remain_intact(
        self,
    ):
        verify_tree = tree_for("components/verify_panel.py")
        verification_sources = set(EXPECTED_KEYS[11:])
        rendered = set()
        for name in ("success_actions", "problem_actions", "verify_panel"):
            rendered |= ui_literal_sources(function_node(verify_tree, name))
        self.assertTrue(verification_sources <= rendered)
        panel = ast.unparse(function_node(verify_tree, "verify_panel"))
        actions = ast.unparse(function_node(verify_tree, "problem_actions"))
        self.assertIn("VerifyState.consume_token", panel)
        self.assertIn("resend_form('Send new link')", actions)
        self.assertIn("AuthState.preferred_language", panel)
        self.assertIn("AuthState.interface_direction", panel)

    def test_confirmation_security_copy_preserves_one_hour_single_use_and_privacy(
        self,
    ):
        email_source, digest_source = EXPECTED_KEYS[12:]
        for locale, entries in GUEST_INTRO_VERIFICATION_CATALOGS.items():
            email_help = entries[email_source]
            digest_help = entries[digest_source]
            with self.subTest(locale=locale):
                self.assertTrue(email_help)
                self.assertTrue(digest_help)
                self.assertNotEqual(email_help, email_source)
                self.assertNotEqual(digest_help, digest_source)
                self.assertNotIn("{email}", email_help)
                self.assertNotIn("{link}", digest_help)
        representative = {
            "fr": ("une heure", "qu’une fois", "ne révélons jamais"),
            "de": ("eine Stunde", "einmal", "verraten niemals"),
            "es": ("una hora", "una sola vez", "nunca revelamos"),
            "ar": ("ساعة واحدة", "مرة واحدة", "لا نكشف أبدًا"),
            "zh": ("一小时", "一次", "绝不会透露"),
            "ha": ("awa ɗaya", "sau ɗaya kawai", "ba ma bayyana"),
        }
        for locale, phrases in representative.items():
            for phrase in phrases:
                with self.subTest(locale=locale, phrase=phrase):
                    self.assertIn(
                        phrase,
                        GUEST_INTRO_VERIFICATION_CATALOGS[locale][email_source],
                    )
        for locale, phrase in {
            "fr": "usage unique",
            "de": "nur einmal",
            "es": "una vez",
            "ar": "مرة واحدة",
            "zh": "只能使用一次",
            "ha": "sau ɗaya ne kawai",
        }.items():
            self.assertIn(
                phrase, GUEST_INTRO_VERIFICATION_CATALOGS[locale][digest_source]
            )

    def test_user_email_and_registration_verification_handlers_are_not_translated_or_changed(
        self,
    ):
        auth_tree = tree_for("components/auth_panel.py")
        verify_tree = tree_for("components/verify_panel.py")
        register = ast.unparse(function_node(auth_tree, "register_form"))
        verify = ast.unparse(function_node(verify_tree, "verify_panel"))
        email_field = next(
            node
            for node in ast.walk(function_node(auth_tree, "register_fields"))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "input"
            and any(
                keyword.arg == "name"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "email"
                for keyword in node.keywords
            )
        )
        self.assertIn("AuthState.register", register)
        self.assertIn("VerifyState.consume_token", verify)
        self.assertTrue(
            any(
                keyword.arg == "on_mount"
                for call in ast.walk(function_node(verify_tree, "verify_panel"))
                if isinstance(call, ast.Call)
                for keyword in call.keywords
            )
        )
        self.assertIsNotNone(mode_card(MODE_CARDS[0]))
        self.assertIsNotNone(success_actions())
        self.assertIsNotNone(problem_actions())
        self.assertEqual(
            next(
                keyword.value.value
                for keyword in email_field.keywords
                if keyword.arg == "placeholder"
            ),
            "you@example.com",
        )
        self.assertIn("VerifyState.verified_email", verify)
        self.assertFalse(
            any(
                ast.dump(call.args[0], include_attributes=False)
                == ast.dump(
                    ast.parse("VerifyState.verified_email", mode="eval").body,
                    include_attributes=False,
                )
                for call in ui_calls(function_node(verify_tree, "verify_panel"))
                if call.args
            )
        )
        self.assertIn("lang=AuthState.preferred_language", verify)
        self.assertIn("dir=AuthState.interface_direction", verify)


if __name__ == "__main__":
    unittest.main()
