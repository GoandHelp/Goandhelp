import reflex as rx

import ast
import unittest
from pathlib import Path

from app.interface_i18n import CATALOGS, COMPLETE_KEYS, catalog, translate
from app.interface_catalog_auth import AUTH_COPY_KEYS
from app.interface_catalog_map import MAP_COPY_KEYS
from app.interface_catalog_reviews import REVIEW_KEYS
from app.interface_catalog_shared import SHARED_KEYS
from app.interface_catalog_settings import SETTINGS_KEYS
from app.interface_catalog_onboarding import LANGUAGE_CHOICE_KEYS
from app.models import LANGUAGE_OPTIONS
from app.scripts.audit_interface_copy import analyze_source
from app.states.auth_state import AuthState


class OfflineCoverageTests(unittest.TestCase):
    def test_completed_source_groups_cover_every_offered_locale(self):
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(COMPLETE_KEYS), len(set(COMPLETE_KEYS)))
        self.assertGreaterEqual(len(COMPLETE_KEYS), 160)
        for language, _ in LANGUAGE_OPTIONS:
            if language == "en":
                for source in COMPLETE_KEYS:
                    self.assertEqual(translate(language, source), source)
                continue
            with self.subTest(language=language):
                self.assertTrue(set(COMPLETE_KEYS) <= CATALOGS[language].keys())
                for source in COMPLETE_KEYS:
                    text = CATALOGS[language][source]
                    self.assertIsInstance(text, str)
                    self.assertTrue(text.strip(), source)
                    self.assertNotIn("\ufffd", text)
                    self.assertFalse(
                        text.startswith((f"[{language}]", f"{language}:")),
                        source,
                    )
                    self.assertNotIn("TODO", text)
                    self.assertNotIn("TRANSLATE_ME", text)
                for source in (
                    "Continue",
                    "Read more",
                    "Let's go!",
                    "No conversations yet",
                    "Could not save language. Please try again.",
                    "I agree to the Terms and User Agreement (required)",
                    "No reviews waiting to be written.",
                ):
                    self.assertNotEqual(translate(language, source), source)

    def test_catalog_groups_are_in_the_completion_manifest(self):
        for keys in (
            AUTH_COPY_KEYS,
            MAP_COPY_KEYS,
            REVIEW_KEYS,
            SHARED_KEYS,
            SETTINGS_KEYS,
            LANGUAGE_CHOICE_KEYS,
        ):
            self.assertTrue(set(keys) <= set(COMPLETE_KEYS))

    def test_copy_and_catalog_mutation_contract(self):
        self.assertEqual(
            translate("es", "Job description"), "Descripción de la tarea"
        )
        self.assertEqual(translate("fr", "First name"), "Prénom")
        self.assertEqual(translate("zh", "Read more"), "阅读更多")
        first = catalog("ja")
        first["Read more"] = "changed"
        self.assertEqual(translate("ja", "Read more"), "続きを読む")
        self.assertEqual(translate("unknown", "Read more"), "Read more")

    def test_auth_feedback_switches_without_changing_source_or_member_data(
        self,
    ):
        state = AuthState(_reflex_internal_init=True)
        state.error = "We couldn't match that email and password."
        state.display_name = "Maya De Silva"
        original = state.error
        for language, _ in LANGUAGE_OPTIONS:
            state.preferred_language = language
            self.assertEqual(
                state.localized_error, translate(language, original)
            )
            self.assertEqual(state.error, original)
            self.assertEqual(state.display_name, "Maya De Silva")
            self.assertEqual(
                state.interface_text.get("Read more", "Read more"),
                translate(language, "Read more"),
            )
        for language in ("ar", "he", "fa"):
            state.preferred_language = language
            self.assertEqual(state.interface_direction, "rtl")
        state.preferred_language = "fr"
        self.assertEqual(state.interface_direction, "ltr")

    def test_language_persistence_and_optimistic_switch_are_retained(self):
        source = Path("app/states/auth_state.py").read_text()
        handler = source.split("async def update_language", 1)[1]
        self.assertLess(
            handler.index("self.preferred_language = language"),
            handler.index("async with rx.asession()"),
        )
        self.assertIn("self.preferred_language = previous", handler)
        self.assertIn("onboarding.interface_language = language", handler)
        self.assertIn('name="goandhelp_interface_language", sync=True', source)
        self.assertIn(
            "return translate(self.preferred_language, self.error)", source
        )

    def test_review_screen_copy_is_all_catalogued(self):
        source = Path("app/components/reviews_section.py").read_text()
        calls = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ui"
        ]
        keys = {
            node.args[0].value
            for node in calls
            if node.args and isinstance(node.args[0], ast.Constant)
        }
        self.assertTrue(set(REVIEW_KEYS) <= keys)
        self.assertTrue(keys <= set(COMPLETE_KEYS))

    def test_screen_wiring_and_language_independent_escape_focus(self):
        contracts = {
            "app/components/auth_panel.py": (
                'ui("Date of birth")',
                'ui("Phone")',
                "ui(item[1])",
                "error_banner(AuthState.localized_error)",
            ),
            "app/components/discover_panel.py": (
                'ui("People, jobs, places...")',
                'ui("Description")',
                'ui("Show on map")',
                'ui("Save search")',
            ),
            "app/components/messages_panel.py": (
                'ui("Send")',
                'ui("Sending…")',
            ),
            "app/components/community_panel.py": (
                'ui("Read more")',
                'ui("No replies yet")',
            ),
            "app/components/unified_inbox.py": (
                'ui("Loading contacts…")',
                'ui("Clear filters")',
                'ui("Back to Inbox")',
            ),
            "app/components/profile_tabs.py": (
                "ui(label)",
                'ui("Appearance")',
                'ui("Date display")',
                'ui("Distance units")',
            ),
            "app/components/map_utilities.py": (
                'ui("No notifications yet")',
                'ui("Loading notifications…")',
            ),
            "app/components/help_hub_panel.py": (
                'ui("Rewards")',
                'ui("No reviews yet")',
            ),
            "app/components/event_cards.py": (
                'ui("Description")',
                'ui("Job category")',
                'ui("Events")',
            ),
        }
        for path, snippets in contracts.items():
            source = Path(path).read_text()
            ast.parse(source)
            for snippet in snippets:
                self.assertIn(snippet, source, path)
        drawer = Path("app/components/discover_panel.py").read_text()
        self.assertIn(
            "document.getElementById('gah-map-filter-close')?.click()", drawer
        )
        self.assertIn("#gah-map-filter-open, #gah-board-filter-open", drawer)
        self.assertNotIn(
            "querySelector('[aria-label=\"Close Search filters\"]')", drawer
        )
        self.assertIn(
            'id="gah-map-filter-open"',
            Path("app/components/member_map.py").read_text(),
        )

    def test_member_content_never_becomes_a_catalog_lookup(self):
        for path, variables in {
            "app/components/community_panel.py": {"topic", "comment"},
            "app/components/reviews_section.py": {"review"},
            "app/components/unified_inbox.py": {"contact"},
            "app/components/member_map.py": {"post"},
        }.items():
            tree = ast.parse(Path(path).read_text())
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "ui"
                ):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Subscript) and isinstance(
                            child.value, ast.Name
                        ):
                            controlled_subject = (
                                child.value.id == "topic"
                                and isinstance(child.slice, ast.Constant)
                                and child.slice.value == "subject"
                            )
                            if not controlled_subject:
                                self.assertNotIn(
                                    child.value.id, variables, path
                                )
        original = Path("app/components/language_control.py").read_text()
        self.assertIn('custom_attrs={"translate": "no"}', original)
        self.assertNotIn('"translate": "yes"', original)
        self.assertIn('ui("Show original language")', original)
        auth = Path("app/components/auth_panel.py").read_text()
        self.assertIn('placeholder="Maya"', auth)
        self.assertIn('placeholder="De Silva"', auth)
        self.assertIn("value=item[0]", auth)

    def test_components_construct_with_reactive_copy(self):
        from app.components.auth_panel import birth_date_group
        from app.components.language_control import original_language_disclosure
        from app.components.profile_tabs import appearance_control
        from app.components.reviews_section import received_reviews_section
        from app.components.unified_inbox import empty_state

        for component in (
            birth_date_group(),
            appearance_control(),
            received_reviews_section(),
            empty_state(),
            original_language_disclosure("Bonjour Maya"),
        ):
            self.assertIsInstance(component, rx.Component)
            self.assertIsInstance(component.render(), dict)

    def test_audit_finds_raw_copy_catalog_gaps_and_templates(self):
        source = """import reflex as rx
from app.interface_i18n import ui
def example():
    return rx.el.div(
        rx.el.p("Novel authored hint"),
        rx.el.p(ui("Uncatalogued banner")),
        rx.el.input(placeholder="Another authored hint"),
        rx.el.p(f"Welcome {State.name}"),
        rx.el.p(State.member_post),
    )
"""
        findings = analyze_source(source)
        by_source = {item["source"]: item for item in findings}
        self.assertEqual(by_source["Novel authored hint"]["kind"], "raw copy")
        self.assertEqual(
            by_source["Uncatalogued banner"]["kind"], "catalog gap"
        )
        self.assertEqual(len(by_source["Uncatalogued banner"]["missing"]), 36)
        self.assertEqual(by_source["Welcome "]["kind"], "template audit")
        self.assertNotIn("State.member_post", by_source)
        self.assertEqual(analyze_source('rx.el.p(ui("Read more"))'), [])

    def test_incomplete_notice_remains_honest_and_localized(self):
        notice = LANGUAGE_CHOICE_KEYS[1]
        for path in (
            "app/components/onboarding.py",
            "app/components/profile_tabs.py",
        ):
            self.assertIn(notice, Path(path).read_text())
        for language, _ in LANGUAGE_OPTIONS:
            if language != "en":
                self.assertNotEqual(translate(language, notice), notice)


if __name__ == "__main__":
    unittest.main()
