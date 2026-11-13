import ast
import string
import unittest
from collections import Counter
from pathlib import Path

from app.components.block_dialog import block_dialog, block_member_button
from app.components.profile_tabs import (
    blocked_member_row,
    blocked_members_section,
)
from app.interface_catalog_block import BLOCK_CATALOGS, BLOCK_KEYS, BLOCK_ROWS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.states.block_state import (
    BLOCK_SUCCESS_COPY,
    UNBLOCK_SUCCESS_COPY,
    BlockState,
)


BLOCK_STATE_PATH = Path("app/states/block_state.py")
DIALOG_PATH = Path("app/components/block_dialog.py")
PROFILE_PATH = Path("app/components/profile_tabs.py")
EXPECTED_BLOCK_KEYS = (
    "Block",
    "Block this member privately",
    "Block privately — they are never told",
    "Their posts, discussions and comments will be hidden from you.",
    "Neither of you can send contact requests or messages while the block is in place.",
    "They are not notified and are never told that you blocked them.",
    "You can unblock them later from Profile › Blocked members.",
    "Blocking…",
    "Confirm block",
    "Safety",
    "Blocking is private and takes effect straight away.",
    "Close block confirmation",
    "Confirm blocking this member",
    "Block {name}?",
    "Block this member?",
    "Private list — only you can see this.",
    "1 blocked member · private list — only you can see this.",
    "{count} blocked members · private list — only you can see this.",
    "Blocked members",
    "Blocked member photo",
    "Blocked {date}",
    "Unblocking…",
    "Unblock",
    "Unblock {name}",
    "Blocked members are never notified. Their posts and comments are hidden from you, and contact requests and messages are prevented in both directions.",
    "Members you have blocked",
    "You haven't blocked anyone. If you ever need to, use the Block action on a member's post, comment or conversation.",
    "Please sign in to block someone.",
    "We couldn't tell who to block.",
    "That member is no longer available.",
    "We couldn't tell who to unblock.",
    "That member wasn't on your blocked list.",
    BLOCK_SUCCESS_COPY,
    UNBLOCK_SUCCESS_COPY,
)


