import reflex as rx
import unittest

from app.states.messaging_state import (
    REVIEW_CONTENT_PREFIX,
    REVIEW_WORD_LIMIT,
    decode_review_content,
    encode_review_content,
    review_released_sql,
)


class ReviewContentTests(unittest.TestCase):
    def test_legacy_text(self):
        for value in ("", "Thank you!", '{"text":"ordinary legacy JSON"}'):
            self.assertEqual(decode_review_content(value), (value, ""))

    def test_round_trip(self):
        original = "Great help!\nThank you, João 🟢"
        response = 'A pleasure — "anytime".'
        self.assertEqual(
            decode_review_content(encode_review_content(original)),
            (original, ""),
        )
        self.assertEqual(
            decode_review_content(encode_review_content(original, response)),
            (original, response),
        )

    def test_unknown_payload_is_not_exposed(self):
        payload = f'{REVIEW_CONTENT_PREFIX}{{"version":99,"text":"hidden"}}'
        self.assertEqual(
            decode_review_content(payload), ("Review text unavailable.", "")
        )

    def test_word_limit_not_character_limit(self):
        text = " ".join(["thoughtful"] * REVIEW_WORD_LIMIT)
        self.assertGreater(len(text), 1000)
        self.assertEqual(len(text.split()), 500)
        self.assertEqual(
            decode_review_content(encode_review_content(text))[0], text
        )

    def test_visibility_is_immediate_after_reviewers_confirmation(self):
        sql = review_released_sql()
        self.assertNotIn("30 days", sql)
        self.assertNotIn("peer", sql)
        self.assertNotIn(
            "release_task.poster_confirmed AND release_task.helper_confirmed",
            sql,
        )
        self.assertIn("r.reviewer_id = release_task.poster_id", sql)
        self.assertIn("r.reviewee_id = release_task.helper_id", sql)
        self.assertIn("AND release_task.poster_confirmed", sql)
        self.assertIn("r.reviewer_id = release_task.helper_id", sql)
        self.assertIn("r.reviewee_id = release_task.poster_id", sql)
        self.assertIn("AND release_task.helper_confirmed", sql)
        self.assertIn("release_task.id = r.completed_task_id", sql)
        with self.assertRaises(ValueError):
            review_released_sql("untrusted")


if __name__ == "__main__":
    unittest.main()
