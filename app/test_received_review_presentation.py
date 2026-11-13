import reflex as rx

import ast
import inspect
import unittest
from datetime import datetime

from app.components import reviews_section, unified_inbox
from app.models import (
    REVIEW_POSTER_CATEGORY_LABELS,
    REVIEW_HELPER_CATEGORY_LABELS,
)
from app.states.messaging_state import category_pairs, review_released_sql
from app.states.profile_state import (
    ProfileState,
    ReceivedReview,
    _review_categories,
)


class ReceivedReviewPresentationTests(unittest.TestCase):
    def test_helpee_chip(self):
        self.assertEqual(
            unified_inbox.HELPEE_BADGE,
            "w-fit shrink-0 flex items-center gap-1.5 rounded-full border "
            "px-2.5 py-0.5 text-[11px] font-bold border-[#e08b12] bg-white text-[#e08b12]",
        )
        self.assertIn(
            '("helpee", rx.icon("hand-helping"',
            inspect.getsource(unified_inbox.type_badge),
        )

    def test_category_order_matches_stored_form(self):
        labels = ["Timeliness", "Work ethic", "Skill", "Friendliness"]
        self.assertEqual(REVIEW_POSTER_CATEGORY_LABELS, labels)
        self.assertEqual(REVIEW_HELPER_CATEGORY_LABELS, labels)
        for direction in ("poster_to_helper", "helper_to_poster"):
            expected = [
                dict(label=label, score=str(score))
                for label, score in zip(labels, [1, 2, 3, 4])
            ]
            self.assertEqual(
                _review_categories(direction, [1, 2, 3, 4]), expected
            )
            self.assertEqual(category_pairs(direction, [1, 2, 3, 4]), expected)

    def test_query_and_actual_mapping(self):
        source = inspect.getsource(ProfileState)
        query = source.split("review_rows = (", 1)[1].split(").all()", 1)[0]
        for token in (
            "JOIN skillkind_completed_task ct",
            "ct.id = r.completed_task_id",
            "JOIN skillkind_help_post p ON p.id = ct.post_id",
            "LEFT JOIN skillkind_profile rp",
            "rp.subscriber_id = reviewer.id",
            "COALESCE(p.title, '')",
            "COALESCE(rp.avatar_path, '')",
            "WHERE r.reviewee_id = :sid AND {review_released_sql()}",
            "ORDER BY r.created_at DESC",
            "LIMIT 8",
        ):
            self.assertIn(token, query)
        self.assertNotIn("reviewer.email", query)
        tree = ast.parse(source)
        mapping = next(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                ast.unparse(target) == "self.received_reviews"
                for target in node.targets
            )
            and isinstance(node.value, ast.ListComp)
        )
        row = (
            1,
            "John Smith",
            27,
            "poster_to_helper",
            4,
            "",
            True,
            datetime(2026, 1, 2),
            1,
            2,
            3,
            4,
            True,
            "Carry boxes upstairs",
            "avatar_test.webp",
        )
        from app.states.messaging_state import decode_review_content

        result = eval(
            compile(ast.Expression(mapping), "<review mapping>", "eval"),
            {
                "review_rows": [row],
                "_review_categories": _review_categories,
                "decode_review_content": decode_review_content,
            },
        )[0]
        self.assertEqual(result["job_title"], row[13])
        self.assertEqual(result["reviewer_avatar"], row[14])
        self.assertEqual(result["reviewer_seed"], "27")
        self.assertEqual(set(result), set(ReceivedReview.__annotations__))
        self.assertNotIn("reviewer_email", result)
        self.assertEqual(result["comment"], "")
        self.assertEqual(
            result["categories"], _review_categories(row[3], [1, 2, 3, 4])
        )
        self.assertIn(
            "release_task.id = r.completed_task_id", review_released_sql()
        )
        self.assertIn(
            "AND release_task.poster_confirmed", review_released_sql()
        )
        self.assertIn(
            "AND release_task.helper_confirmed", review_released_sql()
        )

    def test_review_geometry_privacy_and_retained_content(self):
        source = inspect.getsource(reviews_section)
        for removed in (
            "Organisation",
            "Give Help score",
            "From someone you helped",
            "A quiet thank-you from a Go and Help neighbour.",
            "reviewer_email",
            "direction_label",
            "direction_hint",
            "#2362ef",
            "#e0ebff",
            "#eef3ff",
        ):
            self.assertNotIn(removed, source)
        header = inspect.getsource(reviews_section.your_reviews_header)
        self.assertIn("combined_star_states", header)
        self.assertIn("received_reviews.length()", header)
        section = inspect.getsource(reviews_section.received_reviews_section)
        self.assertIn('"My reviews"', section)
        self.assertNotIn('"Reviews about my work"', section)
        self.assertIn(
            "justify-center",
            inspect.getsource(reviews_section.your_reviews_header),
        )
        card = inspect.getsource(reviews_section.received_review_card)
        self.assertLess(
            card.index('review["job_title"]'),
            card.index('received_rating_stars(review["rating"], True)'),
        )
        self.assertIn('rx.get_upload_url(review["reviewer_avatar"])', card)
        for token in (
            'review["comment"]',
            'review["response"]',
            'review["created"]',
            'review["kindness_flag"]',
        ):
            self.assertIn(token, card)
        stars = inspect.getsource(reviews_section.received_rating_stars)
        for token in (
            "size-6",
            "size-4",
            "out of 5 stars",
            "rx.Var.range(1, 6)",
        ):
            self.assertIn(token, stars)
        row = inspect.getsource(reviews_section.review_category_row)
        self.assertIn("w-full items-center justify-between", row)
        for token in ("rounded", "uppercase", "bg-"):
            self.assertNotIn(token, row)

    def test_render_inbox_and_reviews(self):
        for component in (
            unified_inbox.inbox_toolbar(),
            unified_inbox.unified_conversation_list(rx.el.div()),
            reviews_section.community_reviews_section(),
            reviews_section.received_rating_stars(rx.Var.create(4), True),
            reviews_section.review_category_row(
                rx.Var.create({"label": "Skill", "score": "3"})
            ),
        ):
            self.assertTrue(component.render())


if __name__ == "__main__":
    unittest.main()
