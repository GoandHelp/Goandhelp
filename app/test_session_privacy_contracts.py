import reflex as rx

import asyncio
import ast
import importlib
import inspect
import json
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.avatars import ANIMAL_AVATARS
from app.states.auth_state import AuthState
from app.states.onboarding_state import OnboardingState
from app.components.profile_tabs import details_tab


def source(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as e:
        logging.exception(f"Error: {e}")
        raise


class SessionHarness(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class SessionHydrationTests(unittest.IsolatedAsyncioTestCase):
    async def hydrate(self, row, sid="42", fail=False):
        onboarding = OnboardingState(_reflex_internal_init=True)
        onboarding._reset()
        onboarding.has_row = True
        onboarding.is_complete = True
        state = SessionHarness(
            subscriber_id=sid,
            email="previous@example.invalid",
            display_name="Previous",
            phone="old",
            is_admin=True,
            is_verified=True,
            unverified_access=False,
            checking_session=True,
            error="",
            get_state=AsyncMock(return_value=onboarding),
        )
        session = SessionHarness(
            execute=AsyncMock(return_value=Mock(first=Mock(return_value=row))),
            commit=AsyncMock(),
        )
        if fail:
            session.execute.side_effect = RuntimeError("test database failure")
        with patch(
            "app.states.auth_state.rx.asession", return_value=session
        ) as factory:
            with patch.object(
                OnboardingState,
                "_resolve_progress",
                new=AsyncMock(side_effect=AssertionError("second session")),
            ):
                events = []
                async for event in AuthState.load_session.fn(state):
                    events.append(event)
            self.assertLessEqual(factory.call_count, 1)
        self.assertFalse(state.checking_session)
        return state, onboarding, session, events

    def row(self, progress=True, completed=False):
        return (
            "owner@example.invalid",
            "Owner",
            "",
            "both",
            None,
            "en",
            True,
            False,
            42 if progress else None,
            8,
            "1,2,3,4,5,6,7",
            json.dumps(
                {
                    "setup_version": 3,
                    "username": "owner.name",
                    "home_country": "Canada",
                }
            ),
            "{}",
            "completed" if completed else None,
            1,
            None,
        )

    async def test_one_query_and_one_session_for_active_member(self):
        state, onboarding, session, events = await self.hydrate(self.row())
        self.assertEqual(session.execute.await_count, 1)
        session.commit.assert_awaited_once()
        self.assertTrue(onboarding.progress_loaded)
        self.assertTrue(onboarding.needs_onboarding)
        self.assertEqual(state.email, "owner@example.invalid")
        self.assertEqual(len(events), 2)
        query = str(session.execute.call_args.args[0])
        self.assertIn("LEFT JOIN skillkind_onboarding_progress", query)
        self.assertIn("is_active = TRUE", query)
        self.assertIn("last_seen_at = now()", query)

    async def test_complete_and_legacy_accounts(self):
        for row in (self.row(completed=True), self.row(progress=False)):
            _, onboarding, _, _ = await self.hydrate(row)
            self.assertTrue(onboarding.progress_loaded)
            self.assertFalse(onboarding.needs_onboarding)

    async def test_invalid_and_failed_sessions_clear_gate_fail_closed(self):
        for sid, fail in (
            ("", False),
            ("invalid", False),
            ("42", False),
            ("42", True),
        ):
            state, onboarding, _, events = await self.hydrate(None, sid, fail)
            self.assertEqual(state.subscriber_id, "")
            self.assertEqual(state.email, "")
            self.assertFalse(state.is_admin)
            self.assertFalse(state.is_verified)
            self.assertFalse(onboarding.has_row)
            self.assertTrue(onboarding.progress_loaded)
            self.assertEqual(events, [])

    async def test_bad_progress_cannot_expose_member_product(self):
        row = list(self.row())
        row[9] = "not-a-step"
        state, _, _, events = await self.hydrate(tuple(row))
        self.assertEqual(state.subscriber_id, "")
        self.assertEqual(state.email, "")
        self.assertEqual(events, [])

    def test_followups_are_yielded_after_loading_finally(self):
        code = inspect.getsource(AuthState.load_session.fn)
        self.assertNotIn("_resolve_progress", code)
        self.assertEqual(code.count("rx.asession()"), 1)
        self.assertLess(
            code.index("finally:"), code.index("self.checking_session = False")
        )
        self.assertLess(
            code.index("self.checking_session = False"),
            code.index("yield ProfileState.load_profile"),
        )
        self.assertIn("asyncio.timeout(12)", code)

    async def test_database_timeout_clears_loading_gate_and_session(self):
        onboarding = OnboardingState(_reflex_internal_init=True)
        onboarding._reset()
        state = SessionHarness(
            subscriber_id="42",
            email="previous@example.invalid",
            display_name="Previous",
            phone="old",
            is_admin=True,
            is_verified=True,
            unverified_access=False,
            checking_session=True,
            error="",
            get_state=AsyncMock(return_value=onboarding),
        )

        async def stalled_query(*args, **kwargs):
            await asyncio.sleep(1)

        session = SessionHarness(
            execute=AsyncMock(side_effect=stalled_query),
            commit=AsyncMock(),
        )
        real_timeout = asyncio.timeout
        with patch("app.states.auth_state.rx.asession", return_value=session):
            with patch(
                "app.states.auth_state.asyncio.timeout",
                side_effect=lambda _: real_timeout(0.001),
            ):
                events = [
                    event async for event in AuthState.load_session.fn(state)
                ]

        self.assertEqual(events, [])
        self.assertEqual(state.subscriber_id, "")
        self.assertEqual(state.email, "")
        self.assertFalse(state.checking_session)
        self.assertTrue(onboarding.progress_loaded)
        self.assertFalse(onboarding.has_row)
        self.assertIn("restore your session", state.error)

    def test_session_loading_has_centered_logo_without_recovery_controls(self):
        from app.app import session_skeleton

        component = session_skeleton()
        rendered = str(component.render())
        code = inspect.getsource(session_skeleton)

        for recovery_copy in ("Still loading?", "Retry", "Sign out"):
            self.assertNotIn(recovery_copy, rendered)
            self.assertNotIn(recovery_copy, code)
        for recovery_dom in (
            "gah-loading-recovery",
            "AuthState.load_session",
            "AuthState.sign_out",
            "setTimeout",
            "clearTimeout",
            "7000",
        ):
            self.assertNotIn(recovery_dom, code)

        self.assertIn("h-[100px] w-[100px]", code)
        self.assertIn("absolute left-1/2 top-1/2", code)
        self.assertIn("-translate-x-1/2 -translate-y-1/2", code)
        self.assertIn("document.getElementById('gah-loading-logo-image')", code)
        self.assertIn("logoImage.animate(", code)
        tree = ast.parse(code)
        image_call = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "image"
            and any(
                keyword.arg == "id"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "gah-loading-logo-image"
                for keyword in node.keywords
            )
        )
        logo_container = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "div"
            and any(
                keyword.arg == "id"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "gah-loading-logo"
                for keyword in node.keywords
            )
        )
        self.assertIn(image_call, list(ast.walk(logo_container)))
        container_classes = next(
            keyword.value.value
            for keyword in logo_container.keywords
            if keyword.arg == "class_name"
        )
        self.assertIn("absolute left-1/2 top-1/2", container_classes)
        self.assertIn("-translate-x-1/2 -translate-y-1/2", container_classes)
        self.assertIn("bottom-[calc(5.5rem+env(safe-area-inset-bottom))]", code)
        self.assertIn("AuthState.error", code)
        self.assertIn("OnboardingState.error", code)
        self.assertGreaterEqual(code.count('role="alert"'), 2)
        self.assertIn('role="status"', code)
        self.assertIn('aria_live="polite"', code)
        self.assertIn("prefers-reduced-motion", code)
        self.assertIn("motion.addEventListener('change', sync)", code)
        self.assertIn("motion.removeEventListener('change', sync)", code)
        self.assertIn("pulse.cancel()", code)
        self.assertIn("window.gahLoadingCleanup?.()", code)
        self.assertIn("on_unmount", code)


