import reflex as rx

import unittest
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from test_utils import run_event
from app.states.messaging_state import (
    EMPTY_THREAD,
    MessagingState,
    review_released_sql,
)
from app.states.unified_inbox_state import UnifiedInboxState, job_summary_copy
from app.states.community_state import CommunityState
from app.states.profile_state import ProfileState


class InboxReviewTests(unittest.IsolatedAsyncioTestCase):
    def test_role_copy(self):
        self.assertEqual(
            job_summary_copy("helper", "Move boxes"),
            "Offering you help for: “Move boxes”",
        )
        self.assertEqual(
            job_summary_copy("helpee", "Move boxes"),
            "Asking you for help with: “Move boxes”",
        )

    async def test_filters(self):
        state = UnifiedInboxState()
        for value in ("all", "contact", "helper", "helpee"):
            await run_event(state.set_type_filter, value)
            self.assertEqual(state.type_filter, value)
        await run_event(state.set_type_filter, "invalid")
        self.assertEqual(state.type_filter, "all")

    async def test_own_confirmation_and_navigation(self):
        state = MessagingState()
        state.selected_thread = {
            **EMPTY_THREAD,
            "id": 7,
            "task_id": 9,
            "i_confirmed": True,
        }
        self.assertTrue(state.can_review)
        self.assertFalse(state.selected_thread["is_completed"])
        self.assertEqual(
            [field["label"] for field in state.review_fields],
            ["Timeliness", "Work ethic", "Skill", "Friendliness"],
        )
        await run_event(state.open_review_target)
        self.assertTrue(state.review_target_open)
        self.assertEqual(
            (await state.get_state(ProfileState)).active_tab, "community"
        )
        self.assertEqual(
            (await state.get_state(CommunityState)).section, "reviews"
        )
        await run_event(state.close_review_target)
        self.assertFalse(state.review_target_open)
        self.assertEqual(state.selected_thread["task_id"], 9)
        state.selected_thread = {
            **state.selected_thread,
            "my_review_done": True,
        }
        self.assertFalse(state.can_review)
        state.selected_thread = {
            **state.selected_thread,
            "my_review_done": False,
            "i_confirmed": False,
        }
        self.assertFalse(state.can_review)

    async def test_server_eligibility_preserves_guards(self):
        state = MessagingState()
        result = Mock()
        result.first.return_value = (10, 20)
        session = Mock()
        session.execute = AsyncMock(return_value=result)
        self.assertEqual(
            await state._eligible_review_task(session, 9, 10), (10, 20)
        )
        statement, params = session.execute.call_args.args
        sql = str(statement)
        self.assertIn("ct.poster_id = :sid AND ct.poster_confirmed", sql)
        self.assertIn("ct.helper_id = :sid AND ct.helper_confirmed", sql)
        self.assertIn("ct.poster_id <> ct.helper_id", sql)
        self.assertIn("AND poster.is_active", sql)
        self.assertIn("AND helper.is_active", sql)
        self.assertNotIn("is_verified", sql)
        self.assertIn("ct.id = :ctid", sql)
        self.assertIn(":sid IN (ct.poster_id, ct.helper_id)", sql)
        self.assertIn("p.author_id = ct.poster_id", sql)
        self.assertIn(
            "ct.application_id IS NULL OR a.id = ct.application_id", sql
        )
        self.assertIn("a.post_id = ct.post_id", sql)
        self.assertIn("a.helper_id = ct.helper_id", sql)
        self.assertIn("FOR UPDATE OF ct", sql)
        self.assertIn(
            "mb.blocker_id = ct.poster_id AND mb.blocked_id = ct.helper_id", sql
        )
        self.assertIn(
            "mb.blocker_id = ct.helper_id AND mb.blocked_id = ct.poster_id", sql
        )
        self.assertIn("a.status IN ('accepted', 'completed')", sql)
        self.assertEqual(params, {"ctid": 9, "sid": 10})
        self.assertNotIn(
            "release_task.poster_confirmed AND release_task.helper_confirmed",
            review_released_sql(),
        )
        self.assertNotIn("INTERVAL '30 days'", review_released_sql())
        self.assertIn("skillkind_member_block", sql)

    async def _assert_own_confirmation_sql(self, sid: int):
        state = MessagingState()
        result = Mock()
        result.first.return_value = None
        session = Mock()
        session.execute = AsyncMock(return_value=result)
        self.assertIsNone(await state._eligible_review_task(session, 9, sid))
        statement, params = session.execute.call_args.args
        self.assertEqual(params, {"ctid": 9, "sid": sid})
        sql = str(statement)
        predicate = sql.split("AND ((ct.poster_id = :sid", 1)[1].split(
            "AND poster.is_active", 1
        )[0]
        predicate = f"((ct.poster_id = :sid{predicate}".strip()
        with sqlite3.connect(":memory:") as connection:
            for poster_confirmed in (False, True):
                for helper_confirmed in (False, True):
                    with self.subTest(
                        sid=sid,
                        poster=poster_confirmed,
                        helper=helper_confirmed,
                    ):
                        row = connection.execute(
                            f"""WITH ct AS (
                                SELECT 10 AS poster_id, 20 AS helper_id,
                                       :poster AS poster_confirmed,
                                       :helper AS helper_confirmed
                            ) SELECT {predicate} FROM ct""",
                            {
                                "sid": sid,
                                "poster": poster_confirmed,
                                "helper": helper_confirmed,
                            },
                        ).fetchone()
                        expected = (sid == 10 and poster_confirmed) or (
                            sid == 20 and helper_confirmed
                        )
                        self.assertEqual(bool(row[0]), expected)

    async def test_poster_sql_requires_only_posters_confirmation(self):
        await self._assert_own_confirmation_sql(10)

    async def test_helper_sql_requires_only_helpers_confirmation(self):
        await self._assert_own_confirmation_sql(20)

    async def test_outsider_sql_cannot_use_either_confirmation(self):
        await self._assert_own_confirmation_sql(30)

    async def test_filters_preserve_selected_and_all_pending_targets(self):
        state = MessagingState()
        active = {**EMPTY_THREAD, "id": 1}
        pending = {**EMPTY_THREAD, "id": 2, "task_id": 20, "i_confirmed": True}
        completed = {**pending, "id": 3, "task_id": 30, "is_completed": True}
        reviewed = {**pending, "id": 4, "task_id": 40, "my_review_done": True}
        unconfirmed = {**pending, "id": 5, "task_id": 50, "i_confirmed": False}
        rows = [active, pending, completed, reviewed, unconfirmed]
        state.thread_filter = "active"
        state._apply_threads(rows, 3)
        self.assertEqual([t["id"] for t in state.threads], [1])
        self.assertEqual(state.selected_thread["id"], 3)
        self.assertEqual([t["task_id"] for t in state.review_targets], [20, 30])
        self.assertTrue(state.can_review)
        state.thread_filter = "completed"
        state._apply_threads(rows, 1)
        self.assertEqual(state.selected_thread["id"], 1)
        self.assertEqual(len(state.threads), 4)
        await run_event(state.select_review_target, 20)
        before = dict(state.selected_thread)
        await run_event(state.dismiss_review_target, 20)
        self.assertEqual(state.selected_thread, before)
        self.assertFalse(state.review_target_open)
        state._apply_threads(rows, 2)
        self.assertEqual([t["task_id"] for t in state.review_targets], [30])

    def test_review_title_average_and_message_order(self):
        state = MessagingState()
        state.selected_thread = {**EMPTY_THREAD, "other_name": "Mike Hunt"}
        self.assertEqual(state.review_title, "Review Mike Hunt")
        state.review_scores = dict(zip(state.review_scores, [5, 4, 5, 5]))
        self.assertEqual(state.review_average_label, "Overall 4.8 out of 5")
        source = Path("app/states/messaging_state.py").read_text()
        self.assertIn("ORDER BY m.sent_at ASC, m.id ASC", source)
        self.assertIn("yield MessagingState.open_review_target", source)
        self.assertIn("kindness = False", source)
        ui = Path("app/components/reviews_section.py").read_text()
        self.assertIn('"To review"', ui)
        self.assertIn('"My reviews"', ui)
        self.assertNotIn(
            "Reviews about the help you give and receive live here.", ui
        )
        self.assertNotIn("/100", ui)


if __name__ == "__main__":
    unittest.main()
