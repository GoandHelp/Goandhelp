import reflex as rx

import inspect
import json
from pathlib import Path
from urllib.parse import unquote
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.components import onboarding as ui
from app.components import header
from app.components.auth_panel import register_form
from app.components.map_picker import map_picker
from app.components.request_draft import compact_request_fields, draft_select
from app.components.openfreemap import _MAP_COMPONENT
from app.states.auth_state import AuthState
from app.states.discovery_state import DiscoveryState
from app.states.onboarding_state import (
    OnboardingState,
    TOTAL_STEPS,
    ONBOARDING_SCREENS,
    LANGUAGE_PRESETS,
    LABEL_TO_LANGUAGE_CODE,
    COUNTRY_OPTIONS,
    PERMISSION_TOPICS,
)
from app.test_onboarding_preferences import FinishHarness
from app.test_first_request_onboarding import seed_draft, session_context
from PIL import Image


class ConsolidationTests(unittest.TestCase):
    def test_bounds_legacy_and_completed_accounts(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.home_country = COUNTRY_OPTIONS[0]
        state.username = "test.member"
        seed_draft(state)
        answers = state._answers()
        for completed in (None, "2026-01-01"):
            state._apply_progress_row(
                (
                    14,
                    "1,12,13,14",
                    json.dumps(answers),
                    "{}",
                    completed,
                    4,
                    None,
                )
            )
            self.assertEqual(state.current_step, 13)
            self.assertEqual(state.is_complete, completed is not None)
            self.assertEqual(state.request_title, answers["request_title"])
            self.assertEqual(state.step_label, "Step 13 of 13")
            self.assertEqual(state.progress_width, "100%")
        self.assertEqual(TOTAL_STEPS, 13)
        self.assertEqual(len(ONBOARDING_SCREENS), 13)
        self.assertEqual(set(ui.BACKGROUND_CLASSES), set(range(1, 14)))
        self.assertIn("aria_valuemax=13", inspect.getsource(ui.progress_bar))
        self.assertNotIn("(14,", inspect.getsource(ui.screen_body))

    def test_assets_treatment_and_bounded_preload(self):
        assets = Path(__file__).resolve().parent.parent / "assets"
        expected_assets = [
            "background_portrait_mobile.png",
            "dog_walking_porch.png",
            "text_asset_named.png",
            "background_sewing_portrait.png",
            "woman_soft_people.png",
            "travel_screen_six.png",
            "community_together_vertical.png",
            "screen_eight_skills.png",
            "9_language_vertical.png",
            "map_white_hand.png",
            "portrait_mobile_onboarding.png",
            "vertical_mobile_onboarding.png",
            "9_language_vertical.png",
        ]
        self.assertEqual(
            [ui.BACKGROUND_URLS[step].lstrip("/") for step in range(1, 14)],
            expected_assets,
        )
        for classes in ui.BACKGROUND_CLASSES.values():
            filename = classes.split("url('/")[1].split("')")[0]
            self.assertTrue(filename.endswith(".png"))
            image_path = assets / filename
            self.assertTrue(image_path.is_file())
            with Image.open(image_path) as image:
                image.verify()
            for token in (
                "bg-cover bg-center",
                "saturate-[0.9]",
                "contrast-[0.97]",
                "sepia-[0.08]",
            ):
                self.assertIn(token, classes)
        logo_path = assets / unquote(header.BRAND_LOGO_SRC).lstrip("/")
        self.assertEqual(header.BRAND_LOGO_SRC, "/GO%20AND%20HELP%20LOGO.png")
        self.assertTrue(logo_path.is_file())
        with Image.open(logo_path) as image:
            image.verify()
        source = inspect.getsource(ui.onboarding_flow)
        self.assertIn('rel="preload"', source)
        self.assertIn('type="image/png"', source)
        self.assertIn('rel="prefetch"', source)
        self.assertIn("current_step + 1", source)
        self.assertIn("bg-white/45", inspect.getsource(ui.slide_background))

    def test_exact_copy_and_notification_independence(self):
        source = inspect.getsource(ui)
        for copy in (
            "Go and Help is a community of good people giving and receiving help across a many fields of knowledge",
            "Whatever tasks in life have not yet accomplished, there may be a helper out there who is happy to help",
            "Only a confirmed helper is shown your accurate job location",
            "Disregard to these rules will result in a blocked account",
            "I agree to these community rules",
        ):
            self.assertIn(copy, source)
        self.assertEqual(ONBOARDING_SCREENS[3]["title"], "Get help")
        self.assertIn("phone/device", PERMISSION_TOPICS[0]["body"])
        self.assertIn(
            "In-app notifications are always on", PERMISSION_TOPICS[0]["body"]
        )
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.choose_permission("camera", "not_now")
        state.choose_permission("notifications", "allow_later")
        self.assertEqual(state.perm_camera, "not_now")

    def test_languages_and_consent(self):
        self.assertEqual(
            LANGUAGE_PRESETS[:10],
            [
                "English",
                "Spanish",
                "French",
                "German",
                "Portuguese",
                "Chinese",
                "Russian",
                "Arabic",
                "Hindi",
                "Japanese",
            ],
        )
        self.assertEqual(LANGUAGE_PRESETS[10:], sorted(LANGUAGE_PRESETS[10:]))
        self.assertEqual(len(LANGUAGE_PRESETS), len(set(LANGUAGE_PRESETS)))
        self.assertEqual(LABEL_TO_LANGUAGE_CODE["Chinese"], "zh")
        self.assertEqual(LABEL_TO_LANGUAGE_CODE["Arabic"], "ar")
        chip = inspect.getsource(ui.language_chip)
        self.assertIn("aria_pressed", chip)
        self.assertNotIn("bg-white", chip)
        self.assertNotIn("rounded-full", chip)
        controls = inspect.getsource(ui.language_scroll)
        for token in (
            "Scroll languages up",
            "Scroll languages down",
            "scrollBy",
            "220",
            "triangle",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, controls)
        consent = inspect.getsource(register_form)
        for token in (
            "I agree to the Terms and User Agreement (required)",
            "border-black!",
            "bg-white",
            "peer-checked:bg-[#fba922]",
            "text-black",
        ):
            self.assertIn(token, consent)

    def test_request_layout_and_overlay(self):
        source = inspect.getsource(ui.screen_body)
        self.assertLess(
            source.index("Post your first help request here"),
            source.index("Skip for now"),
        )
        self.assertIn("on_click=OnboardingState.complete_onboarding", source)
        self.assertNotIn(
            "Post help request", inspect.getsource(ui.first_request_screen)
        )
        select = inspect.getsource(draft_select)
        self.assertIn("optional — defaults to Free", select)
        self.assertIn("justify-between", select)
        self.assertIn("item.get('blurb', '')", select)
        self.assertNotIn("max-w-xs", inspect.getsource(compact_request_fields))
        self.assertIn(
            "border border-[#b86e08] bg-[#fff7e8]",
            inspect.getsource(map_picker),
        )
        overlay = inspect.getsource(ui.first_request_celebration)
        self.assertIn(
            "Congratulations, your first help request is ready for the world",
            overlay,
        )
        self.assertIn('aria_live="polite"', overlay)
        self.assertIn("motion-reduce:transition-none", overlay)
        self.assertIn("prefers-reduced-motion", _MAP_COMPONENT)
        self.assertTrue(ui.onboarding_flow().render())


class ConsolidationBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def test_clickable_location_warning_without_database(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.has_row = True
        state.current_step = 10
        state.location_pref = "approximate"
        self.assertTrue(state.can_continue)
        harness = FinishHarness(state)
        with (
            patch.object(
                FinishHarness,
                "get_state",
                AsyncMock(
                    return_value=SimpleNamespace(
                        subscriber_id="7", is_verified=True
                    )
                ),
            ),
            patch.object(rx, "asession") as db,
        ):
            async for _ in OnboardingState.go_next.fn(harness):
                pass
        db.assert_not_called()
        self.assertEqual(harness.current_step, 10)
        self.assertEqual(
            harness.error, "Please zoom in and place your location on the map"
        )
        state.choose_location("off")
        self.assertTrue(state.can_continue)

    async def test_skip_and_posted_finish_choose_different_destinations(self):
        for post_id in (0, 88):
            state = OnboardingState(_reflex_internal_init=True)
            state._reset()
            state.home_country = COUNTRY_OPTIONS[0]
            state.username = "test.member"
            state.first_request_post_id = post_id
            harness = FinishHarness(state)
            session = AsyncMock()
            session.__aenter__.return_value = session
            session.execute.return_value = SimpleNamespace(rowcount=1)
            with patch.object(rx, "asession", return_value=session):
                events = []
                async for event in OnboardingState._finish(harness, 7):
                    events.append(event)
            self.assertTrue(harness.is_complete)
            self.assertEqual(harness.tour_step, 0)
            self.assertFalse(harness.tour_hidden)
            self.assertEqual(harness.tour_prompt_visible, not bool(post_id))
            self.assertNotIn(OnboardingState.apply_tour_target, events)
            if post_id:
                self.assertEqual(
                    events[-1], OnboardingState.celebrate_first_request
                )
            self.assertEqual(harness.celebration_pending, bool(post_id))
            self.assertFalse(
                any(
                    "INSERT INTO skillkind_help_post" in str(c.args[0])
                    for c in session.execute.await_args_list
                )
            )

    async def test_celebration_timing_and_real_map_target(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.is_complete = True
        state.celebration_pending = True
        state.request_longitude, state.request_latitude = 12.25, 44.5
        harness = FinishHarness(state)
        auth = SimpleNamespace(subscriber_id="7", is_signed_in=True)
        discovery = SimpleNamespace(clear_selection=Mock())
        profile = SimpleNamespace()
        snapshots = []

        async def get_state(cls):
            return (
                auth
                if cls is AuthState
                else discovery
                if cls is DiscoveryState
                else profile
            )

        async def sleep(seconds):
            snapshots.append(
                (seconds, harness.celebration_visible, discovery.map_zoom)
            )

        with (
            patch.object(
                FinishHarness, "get_state", AsyncMock(side_effect=get_state)
            ),
            patch(
                "app.states.onboarding_state.asyncio.sleep", side_effect=sleep
            ),
        ):
            events = []
            async for event in OnboardingState.celebrate_first_request.fn(
                harness
            ):
                events.append(event)
        self.assertEqual(
            snapshots, [(0.7, True, 9.0), (2.0, True, 13.0), (0.6, True, 13.0)]
        )
        self.assertEqual(discovery.map_center, [12.25, 44.5])
        self.assertEqual(
            (discovery.map_mode, discovery.view_mode), ("give", "map")
        )
        self.assertEqual(profile.active_tab, "discover")
        self.assertFalse(harness.celebration_pending)
        self.assertFalse(harness.celebration_visible)
        self.assertTrue(harness.tour_prompt_visible)
        self.assertEqual(harness.tour_step, 0)
        self.assertEqual(events, [DiscoveryState.refresh_board])

    async def test_database_idempotency_recognizes_other_tab_post(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.saving = False
        state.has_row = True
        state.current_step = 13
        seed_draft(state)
        state.request_has_point = True
        state.request_latitude, state.request_longitude = 44.5, 12.25
        session = SimpleNamespace(
            execute=AsyncMock(
                return_value=SimpleNamespace(
                    first=lambda: ('{"first_request_post_id":88}',)
                )
            ),
            commit=AsyncMock(),
        )
        with (
            patch.object(
                OnboardingState,
                "get_state",
                AsyncMock(
                    return_value=SimpleNamespace(
                        is_signed_in=True, subscriber_id="7"
                    )
                ),
            ),
            patch.object(rx, "asession", return_value=session_context(session)),
        ):
            events = []
            async for event in OnboardingState.post_first_request.fn(state):
                events.append(event)
        self.assertEqual(state.first_request_post_id, 88)
        self.assertFalse(
            any(
                "INSERT INTO skillkind_help_post" in str(c.args[0])
                for c in session.execute.await_args_list
            )
        )
        self.assertIn(
            "FOR UPDATE", str(session.execute.await_args_list[0].args[0])
        )
        self.assertEqual(events[-1], OnboardingState.complete_onboarding)
        session.commit.assert_awaited_once()
