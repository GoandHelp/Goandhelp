import reflex as rx

import datetime
import inspect
import unittest
from test_utils import run_event
from app.states.help_hub_state import (
    HelpHubState,
    _date_ceiling,
    _schedule_parts,
)
from app.states.saved_search_state import _chips, SavedSearchState
from app.components import (
    help_hub_panel as hub,
    disclosure,
    event_cards,
    saved_items,
    feedback,
    help_post_panel,
)
from app.components.request_heading import request_heading
from app.app import theme_overrides


class RequestsCalendarTests(unittest.IsolatedAsyncioTestCase):
    async def test_open_navigation_selection_and_close(self):
        today = datetime.date.today()
        state = HelpHubState(
            date_input="",
            help_dates=[],
            calendar_open=False,
            calendar_month=today.replace(day=1).isoformat(),
            date_min=today.isoformat(),
            date_max=_date_ceiling(today).isoformat(),
        )
        await run_event(state.toggle_calendar)
        state.calendar_month = today.replace(day=1).isoformat()
        self.assertTrue(state.calendar_open)
        first = state.calendar_month
        await run_event(state.change_calendar_month, -1)
        self.assertEqual(first, state.calendar_month)
        self.assertEqual(len(state.calendar_cells) % 7, 0)
        for _ in range(30):
            await run_event(state.change_calendar_month, 1)
        self.assertEqual(state.calendar_month[:7], state.date_max[:7])
        await run_event(state.select_calendar_day, state.date_max)
        self.assertEqual(state.date_input, state.date_max)
        self.assertFalse(state.calendar_open)
        await run_event(state.toggle_calendar)
        self.assertEqual(state.calendar_month[:7], state.date_max[:7])
        before = state.date_input
        await run_event(state.select_calendar_day, "invalid")
        self.assertEqual(before, state.date_input)
        disabled = [cell for cell in state.calendar_cells if cell["disabled"]]
        for cell in disabled:
            await run_event(state.select_calendar_day, cell["date"])
            self.assertEqual(before, state.date_input)
        await run_event(state.close_calendar)
        self.assertFalse(state.calendar_open)

    async def test_add_date_validation(self):
        state = HelpHubState()
        today = datetime.date.today()
        for value in (
            "",
            "invalid",
            (today - datetime.timedelta(days=1)).isoformat(),
            (_date_ceiling(today) + datetime.timedelta(days=1)).isoformat(),
        ):
            state.date_input = value
            await run_event(state.add_date)
            self.assertTrue(state.date_error)
            self.assertEqual(state.help_dates, [])
        for value in (today.isoformat(), _date_ceiling(today).isoformat()):
            state.date_input = value
            await run_event(state.add_date)
            self.assertIn(value, state.help_dates)
            self.assertEqual(state.date_input, "")
            state.date_input = value
            await run_event(state.add_date)
            self.assertIn("already", state.date_error)
        self.assertEqual(len(state.help_dates), 2)


class RequestsFollowupTests(unittest.TestCase):
    def test_schedule_and_heading(self):
        moment = datetime.datetime(2026, 9, 9, 9)
        self.assertEqual(
            _schedule_parts(moment, "", "", 60)[1], "Wednesday 9 Sept 2026"
        )
        self.assertIn("bg-white", str(disclosure.disclosure_arrow()))
        heading = str(
            request_heading("Title", rx.Var.create(2), "Subtitle", "calendar")
        )
        for token in (
            "text-center",
            "text-xl sm:text-2xl",
            "mt-2",
            "Subtitle",
            "text-[#e08b12]",
        ):
            self.assertIn(token, heading)
        self.assertNotIn("absolute right", heading)
        self.assertNotIn("Icon", heading)
        self.assertNotIn("rounded-full", heading)
        counted_title = request_heading("Title", rx.Var.create(2)).children[0]
        self.assertEqual(counted_title.tag, "h3")
        self.assertIn("text-[#e08b12]", str(counted_title))
        for factory, phrase in (
            (hub.upcoming_help_section, "Get ready to help others"),
            (hub.upcoming_helpees_section, "People ready to help you"),
            (event_cards.others_events_section, "Join many helping hands"),
            (event_cards.hosted_events_section, "Time to manage many hands"),
            (hub.recent_requests_section, "Requests you have already posted"),
        ):
            self.assertIn(phrase, str(factory()))

    def test_saved_radius_and_copy(self):
        self.assertIn("Distance: 50 km", _chips([], "", "", [], "", 50))
        self.assertIn(
            'discovery.distance_km = clamp_distance_km(int(alert["radius_km"]))',
            inspect.getsource(SavedSearchState),
        )
        self.assertIn(
            "Get notified with matching help requests",
            str(saved_items.saved_searches_section()),
        )
        bookmarks = str(saved_items.saved_requests_section())
        self.assertIn("Bookmarked help requests", bookmarks)
        self.assertIn(
            "Help requests you bookmarked in map or list view.", bookmarks
        )

    def test_controls_and_focus(self):
        shell = inspect.getsource(hub.section_shell)
        self.assertIn("HelpHubState.form_open", shell)
        self.assertIn("mx-auto w-full", shell)
        self.assertIn("w-[calc(100%-30px)]", shell)
        metrics = str(hub.counts_summary())
        for token in (
            "grid-cols-3",
            "rounded-xl bg-white",
            "text-[#b86e08]",
            "flex w-full min-w-0",
            "justify-center text-center",
            "shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
            " Open",
            "Requested",
            "Upcoming",
        ):
            self.assertIn(token, metrics)
        self.assertNotIn("Icon", metrics)
        self.assertNotIn("hidden sm:inline-flex", metrics)
        self.assertNotIn("border-[3px]", inspect.getsource(hub.mode_button))
        location = inspect.getsource(hub.job_location_section)
        self.assertNotIn('rx.icon("map-pin"', location)
        self.assertIn("text-center", location)
        upload = inspect.getsource(help_post_panel.photo_upload_section)
        for token in (
            "bg-[#fff7e8]",
            "text-[#e08b12]",
            "border-dashed border-[#fba922]",
            "max_files=5",
            "HelpPostState.handle_upload",
        ):
            self.assertIn(token, upload)
        self.assertIn(
            "text-[#e08b12]", inspect.getsource(hub.required_language_row)
        )
        self.assertIn("gah-post-request", str(hub.post_help_form()))
        self.assertNotIn("2362ef", feedback.INPUT_CLASS)
        self.assertIn("focus:ring-0", feedback.SELECT_CLASS)
        css = str(theme_overrides())
        self.assertIn("border: 1px solid #fba922 !important", css)
        self.assertIn("button.gah-post-request", css)

    def test_calendar_and_requests_branches_compile(self):
        source = inspect.getsource(hub.specific_help_day_field)
        self.assertNotIn('type="date"', source)
        self.assertIn('aria_controls="help-day-calendar"', source)
        self.assertIn("aria_expanded=HelpHubState.calendar_open", source)
        for factory in (
            hub.inline_help_calendar,
            hub.specific_help_day_field,
            hub.post_help_form,
            hub.post_help_section,
            hub.help_hub_panel,
            hub.section_skeleton,
        ):
            component = factory()
            self.assertTrue(component.render())
            self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
