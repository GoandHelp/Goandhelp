import unittest
from collections import Counter
import re

import reflex as rx

from app.components.request_heading import (
    request_heading,
    styled_count_template,
)
from app.components.help_hub_panel import help_summary_card
from app.interface_catalog_request_counts import (
    REQUEST_COUNT_CATALOGS,
    REQUEST_COUNT_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
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


class RequestCountsTranslationTests(unittest.TestCase):
    def test_count_sources_and_locale_rows_are_complete(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS} - {"en"}
        self.assertEqual(set(REQUEST_COUNT_CATALOGS), locales)
        self.assertEqual(REQUEST_COUNT_KEYS, EXPECTED_REQUEST_COUNT_KEYS)
        self.assertEqual(len(REQUEST_COUNT_KEYS), len(set(REQUEST_COUNT_KEYS)))
        self.assertTrue(set(REQUEST_COUNT_KEYS) <= set(COMPLETE_KEYS))
        for locale in locales:
            row = REQUEST_COUNT_CATALOGS[locale]
            self.assertEqual(set(row), set(REQUEST_COUNT_KEYS))
            self.assertTrue(all(value.strip() for value in row.values()))
            for source, value in row.items():
                self.assertEqual(
                    Counter(re.findall(r"\{([a-z]+)\}", source)),
                    Counter(re.findall(r"\{([a-z]+)\}", value)),
                )
                self.assertEqual(CATALOGS[locale][source], value)
        for source in REQUEST_COUNT_KEYS:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unsupported", source), source)

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
