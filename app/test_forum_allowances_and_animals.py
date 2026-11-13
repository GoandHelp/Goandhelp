import reflex as rx

import asyncio
import datetime
import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.avatars import ANIMAL_AVATARS, animal_avatar, member_avatar
from app.components import community_panel, paywall
from app.membership import FREE_BENEFITS, PREMIUM_BENEFITS
from app.states import community_state as forum
from app.states.community_state import CommunityState, EMPTY_TOPIC
from app.states.auth_state import AuthState


class Result:
    def __init__(self, row):
        self.row = row

    def first(self):
        return self.row


class ForumDatabase:
    def __init__(self, premium=False):
        self.premium = premium
        self.topics = []
        self.comments = []
        self.notifications = []
        self.locks = {}
        self.sessions = []

    def session(self):
        session = ForumSession(self)
        self.sessions.append(session)
        return session

    async def is_premium(self, session, sid):
        session.trace.append("premium")
        self.assert_locked(session)
        return self.premium

    def assert_locked(self, session):
        if session.held_lock is None:
            raise AssertionError("Membership was checked before advisory lock")


class ForumSession:
    def __init__(self, database):
        self.database = database
        self.trace = []
        self.pending = []
        self.held_lock = None
        self.committed = False
        self.count_parameters = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    async def rollback(self):
        self.pending.clear()
        if self.held_lock is not None:
            self.held_lock.release()
            self.held_lock = None

    async def commit(self):
        self.trace.append("commit")
        for kind, record in self.pending:
            getattr(self.database, kind).append(record)
        self.pending.clear()
        self.committed = True
        await self.rollback()

    async def execute(self, statement, parameters):
        sql = str(statement)
        await asyncio.sleep(0)
        if "pg_advisory_xact_lock" in sql:
            self.trace.append("lock")
            assert parameters["namespace"] == forum.FORUM_LOCK_NAMESPACE
            lock = self.database.locks.setdefault(
                parameters["sid"], asyncio.Lock()
            )
            await lock.acquire()
            self.held_lock = lock
            return Result(None)
        if "COUNT(*)" in sql:
            self.trace.append("count")
            assert "created_at >= :start AND created_at < :end" in sql
            assert "topic_id" not in sql
            self.count_parameters = parameters

            def count(records):
                return sum(
                    record["sid"] == parameters["sid"]
                    and parameters["start"]
                    <= record["stamp"]
                    < parameters["end"]
                    for record in records
                )

            return Result(
                (count(self.database.topics), count(self.database.comments))
            )
        if "SELECT id, author_id, title" in sql:
            return Result((parameters["tid"], 99, "Discussion"))
        if "INSERT INTO skillkind_community_topic" in sql:
            kind = "topics"
        elif "INSERT INTO skillkind_community_comment" in sql:
            kind = "comments"
        elif "INSERT INTO skillkind_member_notification" in sql:
            kind = "notifications"
        else:
            raise AssertionError(sql)
        self.trace.append("insert")
        self.pending.append((kind, dict(parameters)))
        return Result(None)


class Writer:
    def __init__(self, sid="7"):
        self.auth = SimpleNamespace(subscriber_id=sid, is_signed_in=bool(sid))
        self.membership = SimpleNamespace(paywall_open=False, upgrade_reason="")
        self.title_draft = "Neighbourhood ideas"
        self.body_draft = "A kind discussion for our community."
        self.subject_draft = forum.COMMUNITY_SUBJECT_OTHER
        self.comment_draft = "Thanks for sharing this idea."
        self.selected_topic = {**EMPTY_TOPIC, "id": 42}
        self.draft_version = 0
        self.comment_version = 0
        self.composer_open = True
        self.is_posting = False
        self.is_commenting = False
        self.error = ""
        self.success = ""
        self.comments = []
        self.monthly_topics_used = 0
        self.monthly_comments_used = 0
        self.forum_premium = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, state):
        return self.auth if state is AuthState else self.membership

    def _set_usage(self, premium, topics, comments):
        self.forum_premium = premium
        self.monthly_topics_used = topics
        self.monthly_comments_used = comments

    @property
    def topic_allowance_available(self):
        return self.forum_premium or self.monthly_topics_used < 1

    @property
    def comment_allowance_available(self):
        return self.forum_premium or self.monthly_comments_used < 10

    async def _quota_rejected(self, topic):
        await CommunityState._quota_rejected(self, topic)


