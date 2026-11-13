import reflex as rx

import datetime
import inspect
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image

from app.components import event_cards, member_map, openfreemap
from app.models import CommunityEvent, EVENT_REQUEST_CATEGORIES
from app.states.auth_state import AuthState
from app.states.map_picker_state import MapPickerState
from app.states.event_state import (
    EventState,
    _CARD_SELECT,
    _card,
    _helper_capacity,
    _safe_event_photos,
)


class Harness(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


def planner_state() -> Harness:
    return Harness(
        get_state=AsyncMock(
            side_effect=lambda cls: (
                SimpleNamespace(subscriber_id="42", is_signed_in=True)
                if cls is AuthState
                else MapPickerState(_reflex_internal_init=True)
            )
        ),
        pending_photo_paths=[],
        photo_busy=False,
        photo_error="",
        is_saving=False,
        composer_open=True,
        event_type_draft=EVENT_REQUEST_CATEGORIES[0],
        reward_choice="meal",
        reward_currency="USD",
        budget_quote_allowed=False,
        error="",
        success="",
        _planner_revision=1,
        _photo_sources=[],
    )


def form_data(capacity: str = "1") -> dict[str, str]:
    return {
        "title": "Help restore the community garden",
        "details": "Bring gloves. Tools and lunch provided.",
        "event_type": EVENT_REQUEST_CATEGORIES[0],
        "city": "Porto",
        "country": "Portugal",
        "place_name": "Near the public garden",
        "capacity": capacity,
        "starts_at": (
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=2)
        ).isoformat(),
        "reward_details": "Lunch and refreshments",
    }


def session_mock() -> MagicMock:
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    inserted, point = MagicMock(), MagicMock()
    inserted.first.return_value = (7,)
    point.first.return_value = (41.2, -8.6)
    session.execute = AsyncMock(side_effect=[inserted, point, MagicMock()])
    session.commit = AsyncMock()
    return session


