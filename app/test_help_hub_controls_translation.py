import ast
import re
import unittest
from collections import Counter
from pathlib import Path

import reflex as rx

from app.interface_catalog_help_hub_controls import (
    HELP_HUB_CONTROL_CATALOGS,
    HELP_HUB_CONTROL_KEYS,
)
from app.interface_catalog_help_hub_details import (
    HELP_HUB_DETAIL_CATALOGS,
    HELP_HUB_DETAIL_KEYS,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate
from app.models import LANGUAGE_OPTIONS
from app.scripts.audit_interface_copy import analyze_source
from app.states.help_hub_state import (
    REWARD_CHOICES,
    ConfirmedHelper,
    HelperUpcoming,
    HelpOffer,
)
from app.states.help_post_state import RecentPost
from app.components.help_hub_panel import (
    confirmed_helper_card,
    help_hub_panel,
    help_offer_card,
    own_request_body,
    post_help_form,
    rewards_field,
    upcoming_help_body,
)


class HelpHubControlsTranslationTests(unittest.TestCase):
    def test_catalogs_are_strictly_complete_and_registered(self):
        locales = {code for code, _label in LANGUAGE_OPTIONS} - {"en"}
        groups = (
            (HELP_HUB_CONTROL_KEYS, HELP_HUB_CONTROL_CATALOGS),
            (HELP_HUB_DETAIL_KEYS, HELP_HUB_DETAIL_CATALOGS),
        )
        sources = [source for keys, _catalogs in groups for source in keys]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertTrue(set(sources) <= set(COMPLETE_KEYS))
        for keys, catalogs in groups:
            self.assertEqual(set(catalogs), locales)
            for locale in locales:
                self.assertEqual(set(catalogs[locale]), set(keys))
                for source in keys:
                    self.assertIn(source, CATALOGS[locale])
                    self.assertEqual(
                        translate(locale, source), CATALOGS[locale][source]
                    )
                    self.assertTrue(CATALOGS[locale][source].strip())
                    self.assertNotEqual(CATALOGS[locale][source], source)
                    self.assertEqual(
                        Counter(
                            re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", source)
                        ),
                        Counter(
                            re.findall(
                                r"\{([A-Za-z][A-Za-z0-9_]*)\}",
                                CATALOGS[locale][source],
                            )
                        ),
                    )
        for source in sources:
            self.assertEqual(translate("en", source), source)
            self.assertEqual(translate("unsupported", source), source)

    def test_actual_static_ui_and_field_label_sources_are_covered(self):
        source_path = Path("app/components/help_hub_panel.py")
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        owned_sources: set[str] = set()
        field_label_sources: set[str] = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "ui"
                and node.args
                and isinstance(node.args[0], ast.Subscript)
            ):
                lookup = node.args[0]
                self.assertIsInstance(lookup.value, ast.Name)
                self.assertEqual(lookup.value.id, "item")
                self.assertIsInstance(lookup.slice, ast.Constant)
                self.assertIn(lookup.slice.value, {"label", "blurb"})
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Name
            ):
                continue
            if node.func.id == "ui" and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(
                    value.value, str
                ):
                    owned_sources.add(value.value)
            if node.func.id == "field_label":
                for value in node.args[:2]:
                    if isinstance(value, ast.Constant) and isinstance(
                        value.value, str
                    ):
                        owned_sources.add(value.value)
                        field_label_sources.add(value.value)
            helper_positions = {
                "mode_button": (0,),
                "clock_select": (1,),
                "quote_control": (2,),
                "person_header": (4,),
            }
            for position in helper_positions.get(node.func.id, ()):
                if len(node.args) > position:
                    value = node.args[position]
                    if isinstance(value, ast.Constant) and isinstance(
                        value.value, str
                    ):
                        owned_sources.add(value.value)
        expected_helpers = {
            "Where",
            "Help days",
            "Hours required",
            "Tools",
            "Knowledge and skills",
            "No tools listed",
            "No special skills needed",
            "No special skills listed",
            "Exact meeting place",
            "Not shared yet",
            "Location to agree",
            "Date time and duration",
            "Helper proposes",
            "Waiting on you",
            "Profile photo",
            "Your profile photo",
            "New activity on this job",
            "New activity on this request",
            "New activity on this help request",
            "Your help request totals",
            "Your help summary",
            "1 person required",
        }
        self.assertTrue(expected_helpers <= owned_sources)
        findings = analyze_source(source_path.read_text(encoding="utf-8"))
        raw_copy = {
            str(finding["source"])
            for finding in findings
            if finding["kind"] == "raw copy"
        }
        self.assertEqual(raw_copy - field_label_sources, set())
        self.assertEqual(
            {
                str(finding["source"])
                for finding in findings
                if finding["kind"] == "template audit"
            },
            {" Requested", " Open", " Upcoming", "Offered "},
        )
        missing = {
            (locale, source)
            for locale, _label in LANGUAGE_OPTIONS
            if locale != "en"
            for source in owned_sources
            if source not in CATALOGS[locale]
        }
        self.assertEqual(missing, set())

    def test_reward_metadata_is_native_ui_copy_without_changing_values(self):
        self.assertEqual(
            [
                (item["value"], item["label"], item["blurb"])
                for item in REWARD_CHOICES
            ],
            [
                ("money", "Money", "Set a budget or ask for a quote"),
                ("refreshments", "Refreshments", "Drinks and snacks"),
                ("meal", "A meal", "Lunch, Dinner, Cakes"),
                ("accommodation", "Accommodation", "Work and stay"),
                ("guided_tour", "Guided tour", "I will show you around"),
                ("activity", "Activity", "Cook, Hike, Surf..."),
                ("other_reward", "Other reward", "Anything else"),
            ],
        )
        for item in REWARD_CHOICES:
            for locale, _label in LANGUAGE_OPTIONS:
                if locale != "en":
                    self.assertIn(item["label"], CATALOGS[locale])
                    self.assertIn(item["blurb"], CATALOGS[locale])
        panel_source = Path("app/components/help_hub_panel.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('ui(item["label"])', panel_source)
        self.assertIn('ui(item["blurb"])', panel_source)

    def test_components_build_with_property_backed_typed_record_fixtures(self):
        upcoming: HelperUpcoming = {
            "id": 1,
            "post_id": 2,
            "application_id": 3,
            "proposal_id": 0,
            "proposal_when": "",
            "proposal_mine": False,
            "can_respond": False,
            "title": "",
            "description": "",
            "location": "",
            "location_mode": "approximate",
            "accepted_location": "",
            "dates": "",
            "start_time": "",
            "hours": "",
            "tools": "",
            "knowledge": "",
            "status": "",
            "other_id": 4,
            "other_name": "",
            "other_avatar_seed": "",
            "other_avatar": "",
            "other_verified": False,
            "directions_url": "",
        }
        offer: HelpOffer = {
            "id": 1,
            "post_id": 2,
            "key": "fixture",
            "title": "",
            "description": "",
            "location": "",
            "dates": "",
            "start_time": "",
            "hours": "",
            "tools": "",
            "knowledge": "",
            "pitch": "",
            "proposed": "",
            "applied": "",
            "helper_name": "",
            "helper_avatar_seed": "",
            "helper_handle": "",
            "helper_avatar": "",
            "helper_verified": False,
        }
        confirmed: ConfirmedHelper = {
            "id": 1,
            "post_id": 2,
            "application_id": 3,
            "thread_id": 4,
            "proposal_id": 0,
            "proposal_when": "",
            "proposal_mine": False,
            "can_respond": False,
            "location_mode": "approximate",
            "accepted_location": "",
            "needs_accepted": False,
            "title": "",
            "description": "",
            "location": "",
            "dates": "",
            "start_time": "",
            "hours": "",
            "tools": "",
            "knowledge": "",
            "status": "",
            "helper_id": 5,
            "helper_name": "",
            "helper_avatar_seed": "",
            "helper_handle": "",
            "helper_avatar": "",
            "helper_verified": False,
            "helper_rating": 0.0,
            "helper_rating_count": 0,
            "schedule_time": "",
            "schedule_date": "",
            "directions_url": "",
        }
        recent: RecentPost = {
            "id": 1,
            "title": "",
            "description": "",
            "category": "",
            "category_label": "",
            "reward_label": "",
            "reward_details": "",
            "location": "",
            "scheduled": "",
            "scheduled_iso": "",
            "is_custom_reward": False,
            "status": "",
            "urgency": "",
            "created": "",
            "photos": [],
            "helpers_needed": 1,
            "duration_minutes": 0,
            "tools": "",
            "knowledge_skills": "",
            "accepted_location_name": "",
            "date_time_duration": "",
            "can_edit": False,
        }
        upcoming_var = rx.Var.create(upcoming).to(HelperUpcoming)
        offer_var = rx.Var.create(offer).to(HelpOffer)
        confirmed_var = rx.Var.create(confirmed).to(ConfirmedHelper)
        recent_var = rx.Var.create(recent).to(RecentPost)
        components = (
            help_hub_panel(),
            post_help_form(),
            rewards_field(),
            upcoming_help_body(upcoming_var),
            help_offer_card(offer_var, detail_body=True),
            confirmed_helper_card(confirmed_var, compact=True),
            own_request_body(recent_var),
        )
        self.assertEqual(len(components), 7)
        self.assertTrue(all(component is not None for component in components))


if __name__ == "__main__":
    unittest.main()
