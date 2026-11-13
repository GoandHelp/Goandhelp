import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import reflex as rx

from app.components.auth_panel import register_form
from app.components.guest_map import sign_up_wall
from app.states.auth_state import AuthState
from app.states.event_state import EventState
from app.states.membership_state import MembershipState
from app.states.onboarding_state import OnboardingState
from app.states.profile_metrics_state import ProfileMetricsState
from app.states.profile_state import ProfileState
from app.states.unified_inbox_state import UnifiedInboxState


class GuestAuthSurfaceTests(unittest.TestCase):
    def test_overlay_header_centers_both_registration_and_verification(self):
        source = inspect.getsource(sign_up_wall)
        self.assertIn('"Become a member"', source)
        self.assertIn('"Join our Global Community"', source)
        self.assertIn('"One step left"', source)
        self.assertIn('"Confirm your email"', source)
        self.assertIn(
            'class_name="flex min-w-0 flex-col items-center text-center"',
            source,
        )
        self.assertIn("grid-cols-[3rem_minmax(0,1fr)_3rem]", source)
        self.assertIn("src=BRAND_LOGO_SRC", source)
        self.assertIn('aria_label="Close sign-up panel"', source)
        self.assertTrue(sign_up_wall().render())

    def test_consent_hit_area_is_bounded_and_native_validation_remains(self):
        source = inspect.getsource(register_form)
        self.assertIn('type="checkbox"', source)
        self.assertIn('name="terms_consent"', source)
        self.assertIn("required=True", source)
        self.assertIn('default_value="accepted"', source)
        self.assertIn("peer-focus-visible:outline-2", source)
        self.assertIn("relative mx-auto inline-flex w-fit max-w-full", source)
        self.assertIn("peer absolute inset-0 z-10 m-0 h-full w-full", source)
        self.assertNotIn('class_name="peer sr-only"', source)
        self.assertTrue(register_form().render())

    def test_overlay_scroll_is_viewport_bounded_without_bottom_spacer(self):
        source = inspect.getsource(sign_up_wall)
        self.assertIn("max-h-[calc(100dvh-1.5rem)]", source)
        self.assertIn("sm:max-h-[calc(100dvh-3rem)]", source)
        self.assertIn("min-h-0 flex-col gap-3 overflow-y-auto", source)
        self.assertIn("[overflow-anchor:none]", source)
        self.assertIn("pt-4 pb-3 sm:px-5 sm:pt-5 sm:pb-4", source)
        self.assertNotIn("maxHeight", source)
        self.assertNotIn("max-h-[90vh]", source)
        self.assertNotIn("min-h-screen", source)


class SignOutSilenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_sign_out_resets_other_states_without_notice(self):
        state = AuthState(_reflex_internal_init=True)
        state.subscriber_id = "42"
        state.email = "member@example.com"
        state.joined_label = "Jan 01, 2024"
        state.success = "Previous notice"
        state.awaiting_verification = True
        state.unverified_access = True
        onboarding = SimpleNamespace(_reset=Mock())
        profile = SimpleNamespace(clear_profile=Mock())
        membership = SimpleNamespace(_reset=Mock())
        metrics = SimpleNamespace(_reset=Mock())
        unified = SimpleNamespace(visited_keys=["job:1"], visited_account="42")
        events = EventState(_reflex_internal_init=True)
        events.events = [{"id": 7}]
        events.event_markers = [{"id": "e7"}]
        events.selected_event = [{"id": 7}]
        states = {
            UnifiedInboxState: unified,
            EventState: events,
            OnboardingState: onboarding,
            ProfileState: profile,
            MembershipState: membership,
            ProfileMetricsState: metrics,
        }
        with (
            patch.object(
                AuthState, "get_state", AsyncMock(side_effect=states.get)
            ),
            patch.object(rx, "toast") as toast,
        ):
            result = await AuthState.sign_out.fn(state)
        self.assertIsNone(result)
        toast.assert_not_called()
        onboarding._reset.assert_called_once_with()
        profile.clear_profile.assert_called_once_with()
        membership._reset.assert_called_once_with()
        metrics._reset.assert_called_once_with()
        self.assertEqual(unified.visited_keys, [])
        self.assertEqual(unified.visited_account, "")
        self.assertEqual(events.events, [])
        self.assertEqual(events.event_markers, [])
        self.assertEqual(events.selected_event, [])
        self.assertEqual(state.subscriber_id, "")
        self.assertEqual(state.email, "")
        self.assertEqual(state.joined_label, "")
        self.assertEqual(state.success, "")
        self.assertEqual(state.auth_tab, "register")
        self.assertFalse(state.awaiting_verification)
        self.assertFalse(state.unverified_access)
        self.assertNotIn(
            "Signed out. Safe travels!",
            inspect.getsource(AuthState.sign_out.fn),
        )
