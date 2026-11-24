import inspect
import unittest

from app.app import index, session_skeleton
from app.components.bottom_nav import (
    _click_handler,
    _mount_handler,
    bottom_nav,
)
from app.states.notification_state import NotificationState
from app.states.profile_state import ProfileState


class LoadingBottomBarTests(unittest.TestCase):
    def test_session_skeleton_renders_one_dock_and_centered_loading_logo(self):
        rendered = str(session_skeleton().render())

        self.assertEqual(rendered.count("gah-bottom-dock"), 1)
        self.assertEqual(rendered.count("gah-loading-logo-image"), 1)
        self.assertIn(
            'id:"gah-session-loading"', session_skeleton().render()["props"]
        )
        self.assertIn("from-[#ffe2bd]", rendered)
        self.assertIn("to-[#d9e9d4]", rendered)
        self.assertIn("z-[101]", rendered)
        self.assertEqual(str(bottom_nav().render()).count("gah-bottom-dock"), 1)

    def test_loading_controls_are_disabled_and_have_no_actions_or_notification_load(
        self,
    ):
        rendered = str(bottom_nav(loading=True).render())

        self.assertEqual(rendered.count("disabled"), 5)
        self.assertIsNone(_click_handler(True, ProfileState.return_to_map))
        self.assertIsNone(
            _click_handler(
                True, ProfileState.navigate_from_bottom_nav("help", "")
            )
        )
        self.assertIsNone(_mount_handler(True))
        self.assertEqual(
            _mount_handler(False), NotificationState.load_notifications
        )
        self.assertIsNotNone(_click_handler(False, ProfileState.return_to_map))
        self.assertIn("z-50", str(bottom_nav().render()))

    def test_error_alerts_clear_the_dock_and_pulse_respects_reduced_motion(
        self,
    ):
        component = session_skeleton()
        rendered = str(component.render())
        source = inspect.getsource(session_skeleton)

        self.assertIn(
            "bottom-[calc(5.5rem+env(safe-area-inset-bottom))]", rendered
        )
        self.assertIn("AuthState.error", source)
        self.assertIn("OnboardingState.error", source)
        self.assertEqual(source.count('role="alert"'), 2)
        self.assertIn("duration: 3000, iterations: Infinity", source)
        self.assertIn("prefers-reduced-motion: reduce", source)
        self.assertIn("motion.addEventListener('change', sync)", source)
        self.assertIn("motion.removeEventListener('change', sync)", source)
        self.assertIn("window.gahLoadingCleanup?.()", source)

    def test_root_keeps_the_existing_single_normal_dock_gate(self):
        source = inspect.getsource(index)

        self.assertIn("session_skeleton()", source)
        self.assertIn(
            "rx.cond(MUST_ONBOARD | SESSION_LOADING, rx.fragment(), bottom_nav())",
            source,
        )
        self.assertEqual(source.count("bottom_nav()"), 1)


if __name__ == "__main__":
    unittest.main()
