import ast
import inspect
import unittest
from pathlib import Path

import reflex as rx

from app.components.messages_panel import (
    category_score_chip,
    category_star,
    hub_empty,
    inbox_disclosure,
    report_category_option,
    review_category_row,
)
from app.components.request_heading import request_heading
from app.interface_catalog_events import EVENT_KEYS
from app.interface_catalog_inbox_contacts import INBOX_CONTACT_KEYS
from app.interface_catalog_inbox_direct import INBOX_DIRECT_KEYS
from app.interface_catalog_inbox_feed import INBOX_FEED_KEYS
from app.interface_catalog_job_conversation import (
    JOB_CONVERSATION_CATALOGS,
    JOB_CONVERSATION_KEYS,
    JOB_CONVERSATION_ROWS,
)
from app.interface_catalog_shared import SHARED_KEYS
from app.interface_catalog_shared_interface import SHARED_INTERFACE_KEYS
from app.interface_catalog_skills_prompt import SKILLS_PROMPT_KEYS
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui_template_multi,
)
from app.models import LANGUAGE_OPTIONS, SAFETY_REPORT_CATEGORY_LABELS
from app.states.messaging_state import MessagingState


class JobConversationTranslationTests(unittest.TestCase):
    def test_new_catalog_has_exact_offered_locale_and_source_coverage(self):
        offered = {code for code, _label in LANGUAGE_OPTIONS}
        expected_locales = offered - {"en"}
        self.assertEqual(len(offered), 37)
        self.assertEqual(len(expected_locales), 36)
        self.assertEqual(set(JOB_CONVERSATION_ROWS), expected_locales)
        self.assertEqual(set(JOB_CONVERSATION_CATALOGS), expected_locales)
        self.assertEqual(
            len(JOB_CONVERSATION_KEYS), len(set(JOB_CONVERSATION_KEYS))
        )
        for locale in expected_locales:
            with self.subTest(locale=locale):
                self.assertEqual(
                    set(JOB_CONVERSATION_CATALOGS[locale]),
                    set(JOB_CONVERSATION_KEYS),
                )
                for source in JOB_CONVERSATION_KEYS:
                    translated = JOB_CONVERSATION_CATALOGS[locale][source]
                    self.assertTrue(translated.strip())
                    self.assertNotEqual(translated, source)
                    self.assertEqual(CATALOGS[locale][source], translated)
                    self.assertEqual(translate(locale, source), translated)
                    self.assertEqual(translate("en", source), source)

    def test_existing_full_catalog_groups_remain_registered(self):
        groups = (
            EVENT_KEYS,
            SHARED_KEYS,
            SHARED_INTERFACE_KEYS,
            INBOX_CONTACT_KEYS,
            INBOX_DIRECT_KEYS,
            INBOX_FEED_KEYS,
            SKILLS_PROMPT_KEYS,
            JOB_CONVERSATION_KEYS,
        )
        self.assertTrue(all(set(keys) <= set(COMPLETE_KEYS) for keys in groups))
        for locale, _label in LANGUAGE_OPTIONS:
            if locale == "en":
                continue
            for keys in groups:
                with self.subTest(locale=locale, source=keys[0]):
                    self.assertTrue(set(keys) <= set(CATALOGS[locale]))

    def test_canonical_review_and_report_metadata_is_localized_in_components(
        self,
    ):
        item = rx.Var.create(
            {"field": "category_one", "label": "Timeliness", "score": "4"}
        ).to(dict[str, str])
        field = review_category_row(item)
        self.assertTrue(field.render())
        self.assertTrue(category_score_chip(item).render())
        star = category_star(
            rx.Var.create("category_one").to(str),
            rx.Var.create(4).to(int),
            rx.Var.create(3).to(int),
            rx.Var.create("Timeliness").to(str),
        )
        self.assertTrue(star.render())

        option = report_category_option(
            {"value": "rude_behaviour", "label": "Rude behaviour"}
        )
        self.assertEqual(option.tag, "option")
        self.assertEqual(
            str(option.value), str(rx.Var.create("rude_behaviour"))
        )
        self.assertIn("interface_text", str(option))
        self.assertTrue(
            set(SAFETY_REPORT_CATEGORY_LABELS.values()) <= set(CATALOGS["fr"])
        )
        for locale, _label in LANGUAGE_OPTIONS:
            if locale != "en":
                self.assertTrue(
                    all(
                        label in CATALOGS[locale]
                        for label in SAFETY_REPORT_CATEGORY_LABELS.values()
                    )
                )

    def test_component_templates_keep_dynamic_member_values_out_of_lookup(self):
        source = "{name} received your help with {title}."
        dynamic_values = {
            "name": rx.Var.create("$& {title} 'Zoë'\n名").to(str),
            "title": rx.Var.create('{name} +\nrepaired "bikes"').to(str),
        }
        value = ui_template_multi(source, dynamic_values)
        expression = value._js_expr
        self.assertIn(".replace(new RegExp", expression)
        self.assertIn("(match, slot) =>", expression)
        self.assertIn('"name"', expression)
        self.assertIn('"title"', expression)
        self.assertIn("$&", expression)
        self.assertIn("Zoë", expression)
        self.assertIn("名", expression)
        self.assertIsNotNone(value._get_all_var_data())
        self.assertIn("interface_text", str(value._get_all_var_data()))
        for inserted in dynamic_values.values():
            self.assertTrue(inserted._get_all_var_data())

    def test_rating_and_photo_count_display_logic_uses_canonical_numeric_state(
        self,
    ):
        source = inspect.getsource(category_score_chip)
        self.assertIn('"{score} out of 5"', source)
        self.assertIn(":.1f", source)
        star_source = inspect.getsource(category_star)
        self.assertIn('"{category}: {score} out of 5 stars"', star_source)
        panel_source = inspect.getsource(
            __import__(
                "app.components.messages_panel",
                fromlist=["job_conversation_panel"],
            ).job_conversation_panel
        )
        self.assertIn('selected_thread["is_completed"]', panel_source)
        self.assertIn("awaiting_other_confirm", panel_source)
        self.assertIn('selected_thread["can_complete"]', panel_source)

        state_source = inspect.getsource(MessagingState)
        self.assertIn(
            "max(\n            0, COMPLETED_TASK_PHOTO_MAX_COUNT - len(self.completion_photos)",
            state_source,
        )
        self.assertIn("sum(scores) / 4:.1f", state_source)
        self.assertIn("all(1 <= s <= 5 for s in scores)", state_source)
        panel_text = Path("app/components/messages_panel.py").read_text()
        panel_tree = ast.parse(panel_text)
        labels = {
            node.args[0].value
            for node in ast.walk(panel_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ui"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        self.assertTrue(
            {
                "All 5 photo slots used",
                "1 photo slot left",
                "Score all four categories",
            }
            <= labels
        )
        self.assertIn('"{count} photo slots left"', panel_text)
        self.assertIn('"Overall {score} out of 5"', panel_text)
        photo_source = inspect.getsource(
            __import__(
                "app.components.messages_panel", fromlist=["photo_uploader"]
            ).photo_uploader
        )
        self.assertIn("MessagingState.photo_slots_left", photo_source)
        self.assertIn('(0, ui("All 5 photo slots used"))', photo_source)
        self.assertIn('(1, ui("1 photo slot left"))', photo_source)

    def test_service_names_and_callback_values_remain_canonical(self):
        panel = Path("app/components/messages_panel.py").read_text()
        for brand in (
            "Telegram",
            "WhatsApp",
            "Facebook",
            '"X"',
            "Pinterest",
            "Instagram",
            "TikTok",
        ):
            self.assertIn(brand, panel)
        self.assertIn(
            'share_link_button(\n            "email", ui("Email")', panel
        )
        self.assertIn(
            "on_click=lambda: MessagingState.share_via_device(label)", panel
        )
        self.assertIn('"telegram": (', inspect.getsource(MessagingState))

    def test_helper_localization_does_not_rewrite_user_authored_fields(self):
        panel = Path("app/components/messages_panel.py").read_text()
        self.assertIn('name="body"', panel)
        self.assertIn('name="comment"', panel)
        self.assertIn('name="response"', panel)
        self.assertIn('name="details"', panel)
        self.assertIn("default_value=MessagingState.share_text", panel)
        self.assertIn('review["comment"]', panel)
        self.assertIn('review["response"]', panel)
        self.assertIn('photo["uploader_name"]', panel)
        self.assertIn('offer["title"]', panel)
        self.assertIn('request["post_title"]', panel)
        self.assertIn(
            '"Nothing you write here is shown to the other person or published anywhere. We never accuse anyone in public, and an account is never suspended automatically because of a report."',
            panel,
        )
        self.assertIn(
            '"Only the caption travels with the link. Go and Help does not keep a copy of anything you post elsewhere."',
            panel,
        )
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(
                __import__("app.interface_i18n", fromlist=["ui"])
            ),
        )

    def test_helper_based_headers_keep_their_canonical_string_contracts(self):
        panel_module = __import__(
            "app.components.messages_panel",
            fromlist=["compose_area", "compact_heading"],
        )
        self.assertTrue(panel_module.compose_area().render())
        self.assertTrue(
            hub_empty(
                "No offers from helpers", "A new offer appears here.", "inbox"
            ).render()
        )
        self.assertTrue(
            inbox_disclosure(
                "Offers to help you",
                rx.Var.create(1).to(int),
                rx.Var.create(False).to(bool),
                MessagingState.load_threads,
                "offers",
            ).render()
        )
        self.assertTrue(
            request_heading("Offers to help you", rx.Var.create(1)).render()
        )
        self.assertIn(
            'inbox_subview_header("Write a message"',
            inspect.getsource(panel_module.compose_area),
        )


if __name__ == "__main__":
    unittest.main()
