import inspect
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import reflex as rx

from app.app import index, session_skeleton
from app.components.auth_panel import sign_in_form
from app.components.chat_controls import (
    _correspondence_bubble,
    correspondence_bubble,
)
from app.components.guest_map import guest_map_canvas
from app.components.map_loading import map_loading_logo
from app.components.member_map import member_map_canvas
from app.states.auth_state import AuthState
from app.states.unified_inbox_state import (
    UnifiedInboxState,
    direction_flags,
    job_type,
)


class InboxRoleAndPresentationTests(unittest.TestCase):
    def test_three_poster_threads_always_belong_to_helpers(self):
        threads = [(True, True, False), (True, False, True), (True, True, True)]
        self.assertEqual(
            [job_type(posted) for posted, _, _ in threads], ["helper"] * 3
        )
        self.assertEqual(job_type(False), "helpee")
        self.assertEqual(direction_flags(True, True, 2, True), (True, True))
        self.assertEqual(direction_flags(True, True, 2, False), (True, True))

    def test_role_sql_and_summary_use_thread_ownership_not_messages(self):
        source = inspect.getsource(UnifiedInboxState.load_index.fn)
        self.assertIn(
            'if wanted == "helper":\n                        role_clause = " AND t.poster_id = :sid"',
            source,
        )
        self.assertIn(
            'elif wanted == "helpee":\n                        role_clause = " AND t.helper_id = :sid"',
            source,
        )
        self.assertIn("conv_type = job_type(i_posted)", source)
        self.assertIn('"type_label": TYPE_LABELS[conv_type]', source)
        self.assertIn("m.read_at IS NULL AND t.poster_id = :sid", source)
        self.assertIn("m.read_at IS NULL AND t.helper_id = :sid", source)
        self.assertNotIn(
            "EXISTS (SELECT 1 FROM skillkind_message sent WHERE sent.thread_id",
            source,
        )
        self.assertIn('elif wanted in ("sent", "received"):', source)
        self.assertIn("d.sender_id {sender}", source)
        self.assertIn('"has_sent": has_sent', source)
        self.assertIn('"has_received": has_received', source)
        self.assertIn("accepted.status = 'accepted'", source)
        self.assertIn("skillkind_member_block", source)

    def test_bubble_text_actions_and_signin_fields(self):
        bubble = inspect.getsource(_correspondence_bubble)
        self.assertIn(
            "whitespace-pre-wrap break-words [overflow-wrap:anywhere]", bubble
        )
        self.assertLess(
            bubble.index('msg["body"]'),
            bubble.index('aria_label="Delete message"'),
        )
        self.assertIn("size-11", bubble)
        self.assertIn("on_click=delete_event", bubble)
        self.assertIn("report_button(", bubble)
        self.assertTrue(
            correspondence_bubble(
                {
                    "body": "A long message",
                    "mine": True,
                    "sent_at": "Now",
                    "id": "1",
                }
            ).render()
        )
        form = sign_in_form()
        self.assertIsInstance(form, rx.Component)
        self.assertTrue(form.render())
        css = inspect.getsource(sign_in_form)
        self.assertIn(
            '#gah-sign-in-form input:is([type="email"], [type="password"])', css
        )
        self.assertIn("background-color: #ffffff !important", css)
        self.assertIn("color: #111827 !important", css)
        self.assertIn(":autofill", css)
        self.assertIn(":-webkit-autofill:focus", css)
        self.assertIn("-webkit-text-fill-color: #111827", css)

    def test_single_fullscreen_loader_and_accessible_map_updates(self):
        self.assertIn("fixed inset-0", str(session_skeleton().class_name))
        self.assertTrue(index().render())
        status = map_loading_logo()
        self.assertEqual(str(status.class_name), "sr-only")
        self.assertIn("status", str(status.role))
        self.assertIn("Updating map", str(status))
        for canvas in (guest_map_canvas, member_map_canvas):
            self.assertIn("map_loading_logo()", inspect.getsource(canvas))
            self.assertTrue(canvas().render())
        self.assertNotIn(
            "absolute inset-0", inspect.getsource(map_loading_logo)
        )


class InboxRoleQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_poster_and_helper_filters_and_mixed_direction(self):
        state = UnifiedInboxState(_reflex_internal_init=True)
        (await state.get_state(AuthState)).subscriber_id = "41"
        now = datetime(2026, 1, 2, 12, 0)
        poster_rows = [
            (
                id_,
                41,
                52,
                "Me",
                "member-41",
                True,
                "Helper",
                "member-52",
                True,
                f"Request {id_}",
                "open",
                "City",
                now,
                2,
                "Reply",
                1,
                "",
                "",
                latest,
                sent,
                received,
            )
            for id_, latest, sent, received in (
                (1, 41, True, True),
                (2, 52, False, True),
                (3, 41, True, False),
            )
        ]
        helper_rows = [
            (
                4,
                52,
                41,
                "Poster",
                "member-52",
                True,
                "Me",
                "member-41",
                True,
                "Another request",
                "open",
                "City",
                now,
                2,
                "Reply",
                1,
                "",
                "",
                52,
                True,
                True,
            )
        ]
        summary = (2, 1, 0)
        queries = []

        async def execute(statement, params):
            sql = str(statement)
            queries.append(sql)
            result = MagicMock()
            if "AS helper," in sql:
                result.one.return_value = summary
            elif "FROM skillkind_message_thread t" in sql:
                result.all.return_value = (
                    poster_rows
                    if "AND t.poster_id = :sid" in sql
                    else helper_rows
                )
            else:
                result.all.return_value = []
            return result

        session = MagicMock()
        session.execute = AsyncMock(side_effect=execute)
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=None)
        with patch("reflex.asession", return_value=context):
            state.type_filter = "helper"
            async for _ in UnifiedInboxState.load_index.fn(state):
                pass
            self.assertEqual(
                [item["key"] for item in state.items],
                ["job:1", "job:2", "job:3"],
            )
            self.assertTrue(
                all(item["conv_type"] == "helper" for item in state.items)
            )
            self.assertEqual(
                state.unread_by_type, {"helper": 2, "helpee": 1, "contact": 0}
            )
            self.assertTrue(state.items[0]["has_received"])
            self.assertTrue(state.items[0]["has_sent"])
            self.assertIn("AND t.poster_id = :sid", queries[0])
            state.type_filter = "helpee"
            async for _ in UnifiedInboxState.load_index.fn(state):
                pass
            self.assertEqual([item["key"] for item in state.items], ["job:4"])
            self.assertEqual(state.items[0]["type_label"], "Helpee")
            self.assertIn("AND t.helper_id = :sid", queries[-2])


if __name__ == "__main__":
    unittest.main()
