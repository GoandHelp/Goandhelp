import reflex as rx

import ast
import datetime
import inspect
import unittest
from test_utils import run_event
from app.components import (
    membership_info,
    saved_items,
    help_hub_panel,
    community_panel,
    event_cards,
    reviews_section,
)
from app.components.event_calendar import event_date_calendar
from app.components.transient_surfaces import transient_surface_listeners
from app.components.profile_tabs import profile_tabs
from app.states.community_state import CommunityState
from app.states.event_state import EventState
from app.states.saved_search_state import SavedSearchState, _chips


class EventCalendarTests(unittest.IsolatedAsyncioTestCase):
    async def test_navigation_selection_clear_and_distance(self):
        state = EventState()
        self.assertEqual(state.event_distance_km, 100)
        self.assertEqual(state.event_distance_label, "100 km")
        await run_event(state.set_event_distance_km, 1000)
        self.assertEqual(state.event_distance_label, "1000 km")
        await run_event(state.set_event_distance_km, 2000)
        self.assertEqual(state.event_distance_km, 1000)
        await run_event(state.set_event_distance_km, 0)
        self.assertEqual(state.event_distance_km, 1)
        await run_event(state.toggle_calendar)
        self.assertTrue(state.calendar_open)
        first = state.calendar_month
        await run_event(state.change_calendar_month, -1)
        self.assertEqual(state.calendar_month, first)
        self.assertEqual(len(state.calendar_cells) % 7, 0)
        for _ in range(30):
            await run_event(state.change_calendar_month, 1)
        self.assertFalse(state.calendar_can_next)
        low, high = state._calendar_limits()
        await run_event(state.select_calendar_day, high.isoformat())
        self.assertEqual(state.selected_date, high.isoformat())
        self.assertEqual(state.selected_dates, [high.isoformat()])
        self.assertTrue(state.has_date_filter)
        self.assertTrue(state.calendar_open)
        second = (high - datetime.timedelta(days=1)).isoformat()
        await run_event(state.select_calendar_day, second)
        self.assertEqual(
            state.selected_dates, sorted([high.isoformat(), second])
        )
        self.assertTrue(state.calendar_open)
        await run_event(state.toggle_calendar)
        self.assertEqual(state.calendar_month[:7], high.isoformat()[:7])
        for day in (
            low - datetime.timedelta(days=1),
            high + datetime.timedelta(days=1),
        ):
            await run_event(state.select_calendar_day, day.isoformat())
            self.assertEqual(state.selected_date, high.isoformat())
        await run_event(state.select_calendar_day, high.isoformat())
        self.assertEqual(state.selected_dates, [second])
        self.assertTrue(state.calendar_open)
        await run_event(state.select_calendar_day, second)
        self.assertEqual(state.selected_dates, [])
        self.assertFalse(state.has_date_filter)
        self.assertTrue(state.calendar_open)
        await run_event(state.select_calendar_day, low.isoformat())
        await run_event(state.clear_date_filter)
        self.assertEqual(state.selected_date, "")
        self.assertEqual(state.selected_dates, [])
        self.assertFalse(state.has_date_filter)
        self.assertFalse(state.calendar_open)

    async def test_transient_close_preserves_composer(self):
        state = CommunityState()
        state.subject_list_open = True
        state.composer_open = True
        state.body_draft = "Keep my draft"
        await run_event(state.close_subject_list)
        self.assertFalse(state.subject_list_open)
        self.assertTrue(state.composer_open)
        self.assertEqual(state.body_draft, "Keep my draft")
        event = EventState()
        event.calendar_open = True
        event.composer_open = True
        await run_event(event.close_calendar)
        self.assertFalse(event.calendar_open)
        self.assertTrue(event.composer_open)

    def test_query_bounds_month_end_and_local_dst(self):
        state = EventState(calendar_timezone="UTC")
        now = datetime.datetime(2028, 1, 31, 12, tzinfo=datetime.UTC)
        low, high = state._query_bounds(now)
        self.assertEqual(low, now)
        self.assertEqual(
            high, datetime.datetime(2028, 2, 29, 12, tzinfo=datetime.UTC)
        )
        state.calendar_timezone = "America/New_York"
        state.calendar_mode = "single"
        state.selected_dates = ["2028-03-12"]
        low, high = state._query_bounds(now)
        self.assertEqual(low.hour, 5)
        self.assertEqual(high.hour, 4)
        self.assertEqual(high - low, datetime.timedelta(hours=23))
        source = inspect.getsource(EventState)
        for token in (
            "e.starts_at >= :window_start",
            "e.starts_at < :window_end",
            "CAST(:range_start AS date)",
            "CAST(:range_end AS date)",
            '"window_start": lower',
            '"window_end": upper',
            "skillkind_member_block",
            "COALESCE(e.confirmed_count, 0) < e.capacity",
            "LIMIT 60",
        ):
            self.assertIn(token, source)


