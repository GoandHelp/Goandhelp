import reflex as rx

import datetime
import unittest

from app.help_languages import (
    PREFIX,
    PERIOD_PREFIX,
    decode_duration_period,
    decode_knowledge,
    encode_knowledge,
    encode_knowledge_with_period,
)
from app.states.help_hub_state import (
    HelpHubState,
    _hours_label,
    _schedule_parts,
)


class HelpHubControlsTests(unittest.TestCase):
    def test_clock_choices(self):
        state = HelpHubState()
        self.assertEqual(state.hour_choices, [f"{h:02d}" for h in range(24)])
        self.assertEqual(
            state.minute_choices,
            [f"{m:02d}" for m in range(0, 60, 5)],
        )

    def test_period_labels(self):
        for count in range(1, 8):
            options = HelpHubState._period_options(count)
            self.assertEqual(
                [item["value"] for item in options], ["day", "week", "month"]
            )
            self.assertEqual(
                [item["label"] for item in options],
                ["Day", "Week", "Month"]
                if count == 1
                else ["Days", "Weeks", "Months"],
            )

    def test_specific_time(self):
        self.assertEqual(
            HelpHubState._parse_start_time("specific", "09", "00"),
            (datetime.time(9), "09:00"),
        )
        self.assertEqual(
            HelpHubState._parse_start_time("specific", "23", "55")[1], "23:55"
        )
        for hour, minute in [
            ("24", "00"),
            ("09", "01"),
            ("９", "00"),
            ("-1", "00"),
            ("", "00"),
            ("09", "60"),
        ]:
            with (
                self.subTest(hour=hour, minute=minute),
                self.assertRaises(ValueError),
            ):
                HelpHubState._parse_start_time("specific", hour, minute)

    def test_flexible_time(self):
        self.assertEqual(
            HelpHubState._parse_start_time("flexible", "00", "00", "23", "55")[
                1
            ],
            "flex:00:00-23:55",
        )
        for end_hour, end_minute in [
            ("09", "00"),
            ("08", "55"),
            ("24", "00"),
            ("10", "03"),
            ("10", "６０"),
        ]:
            with (
                self.subTest(end_hour=end_hour, end_minute=end_minute),
                self.assertRaises(ValueError),
            ):
                HelpHubState._parse_start_time(
                    "flexible", "09", "00", end_hour, end_minute
                )

    def test_duration_validation(self):
        self.assertEqual(
            HelpHubState._parse_duration("0", "0", "1", "day"), (0, 1, "day")
        )
        self.assertEqual(
            HelpHubState._parse_duration("10", "55", "7", "month"),
            (655, 7, "month"),
        )
        for values in [
            ("11", "0", "1", "day"),
            ("1", "3", "1", "day"),
            ("1", "0", "0", "day"),
            ("1", "0", "8", "day"),
            ("1", "0", "1", "year"),
            ("１", "0", "1", "day"),
            ("1.0", "0", "1", "day"),
            ("-1", "0", "1", "day"),
        ]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                HelpHubState._parse_duration(*values)

    def test_period_metadata_round_trip(self):
        ordinary = "Careful hands\n日本語 and woodwork"
        for count in range(1, 8):
            for unit in ("day", "week", "month"):
                for codes in ([], ["pt", "en", "pt"]):
                    with self.subTest(count=count, unit=unit, codes=codes):
                        encoded = encode_knowledge_with_period(
                            ordinary, codes, count, unit
                        )
                        self.assertTrue(encoded.startswith(PERIOD_PREFIX))
                        self.assertEqual(
                            decode_duration_period(encoded), (count, unit)
                        )
                        visible, languages = decode_knowledge(encoded)
                        self.assertEqual(visible, ordinary)
                        self.assertEqual(languages, sorted(set(codes)))
                        self.assertNotIn(PREFIX, visible)
                        self.assertNotIn(PERIOD_PREFIX, visible)

    def test_legacy_metadata_compatibility(self):
        self.assertEqual(encode_knowledge("Skills", []), "Skills")
        self.assertEqual(
            encode_knowledge("Skills", ["en"]), f'{PREFIX}["en"]\nSkills'
        )
        for stored in (None, "", "Skills", encode_knowledge("Skills", ["en"])):
            self.assertEqual(decode_duration_period(stored), (1, "day"))
        for prefix in (PREFIX, PERIOD_PREFIX):
            ordinary = f"{prefix}literal text\nMore skills"
            encoded = encode_knowledge_with_period(ordinary, [], 2, "week")
            self.assertEqual(decode_knowledge(encoded), (ordinary, []))

    def test_period_metadata_validation(self):
        for count in (0, 8, -1, True, 1.0, "1", None):
            with self.subTest(count=count), self.assertRaises(ValueError):
                encode_knowledge_with_period("Skills", [], count, "day")
        for unit in ("year", "days", "Day", "", None, 1):
            with self.subTest(unit=unit), self.assertRaises(ValueError):
                encode_knowledge_with_period("Skills", [], 1, unit)
        with self.assertRaises(ValueError):
            encode_knowledge_with_period("Skills", ["invalid"], 1, "day")

    def test_malformed_period_metadata_hidden(self):
        for payload in (
            "not json",
            "null",
            "[]",
            "{}",
            '{"count":0,"unit":"day"}',
            '{"count":8,"unit":"week"}',
            '{"count":true,"unit":"day"}',
            '{"count":1.0,"unit":"day"}',
            '{"count":"1","unit":"day"}',
            '{"count":1,"unit":"year"}',
        ):
            stored = f'{PERIOD_PREFIX}{payload}\n{PREFIX}["en"]\nSkills'
            with self.subTest(payload=payload):
                self.assertEqual(decode_duration_period(stored), (1, "day"))
                self.assertEqual(decode_knowledge(stored), ("Skills", ["en"]))
        unterminated = f'{PERIOD_PREFIX}{{"count":3,"unit":"week"}}'
        self.assertEqual(decode_duration_period(unterminated), (1, "day"))
        self.assertEqual(decode_knowledge(unterminated), ("", []))

    def test_duration_display(self):
        for minutes, count, unit, expected in (
            (60, 1, "day", "1 hour for 1 day"),
            (150, 3, "week", "2 hours 30 minutes for 3 weeks"),
            (5, 7, "month", "5 minutes for 7 months"),
            (1, 1, "month", "1 minute for 1 month"),
            (0, 3, "week", "Duration to be agreed / quoted"),
        ):
            stored = encode_knowledge_with_period("Skills", [], count, unit)
            with self.subTest(minutes=minutes, count=count, unit=unit):
                self.assertEqual(_hours_label(minutes, stored), expected)
                self.assertEqual(
                    _schedule_parts(None, "", "", minutes, stored)[0], expected
                )
        self.assertEqual(_hours_label(60, "Legacy skills"), "1 hour for 1 day")
        self.assertEqual(
            _hours_label(0, "Legacy skills"), "Duration to be agreed / quoted"
        )


if __name__ == "__main__":
    unittest.main()
