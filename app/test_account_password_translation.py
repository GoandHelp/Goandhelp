import reflex as rx

import ast
import string
import unicodedata
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.interface_catalog_account_password import (
    ACCOUNT_PASSWORD_CATALOGS,
    ACCOUNT_PASSWORD_KEYS,
    ACCOUNT_PASSWORD_ROWS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    ENTRY_CATALOGS,
    FORUM_FEEDBACK_CATALOGS,
    translate,
)
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import hash_password
from app.states.profile_state import ProfileState
from app.test_profile_account_security import StateHarness


EXPECTED_KEYS = (
    "Change password",
    "Current password",
    "New password",
    "Confirm new password",
    "Changing password…",
    "Enter your current password.",
    "Passwords need at least 6 characters.",
    "The two passwords don't match.",
    "Choose a new password different from your current password.",
    "We couldn't save that password just now. Please try again.",
    "Current password is incorrect.",
    "Your password has been changed.",
    "Password changed.",
    "Your session expired — please sign in again.",
)


def function_node(path: str, name: str):
    return next(
        node
        for node in ast.walk(ast.parse(Path(path).read_text()))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


class AccountPasswordCatalogTests(unittest.TestCase):
    def test_exact_sources_locales_and_no_fallback(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(ACCOUNT_PASSWORD_KEYS, EXPECTED_KEYS)
        self.assertEqual(len(set(ACCOUNT_PASSWORD_KEYS)), 14)
        self.assertEqual(set(ACCOUNT_PASSWORD_ROWS), offered | {"ha"})
        self.assertEqual(set(ACCOUNT_PASSWORD_CATALOGS), offered | {"ha"})
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))
        for locale, entries in ACCOUNT_PASSWORD_CATALOGS.items():
            self.assertEqual(set(entries), set(EXPECTED_KEYS))
            self.assertEqual(len(ACCOUNT_PASSWORD_ROWS[locale].split("|")), 14)
            for source, value in entries.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertNotIn(source, value)
                    self.assertFalse(value.startswith(f"{locale}:"))
                    for marker in ("TODO", "TRANSLATE_ME", "\ufffd"):
                        self.assertNotIn(marker, value)
                    self.assertIn(source, CATALOGS[locale])
                    self.assertNotEqual(translate(locale, source), source)
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )
                    self.assertEqual(translate("en", source), source)

    def test_rows_are_explicit_static_strings_and_slots_preserved(self):
        tree = ast.parse(
            Path("app/interface_catalog_account_password.py").read_text()
        )
        rows = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "ACCOUNT_PASSWORD_ROWS"
        )
        self.assertIsInstance(rows, ast.Dict)
        for key, value in zip(rows.keys, rows.values, strict=True):
            self.assertIsInstance(key, ast.Constant)
            self.assertIsInstance(value, ast.Constant)
            self.assertIsInstance(value.value, str)
        formatter = string.Formatter()
        for entries in ACCOUNT_PASSWORD_CATALOGS.values():
            for source, value in entries.items():
                expected = Counter(
                    name for _, name, _, _ in formatter.parse(source) if name
                )
                actual = Counter(
                    name for _, name, _, _ in formatter.parse(value) if name
                )
                self.assertEqual(actual, expected)

    def test_six_character_minimum_and_representative_meaning(self):
        source = "Passwords need at least 6 characters."
        for locale, entries in ACCOUNT_PASSWORD_CATALOGS.items():
            with self.subTest(locale=locale):
                digits = [
                    unicodedata.decimal(c)
                    for c in entries[source]
                    if c.isdecimal()
                ]
                self.assertEqual(digits, [6])
        fixtures = {
            "fr": "au moins 6 caractères",
            "de": "mindestens 6 Zeichen",
            "es": "al menos 6 caracteres",
            "zh": "至少需要6个字符",
            "my": "အနည်းဆုံး စာလုံး ၆ လုံး",
            "fa": "حداقل ۶ نویسه",
        }
        for locale, phrase in fixtures.items():
            self.assertIn(phrase, ACCOUNT_PASSWORD_CATALOGS[locale][source])
        self.assertEqual(
            ACCOUNT_PASSWORD_CATALOGS["fr"]["The two passwords don't match."],
            "Les deux mots de passe ne correspondent pas.",
        )
        self.assertEqual(
            ACCOUNT_PASSWORD_CATALOGS["es"][
                "Choose a new password different from your current password."
            ],
            "Elige una nueva contraseña diferente de la actual.",
        )

    def test_established_shared_meanings_are_not_overwritten(self):
        session_source = "Your session expired — please sign in again."
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        for locale in offered:
            self.assertEqual(
                CATALOGS[locale][session_source],
                FORUM_FEEDBACK_CATALOGS[locale][session_source],
            )
            for source in set(EXPECTED_KEYS) & set(ENTRY_CATALOGS[locale]):
                self.assertEqual(
                    CATALOGS[locale][source], ENTRY_CATALOGS[locale][source]
                )
        self.assertEqual(
            CATALOGS["ha"][session_source],
            ACCOUNT_PASSWORD_CATALOGS["ha"][session_source],
        )
        self.assertNotIn("ha", FORUM_FEEDBACK_CATALOGS)
        self.assertNotIn("ha", ENTRY_CATALOGS)
        source = Path("app/interface_i18n.py").read_text()
        merge = source.split(
            "for _language, _entries in ACCOUNT_PASSWORD_CATALOGS.items():", 1
        )[1].split("COMPLETE_KEYS", 1)[0]
        self.assertIn("CATALOGS[_language].setdefault(_key, _value)", merge)
        self.assertNotIn(".update(", merge)

    def test_reactive_display_and_unchanged_form_contracts(self):
        path = "app/components/profile_tabs.py"
        form = function_node(path, "change_password_form")
        calls = [node for node in ast.walk(form) if isinstance(node, ast.Call)]
        fixed = [
            node.args[0].value
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "ui"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ]
        self.assertEqual(fixed.count("Change password"), 3)
        self.assertEqual(fixed.count("Changing password…"), 1)
        for helper, feedback in (
            ("error_banner", "password_error"),
            ("success_banner", "password_success"),
        ):
            call = next(
                node
                for node in calls
                if isinstance(node.func, ast.Name) and node.func.id == helper
            )
            self.assertEqual(
                ast.unparse(call.args[0]), f"ui(ProfileState.{feedback})"
            )
        field = function_node(path, "password_field")
        self.assertIn("ui(label)", ast.unparse(field))
        field_calls = [
            node
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "password_field"
        ]
        self.assertEqual(
            [
                tuple(ast.literal_eval(arg) for arg in node.args)
                for node in field_calls
            ],
            [
                ("Current password", "current_password", "current-password", 1),
                ("New password", "new_password", "new-password", 6),
                ("Confirm new password", "confirm_password", "new-password", 6),
            ],
        )
        rendered_source = ast.unparse(form)
        self.assertIn("on_submit=ProfileState.change_password", rendered_source)
        self.assertIn("reset_on_submit=True", rendered_source)
        self.assertIn("grid-cols-1", rendered_source)
        self.assertIn("md:grid-cols-2", rendered_source)
        self.assertNotIn("on_change", ast.unparse(field))
        for token in (
            "required=True",
            "auto_complete=autocomplete",
            "min_length=minimum",
        ):
            self.assertIn(token, ast.unparse(field))
        state = ProfileState(_reflex_internal_init=True)
        state.password_error = "Current password is incorrect."
        state.password_success = "Your password has been changed."
        originals = (state.password_error, state.password_success)
        for language in ("fr", "ja", "en", "ha"):
            for source in originals:
                self.assertEqual(
                    translate(language, source),
                    CATALOGS.get(language, {}).get(source, source),
                )
            self.assertEqual(
                (state.password_error, state.password_success), originals
            )

    def test_security_source_and_toast_order(self):
        handler = ast.unparse(
            function_node("app/states/profile_state.py", "change_password")
        )
        for token in (
            "not auth.is_signed_in",
            "not sid.isascii()",
            "not sid.isdigit()",
            "len(password) < 6",
            "password != confirm",
            "password == current",
            "hash_password(current)",
            "hash_password(password)",
            "await session.rollback()",
            "await session.commit()",
        ):
            self.assertIn(token, handler)
        node = function_node("app/states/profile_state.py", "change_password")
        sql = [
            n.value
            for n in ast.walk(node)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and "UPDATE " in n.value
        ]
        self.assertEqual(len(sql), 2)
        password_sql = next(
            statement
            for statement in sql
            if "UPDATE skillkind_subscriber" in statement
        )
        reset_sql = next(
            statement
            for statement in sql
            if "UPDATE skillkind_password_reset_token" in statement
        )
        self.assertIn(
            "WHERE id = :sid AND password_hash = :current_hash AND is_active = TRUE RETURNING id",
            " ".join(password_sql.split()),
        )
        self.assertIn(
            "AND used_at IS NULL AND invalidated_at IS NULL",
            " ".join(reset_sql.split()),
        )
        self.assertIn("SET invalidated_at = now()", reset_sql)
        for feedback in EXPECTED_KEYS[5:]:
            self.assertIn(
                feedback,
                [
                    n.value
                    for n in ast.walk(node)
                    if isinstance(n, ast.Constant)
                ],
            )
        self.assertIn(
            "language = (await self.get_state(AuthState)).preferred_language",
            handler,
        )
        self.assertIn("translate(language, 'Password changed.')", handler)
        self.assertLess(
            handler.index("await session.commit()"), handler.index("language =")
        )
        self.assertNotIn("self.password_success = translate", handler)
        self.assertNotIn("self.password_error = translate", handler)


