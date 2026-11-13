import reflex as rx

import unittest
from app.help_languages import (
    LANGUAGE_CHOICES,
    LANGUAGE_CODES,
    PREFIX,
    decode_knowledge,
    encode_knowledge,
)


class HelpLanguageTests(unittest.TestCase):
    def test_expanded_choices_preserve_metadata(self):
        self.assertEqual(
            LANGUAGE_CHOICES[0],
            {"code": "", "flag": "🌐", "name": "Any language"},
        )
        self.assertGreaterEqual(len(LANGUAGE_CODES), 95)
        self.assertLessEqual(len(LANGUAGE_CODES), 110)
        self.assertEqual(len(LANGUAGE_CHOICES), len(LANGUAGE_CODES) + 1)
        legacy = dict(
            zip(
                "en es fr de pt it nl pl uk ru ar hi zh ja ko".split(),
                [
                    "English",
                    "Spanish",
                    "French",
                    "German",
                    "Portuguese",
                    "Italian",
                    "Dutch",
                    "Polish",
                    "Ukrainian",
                    "Russian",
                    "Arabic",
                    "Hindi",
                    "Chinese",
                    "Japanese",
                    "Korean",
                ],
            )
        )
        choices = {row["code"]: row["name"] for row in LANGUAGE_CHOICES}
        for code, name in legacy.items():
            self.assertEqual(choices[code], name)
            self.assertEqual(
                decode_knowledge(f'{PREFIX}["{code}"]\nSkills'),
                ("Skills", [code]),
            )
        for row in LANGUAGE_CHOICES[1:]:
            with self.subTest(code=row["code"]):
                self.assertEqual(set(row), {"code", "flag", "name"})
                self.assertRegex(row["code"], r"^[a-z]{2,3}$")
                self.assertTrue(row["flag"])
                self.assertTrue(row["name"])
                self.assertEqual(
                    decode_knowledge(encode_knowledge("Skills", [row["code"]])),
                    ("Skills", [row["code"]]),
                )

    def test_legacy(self):
        self.assertEqual(
            decode_knowledge("Bring careful hands."),
            ("Bring careful hands.", []),
        )
        self.assertEqual(decode_knowledge(None), ("", []))

    def test_round_trip(self):
        ordinary = "Woodwork\n日本語 and tools"
        self.assertEqual(
            decode_knowledge(encode_knowledge(ordinary, ["pt", "en", "pt"])),
            (ordinary, ["en", "pt"]),
        )

    def test_any_language(self):
        self.assertEqual(
            encode_knowledge("No experience needed", []), "No experience needed"
        )

    def test_reserved_prefix_in_ordinary_text(self):
        ordinary = f"{PREFIX}ordinary text"
        self.assertEqual(
            decode_knowledge(encode_knowledge(ordinary, [])), (ordinary, [])
        )

    def test_invalid_tokens_rejected(self):
        with self.assertRaises(ValueError):
            encode_knowledge("Skills", ["not-a-language"])

    def test_malformed_metadata_hidden(self):
        self.assertEqual(
            decode_knowledge(f"{PREFIX}not json\nKeep this text"),
            ("Keep this text", []),
        )
        self.assertEqual(
            decode_knowledge(f'{PREFIX}["invalid"]\nSkills'), ("Skills", [])
        )


if __name__ == "__main__":
    unittest.main()
