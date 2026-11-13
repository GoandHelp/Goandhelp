import reflex as rx

import inspect
import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.countries import (
    WORLD_COUNTRY_NAMES,
    STRIPE_CURRENCIES,
    country_default_currency,
    supported_currency,
)
from app.states.discovery_state import DiscoveryState, EMPTY_POST
from app.states.help_hub_state import HelpHubState
from app.states.help_post_state import HelpPostState
from app.components.discover_panel import offer_help_section, offer_estimates
from app.components.help_hub_panel import (
    help_summary_card,
    help_summary_row,
    start_time_field,
    duration_field,
    help_day_field,
)
from app.components.help_post_panel import photo_upload_section


class QuoteCompletionTests(unittest.TestCase):
    def test_currency_defaults(self):
        for country in WORLD_COUNTRY_NAMES:
            self.assertIn(country_default_currency(country), STRIPE_CURRENCIES)
        for country, code in [
            ("UK", "GBP"),
            ("Germany", "EUR"),
            ("Canada", "CAD"),
            ("Australia", "AUD"),
            ("Japan", "JPY"),
            ("India", "INR"),
            ("unknown", "USD"),
        ]:
            self.assertEqual(country_default_currency(country), code)
        self.assertEqual(supported_currency(" btc "), "USD")
        state = SimpleNamespace(
            posting_country="", reward_currency="USD", error=""
        )
        HelpHubState.set_posting_country.fn(state, "Canada")
        self.assertEqual(state.reward_currency, "CAD")
        HelpHubState.set_reward_currency.fn(state, "EUR")
        self.assertEqual(state.reward_currency, "EUR")
        HelpHubState.set_posting_country.fn(state, "Japan")
        self.assertEqual(state.reward_currency, "JPY")

    def test_quote_contract_and_format(self):
        allowed = DiscoveryState._quote_allowed
        self.assertTrue(
            allowed(
                "meal,money",
                "dinner",
                0,
                "Money (GBP — Helper quote requested)",
            )
        )
        self.assertTrue(allowed("", "money", 0, "Helper quote requested"))
        for types, legacy, amount, details in [
            ("meal", "money", 0, "Helper quote requested"),
            ("money", "money", 1, "Helper quote requested"),
            ("money", "money", 0, "Free"),
        ]:
            self.assertFalse(allowed(types, legacy, amount, details))
        post = {
            **EMPTY_POST,
            "allow_price_quote": True,
            "allow_duration_estimate": True,
            "reward_currency": "GBP",
        }
        self.assertEqual(
            DiscoveryState._offer_quote_lines(post, "12", "1", "5"),
            "Price quote: 12 GBP\nDuration estimate: 1 hours 5 minutes for 1 day",
        )
        for price in ["", "0", "-1", "NaN", "1e2", "1.234", "１２"]:
            with self.assertRaises(ValueError):
                DiscoveryState._offer_quote_lines(post, price, "1", "0")
        for hours, minutes in [
            ("0", "0"),
            ("1", "60"),
            ("1.5", "0"),
            ("-1", "0"),
        ]:
            with self.assertRaises(ValueError):
                DiscoveryState._offer_quote_lines(post, "1", hours, minutes)
        self.assertEqual(
            DiscoveryState._offer_quote_lines(EMPTY_POST, "bad", "bad", "bad"),
            "",
        )
        state = SimpleNamespace()
        DiscoveryState._reset_offer_draft(state)

        DiscoveryState.set_offer_price.fn(state, "12")
        DiscoveryState.set_offer_hours.fn(state, "2")
        DiscoveryState.set_offer_minutes.fn(state, "30")
        self.assertEqual(
            (state.offer_price, state.offer_hours, state.offer_minutes),
            ("12", "2", "30"),
        )
        DiscoveryState._reset_offer_draft(state)
        self.assertEqual(
            (state.offer_price, state.offer_hours, state.offer_minutes),
            ("", "0", "0"),
        )

    def test_numeric_duration_setters(self):
        state = SimpleNamespace()
        for handler, field, valid, invalid in [
            (
                DiscoveryState.set_offer_hours,
                "offer_hours",
                ("0", "2", "10"),
                ("11", "-1", "2.5"),
            ),
            (
                DiscoveryState.set_offer_minutes,
                "offer_minutes",
                ("0", "5", "55"),
                ("3", "59", "60"),
            ),
        ]:
            for value in valid:
                handler.fn(state, value)
                self.assertEqual(getattr(state, field), value)
            for value in invalid:
                handler.fn(state, value)
                self.assertEqual(getattr(state, field), "")

    def test_ui_contracts(self):
        source = inspect.getsource(offer_help_section)
        self.assertLess(
            source.index("rx.el.textarea"), source.index("offer_estimates()")
        )
        self.assertLess(
            source.index("offer_estimates()"), source.index('"Offer help"')
        )
        self.assertIn("offer_can_send", source)
        estimates = inspect.getsource(offer_estimates)
        self.assertIn('selected_post["allow_price_quote"]', estimates)
        self.assertIn('selected_post["allow_duration_estimate"]', estimates)
        metric = inspect.getsource(help_summary_card)
        for token in [
            '" help given"',
            '" help received"',
            '"Helped"',
            '"Received help"',
            '" "',
            '" time"',
            '" times"',
            "text-base sm:text-lg",
        ]:
            self.assertIn(token, metric)
        self.assertNotIn('class_name="flex', metric)
        self.assertIn(
            "grid-cols-2 gap-x-6", inspect.getsource(help_summary_row)
        )
        self.assertNotIn(
            "border-[#e08b12]", inspect.getsource(help_summary_row)
        )
        self.assertIn("bg-transparent", inspect.getsource(help_summary_row))
        self.assertIn("rounded-xl bg-white", metric)
        for component in [start_time_field, duration_field, help_day_field]:
            self.assertIn(
                "justify-start text-left", inspect.getsource(component)
            )
        self.assertNotIn("bg-[#fff7e8]", inspect.getsource(duration_field))
        upload = inspect.getsource(photo_upload_section)
        for token in [
            "photo_busy",
            "Pictures are being uploaded",
            "BRAND_LOGO_SRC",
            "motion-safe:animate-pulse",
        ]:
            self.assertIn(token, upload)


class UploadLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def upload_state(self):
        state = SimpleNamespace(
            photo_busy=False,
            photo_error="",
            photo_notice="",
            pending_photo_paths=[],
        )
        state._process_photos = MethodType(HelpPostState._process_photos, state)
        return state

    async def test_oversized_source_is_rejected_without_error_logging(self):
        state = self.upload_state()
        upload = SimpleNamespace(
            name="large-photo.jpg",
            content_type="image/jpeg",
            size=3_000_001,
            read=AsyncMock(return_value=b""),
        )
        with (
            patch("app.states.help_post_state.rx.get_upload_dir"),
            self.assertNoLogs(level="ERROR"),
        ):
            handler = HelpPostState.handle_upload.fn(state, [upload])
            await anext(handler)
            self.assertTrue(state.photo_busy)
            async for _ in handler:
                pass
        self.assertFalse(state.photo_busy)
        self.assertEqual(state.pending_photo_paths, [])
        self.assertEqual(state.photo_notice, "")
        self.assertIn("large-photo.jpg", state.photo_error)
        self.assertIn("static JPEG/JPG, PNG or WebP", state.photo_error)
        self.assertIn("maximum 3 MB per source", state.photo_error)
        self.assertNotIn("Source photo exceeds 3 MB", state.photo_error)
        upload.read.assert_not_awaited()

    async def test_unexpected_read_failure_is_logged_and_rejected(self):
        state = self.upload_state()
        upload = SimpleNamespace(
            name="unreadable.jpg",
            content_type="image/jpeg",
            size=100,
            read=AsyncMock(
                side_effect=OSError("Unexpected upload read failure")
            ),
        )
        with (
            patch("app.states.help_post_state.rx.get_upload_dir"),
            self.assertLogs(level="ERROR") as captured,
        ):
            handler = HelpPostState.handle_upload.fn(state, [upload])
            await anext(handler)
            self.assertTrue(state.photo_busy)
            async for _ in handler:
                pass
        self.assertFalse(state.photo_busy)
        self.assertEqual(state.pending_photo_paths, [])
        self.assertEqual(state.photo_notice, "")
        self.assertIn("Couldn't accept unreadable.jpg", state.photo_error)
        self.assertIn("maximum 3 MB per source", state.photo_error)
        self.assertNotIn("Unexpected upload read failure", state.photo_error)
        self.assertTrue(
            any(
                "Unexpected upload read failure" in record.getMessage()
                and record.exc_info is not None
                for record in captured.records
            )
        )
        upload.read.assert_awaited_once_with(3_000_001)

    async def test_busy_clears_on_success_and_failure(self):
        for failure in [False, True]:
            state = SimpleNamespace(
                photo_busy=False,
                photo_error="",
                _process_photos=AsyncMock(
                    side_effect=ValueError("rejected") if failure else None
                ),
            )
            handler = HelpPostState.handle_upload.fn(state, [])
            await anext(handler)
            self.assertTrue(state.photo_busy)
            if failure:
                with self.assertLogs(level="ERROR"):
                    async for _ in handler:
                        pass
            else:
                async for _ in handler:
                    pass
            self.assertFalse(state.photo_busy)


if __name__ == "__main__":
    unittest.main()
