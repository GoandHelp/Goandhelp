import inspect
import unittest

from app.states.auth_state import AuthState
from app.states.event_state import (
    EventState,
    _safe_range_dates,
    _safe_timezone_name,
)


class TargetedRepairTests(unittest.TestCase):
    def test_invalid_timezone_falls_back_and_valid_timezone_is_preserved(self):
        self.assertEqual(_safe_timezone_name("Not/A_Zone"), "UTC")
        self.assertEqual(
            _safe_timezone_name("America/New_York"), "America/New_York"
        )

    def test_range_contract_uses_independent_date_casts(self):
        source = inspect.getsource(EventState.load_events.fn)
        self.assertIn("CAST(:range_start AS date)", source)
        self.assertIn("CAST(:range_end AS date)", source)
        self.assertNotIn("COALESCE(NULLIF(:range_end", source)
        self.assertNotIn("NULLIF(:range_end", source)

    def test_range_parameters_never_bind_empty_dates(self):
        self.assertEqual(
            _safe_range_dates("", ""), ("1970-01-01", "1970-01-01")
        )
        self.assertEqual(
            _safe_range_dates("2026-09-26", ""),
            ("2026-09-26", "2026-09-26"),
        )
        self.assertEqual(
            _safe_range_dates("2026-09-26", "not-a-date"),
            ("2026-09-26", "2026-09-26"),
        )

    def test_sign_in_closes_loading_gate_after_onboarding(self):
        source = inspect.getsource(AuthState.sign_in.fn)
        hydration = source.index("_resolve_progress")
        loading_reset = source.index("self.checking_session = False")
        self.assertLess(hydration, loading_reset)
        self.assertIn("finally:", source)
        self.assertIn(
            "finally:\n            async with self:\n                self.checking_session = False",
            source,
        )


if __name__ == "__main__":
    unittest.main()
