import reflex as rx

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.states.auth_state import AuthState
from app.states.discovery_state import (
    DiscoveryState,
    EMPTY_POST,
    EMPTY_HELPER,
    DISCOVERY_RESULT_CAP,
)
from app.states.profile_state import ProfileState
from app.states.guest_map_state import GuestMapState
from app.states.notification_state import NotificationState
from app.states.membership_state import MembershipState
from app.states.profile_metrics_state import ProfileMetricsState
from app.states.bookmark_state import BookmarkState
from app.states.help_share_state import HelpShareState


class Harness(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


def post_row(pid, author=42):
    row = [None] * 37
    row[0], row[1], row[3], row[14] = pid, "Request", "other", author
    row[25], row[26] = 51.5, -0.12
    return tuple(row)


class OwnedRequestTests(unittest.IsolatedAsyncioTestCase):
    async def load(self, missing=False, capped=False):
        state = Harness(
            get_state=AsyncMock(
                return_value=SimpleNamespace(subscriber_id="42")
            ),
            category_filters=["teaching"],
            reward_filter="lunch",
            city_filter="Elsewhere",
            pending_post_id=1,
            selected_post=dict(EMPTY_POST),
            distance_km=25,
            distance_initialized=True,
            view_mode="map",
            distance_warning=True,
            _premium_now=AsyncMock(return_value=True),
            _advanced_clause=Mock(
                return_value=(
                    " AND pr.nationality = :nationality",
                    {"nationality": "Elsewhere"},
                )
            ),
            _viewer_point=AsyncMock(
                return_value=(None, None, 25) if missing else (51.5, -0.12, 25)
            ),
            _quote_allowed=DiscoveryState._quote_allowed,
        )
        state._row_to_post = lambda row, photos: DiscoveryState._row_to_post(
            state, row, photos
        )
        owned = (
            [post_row(i) for i in range(1, DISCOVERY_RESULT_CAP + 1)]
            if capped
            else [post_row(1)]
        )
        external = [post_row(1), post_row(101, 55)]
        queries = []

        async def execute(query, params):
            sql = str(query)
            queries.append((sql, params))
            if "SELECT p.id" in sql:
                data = owned if "p.author_id = :sid" in sql else external
            elif "SELECT category, COUNT(*)" in sql:
                data = [("other", 2)]
            else:
                data = []
            return Mock(all=Mock(return_value=data))

        session = Harness(execute=AsyncMock(side_effect=execute))
        with (
            patch.object(rx, "asession", return_value=session),
            patch("app.location_privacy.is_land", return_value=True),
        ):
            events = []
            async for event in DiscoveryState._load_jobs(state):
                events.append(event)
        return state, queries, events

    async def test_owned_sql_safety_filters_privacy_and_selection(self):
        state, queries, events = await self.load()
        owned, external = queries[0], queries[1]
        self.assertIn("p.author_id = :sid", owned[0])
        self.assertEqual(owned[1], {"sid": 42})
        for sql, _ in (owned, external):
            for clause in (
                "p.status = 'open'",
                "s.is_active = TRUE",
                "skillkind_completed_task",
                "ca.status = 'accepted'",
                "GREATEST(COALESCE(p.helpers_needed, 1), 1)",
                "p.expires_at > now()",
                f"LIMIT {DISCOVERY_RESULT_CAP}",
            ):
                self.assertIn(clause, sql)
        for token in (
            ":nationality",
            ":city",
            ":reward",
            ":max_distance_km",
            ":job_cat_",
        ):
            self.assertNotIn(token, owned[0])
            self.assertIn(token, external[0])
        self.assertIn("p.author_id <> :sid", external[0])
        self.assertEqual([p["id"] for p in state.posts], [1, 101])
        self.assertEqual(state.open_total, 2)
        self.assertEqual(state.selected_post["id"], 1)
        self.assertNotEqual(
            (state.posts[0]["lat"], state.posts[0]["lng"]), (51.5, -0.12)
        )
        with patch("app.location_privacy.is_land", return_value=True):
            again = state._row_to_post(post_row(1), [])
        self.assertEqual(
            (again["lat"], again["lng"]),
            (state.posts[0]["lat"], state.posts[0]["lng"]),
        )
        self.assertEqual(
            events, [BookmarkState.load_bookmarks, HelpShareState.resolve]
        )
        self.assertIn(
            "poster_id == int(sid)",
            inspect.getsource(DiscoveryState._send_offer),
        )
        state.posts = [state.posts[0]]
        state.group_poster_id = 0
        markers = DiscoveryState.job_map_markers.fget(state)
        self.assertEqual(markers[0]["id"], "p1")
        state._reset_offer_draft = Mock()
        state.selected_post = dict(EMPTY_POST)
        with patch.object(
            rx,
            "asession",
            side_effect=AssertionError("Owner must not count a view"),
        ):
            ignored_events = []
            async for event in DiscoveryState.select_post.fn(state, 1):
                ignored_events.append(event)
        self.assertEqual(state.selected_post["id"], 1)

    async def test_missing_origin_retains_owned_without_external_counts(self):
        state, queries, events = await self.load(missing=True)
        self.assertEqual([p["id"] for p in state.posts], [1])
        self.assertEqual(state.open_total, 0)
        self.assertTrue(all(v == 0 for v in state.category_counts.values()))
        self.assertTrue(state.distance_warning)
        self.assertEqual(
            len([sql for sql, _ in queries if "SELECT p.id" in sql]), 1
        )
        self.assertIn(HelpShareState.resolve, events)

    async def test_owned_first_bounded_merge(self):
        state, _, _ = await self.load(capped=True)
        self.assertEqual(len(state.posts), DISCOVERY_RESULT_CAP)
        self.assertEqual(
            [p["id"] for p in state.posts],
            list(range(1, DISCOVERY_RESULT_CAP + 1)),
        )


class PassportNavigationTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_destinations_close_before_first_yield(self):
        for destination in (
            "profile",
            "help",
            "discover",
            "community",
            "inbox",
            "logo",
        ):
            discovery = DiscoveryState(_reflex_internal_init=True)
            discovery.selected_helper = {**EMPTY_HELPER, "id": 8}
            discovery.selected_post = {**EMPTY_POST, "id": 19}
            discovery.direct_open = discovery.is_loading_direct = (
                discovery.is_sending_direct
            ) = True
            discovery.direct_requests = [
                {
                    "id": 19,
                    "title": "Request",
                    "categories": [],
                    "category_label": "",
                }
            ]
            discovery.direct_post_id = 19
            discovery.direct_draft = discovery.direct_warning = (
                discovery.direct_notice
            ) = "Draft"
            discovery.group_poster_id = 8
            discovery.view_mode = "list"
            auth = SimpleNamespace(is_signed_in=True)
            notifications = SimpleNamespace(help_unread=3)
            guest = SimpleNamespace(wall_open=True, wall_reason="Join")

            async def get_state(cls):
                return {
                    AuthState: auth,
                    DiscoveryState: discovery,
                    NotificationState: notifications,
                    GuestMapState: guest,
                }.get(cls, SimpleNamespace(open_key="privacy"))

            state = SimpleNamespace(
                get_state=get_state,
                _normalize_tab=ProfileState._normalize_tab,
                active_tab="community",
            )
            events = []
            if destination == "logo":
                self.assertIsNone(await ProfileState.return_to_map.fn(state))
            else:
                async for event in ProfileState.navigate_from_bottom_nav.fn(
                    state, destination, ""
                ):
                    self.assertEqual(discovery.selected_helper["id"], 0)
                    self.assertEqual(state.active_tab, destination)
                    events.append(event)
            self.assertEqual(
                state.active_tab,
                "discover" if destination == "logo" else destination,
            )
            self.assertEqual(discovery.selected_helper["id"], 0)
            self.assertEqual(discovery.selected_post["id"], 19)
            self.assertEqual(discovery.group_poster_id, 0)
            self.assertFalse(
                discovery.direct_open
                or discovery.is_loading_direct
                or discovery.is_sending_direct
            )
            self.assertEqual(discovery.direct_requests, [])
            self.assertEqual(discovery.direct_post_id, 0)
            self.assertEqual(
                (
                    discovery.direct_draft,
                    discovery.direct_warning,
                    discovery.direct_notice,
                ),
                ("", "", ""),
            )
            self.assertEqual(
                discovery.view_mode, "map" if destination == "logo" else "list"
            )
            expected = {
                "profile": [
                    MembershipState.load_membership,
                    ProfileMetricsState.load_metrics,
                ],
                "help": [NotificationState.mark_help_read],
            }
            self.assertEqual(events, expected.get(destination, []))
            if destination == "help":
                self.assertEqual(notifications.help_unread, 0)

    async def test_guest_destinations_do_not_touch_discovery(self):
        for tab in ("profile", "help", "discover", "community", "inbox"):
            auth = SimpleNamespace(is_signed_in=False, set_auth_tab=Mock())
            guest = SimpleNamespace(wall_open=False, wall_reason="")

            async def get_state(cls):
                self.assertIn(cls, (AuthState, GuestMapState))
                return auth if cls is AuthState else guest

            state = SimpleNamespace(
                get_state=get_state,
                _normalize_tab=ProfileState._normalize_tab,
                active_tab="discover",
            )
            events = []
            async for event in ProfileState.navigate_from_bottom_nav.fn(
                state, tab, " Join us "
            ):
                events.append(event)
            self.assertEqual(events, [])
            self.assertTrue(guest.wall_open)
            self.assertEqual(guest.wall_reason, "Join us")
            self.assertEqual(state.active_tab, "discover")
            auth.set_auth_tab.assert_called_once_with("signin")
