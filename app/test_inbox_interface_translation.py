import ast
import inspect
import json
import shutil
import subprocess
import unittest
from collections import Counter
from pathlib import Path
from string import Formatter

import reflex as rx

from app.components import (
    chat_controls,
    contacts_panel,
    feedback,
    noncontact_panel,
    unified_inbox,
)
from app.interface_catalog_events import EVENT_KEYS
from app.interface_catalog_shared import SHARED_KEYS
from app.interface_catalog_shared_interface import SHARED_INTERFACE_KEYS
from app.interface_catalog_inbox_contacts import (
    INBOX_CONTACT_CATALOGS,
    INBOX_CONTACT_KEYS,
    INBOX_CONTACT_ROWS,
)
from app.interface_catalog_inbox_direct import (
    INBOX_DIRECT_CATALOGS,
    INBOX_DIRECT_KEYS,
    INBOX_DIRECT_ROWS,
)
from app.interface_catalog_inbox_feed import (
    INBOX_FEED_CATALOGS,
    INBOX_FEED_KEYS,
    INBOX_FEED_ROWS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    translate,
    ui,
    ui_template,
)
from app.models import LANGUAGE_OPTIONS
from app.states.contacts_state import ContactsState

LOCALES = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
CATALOG_GROUPS = (
    (INBOX_CONTACT_KEYS, INBOX_CONTACT_ROWS, INBOX_CONTACT_CATALOGS),
    (INBOX_DIRECT_KEYS, INBOX_DIRECT_ROWS, INBOX_DIRECT_CATALOGS),
    (INBOX_FEED_KEYS, INBOX_FEED_ROWS, INBOX_FEED_CATALOGS),
)
ALL_INBOX_KEYS = tuple(
    dict.fromkeys(key for keys, _, _ in CATALOG_GROUPS for key in keys)
)
MEMBER_VALUE = '$& {name} {type} "quoted"\nÅlesund 日本'


