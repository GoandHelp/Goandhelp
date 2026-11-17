import json
import re
import subprocess
import unittest
from pathlib import Path

from app.interface_catalog_help_post_details import (
    HELP_POST_DETAIL_CATALOGS,
    HELP_POST_DETAIL_KEYS,
)
from app.interface_catalog_help_post_guidance import (
    HELP_POST_GUIDANCE_CATALOGS,
    HELP_POST_GUIDANCE_KEYS,
)
from app.interface_catalog_help_post_templates import (
    HELP_POST_COUNT_LABEL_KEYS,
    HELP_POST_TEMPLATE_CATALOGS,
    HELP_POST_UI_TEMPLATE_KEYS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template_multi,
)
from app.models import LANGUAGE_OPTIONS
from app.scripts.audit_interface_copy import audit_paths
from app.states.auth_state import AuthState

EXPECTED_GUIDANCE = (
    "Describe the job, the place and what a helper should bring.",
    "Describe the task, offer something warm in return, and pick the moment you need someone there.",
    "Every two weeks, on the same weekday.",
    "Fill in the form above and your first request will appear here.",
    "Five photos attached - remove one to swap it out",
    "Free requests are for one helper. Premium members can request 1–500 people.",
    "Go and Help receives an 8% fee",
    "Home-cooked dinner with my family in the old town",
    "I'm moving out of a fourth-floor flat and need someone strong for an hour. Lift is broken, boxes are packed and light-ish...",
    "Keep your current location, or place a replacement pin below. Editing closes as soon as any help offer arrives.",
    "Maya from Lisbon",
    "Off by default. When on, each date is created automatically from the date and time you picked above — always within your posting allowance.",
    "Post what you need a hand with.",
    "Premium lets you confirm up to 500 helpers. Your request stays open until all places are filled.",
    "Rua das Flores 22, by the blue door",
    "Static JPEG/JPG, PNG or WebP only · 3 MB maximum · no video",
    "Tap the cross to remove a photo before posting.",
    "The last six pages of your journal — freshest first.",
    "This repeating request has finished.",
    "Turn on “Repeat this request” in the form above and each date will be created for you.",
    "Two hands to carry boxes up three flights",
    "Your exact pin stays private. Helpers see an approximate area until confirmed.",
)
EXPECTED_TEMPLATES = (
    "{count} characters left",
    "{count} of 5 slots free",
    "{count} / 5 attached",
    "{count} created",
    "Remove “{title}” from the board?",
    "Delete {title}",
    "People required: {count}",
)
EXPECTED_COUNT_LABELS = ("Requests posted", "Still open", "Upcoming")


