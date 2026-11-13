import reflex as rx

import ast
import datetime
import inspect
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components.help_hub_panel import (
    post_help_form,
    money_details_field,
    duration_field,
    help_day_field,
    required_languages_field,
)
from app.components.help_post_panel import (
    CATEGORY_LISTENERS,
    category_section,
    photo_upload_section,
)
from app.help_languages import decode_duration_period, decode_knowledge
from app.models import help_duration_label
from app.states.help_hub_state import (
    HelpHubState,
    REWARD_CHOICES,
    LEGACY_REWARD_TYPE,
    _hours_label,
)
from app.states.help_post_state import HelpPostState


class Draft(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, state):
        return self.states[state.__name__]


class Session:
    def __init__(self):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def begin(self):
        return self

    async def execute(self, sql, params):
        self.calls.append((str(sql), params))
        return SimpleNamespace(scalar_one=lambda: 42, all=lambda: [])


def draft():
    return Draft(
        is_saving=False,
        help_dates=[
            (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        ],
        day_mode="specific",
        time_mode="specific",
        flexible_days=[],
        custom_weekdays=[],
        selected_rewards=["money"],
        posting_country="United Kingdom",
        reward_currency="USD",
        required_languages=[],
        budget_quote_allowed=False,
        duration_quote_allowed=False,
        duration_period_count=3,
        duration_period_unit="week",
        form_open=True,
        rewards_open=True,
        missing_fields=[],
        error="",
        success="",
        _parse_start_time=HelpHubState._parse_start_time,
        _parse_duration=HelpHubState._parse_duration,
        _money_details=HelpHubState._money_details,
        states={
            "AuthState": SimpleNamespace(subscriber_id="7"),
            "HelpPostState": SimpleNamespace(
                pending_photo_paths=[], selected_categories=["labour"]
            ),
            "MapPickerState": SimpleNamespace(
                has_point=True, latitude=51.5, longitude=-0.1
            ),
        },
    )


def payload():
    return dict(
        title="Carry some boxes",
        description="Please help carry boxes up the stairs.",
        specific_hour="09",
        specific_minute="00",
        duration_hours="1",
        duration_minutes_part="30",
        duration_period_count="3",
        duration_period_unit="week",
        money_budget="12.50",
    )


class AskHelpTests(unittest.TestCase):
    def test_field_order_and_labels(self):
        source = inspect.getsource(post_help_form)
        markers = [
            'field_label("Job title"',
            'field_label("Job description"',
            "category_section()",
            "photo_upload_section()",
            "help_day_field()",
            "start_time_field()",
            "duration_field()",
            "job_location_section()",
            "rewards_field()",
            "HelpHubState.missing_fields",
            'type="submit"',
        ]
        positions = [source.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("required_languages_field()", source)
        self.assertNotIn("md:grid-cols-2", source)
        self.assertNotIn('name="tools"', source)
        self.assertNotIn('name="knowledge_skills"', source)
        self.assertNotIn('field_label("Tools"', source)
        self.assertNotIn('field_label("Knowledge and Skills"', source)
        for component, label in [
            (category_section, "Job category"),
            (photo_upload_section, "Upload Photos"),
            (help_day_field, "Date"),
            (required_languages_field, "Required Language"),
        ]:
            self.assertIn(
                f'field_label("{label}"', inspect.getsource(component)
            )

    def test_category_boundary_and_cleanup_contract(self):
        for event, suffix in [
            ("click", ""),
            ("scroll", ", true"),
            ("keydown", ""),
        ]:
            self.assertIn(
                f"addEventListener('{event}', close{suffix})",
                CATEGORY_LISTENERS,
            )
            self.assertIn(
                f"removeEventListener('{event}', close{suffix})",
                CATEGORY_LISTENERS,
            )
        self.assertIn("boundary.contains(event.target)", CATEGORY_LISTENERS)
        self.assertIn(
            "getAttribute('aria-expanded') !== 'true'", CATEGORY_LISTENERS
        )
        self.assertIn("event.key === 'Escape'", CATEGORY_LISTENERS)
        self.assertIn("trigger.focus()", CATEGORY_LISTENERS)
        source = inspect.getsource(category_section)
        for token in [
            "on_mount=",
            "on_unmount=",
            'aria_controls="job-category-options"',
            'id="job-category-options"',
            'id="job-category-boundary"',
            "data-category-close",
        ]:
            self.assertIn(token, source)
        state = SimpleNamespace(category_dropdown_open=True)
        HelpPostState.close_category_dropdown.fn(state)
        HelpPostState.close_category_dropdown.fn(state)
        self.assertFalse(state.category_dropdown_open)

    def test_money_ui_and_toggles(self):
        self.assertIn("money", [r["value"] for r in REWARD_CHOICES])
        self.assertEqual(LEGACY_REWARD_TYPE["money"], "money")
        source = inspect.getsource(money_details_field)
        for token in [
            'contains("money")',
            'name="money_budget"',
            'min="0.01"',
            'step="0.01"',
            'max="99999999.99"',
            "disabled=HelpHubState.budget_quote_allowed",
            "Go and Help receives an 8% fee",
            "HelpHubState.reward_currency",
        ]:
            self.assertIn(token, source)
        self.assertIn(
            "disabled=HelpHubState.duration_quote_allowed",
            inspect.getsource(duration_field),
        )
        state = draft()
        HelpHubState.toggle_budget_quote.fn(state)
        HelpHubState.toggle_duration_quote.fn(state)
        self.assertTrue(
            state.budget_quote_allowed and state.duration_quote_allowed
        )
        HelpHubState.toggle_reward.fn(state, "money")
        self.assertFalse(state.budget_quote_allowed)
        HelpHubState.toggle_budget_quote.fn(state)
        self.assertFalse(state.budget_quote_allowed)
        HelpHubState.toggle_form.fn(state)
        self.assertFalse(state.duration_quote_allowed)
        self.assertFalse(state.rewards_open)
        self.assertEqual(state.posting_country, "")

    def test_decimal_validation(self):
        for raw in [
            "",
            "NaN",
            "Infinity",
            "-1",
            "0",
            "0.001",
            "1.234",
            "100000000",
            "1e2",
            "１２",
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                HelpHubState._money_details(True, False, raw, "USD")
        for raw in ["0.01", "12.5", "99999999.99"]:
            amount, summary = HelpHubState._money_details(
                True, False, raw, "USD"
            )
            self.assertEqual(amount, Decimal(raw))
            self.assertIn(f"USD {amount:.2f}", summary)
        self.assertEqual(
            HelpHubState._money_details(False, False, "stale", "USD"),
            (Decimal(0), ""),
        )
        self.assertIn(
            "quote requested",
            HelpHubState._money_details(True, True, "stale", "USD")[1],
        )
        self.assertIn("quoted", help_duration_label(0))
        self.assertIn("quoted", _hours_label(0, ""))
        self.assertEqual(_hours_label(90, ""), "1 hour 30 minutes for 1 day")


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def submit(self, state, data):
        session = Session()
        with (
            patch(
                "app.states.help_hub_state.rx.asession", return_value=session
            ),
            patch(
                "app.states.help_hub_state.check_post_allowance",
                new=AsyncMock(return_value=(True, False, 0, 3)),
            ),
        ):
            async for _ in HelpHubState.create_help_request.fn(state, data):
                pass
        return session

    async def test_existing_columns_and_budget_summary(self):
        state = draft()
        session = await self.submit(state, payload())
        self.assertTrue(session.calls)
        sql, params = session.calls[0]
        self.assertIn("INSERT INTO skillkind_help_post", sql)
        self.assertEqual(params["reward_value"], Decimal("12.50"))
        self.assertEqual(params["reward_types"], "money")
        self.assertEqual(params["reward_type"], "money")
        self.assertIn("USD 12.50 budget", params["reward_details"])
        self.assertEqual(params["duration"], 90)
        self.assertEqual(params["tools"], "")
        self.assertEqual(decode_knowledge(params["knowledge"]), ("", []))
        self.assertEqual(
            decode_duration_period(params["knowledge"]), (3, "week")
        )
        for field in [
            "reward_value",
            "reward_currency",
            "reward_details",
            "reward_types",
            "duration_minutes",
        ]:
            self.assertIn(field, sql)
        self.assertIn(":reward_currency", sql)
        self.assertEqual(params["reward_currency"], "USD")
        for forbidden in [
            "money_budget",
            "budget_quote_allowed",
            "duration_quote_allowed",
            "payment",
            "stripe",
            "payout",
        ]:
            self.assertNotIn(forbidden, sql.lower())
        self.assertFalse(state.form_open)
        self.assertFalse(state.rewards_open)
        self.assertEqual(state.posting_country, "")

    async def test_currency_override_bind_and_fallback(self):
        for code, expected in [("GBP", "GBP"), ("CAD", "CAD"), ("BAD", "USD")]:
            state = draft()
            state.reward_currency = code
            session = await self.submit(state, payload())
            sql, params = session.calls[0]
            self.assertIn(":reward_currency", sql)
            self.assertEqual(params["reward_currency"], expected)
            self.assertIn(expected, params["reward_details"])

    async def test_quotes_skip_stale_inputs_and_reset(self):
        state = draft()
        state.budget_quote_allowed = state.duration_quote_allowed = True
        data = payload()
        for key in [
            "money_budget",
            "duration_hours",
            "duration_minutes_part",
            "duration_period_count",
            "duration_period_unit",
        ]:
            data[key] = "invalid stale input"
        session = await self.submit(state, data)
        params = session.calls[0][1]
        self.assertEqual(params["reward_value"], Decimal(0))
        self.assertEqual(params["duration"], 0)
        self.assertEqual(
            decode_duration_period(params["knowledge"]), (3, "week")
        )
        self.assertIn("quote requested", params["reward_details"])
        self.assertFalse(
            state.budget_quote_allowed or state.duration_quote_allowed
        )

    async def test_validation_preserves_draft_and_never_writes(self):
        state = draft()
        state.duration_quote_allowed = True
        data = payload()
        data["money_budget"] = "1.234"
        with (
            self.assertNoLogs(level="WARNING"),
            self.assertNoLogs("app.states.help_hub_state", level="WARNING"),
        ):
            session = await self.submit(state, data)
        self.assertEqual(session.calls, [])
        self.assertTrue(state.duration_quote_allowed)
        self.assertEqual(state.selected_rewards, ["money"])
        self.assertIn("two decimal places", state.error)
        self.assertEqual(
            state.error,
            "Enter your budget in USD with at most two decimal places, or allow a Helper quote.",
        )
        self.assertEqual(state.missing_fields, [])
        self.assertEqual(state.success, "")
        self.assertFalse(state.is_saving)
        self.assertEqual(data["money_budget"], "1.234")
        self.assertTrue(state.form_open)


if __name__ == "__main__":
    unittest.main()
