import reflex as rx

import datetime
import inspect
import unittest
from unittest.mock import AsyncMock, patch
from contextlib import ExitStack

from app.states.help_hub_state import HelpHubState, CompletedJob, PastHelper
from app.components import help_hub_panel as panel


class CompletedHistoryTests(unittest.IsolatedAsyncioTestCase):
    def row(self):
        return (
            17,
            8,
            3,
            "Completed request",
            "Rome",
            "Italy",
            datetime.datetime(2026, 1, 2),
            90,
            "A meal",
            "Thank you",
            "Helper",
            "helper",
            "portrait.png",
            True,
            4.5,
            8,
            22,
            4,
        )

    def test_mapping(self):
        job = HelpHubState._completed_job(self.row())
        helper = HelpHubState._past_helper(self.row())
        self.assertEqual(set(job), set(CompletedJob.__annotations__))
        self.assertEqual(set(helper), set(PastHelper.__annotations__))
        self.assertEqual(job["location"], "Rome, Italy")
        self.assertEqual(job["completed_date"], "Jan 02, 2026")
        self.assertTrue(job["actual_duration"])
        self.assertEqual(job["reward_given"], "A meal")
        self.assertEqual(job["helper_handle"], "@helper")
        self.assertEqual(helper["completed_job_count"], 4)
        self.assertEqual(helper["thread_id"], 22)
        self.assertEqual(helper["latest_title"], job["title"])
        for dto in (job, helper):
            self.assertFalse(any("email" in key for key in dto))
        row = list(self.row())
        for index in range(3, 18):
            row[index] = None
        empty = HelpHubState._completed_job(row)
        self.assertEqual(empty["actual_duration"], "")
        self.assertEqual(empty["thread_id"], 0)
        self.assertEqual(empty["helper_rating"], 0.0)
        self.assertEqual(empty["helper_rating_count"], 0)
        self.assertEqual(empty["helper_avatar"], "")

    async def test_queries_are_bounded_owned_read_only(self):
        class Result:
            def all(inner):
                return [self.row()]

        session = AsyncMock()
        session.execute.return_value = Result()
        state = HelpHubState()
        jobs, helpers = await state._load_completed_history(session, "9")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(len(helpers), 1)
        calls = session.execute.call_args_list
        self.assertEqual(len(calls), 2)
        for call in calls:
            sql = str(call.args[0])
            self.assertEqual(call.args[1], {"sid": 9})
            self.assertIn("ct.poster_id = :sid", sql)
            self.assertIn(
                "mb.blocker_id = :sid AND mb.blocked_id = ct.helper_id", sql
            )
            self.assertIn(
                "mb.blocker_id = ct.helper_id AND mb.blocked_id = :sid", sql
            )
            self.assertIn("mt.poster_id = ct.poster_id", sql)
            self.assertIn("hp.helper_rating_avg", sql)
            self.assertNotIn("email", sql)
            for forbidden in ("INSERT", "UPDATE", "DELETE", "ALTER"):
                self.assertNotIn(forbidden, sql)
        self.assertIn("LIMIT 60", str(calls[0].args[0]))
        latest = str(calls[1].args[0])
        self.assertIn("DISTINCT ON (ct.helper_id)", latest)
        self.assertIn(
            "ORDER BY ct.helper_id, ct.completed_at DESC NULLS LAST, ct.id DESC",
            latest,
        )
        self.assertIn("COUNT(*) OVER (PARTITION BY ct.helper_id)", latest)
        self.assertNotIn("LIMIT", latest)

    def test_reset_and_locked_population(self):
        source = inspect.getsource(HelpHubState)
        load = source[
            source.index("async def load_help_hub") : source.index(
                "async def _load_help_hub_data"
            )
        ]
        self.assertEqual(load.count("self.completed_jobs = []"), 2)
        self.assertEqual(load.count("self.past_helpers = []"), 2)
        self.assertIn("self.completed_jobs = completed_jobs", source)
        self.assertIn("self.past_helpers = past_helpers", source)
        self.assertIn("subscriber_id != sid", source)

    def test_rendered_requests_excludes_duplicate_history(self):
        component = panel.help_hub_panel()
        rendered = str(component.render())
        for duplicate in ("Completed jobs", "Past helpers"):
            self.assertNotIn(duplicate, rendered)
        for history_var in ("completed_jobs", "past_helpers"):
            self.assertNotIn(history_var, rendered)
        for remaining in (
            "Ask for Help",
            "Your help summary",
            "Requests you have already posted",
            "Get ready to help others",
            "People ready to help you",
            "Join many helping hands",
            "Time to manage many hands",
            "Get notified with matching help requests",
            "Help requests you bookmarked in map or list view.",
        ):
            self.assertIn(remaining, rendered)
        self.assertEqual(len(component.children), 9)

    def test_remaining_section_order_and_loaders(self):
        names = (
            "post_help_section",
            "help_summary_row",
            "recent_requests_section",
            "upcoming_help_section",
            "upcoming_helpees_section",
            "others_events_section",
            "hosted_events_section",
            "saved_searches_section",
            "saved_requests_section",
        )
        with ExitStack() as stack:
            for name in names:
                stack.enter_context(
                    patch.object(panel, name, return_value=rx.el.section(name))
                )
            component = panel.help_hub_panel()
        self.assertEqual(
            [str(child.children[0]) for child in component.children],
            [str(rx.el.section(name).children[0]) for name in names],
        )
        mount = str(component.event_triggers["on_mount"])
        for loader in (
            "load_help_hub",
            "load_recent",
            "load_alerts",
            "load_bookmarks",
            "load_my_events",
        ):
            self.assertIn(loader, mount)

    def test_spacing_is_responsive_and_requests_only(self):
        classes = str(panel.help_hub_panel().class_name)
        for token in (
            "gah-requests-panel",
            "flex-col",
            "w-full",
            "min-w-0",
            "gap-8",
            "sm:gap-10",
            "[&>section>div:first-child:has(>h3)]:mb-4",
            "sm:[&>section>div:first-child:has(>h3)]:mb-5",
            "[&>section>div:first-child>p]:mt-1.5",
            "sm:[&>section>div:first-child>p]:mt-2",
            "[&>section>p:first-of-type]:mt-1.5",
            "sm:[&>section>p:first-of-type]:mt-2",
            "[&>section>button_p]:mt-1.5",
        ):
            self.assertIn(token, classes)
        from app.components.request_heading import request_heading

        shared = str(request_heading("Heading", rx.Var.create(1), "Subtitle"))
        self.assertIn("mt-0", shared)
        self.assertNotIn("gah-requests-panel", shared)
        for factory in (
            panel.recent_requests_section,
            panel.upcoming_help_section,
            panel.upcoming_helpees_section,
        ):
            self.assertIn("gah-edge-stack", str(factory()))
            self.assertIn("gap-0", str(factory()))

    def test_remaining_requests_actions_are_wired(self):
        from reflex.event import EventChain

        wired_actions = set()
        pending = [panel.help_hub_panel()]
        while pending:
            component = pending.pop()
            for chain in component.event_triggers.values():
                if isinstance(chain, EventChain):
                    wired_actions.update(
                        event.handler.fn.__name__ for event in chain.events
                    )
            pending.extend(
                child
                for child in component.children
                if isinstance(child, rx.Component)
            )
        for action in (
            "toggle_form",
            "create_help_request",
            "focus_thread",
            "apply_alert",
            "toggle_alert",
            "delete_alert",
            "open_on_map",
            "toggle_bookmark",
            "save_note",
            "confirm_request",
            "decline_request",
        ):
            with self.subTest(action=action):
                self.assertIn(action, wired_actions)
        self.assertIn(
            "owner_delete_footer(post)",
            inspect.getsource(panel.own_request_body),
        )

    def test_rendering_does_not_clear_existing_history(self):
        state = HelpHubState()
        state.completed_jobs = [HelpHubState._completed_job(self.row())]
        state.past_helpers = [HelpHubState._past_helper(self.row())]
        jobs = list(state.completed_jobs)
        helpers = list(state.past_helpers)
        self.assertTrue(panel.help_hub_panel().render())
        self.assertEqual(state.completed_jobs, jobs)
        self.assertEqual(state.past_helpers, helpers)
        source = inspect.getsource(HelpHubState._load_help_hub_data)
        self.assertIn("await self._load_completed_history(", source)
        self.assertIn("self.completed_jobs = completed_jobs", source)
        self.assertIn("self.past_helpers = past_helpers", source)


if __name__ == "__main__":
    unittest.main()
