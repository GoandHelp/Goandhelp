import reflex as rx

import ast
import inspect
import json
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path
from string import Formatter

from playwright.sync_api import sync_playwright

from app.components import (
    bookmark_tab,
    chat_controls,
    chat_safety,
    contacts_panel,
    feedback,
    footer,
    guest_filters,
    help_share,
    message_attachments,
    noncontact_panel,
)
from app.interface_catalog_shared_interface import (
    SHARED_INTERFACE_CATALOGS,
    SHARED_INTERFACE_KEYS,
    SHARED_INTERFACE_ROWS,
)
from app.interface_catalog_events import EVENT_KEYS
from app.interface_catalog_admin_ui import ADMIN_UI_CATALOGS
from app.interface_catalog_map_status import MAP_STATUS_CATALOGS
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template,
)
from app.models import LANGUAGE_OPTIONS
from app.scripts.capture_screenshots import BROWSER_ARGS, resolve_executable
from app.states.auth_state import AuthState
from app.states.guest_map_state import GuestMapState

EXPECTED_SOURCES = (
    "Not applicable",
    "No helpers match your filters",
    "No open jobs match your filters",
    "Language",
    "Email verified — confirms control of the email address, not real-world identity.",
    "Traveller avatar",
    "Contact profile photo",
    "Delete message",
    "Report message",
    "Already a contact",
    "Contact request pending",
    "Pending photo attachments",
    "Attaching…",
    "Attach photos",
    "Share request",
    "Close share options",
    "Copy link",
    "Share this help request",
    "Not a contact",
    "Close conversation",
    "Write a message",
    "Write your reply…",
    "No conversation selected",
    "Attach photos: JPEG, PNG or WebP, up to five, 3 MB each",
    "Message photo {number}",
    "Open message photo {number} at full size in a new tab",
    "Pending message photo {number}",
    "Remove pending photo {number}",
    "Share {title}",
    "Share via {service} (opens a new window)",
    "Remove {title} from your saved help requests",
    "Save {title} to your help requests",
)
MEMBER_VALUE = "$& {$&} {title} Ålesund 日本"
REUSED_SOURCES = (
    "Give help",
    "Email verified",
    "Open member profile",
    "Add contact",
    "Community in your hands",
    "Cancel",
    "Requests",
    "Decline",
    "Sending…",
    "Send",
    "No messages yet",
)


