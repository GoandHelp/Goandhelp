import datetime
import json
import re
from collections import Counter
import subprocess
import unittest

import reflex as rx

from app.components.help_post_metadata import (
    localized_date_time,
    localized_metadata,
    localized_reward,
)
from app.components.help_post_panel import (
    option_item,
    post_card,
    repeat_section,
    schedule_card,
)
from app.interface_catalog_help_post_category_hints import (
    HELP_POST_CATEGORY_HINT_CATALOGS,
    HELP_POST_CATEGORY_HINT_KEYS,
)
from app.interface_catalog_help_post_metadata import (
    HELP_POST_METADATA_CATALOGS,
    HELP_POST_METADATA_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.help_post_state import (
    HelpPostState,
    RecentPost,
    RecurringSummary,
)

EXPECTED_CHOICES = (
    "1 day",
    "1 hour",
    "15 min",
    "2 hours",
    "3 hours",
    "30 min",
    "4 hours",
    "5 hours",
    "6 hours",
    "7 hours",
    "Daily",
    "Every two weeks",
    "Flexible — any time works",
    "Monthly",
    "Same date each month",
    "Same time every day",
    "Same weekday each week",
    "Same weekday, fortnightly",
    "Soon — within a few days",
    "Urgent — I need help now",
    "Weekly",
)
EXPECTED_METADATA = (
    *EXPECTED_CHOICES,
    "One-time request",
    "Every day",
    "Every week",
    "Every month",
    "Every {count} days",
    "Every {count} weeks",
    "Every {count} months",
    "Active",
    "Paused",
    "Ended",
    "No further dates",
    "No end date",
    "Time to agree",
    "Reward: {reward}",
    "Reward: {amount}{currency}",
    "Reward: Quote requested ({currency}).",
)
EXPECTED_HINTS = (
    "Choose 1 category. Select or unselect an option. Premium members can add up to 3.",
    "{chosen} of {limit} chosen — you can add {left} more.",
    "Free members choose {limit} category. Tap it again to swap it, or go premium for up to 3.",
    "All {limit} categories chosen. Unselect one to swap it.",
    "required — choose 1",
    "required — choose 1 to {limit}",
)


def replace_catalog_lookups(
    expression: str, locale: str, keys: tuple[str, ...]
) -> str:
    for key in keys:
        expression = expression.replace(
            str(ui(key)), json.dumps(translate(locale, key), ensure_ascii=False)
        )
    return expression.replace(
        str(AuthState.preferred_language), json.dumps(locale)
    )


def node_values(expressions: list[str]) -> list[str]:
    result = subprocess.run(
        [
            "node",
            "-e",
            "process.stdout.write(JSON.stringify(JSON.parse(process.argv[1]).map(expression => eval(expression))))",
            json.dumps(expressions, ensure_ascii=False),
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


class HelpPostMetadataTranslationTests(unittest.TestCase):
    def test_complete_catalog_sources_native_rows_and_fallbacks(self):
        self.assertEqual(HELP_POST_METADATA_KEYS, EXPECTED_METADATA)
        self.assertEqual(HELP_POST_CATEGORY_HINT_KEYS, EXPECTED_HINTS)
        offered = {code for code, _ in LANGUAGE_OPTIONS}
        native_codes = offered - {"en"}
        self.assertEqual(len(offered), 37)
        self.assertEqual(set(HELP_POST_METADATA_CATALOGS), native_codes)
        self.assertEqual(set(HELP_POST_CATEGORY_HINT_CATALOGS), native_codes)
        self.assertTrue(
            set(EXPECTED_METADATA + EXPECTED_HINTS) <= set(COMPLETE_KEYS)
        )
        for catalogs, sources in (
            (HELP_POST_METADATA_CATALOGS, EXPECTED_METADATA),
            (HELP_POST_CATEGORY_HINT_CATALOGS, EXPECTED_HINTS),
        ):
            for locale in native_codes:
                self.assertEqual(set(catalogs[locale]), set(sources))
                for source, value in catalogs[locale].items():
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())
                    self.assertIn(source, CATALOGS[locale])
                    runtime_value = CATALOGS[locale][source]
                    self.assertIsInstance(runtime_value, str)
                    self.assertTrue(runtime_value.strip())
                    self.assertEqual(translate(locale, source), runtime_value)
                    source_slots = Counter(
                        re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)
                    )
                    translated_slots = Counter(
                        re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", value)
                    )
                    runtime_slots = Counter(
                        re.findall(
                            r"\{([A-Za-z][A-Za-z0-9_]*)\}", runtime_value
                        )
                    )
                    self.assertEqual(translated_slots, source_slots)
                    self.assertEqual(runtime_slots, source_slots)
        for key in EXPECTED_METADATA + EXPECTED_HINTS:
            self.assertEqual(translate("en", key), key)
            self.assertEqual(translate("unlisted-locale", key), key)

    def test_real_form_choices_and_repeat_templates_render_for_every_locale(
        self,
    ):
        state = HelpPostState()
        actual_choices = {
            item["label"]
            for group in (
                state.duration_options,
                state.urgency_options,
                state.cadence_choices,
            )
            for item in group
        }
        self.assertTrue(set(EXPECTED_CHOICES) <= set(HELP_POST_METADATA_KEYS))
        self.assertTrue(actual_choices <= set(COMPLETE_KEYS))
        for locale in HELP_POST_METADATA_CATALOGS:
            for key in actual_choices:
                self.assertIn(key, CATALOGS[locale])
                self.assertTrue(CATALOGS[locale][key].strip())
                self.assertEqual(translate(locale, key), CATALOGS[locale][key])

        keys = tuple(EXPECTED_METADATA) + tuple(actual_choices)
        cases = tuple(
            (
                f"Every {count} {unit}",
                f"Every {{count}} {unit}",
                {"count": str(count)},
            )
            for unit in ("days", "weeks", "months")
            for count in (1, 2, 52)
        )
        for locale in ("en", "fr", "ar", "ja"):
            expressions = []
            expected = []
            for source, template, slots in cases:
                expression = replace_catalog_lookups(
                    str(localized_metadata(source)), locale, keys
                )
                expressions.append(expression)
                translated = translate(locale, template)
                expected.append(translated.replace("{count}", slots["count"]))
            any_label = "Any"
            expressions.append(
                replace_catalog_lookups(
                    str(localized_metadata(any_label)), locale, keys
                )
            )
            expected.append(translate(locale, any_label))
            unknown = "Every 2 fortnights"
            expressions.append(
                replace_catalog_lookups(
                    str(localized_metadata(unknown)), locale, keys
                )
            )
            expected.append(unknown)
            self.assertEqual(node_values(expressions), expected)

        rendered = option_item({"label": "1 day", "value": "1440"})
        self.assertIsNotNone(rendered)
        self.assertIsNotNone(repeat_section())

    def test_reward_values_localize_owned_copy_and_preserve_member_payloads(
        self,
    ):
        fixtures = (
            ("Reward: Lunch", False, "Reward: {reward}", "Lunch"),
            ("Reward: 125USD", False, "Reward: {amount}{currency}", "125USD"),
            (
                "Reward: Quote requested (EUR)",
                False,
                "Reward: Quote requested ({currency}).",
                "EUR",
            ),
            ("Reward: Lunch", True, "Reward: {reward}", "Lunch"),
            ("Reward: Cancel", True, "Reward: {reward}", "Cancel"),
            (
                "Reward: line one\n$& {count} {reward} ☃",
                True,
                "Reward: {reward}",
                "line one\n$& {count} {reward} ☃",
            ),
            (
                "Reward: unknown custom 🧭",
                False,
                "Reward: {reward}",
                "unknown custom 🧭",
            ),
        )
        keys = tuple(EXPECTED_METADATA) + (
            "Lunch",
            "Dinner",
            "Accommodation",
            "Guided tours",
            "Workshops",
            "Lessons",
            "Other",
            "Meal",
            "Free",
        )
        for locale in ("en", "fr", "ar", "ja"):
            expressions = []
            expected = []
            for label, custom, template, value in fixtures:
                expression = replace_catalog_lookups(
                    str(localized_reward(label, custom)), locale, keys
                )
                expressions.append(expression)
                translated = translate(locale, template)
                reward_value = (
                    translate(locale, value)
                    if not custom and value == "Lunch"
                    else value
                )
                expected.append(
                    translated.replace("{reward}", reward_value)
                    .replace("{amount}", "125")
                    .replace("{currency}", "USD" if "125" in value else value)
                )
            self.assertEqual(node_values(expressions), expected)

    def test_iso_dates_use_native_icu_utc_gregorian_formatting(self):
        instant = "2032-02-29T00:15:00+00:00"
        end_date = "2032-02-29"
        locales = ("en", "fr", "ar", "ja")
        expressions: list[str] = []
        for locale in locales:
            expressions.extend(
                [
                    replace_catalog_lookups(
                        str(localized_date_time(instant)),
                        locale,
                        EXPECTED_METADATA,
                    ),
                    replace_catalog_lookups(
                        str(localized_date_time(end_date, date_only=True)),
                        locale,
                        EXPECTED_METADATA,
                    ),
                    replace_catalog_lookups(
                        str(localized_date_time("")), locale, EXPECTED_METADATA
                    ),
                ]
            )
        actual = node_values(expressions)
        expected = []
        for locale in locales:
            day = (
                subprocess.run(
                    [
                        "node",
                        "-e",
                        "const d=new Date(process.argv[1]);const l=process.argv[2];const o={calendar:'gregory',timeZone:'UTC',year:'numeric',month:'short',day:'numeric'};const t={calendar:'gregory',timeZone:'UTC',hour:'2-digit',minute:'2-digit',hourCycle:'h23'};process.stdout.write(new Intl.DateTimeFormat(l,o).format(d)+' · '+new Intl.DateTimeFormat(l,t).format(d)+'\\n'+new Intl.DateTimeFormat(l,o).format(new Date(process.argv[3])))",
                        instant,
                        locale,
                        end_date,
                    ],
                    capture_output=True,
                    check=True,
                    text=True,
                )
                .stdout.rstrip("\n")
                .split("\n")
            )
            expected.extend(
                [day[0], day[1], translate(locale, "Time to agree")]
            )
        self.assertEqual(actual, expected)
        self.assertEqual(
            datetime.datetime.fromisoformat(instant).isoformat(), instant
        )
        self.assertEqual(end_date, "2032-02-29")

    def test_real_row_mappers_add_display_only_fields_and_keep_existing_values(
        self,
    ):
        scheduled = datetime.datetime(2032, 2, 29, 0, 15, tzinfo=datetime.UTC)
        created = datetime.datetime(2031, 8, 1, tzinfo=datetime.UTC)
        row = [
            51,
            "Member's exact title",
            "Member's exact description",
            "cook",
            "other",
            "Lunch\n$& {count}",
            "Rua Example 7",
            "Porto",
            scheduled,
            "open",
            "soon",
            created,
            2,
            90,
            "tools",
            "skills",
            "accepted place",
            "",
            "",
            True,
            "other",
            0,
            "USD",
        ]
        mapped = HelpPostState()._row_to_post(row, [])
        self.assertEqual(mapped["title"], row[1])
        self.assertEqual(mapped["description"], row[2])
        self.assertEqual(mapped["location"], "Rua Example 7, Porto")
        self.assertEqual(mapped["reward_details"], "")
        self.assertEqual(mapped["reward_label"], "Reward: Lunch\n$& {count}")
        self.assertTrue(mapped["is_custom_reward"])
        self.assertEqual(
            mapped["scheduled"], scheduled.strftime("%b %d, %Y · %H:%M")
        )
        self.assertEqual(mapped["scheduled_iso"], scheduled.isoformat())
        self.assertEqual(mapped["status"], "open")

        schedule_row = [
            9,
            "Member's title",
            "weekly",
            2,
            "active",
            scheduled,
            datetime.date(2032, 3, 31),
            4,
        ]
        schedule = HelpPostState._row_to_schedule(schedule_row)
        self.assertEqual(schedule["title"], schedule_row[1])
        self.assertEqual(schedule["cadence"], "weekly")
        self.assertEqual(schedule["status"], "active")
        self.assertEqual(
            schedule["next_label"], scheduled.strftime("%b %d, %Y · %H:%M")
        )
        self.assertEqual(schedule["end_label"], "Mar 31, 2032")
        self.assertEqual(schedule["next_iso"], scheduled.isoformat())
        self.assertEqual(schedule["end_iso"], "2032-03-31")
        self.assertEqual(schedule["count"], 4)

        no_dates = HelpPostState._row_to_schedule(
            [10, "No dates", "weekly", 1, "completed", None, None, 0]
        )
        self.assertEqual(no_dates["next_label"], "No further dates")
        self.assertEqual(no_dates["end_label"], "No end date")
        self.assertEqual(no_dates["next_iso"], "")
        self.assertEqual(no_dates["end_iso"], "")

    def test_scoped_consumers_and_reactive_language_dependencies(self):
        fixtures = {
            "id": 1,
            "title": "Member title",
            "description": "Member description",
            "category": "cook",
            "category_label": "Cook",
            "reward_label": "Reward: Lunch",
            "reward_details": "",
            "is_custom_reward": False,
            "location": "Member place",
            "scheduled": "Feb 29, 2032 · 00:15",
            "scheduled_iso": "2032-02-29T00:15:00+00:00",
            "status": "open",
            "urgency": "flexible",
            "created": "",
            "photos": [],
            "helpers_needed": 1,
            "duration_minutes": 60,
            "tools": "",
            "knowledge_skills": "",
            "accepted_location_name": "",
            "date_time_duration": "",
            "can_edit": False,
        }
        self.assertIsNotNone(post_card(rx.Var.create(fixtures).to(RecentPost)))
        self.assertIsNotNone(
            schedule_card(
                rx.Var.create(
                    {
                        "id": 1,
                        "title": "Recurring title",
                        "cadence": "weekly",
                        "cadence_label": "Every 2 weeks",
                        "status": "active",
                        "status_label": "Active",
                        "next_label": "Feb 29, 2032 · 00:15",
                        "end_label": "No end date",
                        "next_iso": "2032-02-29T00:15:00+00:00",
                        "end_iso": "",
                        "count": 2,
                        "is_active": True,
                        "is_paused": False,
                        "is_ended": False,
                    }
                ).to(RecurringSummary)
            )
        )
        metadata_dependencies = str(
            localized_metadata(HelpPostState.repeat_summary)._get_all_var_data()
        )
        self.assertIn("interface_text", metadata_dependencies)
        self.assertIn("repeat_summary", metadata_dependencies)
        reward_dependencies = str(
            localized_reward(
                HelpPostState.repeat_summary, False
            )._get_all_var_data()
        )
        self.assertIn("interface_text", reward_dependencies)
        date_dependencies = str(
            localized_date_time(HelpPostState.schedule_min)._get_all_var_data()
        )
        self.assertIn("interface_text", date_dependencies)
        self.assertIn("preferred_language", date_dependencies)


if __name__ == "__main__":
    unittest.main()
