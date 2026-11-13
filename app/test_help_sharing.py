import reflex as rx

import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from app.states.help_share_state import parse_shared_help, share_links
from app.filter_categories import FILTER_CATEGORIES, expand_category_tokens


class HelpSharingTests(unittest.TestCase):
    def test_invalid_ids(self):
        for value in (
            None,
            [],
            ["12"],
            "",
            "0",
            "-1",
            "1.5",
            "1&x=2",
            "９",
            "9" * 40,
        ):
            self.assertEqual(parse_shared_help(value), 0)
        self.assertEqual(parse_shared_help("123"), 123)

    def test_encoded_links(self):
        with patch(
            "app.states.help_share_state.public_base_url",
            return_value="https://example.com",
        ):
            url, links = share_links(
                123, "Help & care / café?", "https://example.com"
            )
        self.assertEqual(
            parse_qs(urlsplit(url).query), {"shared_help": ["123"]}
        )
        self.assertEqual(len(links), 5)
        whatsapp = parse_qs(urlsplit(links[0]["href"]).query)["text"][0]
        self.assertIn("Help & care / café?", whatsapp)
        self.assertIn(url, whatsapp)
        self.assertNotIn("latitude", url)
        self.assertNotIn("address", url)

    def test_other_last_and_aliases(self):
        self.assertEqual(FILTER_CATEGORIES[-1]["value"], "other")
        self.assertEqual(FILTER_CATEGORIES[0]["value"], "events")
        labels = [item["label"].casefold() for item in FILTER_CATEGORIES[1:-1]]
        self.assertEqual(labels, sorted(labels))
        self.assertIn("services", expand_category_tokens(["other"]))
        self.assertIn("builder", expand_category_tokens(["construction"]))


if __name__ == "__main__":
    unittest.main()