class AccountPasswordToastTests(unittest.IsolatedAsyncioTestCase):
    async def test_current_language_after_commit_without_extra_writes(self):
        for locale in ACCOUNT_PASSWORD_CATALOGS:
            with self.subTest(locale=locale):
                state = StateHarness(
                    auth=SimpleNamespace(
                        subscriber_id="42",
                        is_signed_in=True,
                        preferred_language="en",
                    ),
                    password_busy=False,
                    password_error="",
                    password_success="",
                )
                session = MagicMock()
                session.__aenter__ = AsyncMock(return_value=session)
                session.__aexit__ = AsyncMock(return_value=False)
                result = MagicMock()
                result.first.return_value = (42,)
                session.execute = AsyncMock(return_value=result)
                session.rollback = AsyncMock()

                async def commit():
                    state.auth.preferred_language = locale

                session.commit = AsyncMock(side_effect=commit)
                with (
                    patch(
                        "app.states.profile_state.rx.asession",
                        return_value=session,
                    ),
                    patch(
                        "app.states.profile_state.rx.toast",
                        return_value=rx.noop(),
                    ) as toast,
                ):
                    events = [
                        event
                        async for event in ProfileState.change_password.fn(
                            state,
                            {
                                "current_password": "old-secret",
                                "new_password": "new-secret",
                                "confirm_password": "new-secret",
                                "sid": "999",
                            },
                        )
                    ]
                toast.assert_called_once_with(
                    translate(locale, "Password changed."), duration=4000
                )
                self.assertEqual(len(events), 1)
                self.assertEqual(
                    state.password_success, "Your password has been changed."
                )
                self.assertEqual(state.password_error, "")
                self.assertFalse(state.password_busy)
                self.assertEqual(session.execute.await_count, 2)
                session.commit.assert_awaited_once()
                session.rollback.assert_not_awaited()
                params = session.execute.call_args_list[0].args[1]
                self.assertEqual(
                    params,
                    {
                        "sid": 42,
                        "current_hash": hash_password("old-secret"),
                        "new_hash": hash_password("new-secret"),
                    },
                )

    async def test_no_toast_on_wrong_password_or_failed_commit(self):
        for fail_commit in (False, True):
            with self.subTest(fail_commit=fail_commit):
                state = StateHarness(
                    auth=SimpleNamespace(
                        subscriber_id="42",
                        is_signed_in=True,
                        preferred_language="fr",
                    ),
                    password_busy=False,
                    password_error="",
                    password_success="",
                )
                session = MagicMock()
                session.__aenter__ = AsyncMock(return_value=session)
                session.__aexit__ = AsyncMock(return_value=False)
                result = MagicMock()
                result.first.return_value = (42,) if fail_commit else None
                session.execute = AsyncMock(return_value=result)
                session.rollback = AsyncMock()
                session.commit = AsyncMock(
                    side_effect=RuntimeError("commit failed")
                    if fail_commit
                    else None
                )
                with (
                    patch(
                        "app.states.profile_state.rx.asession",
                        return_value=session,
                    ),
                    patch("app.states.profile_state.rx.toast") as toast,
                    patch("app.states.profile_state.logging.exception"),
                ):
                    events = [
                        event
                        async for event in ProfileState.change_password.fn(
                            state,
                            {
                                "current_password": "old-secret",
                                "new_password": "new-secret",
                                "confirm_password": "new-secret",
                            },
                        )
                    ]
                self.assertFalse(events)
                toast.assert_not_called()
                self.assertFalse(state.password_success)
                self.assertFalse(state.password_busy)
                self.assertEqual(
                    state.password_error,
                    "We couldn't save that password just now. Please try again."
                    if fail_commit
                    else "Current password is incorrect.",
                )
                session.rollback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
