import json
import shutil
import subprocess
import unittest
from collections import Counter
import re

import reflex as rx

from app.components.request_heading import (
    request_heading,
    styled_count_template,
)
from app.components.help_hub_panel import help_summary_card
from app.interface_catalog_request_count_headings import (
    REQUEST_COUNT_HEADING_ROWS,
)
from app.interface_catalog_request_count_subtitles import (
    REQUEST_COUNT_SUBTITLE_ROWS,
)
from app.interface_catalog_request_count_totals import (
    REQUEST_COUNT_TOTAL_ROWS,
)
from app.interface_catalog_request_counts import (
    REQUEST_COUNT_CATALOGS,
    REQUEST_COUNT_KEYS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template,
    ui_template_multi,
)
from app.models import LANGUAGE_OPTIONS


EXPECTED_REQUEST_COUNT_KEYS = (
    "{count} upcoming jobs",
    "{count} Confirmed job",
    "{count} Confirmed jobs",
    "{count} Confirmed helper",
    "{count} Confirmed helpers",
    "{count} Event",
    "{count} Events",
    "{count} Hosted event",
    "{count} Hosted events",
    "{count} Help request",
    "{count} Help requests",
    "{count} Search alerts",
    "{count} search alert",
    "{count} search alerts",
    "{count} Bookmarked help request",
    "{count} Bookmarked help requests",
    "{count} Offer to help you",
    "{count} Offers to help you",
    "{count} Request for your help",
    "{count} Requests for your help",
    "Get ready to help others",
    "People ready to help you",
    "Requests you have already posted",
    "Join many helping hands",
    "Manage helpers for your event",
    "Get notified with matching help requests",
    "Help requests you bookmarked in map or list view.",
    "{count} help given",
    "{count} help received",
    "Helped {count} time",
    "Helped {count} times",
    "Received help {count} time",
    "Received help {count} times",
    "{count} Requested",
    "{count} Open",
    "{count} Upcoming",
    "{count} people required",
    "{rating} out of 5 stars; {count} reviews",
    "Offered {date}",
)


EXPECTED_LOCALES = frozenset(
    "am ar bn my zh cs da nl fi fr de el gu he hi hu id it ja kn ko ml mr "
    "ne fa pl pt ro es sw sv ta te th tr vi".split()
)


def _slots(text: str) -> Counter:
    return Counter(re.findall(r"\{([a-z]+)\}", text))


