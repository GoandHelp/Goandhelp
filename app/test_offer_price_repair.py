import reflex as rx

import ast
import inspect
import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.components.discover_panel import offer_estimates, offer_help_section
from app.states.discovery_state import DiscoveryState, EMPTY_POST


class OfferPriceTests(unittest.TestCase):
    def test_locale_prices_and_canonical_state(self):
        post = {
            **EMPTY_POST,
            "allow_price_quote": True,
            "reward_currency": "EUR",
        }
        for raw, canonical, formatted in [
            ("12", "12", "12"),
            ("500", "500", "500"),
            ("99999999", "99999999", "99999999"),
        ]:
            with self.subTest(raw=raw):
                state = SimpleNamespace(offer_price="")
                DiscoveryState.set_offer_price.fn(state, raw)
                self.assertEqual(state.offer_price, canonical)
                for value in (raw, state.offer_price):
                    self.assertEqual(
                        DiscoveryState._offer_quote_lines(
                            post, value, "0", "0"
                        ),
                        f"Price quote: {formatted} EUR",
                    )

    def test_invalid_formats_remain_invalid(self):
        post = {**EMPTY_POST, "allow_price_quote": True}
        for raw in (
            "",
            "0",
            "0.00",
            "0,00",
            "-1",
            "-0,01",
            "+12",
            "1e2",
            "1E2",
            "NaN",
            "Infinity",
            "-Infinity",
            "inf",
            "100000000",
            "100000000,00",
            "12.500",
            "12,500",
            "12.50",
            "12,50",
            "1,234.50",
            "1.234,50",
            "1,2,3",
            "1..2",
            ".50",
            ",50",
            "12.",
            "12,",
            "１２",
            "1 2",
        ):
            with self.subTest(raw=raw), self.assertNoLogs(level="ERROR"):
                state = SimpleNamespace(offer_price="")
                DiscoveryState.set_offer_price.fn(state, raw)
                for value in (raw, state.offer_price):
                    with self.assertRaisesRegex(
                        ValueError, "positive whole-number price quote"
                    ):
                        DiscoveryState._offer_quote_lines(post, value, "0", "0")

    def test_quote_controls_dispatch_immediately_and_message_is_unchanged(self):
        tree = ast.parse(inspect.getsource(offer_estimates))
        changes = [
            ast.unparse(keyword.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for keyword in node.keywords
            if keyword.arg == "on_change"
        ]
        self.assertCountEqual(
            changes,
            [
                "DiscoveryState.set_offer_price_number",
                "DiscoveryState.set_offer_hours",
                "DiscoveryState.set_offer_minutes",
                "DiscoveryState.set_offer_period_count",
                "DiscoveryState.set_offer_period_unit",
            ],
        )
        self.assertIn(
            "DiscoveryState.set_offer_draft.debounce(300)",
            inspect.getsource(offer_help_section),
        )
        self.assertIsInstance(DiscoveryState.send_offer, rx.event.EventHandler)
        for helper in (
            "_send_offer",
            "_offer_quote_lines",
            "_normalized_offer_price",
        ):
            self.assertFalse(
                isinstance(
                    getattr(DiscoveryState, helper), rx.event.EventHandler
                )
            )


class OfferContext(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class AuthoritativeQuoteTests(unittest.IsolatedAsyncioTestCase):
    async def test_stale_requirements_are_correctable_without_writes_or_error_logs(
        self,
    ):
        for wrapper in (False, True):
            for duration in (False, True):
                with self.subTest(wrapper=wrapper, duration=duration):
                    state = OfferContext(
                        selected_post={**EMPTY_POST, "id": 17, "poster_id": 23},
                        offer_draft="I can help with this request.",
                        offer_price="",
                        offer_hours="0",
                        offer_minutes="0",
                        offer_period_count="1",
                        offer_period_unit="days",
                        offer_open=True,
                        is_sending_offer=False,
                        error="",
                        success="Old success",
                        get_state=AsyncMock(
                            return_value=SimpleNamespace(subscriber_id="42")
                        ),
                        _offer_quote_lines=DiscoveryState._offer_quote_lines,
                        _quote_allowed=DiscoveryState._quote_allowed,
                    )
                    state._send_offer = MethodType(
                        DiscoveryState._send_offer, state
                    )
                    row = (
                        "open",
                        23,
                        "Request",
                        1,
                        "meal" if duration else "money",
                        "meal" if duration else "money",
                        0,
                        "" if duration else "Helper quote requested",
                        0 if duration else 60,
                        "EUR",
                    )
                    session = MagicMock()
                    session.__aenter__ = AsyncMock(return_value=session)
                    session.__aexit__ = AsyncMock(return_value=False)
                    session.rollback = AsyncMock()
                    session.commit = AsyncMock()

                    async def read_only(statement, params):
                        self.assertTrue(state.is_sending_offer)
                        self.assertTrue(
                            str(statement).strip().startswith("SELECT")
                        )
                        self.assertIn("FOR UPDATE", str(statement))
                        # Ensure the validation branch itself clears any success.
                        state.success = "Stale success"
                        return SimpleNamespace(first=lambda: row)

                    session.execute = AsyncMock(side_effect=read_only)
                    with (
                        patch(
                            "app.states.discovery_state.rx.asession",
                            return_value=session,
                        ),
                        self.assertNoLogs(level="ERROR"),
                    ):
                        events = []
                        handler = (
                            DiscoveryState.send_offer.fn(state)
                            if wrapper
                            else state._send_offer()
                        )
                        async for event in handler:
                            events.append(event)
                    self.assertEqual(events, [])
                    self.assertFalse(state.is_sending_offer)
                    self.assertEqual(state.success, "")
                    self.assertIn(
                        "at least one minute"
                        if duration
                        else "positive whole-number price quote",
                        state.error,
                    )
                    self.assertTrue(state.offer_open)
                    self.assertEqual(state.selected_post["id"], 17)
                    self.assertTrue(
                        state.selected_post[
                            "allow_duration_estimate"
                            if duration
                            else "allow_price_quote"
                        ]
                    )
                    self.assertEqual(
                        state.selected_post["reward_currency"], "EUR"
                    )
                    self.assertEqual(
                        state.offer_draft, "I can help with this request."
                    )
                    session.execute.assert_awaited_once()
                    session.rollback.assert_awaited_once()
                    session.commit.assert_not_awaited()
                    session.__aexit__.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
