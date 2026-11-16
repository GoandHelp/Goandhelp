import json
import re
import subprocess
import unittest
from string import Formatter

from pathlib import Path
from test_utils import run_event

from app.components.job_feedback import job_feedback
from app.components.messages_panel import messages_panel
from app.interface_catalog_job_feedback import (
    JOB_FEEDBACK_LITERAL_KEYS,
    JOB_FEEDBACK_TEMPLATE_CATALOGS,
    JOB_FEEDBACK_TEMPLATE_KEYS,
    JOB_FEEDBACK_TOAST_CATALOGS,
    JOB_FEEDBACK_TOAST_KEYS,
)
from app.interface_catalog_job_feedback_literals import (
    JOB_FEEDBACK_LITERAL_CATALOGS,
    JOB_FEEDBACK_LITERAL_TRANSLATION_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import LANGUAGE_OPTIONS
from app.states.messaging_state import MessagingState


class JobFeedbackTranslationTests(unittest.IsolatedAsyncioTestCase):
    def test_feedback_templates_cover_every_offered_non_english_locale(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS}
        non_english = locales - {"en"}
        self.assertEqual(len(locales), 37)
        self.assertEqual(len(non_english), 36)
        self.assertEqual(set(JOB_FEEDBACK_TEMPLATE_CATALOGS), non_english)
        self.assertEqual(
            len(JOB_FEEDBACK_TEMPLATE_KEYS),
            len(set(JOB_FEEDBACK_TEMPLATE_KEYS)),
        )
        self.assertTrue(set(JOB_FEEDBACK_TEMPLATE_KEYS) <= set(COMPLETE_KEYS))
        formatter = Formatter()
        for locale in non_english:
            catalog = JOB_FEEDBACK_TEMPLATE_CATALOGS[locale]
            self.assertEqual(set(catalog), set(JOB_FEEDBACK_TEMPLATE_KEYS))
            for source, value in catalog.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertEqual(CATALOGS[locale][source], value)
                    self.assertEqual(translate(locale, source), value)
                    self.assertCountEqual(
                        [
                            field
                            for _, field, _, _ in formatter.parse(source)
                            if field
                        ],
                        [
                            field
                            for _, field, _, _ in formatter.parse(value)
                            if field
                        ],
                    )
        self.assertEqual(set(JOB_FEEDBACK_TOAST_CATALOGS), non_english)
        for source in (*JOB_FEEDBACK_TEMPLATE_KEYS, *JOB_FEEDBACK_TOAST_KEYS):
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unknown-locale", source), source)
            for locale in non_english:
                self.assertTrue(translate(locale, source).strip())
                self.assertNotEqual(translate(locale, source), source)

    def test_all_literal_feedback_sources_have_full_runtime_translation_coverage(
        self,
    ):
        non_english = {code for code, _label in LANGUAGE_OPTIONS} - {"en"}
        self.assertEqual(len(JOB_FEEDBACK_LITERAL_KEYS), 55)
        self.assertEqual(len(JOB_FEEDBACK_LITERAL_TRANSLATION_KEYS), 48)
        self.assertTrue(set(JOB_FEEDBACK_LITERAL_KEYS) <= set(COMPLETE_KEYS))
        self.assertEqual(set(JOB_FEEDBACK_LITERAL_CATALOGS), non_english)
        self.assertTrue(non_english <= set(CATALOGS))
        self.assertEqual(
            set(JOB_FEEDBACK_LITERAL_TRANSLATION_KEYS),
            set(JOB_FEEDBACK_LITERAL_KEYS)
            - {
                "Your session expired — please sign in again.",
                *JOB_FEEDBACK_TOAST_KEYS,
            },
        )
        for source in JOB_FEEDBACK_LITERAL_KEYS:
            self.assertIn(source, COMPLETE_KEYS)
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unknown-locale", source), source)
            for locale in non_english:
                with self.subTest(locale=locale, source=source):
                    value = translate(locale, source)
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertIn(source, CATALOGS[locale])
        for locale in non_english:
            with self.subTest(locale=locale):
                group = JOB_FEEDBACK_LITERAL_CATALOGS[locale]
                self.assertEqual(
                    set(group), set(JOB_FEEDBACK_LITERAL_TRANSLATION_KEYS)
                )
                for source, translated in group.items():
                    self.assertTrue(translated.strip())
                    self.assertNotEqual(translated, source)
                    self.assertEqual(CATALOGS[locale][source], translated)
                    self.assertEqual(translate(locale, source), translated)

    def test_producer_inventory_includes_failure_validation_constant_and_toast_sources(
        self,
    ):
        from app.interface_catalog_job_feedback import (
            JOB_FEEDBACK_LITERAL_KEYS,
        )

        inventory = set(JOB_FEEDBACK_LITERAL_KEYS)
        self.assertEqual(len(inventory), 55)
        self.assertTrue(set(JOB_FEEDBACK_TOAST_KEYS) <= inventory)
        self.assertTrue(
            {
                "That request is no longer open — it may have been withdrawn, already answered, or given to another helper.",
                "We couldn't load your Inbox just now. Please use Refresh to try again.",
                "We couldn't load this conversation. Please try again.",
                "Keep messages under 2000 characters.",
                "Keep the story note under 2000 characters.",
                "Keep the reward under 255 characters.",
                "Keep your review to 500 words or fewer.",
                "Write a response of 1–500 words.",
                "No photo could be added. Check the format (JPG, PNG, WebP, maximum 3 MB, static images only, no video) and the five-photo limit.",
                "Reports open once both sides confirm the job.",
                "Please describe what happened in a little more detail (20 characters or more).",
                "Thank you — this report is private and now with our review team. Nothing is published and no one is accused publicly.",
            }
            <= inventory
        )
        state_source = Path("app/states/messaging_state.py").read_text()
        for toast_source in JOB_FEEDBACK_TOAST_KEYS:
            self.assertIn(toast_source, state_source)
        self.assertIn("STALE_REQUEST_ERROR", state_source)
        self.assertIn("REVIEW_ELIGIBILITY_ERROR", state_source)
        self.assertIn("REPORT_DETAILS_MIN", state_source)
        self.assertIn("REPORT_DETAILS_MAX", state_source)

    def test_all_eight_owned_feedback_bindings_are_scoped_to_job_feedback(self):
        panel = messages_panel()
        self.assertTrue(panel.render())
        source = Path("app/components/messages_panel.py").read_text()
        expected_bindings = (
            "error_banner(job_feedback(MessagingState.error))",
            "success_banner(job_feedback(MessagingState.success))",
            "job_feedback(MessagingState.response_error)",
            "job_feedback(MessagingState.photo_error)",
            "job_feedback(MessagingState.photo_success)",
            "job_feedback(MessagingState.report_error)",
            "job_feedback(MessagingState.report_success)",
            "job_feedback(MessagingState.share_note)",
        )
        for binding in expected_bindings:
            with self.subTest(binding=binding):
                self.assertIn(binding, source)
        self.assertIn("error_banner(ContactsState.error)", source)
        self.assertIn("success_banner(ContactsState.success)", source)
        self.assertIn("error_banner(MessageDeletionState.error)", source)
        self.assertIn("success_banner(MessageDeletionState.success)", source)
        self.assertIn('name="body"', source)
        self.assertIn('name="comment"', source)
        self.assertIn('name="response"', source)
        self.assertIn('name="details"', source)
        self.assertIn("default_value=MessagingState.share_text", source)

    def test_feedback_helper_is_reactive_and_keeps_whole_source_dependency(
        self,
    ):
        value = job_feedback(MessagingState.share_note)
        data = value._get_all_var_data()
        self.assertIsNotNone(data)
        dependencies = str(data)
        self.assertIn("interface_text", dependencies)
        self.assertIn("share_note", dependencies)
        fields = (
            (MessagingState.error, "error"),
            (MessagingState.success, "success"),
            (MessagingState.response_error, "response_error"),
            (MessagingState.photo_error, "photo_error"),
            (MessagingState.photo_success, "photo_success"),
            (MessagingState.report_error, "report_error"),
            (MessagingState.report_success, "report_success"),
        )
        for field, field_name in fields:
            value = job_feedback(field)
            self.assertIn("interface_text", str(value._get_all_var_data()))
            self.assertIn(field_name, str(value._get_all_var_data()))

    def test_real_catalog_templates_execute_with_literal_dynamic_values(self):
        title = 'First line\nZoë “雪” {name} {title} "$&" and \\ literal'
        examples = (
            (JOB_FEEDBACK_TEMPLATE_KEYS[0], {"title": title}),
            (JOB_FEEDBACK_TEMPLATE_KEYS[1], {"added": "2", "skipped": "7"}),
            (JOB_FEEDBACK_TEMPLATE_KEYS[2], {"added": "2"}),
            (
                JOB_FEEDBACK_TEMPLATE_KEYS[3],
                {"network_label": 'X\n"$& {title}'},
            ),
        )
        locales = ("en", "fr", "ar", "ja")
        cases: list[tuple[str, str, str, tuple[str, ...]]] = []
        for locale in locales:
            for template, captures in examples:
                source = template
                for slot, capture in captures.items():
                    source = source.replace("{" + slot + "}", capture)
                expression = job_feedback(source)._js_expr
                for key in JOB_FEEDBACK_TEMPLATE_KEYS:
                    expression = expression.replace(
                        str(ui(key)),
                        json.dumps(translate(locale, key), ensure_ascii=False),
                    )
                expression = expression.replace(
                    str(ui(source)),
                    json.dumps(translate(locale, source), ensure_ascii=False),
                )
                translated = translate(locale, template)
                expected = re.sub(
                    r"\{(title|added|skipped|network_label)\}",
                    lambda match: captures[match.group(1)],
                    translated,
                )
                cases.append(
                    (expression, expected, "template", tuple(captures.values()))
                )
                for capture in captures.values():
                    self.assertIn(capture, expected)

        literal_sources = (
            "Your session expired — please sign in again.",
            "That request is no longer open — it may have been withdrawn, already answered, or given to another helper.",
            "We couldn't load your Inbox just now. Please use Refresh to try again.",
            "Thank you — this report is private and now with our review team. Nothing is published and no one is accused publicly.",
            "Your device share sheet opened — finish the post in the app you picked.",
            "Sharing isn't available in this browser, so your caption and link were copied — paste them into the app.",
            "Share cancelled — nothing was posted.",
            "We couldn't open a share sheet or copy automatically. Select the caption above and copy it by hand.",
        )
        for locale in locales:
            for source in literal_sources:
                expression = job_feedback(source)._js_expr
                for key in JOB_FEEDBACK_TEMPLATE_KEYS:
                    expression = expression.replace(
                        str(ui(key)),
                        json.dumps(translate(locale, key), ensure_ascii=False),
                    )
                expression = expression.replace(
                    str(ui(source)),
                    json.dumps(translate(locale, source), ensure_ascii=False),
                )
                cases.append(
                    (expression, translate(locale, source), "literal", ())
                )

        unknown = 'A member-authored sentence with {title}, quotes " and $&'
        for locale in locales:
            expression = job_feedback(unknown)._js_expr
            for key in JOB_FEEDBACK_TEMPLATE_KEYS:
                expression = expression.replace(
                    str(ui(key)),
                    json.dumps(translate(locale, key), ensure_ascii=False),
                )
            expression = expression.replace(
                str(ui(unknown)),
                json.dumps(translate(locale, unknown), ensure_ascii=False),
            )
            cases.append((expression, unknown, "unknown", ()))

        script = (
            "const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
            "const results = cases.map((expression) => eval(expression));"
            "process.stdout.write(JSON.stringify(results));"
        )
        result = subprocess.run(
            ["node", "-e", script],
            input=json.dumps([case[0] for case in cases], ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
        )
        displayed_values = json.loads(result.stdout)
        self.assertEqual(len(displayed_values), len(cases))
        for displayed, (_expression, expected, case_type, captures) in zip(
            displayed_values, cases, strict=True
        ):
            with self.subTest(case_type=case_type, expected=expected):
                self.assertEqual(displayed, expected)
                for capture in captures:
                    self.assertIn(capture, displayed)

    async def test_share_callback_preserves_payload_and_canonicalizes_cancelled_or_unknown(
        self,
    ):
        state = MessagingState()
        state.share_caption = "Typed caption {title} $&"
        state.selected_thread = {
            **state.selected_thread,
            "story_note": "Original story note",
        }
        before_caption = state.share_caption
        before_story = state.selected_thread["story_note"]
        for outcome, source in (
            ("cancelled", "Share cancelled — nothing was posted."),
            (
                "unexpected-status",
                "We couldn't open a share sheet or copy automatically. Select the caption above and copy it by hand.",
            ),
        ):
            await run_event(state.share_result, outcome)
            self.assertEqual(state.share_note, source)
            self.assertEqual(state.share_caption, before_caption)
            self.assertEqual(state.selected_thread["story_note"], before_story)
            for locale in ("en", "fr", "ar", "ja"):
                display = translate(locale, state.share_note)
                self.assertEqual(display, translate(locale, source))

    def test_existing_catalog_groups_are_retained_and_feedback_helpers_unchanged(
        self,
    ):
        for source in (
            "Your session expired — please sign in again.",
            "Score all four categories",
        ):
            self.assertIn(source, COMPLETE_KEYS)
            for locale, _label in LANGUAGE_OPTIONS:
                if locale != "en":
                    self.assertNotEqual(translate(locale, source), source)
        from app.components.feedback import error_banner, success_banner

        self.assertTrue(error_banner("External state message").render())
        self.assertTrue(success_banner("External state message").render())
        self.assertIn(
            "rx.el.p(message", __import__("inspect").getsource(error_banner)
        )
        self.assertIn(
            "rx.el.p(\n                message",
            __import__("inspect").getsource(success_banner),
        )


if __name__ == "__main__":
    unittest.main()