class CurrentCommunityComponentTests(unittest.TestCase):
    def test_membership_and_saved_radius(self):
        source = inspect.getsource(membership_info.comparison_column)
        self.assertLess(source.index("rx.icon(icon"), source.index("rx.el.h4"))
        self.assertLess(source.index("rx.el.h4"), source.index('"Your tier"'))
        tree = ast.parse(source)
        tier_nodes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == "Your tier"
        ]
        price_paragraphs = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.el.p"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "price"
        ]
        self.assertEqual(len(tier_nodes), 1)
        self.assertEqual(len(price_paragraphs), 1)
        self.assertLess(
            (tier_nodes[0].lineno, tier_nodes[0].col_offset),
            (price_paragraphs[0].lineno, price_paragraphs[0].col_offset),
        )
        self.assertIn("Distance: 50 km", _chips([], "", "", [], "", 50))
        self.assertNotIn("Distance: 0 km", _chips([], "", "", [], "", 0))
        chip = str(saved_items.alert_chip(rx.Var.create("Distance: 50 km")))
        for token in ("border-[#e08b12]", "bg-[#fff7e8]", "text-black"):
            self.assertIn(token, chip)
        self.assertIn(
            'discovery.distance_km = clamp_distance_km(int(alert["radius_km"]))',
            inspect.getsource(SavedSearchState),
        )
        for factory in (
            saved_items.saved_requests_section,
            saved_items.saved_searches_section,
        ):
            self.assertIn("text-center text-sm font-medium", str(factory()))

    def test_request_controls(self):
        metrics = str(help_hub_panel.counts_summary())
        for token in (
            "grid-cols-3",
            "flex w-full min-w-0",
            "justify-center text-center",
            "shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
            "rounded-xl bg-white",
            "text-[#b86e08]",
        ):
            self.assertIn(token, metrics)
        self.assertNotIn("Still open", metrics)
        self.assertNotIn("hidden sm:inline-flex", metrics)
        self.assertNotIn("Icon", metrics)
        for factory in (
            help_hub_panel.reward_checkbox,
            help_hub_panel.job_location_section,
        ):
            source = inspect.getsource(factory)
            for token in ("bg-[#fff7e8]", "border-[#fba922]", "text-[#e08b12]"):
                self.assertIn(token, source)
        language_tree = ast.parse(
            inspect.getsource(help_hub_panel.required_language_row)
        )
        button = language_tree.body[0].body[0].value
        language_branch = button.args[0]
        self.assertEqual(ast.unparse(language_branch.func), "rx.cond")
        self.assertEqual(
            ast.dump(language_branch.args[0]),
            ast.dump(ast.parse('item["code"] == ""', mode="eval").body),
        )
        globe_literals = [
            node
            for node in ast.walk(language_tree)
            if isinstance(node, ast.Constant) and node.value == "globe"
        ]
        self.assertEqual(len(globe_literals), 1)
        any_language = language_branch.args[1]
        self.assertEqual(ast.unparse(any_language.func), "rx.icon")
        self.assertEqual(ast.literal_eval(any_language.args[0]), "globe")
        self.assertIn(globe_literals[0], list(ast.walk(any_language)))
        flag = ast.dump(ast.parse('item["flag"]', mode="eval").body)
        self.assertNotIn(flag, ast.dump(any_language))
        self.assertIn(flag, ast.dump(language_branch.args[2]))
        for child in button.args[1:]:
            self.assertNotIn(flag, ast.dump(child))
            self.assertNotIn(globe_literals[0], list(ast.walk(child)))
        self.assertIn(
            "text-[#e08b12]", str(help_hub_panel.specific_help_day_field())
        )
        self.assertIn(
            "I.e. Home-made Olive Oil and a ride to Milan",
            str(help_hub_panel.conditional_reward_fields()),
        )
        self.assertIn(
            "gah-orange-control", inspect.getsource(help_hub_panel.mode_button)
        )

    def test_community_headings_and_outside_close(self):
        self.assertIn("gah-orange-control", community_panel.FOLDER_TAB_ACTIVE)
        self.assertIn(
            "border border-[#fba922]", community_panel.FOLDER_TAB_ACTIVE
        )
        for factory in (
            community_panel.community_section,
            event_cards.planner_control,
        ):
            self.assertIn("border border-[#fba922]", inspect.getsource(factory))
        forum_heading = str(community_panel.topic_feed().children[0])
        self.assertIn("text-xl sm:text-2xl", forum_heading)
        self.assertNotIn("MessagesSquare", forum_heading)
        listener = inspect.getsource(transient_surface_listeners)
        for token in (
            "relatedTarget",
            "wrapper.contains(target)",
            "pointerdown",
            "focusout",
            "gah-member-section",
            "scroll",
        ):
            self.assertIn(token, listener)
        self.assertIn(
            "CommunityState.close_subject_list",
            inspect.getsource(community_panel.subject_dropdown),
        )
        self.assertIn(
            "EventState.close_calendar", inspect.getsource(event_date_calendar)
        )
        feed = inspect.getsource(event_cards.events_feed)
        self.assertIn('"Upcoming event"', feed)
        self.assertIn('"Upcoming events"', feed)
        self.assertNotIn("event_count_label", feed)
        self.assertLess(
            feed.index("event_date_calendar()"),
            feed.index("event_distance_control()"),
        )
        distance = inspect.getsource(event_cards.event_distance_control)
        self.assertNotIn('"radar"', distance)
        for token in (
            "gah-distance-range",
            "--distance-progress",
            'max="1000"',
            'min="1"',
        ):
            self.assertIn(token, distance)
        reviews = inspect.getsource(reviews_section.your_reviews_header)
        self.assertIn('"Review received"', reviews)
        self.assertIn('"Reviews received"', reviews)
        self.assertIn("ProfileState.combined_star_states", reviews)
        self.assertIn("ProfileState.combined_rating_avg", reviews)
        received = inspect.getsource(reviews_section.received_reviews_section)
        self.assertIn('"My reviews"', received)
        self.assertNotIn('"Reviews about my work"', received)

    def test_component_branches(self):
        for factory in (
            profile_tabs,
            membership_info.membership_information_section,
            help_hub_panel.help_hub_panel,
            community_panel.community_panel,
            community_panel.community_section,
            event_cards.events_section,
            event_date_calendar,
            reviews_section.community_reviews_section,
        ):
            with self.subTest(factory=factory.__name__):
                component = factory()
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
