import reflex as rx

import inspect
import unittest

from app.components import onboarding
from app.components import request_draft
from app.models import LOCATION_MODE_HIDDEN
from app.states.onboarding_state import (
    OnboardingState,
    ONBOARDING_SCREENS,
    TOTAL_STEPS,
    COUNTRY_OPTIONS,
    parse_steps,
)


class OnboardingStoryTests(unittest.TestCase):
    def setUp(self):
        self.state = OnboardingState(_reflex_internal_init=True)
        # Direct Reflex test instances can share cached defaults.
        self.state.current_step = 1
        self.state.username = ""
        self.state.username_feedback = ""
        self.state.home_country = ""
        self.state.categories = []
        self.state.languages = []
        self.state.location_pref = ""
        self.state.safety_ack = False
        self.state.perm_location = ""
        self.state.perm_notifications = ""
        self.state.perm_camera = ""
        self.state.ready_confirmed = False

    def test_progress_and_titles(self):
        self.assertEqual(TOTAL_STEPS, 13)
        self.assertEqual(len(ONBOARDING_SCREENS), 13)
        self.assertEqual(
            [s["title"] for s in ONBOARDING_SCREENS[:7]],
            [
                "Welcome to Go and Help",
                "What is Go and Help?",
                "Give help",
                "Get help",
                "Offer a reward",
                "Help and travel",
                "Join or create an Event for larger projects",
            ],
        )
        for step in range(1, 14):
            self.state.current_step = step
            self.assertEqual(self.state.step_label, f"Step {step} of 13")
            self.assertEqual(
                self.state.progress_width, f"{round(step * 100 / 13)}%"
            )
        self.assertEqual(parse_steps("0,1,12,13,14,15,99,bad,1"), [1, 12, 13])
        self.state.current_step = 99
        self.assertEqual(self.state.progress_width, "100%")
        self.assertEqual(self.state.screen, ONBOARDING_SCREENS[-1])

    def test_country_and_username_gate(self):
        self.state.username = "valid.name"
        self.assertFalse(self.state.can_continue)
        self.state.home_country = COUNTRY_OPTIONS[0]
        self.assertTrue(self.state.can_continue)
        for username in ("", "ab", "has space", "UPPER", "a" * 31, "@invalid"):
            self.state.username = username
            self.assertFalse(self.state.can_continue)
        self.state.username = "valid_name.123"
        self.state.username_feedback = "That username is already taken."
        self.assertFalse(self.state.can_continue)
        self.state.username_feedback = "Username available"
        self.assertTrue(self.state.can_continue)
        self.state.home_country = "Not a country"
        self.assertFalse(self.state.can_continue)
        for step in range(2, 8):
            self.state.current_step = step
            self.assertTrue(self.state.can_continue)

    def test_exact_story_copy(self):
        source = inspect.getsource(onboarding.story_screen)
        for copy in (
            "Go and Help is a community of good people giving and receiving help across a many fields of knowledge",
            "A helper: Someone who gives help",
            "A helpee: someone who receives help",
            "Help people with simple or technical tasks",
            "locally or globally",
            "All give good Karma...",
            "Whatever tasks in life have not yet accomplished, there may be a helper out there who is happy to help",
            "Whether a second hand bicycle, vintage music records, lunch, cake or cash.",
            "Select what you can offer to thank a helper",
            "Can you give first aid, play a gig or fix a leaky bamboo roof?",
            "From Bangkok to Berlin use Go and Help while travelling. Swap your knowledge and skills for food and accommodation.",
            "Many hands make light work, so joining an event allows many people to come together and help your community.",
            "Festivals",
            "Community projects",
            "Disaster relief",
        ):
            self.assertIn(copy, source)
        first = inspect.getsource(onboarding.screen_body)
        self.assertIn("Community in your hands", first)
        self.assertIn("Choose your username:", first)
        self.assertIn(
            "3–30 lowercase letters, numbers, periods or underscores", first
        )
        self.assertIn(
            "Choose your nationality:",
            inspect.getsource(onboarding.country_screen),
        )
        self.assertIn(
            "rx.foreach(COUNTRY_OPTIONS, country_option)",
            inspect.getsource(onboarding.country_screen),
        )

    def test_requested_screen_and_reward_layout_is_scoped(self):
        flow = inspect.getsource(onboarding.onboarding_flow)
        body = inspect.getsource(onboarding.screen_body)
        details = inspect.getsource(onboarding.custom_answer)
        rewards = inspect.getsource(request_draft.onboarding_rewards)
        self.assertIn("OnboardingState.current_step == 1", flow)
        self.assertIn("mb-3", flow)
        self.assertIn("mb-8", flow)
        self.assertIn("skill_details=True", body)
        self.assertIn("skill_details,", details)
        self.assertIn("max-w-sm", details)
        self.assertIn("max-w-xs", details)
        self.assertIn('"Any other languages:"', body)
        self.assertIn("text-base font-bold", body)
        self.assertIn("Post your first help request here", body)
        self.assertIn("justify-between", rewards)
        self.assertIn("optional — defaults to Free", rewards)
        self.assertIn(
            "rx.foreach(REWARD_CHOICES, onboarding_reward_row)", rewards
        )

    def test_backgrounds_and_removed_chrome(self):
        assets = (
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
        )
        self.assertEqual(set(onboarding.BACKGROUND_CLASSES), set(range(1, 14)))
        for step, asset in enumerate(assets, 1):
            classes = onboarding.BACKGROUND_CLASSES[step]
            self.assertIn("bg-[url('/{}')]".format(asset), classes)
            self.assertIn("absolute inset-0", classes)
            self.assertIn("bg-cover bg-center", classes)
        background = inspect.getsource(onboarding.slide_background)
        self.assertIn("current_step <= 13", background)
        self.assertIn('absolute inset-0 bg-white"', background)
        source = inspect.getsource(onboarding).split(
            "# ------------------------------------------------------------------ the tour"
        )[0]
        for old in (
            "CARD_CLASS",
            "value_illustration",
            "value_screen",
            "color_fields",
            "blur-[",
            "sticky top-0",
            '["kicker"]',
            "MODE_CHOICES",
        ):
            self.assertNotIn(old, source)
        self.assertIn("aria_valuemax=13", source)
        self.assertIn(
            "justify-center", inspect.getsource(onboarding.onboarding_actions)
        )

    def test_component_build_and_later_mapping(self):
        self.assertTrue(str(onboarding.onboarding_flow()))
        source = inspect.getsource(onboarding.screen_body)
        for expected in (
            "(12, permissions_screen())",
            "first_request_screen(),",
        ):
            self.assertIn(expected, source)
        for step, field in (
            (8, "categories"),
            (9, "languages"),
            (10, "location_pref"),
            (11, "safety_ack"),
        ):
            self.state.current_step = step
            self.assertFalse(self.state.can_continue)
            setattr(
                self.state,
                field,
                {
                    "categories": ["arts"],
                    "languages": ["English"],
                    "location_pref": LOCATION_MODE_HIDDEN,
                    "safety_ack": True,
                }[field],
            )
            self.assertTrue(self.state.can_continue)
        self.assertEqual(self.state._answers()["setup_version"], 3)


if __name__ == "__main__":
    unittest.main()
