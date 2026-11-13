import reflex as rx

import ast
import asyncio
import copy
import string
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.components.report_dialog import (
    category_option,
    report_button,
    report_dialog,
    report_form,
)
from app.interface_catalog_report import (
    REPORT_CATALOGS,
    REPORT_KEYS,
    REPORT_ROWS,
)
from app.interface_catalog_block import BLOCK_CATALOGS
from app.interface_catalog_shared import SHARED_CATALOGS
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, translate, ui
from app.models import (
    LANGUAGE_OPTIONS,
    SAFETY_REPORT_CATEGORIES,
    SAFETY_REPORT_CATEGORY_LABELS,
)
from app.states import content_report_state as reports
from app.states.auth_state import AuthState

ROOT = Path(__file__).parent
EXPECTED_KEYS = (
    "Report",
    "Report unsafe content privately",
    "Report privately to the Go and Help safety team",
    "What kind of problem is this?",
    "required",
    "Choose a safety category",
    "What happened?",
    "20–2,000 characters",
    "Tell us what you saw, when it happened, and anything our team should know.",
    "Reports stay private. The person you report is never told who sent it.",
    "Cancel",
    "Sending…",
    "Send report",
    "Safety",
    "Close report form",
    "Report unsafe content",
    "Report this help request",
    "Report this profile",
    "Report this community topic",
    "Report this community comment",
    "Report this direct message",
    "Report this non-contact message",
    "Report this content",
    "Rude behaviour",
    "Abusive language",
    "Threats or violence",
    "Sexual harassment",
    "Discrimination",
    "Unsafe conduct",
    "Fraud or theft",
    "Privacy violation",
    "Other",
    "Please sign in to report content.",
    "We couldn't tell what you're reporting.",
    "Choose what kind of problem this is.",
    "Please describe what happened in at least 20 characters.",
    "Please keep it under 2000 characters.",
    "That content is no longer available to report.",
    "You can't report your own content.",
    "You've already reported this — our team can see it.",
    "Thank you — your report is private and with our safety team.",
    "Report sent privately to the Go and Help safety team.",
)


def tree_for(relative: str) -> ast.Module:
    return ast.parse((ROOT / relative).read_text())


