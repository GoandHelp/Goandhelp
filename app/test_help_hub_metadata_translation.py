import ast
import json
import re
import shutil
import subprocess
import unittest
import unicodedata
from collections import Counter
from pathlib import Path

import reflex as rx

from app.components.help_hub_metadata import (
    DATE_ERROR_SOURCES,
    DURATION_UNIT_CATALOGS,
    PRIVACY_SOURCE,
    localized_calendar_accessible_date,
    localized_calendar_month,
    localized_date_error,
    localized_date_trigger,
    localized_date_value,
    localized_duration_unit,
    localized_flexible_summary,
    localized_help_privacy,
    localized_rewards_summary,
    localized_selected_date_count,
)
from app.components.help_hub_panel import (
    calendar_day,
    date_chip,
    duration_field,
    help_day_field,
    inline_help_calendar,
    post_help_form,
    rewards_field,
)
from app.interface_catalog_help_hub_metadata import (
    HELP_HUB_METADATA_CATALOGS,
    HELP_HUB_METADATA_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.help_hub_state import FLEXIBLE_CHOICES, REWARD_CHOICES, WEEKDAYS


EXPECTED_METADATA_KEYS = (
    "Any Day",
    "Any weekday",
    "Any weekend",
    "Custom",
    "Mondays",
    "Tuesdays",
    "Wednesdays",
    "Thursdays",
    "Fridays",
    "Saturdays",
    "Sundays",
    "Day",
    "Days",
    "Week",
    "Weeks",
    "Month",
    "Months",
    "Choose flexible days",
    "Choose rewards",
    "{count} rewards selected",
    "No days chosen yet",
    "{count} day chosen",
    "{count} days chosen",
    PRIVACY_SOURCE,
    *DATE_ERROR_SOURCES,
)


class HelpHubMetadataTranslationTests(unittest.TestCase):
    def test_metadata_catalogs_are_authored_complete_and_template_safe(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS} - {"en"}
        self.assertEqual(HELP_HUB_METADATA_KEYS, EXPECTED_METADATA_KEYS)
        self.assertEqual(len(HELP_HUB_METADATA_KEYS), 28)
        self.assertEqual(set(HELP_HUB_METADATA_CATALOGS), locales)
        self.assertTrue(set(HELP_HUB_METADATA_KEYS) <= set(COMPLETE_KEYS))
        for locale in locales:
            entries = HELP_HUB_METADATA_CATALOGS[locale]
            self.assertEqual(set(entries), set(EXPECTED_METADATA_KEYS))
            for source in EXPECTED_METADATA_KEYS:
                native = entries[source]
                self.assertTrue(native.strip(), (locale, source))
                self.assertNotEqual(native, source, (locale, source))
                self.assertEqual(
                    Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)),
                    Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", native)),
                    (locale, source),
                )
                self.assertIn(source, CATALOGS[locale])
                runtime_value = CATALOGS[locale][source]
                self.assertTrue(runtime_value.strip(), (locale, source))
                self.assertNotEqual(runtime_value, source, (locale, source))
                self.assertEqual(translate(locale, source), runtime_value)
                self.assertEqual(
                    Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)),
                    Counter(
                        re.findall(
                            r"\{([A-Za-z][A-Za-z0-9_]*)\}", runtime_value
                        )
                    ),
                    (locale, source),
                )
                self.assertEqual(translate("en", source), source)
                self.assertEqual(translate("unsupported", source), source)

    def test_canonical_state_sources_and_display_helpers_are_wired(self):
        self.assertEqual(
            FLEXIBLE_CHOICES,
            ["Any Day", "Any weekday", "Any weekend", "Custom"],
        )
        self.assertEqual(
            WEEKDAYS,
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
        )
        self.assertEqual(
            [item["value"] for item in REWARD_CHOICES],
            [
                "money",
                "refreshments",
                "meal",
                "accommodation",
                "guided_tour",
                "activity",
                "other_reward",
            ],
        )
        panel_path = Path("app/components/help_hub_panel.py")
        panel_tree = ast.parse(panel_path.read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(panel_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(
            {
                "localized_calendar_month",
                "localized_calendar_accessible_date",
                "localized_date_trigger",
                "localized_date_value",
                "localized_date_error",
                "localized_flexible_summary",
                "localized_rewards_summary",
                "localized_selected_date_count",
                "localized_help_privacy",
            }
            <= calls
        )
        component_text = panel_path.read_text(encoding="utf-8")
        self.assertIn(
            "on_click=lambda: HelpHubState.remove_date(value)", component_text
        )
        named_fields: set[str] = set()
        component_ids: set[str] = set()
        clock_select_fields: set[str] = set()
        submit_handlers: set[str] = set()
        for node in ast.walk(panel_tree):
            if not isinstance(node, ast.Call):
                continue
            function_name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            for keyword in node.keywords:
                if keyword.arg == "name" and isinstance(
                    keyword.value, ast.Constant
                ):
                    named_fields.add(str(keyword.value.value))
                if keyword.arg == "id" and isinstance(
                    keyword.value, ast.Constant
                ):
                    component_ids.add(str(keyword.value.value))
                if keyword.arg == "on_submit" and isinstance(
                    keyword.value, ast.Attribute
                ):
                    submit_handlers.add(keyword.value.attr)
            if function_name == "clock_select" and node.args:
                if isinstance(node.args[0], ast.Constant):
                    clock_select_fields.add(str(node.args[0].value))
        expected_fields = {
            "title",
            "description",
            "specific_hour",
            "specific_minute",
            "from_hour",
            "from_minute",
            "to_hour",
            "to_minute",
            "duration_hours",
            "duration_minutes_part",
            "duration_period_count",
            "duration_period_unit",
            "address",
            "city",
            "country",
            "reward_currency",
            "money_budget",
            "accommodation_nights",
            "guided_tour_details",
            "activity_details",
            "other_reward_details",
        }
        self.assertTrue(expected_fields <= named_fields | clock_select_fields)
        self.assertTrue(
            {
                "help-day-input",
                "help-day-calendar",
                "help-rewards-boundary",
                "help-reward-options",
                "gah-ask-help-form",
            }
            <= component_ids
        )
        self.assertIn("create_help_request", submit_handlers)
        duration_function = next(
            node
            for node in panel_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "duration_period_select"
        )
        duration_helper_calls = [
            node
            for node in ast.walk(duration_function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "localized_duration_unit"
        ]
        self.assertEqual(len(duration_helper_calls), 1)
        self.assertEqual(
            ast.dump(duration_helper_calls[0].args[0]),
            ast.dump(ast.parse("item['label']", mode="eval").body),
        )
        self.assertEqual(
            sum(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "localized_duration_unit"
                for node in ast.walk(panel_tree)
            ),
            1,
        )
        duration_option = next(
            node
            for node in ast.walk(duration_function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "option"
        )
        self.assertEqual(
            ast.dump(duration_option.args[0]),
            ast.dump(
                ast.parse(
                    "localized_duration_unit(item['label'])", mode="eval"
                ).body
            ),
        )
        duration_value = next(
            keyword.value
            for keyword in duration_option.keywords
            if keyword.arg == "value"
        )
        self.assertEqual(
            ast.dump(duration_value),
            ast.dump(ast.parse("item['value']", mode="eval").body),
        )
        helper_tree = ast.parse(
            Path("app/components/help_hub_metadata.py").read_text(
                encoding="utf-8"
            )
        )
        imports = {
            node.module
            for node in ast.walk(helper_tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertIn("app.interface_i18n", imports)
        self.assertIn("app.states.auth_state", imports)
        self.assertTrue(
            any(
                isinstance(node, ast.Attribute)
                and node.attr == "preferred_language"
                for node in ast.walk(helper_tree)
            )
        )
        state_tree = ast.parse(
            Path("app/states/help_hub_state.py").read_text(encoding="utf-8")
        )
        state_classes = [
            node
            for node in state_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "HelpHubState"
        ]
        annotations = {
            target.id
            for state_class in state_classes
            for node in state_class.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and ast.unparse(node.annotation) == "list[str]"
            for target in [node.target]
        }
        self.assertTrue(
            {
                "flexible_days",
                "custom_weekdays",
                "help_dates",
                "selected_rewards",
            }
            <= annotations
        )

    def test_help_form_builders_and_typed_calendar_cell_construct(self):
        cell: dict[str, str | bool] = {
            "date": "2027-02-06",
            "label": "6",
            "accessible_label": "Saturday 06 February 2027",
            "disabled": False,
            "selected": True,
            "today": False,
        }
        typed_cell = rx.Var.create(cell).to(dict[str, str | bool])
        components = (
            calendar_day(typed_cell),
            date_chip(rx.Var.create("2027-02-06").to(str)),
            help_day_field(),
            inline_help_calendar(),
            rewards_field(),
            duration_field(),
            post_help_form(),
        )
        self.assertTrue(all(component is not None for component in components))

    def test_amharic_metadata_row_is_valid_native_text(self):
        row = HELP_HUB_METADATA_CATALOGS["am"]
        self.assertEqual(set(row), set(EXPECTED_METADATA_KEYS))
        self.assertEqual(row["Day"], "ቀን")
        self.assertEqual(row["Month"], "ወር")
        for source in EXPECTED_METADATA_KEYS:
            value = row[source]
            self.assertTrue(value.strip(), source)
            self.assertNotEqual(value, source, source)
            self.assertEqual(
                Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)),
                Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", value)),
                source,
            )
            without_slots = re.sub(r"\{[A-Za-z][A-Za-z0-9_]*\}", "", value)
            self.assertTrue(
                all(
                    unicodedata.name(character, "").startswith("ETHIOPIC")
                    for character in without_slots
                    if character.isalpha()
                ),
                source,
            )
        privacy = row[PRIVACY_SOURCE]
        self.assertIn("0.5–1", privacy)
        self.assertIn("ሁለታችሁም ከተስማማችሁ", privacy)
        self.assertIn("ትክክለኛው ቦታዎ የሚታየው", privacy)
        self.assertIn("በኋላ ብቻ", privacy)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_compiled_duration_unit_catalog_is_scoped_and_preserves_unknown_text(
        self,
    ):
        locales = [code for code, _label in LANGUAGE_OPTIONS]
        units = ("Day", "Days", "Week", "Weeks", "Month", "Months")
        self.assertEqual(
            set(DURATION_UNIT_CATALOGS), set(HELP_HUB_METADATA_CATALOGS)
        )
        for locale, entries in DURATION_UNIT_CATALOGS.items():
            self.assertEqual(set(entries), set(units), locale)
            self.assertEqual(
                entries,
                {
                    unit: HELP_HUB_METADATA_CATALOGS[locale][unit]
                    for unit in units
                },
                locale,
            )
        fixtures: list[dict[str, str]] = []
        for locale in locales:
            for source in units:
                expected = (
                    source
                    if locale == "en"
                    else HELP_HUB_METADATA_CATALOGS[locale][source]
                )
                expression = str(
                    localized_duration_unit(rx.Var.create(source).to(str))
                ).replace(
                    str(AuthState.preferred_language),
                    json.dumps(locale),
                )
                fixtures.append(
                    {"expression": expression, "expected": expected}
                )
        for locale in ("id", "ja", "ar", "en", "unsupported"):
            for source in (
                "",
                "Day\\nDays",
                "member-authored 日 نهار",
                "$& Day",
                "__proto__",
                "constructor",
                "prototype",
            ):
                expression = str(
                    localized_duration_unit(rx.Var.create(source).to(str))
                ).replace(
                    str(AuthState.preferred_language),
                    json.dumps(locale),
                )
                fixtures.append({"expression": expression, "expected": source})
        self.assertEqual(CATALOGS["id"]["Day"], "Siang")
        self.assertEqual(HELP_HUB_METADATA_CATALOGS["id"]["Day"], "Hari")
        self.assertEqual(CATALOGS["ja"]["Day"], "昼")
        self.assertEqual(CATALOGS["ja"]["Month"], "月")
        self.assertEqual(HELP_HUB_METADATA_CATALOGS["ja"]["Day"], "日")
        self.assertEqual(HELP_HUB_METADATA_CATALOGS["ja"]["Month"], "か月")
        self.assertEqual(CATALOGS["ar"]["Day"], "نهار")
        self.assertEqual(HELP_HUB_METADATA_CATALOGS["ar"]["Day"], "يوم")
        script = (
            "const fixtures = JSON.parse(require('fs').readFileSync(0, 'utf8')); "
            "const results = fixtures.map(item => eval(item.expression) === item.expected); "
            "if (!results.every(Boolean)) { console.error(results.findIndex(value => !value)); process.exit(1); } "
            "console.log(results.length);"
        )
        completed = subprocess.run(
            ["node", "-e", script],
            input=json.dumps(fixtures, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(int(completed.stdout.strip()), len(fixtures))

    @unittest.skipUnless(
        shutil.which("node"), "Node.js is needed to evaluate Intl"
    )
    def test_compiled_display_expressions_and_native_intl_dates(self):
        locales = [code for code, _label in LANGUAGE_OPTIONS]
        translations = {
            locale: {
                key: translate(locale, key)
                for key in (
                    *EXPECTED_METADATA_KEYS,
                    *WEEKDAYS,
                    *(item["label"] for item in REWARD_CHOICES),
                    "Choose a date",
                )
            }
            for locale, _label in LANGUAGE_OPTIONS
        }
        fixtures: list[dict[str, str]] = []

        def add(
            locale: str,
            var: rx.Var[str],
            mode: str,
            raw: str = "",
            expected: str = "",
        ) -> None:
            fixtures.append(
                {
                    "locale": locale,
                    "expression": self._substitute_expression(
                        str(var), locale, translations[locale]
                    ),
                    "mode": mode,
                    "raw": raw,
                    "expected": expected,
                }
            )

        for locale, _label in LANGUAGE_OPTIONS:
            for kind, formatter in (
                ("month", localized_calendar_month),
                ("accessible", localized_calendar_accessible_date),
                ("date", localized_date_value),
            ):
                for date in (
                    "2027-02-06",
                    "2027-02-31",
                    "",
                    "literal\\n$&{count}",
                ):
                    add(locale, formatter(date), "date", date, kind)
            add(
                locale,
                localized_date_trigger(""),
                "text",
                expected=translate(locale, "Choose a date"),
            )
            for raw in ("2027-02-06", "2027-02-31", "literal\\n$&{count}"):
                add(locale, localized_date_trigger(raw), "date", raw, "trigger")
            for raw in (
                "Cancel",
                "Delete",
                "literal\\n$&{count}",
                *DATE_ERROR_SOURCES,
            ):
                add(
                    locale,
                    localized_date_error(raw),
                    "text",
                    expected=translate(locale, raw)
                    if raw in DATE_ERROR_SOURCES
                    else raw,
                )
            add(
                locale,
                localized_help_privacy(PRIVACY_SOURCE),
                "text",
                expected=translate(locale, PRIVACY_SOURCE),
            )
            add(
                locale,
                localized_help_privacy("member-authored line"),
                "text",
                expected="member-authored line",
            )
            for choices, weekdays in (
                ([], []),
                (["Any Day", "Custom"], ["Monday"]),
                (["Any weekday", "Any weekend"], []),
                (["Custom"], ["Sunday", "Monday", "Friday"]),
            ):
                tokens: list[str] = []
                if "Any Day" in choices:
                    expected_summary = translate(locale, "Any Day")
                else:
                    if "Any weekday" in choices:
                        tokens.append(translate(locale, "Any weekday"))
                    if "Any weekend" in choices:
                        tokens.append(translate(locale, "Any weekend"))
                    if "Custom" in choices:
                        tokens.extend(
                            translate(locale, day)
                            for day in WEEKDAYS
                            if day in weekdays
                        )
                    expected_summary = ", ".join(tokens) or translate(
                        locale, "Choose flexible days"
                    )
                add(
                    locale,
                    localized_flexible_summary(
                        rx.Var.create(choices).to(list[str]),
                        rx.Var.create(weekdays).to(list[str]),
                    ),
                    "text",
                    expected=expected_summary,
                )
            for selected in (
                [],
                ["money"],
                ["money", "meal"],
                ["money", "meal", "activity"],
                ["unknown"],
                ["meal", "money", "meal"],
            ):
                labels = [
                    translate(locale, item["label"])
                    for value in selected
                    for item in REWARD_CHOICES
                    if item["value"] == value
                ]
                if not labels:
                    expected_summary = translate(locale, "Choose rewards")
                elif len(labels) > 2:
                    expected_summary = translate(
                        locale, "{count} rewards selected"
                    ).replace("{count}", str(len(labels)))
                else:
                    expected_summary = ", ".join(labels)
                add(
                    locale,
                    localized_rewards_summary(
                        rx.Var.create(selected).to(list[str])
                    ),
                    "text",
                    expected=expected_summary,
                )
            for count in (0, 1, 7):
                dates = [
                    f"2027-02-{index:02d}" for index in range(1, count + 1)
                ]
                if count == 0:
                    expected_count = translate(locale, "No days chosen yet")
                else:
                    key = (
                        "{count} day chosen"
                        if count == 1
                        else "{count} days chosen"
                    )
                    expected_count = translate(locale, key).replace(
                        "{count}", str(count)
                    )
                add(
                    locale,
                    localized_selected_date_count(
                        rx.Var.create(dates).to(list[str])
                    ),
                    "text",
                    expected=expected_count,
                )

        payload = json.dumps(fixtures, ensure_ascii=False)
        script = (
            "const items = JSON.parse(require('fs').readFileSync(0, 'utf8')); "
            "const values = items.map(item => { const result = eval(item.expression); "
            "if (item.mode !== 'date') return result; "
            "if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(item.raw)) return result === item.raw; "
            "const date = new Date(`${item.raw}T00:00:00.000Z`); "
            "if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== item.raw) return result === item.raw; "
            "const options = item.expected === 'month' ? {month:'long', year:'numeric'} : "
            "item.expected === 'accessible' ? {weekday:'long', day:'numeric', month:'long', year:'numeric'} : "
            "{year:'numeric', month:'numeric', day:'numeric'}; "
            "return new Intl.DateTimeFormat(item.locale, {calendar:'gregory', timeZone:'UTC', ...options}).format(date) === result; }); "
            "const locales = " + json.dumps(locales) + "; "
            "const supported = Intl.DateTimeFormat.supportedLocalesOf(locales); "
            "console.log(JSON.stringify({values, supported}));"
        )
        completed = subprocess.run(
            ["node", "-e", script],
            input=payload,
            capture_output=True,
            text=True,
            check=True,
        )
        output = json.loads(completed.stdout)
        self.assertEqual(set(output["supported"]), set(locales))
        self.assertTrue(all(output["values"]))
        for index, item in enumerate(fixtures):
            if item["mode"] == "text":
                self.assertEqual(
                    output["values"][index], item["expected"], (item, index)
                )

    @staticmethod
    def _substitute_expression(
        expression: str, locale: str, translations: dict[str, str]
    ) -> str:
        rendered = expression
        for source in sorted(translations, key=len, reverse=True):
            rendered = rendered.replace(
                str(ui(source)),
                json.dumps(translations[source], ensure_ascii=False),
            )
        rendered = rendered.replace(
            str(AuthState.preferred_language), json.dumps(locale)
        )
        return rendered


if __name__ == "__main__":
    unittest.main()