async def consume(handler, state):
    return [event async for event in handler.fn(state)]


class ForumQuotaTests(unittest.IsolatedAsyncioTestCase):
    async def run_writers(self, database, handler, writers):
        async def not_blocked(*args):
            return False

        with (
            patch.object(rx, "asession", database.session),
            patch.object(forum, "db_is_premium", database.is_premium),
            patch.object(forum, "are_members_blocked", not_blocked),
        ):
            await asyncio.gather(
                *(consume(handler, writer) for writer in writers)
            )

    async def test_new_canonical_subjects_pass_server_posting_validation(self):
        for subject in ("Activities", "Money"):
            with self.subTest(subject=subject):
                database = ForumDatabase()
                writer = Writer()
                writer.subject_draft = subject
                await self.run_writers(
                    database, CommunityState.create_topic, [writer]
                )
                self.assertEqual(len(database.topics), 1)
                self.assertEqual(database.topics[0]["subject"], subject)
                self.assertEqual(writer.monthly_topics_used, 1)
                self.assertFalse(writer.composer_open)
                self.assertEqual(writer.subject_draft, "")
                self.assertFalse(writer.membership.paywall_open)

    async def test_unknown_subject_never_reaches_database(self):
        database = ForumDatabase()
        writer = Writer()
        writer.subject_draft = "Not a canonical subject"
        await self.run_writers(database, CommunityState.create_topic, [writer])
        self.assertEqual(database.sessions, [])
        self.assertEqual(database.topics, [])
        self.assertIn("pinned subjects", writer.error)
        self.assertEqual(writer.subject_draft, "Not a canonical subject")

    async def test_concurrent_free_topics_use_same_transaction_lock(self):
        database = ForumDatabase()
        writers = [Writer(), Writer()]
        await self.run_writers(database, CommunityState.create_topic, writers)
        self.assertEqual(len(database.topics), 1)
        rejected = next(
            writer for writer in writers if writer.membership.paywall_open
        )
        self.assertEqual(
            rejected.membership.upgrade_reason, forum.FORUM_TOPIC_REASON
        )
        self.assertEqual(rejected.error, forum.FORUM_TOPIC_CAP)
        self.assertEqual(rejected.title_draft, "Neighbourhood ideas")
        self.assertEqual(
            rejected.body_draft, "A kind discussion for our community."
        )
        self.assertEqual(rejected.subject_draft, forum.COMMUNITY_SUBJECT_OTHER)
        self.assertFalse(rejected.is_posting)
        for session in database.sessions:
            self.assertEqual(session.trace[:3], ["lock", "premium", "count"])
        self.assertEqual(
            sum(session.committed for session in database.sessions), 1
        )
        committed = next(
            session for session in database.sessions if session.committed
        )
        self.assertEqual(committed.trace[-2:], ["insert", "commit"])

    async def test_comments_are_ten_total_not_per_discussion_and_keep_draft(
        self,
    ):
        database = ForumDatabase()
        stamp = datetime.datetime.now(datetime.UTC)
        database.comments = [
            {"sid": 7, "stamp": stamp, "tid": number} for number in range(9)
        ]
        writers = [Writer(), Writer()]
        writers[1].selected_topic = {**EMPTY_TOPIC, "id": 43}
        await self.run_writers(database, CommunityState.add_comment, writers)
        self.assertEqual(len(database.comments), 10)
        self.assertEqual(len(database.notifications), 1)
        rejected = next(
            writer for writer in writers if writer.membership.paywall_open
        )
        self.assertEqual(
            rejected.membership.upgrade_reason, forum.FORUM_COMMENT_REASON
        )
        self.assertEqual(rejected.error, forum.FORUM_COMMENT_CAP)
        self.assertEqual(
            rejected.comment_draft, "Thanks for sharing this idea."
        )
        self.assertFalse(rejected.is_commenting)
        self.assertEqual(rejected.monthly_comments_used, 10)

    async def test_premium_bypasses_both_caps(self):
        for handler, kind, used in (
            (CommunityState.create_topic, "topics", 1),
            (CommunityState.add_comment, "comments", 10),
        ):
            database = ForumDatabase(premium=True)
            records = [
                {"sid": 7, "stamp": datetime.datetime.now(datetime.UTC)}
                for _ in range(used)
            ]
            setattr(database, kind, records)
            writers = [Writer(), Writer()]
            await self.run_writers(database, handler, writers)
            self.assertEqual(len(getattr(database, kind)), used + 2)
            self.assertTrue(
                all(not writer.membership.paywall_open for writer in writers)
            )

    async def test_previous_month_and_other_members_do_not_consume_allowance(
        self,
    ):
        database = ForumDatabase()
        stamp = datetime.datetime.now(datetime.UTC)
        start, _ = forum.forum_month_bounds(stamp)
        database.topics = [
            {"sid": 7, "stamp": start - datetime.timedelta(microseconds=1)},
            {"sid": 8, "stamp": stamp},
        ]
        await self.run_writers(
            database, CommunityState.create_topic, [Writer()]
        )
        self.assertEqual(len(database.topics), 3)

    async def test_signed_out_and_invalid_text_never_insert(self):
        for handler in (
            CommunityState.create_topic,
            CommunityState.add_comment,
        ):
            database = ForumDatabase(premium=True)
            writer = Writer("")
            await self.run_writers(database, handler, [writer])
            self.assertEqual(database.sessions, [])
            self.assertIn("sign in", writer.error)
        writer = Writer()
        writer.comment_draft = "word " * 1001
        await self.run_writers(
            ForumDatabase(), CommunityState.add_comment, [writer]
        )
        self.assertIn("limited", writer.error)
        self.assertFalse(writer.is_commenting)

    async def test_composer_and_reply_prompt_refresh_stale_monthly_allowances(
        self,
    ):
        database = ForumDatabase()
        writer = Writer()
        writer.composer_open = False
        with (
            patch.object(rx, "asession", database.session),
            patch.object(
                forum,
                "forum_usage",
                AsyncMock(
                    return_value=(
                        False,
                        1,
                        10,
                        datetime.datetime.now(datetime.UTC),
                    )
                ),
            ),
        ):
            await CommunityState.toggle_composer.fn(writer)
            self.assertFalse(writer.composer_open)
            self.assertEqual(
                writer.membership.upgrade_reason,
                "Go premium to start more topics",
            )
            self.assertEqual(
                writer.body_draft, "A kind discussion for our community."
            )
            await CommunityState.open_comment_paywall.fn(writer)
            self.assertEqual(
                writer.membership.upgrade_reason, "Go premium to comment more"
            )
        writer.membership.paywall_open = False
        with (
            patch.object(rx, "asession", database.session),
            patch.object(
                forum,
                "forum_usage",
                AsyncMock(
                    return_value=(
                        False,
                        0,
                        0,
                        datetime.datetime.now(datetime.UTC),
                    )
                ),
            ),
        ):
            await CommunityState.toggle_composer.fn(writer)
            self.assertTrue(writer.composer_open)
            await CommunityState.open_comment_paywall.fn(writer)
            self.assertTrue(writer.comment_allowance_available)
            self.assertFalse(writer.membership.paywall_open)

    async def test_failed_insert_clears_busy_without_losing_draft(self):
        database = ForumDatabase()

        async def fail(*args, **kwargs):
            raise RuntimeError("Unavailable")

        writer = Writer()
        with patch.object(forum, "forum_usage", fail):
            await self.run_writers(
                database, CommunityState.add_comment, [writer]
            )
        self.assertFalse(writer.is_commenting)
        self.assertEqual(writer.comment_draft, "Thanks for sharing this idea.")
        self.assertIn("try again", writer.error)
        self.assertFalse(database.sessions[0].committed)