def _evaluate_js(expressions: list[str]) -> list[str]:
    script = (
        "const exprs = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "process.stdout.write(JSON.stringify(exprs.map((expr) => eval(expr))));"
    )
    completed = subprocess.run(
        ["node", "-e", script],
        input=json.dumps(expressions),
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(completed.stdout)


class RequestCountsTranslationTests(unittest.TestCase):
    def test_count_sources_and_locale_rows_are_complete(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS} - {"en"}
        self.assertEqual(locales, EXPECTED_LOCALES)
        self.assertEqual(len(locales), 36)
        self.assertEqual(set(REQUEST_COUNT_CATALOGS), locales)
        self.assertNotIn("en", REQUEST_COUNT_CATALOGS)
        self.assertEqual(REQUEST_COUNT_KEYS, EXPECTED_REQUEST_COUNT_KEYS)
        self.assertEqual(len(REQUEST_COUNT_KEYS), 39)
        self.assertEqual(len(REQUEST_COUNT_KEYS), len(set(REQUEST_COUNT_KEYS)))
        self.assertTrue(set(REQUEST_COUNT_KEYS) <= set(COMPLETE_KEYS))
        for rows, size in (
            (REQUEST_COUNT_HEADING_ROWS, 20),
            (REQUEST_COUNT_SUBTITLE_ROWS, 7),
            (REQUEST_COUNT_TOTAL_ROWS, 12),
        ):
            self.assertEqual(set(rows), locales)
            for locale, row in rows.items():
                self.assertEqual(len(row.split("|")), size, locale)
        for locale in sorted(locales):
            row = REQUEST_COUNT_CATALOGS[locale]
            self.assertEqual(tuple(row), REQUEST_COUNT_KEYS)
            self.assertEqual(len(row), 39)
            for source, value in row.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertNotEqual(value.casefold(), source.casefold())
                    self.assertEqual(_slots(source), _slots(value))
                    self.assertIn(source, CATALOGS[locale])
                    runtime = CATALOGS[locale][source]
                    self.assertTrue(runtime.strip())
                    self.assertNotEqual(runtime, source)
                    self.assertEqual(_slots(source), _slots(runtime))
                    self.assertEqual(translate(locale, source), runtime)
        for source in REQUEST_COUNT_KEYS:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unsupported", source), source)

    def test_reactive_count_pieces_depend_on_interface_text(self):
        count = rx.Var.create(7).to(int)
        for source in REQUEST_COUNT_KEYS[:20]:
            template = ui(source)
            template_js = str(template)
            self.assertIn("interface_text", template_js)
            data = template._get_all_var_data()
            self.assertIsNotNone(data)
            self.assertIn("auth_state", data.state)
            pieces = template.split("{count}")
            self.assertIn(template_js, str(pieces[0]))
            self.assertIn(template_js, str(pieces[1]))
            rendered = str(styled_count_template(template, count))
            self.assertIn("text-[#e08b12]", rendered)
            self.assertIn("interface_text", rendered)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_compiled_count_templates_evaluate_native_word_order(self):
        sources = (
            "{count} Events",
            "{count} Offers to help you",
            "{count} Requests for your help",
            "Helped {count} times",
            "Received help {count} time",
            "{count} people required",
        )
        payload = "Line one\nLine two $& $1 {count} \"quoted\" 'single'"
        count = rx.Var.create(7).to(int)
        expressions: list[str] = []
        expected: list[str] = []
        for locale in ("en", "fr", "ar", "ja"):
            for source in sources:
                native = translate(locale, source)
                ui_js = str(ui(source))
                native_js = json.dumps(native)
                full_js = str(ui_template(source, "count", count))
                pieces = ui(source).split("{count}")
                for compiled in (full_js, str(pieces[0]), str(pieces[1])):
                    self.assertIn(ui_js, compiled)
                    replaced = compiled.replace(ui_js, native_js)
                    self.assertNotIn("interface_text", replaced)
                    expressions.append(replaced)
                before, after = native.split("{count}")
                expected.extend((f"{before}7{after}", before, after))
            offered_js = str(ui("Offered {date}"))
            offered = translate(locale, "Offered {date}")
            expressions.append(
                str(ui_template("Offered {date}", "date", payload)).replace(
                    offered_js, json.dumps(offered)
                )
            )
            expected.append(offered.replace("{date}", payload))
            rating_source = "{rating} out of 5 stars; {count} reviews"
            rating_js = str(ui(rating_source))
            rating = translate(locale, rating_source)
            expressions.append(
                str(
                    ui_template_multi(
                        rating_source, {"rating": "4.5", "count": count}
                    )
                ).replace(rating_js, json.dumps(rating))
            )
            expected.append(
                rating.replace("{rating}", "4.5").replace("{count}", "7")
            )
        results = _evaluate_js(expressions)
        self.assertEqual(results, expected)
        by_locale = {
            locale: REQUEST_COUNT_CATALOGS[locale]["Helped {count} times"]
            for locale in ("fr", "ar", "ja")
        }
        by_locale["en"] = translate("en", "Helped {count} times")
        self.assertTrue(by_locale["en"].startswith("Helped "))
        self.assertTrue(by_locale["ja"].startswith("{count}"))
        self.assertNotEqual(by_locale["fr"], by_locale["en"])
        self.assertNotEqual(by_locale["ar"], by_locale["en"])
        for result in results:
            self.assertNotIn("{count}", result.replace(payload, ""))

    def test_component_builders_accept_reactive_counts_for_all_heading_cases(
        self,
    ):
        headings = (
            "Confirmed Help",
            "Confirmed Helpers",
            "Events",
            "Hosted events",
            "Your help requests",
            "Saved search alerts",
            "Bookmarked help requests",
            "Offers to help you",
            "Requests for your help",
        )
        for title in headings:
            for number in (0, 1, 7):
                count = rx.Var.create(number).to(int)
                component = request_heading(title, count)
                self.assertIsNotNone(component)
        for number in (0, 1, 7):
            count = rx.Var.create(number).to(int)
            self.assertIsNotNone(
                styled_count_template(ui("{count} Requested"), count)
            )
            self.assertIsNotNone(help_summary_card("help given", count))
            self.assertIsNotNone(help_summary_card("help received", count))


if __name__ == "__main__":
    unittest.main()
