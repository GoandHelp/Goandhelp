import ast
import inspect
import re
import textwrap
import unittest
from collections import Counter

from app.interface_catalog_help_post_feedback import (
    HELP_POST_FEEDBACK_CATALOGS,
    HELP_POST_FEEDBACK_KEYS,
)
from app.interface_catalog_help_post_status_feedback import (
    HELP_POST_STATUS_FEEDBACK_CATALOGS,
    HELP_POST_STATUS_FEEDBACK_KEYS,
)
from app.interface_catalog_help_post_validation import (
    HELP_POST_VALIDATION_CATALOGS,
    HELP_POST_VALIDATION_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS
from app.states.help_post_state import HelpPostState


class HelpPostFeedbackTranslationTests(unittest.TestCase):
    def test_all_owned_sources_have_native_catalog_entries_and_runtime_registration(
        self,
    ):
        locales = {code for code, _label in LANGUAGE_OPTIONS} - {"en"}
        groups = (
            (HELP_POST_VALIDATION_KEYS, HELP_POST_VALIDATION_CATALOGS),
            (HELP_POST_FEEDBACK_KEYS, HELP_POST_FEEDBACK_CATALOGS),
            (
                HELP_POST_STATUS_FEEDBACK_KEYS,
                HELP_POST_STATUS_FEEDBACK_CATALOGS,
            ),
        )
        sources = [source for keys, _catalogs in groups for source in keys]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertTrue(set(sources) <= set(COMPLETE_KEYS))
        for keys, catalogs in groups:
            self.assertEqual(set(catalogs), locales)
            for locale in locales:
                self.assertEqual(set(catalogs[locale]), set(keys))
                for source, value in catalogs[locale].items():
                    self.assertTrue(value.strip())
                    self.assertIn(source, CATALOGS[locale])
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )
                    self.assertNotEqual(value, source)
                    self.assertEqual(
                        Counter(
                            re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)
                        ),
                        Counter(
                            re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", value)
                        ),
                    )
        for source in sources:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unknown", source), source)

    def test_safe_parser_localizes_owned_patterns_and_preserves_payload(self):
        title = 'line one\\nCancel $& {count} "quoted"'
        success_source = f'"{title}" is live - helpers nearby can see it now. It repeats: Every 2 weeks.'
        upload_source = "Couldn't accept Cancel.png, Lunch & tea.jpg. Use static JPEG/JPG, PNG or WebP, maximum 3 MB per source. No video; stored results are under 1 MB. 2 photo(s) were skipped: 5 photos is the maximum."
        for locale in ("en", "fr", "ar", "ja", *HELP_POST_FEEDBACK_CATALOGS):
            localized_success = HelpPostState._localized_feedback_text(
                locale, success_source
            )
            self.assertIn(title, localized_success)
            self.assertIn(
                translate(locale, "Every {count} weeks").replace(
                    "{count}", "2"
                ),
                localized_success,
            )
            localized_upload = HelpPostState._localized_feedback_text(
                locale, upload_source
            )
            self.assertIn("Cancel.png, Lunch & tea.jpg", localized_upload)
            self.assertIn("2", localized_upload)
            self.assertEqual(
                HelpPostState._localized_feedback_text(locale, "Delete"),
                "Delete",
            )
            self.assertEqual(
                HelpPostState._localized_feedback_text(locale, "Time to agree"),
                "Time to agree",
            )
            self.assertEqual(
                HelpPostState._localized_feedback_text(
                    locale, "Unknown service message — please try again."
                ),
                "Unknown service message — please try again.",
            )

    def test_actual_producer_literals_are_covered(self):
        from app.membership import cap_message
        from app.request_draft import validate_request
        from app.skill_categories import category_limit_message

        producer_sources = "\n".join(
            textwrap.dedent(
                inspect.getsource(getattr(producer, "fn", producer))
            )
            for producer in (
                HelpPostState.create_post,
                HelpPostState.begin_edit,
                HelpPostState.save_edit,
                HelpPostState.handle_upload,
                HelpPostState._process_photos,
                HelpPostState.remove_photo,
                HelpPostState._update_schedule,
                HelpPostState.resume_schedule,
                HelpPostState.pause_schedule,
                HelpPostState.end_schedule,
                validate_request,
                cap_message,
                category_limit_message,
            )
        )
        parsed = ast.parse(producer_sources)
        actual_literals = {
            node.value
            for node in ast.walk(parsed)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        owned_literals = set(HELP_POST_VALIDATION_KEYS) | set(
            HELP_POST_STATUS_FEEDBACK_KEYS
        )
        dynamic_keys = {
            source for source in owned_literals if "{" in source
        } | {
            "You can attach up to 5 photos per help request.",
            "Choose at most 3 categories for one help request.",
            "Job info must stay within 500 characters.",
        }
        self.assertTrue((owned_literals - dynamic_keys) <= actual_literals)
        self.assertTrue(dynamic_keys <= owned_literals)
        self.assertIn("MAX_PHOTOS", producer_sources)
        self.assertIn("MAX_REQUEST_CATEGORIES", producer_sources)
        self.assertIn("JOB_INFO_MAX_CHARS", producer_sources)
        self.assertIn("Help request updated.", actual_literals)
        self.assertIn("Help request posted.", actual_literals)

    def test_owned_cadence_forms_and_existing_feedback_fields(self):
        for locale in ("en", "fr", "ar", "ja"):
            for unit in ("day", "week", "month"):
                source = f'"Garden\n$& {{count}}" is live - helpers nearby can see it now. It repeats: Every 2 {unit}s.'
                rendered = HelpPostState._localized_feedback_text(
                    locale, source
                )
                self.assertIn("Garden\n$& {count}", rendered)
                self.assertIn("{count}", rendered)
        state = HelpPostState()
        feedback_implementation = inspect.getsource(HelpPostState)
        self.assertIn("auth.preferred_language", feedback_implementation)
        for field in (
            "error",
            "success",
            "photo_error",
            "photo_notice",
            "schedule_error",
            "schedule_notice",
            "edit_error",
        ):
            self.assertIn(field, feedback_implementation)
        self.assertEqual(state.error, "")
        self.assertEqual(state.success, "")
        self.assertEqual(state.photo_error, "")
        self.assertEqual(state.photo_notice, "")
        self.assertEqual(state.schedule_error, "")
        self.assertEqual(state.schedule_notice, "")
        self.assertEqual(state.edit_error, "")


if __name__ == "__main__":
    unittest.main()
