import reflex as rx

import datetime
import unittest

from app.states.help_post_state import HelpPostState


class HelpDateBoundsTests(unittest.TestCase):
    def test_calendar_years_preserve_time(self):
        now = datetime.datetime(
            2026, 3, 1, 12, 34, 56, 789, tzinfo=datetime.UTC
        )
        self.assertEqual(
            HelpPostState._two_year_ceiling(now),
            datetime.datetime(2028, 3, 1, 12, 34, 56, 789, tzinfo=datetime.UTC),
        )

    def test_leap_day_clamps_to_last_valid_day(self):
        now = datetime.datetime(2028, 2, 29, 9, 30, tzinfo=datetime.UTC)
        self.assertEqual(
            HelpPostState._two_year_ceiling(now),
            datetime.datetime(2030, 2, 28, 9, 30, tzinfo=datetime.UTC),
        )

    def test_december_rollover(self):
        now = datetime.datetime(2026, 12, 31, 23, 59, tzinfo=datetime.UTC)
        ceiling = HelpPostState._two_year_ceiling(now)
        self.assertEqual(ceiling.year, 2028)
        self.assertEqual(ceiling.month, 12)
        self.assertEqual(ceiling.day, 31)
        self.assertIs(ceiling.tzinfo, datetime.UTC)


if __name__ == "__main__":
    unittest.main()