class SharedInterfaceTranslationTests(unittest.TestCase):
    def test_exact_locales_and_full_source_coverage(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(SHARED_INTERFACE_KEYS, EXPECTED_SOURCES)
        self.assertEqual(len(set(SHARED_INTERFACE_KEYS)), 32)
        self.assertEqual(set(SHARED_INTERFACE_CATALOGS), offered)
        self.assertEqual(set(SHARED_INTERFACE_ROWS), offered)
        self.assertTrue(set(EXPECTED_SOURCES) <= set(COMPLETE_KEYS))
        for locale, entries in SHARED_INTERFACE_CATALOGS.items():
            self.assertEqual(set(entries), set(EXPECTED_SOURCES), locale)
            self.assertEqual(len(SHARED_INTERFACE_ROWS[locale].split("|")), 32)
            for source, value in entries.items():
                with self.subTest(locale=locale, source=source):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertEqual(CATALOGS[locale][source], value)
                    self.assertEqual(translate(locale, source), value)
                    self.assertEqual(translate("en", source), source)
            for source in REUSED_SOURCES:
                self.assertTrue(CATALOGS[locale][source].strip())

    def test_literal_rows_and_exact_slot_multiplicity(self):
        tree = ast.parse(
            Path("app/interface_catalog_shared_interface.py").read_text()
        )
        rows = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SHARED_INTERFACE_ROWS"
        )
        self.assertEqual(ast.literal_eval(rows), SHARED_INTERFACE_ROWS)
        self.assertIsInstance(rows, ast.Dict)
        self.assertTrue(
            all(isinstance(value, ast.Constant) for value in rows.values)
        )
        formatter = Formatter()
        for locale, entries in SHARED_INTERFACE_CATALOGS.items():
            for source, value in entries.items():
                expected = Counter(
                    slot for _, slot, _, _ in formatter.parse(source) if slot
                )
                actual = Counter(
                    slot for _, slot, _, _ in formatter.parse(value) if slot
                )
                self.assertEqual(expected, actual, (locale, source))
                self.assertNotIn("TODO", value)
                if len(source) > 30:
                    self.assertNotEqual(value, source, (locale, source))
            limits = entries[EXPECTED_SOURCES[23]]
            for token in ("JPEG", "PNG", "WebP", "3 MB"):
                self.assertIn(token, limits, locale)

    def test_prior_catalogs_and_truthful_incomplete_notice_retained(self):
        self.assertTrue(set(EVENT_KEYS) <= set(COMPLETE_KEYS))
        for locale, _ in LANGUAGE_OPTIONS:
            if locale == "en":
                continue
            self.assertTrue(set(EVENT_KEYS) <= set(CATALOGS[locale]))
            for group in (ADMIN_UI_CATALOGS, MAP_STATUS_CATALOGS):
                for source, value in group[locale].items():
                    self.assertEqual(CATALOGS[locale][source], value)
            self.assertIn(
                "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language.",
                CATALOGS[locale],
            )
        manifest = inspect.getsource(
            __import__("app.interface_i18n", fromlist=["ui"])
        )
        self.assertIn("CATALOGS[_language].setdefault(_key, _value)", manifest)

    def test_template_expressions_preserve_values_and_dependency_hooks(self):
        for source in EXPECTED_SOURCES[24:]:
            slot = next(
                slot for _, slot, _, _ in Formatter().parse(source) if slot
            )
            for value in (MEMBER_VALUE, "5", GuestMapState.preview_title):
                with self.subTest(source=source, value=str(value)):
                    expression = ui_template(source, slot, value)
                    serialized = str(expression)
                    self.assertIn(f'.split("{{{slot}}}").join(', serialized)
                    self.assertNotIn(".replace(", serialized)
                    self.assertNotIn(".replaceAll(", serialized)
                    self.assertIs(expression._var_type, str)
                    self.assertTrue(rx.el.span(expression).render())
                    dependencies = expression._get_all_var_data()
                    self.assertIsNotNone(dependencies)
                    for data in (
                        ui(source)._get_all_var_data(),
                        rx.Var.create(value)._get_all_var_data(),
                    ):
                        if data is not None:
                            self.assertTrue(
                                set(data.hooks) <= set(dependencies.hooks)
                            )
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(ui),
        )
        auth_source = Path("app/states/auth_state.py").read_text()
        self.assertIn("return catalog(self.preferred_language)", auth_source)
        self.assertIn("self.preferred_language = language", auth_source)

    def test_offline_javascript_substitution_does_not_interpret_member_values(
        self,
    ):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=resolve_executable(
                    playwright.chromium.executable_path
                ),
                headless=True,
                args=list(BROWSER_ARGS),
            )
            try:
                page = browser.new_page()
                self.assertEqual(page.url, "about:blank")
                for locale in ("en", "fr", "ar"):
                    for source in EXPECTED_SOURCES[24:]:
                        slot = next(
                            slot
                            for _, slot, _, _ in Formatter().parse(source)
                            if slot
                        )
                        for value in (MEMBER_VALUE, "5", "WhatsApp"):
                            with self.subTest(
                                locale=locale, source=source, value=value
                            ):
                                expression = ui_template(source, slot, value)
                                localized = translate(locale, source)
                                compiled = str(expression).replace(
                                    str(ui(source)), json.dumps(localized)
                                )
                                actual = page.evaluate(
                                    "expr => { const isTrue = x => Boolean(x); return eval(expr); }",
                                    compiled,
                                )
                                self.assertEqual(
                                    actual,
                                    localized.replace(f"{{{slot}}}", value),
                                )
                page.close()
            finally:
                browser.close()

    def test_actual_shared_component_renders_use_reactive_lookups(self):
        title = rx.Var.create(MEMBER_VALUE)
        number = rx.Var.create(0)
        components = (
            (feedback.verified_badge(True), ("Email verified",)),
            (feedback.verified_tick(True), ("Email verified",)),
            (feedback.verified_chip(True), (EXPECTED_SOURCES[4],)),
            (
                feedback.avatar_with_tick("/placeholder.svg", True, "size-12"),
                ("Traveller avatar", "Open member profile"),
            ),
            (
                feedback.avatar_with_tick(
                    "/placeholder.svg", True, "size-12", "Contact profile photo"
                ),
                ("Contact profile photo",),
            ),
            (
                chat_controls.correspondence_bubble(
                    {
                        "id": 1,
                        "body": MEMBER_VALUE,
                        "mine": False,
                        "sent_at": "today",
                        "photos": ["test.jpg"],
                    },
                    "contact_message",
                ),
                (
                    EXPECTED_SOURCES[24],
                    EXPECTED_SOURCES[25],
                    "Delete message",
                    "Report message",
                ),
            ),
            (
                chat_safety.chat_safety(rx.Var.create(1), title),
                ("Already a contact", "Contact request pending", "Add contact"),
            ),
            (
                message_attachments.pending_photo(
                    rx.Var.create("test.jpg"), number
                ),
                (EXPECTED_SOURCES[26], EXPECTED_SOURCES[27]),
            ),
            (
                message_attachments.message_attachments(),
                (
                    "Pending photo attachments",
                    "Attaching…",
                    "Attach photos",
                    EXPECTED_SOURCES[23],
                ),
            ),
            (
                help_share.help_share(rx.Var.create(1), title, "test"),
                (
                    "Share request",
                    "Close share options",
                    "Copy link",
                    "Share this help request",
                    EXPECTED_SOURCES[28],
                    EXPECTED_SOURCES[29],
                ),
            ),
            (
                bookmark_tab.bookmark_tab(rx.Var.create(1), title),
                (EXPECTED_SOURCES[30], EXPECTED_SOURCES[31]),
            ),
            (footer.footer(), ("Language", "Community in your hands")),
            (contacts_panel.requests_section(), ("Requests", "Decline")),
            (contacts_panel.conversation_header(), ("Close conversation",)),
            (contacts_panel.message_history(), ("No messages yet",)),
            (
                contacts_panel.composer(),
                ("Write a message", "Sending…", "Send"),
            ),
            (
                contacts_panel.conversation_panel(),
                ("No conversation selected",),
            ),
            (
                noncontact_panel.compose_form(rx.Var.create(1), title),
                ("Write a message", "Cancel", "Sending…"),
            ),
            (
                noncontact_panel.thread_header(),
                ("Not a contact", "Close conversation"),
            ),
            (
                noncontact_panel.reply_composer(),
                ("Write your reply…", "Sending…", "Send"),
            ),
            (guest_filters.guest_rewards(), ("Not applicable",)),
            (
                guest_filters.guest_filter_status(),
                (
                    "No helpers match your filters",
                    "No open jobs match your filters",
                ),
            ),
        )
        for component, keys in components:
            rendered = str(component)
            self.assertTrue(component.render())
            for source in keys:
                with self.subTest(component=component.tag, source=source):
                    self.assertIn(str(ui(source)), rendered)

    def test_member_content_urls_and_helper_contracts_are_not_translated(self):
        source = Path("app/components/chat_controls.py").read_text()
        self.assertIn('msg["body"].to(str),', source)
        self.assertNotIn('ui(msg["body"]', source)
        self.assertNotIn('ui_template(msg["body"]', source)
        share_source = inspect.getsource(help_share.help_share)
        self.assertIn('href=link["href"]', share_source)
        self.assertIn('link["label"],', share_source)
        self.assertNotIn('ui(link["label"])', share_source)
        self.assertEqual(
            feedback._avatar_interface_label(MEMBER_VALUE), MEMBER_VALUE
        )
        member_var = rx.Var.create(MEMBER_VALUE)
        self.assertIs(feedback._avatar_interface_label(member_var), member_var)
        self.assertIn(
            'field_label(\n                "Write a message",',
            inspect.getsource(noncontact_panel.compose_form),
        )
        self.assertIn("ui(label)", inspect.getsource(feedback.field_label))
        attachment_source = inspect.getsource(
            message_attachments.message_attachments
        )
        self.assertIn("max_files=5", attachment_source)
        self.assertIn("max_size=3_000_000", attachment_source)


class GuestMarkerTranslationTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_state_tree_switches_generic_label_without_changing_payload(
        self,
    ):
        state = GuestMapState(_reflex_internal_init=True)
        auth = await state.get_state(AuthState)
        original_language = auth.preferred_language
        original_jobs = deepcopy(state.jobs)
        original_helpers = deepcopy(state.helpers)
        original_mode = state.browse_mode
        original_identity = (auth.subscriber_id, auth.email, auth.display_name)
        try:
            state.helpers = [{"code": "helper:test", "lat": 46.2, "lng": 6.1}]
            state.jobs = [
                {
                    "code": "job:test",
                    "title": MEMBER_VALUE,
                    "description": "Member description 日本",
                    "lat": 46.3,
                    "lng": 6.2,
                }
            ]
            jobs = deepcopy(state.jobs)
            helpers = deepcopy(state.helpers)
            for locale in ("fr", "ar", "en", "fr"):
                auth.preferred_language = locale
                state.browse_mode = "get"
                originals = deepcopy(state.map_markers)
                localized = await state.localized_map_markers
                self.assertEqual(
                    localized[0]["label"], translate(locale, "Give help")
                )
                self.assertEqual(originals[0]["label"], "Give help")
                self.assertEqual(
                    localized,
                    [
                        {**marker, "label": translate(locale, "Give help")}
                        for marker in originals
                    ],
                )
                state.browse_mode = "give"
                self.assertEqual(
                    await state.localized_map_markers, state.map_markers
                )
                self.assertEqual(
                    (await state.localized_map_markers)[0]["label"],
                    MEMBER_VALUE,
                )
            self.assertEqual(state.jobs, jobs)
            self.assertEqual(state.helpers, helpers)
            self.assertEqual(
                (auth.subscriber_id, auth.email, auth.display_name),
                original_identity,
            )
        finally:
            auth.preferred_language = original_language
            state.jobs = original_jobs
            state.helpers = original_helpers
            state.browse_mode = original_mode

    async def test_locale_dependency_and_canvas_binding_are_explicit(self):
        state_source = Path("app/states/guest_map_state.py").read_text()
        tree = ast.parse(state_source)
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "localized_map_markers"
        )
        body = ast.unparse(method)
        self.assertIn("await self.get_state(AuthState)", body)
        self.assertIn("auth.preferred_language", body)
        self.assertIn("self.map_markers", body)
        self.assertIn("rx.var", ast.unparse(method.decorator_list[0]))
        for forbidden in (
            "asession",
            "session(",
            "load_preview",
            "fetch_guest_preview",
            "update_language",
            "httpx",
        ):
            self.assertNotIn(forbidden, body)
        self.assertIn(
            "markers=GuestMapState.localized_map_markers",
            Path("app/components/guest_map.py").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