def method(name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(tree_for("states/content_report_state.py"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def plain_method(name: str):
    node = copy.deepcopy(method(name))
    node.decorator_list = []
    namespace = dict(vars(reports))
    exec(
        compile(
            ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
            "report-test-method",
            "exec",
        ),
        namespace,
    )
    return namespace[name]


def lookup_args(tree: ast.AST) -> list[ast.expr]:
    return [
        node.args[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "ui"
        and node.args
    ]


class ReportHarness(SimpleNamespace):
    async def __aenter__(self):
        self.locked = True
        return self

    async def __aexit__(self, *args):
        self.locked = False

    async def get_state(self, state):
        if state is not AuthState:
            raise AssertionError("Unexpected cross-state access")
        return self.auth


class SharedReportTranslationTests(unittest.TestCase):
    def test_exact_keys_locales_presence_and_shared_preservation(self):
        offered = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(len(offered), 36)
        self.assertEqual(REPORT_KEYS, EXPECTED_KEYS)
        self.assertEqual(len(REPORT_KEYS), 42)
        self.assertEqual(set(REPORT_ROWS), offered | {"ha"})
        self.assertEqual(set(REPORT_CATALOGS), offered | {"ha"})
        self.assertTrue(set(REPORT_KEYS) <= set(COMPLETE_KEYS))
        for locale, entries in REPORT_CATALOGS.items():
            self.assertEqual(set(entries), set(EXPECTED_KEYS))
            for key, value in entries.items():
                with self.subTest(locale=locale, key=key):
                    self.assertTrue(value.strip())
                    self.assertIn(key, CATALOGS[locale])
                    self.assertTrue(CATALOGS[locale][key].strip())
                    self.assertEqual(
                        translate(locale, key), CATALOGS[locale][key]
                    )
                    self.assertEqual(translate("en", key), key)
                    for marker in ("TODO", "TRANSLATE_ME", "\ufffd"):
                        self.assertNotIn(marker, value)
            self.assertEqual(
                translate(locale, "Cancel"), CATALOGS[locale]["Cancel"]
            )
            self.assertEqual(
                translate(locale, "Sending…"),
                SHARED_CATALOGS[locale]["Sending…"],
            )
            self.assertEqual(
                translate(locale, "Safety"), BLOCK_CATALOGS[locale]["Safety"]
            )
        self.assertEqual(
            REPORT_CATALOGS["fr"]["Discrimination"], "Discrimination"
        )
        merge = next(
            node
            for node in tree_for("interface_i18n.py").body
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Attribute)
            and isinstance(node.iter.func.value, ast.Name)
            and node.iter.func.value.id == "REPORT_CATALOGS"
        )
        self.assertTrue(
            any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "setdefault"
                for n in ast.walk(merge)
            )
        )

    def test_static_authored_rows_and_exact_named_slots(self):
        rows = next(
            node.value
            for node in tree_for("interface_catalog_report.py").body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "REPORT_ROWS"
        )
        self.assertEqual(ast.literal_eval(rows), REPORT_ROWS)
        self.assertTrue(
            all(isinstance(node, ast.Constant) for node in rows.values)
        )
        formatter = string.Formatter()
        for entries in REPORT_CATALOGS.values():
            for source, value in entries.items():
                self.assertEqual(
                    Counter(
                        name
                        for _, name, _, _ in formatter.parse(source)
                        if name is not None
                    ),
                    Counter(
                        name
                        for _, name, _, _ in formatter.parse(value)
                        if name is not None
                    ),
                )

    def test_canonical_categories_and_whole_title_mapping(self):
        expected_categories = {
            "rude_behaviour": "Rude behaviour",
            "abusive_language": "Abusive language",
            "threats_or_violence": "Threats or violence",
            "sexual_harassment": "Sexual harassment",
            "discrimination": "Discrimination",
            "unsafe_conduct": "Unsafe conduct",
            "fraud_or_theft": "Fraud or theft",
            "privacy_violation": "Privacy violation",
            "other": "Other",
        }
        self.assertEqual(SAFETY_REPORT_CATEGORY_LABELS, expected_categories)
        self.assertEqual(
            set(SAFETY_REPORT_CATEGORIES), set(expected_categories)
        )
        self.assertEqual(
            {item["value"]: item["label"] for item in reports.CATEGORY_OPTIONS},
            expected_categories,
        )
        self.assertEqual(
            reports.REPORT_TITLE_SOURCES,
            {
                "job_message": "Report this help request",
                "profile": "Report this profile",
                "community_topic": "Report this community topic",
                "community_comment": "Report this community comment",
                "contact_message": "Report this direct message",
                "noncontact_message": "Report this non-contact message",
                "": "Report this content",
            },
        )
        self.assertTrue(
            set(reports.REPORT_TITLE_SOURCES.values()) <= set(REPORT_KEYS)
        )

    def test_reactive_title_preserves_member_and_source_state(self):
        state = ReportHarness(
            auth=SimpleNamespace(preferred_language="fr"),
            target_type="profile",
            target_id=77,
            target_hint="ليلى {member} 原文",
            target_label="Profile",
            error="You can't report your own content.",
            success="",
            category="other",
        )
        fn = plain_method("localized_dialog_title")
        snapshot = {
            key: value for key, value in vars(state).items() if key != "auth"
        }
        for locale in REPORT_CATALOGS:
            state.auth.preferred_language = locale
            for target, source in reports.REPORT_TITLE_SOURCES.items():
                state.target_type = target
                self.assertEqual(
                    asyncio.run(fn(state)), translate(locale, source)
                )
            state.target_type = "unknown"
            self.assertEqual(
                asyncio.run(fn(state)), translate(locale, "Report this content")
            )
        state.target_type = snapshot["target_type"]
        self.assertEqual(
            {key: value for key, value in vars(state).items() if key != "auth"},
            snapshot,
        )
        self.assertFalse(
            any(
                isinstance(n, ast.Attribute) and n.attr == "lower"
                for n in ast.walk(method("localized_dialog_title"))
            )
        )

    def test_privacy_and_numeric_meaning_fixtures(self):
        source = "Reports stay private. The person you report is never told who sent it."
        fixtures = {
            "fr": "ne saura jamais qui",
            "es": "Nunca se comunica",
            "de": "nie mitgeteilt",
            "ar": "لا يُخبَر",
            "zh": "永远不会获知",
        }
        for locale, phrase in fixtures.items():
            self.assertIn(phrase, REPORT_CATALOGS[locale][source])
        for locale, entries in REPORT_CATALOGS.items():
            with self.subTest(locale=locale):
                self.assertIn(
                    "20",
                    entries[
                        "Please describe what happened in at least 20 characters."
                    ],
                )
                self.assertIn(
                    "2000", entries["Please keep it under 2000 characters."]
                )
                self.assertIn("20", entries["20–2,000 characters"])
                self.assertIn("Go and Help", entries[EXPECTED_KEYS[-1]])
        self.assertEqual(
            (reports.DETAILS_MIN_LENGTH, reports.DETAILS_MAX_LENGTH), (20, 2000)
        )

    def test_ui_literals_dynamic_lookups_and_member_hint(self):
        tree = tree_for("components/report_dialog.py")
        args = lookup_args(tree)
        literals = {arg.value for arg in args if isinstance(arg, ast.Constant)}
        expected_ui = set(EXPECTED_KEYS[:16]) - {
            "Report",
            "Report unsafe content privately",
            "Report privately to the Go and Help safety team",
            "What kind of problem is this?",
            "required",
            "What happened?",
            "20–2,000 characters",
        }
        self.assertTrue(expected_ui <= literals)
        argument_trees = {
            ast.dump(arg, include_attributes=False) for arg in args
        }
        for expression in (
            "label",
            "accessible_label",
            "accessible_title",
            "item['label']",
            "ContentReportState.error",
        ):
            self.assertIn(
                ast.dump(
                    ast.parse(expression, mode="eval").body,
                    include_attributes=False,
                ),
                argument_trees,
            )
        self.assertFalse(any("target_hint" in ast.unparse(arg) for arg in args))
        self.assertTrue(
            any(
                isinstance(n, ast.JoinedStr) and "target_hint" in ast.unparse(n)
                for n in ast.walk(tree)
            )
        )
        attrs = {
            ast.unparse(n)
            for n in ast.walk(tree)
            if isinstance(n, ast.Attribute)
        }
        self.assertTrue(
            {
                "AuthState.preferred_language",
                "AuthState.interface_direction",
                "ContentReportState.localized_dialog_title",
            }
            <= attrs
        )
        self.assertIsNotNone(report_form())
        self.assertIsNotNone(report_dialog())
        self.assertIsNotNone(
            category_option({"label": "Other", "value": "other"})
        )
        self.assertIsNotNone(
            report_button(
                "profile",
                77,
                "Original member",
                label=ui("Report"),
                accessible_label=ui("Report unsafe content privately"),
                accessible_title=ui(
                    "Report privately to the Go and Help safety team"
                ),
            )
        )

    def test_validation_only_never_touches_database(self):
        async def exercise():
            fn = plain_method("submit_report")
            cases = [
                ("", "profile", 77, "other", "x" * 20, EXPECTED_KEYS[32]),
                ("12", "unknown", 77, "other", "x" * 20, EXPECTED_KEYS[33]),
                ("12", "profile", 0, "other", "x" * 20, EXPECTED_KEYS[33]),
                (
                    "12",
                    "profile",
                    77,
                    "not-a-category",
                    "x" * 20,
                    EXPECTED_KEYS[34],
                ),
                (
                    "12",
                    "profile",
                    77,
                    "other",
                    "  " + "x" * 19 + "  ",
                    EXPECTED_KEYS[35],
                ),
                ("12", "profile", 77, "other", "原" * 2001, EXPECTED_KEYS[36]),
            ]
            with patch.object(
                rx,
                "asession",
                side_effect=AssertionError("No report writes in tests"),
            ) as database:
                for sid, target, tid, category, details, error in cases:
                    state = ReportHarness(
                        auth=SimpleNamespace(
                            subscriber_id=sid, preferred_language="fr"
                        ),
                        target_type=target,
                        target_id=tid,
                        category=category,
                        error="",
                        success="",
                        is_sending=False,
                    )
                    data = {"details": details}
                    async for _ in fn(state, data):
                        pass
                    self.assertEqual(state.error, error)
                    self.assertEqual(data["details"], details)
                    self.assertFalse(state.is_sending)
                database.assert_not_called()

        asyncio.run(exercise())

    def test_source_security_excerpt_and_success_toast_contract(self):
        node = method("submit_report")
        literals = {
            n.value
            for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        }
        self.assertTrue(set(EXPECTED_KEYS[37:]) <= literals)
        sql = " ".join(
            " ".join(value.split())
            for value in literals
            if "skillkind_content_report" in value
        )
        for fragment in (
            "WHERE reporter_id = :sid",
            "AND target_type = :ttype",
            "AND target_id = :tid",
            "target_excerpt, category, details, status",
            ":excerpt, :category, :details, :status",
        ):
            self.assertIn(fragment, sql)
        for target in ("contact_message", "noncontact_message"):
            self.assertIn(
                "recipient_id = :sid", reports._TARGET_QUERIES[target]
            )
        for expression in (
            "reported_id == int(sid)",
            "existing is not None",
            "message_preview(row[1])[:500]",
            "str(row[1] or '')[:500]",
            "len(details) < DETAILS_MIN_LENGTH",
            "len(details) > DETAILS_MAX_LENGTH",
        ):
            self.assertIn(expression, ast.unparse(node))
        self.assertEqual(
            sum(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "commit"
                for n in ast.walk(node)
            ),
            1,
        )
        translates = [
            n
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "translate"
        ]
        self.assertEqual(len(translates), 1)
        self.assertEqual(
            ast.literal_eval(translates[0].args[1]), EXPECTED_KEYS[-1]
        )
        contexts = [n for n in ast.walk(node) if isinstance(n, ast.AsyncWith)]
        self.assertTrue(
            any(
                any(
                    isinstance(n, ast.Assign)
                    and any(
                        isinstance(t, ast.Name) and t.id == "language"
                        for t in n.targets
                    )
                    for n in ast.walk(context)
                )
                for context in contexts
            )
        )
        lookup = next(
            n
            for n in ast.walk(node)
            if isinstance(n, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "language"
                for t in n.targets
            )
        )
        commit = next(
            n
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "commit"
        )
        self.assertGreater(lookup.lineno, commit.lineno)
        self.assertIn("await self.get_state(AuthState)", ast.unparse(lookup))
        for name in ("open_report", "close_report", "set_category"):
            fn = plain_method(name)
            self.assertFalse(
                any(
                    isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name)
                    and n.func.id in {"ui", "translate"}
                    for n in ast.walk(method(name))
                )
            )
            state = ReportHarness(
                is_open=False,
                target_type="",
                target_id=0,
                target_label="",
                target_hint="",
                category="",
                error="",
                success="",
            )
            if name == "open_report":
                original = "ليلى {member} 原文" * 30
                fn(state, "profile", 77, original)
                self.assertEqual(state.target_hint, original[:160])
                self.assertEqual(state.target_label, "Profile")
            elif name == "set_category":
                fn(state, "other")
                self.assertEqual(state.category, "other")
            else:
                fn(state)
                self.assertFalse(state.is_open)


if __name__ == "__main__":
    unittest.main()
