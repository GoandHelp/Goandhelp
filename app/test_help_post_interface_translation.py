import json
import subprocess
import unittest
from pathlib import Path

from app.components.help_post_panel import (
    help_post_panel,
    owner_edit_form,
    post_form,
    recent_posts_section,
    recurring_section,
)
from app.components.request_draft import (
    compact_request_fields,
    onboarding_rewards,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template_multi,
)
from app.interface_catalog_help_post_controls import (
    HELP_POST_CONTROL_CATALOGS,
    HELP_POST_CONTROL_KEYS,
)
from app.models import LANGUAGE_OPTIONS
from app.states.help_post_state import HelpPostState


class HelpPostInterfaceTranslationTests(unittest.TestCase):
    def test_help_post_control_catalogs_cover_all_sources_and_locales(self):
        expected_keys = (
            "Ask for help",
            "Attached job photo",
            "Cancelled",
            "Choose job categories",
            "Choose…",
            "Close job categories",
            "Completed",
            "Confirm removing this help request",
            "Confirmed",
            "Date & time needed",
            "Delete",
            "Describe your reward",
            "Edit",
            "Edit help request",
            "End",
            "Expired",
            "Flexible",
            "How long will it take?",
            "How often",
            "Job categories",
            "Job info",
            "Job photos",
            "Job title",
            "Keep it",
            "Keep this help request",
            "Location of this request",
            "Meeting point",
            "New activity on this help request",
            "Number of people required",
            "One-time",
            "Open",
            "Pause",
        )
        offered_codes = {code for code, _label in LANGUAGE_OPTIONS}
        non_english_codes = offered_codes - {"en"}
        self.assertEqual(HELP_POST_CONTROL_KEYS, expected_keys)
        self.assertEqual(len(HELP_POST_CONTROL_KEYS), 32)
        self.assertEqual(len(set(HELP_POST_CONTROL_KEYS)), 32)
        self.assertEqual(set(HELP_POST_CONTROL_CATALOGS), non_english_codes)
        self.assertTrue(set(HELP_POST_CONTROL_KEYS) <= set(COMPLETE_KEYS))
        for code in non_english_codes:
            self.assertIn(code, CATALOGS)
            self.assertEqual(
                set(HELP_POST_CONTROL_CATALOGS[code]), set(expected_keys)
            )
            for source in expected_keys:
                with self.subTest(locale=code, source=source):
                    value = HELP_POST_CONTROL_CATALOGS[code][source]
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())
                    self.assertIn(source, CATALOGS[code])
                    runtime_value = CATALOGS[code][source]
                    self.assertIsInstance(runtime_value, str)
                    self.assertTrue(runtime_value.strip())
                    self.assertEqual(translate(code, source), runtime_value)
                    if (code, source) not in {
                        ("nl", "Open"),
                        ("fr", "Flexible"),
                        ("de", "Pause"),
                    }:
                        self.assertNotEqual(value, source)
                        self.assertNotEqual(runtime_value, source)
        for source in expected_keys:
            self.assertNotIn(source, CATALOGS["en"])
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unknown-locale", source), source)

    def test_all_offered_locales_and_existing_shared_copy_fallback(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS}
        self.assertEqual(len(locales), 37)
        self.assertEqual(len(locales - {"en"}), 36)
        existing_sources = (
            "Job Title",
            "Job description",
            "Job category",
            "Date",
            "Rewards",
            "Save changes",
            "Cancel",
        )
        self.assertTrue(set(existing_sources) <= set(COMPLETE_KEYS))
        for locale in locales - {"en"}:
            self.assertIn(locale, CATALOGS)
            for source in existing_sources:
                with self.subTest(locale=locale, source=source):
                    self.assertIn(source, CATALOGS[locale])
                    self.assertTrue(CATALOGS[locale][source])
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )
                    if (locale, source) != ("fr", "Date"):
                        self.assertNotEqual(translate(locale, source), source)
                    else:
                        self.assertEqual(translate(locale, source), "Date")
        for source in existing_sources:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unknown-locale", source), source)

    def test_post_edit_recent_and_recurring_components_render(self):
        for component in (
            help_post_panel(),
            post_form(),
            owner_edit_form(),
            recent_posts_section(),
            recurring_section(),
            compact_request_fields(HelpPostState, "edit-help-request"),
            onboarding_rewards(),
        ):
            self.assertTrue(component.render())

    def test_existing_submission_and_edit_contracts_remain_intact(self):
        source = Path("app/components/help_post_panel.py").read_text()
        for token in (
            'name="title"',
            'name="description"',
            'name="scheduled_for"',
            'name="helpers_needed"',
            "max_length=500",
            "max=500",
            "MembershipState.is_premium",
            "HelpPostState.create_post",
            "HelpPostState.save_edit",
            "HelpPostState.cancel_edit",
            'post["title"]',
            'post["description"]',
            'post["reward_details"]',
            'post["location"]',
        ):
            self.assertIn(token, source)
        self.assertNotIn('ui(post["title"])', source)
        self.assertNotIn('ui(post["description"])', source)
        self.assertNotIn('ui(post["reward_details"])', source)
        self.assertIn(
            'translate(auth.preferred_language, "Help request updated.")',
            Path("app/states/help_post_state.py").read_text(),
        )
        self.assertIn(
            'translate(interface_language, "Help request posted.")',
            Path("app/states/help_post_state.py").read_text(),
        )

    def test_template_helper_preserves_slots_and_unknown_member_values(self):
        title = 'First line\nZoë “雪” {name} {title} "$&" and \\ literal'
        value = ui_template_multi(
            "Remove “{title}” from the board?", {"title": title}
        )
        expression = value._js_expr
        expression = expression.replace(
            str(ui("Remove “{title}” from the board?")),
            json.dumps("Remove “{title}” from the board?", ensure_ascii=False),
        )
        result = subprocess.run(
            [
                "node",
                "-e",
                "process.stdout.write(JSON.stringify(eval(process.argv[1])))",
                expression,
            ],
            capture_output=True,
            check=True,
            text=True,
        )
        self.assertEqual(
            json.loads(result.stdout), f"Remove “{title}” from the board?"
        )

    def test_feedback_display_vars_depend_on_all_owned_canonical_fields_and_language(
        self,
    ):
        rendered = (
            ui(HelpPostState.localized_feedback["error"]),
            ui(HelpPostState.localized_category_count_label),
            ui(HelpPostState.localized_category_slot_hint),
            ui(HelpPostState.category_summary_label),
        )
        for value in rendered:
            dependency_data = str(value._get_all_var_data())
            self.assertIn("interface_text", dependency_data)
        fields = (
            "error",
            "success",
            "photo_error",
            "photo_notice",
            "schedule_error",
            "schedule_notice",
            "edit_error",
        )
        state_source = Path("app/states/help_post_state.py").read_text()
        self.assertTrue(
            all(
                f'"{field}": self._localized_feedback_text' in state_source
                for field in fields
            )
        )
        self.assertIn("source: str", state_source)
        self.assertIn("return translate(language, source)", state_source)


if __name__ == "__main__":
    unittest.main()