class EmailPrivacyTests(unittest.TestCase):
    # These modules intentionally handle the owner's private credentials or
    # privileged moderation. Sharing links named 'email' contain no recipient.
    exceptions = {
        "admin_state.py",
        "auth_state.py",
        "password_reset_state.py",
        "verify_state.py",
        "membership_state.py",
        "admin_panel.py",
        "auth_panel.py",
        "reset_password_panel.py",
        "verify_panel.py",
        "verification_notice.py",
    }

    def test_public_dto_fields_and_sql_projections(self):
        root = Path(__file__).parent
        for folder in ("states", "components"):
            for path in (root / folder).glob("*.py"):
                if path.name in self.exceptions:
                    continue
                tree = ast.parse(source(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.AnnAssign) and isinstance(
                        node.target, ast.Name
                    ):
                        name = node.target.id
                        self.assertFalse(
                            name == "email" or name.endswith("_email"),
                            f"{path.name}: {name}",
                        )
                    if isinstance(node, ast.Constant) and isinstance(
                        node.value, str
                    ):
                        value = node.value
                        if "SELECT" in value.upper() or " LIKE :q" in value:
                            self.assertNotRegex(
                                value, r"\b\w+\.email\b", path.name
                            )
                    if isinstance(node, ast.Dict):
                        for key in node.keys:
                            if isinstance(key, ast.Constant) and isinstance(
                                key.value, str
                            ):
                                self.assertFalse(
                                    key.value.endswith("_email"),
                                    f"{path.name}: {key.value}",
                                )
                    if isinstance(node, ast.JoinedStr):
                        rendered = ast.unparse(node)
                        if "dicebear" in rendered:
                            self.assertNotIn("email", rendered, path.name)

    def test_runtime_public_defaults_and_components(self):
        for name in (
            "contacts",
            "discovery",
            "community",
            "messaging",
            "noncontact",
        ):
            module = importlib.import_module(f"app.states.{name}_state")
            for label, value in vars(module).items():
                if label.startswith("EMPTY") and isinstance(value, dict):
                    self.assertNotIn("email", value)
                    self.assertFalse(
                        any(key.endswith("_email") for key in value)
                    )
                    self.assertNotIn("@example", json.dumps(value))
        from app.components.header import account_badge
        from app.states.discovery_state import _avatar_image_url

        url = _avatar_image_url("", "member-42")
        self.assertIn(url, ANIMAL_AVATARS)
        self.assertNotIn("seed", url)
        self.assertNotIn("member-42", url)
        self.assertNotIn("@", url)
        self.assertNotIn("auth_state.email", str(account_badge()))
        self.assertTrue(details_tab().render())

    def test_owner_email_is_readonly_unsubmitted_and_in_order(self):
        code = inspect.getsource(details_tab)
        handle = code.index('field_label("Public handle"')
        phone = code.index('field_label("Phone"')
        email = code.index('"profile-private-email"')
        self.assertLess(handle, phone)
        self.assertLess(phone, email)
        tree = ast.parse(code)
        inputs = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "input"
        ]
        private = next(
            node
            for node in inputs
            if any(
                k.arg == "id"
                and isinstance(k.value, ast.Constant)
                and k.value.value == "profile-private-email"
                for k in node.keywords
            )
        )
        props = {k.arg: k.value for k in private.keywords}
        self.assertTrue(props["read_only"].value)
        self.assertNotIn("name", props)
        self.assertNotIn("on_change", props)
        self.assertEqual(ast.unparse(props["default_value"]), "AuthState.email")
        self.assertIn("aria_describedby", props)
        self.assertIn("only visible to you", code)
        self.assertIn("phone_privacy_notice()", code)


if __name__ == "__main__":
    unittest.main()