def function_node(
    path: Path, name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


class PrivateBlockCatalogTests(unittest.TestCase):
    def test_exact_sources_locales_and_complete_key_registration(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        expected_locales = offered | {"ha"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(BLOCK_KEYS, EXPECTED_BLOCK_KEYS)
        self.assertEqual(set(BLOCK_ROWS), expected_locales)
        self.assertEqual(set(BLOCK_CATALOGS), expected_locales)
        self.assertTrue(set(BLOCK_KEYS) <= set(COMPLETE_KEYS))
        self.assertIn("Cancel", COMPLETE_KEYS)

        for locale in expected_locales:
            entries = BLOCK_CATALOGS[locale]
            self.assertEqual(set(entries), set(BLOCK_KEYS))
            for source, value in entries.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertTrue(CATALOGS[locale][source].strip())
                    self.assertNotEqual(CATALOGS[locale][source], source)
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )
                    self.assertEqual(translate("en", source), source)
                    for marker in ("TODO", "TRANSLATE_ME", "\ufffd"):
                        self.assertNotIn(marker, value)

    def test_rows_are_static_authored_text_and_named_slots_are_exact(self):
        tree = ast.parse(Path("app/interface_catalog_block.py").read_text())
        rows_node = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "BLOCK_ROWS"
        )
        self.assertIsInstance(rows_node, ast.Dict)
        for key, value in zip(rows_node.keys, rows_node.values, strict=True):
            self.assertIsInstance(key, ast.Constant)
            self.assertIsInstance(value, ast.Constant)
            self.assertIsInstance(value.value, str)
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "BLOCK_ROWS"
                and node.func.attr == "update"
            ):
                continue
            self.assertIsInstance(node.args[0], ast.Dict)
            for key, value in zip(
                node.args[0].keys, node.args[0].values, strict=True
            ):
                self.assertIsInstance(key, ast.Constant)
                self.assertIsInstance(value, ast.Constant)
                self.assertIsInstance(value.value, str)

        formatter = string.Formatter()
        for entries in BLOCK_CATALOGS.values():
            for source, value in entries.items():
                source_slots = Counter(
                    name for _, name, _, _ in formatter.parse(source) if name
                )
                translated_slots = Counter(
                    name for _, name, _, _ in formatter.parse(value) if name
                )
                self.assertEqual(translated_slots, source_slots)
        self.assertEqual(
            Counter(
                name
                for _, name, _, _ in formatter.parse("Block {name}?")
                if name
            ),
            Counter({"name": 1}),
        )

    def test_privacy_meanings_keep_unilateral_private_and_two_way_effects(self):
        fixtures = {
            "es": (
                "nunca se le avisará",
                "ambas direcciones",
                "Nada de lo eliminado se recupera",
            ),
            "fr": (
                "n’en sera jamais informée",
                "dans les deux sens",
                "Rien de supprimé ne revient",
            ),
            "de": (
                "wird nie informiert",
                "in beide Richtungen",
                "Gelöschte Inhalte kommen nicht zurück",
            ),
            "ar": (
                "لن يتم إخبارهم أبدًا",
                "في كلا الاتجاهين",
                "لا يعود أي شيء محذوف",
            ),
            "zh": (
                "绝不会告知对方",
                "双方",
                "已删除的内容不会恢复",
            ),
        }
        sources = (
            "Block privately — they are never told",
            "Blocked members are never notified. Their posts and comments are hidden from you, and contact requests and messages are prevented in both directions.",
            "Unblocked. You'll see their posts again and you can both send contact requests and messages. Nothing deleted comes back.",
        )
        for locale, phrases in fixtures.items():
            for source, phrase in zip(sources, phrases, strict=True):
                self.assertIn(phrase, BLOCK_CATALOGS[locale][source])
        self.assertEqual(
            translate(
                "en",
                "They are not notified and are never told that you blocked them.",
            ),
            "They are not notified and are never told that you blocked them.",
        )
        self.assertEqual(translate("ha", "Cancel"), CATALOGS["ha"]["Cancel"])
        self.assertEqual(CATALOGS["es"]["Block"], "Bloquear")
        i18n_source = Path("app/interface_i18n.py").read_text()
        block_merge = i18n_source.split(
            "for _language, _entries in BLOCK_CATALOGS.items():", 1
        )[1].split("COMPLETE_KEYS", 1)[0]
        self.assertIn(
            "CATALOGS[_language].setdefault(_key, _value)", block_merge
        )

    def test_dynamic_name_count_and_date_values_are_substituted_verbatim(self):
        name = "ليلى {member}"
        date = "Feb 03, 2025"
        name_line = translate("fr", "Block {name}?").replace("{name}", name)
        count_line = translate(
            "fr",
            "{count} blocked members · private list — only you can see this.",
        ).replace("{count}", "7")
        date_line = translate("fr", "Blocked {date}").replace("{date}", date)
        self.assertIn(name, name_line)
        self.assertIn("7", count_line)
        self.assertIn(date, date_line)
        self.assertIn("{member}", name_line)

        profile_source = ast.unparse(
            function_node(PROFILE_PATH, "blocked_member_row")
        )
        self.assertIn(
            "ui_template('Blocked {date}', 'date', member['blocked_on'])",
            profile_source,
        )
        self.assertIn(
            "ui_template('Unblock {name}', 'name', member['name'])",
            profile_source,
        )
        self.assertIn("member['name']", profile_source)
        self.assertIn("member['handle']", profile_source)
        self.assertNotIn("ui(member['name'])", profile_source)
        self.assertNotIn("ui(member['handle'])", profile_source)

    def test_ui_wiring_and_state_sources_preserve_database_contract(self):
        dialog = ast.unparse(function_node(DIALOG_PATH, "block_dialog"))
        for phrase in (
            "ui('Safety')",
            "ui('Blocking is private and takes effect straight away.')",
            "ui('Close block confirmation')",
            "ui('Confirm blocking this member')",
            "ui('Block this member?')",
            "ui_template('Block {name}?', 'name', BlockState.target_name)",
            "AuthState.preferred_language",
            "AuthState.interface_direction",
        ):
            self.assertIn(phrase, dialog)

        button = ast.unparse(function_node(DIALOG_PATH, "block_member_button"))
        self.assertIn("ui(label)", button)
        self.assertIn("ui(accessible_label)", button)
        self.assertIn("ui(accessible_title)", button)
        point = ast.unparse(function_node(DIALOG_PATH, "_plain_point"))
        self.assertIn("ui(copy)", point)

        row = ast.unparse(function_node(PROFILE_PATH, "blocked_member_row"))
        section_node = function_node(PROFILE_PATH, "blocked_members_section")
        section = ast.unparse(section_node)
        for phrase in (
            "ui('Blocked member photo')",
            "ui('Unblocking…')",
            "ui('Unblock')",
            "ui_template('Unblock {name}'",
        ):
            self.assertIn(phrase, row)
        for phrase in (
            "BlockState.localized_blocked_count_label",
            "ui(BlockState.list_error)",
            "ui(BlockState.list_success)",
            "ui('Blocked members are never notified.",
            "ui('Members you have blocked')",
        ):
            self.assertIn(phrase, section)
        empty_state_key = next(
            key
            for key in EXPECTED_BLOCK_KEYS
            if key.startswith("You haven't blocked anyone.")
        )
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "ui"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == empty_state_key
                and not node.keywords
                for node in ast.walk(section_node)
            )
        )

        self.assertIsNotNone(block_dialog())
        self.assertIsNotNone(
            block_member_button(
                77,
                "Original member",
                label=ui("Block"),
                accessible_label=ui("Block this member privately"),
                accessible_title=ui("Block privately — they are never told"),
            )
        )
        self.assertIsNotNone(blocked_members_section())
        row_component = blocked_member_row(
            {
                "id": 23,
                "name": "Member Original",
                "handle": "@original",
                "avatar": "",
                "avatar_seed": "member-23",
                "verified": False,
                "blocked_on": "Feb 03, 2025",
            }
        )
        self.assertTrue(row_component)

        state_source = BLOCK_STATE_PATH.read_text()
        self.assertIn(
            'BLOCK_SUCCESS_COPY = (\n    "Blocked. Their posts and comments are hidden from you, your "\n'
            '    "conversations with them are closed, and neither of you can send "\n'
            '    "contact requests or messages. They are not told about this."\n)',
            state_source,
        )
        self.assertIn(
            'UNBLOCK_SUCCESS_COPY = (\n    "Unblocked. You\'ll see their posts again and you can both send contact "\n'
            '    "requests and messages. Nothing deleted comes back."\n)',
            state_source,
        )
        self.assertIn("self.success = BLOCK_SUCCESS_COPY", state_source)
        self.assertIn("self.list_success = UNBLOCK_SUCCESS_COPY", state_source)
        self.assertIn("translate(language, BLOCK_SUCCESS_COPY)", state_source)
        self.assertIn("translate(language, UNBLOCK_SUCCESS_COPY)", state_source)
        for sql_fragment in (
            "SELECT id FROM skillkind_subscriber",
            "INSERT INTO skillkind_member_block",
            "DELETE FROM skillkind_member_block",
            "ON CONFLICT (blocker_id, blocked_id) DO NOTHING",
            "WHERE blocker_id = :sid AND blocked_id = :tid",
        ):
            self.assertIn(sql_fragment, state_source)
        self.assertEqual(state_source.count("await asession.commit()"), 2)

        count_var = function_node(
            BLOCK_STATE_PATH, "localized_blocked_count_label"
        )
        self.assertIn("await self.get_state(AuthState)", ast.unparse(count_var))
        self.assertIn(
            "translate(auth.preferred_language", ast.unparse(count_var)
        )
        self.assertIn("def blocked_count_label(self) -> str:", state_source)


if __name__ == "__main__":
    unittest.main()
