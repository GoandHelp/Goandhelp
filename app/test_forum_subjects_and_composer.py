import reflex as rx

import ast
import inspect
import itertools
import unittest
from types import SimpleNamespace

from app.components import community_panel
from app.models import (
    COMMUNITY_SUBJECTS,
    COMMUNITY_SUBJECT_ICONS,
    CommunityTopic,
)
from app.states.community_state import CommunityState


class ForumSubjectsTests(unittest.TestCase):
    def test_canonical_order_icons_and_constraint(self):
        previous = [
            "First time Helper",
            "First time Helpee",
            "Communication",
            "Privacy",
            "Emergencies",
            "Events",
            "Job management",
            "Health and Safety",
            "Regulations",
            "Work visas",
            "Meeting people",
            "Businesses",
            "Workshops",
            "Tours",
            "Dinner",
            "Other",
        ]
        self.assertEqual(
            [
                subject
                for subject in COMMUNITY_SUBJECTS
                if subject not in ("Activities", "Money")
            ],
            previous,
        )
        self.assertEqual(len(COMMUNITY_SUBJECTS), len(set(COMMUNITY_SUBJECTS)))
        self.assertEqual(COMMUNITY_SUBJECTS[-1], "Other")
        self.assertEqual(
            COMMUNITY_SUBJECTS[COMMUNITY_SUBJECTS.index("Events") + 1],
            "Activities",
        )
        self.assertEqual(
            COMMUNITY_SUBJECTS[COMMUNITY_SUBJECTS.index("Businesses") + 1],
            "Money",
        )
        constraint = next(
            constraint
            for constraint in CommunityTopic.__table__.constraints
            if constraint.name == "ck_community_topic_subject_category"
        )
        state = CommunityState()
        self.assertEqual(
            [item["value"] for item in state.subject_options],
            COMMUNITY_SUBJECTS,
        )
        for subject, icon in (("Activities", "activity"), ("Money", "coins")):
            self.assertEqual(COMMUNITY_SUBJECT_ICONS[subject], icon)
            self.assertTrue(rx.icon(icon).render())
            self.assertIn(f"'{subject}'", str(constraint.sqltext))
            item = next(
                item
                for item in state.subject_options
                if item["value"] == subject
            )
            self.assertEqual(
                item, {"value": subject, "label": subject, "icon": icon}
            )
            for factory in (
                community_panel.subject_filter_button,
                community_panel.subject_icon_button,
                community_panel.subject_checklist_row,
                community_panel.subject_option,
            ):
                component = factory(item)
                self.assertTrue(component.render())
                self.assertIn(subject, str(component))
            mobile = str(community_panel.subject_icon_button(item))
            self.assertIn("aria-label", mobile)
            self.assertIn("aria-pressed", mobile)

    def test_drafts_and_persisted_multifilters(self):
        state = CommunityState()
        state.title_draft = "Community ideas"
        state.body_draft = "Share your experiences here."
        for subject in ("Activities", "Money"):
            CommunityState.set_subject_draft.fn(state, subject)
            self.assertEqual(state.subject_draft, subject)
            self.assertTrue(state.subject_chosen)
            self.assertTrue(state.can_post_topic)
            self.assertIn(subject, state.subject_hint)
            CommunityState.toggle_subject_filter.fn(state, subject)
            self.assertIn(subject, state.selected_subject_filters)
        self.assertEqual(
            state.selected_subject_filters, ["Activities", "Money"]
        )
        state.subject_filter_store = "Money|Unknown|Activities|Money"
        self.assertEqual(
            state.selected_subject_filters, ["Activities", "Money"]
        )
        CommunityState.toggle_subject_filter.fn(state, "Activities")
        self.assertEqual(state.selected_subject_filters, ["Money"])
        CommunityState.toggle_subject_filter.fn(state, "Unknown")
        self.assertEqual(state.selected_subject_filters, ["Money"])
        CommunityState.set_subject_draft.fn(state, "Unknown")
        self.assertEqual(state.subject_draft, "")
        self.assertFalse(state.can_post_topic)
        for factory in (
            community_panel.subject_folder_grid,
            community_panel.subject_dropdown,
            community_panel.topic_composer,
        ):
            self.assertIn("subject_options", inspect.getsource(factory))
            self.assertTrue(factory().render())


class ForumComposerNoticeTests(unittest.TestCase):
    def test_notice_is_immediate_single_sibling_and_gated(self):
        source = inspect.getsource(community_panel.community_section)
        tree = ast.parse(source)
        root = tree.body[0].body[0].value
        control_block = root.args[2]
        control_row = control_block.args[0]
        button_condition, notice_condition = control_row.args
        self.assertEqual(ast.unparse(button_condition.func), "rx.cond")
        self.assertEqual(ast.unparse(notice_condition.func), "rx.cond")
        self.assertEqual(ast.unparse(notice_condition.args[1].func), "rx.el.p")
        self.assertEqual(
            ast.unparse(notice_condition.args[2].func), "rx.fragment"
        )
        self.assertIn("topic_composer", ast.unparse(control_block.args[1]))
        self.assertEqual(source.count("Free: 1 topic per month"), 1)
        self.assertEqual(source.count("Text only, kept forever"), 1)
        classes = next(
            keyword.value.value
            for keyword in control_row.keywords
            if keyword.arg == "class_name"
        )
        self.assertIn("flex-col items-center justify-center", classes)
        notice = notice_condition.args[1]
        wording = compile(ast.Expression(notice.args[0]), "<notice>", "eval")
        condition = compile(
            ast.Expression(notice_condition.args[0]), "<visibility>", "eval"
        )
        for signed_in, opened, premium, available in itertools.product(
            (0, 1), repeat=4
        ):
            context = {
                "AuthState": SimpleNamespace(is_signed_in=signed_in),
                "CommunityState": SimpleNamespace(
                    composer_open=opened,
                    forum_premium=premium,
                    topic_allowance_available=available,
                    topics_remaining=0,
                    comments_remaining=7,
                ),
            }
            self.assertEqual(
                bool(eval(condition, {}, context)),
                bool(signed_in and opened and not premium and available),
            )
            self.assertEqual(
                eval(wording, {}, context),
                "Free: 1 topic per month · 10 comments per month. Remaining this UTC month: "
                "0 topic · 7 comments. Text only, kept forever on the board — titles up to "
                "200 characters and posts up to 5,000 words.",
            )
        self.assertTrue(community_panel.community_section().render())

    def test_remaining_counters_are_live_and_clamped(self):
        state = CommunityState()
        self.assertEqual(
            (state.topics_remaining, state.comments_remaining), (1, 10)
        )
        state.monthly_topics_used = 1
        state.monthly_comments_used = 3
        self.assertEqual(
            (state.topics_remaining, state.comments_remaining), (0, 7)
        )
        state.monthly_topics_used = 4
        state.monthly_comments_used = 12
        self.assertEqual(
            (state.topics_remaining, state.comments_remaining), (0, 0)
        )
        self.assertFalse(state.topic_allowance_available)
        state.forum_premium = True
        self.assertTrue(state.topic_allowance_available)


if __name__ == "__main__":
    unittest.main()
