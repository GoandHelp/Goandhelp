import reflex as rx

import ast
import inspect
from pathlib import Path
from string import Formatter
import unittest
from unittest.mock import AsyncMock, patch

from app.interface_catalog_forum import FORUM_LABEL_KEYS, FORUM_LABEL_CATALOGS
from app.interface_catalog_forum_text import (
    FORUM_TEXT_KEYS,
    FORUM_TEXT_CATALOGS,
)
from app.interface_catalog_forum_feedback import (
    FORUM_FEEDBACK_KEYS,
    FORUM_FEEDBACK_CATALOGS,
)
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    FORUM_KEYS,
    translate,
    ui_template,
)
from app.models import COMMUNITY_SUBJECTS, LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.community_state import (
    CommunityState,
    EMPTY_TOPIC,
    TopicItem,
    CommentItem,
)

GROUPS = (
    (FORUM_LABEL_KEYS, FORUM_LABEL_CATALOGS),
    (FORUM_TEXT_KEYS, FORUM_TEXT_CATALOGS),
    (FORUM_FEEDBACK_KEYS, FORUM_FEEDBACK_CATALOGS),
)
ALL_TOPICS = {
    "am": "ሁሉም ርዕሶች",
    "ar": "كل المواضيع",
    "bn": "সব বিষয়",
    "my": "ခေါင်းစဉ်အားလုံး",
    "zh": "所有话题",
    "cs": "Všechna témata",
    "da": "Alle emner",
    "nl": "Alle onderwerpen",
    "fi": "Kaikki aiheet",
    "fr": "Tous les sujets",
    "de": "Alle Themen",
    "el": "Όλα τα θέματα",
    "gu": "બધા વિષયો",
    "he": "כל הנושאים",
    "hi": "सभी विषय",
    "hu": "Minden téma",
    "id": "Semua topik",
    "it": "Tutti gli argomenti",
    "ja": "すべての話題",
    "kn": "ಎಲ್ಲ ವಿಷಯಗಳು",
    "ko": "모든 주제",
    "ml": "എല്ലാ വിഷയങ്ങളും",
    "mr": "सर्व विषय",
    "ne": "सबै विषयहरू",
    "fa": "همه موضوع‌ها",
    "pl": "Wszystkie tematy",
    "pt": "Todos os tópicos",
    "ro": "Toate subiectele",
    "es": "Todos los temas",
    "sw": "Mada zote",
    "sv": "Alla ämnen",
    "ta": "அனைத்து தலைப்புகள்",
    "te": "అన్ని విషయాలు",
    "th": "ทุกหัวข้อ",
    "tr": "Tüm konular",
    "vi": "Tất cả chủ đề",
}