class ForumMonthAndAvatarTests(unittest.TestCase):
    def test_utc_month_boundaries_including_leap_year_and_year_rollover(self):
        for stamp, expected_start, expected_end in (
            (
                datetime.datetime(2024, 2, 29, 23, 59, tzinfo=datetime.UTC),
                (2024, 2, 1),
                (2024, 3, 1),
            ),
            (
                datetime.datetime(2025, 12, 31, 23, 59, tzinfo=datetime.UTC),
                (2025, 12, 1),
                (2026, 1, 1),
            ),
            (
                datetime.datetime(
                    2026,
                    3,
                    1,
                    1,
                    tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
                ),
                (2026, 2, 1),
                (2026, 3, 1),
            ),
        ):
            start, end = forum.forum_month_bounds(stamp)
            self.assertEqual(
                (start.year, start.month, start.day), expected_start
            )
            self.assertEqual((end.year, end.month, end.day), expected_end)
            self.assertEqual(start.tzinfo, datetime.UTC)
            self.assertLess(start, end)

    def test_four_local_choices_stable_and_email_safe(self):
        choices = [animal_avatar(f"member-{number}") for number in range(1, 5)]
        self.assertEqual(set(choices), set(ANIMAL_AVATARS))
        for seed in (
            "",
            "member-123",
            "owl",
            "猫",
            "🐈",
            "private@example.test",
        ):
            self.assertEqual(animal_avatar(seed), animal_avatar(seed))
            self.assertIn(animal_avatar(seed), ANIMAL_AVATARS)
            if seed:
                self.assertNotIn(seed, animal_avatar(seed))
        self.assertEqual(
            animal_avatar("private@example.test"), animal_avatar("member")
        )
        for path in ANIMAL_AVATARS:
            self.assertTrue(Path("assets", path.lstrip("/")).is_file())

    def test_var_helper_compiles_and_photos_take_precedence(self):
        result = animal_avatar(AuthState.subscriber_id)
        self.assertIsInstance(result, rx.Var)
        self.assertIn("codePointAt", str(result))
        self.assertNotIn("dicebear", str(result))
        self.assertEqual(
            member_avatar("photo.webp", "member-9"), "/_upload/photo.webp"
        )
        self.assertEqual(
            member_avatar("", "member-9"), animal_avatar("member-9")
        )
        self.assertTrue(
            rx.image(
                src=member_avatar(
                    rx.Var.create("photo.webp"), AuthState.subscriber_id
                ),
                alt="Member",
            ).render()
        )

    def test_ui_allowances_paywall_reasons_and_no_external_avatar_service(self):
        section = inspect.getsource(community_panel.community_section)
        self.assertIn("1 topic per month", section)
        self.assertIn("10 comments per month", section)
        self.assertIn("CommunityState.toggle_composer", section)
        self.assertIn("CommunityState.topic_allowance_available", section)
        self.assertNotIn("MembershipState.is_premium", section)
        self.assertIn(
            "CommunityState.comment_allowance_available",
            inspect.getsource(community_panel.topic_detail),
        )
        self.assertIn(
            "CommunityState.open_comment_paywall",
            inspect.getsource(community_panel.locked_comment_prompt),
        )
        modal = inspect.getsource(paywall.paywall_modal)
        self.assertIn("MembershipState.upgrade_reason", modal)
        self.assertIn("CATEGORY_UPGRADE_REASON", modal)
        self.assertIn("FORUM_TOPIC_CAP", modal)
        self.assertIn("FORUM_COMMENT_CAP", modal)
        self.assertTrue(community_panel.community_section().render())
        self.assertTrue(paywall.paywall_modal().render())
        self.assertTrue(
            any(
                "Unlimited" in benefit and "forum" in benefit
                for benefit in PREMIUM_BENEFITS
            )
        )
        self.assertTrue(
            any("1 forum topic" in benefit for benefit in FREE_BENEFITS)
        )
        self.assertTrue(
            any("10 forum comments" in benefit for benefit in FREE_BENEFITS)
        )
        for folder in ("app/components", "app/states"):
            for path in Path(folder).glob("*.py"):
                self.assertNotIn(
                    "api.dicebear.com", path.read_text(), str(path)
                )


if __name__ == "__main__":
    unittest.main()