class InboxInterfaceCatalogTests(unittest.TestCase):
    def test_all_catalog_groups_have_exact_locale_and_source_parity(self):
        self.assertEqual(len(LOCALES), 36)
        for keys, rows, catalogs in CATALOG_GROUPS:
            with self.subTest(group=keys[0]):
                self.assertEqual(set(rows), LOCALES)
                self.assertEqual(set(catalogs), LOCALES)
                self.assertEqual(len(keys), len(set(keys)))
                for locale in LOCALES:
                    self.assertEqual(set(catalogs[locale]), set(keys), locale)
                    self.assertEqual(len(rows[locale].split("|")), len(keys))
                    for source, translated in catalogs[locale].items():
                        with self.subTest(locale=locale, source=source):
                            self.assertTrue(translated.strip())
                            if len(source) > 24:
                                self.assertNotEqual(source, translated)
                            self.assertTrue(CATALOGS[locale][source].strip())
                            if len(source) > 24:
                                self.assertNotEqual(
                                    CATALOGS[locale][source], source
                                )
                            self.assertEqual(
                                translate(locale, source),
                                CATALOGS[locale][source],
                            )
                            self.assertEqual(translate("en", source), source)
                            expected_slots = Counter(
                                slot
                                for _, slot, _, _ in Formatter().parse(source)
                                if slot
                            )
                            actual_slots = Counter(
                                slot
                                for _, slot, _, _ in Formatter().parse(
                                    translated
                                )
                                if slot
                            )
                            self.assertEqual(expected_slots, actual_slots)
                            self.assertNotIn("TODO", translated)
        self.assertTrue(set(ALL_INBOX_KEYS) <= set(COMPLETE_KEYS))

    def test_catalog_rows_are_literal_static_data_and_prior_catalogs_remain(
        self,
    ):
        modules = (
            (
                "app/interface_catalog_inbox_contacts.py",
                "INBOX_CONTACT_ROWS",
                INBOX_CONTACT_ROWS,
            ),
            (
                "app/interface_catalog_inbox_direct.py",
                "INBOX_DIRECT_ROWS",
                INBOX_DIRECT_ROWS,
            ),
            (
                "app/interface_catalog_inbox_feed.py",
                "INBOX_FEED_ROWS",
                INBOX_FEED_ROWS,
            ),
        )
        for file_name, name, expected in modules:
            tree = ast.parse(Path(file_name).read_text())
            node = next(
                item
                for item in tree.body
                if isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == name
            )
            self.assertEqual(ast.literal_eval(node.value), expected)
            self.assertIsInstance(node.value, ast.Dict)
            self.assertTrue(
                all(
                    isinstance(value, ast.Constant)
                    for value in node.value.values
                )
            )
        self.assertTrue(set(EVENT_KEYS) <= set(COMPLETE_KEYS))
        self.assertTrue(set(SHARED_KEYS) <= set(COMPLETE_KEYS))
        self.assertTrue(set(SHARED_INTERFACE_KEYS) <= set(COMPLETE_KEYS))
        for locale in LOCALES:
            self.assertTrue(set(EVENT_KEYS) <= set(CATALOGS[locale]))
            self.assertTrue(set(SHARED_INTERFACE_KEYS) <= set(CATALOGS[locale]))
        self.assertEqual(CATALOGS["fr"]["Find people"], "Trouver des personnes")
        self.assertEqual(CATALOGS["es"]["Find people"], "Buscar personas")
        interface_source = inspect.getsource(
            __import__("app.interface_i18n", fromlist=["ui"])
        )
        self.assertIn(
            "CATALOGS[_language].setdefault(_key, _value)", interface_source
        )

    def test_every_inbox_copy_source_is_bound_through_ui_or_canonical_wrapper(
        self,
    ):
        files = (
            "app/components/contacts_panel.py",
            "app/components/noncontact_panel.py",
            "app/components/unified_inbox.py",
        )
        wrapped_sources: set[str] = set()
        for file_name in files:
            tree = ast.parse(Path(file_name).read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                function = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else getattr(node.func, "attr", "")
                )
                if function in {
                    "ui",
                    "ui_template",
                    "field_label",
                    "inbox_subview_header",
                }:
                    for argument in (
                        node.args[:2]
                        if function == "field_label"
                        else node.args[:1]
                    ):
                        if isinstance(argument, ast.Constant) and isinstance(
                            argument.value, str
                        ):
                            wrapped_sources.add(argument.value)
        dynamic_canonical_sources = {
            "Request pending",
            "Contacts",
            "Request declined",
            "Contact removed",
            "Contact",
            "Helper",
            "Helpee",
            "Helpers",
            "Helpees",
        }
        self.assertTrue(
            (set(ALL_INBOX_KEYS) - dynamic_canonical_sources) <= wrapped_sources
        )
        for file_name in files:
            tree = ast.parse(Path(file_name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for keyword in node.keywords:
                        if keyword.arg in {
                            "placeholder",
                            "title",
                            "alt",
                            "aria_label",
                        }:
                            self.assertFalse(
                                isinstance(keyword.value, ast.Constant)
                                and isinstance(keyword.value.value, str),
                                (
                                    file_name,
                                    keyword.arg,
                                    ast.dump(keyword.value),
                                ),
                            )
        self.assertIn("Write a message", wrapped_sources)
        self.assertIn("Close conversation", wrapped_sources)
        self.assertIn("No conversation selected", wrapped_sources)
        self.assertIn("Write your reply…", wrapped_sources)
        self.assertIn("Not a contact", wrapped_sources)
        required_module_sources = set(ALL_INBOX_KEYS) | {
            "Write a message",
            "Write your reply…",
            "Close conversation",
            "No conversation selected",
            "Not a contact",
            "Contact profile photo",
            "No messages yet",
            "Send",
            "Cancel",
            "Decline",
            "Requests",
            "Back",
            "New",
        }
        self.assertTrue(required_module_sources <= set(COMPLETE_KEYS))
        for locale in LOCALES:
            self.assertTrue(
                required_module_sources <= set(CATALOGS[locale]), locale
            )
        contacts_source = Path(files[0]).read_text()
        self.assertIn(
            "field_label(",
            Path("app/components/noncontact_panel.py").read_text(),
        )
        self.assertIn("inbox_subview_header(", Path(files[2]).read_text())
        self.assertIn(
            'ui(ContactsState.selected_contact["status_label"])',
            contacts_source,
        )
        self.assertIn('ui(item["type_label"])', Path(files[2]).read_text())
        self.assertIn('ui(option["label"])', Path(files[2]).read_text())
        self.assertIn(
            '"Member profile photo"',
            inspect.getsource(feedback._avatar_interface_label),
        )

    def test_ui_templates_keep_auth_dependency_and_member_values_are_not_reinterpreted(
        self,
    ):
        self.assertIn(
            "AuthState.interface_text.get(source, source)",
            inspect.getsource(ui),
        )
        expression = ui_template("Message {name}", "name", MEMBER_VALUE)
        dependencies = expression._get_all_var_data()
        self.assertIsNotNone(dependencies)
        self.assertTrue(rx.el.span(expression).render())
        self.assertIn('.split("{name}").join(', str(expression))
        self.assertNotIn(".replace(", str(expression))
        self.assertIsNotNone(ui("Find people")._get_all_var_data())
        self.assertIn(
            "ContactsState.contacts.length().to_string()",
            inspect.getsource(contacts_panel.contacts_header),
        )
        self.assertNotIn(
            "contact_count_heading",
            inspect.getsource(contacts_panel.contacts_header),
        )
        self.assertIn(
            'ui_template(\n                    "{count} Contacts"',
            inspect.getsource(contacts_panel.contacts_header),
        )
        self.assertIn(
            'item["preview"].startswith("Subject: ")',
            inspect.getsource(unified_inbox.conversation_card),
        )
        self.assertNotIn(
            'ui("Subject: ")',
            inspect.getsource(unified_inbox.conversation_card),
        )
        self.assertIn(
            'item["preview"]',
            inspect.getsource(unified_inbox.conversation_card),
        )
        self.assertIn(
            'contact["other_name"]',
            inspect.getsource(contacts_panel.contact_row),
        )
        self.assertIn(
            'contact["intro_note"]',
            inspect.getsource(contacts_panel.incoming_card),
        )
        bubble_source = inspect.getsource(chat_controls._correspondence_bubble)
        self.assertIn('msg["body"].to(str)', bubble_source)
        self.assertNotIn('ui(msg["body"]', bubble_source)
        self.assertIn(
            "_correspondence_bubble(_normalize_message(msg), target, delete_event)",
            inspect.getsource(chat_controls.correspondence_bubble),
        )

    def test_message_history_empty_state_uses_distinct_localized_heading_and_caption(
        self,
    ):
        source = inspect.getsource(contacts_panel.message_history)
        tree = ast.parse(source)
        localized_paragraphs = []
        raw_paragraph_text = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            if node.func.attr != "p" or not node.args:
                continue
            text = node.args[0]
            if isinstance(text, ast.Constant) and isinstance(text.value, str):
                raw_paragraph_text.append(text.value)
                continue
            if not isinstance(text, ast.Call) or not isinstance(
                text.func, ast.Name
            ):
                continue
            if text.func.id != "ui" or not text.args:
                continue
            value = text.args[0]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                class_name = next(
                    (
                        keyword.value.value
                        for keyword in node.keywords
                        if keyword.arg == "class_name"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ),
                    "",
                )
                localized_paragraphs.append((value.value, class_name))

        self.assertIn(
            ("No messages yet", "text-sm font-semibold text-[#111827]"),
            localized_paragraphs,
        )
        self.assertIn(
            (
                "Say hello, share where you're heading, and swap a little help.",
                "text-sm font-medium text-[#4b5563] mt-1",
            ),
            localized_paragraphs,
        )
        self.assertNotIn(
            "Say hello, share where you're heading, and swap a little help.",
            raw_paragraph_text,
        )
        rendered_component = contacts_panel.message_history()
        self.assertTrue(rendered_component.render())
        rendered = str(rendered_component)
        self.assertIn(str(ui("No messages yet")), rendered)
        self.assertIn(
            str(
                ui(
                    "Say hello, share where you're heading, and swap a little help."
                )
            ),
            rendered,
        )

    def test_node_substitution_preserves_special_member_text_and_role_templates(
        self,
    ):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is not installed")
        sources = (
            "Open {name}'s passport",
            "New message to {name}",
            "Message {name}",
            "Message {name} in the Inbox",
            "Open the Contact conversation with {name}",
            "Open the Helper conversation with {name}",
            "Open the Helpee conversation with {name}",
        )
        for locale in ("fr", "ar", "ja", "es"):
            for source in sources:
                expression = ui_template(source, "name", MEMBER_VALUE)
                localized = translate(locale, source)
                compiled = str(expression).replace(
                    str(ui(source)), json.dumps(localized)
                )
                script = f"process.stdout.write(JSON.stringify(eval({json.dumps(compiled)})))"
                result = subprocess.run(
                    [node, "-e", script],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(
                    json.loads(result.stdout),
                    localized.replace("{name}", MEMBER_VALUE),
                )
        for source in (
            "Open the Contact conversation with {name}",
            "Open the Helper conversation with {name}",
            "Open the Helpee conversation with {name}",
        ):
            self.assertEqual(translate("en", source), source)

    def test_inbox_components_construct_and_render_without_invoking_handlers(
        self,
    ):
        member_name = "$& {name} {type} Ålesund 日本"
        contact = {
            "link_id": 41,
            "other_id": 17,
            "other_name": member_name,
            "other_handle": "member_handle",
            "other_avatar": "",
            "other_avatar_seed": "member",
            "other_verified": False,
            "other_city": "Lausanne",
            "country_flag": "🇨🇭",
            "nationality": "Switzerland",
            "requested_at": "tomorrow",
            "intro_note": "Member-authored note 日本",
            "unread_count": 1,
        }
        item = {
            "key": "contact:41",
            "kind": "contact",
            "ref_id": 41,
            "conv_type": rx.Var.create("contact"),
            "type_label": rx.Var.create("Contact"),
            "unread_count": rx.Var.create(1),
            "other_avatar": rx.Var.create(""),
            "other_avatar_seed": rx.Var.create("member"),
            "other_verified": rx.Var.create(False),
            "other_name": rx.Var.create(member_name),
            "job_title": rx.Var.create(""),
            "preview": rx.Var.create(
                "Subject: Member subject 日本\\n\\nMember-authored preview"
            ),
            "last_photo": rx.Var.create(""),
        }
        option = {
            "value": rx.Var.create("helper"),
            "icon": "hand",
            "label": rx.Var.create("Helpers"),
        }
        person_id = rx.Var.create(17)
        person_name = rx.Var.create(member_name)
        components = (
            contacts_panel.contacts_header(),
            contacts_panel.incoming_card(contact),
            contacts_panel.contact_row(contact),
            contacts_panel.contacts_list(),
            contacts_panel.requests_section(),
            contacts_panel.conversation_header(),
            contacts_panel.message_history(),
            contacts_panel.composer(),
            contacts_panel.conversation_panel(embedded=True),
            contacts_panel.conversation_panel(dedicated=True),
            noncontact_panel.compose_form(person_id, person_name),
            noncontact_panel.message_control(person_id, person_name),
            noncontact_panel.thread_header(),
            noncontact_panel.thread_history(),
            noncontact_panel.reply_composer(),
            noncontact_panel.noncontact_conversation_view(embedded=True),
            noncontact_panel.noncontact_conversation_view(dedicated=True),
            unified_inbox.type_badge(item),
            unified_inbox.conversation_card(item),
            unified_inbox.filter_chip(option),
            unified_inbox.inbox_toolbar(),
            unified_inbox.inbox_contacts_view(),
            unified_inbox.empty_state(),
            unified_inbox.unified_conversation_list(),
            feedback.avatar_with_tick(
                "/placeholder.svg", False, "size-10", "Member profile photo"
            ),
        )
        for component in components:
            with self.subTest(component=component.tag):
                self.assertTrue(component.render())
                self.assertTrue(str(component))
        self.assertIn(
            "{count} Contacts",
            str(
                ui_template(
                    "{count} Contacts",
                    "count",
                    ContactsState.contacts.length().to_string(),
                )
            ),
        )
        self.assertIn("Member profile photo", INBOX_FEED_KEYS)
        self.assertIn("Latest message photo", INBOX_FEED_KEYS)
        self.assertIn("All conversations", INBOX_FEED_KEYS)
        self.assertIn(
            "No confirmed contacts yet. Connect with someone in Community to start writing.",
            INBOX_FEED_KEYS,
        )
        self.assertIn("Message {name} in the Inbox", INBOX_CONTACT_KEYS)
        self.assertIn(
            "Not a contact · Replies are welcome either way", INBOX_DIRECT_KEYS
        )
        self.assertIn(
            "type_filters", inspect.getsource(unified_inbox.inbox_toolbar)
        )
        contacts_header_source = inspect.getsource(
            contacts_panel.contacts_header
        )
        self.assertIn(
            "ContactsState.contacts.length().to_string()",
            contacts_header_source,
        )
        count_heading = ui_template(
            "{count} Contacts",
            "count",
            ContactsState.contacts.length().to_string(),
        )
        self.assertIsNotNone(count_heading._get_all_var_data())
        self.assertIn('.split("{count}").join(', str(count_heading))


if __name__ == "__main__":
    unittest.main()
