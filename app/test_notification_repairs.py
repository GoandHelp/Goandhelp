import reflex as rx

import ast
import inspect
import textwrap
import sqlite3
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.states.contacts_state import ContactsState
from app.states.notification_state import (
    NotificationState,
    NOTIFICATION_FILTER,
    _classify,
)
from app.states.messaging_state import MessagingState, EMPTY_THREAD
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState
from app.states.community_state import CommunityState
from app.states.noncontact_state import NonContactMessagingState
from app.states.unified_inbox_state import UnifiedInboxState


class NotificationRepairTests(unittest.IsolatedAsyncioTestCase):
    def test_community_preferences(self):
        self.assertNotRegex(
            NOTIFICATION_FILTER,
            r"(?i)\bOR\s+kind\s*(?=OR\b|AND\b|THEN\b|$)",
        )
        community_branch = NOTIFICATION_FILTER.split("WHEN", 2)[1]
        self.assertEqual(
            " ".join(community_branch.split()),
            "LOWER(TRIM(COALESCE(target_route, ''))) = 'community' "
            "OR LOWER(TRIM(COALESCE(target_route, ''))) LIKE 'community:%' "
            "OR kind LIKE 'community_%' THEN :notify_community_activity",
        )
        with sqlite3.connect(":memory:") as db:
            for route in (
                "community",
                "community:reviews:42",
                "community:events",
                "community:forum:9",
                " COMMUNITY:REVIEWS:42 ",
            ):
                for enabled in (False, True):
                    params = dict(
                        target_route=route,
                        kind="help_offer",
                        notify_community_activity=enabled,
                        notify_help_offers=True,
                        notify_messages=True,
                        notify_schedule_changes=True,
                        notify_reminders=True,
                    )
                    result = db.execute(
                        f"SELECT {NOTIFICATION_FILTER} FROM (SELECT :target_route AS target_route, :kind AS kind)",
                        params,
                    ).fetchone()[0]
                    self.assertEqual(bool(result), enabled)
                self.assertEqual(
                    _classify("help_offer", route, "")[0], "community"
                )
        self.assertEqual(
            _classify("community_like", "community:reviews:42", "")[1],
            "reviews",
        )

    def test_noncontact_availability_generator(self):
        tree = ast.parse(
            textwrap.dedent(
                inspect.getsource(NotificationState.open_notification.fn)
            )
        )
        expected = ast.parse(
            'any(c["conv_id"] == direct for c in noncontact.conversations)',
            mode="eval",
        ).body
        calls = [
            ast.dump(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        ]
        self.assertIn(ast.dump(expected), calls)
        self.assertNotIn(
            ast.dump(
                ast.parse('any(c["conv_id"] == direct)', mode="eval").body
            ),
            calls,
        )

    async def test_complete_contact_success_and_unchanged_toast(self):
        auth = SimpleNamespace(subscriber_id="10")
        state = Mock()
        state.get_state = AsyncMock(return_value=auth)
        state.__aenter__ = AsyncMock(return_value=state)
        state.__aexit__ = AsyncMock(return_value=False)
        result = Mock()
        result.first.side_effect = [("pending", "Alex"), (20,)]
        session = Mock(
            execute=AsyncMock(return_value=result), commit=AsyncMock()
        )

        @asynccontextmanager
        async def connection():
            yield session

        with (
            patch.object(rx, "asession", connection),
            patch(
                "app.states.contacts_state.are_members_blocked",
                AsyncMock(return_value=False),
            ),
        ):
            events = []
            async for event in ContactsState.accept_request.fn(state, 7):
                events.append(event)
        self.assertEqual(
            state.success,
            "Alex is now one of your contacts — say hello whenever you're passing through.",
        )
        self.assertEqual(len(events), 3)
        self.assertIn(
            'yield rx.toast(f"{other_name} added to your contacts.", duration=3500)',
            inspect.getsource(ContactsState.accept_request.fn),
        )

    async def route(self, kind, route="", thread=0, targets=(), eligible=True):
        profile = SimpleNamespace(active_tab="map")
        community = SimpleNamespace(section="community")
        messaging = SimpleNamespace(
            dismissed_review_task_ids=[],
            review_targets=list(targets),
            threads=[{**EMPTY_THREAD, "id": thread}] if thread else [],
            selected_thread={**EMPTY_THREAD, "id": 999},
            _load_threads_data=AsyncMock(),
            _eligible_review_task=AsyncMock(
                return_value=(10, 20) if eligible else None
            ),
        )
        states = {
            AuthState: SimpleNamespace(subscriber_id="10"),
            ProfileState: profile,
            CommunityState: community,
            MessagingState: messaging,
            ContactsState: SimpleNamespace(),
            NonContactMessagingState: SimpleNamespace(),
            UnifiedInboxState: SimpleNamespace(preserve_next_mount=False),
        }
        state = Mock(action_id=0, error="")
        state.get_state = AsyncMock(side_effect=lambda cls: states[cls])
        state.__aenter__ = AsyncMock(return_value=state)
        state.__aexit__ = AsyncMock(return_value=False)
        result = Mock()
        result.first.side_effect = [
            (kind, route, "Review helper", 20, 0, 8, 0, 0),
            (thread,) if thread else None,
        ]
        session = Mock(
            execute=AsyncMock(return_value=result), commit=AsyncMock()
        )

        @asynccontextmanager
        async def connection():
            yield session

        with patch.object(rx, "asession", connection):
            events = []
            async for event in NotificationState.open_notification.fn(
                state, {"id": 3}
            ):
                events.append(event)
        return state, profile, community, messaging, events

    async def test_help_post_without_thread_falls_back(self):
        for kind in ("help_offer", "direct_help_request", "direct_request"):
            state, profile, _, messaging, events = await self.route(kind)
            self.assertEqual(profile.active_tab, "help")
            self.assertEqual(state.error, "")
            messaging._load_threads_data.assert_not_awaited()
            self.assertTrue(
                any(
                    getattr(e, "fn", None) and e.fn.__name__ == "load_help_hub"
                    for e in events
                )
            )

    async def test_job_uses_exact_thread_not_previous_selection(self):
        state, profile, _, messaging, events = await self.route(
            "help_offer", thread=17
        )
        self.assertEqual(profile.active_tab, "inbox")
        self.assertEqual(state.error, "")
        messaging._load_threads_data.assert_awaited_once_with("10", 17)
        opening = [
            e
            for e in events
            if getattr(getattr(e, "handler", None), "fn", None)
            and e.handler.fn.__name__ == "open_item"
        ]
        self.assertEqual(len(opening), 1)
        self.assertIn("17", str(opening[0].args))

    async def test_exact_completed_task_after_loading(self):
        target = {**EMPTY_THREAD, "id": 17, "task_id": 42, "i_confirmed": True}
        state, profile, community, messaging, events = await self.route(
            "community_like", "community:reviews:42", targets=[target]
        )
        self.assertEqual(state.error, "")
        self.assertEqual(
            (profile.active_tab, community.section), ("community", "reviews")
        )
        messaging._load_threads_data.assert_awaited_once_with("10", 0)
        self.assertEqual(
            messaging._eligible_review_task.await_args.args[1:], (42, 10)
        )
        selection = [
            e
            for e in events
            if getattr(getattr(e, "handler", None), "fn", None)
            and e.handler.fn.__name__ == "select_review_target"
        ]
        self.assertEqual(len(selection), 1)
        self.assertIn("42", str(selection[0].args))
        self.assertTrue(
            any(
                getattr(e, "fn", None) and e.fn.__name__ == "open_review_target"
                for e in events
            )
        )

    async def test_missing_exact_review_is_unavailable(self):
        for targets in (
            [],
            [{**EMPTY_THREAD, "id": 17, "task_id": 41, "i_confirmed": True}],
        ):
            with self.assertLogs(level="ERROR"):
                state, _, _, _, _ = await self.route(
                    "community_like", "community:reviews:42", targets=targets
                )
            self.assertEqual(
                state.error,
                "This notification destination is no longer available.",
            )

    def test_reused_loaders_lock_their_mutations(self):
        for path, method, assignment in (
            (
                "contacts_state",
                "_load_contacts_data",
                "self.contacts = accepted",
            ),
            (
                "noncontact_state",
                "_load_conversations_data",
                "self.conversations = loaded",
            ),
            ("messaging_state", "_load_threads_data", "self._apply_threads("),
        ):
            source = (
                Path(f"app/states/{path}.py")
                .read_text()
                .split(f"async def {method}", 1)[1]
                .split("\n    @rx.event", 1)[0]
            )
            self.assertLess(
                source.index("async with self:"), source.index(assignment)
            )


if __name__ == "__main__":
    unittest.main()
