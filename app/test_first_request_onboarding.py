import reflex as rx

import datetime
import inspect
import json
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.request_draft import (
    FIRST_REQUEST_INSERT,
    EDIT_REQUEST_UPDATE,
    EDITABLE_POST,
    validate_request,
    valid_request_point,
)
from app.states.onboarding_state import OnboardingState, ONBOARDING_SCREENS
from app.states.help_post_state import HelpPostState
from app.states.auth_state import AuthState
from app.skill_categories import CATEGORY_CHOICES


def valid_params(**overrides):
    values = dict(
        title="Help with garden",
        description="Please help me tidy the garden.",
        category=CATEGORY_CHOICES[0]["value"],
        day=datetime.date.today().isoformat(),
        reward="money",
        currency="EUR",
        budget="25.50",
        quote=False,
        other="",
    )
    values.update(overrides)
    return validate_request(**values)


def session_context(session):
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


def seed_draft(state):
    state.request_title = "Help with garden"
    state.request_description = "Please help me tidy the garden."
    state.request_category = CATEGORY_CHOICES[0]["value"]
    state.request_date = datetime.date.today().isoformat()
    state.request_reward = "money"
    state.request_currency = "EUR"
    state.request_budget = "25.50"
    state.request_quote = False


class FirstRequestValidationTests(unittest.TestCase):
    def test_money_and_fixed_time(self):
        result = valid_params()
        self.assertEqual(result["reward_value"], Decimal("25.50"))
        self.assertEqual(result["reward_currency"], "EUR")
        self.assertEqual(result["reward_type"], "money")
        self.assertEqual(result["reward_types"], "money")
        self.assertEqual(result["scheduled"].hour, 13)
        self.assertEqual(result["scheduled"].minute, 0)
        self.assertEqual(result["start_time"], "13:00")
        quote = valid_params(quote=True, budget="")
        self.assertEqual(quote["reward_value"], 0)
        self.assertIn("Helper quote requested", quote["reward_details"])

    def test_invalid_inputs(self):
        for overrides in [
            dict(title="abc"),
            dict(title="a" * 161),
            dict(description="short"),
            dict(description="a" * 501),
            dict(category="made_up"),
            dict(category="arts,cleaner"),
            dict(day="invalid"),
            dict(day="2000-01-01"),
            dict(day="2999-01-01"),
            dict(reward="unknown"),
            dict(currency="FAKE"),
            dict(budget="-1"),
            dict(budget="NaN"),
            dict(budget="1.001"),
            dict(budget="0"),
            dict(reward="other_reward", other=""),
        ]:
            with (
                self.subTest(overrides=overrides),
                self.assertRaises(ValueError),
            ):
                valid_params(**overrides)
        result = valid_params(reward="other_reward", other="A homemade cake")
        self.assertEqual(result["reward_type"], "other")
        self.assertEqual(result["other_details"], "A homemade cake")
        self.assertFalse(valid_request_point(True, float("nan"), 2))
        self.assertFalse(valid_request_point(True, 91, 2))
        self.assertFalse(valid_request_point(False, 0, 0))
        self.assertTrue(valid_request_point(True, 0, 0))

    def test_round_trip_and_gates(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        seed_draft(state)
        state.request_date = ""
        state.request_has_point = True
        state.request_latitude, state.request_longitude = 51.5, -0.12
        restored = OnboardingState(_reflex_internal_init=True)
        restored._apply_answers(json.loads(json.dumps(state._answers())), {})
        self.assertEqual(restored._request_answers(), state._request_answers())
        restored.current_step = 13
        restored.ready_confirmed = True
        self.assertTrue(restored.can_continue)
        restored.first_request_post_id = 55
        self.assertTrue(restored.can_continue)
        restored.current_step = 14
        restored.ready_confirmed = False
        self.assertTrue(restored.can_continue)
        restored.ready_confirmed = True
        self.assertTrue(restored.can_continue)
        restored._reset()
        self.assertEqual(restored.first_request_post_id, 0)

    def test_screens_and_sql_contract(self):
        from app.components.onboarding import first_request_screen
        from app.components.request_draft import compact_request_fields

        self.assertEqual(
            ONBOARDING_SCREENS[12]["title"], "Need help with a job?"
        )
        self.assertEqual(len(ONBOARDING_SCREENS), 13)
        source = inspect.getsource(compact_request_fields)
        for forbidden in [
            "photos",
            "Knowledge and Skills",
            "Start time",
            "Required Language",
            "helpers_needed",
            "recurrence",
            '"City"',
            '"Country"',
            '"Address"',
        ]:
            self.assertNotIn(forbidden, source)
        self.assertNotIn(
            "first_request_post_id", inspect.getsource(first_request_screen)
        )
        self.assertNotIn(
            "Your first request is posted",
            inspect.getsource(first_request_screen),
        )
        self.assertTrue(first_request_screen().render())
        self.assertIn(
            "show_date=False", inspect.getsource(first_request_screen)
        )
        self.assertTrue(
            inspect.signature(compact_request_fields)
            .parameters["show_date"]
            .default
        )
        state = OnboardingState(_reflex_internal_init=True)
        state.current_step = 13
        self.assertEqual(state.continue_label, "Let's go and help!")
        state.current_step = 14
        self.assertEqual(state.continue_label, "Let's go and help!")
        self.assertTrue(first_request_screen().render())
        self.assertIn("accepted_latitude", FIRST_REQUEST_INSERT)
        self.assertIn("'approximate'", FIRST_REQUEST_INSERT)
        self.assertIn("60", FIRST_REQUEST_INSERT)
        self.assertIn("NOT EXISTS", EDITABLE_POST)
        self.assertIn("a.post_id = p.id", EDITABLE_POST)
        self.assertNotIn("a.status", EDITABLE_POST)
        self.assertIn("RETURNING p.id", EDIT_REQUEST_UPDATE)
        self.assertIn("ELSE p.latitude", EDIT_REQUEST_UPDATE)
        self.assertIn(
            "AS can_edit", inspect.getsource(HelpPostState.load_recent.fn)
        )


class FirstRequestTransactionTests(unittest.IsolatedAsyncioTestCase):
    async def test_insert_and_duplicate(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.has_row = True
        state.saving = False
        state.current_step = 13
        seed_draft(state)
        state.request_has_point = True
        state.request_latitude, state.request_longitude = 51.5, -0.12
        auth = SimpleNamespace(is_signed_in=True, subscriber_id="7")
        calls = []

        async def execute(sql, params):
            calls.append((str(sql), params))
            if "SELECT answers_json" in str(sql):
                return SimpleNamespace(first=lambda: ("{}",))
            if "INSERT INTO skillkind_help_post" in str(sql):
                return SimpleNamespace(scalar_one=lambda: 88)
            return SimpleNamespace(first=lambda: (88,))

        session = SimpleNamespace(
            execute=AsyncMock(side_effect=execute),
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )
        with (
            patch.object(
                OnboardingState, "get_state", AsyncMock(return_value=auth)
            ),
            patch("reflex.asession", return_value=session_context(session)),
            patch(
                "app.states.onboarding_state.check_post_allowance",
                AsyncMock(return_value=(True, False, 0, 2)),
            ),
        ):
            async for _ in OnboardingState.post_first_request.fn(state):
                pass
            state.current_step = 13
            async for _ in OnboardingState.post_first_request.fn(state):
                pass
        inserts = [
            params
            for sql, params in calls
            if "INSERT INTO skillkind_help_post" in sql
        ]
        self.assertEqual(len(inserts), 1)
        self.assertEqual(inserts[0]["scheduled"].hour, 13)
        self.assertEqual(
            inserts[0]["help_dates"], datetime.date.today().isoformat()
        )
        self.assertEqual(inserts[0]["latitude"], 51.5)
        self.assertEqual(inserts[0]["longitude"], -0.12)
        self.assertEqual(inserts[0]["reward_value"], Decimal("25.50"))
        self.assertEqual(inserts[0]["lifetime"], "1 month")
        saved = next(
            json.loads(params["answers"])
            for sql, params in calls
            if "current_step = 13" in sql
        )
        self.assertEqual(saved["first_request_post_id"], 88)
        self.assertEqual(state.current_step, 13)
        self.assertFalse(state.saving)
        session.commit.assert_awaited_once()

    async def test_edit_offer_race_rolls_back(self):
        state = HelpPostState(_reflex_internal_init=True)
        seed_draft(state)
        state.edit_post_id = 88
        state.edit_busy = False
        auth = SimpleNamespace(is_signed_in=True, subscriber_id="7")
        picker = SimpleNamespace(
            open_key="edit-help-request",
            has_point=False,
            latitude=0.0,
            longitude=0.0,
        )

        async def get_state(cls):
            return auth if cls is AuthState else picker

        session = SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(first=lambda: None)),
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )
        with (
            patch.object(
                HelpPostState, "get_state", AsyncMock(side_effect=get_state)
            ),
            patch("reflex.asession", return_value=session_context(session)),
        ):
            async for _ in HelpPostState.save_edit.fn(state):
                pass
        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()
        self.assertIn("help offer", state.edit_error)
        self.assertEqual(state.edit_post_id, 88)
        self.assertFalse(state.edit_busy)
        update = session.execute.await_args_list[-1]
        self.assertIn("NOT EXISTS", str(update.args[0]))
        self.assertEqual(update.args[1]["sid"], 7)
        self.assertFalse(update.args[1]["repin"])