class EventPlannerTests(unittest.IsolatedAsyncioTestCase):
    def test_dropdown_bounds_and_server_validation(self):
        state = EventState(_reflex_internal_init=True)
        self.assertEqual(state.helper_options, list(range(1, 101)))
        for number in range(1, 101):
            self.assertEqual(_helper_capacity(str(number)), number)
        for value in ("0", "101", "-1", "1.5", "1e2", "", "NaN", "١"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _helper_capacity(value)
        source = inspect.getsource(event_cards.event_composer)
        self.assertLess(
            source.index('"Job category"'), source.index('"Number of helpers"')
        )
        self.assertLess(
            source.index('"Number of helpers"'),
            source.index("event_photo_upload()"),
        )
        self.assertLess(
            source.index("event_photo_upload()"),
            source.index('"Approximate place"'),
        )
        self.assertIn('default_value="1"', source)
        self.assertIn('name="capacity"', source)
        self.assertNotIn('type="number"', source)

    async def test_free_member_opens_planner_without_membership_lookup(self):
        state = EventState(_reflex_internal_init=True)
        auth = SimpleNamespace(subscriber_id="42", is_signed_in=True)
        picker = MapPickerState(_reflex_internal_init=True)
        with patch.object(
            EventState,
            "get_state",
            AsyncMock(
                side_effect=lambda cls: auth if cls is AuthState else picker
            ),
        ) as getter:
            await EventState.toggle_composer.fn(state)
        getter.assert_any_await(AuthState)
        getter.assert_any_await(MapPickerState)
        self.assertEqual(picker.open_key, "event-planner")
        self.assertTrue(state.composer_open)
        source = inspect.getsource(event_cards.planner_control)
        self.assertIn('"Plan an event"', source)
        self.assertNotIn("MembershipState", source)
        self.assertNotIn("paywall", source)

    async def test_free_member_publishes_real_row_and_refreshes_both_lists(
        self,
    ):
        state, session = planner_state(), session_mock()
        photo = f"event_42_{'a' * 32}.webp"
        state.pending_photo_paths = [photo]
        with (
            patch("app.states.event_state.rx.asession", return_value=session),
            patch(
                "app.states.event_state.approximate_point",
                return_value=(41.25, -8.65),
            ),
        ):
            events = [
                event
                async for event in EventState.create_event.fn(
                    state, form_data("100")
                )
            ]
        self.assertFalse(state.is_saving)
        self.assertFalse(state.composer_open)
        self.assertEqual(state.pending_photo_paths, [])
        session.commit.assert_awaited_once()
        sql, params = session.execute.call_args_list[0].args
        self.assertIn("INSERT INTO skillkind_community_event", str(sql))
        self.assertEqual(params["capacity"], 100)
        self.assertEqual(json.loads(params["photos"]), [photo])
        self.assertEqual(params["reward"], "A meal: Lunch and refreshments")
        self.assertEqual(
            events[-2:], [EventState.load_events, EventState.load_my_events]
        )
        location_params = session.execute.call_args_list[2].args[1]
        self.assertEqual(
            (location_params["lat"], location_params["lon"]), (41.25, -8.65)
        )
        state.get_state.assert_any_await(AuthState)
        state.get_state.assert_any_await(MapPickerState)

    async def test_invalid_helpers_do_not_write_or_close(self):
        for capacity in ("0", "101", "-1", "", "1.5"):
            state = planner_state()
            with patch("app.states.event_state.rx.asession") as database:
                events = [
                    event
                    async for event in EventState.create_event.fn(
                        state, form_data(capacity)
                    )
                ]
            self.assertIn("between 1 and 100", state.error)
            self.assertTrue(state.composer_open)
            self.assertFalse(state.is_saving)
            database.assert_not_called()

    async def test_database_failure_retains_form_and_photos(self):
        state, session = planner_state(), session_mock()
        state.pending_photo_paths = [f"event_42_{'b' * 32}.webp"]
        session.execute.side_effect = RuntimeError("Temporary failure")
        with patch("app.states.event_state.rx.asession", return_value=session):
            events = [
                event
                async for event in EventState.create_event.fn(
                    state, form_data()
                )
            ]
        self.assertTrue(state.composer_open)
        self.assertFalse(state.is_saving)
        self.assertTrue(state.pending_photo_paths)
        self.assertIn("try again", state.error)
        session.commit.assert_not_awaited()

    async def test_photo_processing_saves_webp_and_removes_source(self):
        state = planner_state()
        state.photo_busy = True
        buffer = BytesIO()
        Image.new("RGB", (120, 80), "orange").save(buffer, format="PNG")
        with (
            tempfile.TemporaryDirectory() as folder,
            patch(
                "app.states.event_state.rx.get_upload_dir",
                return_value=Path(folder),
            ),
        ):
            source = f"event_source_{'a' * 32}"
            state._photo_sources = [(source, "garden.png", "image/png")]
            Path(folder, source).write_bytes(buffer.getvalue())
            events = [
                event
                async for event in EventState.process_photos.fn(
                    state, list(state._photo_sources), "42", 1
                )
            ]
            self.assertEqual(len(state.pending_photo_paths), 1)
            self.assertFalse(Path(folder, source).exists())
            path = state.pending_photo_paths[0]
            with Image.open(Path(folder, path)) as photo:
                self.assertEqual(photo.format, "WEBP")
                self.assertEqual(photo.size, (120, 80))
            self.assertLess(Path(folder, path).stat().st_size, 1_000_000)
            await EventState.remove_photo.fn(state, path)
            self.assertFalse(Path(folder, path).exists())
            self.assertEqual(state.pending_photo_paths, [])
        self.assertFalse(state.photo_busy)

    async def test_mismatched_photo_is_rejected_without_persistence(self):
        state = planner_state()
        state.photo_busy = True
        source = f"event_source_{'d' * 32}"
        state._photo_sources = [(source, "garden.jpg", "image/jpeg")]
        buffer = BytesIO()
        Image.new("RGB", (10, 10), "orange").save(buffer, format="PNG")
        with (
            tempfile.TemporaryDirectory() as folder,
            patch(
                "app.states.event_state.rx.get_upload_dir",
                return_value=Path(folder),
            ),
        ):
            Path(folder, source).write_bytes(buffer.getvalue())
            events = [
                event
                async for event in EventState.process_photos.fn(
                    state, list(state._photo_sources), "42", 1
                )
            ]
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertEqual(state.pending_photo_paths, [])
        self.assertTrue(state.photo_error)
        self.assertFalse(state.photo_busy)

    async def test_source_size_and_slot_limit_fail_visibly(self):
        state = planner_state()
        upload = SimpleNamespace(
            size=3_000_001, name="large.png", read=AsyncMock()
        )
        with (
            tempfile.TemporaryDirectory() as folder,
            patch(
                "app.states.event_state.rx.get_upload_dir",
                return_value=Path(folder),
            ),
        ):
            events = [
                event
                async for event in EventState.handle_upload.fn(state, [upload])
            ]
        upload.read.assert_not_awaited()
        self.assertIn("3 MB", state.photo_error)
        self.assertFalse(state.photo_busy)
        state.pending_photo_paths = [
            f"event_42_{index:032x}.webp" for index in range(5)
        ]
        events = [
            event
            async for event in EventState.handle_upload.fn(state, [upload])
        ]
        self.assertIn("five", state.photo_error)
        self.assertEqual(len(state.pending_photo_paths), 5)

    def test_safe_persisted_photos_and_card_capacity(self):
        photo = f"event_42_{'c' * 32}.webp"
        for value in (
            "",
            "null",
            "{}",
            "invalid",
            '["../secret.webp"]',
            '["https://example.com/photo.webp"]',
        ):
            self.assertEqual(_safe_event_photos(value), [])
        self.assertEqual(
            _safe_event_photos(json.dumps([photo, photo])), [photo]
        )
        self.assertIn("photo_paths", CommunityEvent.__table__.columns)
        self.assertTrue(CommunityEvent.__table__.columns.photo_paths.nullable)
        self.assertIn("e.photo_paths", _CARD_SELECT)
        row = (
            7,
            "teamwork",
            "Garden",
            "Details",
            "Park",
            "Porto",
            "Portugal",
            datetime.datetime.now(datetime.UTC),
            None,
            1,
            1,
            42,
            "Host",
            "member-42",
            "",
            True,
            "",
            0,
            41.25,
            -8.65,
            json.dumps([photo]),
            "Lunch",
        )
        card = _card(row, 99)
        self.assertEqual(card["photo_paths"], [photo])
        self.assertIn("1 helpers needed", card["capacity_label"])
        self.assertTrue(card["is_full"])
        self.assertFalse(card["can_join"])
        self.assertNotIn("latitude", card)
        self.assertNotIn("longitude", card)
        self.assertTrue(event_cards.event_card(card).render())

    def test_map_list_selection_and_gold_star(self):
        self.assertIn(
            "discovery_event_list()",
            inspect.getsource(member_map.member_list_view),
        )
        self.assertIn(
            "EventState.select_event",
            inspect.getsource(event_cards.discovery_event_list),
        )
        renderer = openfreemap._MAP_COMPONENT.split(
            '} else if (marker.kind === "event") {'
        )[1].split("} else if")[0]
        self.assertIn("border-radius:999px", renderer)
        self.assertIn("background:#dca126", renderer)
        self.assertIn('goAndHelpIconSvg("star", 27, "#ffffff")', renderer)
        self.assertNotIn("rotate(", renderer)
        for component in (
            event_cards.event_composer,
            event_cards.event_planner_screen,
            event_cards.discovery_event_list,
        ):
            self.assertTrue(component().render())


if __name__ == "__main__":
    unittest.main()