class ForumCatalogTests(unittest.TestCase):
    def test_exact_catalog_phrase_sets_for_all_36_locales(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(set(ALL_TOPICS), offered)
        self.assertEqual(len(offered), 36)
        self.assertTrue(set(FORUM_KEYS) <= set(COMPLETE_KEYS))
        for keys, catalogs in GROUPS:
            self.assertEqual(len(keys), len(set(keys)))
            self.assertEqual(set(catalogs), offered)
            for code in offered:
                self.assertEqual(set(catalogs[code]), set(keys), code)
                for key in keys:
                    with self.subTest(locale=code, phrase=key):
                        value = catalogs[code][key]
                        self.assertEqual(CATALOGS[code][key], value)
                        self.assertTrue(value.strip())
                        self.assertNotIn("\ufffd", value)
                        self.assertNotIn("TODO", value)
                        self.assertNotIn("TRANSLATE_ME", value)
                        self.assertFalse(
                            value.startswith((f"[{code}]", f"{code}:"))
                        )
                        if len(key) > 30:
                            self.assertNotEqual(value, key)
                        self.assertEqual(translate("en", key), key)
        for code, expected in ALL_TOPICS.items():
            self.assertEqual(translate(code, "All topics"), expected)
        for code in offered:
            self.assertTrue(set(COMMUNITY_SUBJECTS) <= set(CATALOGS[code]))

    def test_all_template_fields_and_original_substitutions(self):
        formatter = Formatter()
        values = {
            "count": 17,
            "limit": "5,000",
            "topics": 1,
            "comments": 9,
            "subject": "原文 {count} ليلى",
            "subjects": "أخرى, Original {subject}",
            "section": "منتدى {original}",
        }
        for code, _ in LANGUAGE_OPTIONS:
            for source in (*FORUM_TEXT_KEYS, *FORUM_FEEDBACK_KEYS):
                expected = [
                    field for _, field, _, _ in formatter.parse(source) if field
                ]
                translated = translate(code, source)
                fields = [
                    field
                    for _, field, _, _ in formatter.parse(translated)
                    if field
                ]
                self.assertCountEqual(fields, expected, (code, source))
                formatted = translated.format(**values)
                for name in fields:
                    self.assertIn(str(values[name]), formatted)
        expression = ui_template(
            "New activity in {section}", "section", "ليلى {count}"
        )
        self.assertIsInstance(expression, rx.Var)
        self.assertIn("split", str(expression))
        self.assertIn("join", str(expression))

    def test_forum_accessibility_placeholders_and_fixed_copy_inventory(self):
        tree = ast.parse(Path("app/components/community_panel.py").read_text())
        forum_nodes = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.lineno
            >= next(
                n.lineno
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "subject_option"
            )
        ]
        for function in forum_nodes:
            for node in ast.walk(function):
                if isinstance(node, ast.keyword) and node.arg in {
                    "title",
                    "aria_label",
                    "placeholder",
                }:
                    self.assertFalse(
                        isinstance(node.value, ast.Constant),
                        (function.name, node.arg),
                    )
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id in {
                    "ui",
                    "ui_template",
                    "field_label",
                }:
                    if node.args and isinstance(node.args[0], ast.Constant):
                        self.assertIn(
                            node.args[0].value, COMPLETE_KEYS, function.name
                        )
                if isinstance(node.func, ast.Name) and node.func.id == "ui":
                    for item in ast.walk(node.args[0]):
                        if isinstance(item, ast.Subscript) and isinstance(
                            item.slice, ast.Constant
                        ):
                            self.assertNotIn(
                                item.slice.value,
                                {
                                    "title",
                                    "body",
                                    "preview",
                                    "author_name",
                                    "author_handle",
                                    "handle",
                                },
                            )
        source = Path("app/components/community_panel.py").read_text()
        self.assertIn('ui(topic["subject"])', source)
        self.assertIn('ui(CommunityState.selected_topic["subject"])', source)
        self.assertIn('value=item["value"]', source)
        self.assertIn('ui("Read more")', source)
        self.assertIn("ui(CommunityState.error)", source)
        self.assertIn("success_banner(ui(CommunityState.success))", source)
        self.assertIn("before:bg-inherit", source)
        self.assertIn("dir=AuthState.interface_direction", source)
        self.assertNotIn(
            "shadow",
            source.split("FOLDER_TAB_ACTIVE =", 1)[1].split(
                "FOLDER_TAB_INACTIVE", 1
            )[0],
        )

    def test_every_forum_constructor_renders(self):
        from app.components import community_panel as panel

        topic = rx.Var.create(
            {
                **EMPTY_TOPIC,
                "id": 7,
                "subject": "Other",
                "title": "Member title",
                "body": "Original body",
                "preview": "Original preview",
                "author_name": "ليلى",
                "author_handle": "@original",
            }
        ).to(TopicItem)
        comment = rx.Var.create(
            {
                "id": 9,
                "author_id": 4,
                "author_name": "Member name",
                "author_avatar_seed": "member-4",
                "author_handle": "@member",
                "author_avatar": "",
                "author_verified": True,
                "body": "Original comment {count}",
                "created": "2026-01-01",
                "mine": False,
            }
        ).to(CommentItem)
        option = rx.Var.create(
            {"label": "Other", "value": "Other", "icon": "circle-ellipsis"}
        ).to(dict[str, str])
        components = (
            panel.subject_option(option),
            panel.subject_filter_button(option),
            panel.subject_icon_button(option),
            panel.subject_checklist_row(option),
            panel.subject_dropdown(),
            panel.subject_icon_row(),
            panel.subject_mobile_controls(),
            panel.subject_folder_grid(),
            panel.topic_composer(),
            panel.comment_composer(),
            panel.locked_comment_prompt(),
            panel.topic_card(topic),
            panel.comment_card(comment),
            panel.topic_detail(),
            panel.topic_feed(),
            panel.community_section(),
            panel.community_header(),
        )
        for component in components:
            self.assertIsInstance(component, rx.Component)
            self.assertIsInstance(component.render(), dict)

    def test_draft_subject_and_feedback_sources_are_preserved(self):
        state = CommunityState(_reflex_internal_init=True)
        state.title_draft = "ليلى {count} Title"
        state.body_draft = "Original member body"
        state.subject_filter_store = "Privacy|Other"
        CommunityState.set_subject_draft.fn(state, "Other")
        self.assertEqual(state.subject_draft, "Other")
        self.assertEqual(state.selected_subject_filters, ["Privacy", "Other"])
        CommunityState.set_subject_draft.fn(state, "Otros")
        self.assertEqual(state.subject_draft, "")
        self.assertEqual(state.title_draft, "ليلى {count} Title")
        self.assertEqual(state.body_draft, "Original member body")
        state.error = "Give your discussion a title."
        state.success = "Your reply is on the board."
        for code, _ in LANGUAGE_OPTIONS:
            translate(code, state.error)
            translate(code, state.success)
            self.assertEqual(state.error, "Give your discussion a title.")
            self.assertEqual(state.success, "Your reply is on the board.")
        self.assertIn("characters", state.title_limit_label)
        self.assertIn("words", state.body_limit_label)


class ForumReactiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_hydrated_language_display_changes_without_draft_mutation(
        self,
    ):
        state = CommunityState(_reflex_internal_init=True)
        auth = AuthState(_reflex_internal_init=True)
        state.subject_filter_store = "Privacy|Other"
        state.subject_draft = "Other"
        state.title_draft = "Member title {count}"
        state.body_draft = "Member body remains original"
        state.comment_draft = "Original comment"
        state.error = "Give your discussion a title."
        state.success = "Your reply is on the board."
        state.monthly_comments_used = 3
        before = (
            state.subject_filter_store,
            state.subject_draft,
            state.title_draft,
            state.body_draft,
            state.comment_draft,
            state.draft_version,
            state.comment_version,
            state.error,
            state.success,
        )
        with patch.object(
            CommunityState, "get_state", new=AsyncMock(return_value=auth)
        ) as get_state:
            for code, _ in LANGUAGE_OPTIONS:
                auth.preferred_language = code
                display = await inspect.getattr_static(
                    CommunityState, "forum_display"
                ).fget(state)
                labels = [
                    translate(code, subject) for subject in ["Privacy", "Other"]
                ]
                self.assertEqual(display["filter_label"], ", ".join(labels))
                self.assertEqual(
                    display["filter_summary"],
                    translate(
                        code, "Filtered to {count} subjects: {subjects}."
                    ).format(count=2, subjects=", ".join(labels)),
                )
                self.assertEqual(
                    display["replies"],
                    translate(code, "{count} replies").format(count=0),
                )
                self.assertEqual(
                    display["comment_allowance"],
                    translate(
                        code,
                        "10 comments per month · {count} remaining this UTC month",
                    ).format(count=7),
                )
                self.assertEqual(
                    display["title_error"],
                    translate(
                        code, "Titles can be at most {limit} characters."
                    ).format(limit=200),
                )
                self.assertEqual(
                    display["body_error"],
                    translate(
                        code,
                        "That post is longer than {limit} words — please shorten it.",
                    ).format(limit=5000),
                )
                self.assertEqual(
                    display["comment_error"],
                    translate(
                        code, "Comments are limited to {limit} words."
                    ).format(limit=1000),
                )
                self.assertEqual(
                    before,
                    (
                        state.subject_filter_store,
                        state.subject_draft,
                        state.title_draft,
                        state.body_draft,
                        state.comment_draft,
                        state.draft_version,
                        state.comment_version,
                        state.error,
                        state.success,
                    ),
                )
            get_state.assert_called_with(AuthState)
            state.subject_filter_store = ""
            auth.preferred_language = "ar"
            display = await inspect.getattr_static(
                CommunityState, "forum_display"
            ).fget(state)
            self.assertEqual(display["filter_label"], ALL_TOPICS["ar"])
            state.subject_filter_store = "Other"
            display = await inspect.getattr_static(
                CommunityState, "forum_display"
            ).fget(state)
            self.assertEqual(
                display["filter_summary"],
                translate("ar", "Filtered to {subject}.").format(
                    subject=translate("ar", "Other")
                ),
            )

    async def test_toasts_use_current_hydrated_language_and_keep_source(self):
        state = CommunityState(_reflex_internal_init=True)
        auth = AuthState(_reflex_internal_init=True)
        with patch.object(
            CommunityState, "get_state", new=AsyncMock(return_value=auth)
        ) as get_state:
            for code, _ in LANGUAGE_OPTIONS:
                auth.preferred_language = code
                for source in (
                    "Discussion posted.",
                    "That discussion is no longer available.",
                ):
                    with patch("app.states.community_state.rx.toast") as toast:
                        await CommunityState.show_forum_toast.fn(state, source)
                        toast.assert_called_once_with(
                            translate(code, source), duration=3000
                        )
            get_state.assert_called_with(AuthState)
        text = Path("app/states/community_state.py").read_text()
        self.assertIn(
            'yield CommunityState.show_forum_toast("Discussion posted.")', text
        )
        tree = ast.parse(text)
        semantic_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Yield)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "CommunityState"
            and node.value.func.attr == "show_forum_toast"
            and len(node.value.args) == 1
            and isinstance(node.value.args[0], ast.Constant)
        ]
        self.assertTrue(
            any(
                call.value.args[0].value
                == "That discussion is no longer available."
                for call in semantic_calls
            )
        )


if __name__ == "__main__":
    unittest.main()
