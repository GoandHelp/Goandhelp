import reflex as rx

import datetime
import inspect
import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.components import (
    event_cards,
    location_selection,
    onboarding,
    profile_tabs,
)
from app.location_privacy import (
    _distance_km,
    post_guest_approximate,
    post_member_approximate,
    profile_approximate,
)
from app.states.auth_state import AuthState
from app.states.event_state import EventState
from app.states.help_hub_state import HelpHubState
from app.states.help_post_state import HelpPostState
from app.states.map_picker_state import MapPickerState
from app.states.profile_state import ProfileState


class LoadHarness(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class EventLocationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.state = EventState(_reflex_internal_init=True)
        self.profile = SimpleNamespace(
            location_mode="hidden", show_location=False
        )
        self.auth = SimpleNamespace(subscriber_id="42")
        self.getter = self.enterContext(
            patch.object(
                EventState,
                "get_state",
                AsyncMock(
                    side_effect=lambda cls: (
                        self.auth if cls is AuthState else self.profile
                    )
                ),
            )
        )

    async def test_browser_fix_is_private_and_never_changes_profile(self):
        with patch("app.states.event_state.rx.asession") as database:
            await EventState.toggle_events_location.fn(self.state)
            self.assertTrue(self.state.events_geo_busy)
            self.assertGreater(self.state.events_geo_token, 0)
            result = await EventState.events_position_found.fn(
                self.state, 41.2, -8.6, 10
            )
            self.assertEqual(result, EventState.load_events)
            self.assertEqual(
                self.state._filter_point(False, 10, 20), (41.2, -8.6)
            )
            self.assertEqual(self.state.events_location_source, "session")
            self.assertEqual(self.state.event_markers, [])
            self.assertEqual(self.state.events, [])
            self.assertFalse(self.profile.show_location)
            self.assertEqual(self.profile.location_mode, "hidden")
            database.assert_not_called()
            await EventState.toggle_events_location.fn(self.state)
            self.assertFalse(self.state._events_has_point)
            self.assertIsNone(self.state._filter_point(False, 10, 20))

    async def test_map_visibility_sync_on_off_and_events_off_are_one_way(self):
        self.profile.location_mode = "approximate"
        self.profile.show_location = True
        self.assertEqual(
            await EventState.sync_map_location.fn(self.state),
            EventState.load_events,
        )
        self.assertEqual(self.state._filter_point(True, 41, -8), (41, -8))
        await EventState.toggle_events_location.fn(self.state)
        self.assertTrue(self.profile.show_location)
        self.assertTrue(self.state.events_location_disabled)
        self.assertIsNone(self.state._filter_point(True, 41, -8))
        self.profile.show_location = False
        await EventState.sync_map_location.fn(self.state)
        self.assertFalse(self.state.events_location_disabled)
        self.assertIsNone(self.state._filter_point(False, 41, -8))
        self.profile.show_location = True
        await EventState.sync_map_location.fn(self.state)
        self.assertEqual(self.state.events_location_source, "profile")
        self.assertFalse(self.state.events_geo_busy)

    async def test_invalid_fixes_denial_and_late_callbacks_are_safe(self):
        for lat, lon in (
            (float("nan"), 0),
            (0, float("inf")),
            (91, 0),
            (0, -181),
        ):
            await EventState.toggle_events_location.fn(self.state)
            await EventState.events_position_found.fn(self.state, lat, lon, 0)
            self.assertFalse(self.state._events_has_point)
            self.assertTrue(self.state.events_location_error)
        await EventState.toggle_events_location.fn(self.state)
        EventState.events_position_failed.fn(self.state, "Permission declined")
        self.assertEqual(
            self.state.events_location_error, "Permission declined"
        )
        await EventState.events_position_found.fn(self.state, 40, 20, 0)
        self.assertFalse(self.state._events_has_point)
        await EventState.toggle_events_location.fn(self.state)
        await EventState.toggle_events_location.fn(self.state)
        await EventState.events_position_found.fn(self.state, 40, 20, 0)
        self.assertFalse(self.state._events_has_point)

    async def test_session_change_discards_fix_and_unsolicited_fix_is_ignored(
        self,
    ):
        await EventState.events_position_found.fn(self.state, 40, 20, 0)
        self.assertFalse(self.state._events_has_point)
        await EventState.toggle_events_location.fn(self.state)
        self.auth.subscriber_id = "43"
        await EventState.events_position_found.fn(self.state, 40, 20, 0)
        self.assertFalse(self.state._events_has_point)
        self.assertFalse(self.state.events_location_enabled)

    async def test_load_filters_with_explicit_source_and_never_publishes_browser_fix(
        self,
    ):
        now = datetime.datetime.now(datetime.UTC)
        row = (
            7,
            "gathering",
            "Neighbour gathering",
            "[gah-event:v1:gathering]\nBring a bowl",
            "Market square",
            "Town",
            "Spain",
            now,
            None,
            10,
            0,
            99,
            "Neighbour",
            "member-99",
            "",
            True,
            "",
            0,
            41.21,
            -8.61,
        )
        for mode, visible, session_fix, expect_card in (
            ("hidden", False, False, False),
            ("approximate", False, False, False),
            ("hidden", True, False, False),
            ("approximate", True, False, True),
            ("hidden", False, True, True),
        ):
            with self.subTest(
                mode=mode, visible=visible, session_fix=session_fix
            ):
                state = LoadHarness(
                    _events_owner="42",
                    _events_point=(41.2, -8.6),
                    _events_has_point=session_fix,
                    events_location_enabled=session_fix,
                    events_location_disabled=False,
                    events_location_source="none",
                    events_location_revision=1,
                    event_distance_km=100.0,
                    selected_date="",
                    selected_dates=[],
                    calendar_mode="single",
                    range_start="",
                    range_end="",
                    calendar_timezone="UTC",
                    selected_event=[],
                    events=[],
                    event_markers=[],
                    is_loading=False,
                    has_loaded=False,
                    error="",
                )
                state.get_state = AsyncMock(
                    side_effect=lambda cls: (
                        self.auth
                        if cls is AuthState
                        else SimpleNamespace(
                            location_mode=mode, show_location=visible
                        )
                    )
                )
                state._check_events_owner = lambda sid: None
                state._query_bounds = lambda stamp: (
                    stamp,
                    stamp + datetime.timedelta(days=30),
                )
                state._valid_filter_point = EventState._valid_filter_point
                state._filter_point = MethodType(
                    EventState._filter_point, state
                )
                session = MagicMock()
                session.__aenter__ = AsyncMock(return_value=session)
                session.__aexit__ = AsyncMock(return_value=False)
                profile_result, rows_result = MagicMock(), MagicMock()
                profile_result.first.return_value = (
                    ("Portugal", 41.2, -8.6)
                    if mode == "approximate" and visible
                    else ("Portugal", None, None)
                )
                rows_result.all.return_value = [row]
                session.execute = AsyncMock(
                    side_effect=[profile_result, rows_result]
                )
                session.commit = AsyncMock()
                with patch(
                    "app.states.event_state.rx.asession", return_value=session
                ):
                    await EventState.load_events.fn(state)
                self.assertEqual(len(state.events), int(expect_card))
                self.assertFalse(state.is_loading)
                self.assertTrue(state.has_loaded)
                session.commit.assert_not_awaited()
                for marker in state.event_markers:
                    self.assertEqual(marker["kind"], "event")
                    self.assertEqual(marker["icon"], "star")
                    self.assertEqual(marker["color"], "#dca126")
                    self.assertEqual(marker["ink"], "#ffffff")
                    self.assertEqual(
                        (marker["lat"], marker["lng"]), (41.21, -8.61)
                    )
                    self.assertNotEqual(
                        (marker["lat"], marker["lng"]), state._events_point
                    )
                for card in state.events:
                    self.assertNotIn("latitude", card)
                    self.assertNotIn("longitude", card)
                for call in session.execute.call_args_list:
                    self.assertNotIn("UPDATE", str(call.args[0]))
                    self.assertNotIn("INSERT", str(call.args[0]))

    def test_saved_hidden_coordinates_are_never_a_filter_source(self):
        self.assertIsNone(self.state._filter_point(False, 41, -8))
        self.assertEqual(self.state.events_location_source, "none")
        self.assertIsNone(self.state._filter_point(True, float("nan"), -8))
        self.assertEqual(self.state._filter_point(True, 0, 0), (0, 0))
        source = inspect.getsource(EventState.load_events.fn)
        self.assertIn(
            'profile.location_mode == "approximate" and profile.show_location',
            source,
        )
        self.assertIn(
            "CASE WHEN location_mode = 'approximate' AND show_location = TRUE THEN latitude END",
            source,
        )
        self.assertIn(
            "location_revision != self.events_location_revision", source
        )
        self.assertIn("COALESCE(e.capacity, 0)", source)
        self.assertIn("skillkind_member_block", source)
        self.assertIn("selected_dates", source)
        self.assertIn("same_country", source)


class PrivacyPresentationTests(unittest.TestCase):
    def test_profile_editor_removed_but_map_toggle_and_account_country_remain(
        self,
    ):
        for obsolete in (
            "location_disclosure_section",
            "location_details_form",
            "area_tab",
            "coordinates_field",
        ):
            self.assertFalse(hasattr(profile_tabs, obsolete))
        self.assertNotIn("My location", str(profile_tabs.profile_screen()))
        self.assertIn(
            '("area", profile_screen())',
            inspect.getsource(profile_tabs.screen_content),
        )
        self.assertEqual(ProfileState._normalize_tab("area"), "profile")
        self.assertIn(
            'name="home_country"', inspect.getsource(profile_tabs.details_tab)
        )
        self.assertIn(
            "home_country = :home_country",
            inspect.getsource(ProfileState.save_details.fn),
        )
        self.assertIn(
            'location_tap("approximate", "Approx",',
            inspect.getsource(location_selection.location_selection),
        )
        self.assertIn(
            'location_choice("Approx", "approximate")',
            inspect.getsource(onboarding.location_screen),
        )
        self.assertTrue(location_selection.location_selection().render())
        self.assertTrue(event_cards.events_location_control().render())

    def test_map_changes_reload_events_without_reverse_visibility_writes(self):
        for handler in (
            ProfileState.set_location_mode,
            ProfileState.save_live_position,
        ):
            self.assertIn(
                "yield EventState.sync_map_location",
                inspect.getsource(handler.fn),
            )
        for handler in (
            EventState.toggle_events_location,
            EventState.events_position_found,
            EventState.events_position_failed,
        ):
            source = inspect.getsource(handler.fn)
            self.assertNotIn("asession", source)
            self.assertNotIn("profile.show_location =", source)
            self.assertNotRegex(source, r"profile\.location_mode\s*=(?!=)")
        self.assertNotIn("location_selection", inspect.getsource(event_cards))

    def test_help_request_points_stay_independent_and_separately_salted(self):
        source = inspect.getsource(HelpHubState.create_help_request.fn)
        self.assertIn("await self.get_state(MapPickerState)", source)
        for forbidden in (
            "show_location = TRUE",
            "profile.show_location =",
            "profile.location_mode =",
            "set_location_mode(",
        ):
            self.assertNotIn(forbidden, source)
        edit_source = inspect.getsource(HelpPostState.save_edit.fn)
        self.assertNotIn("show_location", edit_source)
        self.assertIn("await self.get_state(MapPickerState)", edit_source)
        picker_source = inspect.getsource(MapPickerState)
        self.assertNotIn("ProfileState", picker_source)
        with patch("app.location_privacy.is_land", return_value=True):
            member = post_member_approximate(42, 41.2, -8.6)
            guest = post_guest_approximate(42, 41.2, -8.6)
            profile = profile_approximate(42, 41.2, -8.6)
            self.assertEqual(member, post_member_approximate(42, 41.2, -8.6))
            self.assertNotEqual(member, guest)
            self.assertNotEqual(member, profile)
            for point in (member, guest):
                self.assertIsNotNone(point)
                self.assertTrue(0.5 <= _distance_km(41.2, -8.6, *point) <= 1.0)


if __name__ == "__main__":
    unittest.main()
