import reflex as rx

import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.request_draft import REQUEST_TEXT_FIELDS, normalize_request_payload
from app.states.help_post_state import HelpPostState
from app.states.onboarding_state import OnboardingState


PAYLOADS = (
    (" 25.50 ", " 25.50 "),
    (25, "25"),
    (25.5, "25.5"),
    (0, "0"),
    (0.0, "0.0"),
    (None, ""),
    (True, "True"),
    ("x" * 1001, "x" * 1000),
    ("é" * 1000, "é" * 1000),
)


class RequestPayloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_both_handlers_normalize_all_text_fields(self):
        onboarding = OnboardingState(_reflex_internal_init=True)
        onboarding._reset()
        onboarding.has_row = False
        self.assertFalse(onboarding.has_row)
        edit = HelpPostState(_reflex_internal_init=True)
        with (
            patch.object(OnboardingState, "get_state", AsyncMock()) as lookup,
            patch.object(rx, "asession") as database,
        ):
            for field in REQUEST_TEXT_FIELDS:
                for payload, expected in PAYLOADS:
                    with self.subTest(field=field, payload=repr(payload)[:40]):
                        await OnboardingState.set_request_field.fn(
                            onboarding, field, payload
                        )
                        HelpPostState.set_request_field.fn(edit, field, payload)
                        self.assertEqual(getattr(onboarding, field), expected)
                        self.assertEqual(getattr(edit, field), expected)
                        self.assertIsInstance(getattr(onboarding, field), str)
                        self.assertIsInstance(getattr(edit, field), str)
            lookup.assert_not_awaited()
            database.assert_not_called()

    async def test_unknown_fields_and_busy_guards_do_not_mutate(self):
        onboarding = OnboardingState(_reflex_internal_init=True)
        edit = HelpPostState(_reflex_internal_init=True)
        onboarding.request_budget = edit.request_budget = "original"
        with patch.object(
            OnboardingState, "_save_request_draft", AsyncMock()
        ) as save:
            for field in ("unknown_field", "error", "request_quote"):
                await OnboardingState.set_request_field.fn(
                    onboarding, field, 25.5
                )
                HelpPostState.set_request_field.fn(edit, field, 25.5)
            self.assertFalse(hasattr(onboarding, "unknown_field"))
            self.assertFalse(hasattr(edit, "unknown_field"))
            self.assertEqual(onboarding.error, "")
            self.assertEqual(edit.error, "")
            self.assertFalse(onboarding.request_quote)
            self.assertFalse(edit.request_quote)
            onboarding.saving = True
            await OnboardingState.set_request_field.fn(
                onboarding, "request_budget", None
            )
            onboarding.saving = False
            onboarding.first_request_post_id = 1
            await OnboardingState.set_request_field.fn(
                onboarding, "request_budget", 25.5
            )
            edit.edit_busy = True
            HelpPostState.set_request_field.fn(edit, "request_budget", 25.5)
            self.assertEqual(onboarding.request_budget, "original")
            self.assertEqual(edit.request_budget, "original")
            save.assert_not_awaited()

    async def test_inactive_drafts_skip_lookup_and_database(self):
        for has_row, complete in ((False, False), (False, True), (True, True)):
            with self.subTest(has_row=has_row, complete=complete):
                state = OnboardingState(_reflex_internal_init=True)
                state.has_row = has_row
                state.is_complete = complete
                with (
                    patch.object(
                        OnboardingState, "get_state", AsyncMock()
                    ) as lookup,
                    patch.object(rx, "asession") as database,
                ):
                    await state._save_request_draft()
                    lookup.assert_not_awaited()
                    database.assert_not_called()

    async def test_active_draft_persists_normalized_budget(self):
        state = OnboardingState(_reflex_internal_init=True)
        state.has_row = True
        auth = SimpleNamespace(is_signed_in=True, subscriber_id="7")
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        with (
            patch.object(
                OnboardingState, "get_state", AsyncMock(return_value=auth)
            ) as lookup,
            patch.object(rx, "asession", return_value=session),
        ):
            await OnboardingState.set_request_field.fn(
                state, "request_budget", 25.5
            )
        lookup.assert_awaited_once()
        session.execute.assert_awaited_once()
        session.commit.assert_awaited_once()
        sql, params = session.execute.await_args.args
        self.assertIn("completed_at IS NULL", str(sql))
        self.assertIn("first_request_post_id", str(sql))
        self.assertEqual(params["sid"], 7)
        self.assertEqual(json.loads(params["draft"])["request_budget"], "25.5")

    def test_helper_never_stringifies_rich_objects(self):
        rich = MagicMock()
        rich.__str__.side_effect = AssertionError("must not stringify objects")
        for value in (rich, {}, [], (25.5,), b"25.5"):
            self.assertEqual(normalize_request_payload(value), "")
        rich.__str__.assert_not_called()
        for value, expected in PAYLOADS:
            self.assertEqual(normalize_request_payload(value), expected)


if __name__ == "__main__":
    unittest.main()