class HelpPostGuidanceTranslationTests(unittest.TestCase):
    def test_source_groups_and_complete_catalog_coverage(self):
        self.assertEqual(len(EXPECTED_GUIDANCE), 22)
        self.assertEqual(len(set(EXPECTED_GUIDANCE)), 22)
        self.assertEqual(len(EXPECTED_TEMPLATES), 7)
        self.assertEqual(len(set(EXPECTED_TEMPLATES)), 7)
        self.assertEqual(len(EXPECTED_COUNT_LABELS), 3)
        self.assertEqual(HELP_POST_GUIDANCE_KEYS, EXPECTED_GUIDANCE[:11])
        self.assertEqual(HELP_POST_DETAIL_KEYS, EXPECTED_GUIDANCE[11:])
        self.assertEqual(HELP_POST_UI_TEMPLATE_KEYS, EXPECTED_TEMPLATES)
        self.assertEqual(HELP_POST_COUNT_LABEL_KEYS, EXPECTED_COUNT_LABELS)

        guidance_keys = (*HELP_POST_GUIDANCE_KEYS, *HELP_POST_DETAIL_KEYS)
        template_keys = (
            *HELP_POST_UI_TEMPLATE_KEYS,
            *HELP_POST_COUNT_LABEL_KEYS,
        )
        all_new_keys = (*guidance_keys, *template_keys)
        self.assertEqual(len(all_new_keys), 32)
        self.assertEqual(len(set(all_new_keys)), 32)
        self.assertTrue(set(all_new_keys) <= set(COMPLETE_KEYS))

        offered_codes = {code for code, _label in LANGUAGE_OPTIONS}
        non_english_codes = offered_codes - {"en"}
        self.assertEqual(len(offered_codes), 37)
        self.assertEqual(len(non_english_codes), 36)
        for catalogs, expected in (
            (HELP_POST_GUIDANCE_CATALOGS, set(HELP_POST_GUIDANCE_KEYS)),
            (HELP_POST_DETAIL_CATALOGS, set(HELP_POST_DETAIL_KEYS)),
            (HELP_POST_TEMPLATE_CATALOGS, set(template_keys)),
        ):
            self.assertEqual(set(catalogs), non_english_codes)
            for code in non_english_codes:
                with self.subTest(locale=code):
                    self.assertEqual(set(catalogs[code]), expected)
                    for source, value in catalogs[code].items():
                        self.assertIsInstance(value, str)
                        self.assertTrue(value.strip())
                        self.assertIn(source, CATALOGS[code])
                        self.assertEqual(CATALOGS[code][source], value)
                        self.assertEqual(translate(code, source), value)

        for source in all_new_keys:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unsupported-locale", source), source)

    def test_template_placeholder_names_and_multiplicity_match_every_locale(
        self,
    ):
        for code, entries in HELP_POST_TEMPLATE_CATALOGS.items():
            for source in EXPECTED_TEMPLATES:
                expected_slots = re.findall(
                    r"\{([A-Za-z][A-Za-z0-9_]*)\}", source
                )
                actual_slots = re.findall(
                    r"\{([A-Za-z][A-Za-z0-9_]*)\}", entries[source]
                )
                with self.subTest(locale=code, source=source):
                    self.assertEqual(actual_slots, expected_slots)
                    self.assertEqual(
                        re.findall(
                            r"\{([A-Za-z][A-Za-z0-9_]*)\}",
                            CATALOGS[code][source],
                        ),
                        expected_slots,
                    )

    def test_known_help_post_sources_have_no_uncatalogued_static_copy(self):
        findings = audit_paths(
            [
                Path("app/components/help_post_panel.py"),
                Path("app/components/request_draft.py"),
            ]
        )
        remaining = sorted(
            {
                str(finding["source"])
                for finding in findings
                if finding["missing"]
                and finding["source"] not in {"Porto", "Portugal"}
            }
        )
        self.assertEqual(remaining, [])

    def test_template_substitution_is_literal_for_real_compiled_expressions(
        self,
    ):
        locales = ("en", "fr", "ar", "ja")
        member_title = 'Aïcha {count}\nZoë “雪” "$&" and \\ literal'
        count_value = '7 {count} "$&" \\ count\n二行'
        source_values = {
            "count": count_value,
            "title": member_title,
        }

        for locale in locales:
            expressions: list[str] = []
            expected_results: list[str] = []
            for source in EXPECTED_TEMPLATES:
                slots = re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)
                actual_values = {
                    slot: source_values[slot] for slot in dict.fromkeys(slots)
                }
                expression = str(
                    ui_template_multi(source, actual_values)._js_expr
                )
                localized_template = translate(locale, source)
                expression = expression.replace(
                    str(ui(source)),
                    json.dumps(localized_template, ensure_ascii=False),
                )
                expressions.append(expression)
                expected_results.append(
                    re.sub(
                        r"\{(count|title)\}",
                        lambda match: source_values[match.group(1)],
                        localized_template,
                    )
                )

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
            self.assertEqual(json.loads(result.stdout), expected_results)

        reactive_template = ui_template_multi(
            EXPECTED_TEMPLATES[4], {"title": AuthState.display_name}
        )
        dependencies = str(reactive_template._get_all_var_data())
        self.assertIn("interface_text", dependencies)
        self.assertIn("display_name", dependencies)


if __name__ == "__main__":
    unittest.main()
