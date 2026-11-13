import reflex as rx

import inspect
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from faker import Faker
from sqlalchemy import insert, text

from app.components import messages_panel, unified_inbox
from app.models import (
    Subscriber,
    HelpPost,
    ContactLink,
    MessageThread,
    NonContactConversation,
)
from app.states.auth_state import AuthState
from app.states.unified_inbox_state import UnifiedInboxState, UnifiedItem


class DismissalContracts(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state = UnifiedInboxState(_reflex_internal_init=True)
        auth = await self.state.get_state(AuthState)
        auth.subscriber_id = "41"
        auth.email = "inbox-test@example.invalid"

    async def test_invalid_keys_and_signed_out_never_touch_database(self):
        with patch("reflex.asession") as database:
            for key in (
                "",
                "unknown:7",
                "contact:0",
                "job:-1",
                "job:7:8",
                "job:2147483648",
                "contact:7;DELETE",
                "noncontact:abc",
            ):
                await UnifiedInboxState.dismiss_thread.fn(self.state, key)
                self.assertTrue(self.state.error)
            (await self.state.get_state(AuthState)).email = ""
            await UnifiedInboxState.dismiss_thread.fn(self.state, "contact:7")
            self.assertIn("sign in", self.state.error)
            database.assert_not_called()

    async def test_missing_authorization_rolls_back_without_message_update(
        self,
    ):
        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(first=lambda: None))
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        self.state.selected_key = "job:7"
        self.state.view = "thread"
        with patch("reflex.asession", return_value=context):
            result = await UnifiedInboxState.dismiss_thread.fn(
                self.state, "job:7"
            )
        self.assertIsNone(result)
        self.assertTrue(self.state.error)
        self.assertEqual(self.state.selected_key, "job:7")
        self.assertEqual(session.execute.await_count, 1)
        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    async def test_message_update_failure_rolls_back_and_keeps_selection(self):
        session = MagicMock()
        session.execute = AsyncMock(
            side_effect=[
                MagicMock(first=lambda: (1,)),
                RuntimeError("fixture failure"),
            ]
        )
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        self.state.selected_key = "contact:7"
        self.state.visited_keys = ["contact:7"]
        with (
            patch("reflex.asession", return_value=context),
            patch("logging.exception") as logged,
        ):
            await UnifiedInboxState.dismiss_thread.fn(self.state, "contact:7")
        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()
        logged.assert_called()
        self.assertIn("messages are safe", self.state.error)
        self.assertEqual(self.state.selected_key, "contact:7")
        self.assertEqual(self.state.visited_keys, ["contact:7"])

    def test_listing_predicates_and_existing_semantics(self):
        source = inspect.getsource(UnifiedInboxState.load_index.fn)
        for kind, alias, ending in (
            ("contact", "cl", "{contact_direction}{contact_search}"),
            ("noncontact", "c", "{noncontact_direction}{noncontact_search}"),
            ("job", "t", "{role_clause}{job_search}"),
        ):
            start = source.index(f"dismissed.kind = '{kind}'")
            end = source.index(ending, start)
            clause = source[start:end]
            self.assertIn(f"dismissed.ref_id = {alias}.id", clause)
            self.assertIn(
                f"{alias}.last_message_at IS NULL OR {alias}.last_message_at <= dismissed.dismissed_at",
                clause,
            )
            self.assertLess(end, source.index("LIMIT 60", end))
        self.assertEqual(
            source.count("FROM skillkind_inbox_thread_dismissal dismissed"), 3
        )
        self.assertIn("dismissed.subscriber_id = :sid", source)
        self.assertIn("self.index_generation != generation", source)
        removal = inspect.getsource(UnifiedInboxState.dismiss_thread.fn)
        for token in (
            "own.is_active = TRUE",
            "p.status = 'accepted'",
            "ON CONFLICT (subscriber_id, kind, ref_id)",
            "EXCLUDED.dismissed_at",
            "RETURNING id",
            "sender_id <> :sid",
            "recipient_id = :sid",
            "AND read_at IS NULL",
            "await session.rollback()",
            "return UnifiedInboxState.load_index",
        ):
            self.assertIn(token, removal)
        self.assertNotIn("DELETE FROM", removal)

    def test_accessible_sibling_buttons_and_thread_header(self):
        fake = Faker()
        item = {field: "" for field in UnifiedItem.__annotations__}
        item.update(
            key="contact:7",
            kind="contact",
            conv_type="contact",
            type_label="Contact",
            ref_id=7,
            other_id=42,
            other_name=fake.name(),
            other_initial="M",
            other_verified=False,
            unread_count=1,
            message_count=2,
            has_sent=True,
            has_received=True,
        )
        card = unified_inbox.conversation_card(
            rx.Var.create(item).to(UnifiedItem)
        )
        self.assertEqual(len(card.children), 2)
        opened, removed = card.children
        self.assertIn("open_item", str(opened))
        self.assertIn("dismiss_thread", str(removed))
        self.assertNotIn("dismiss_thread", str(opened))
        self.assertIn("Remove from Inbox", str(removed))
        self.assertIn("aria-label", str(removed))
        self.assertIn("size-16", str(opened))
        self.assertIn("shadow-none", str(card.class_name))
        self.assertTrue(card.render())
        thread = messages_panel.inbox_thread_view()
        self.assertIn("dismiss_thread", str(thread.children[0]))
        self.assertIn("Back to Inbox", str(thread.children[0]))
        self.assertTrue(thread.render())
        self.assertIn(
            "error_banner(UnifiedInboxState.error)",
            inspect.getsource(messages_panel.inbox_thread_view),
        )


class DatabaseDismissalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        fake = Faker()
        self.members: list[int] = []
        async with rx.asession() as session:
            for _ in range(3):
                sid = (
                    await session.execute(
                        insert(Subscriber.__table__)
                        .values(
                            email=f"dismissal-{uuid4().hex}@example.invalid",
                            display_name=fake.name(),
                            is_active=True,
                            is_verified=True,
                        )
                        .returning(Subscriber.id)
                    )
                ).scalar_one()
                self.members.append(sid)
            first, second, _ = self.members
            self.post = (
                await session.execute(
                    insert(HelpPost.__table__)
                    .values(author_id=first, title=fake.sentence())
                    .returning(HelpPost.id)
                )
            ).scalar_one()
            contact = (
                await session.execute(
                    insert(ContactLink.__table__)
                    .values(
                        requester_id=first,
                        recipient_id=second,
                        status="accepted",
                    )
                    .returning(ContactLink.id)
                )
            ).scalar_one()
            direct = (
                await session.execute(
                    insert(NonContactConversation.__table__)
                    .values(initiator_id=first, recipient_id=second)
                    .returning(NonContactConversation.id)
                )
            ).scalar_one()
            job = (
                await session.execute(
                    insert(MessageThread.__table__)
                    .values(
                        post_id=self.post,
                        poster_id=first,
                        helper_id=second,
                        subject=fake.sentence(),
                    )
                    .returning(MessageThread.id)
                )
            ).scalar_one()
            self.sources = {
                "contact": (
                    contact,
                    "skillkind_contact_link",
                    "skillkind_contact_message",
                    "contact_link_id",
                ),
                "noncontact": (
                    direct,
                    "skillkind_noncontact_conversation",
                    "skillkind_noncontact_message",
                    "conversation_id",
                ),
                "job": (
                    job,
                    "skillkind_message_thread",
                    "skillkind_message",
                    "thread_id",
                ),
            }
            for kind, (ref, parent, messages, foreign) in self.sources.items():
                for sender, recipient in ((first, second), (second, first)):
                    recipient_column = ", recipient_id" if kind != "job" else ""
                    recipient_value = ", :recipient" if kind != "job" else ""
                    await session.execute(
                        text(
                            f"INSERT INTO {messages} ({foreign}, sender_id, body{recipient_column}) VALUES (:ref, :sender, :body{recipient_value})"
                        ),
                        {
                            "ref": ref,
                            "sender": sender,
                            "recipient": recipient,
                            "body": fake.sentence(),
                        },
                    )
                await session.execute(
                    text(
                        f"UPDATE {parent} SET last_message_at = now() - INTERVAL '1 minute' WHERE id = :ref"
                    ),
                    {"ref": ref},
                )
            await session.commit()
        self.state = UnifiedInboxState(_reflex_internal_init=True)
        auth = await self.state.get_state(AuthState)
        auth.subscriber_id = str(first)
        auth.email = "dismissal-test@example.invalid"

    async def asyncTearDown(self):
        async with rx.asession() as session:
            await session.execute(
                text("DELETE FROM skillkind_help_post WHERE id = :id"),
                {"id": self.post},
            )
            await session.execute(
                text("DELETE FROM skillkind_subscriber WHERE id = ANY(:ids)"),
                {"ids": self.members},
            )
            await session.commit()

    async def load(self, state):
        async for _ in UnifiedInboxState.load_index.fn(state):
            pass

    async def test_three_kinds_private_persistent_and_new_messages_reappear(
        self,
    ):
        viewer, other, _ = self.members
        for kind, (ref, parent, messages, foreign) in self.sources.items():
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "UPDATE skillkind_contact_link SET status = :status WHERE id = :ref"
                    ),
                    {
                        "status": "accepted"
                        if kind == "contact"
                        else "pending",
                        "ref": self.sources["contact"][0],
                    },
                )
                await session.commit()
            key = f"{kind}:{ref}"
            await self.load(self.state)
            self.assertIn(key, [item["key"] for item in self.state.items])
            self.state.selected_key = key
            self.state.view = "thread"
            self.state.visited_keys = [key, "job:999"]
            result = await UnifiedInboxState.dismiss_thread.fn(self.state, key)
            self.assertIsNotNone(result)
            self.assertEqual(self.state.error, "")
            self.assertEqual(
                (self.state.view, self.state.selected_key), ("inbox", "")
            )
            self.assertNotIn(key, self.state.visited_keys)
            self.assertNotIn(key, [item["key"] for item in self.state.items])
            async with rx.asession() as session:
                rows = (
                    await session.execute(
                        text(
                            f"SELECT sender_id, read_at FROM {messages} WHERE {foreign} = :ref ORDER BY id"
                        ),
                        {"ref": ref},
                    )
                ).all()
                self.assertEqual(len(rows), 2)
                self.assertIsNone(
                    next(row[1] for row in rows if row[0] == viewer)
                )
                self.assertIsNotNone(
                    next(row[1] for row in rows if row[0] == other)
                )
                self.assertEqual(
                    (
                        await session.execute(
                            text(
                                "SELECT COUNT(*) FROM skillkind_inbox_thread_dismissal WHERE subscriber_id = :other"
                            ),
                            {"other": other},
                        )
                    ).scalar_one(),
                    0,
                )
            fresh = UnifiedInboxState(_reflex_internal_init=True)
            auth = await fresh.get_state(AuthState)
            auth.subscriber_id = str(viewer)
            auth.email = "fresh-session@example.invalid"
            await self.load(fresh)
            self.assertNotIn(key, [item["key"] for item in fresh.items])
            auth.subscriber_id = str(other)
            await self.load(fresh)
            self.assertIn(key, [item["key"] for item in fresh.items])
            auth.subscriber_id = str(viewer)
            for sender in (other, viewer):
                async with rx.asession() as session:
                    recipient_column = ", recipient_id" if kind != "job" else ""
                    recipient_value = ", :recipient" if kind != "job" else ""
                    await session.execute(
                        text(
                            f"INSERT INTO {messages} ({foreign}, sender_id, body{recipient_column}) VALUES (:ref, :sender, 'New message'{recipient_value})"
                        ),
                        {
                            "ref": ref,
                            "sender": sender,
                            "recipient": viewer if sender == other else other,
                        },
                    )
                    await session.execute(
                        text(
                            f"UPDATE {parent} SET last_message_at = :stamp WHERE id = :ref"
                        ),
                        {
                            "ref": ref,
                            "stamp": datetime.now(UTC) + timedelta(seconds=1),
                        },
                    )
                    await session.commit()
                await self.load(self.state)
                self.assertIn(key, [item["key"] for item in self.state.items])
                await UnifiedInboxState.dismiss_thread.fn(self.state, key)
            async with rx.asession() as session:
                count = (
                    await session.execute(
                        text(
                            "SELECT COUNT(*) FROM skillkind_inbox_thread_dismissal WHERE subscriber_id = :sid AND kind = :kind AND ref_id = :ref"
                        ),
                        {"sid": viewer, "kind": kind, "ref": ref},
                    )
                ).scalar_one()
                self.assertEqual(count, 1)

    async def test_outsider_inactive_pending_and_bilateral_blocks_no_writes(
        self,
    ):
        auth = await self.state.get_state(AuthState)
        viewer, other, outsider = self.members
        for kind, (ref, _, _, _) in self.sources.items():
            auth.subscriber_id = str(outsider)
            await UnifiedInboxState.dismiss_thread.fn(
                self.state, f"{kind}:{ref}"
            )
            self.assertTrue(self.state.error)
        auth.subscriber_id = str(viewer)
        async with rx.asession() as session:
            await session.execute(
                text(
                    "UPDATE skillkind_subscriber SET is_active = FALSE WHERE id = :sid"
                ),
                {"sid": viewer},
            )
            await session.commit()
        await UnifiedInboxState.dismiss_thread.fn(
            self.state, f"job:{self.sources['job'][0]}"
        )
        self.assertTrue(self.state.error)
        async with rx.asession() as session:
            await session.execute(
                text(
                    "UPDATE skillkind_subscriber SET is_active = TRUE WHERE id = :sid"
                ),
                {"sid": viewer},
            )
            await session.execute(
                text(
                    "UPDATE skillkind_contact_link SET status = 'pending' WHERE id = :ref"
                ),
                {"ref": self.sources["contact"][0]},
            )
            await session.commit()
        await UnifiedInboxState.dismiss_thread.fn(
            self.state, f"contact:{self.sources['contact'][0]}"
        )
        self.assertTrue(self.state.error)
        for blocker, blocked in ((viewer, other), (other, viewer)):
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "INSERT INTO skillkind_member_block (blocker_id, blocked_id) VALUES (:first, :second)"
                    ),
                    {"first": blocker, "second": blocked},
                )
                await session.commit()
            for kind in ("noncontact", "job"):
                await UnifiedInboxState.dismiss_thread.fn(
                    self.state, f"{kind}:{self.sources[kind][0]}"
                )
                self.assertTrue(self.state.error)
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "DELETE FROM skillkind_member_block WHERE blocker_id = :first AND blocked_id = :second"
                    ),
                    {"first": blocker, "second": blocked},
                )
                await session.commit()
        async with rx.asession() as session:
            self.assertEqual(
                (
                    await session.execute(
                        text(
                            "SELECT COUNT(*) FROM skillkind_inbox_thread_dismissal WHERE subscriber_id = ANY(:ids)"
                        ),
                        {"ids": self.members},
                    )
                ).scalar_one(),
                0,
            )
            for ref, _, messages, foreign in self.sources.values():
                self.assertEqual(
                    (
                        await session.execute(
                            text(
                                f"SELECT COUNT(*) FROM {messages} WHERE {foreign} = :ref AND read_at IS NULL"
                            ),
                            {"ref": ref},
                        )
                    ).scalar_one(),
                    2,
                )


if __name__ == "__main__":
    unittest.main()
