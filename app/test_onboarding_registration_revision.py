import reflex as rx

import datetime
import inspect
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components import onboarding, auth_panel
from app.models import LOCATION_MODE_HIDDEN
from app.skill_categories import CATEGORY_CHOICES, category_labels
from app.states.auth_state import (
    parse_birth_parts,
    validate_birth_date,
    MIN_REGISTRATION_AGE,
)
from app.states.onboarding_state import OnboardingState, COUNTRY_OPTIONS
from app.test_onboarding_preferences import FinishHarness


class RevisionTests(unittest.TestCase):
    def test_images_and_white_surfaces(self):
        expected = [
            "background_portrait_mobile.png",
            "dog_walking_porch.png",
            "text_asset_named.png",
            "background_sewing_portrait.png",
            "woman_soft_people.png",
        ]
        for step, asset in enumerate(expected, 1):
            self.assertIn(asset, onboarding.BACKGROUND_CLASSES[step])
        source = inspect.getsource(onboarding)
        self.assertIn("bg-white/80", source)
        self.assertIn("absolute inset-0 bg-white/45", source)
        body = inspect.getsource(onboarding.screen_body)
        self.assertIn("OnboardingState.categories.length() > 0", body)
        self.assertIn('"Any more details?"', body)
        self.assertNotIn("CATEGORY_OTHER", body)
        self.assertIn(
            "placeholder=label", inspect.getsource(onboarding.custom_answer)
        )
        self.assertLess(
            body.index("Post your first help request here"),
            body.index("Skip for now"),
        )
        self.assertLess(
            body.index("Skip for now"), body.index("first_request_screen(),")
        )

    def test_all_categories_optional_details_roundtrip(self):
        state = OnboardingState(_reflex_internal_init=True)
        for choice in CATEGORY_CHOICES:
            state._reset()
            state.saving = False
            state.current_step = 8
            state.toggle_category(choice["value"])
            self.assertTrue(state.can_continue)
            state.set_custom_skill("Practical experience")
            answers = json.loads(json.dumps(state._answers()))
            state._apply_answers(answers, {})
            self.assertEqual(state._profile_skills(), "Practical experience")
            for label in category_labels(state.categories):
                self.assertIn(label, state.summary_rows[2]["value"])
            self.assertIn(
                "Practical experience", state.summary_rows[2]["value"]
            )
        state.categories = ["invalid-category"]
        self.assertFalse(state.can_continue)

    def test_location_defaults_restore_and_drag(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.saving = False
        self.assertEqual(state.location_pref, LOCATION_MODE_HIDDEN)
        center, zoom = list(state.map_center), state.map_zoom
        state.set_location_point(float("nan"), 5)
        self.assertEqual(state.location_pref, LOCATION_MODE_HIDDEN)
        state.set_location_point(12, 45)
        self.assertEqual(state.location_pref, "approximate")
        self.assertEqual((state.map_center, state.map_zoom), (center, zoom))
        state.choose_location("off")
        state._apply_answers(json.loads(json.dumps(state._answers())), {})
        self.assertEqual(state.location_pref, LOCATION_MODE_HIDDEN)
        state.set_location_point(13, 44)
        self.assertEqual(state.location_pref, "approximate")
        source = inspect.getsource(onboarding.location_choice)
        self.assertIn("ring-2 ring-[#e08b12]", source)
        self.assertIn(
            "camera_updates=False",
            inspect.getsource(onboarding.location_screen),
        )

    def test_years_and_exact_birthday(self):
        self.assertEqual(MIN_REGISTRATION_AGE, 16)
        years = list(map(int, auth_panel.YEAR_OPTIONS))
        self.assertEqual(
            years,
            list(
                range(
                    auth_panel.CURRENT_YEAR - 16,
                    auth_panel.CURRENT_YEAR - 120,
                    -1,
                )
            ),
        )
        real_date = datetime.date
        with patch("app.states.auth_state.datetime.date") as date:
            date.today.return_value = real_date(2026, 6, 15)
            self.assertEqual(validate_birth_date(real_date(2010, 6, 15))[1], "")
            self.assertIn("16", validate_birth_date(real_date(2010, 6, 16))[1])
            self.assertEqual(validate_birth_date(real_date(2009, 6, 16))[1], "")
            self.assertTrue(validate_birth_date(real_date(2027, 1, 1))[1])
            date.side_effect = real_date
            self.assertTrue(parse_birth_parts("29", "2", "2010")[1])
            self.assertEqual(parse_birth_parts("29", "2", "2008")[1], "")


class RevisionPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_skills_draft_saves_only_answer_patch(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.saving = False
        state.has_row = True
        state.categories = [CATEGORY_CHOICES[0]["value"]]
        state.set_custom_skill("x" * 700)
        session = AsyncMock()
        session.__aenter__.return_value = session
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
            patch.object(rx, "asession", return_value=session),
        ):
            await OnboardingState.persist_skills_draft.fn(state)
        sql, params = session.execute.await_args.args
        self.assertIn("completed_at IS NULL", str(sql))
        saved = json.loads(params["draft"])
        self.assertEqual(len(saved["custom_skill"]), 500)
        self.assertEqual(saved["categories"], state.categories)
        state._apply_answers(saved, {})
        self.assertEqual(state._profile_skills(), saved["custom_skill"])
        session.commit.assert_awaited_once()

    async def test_primary_queues_post_even_partial_draft(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.saving = False
        state.has_row = True
        state.current_step = 13
        state.request_title = "Partial draft"
        harness = FinishHarness(state)
        session = AsyncMock()
        session.__aenter__.return_value = session
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
            patch.object(rx, "asession", return_value=session),
            patch.object(rx, "toast") as toast,
        ):
            events = []
            async for event in OnboardingState.go_next.fn(harness):
                events.append(event)
        self.assertEqual(harness.current_step, 13)
        self.assertEqual(harness.first_request_post_id, 0)
        session.execute.assert_not_awaited()
        self.assertEqual(events, [OnboardingState.post_first_request])
        toast.assert_not_called()

    async def test_completion_is_silent_and_tour_is_persisted(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.username = "test.member"
        state.home_country = COUNTRY_OPTIONS[0]
        state.categories = [CATEGORY_CHOICES[0]["value"]]
        state.custom_skill = "Sewing repairs"
        harness = FinishHarness(state)
        session = AsyncMock()
        session.execute.return_value = SimpleNamespace(rowcount=1)
        session.__aenter__.return_value = session
        with (
            patch.object(rx, "asession", return_value=session),
            patch.object(rx, "toast") as toast,
        ):
            events = []
            async for event in OnboardingState._finish(harness, 7):
                events.append(event)
        self.assertTrue(harness.is_complete)
        self.assertEqual(harness.tour_step, 0)
        self.assertFalse(harness.tour_hidden)
        self.assertTrue(harness.tour_prompt_visible)
        self.assertNotIn(OnboardingState.apply_tour_target, events)
        self.assertEqual(len(events), 1)
        toast.assert_not_called()
        profile = next(
            call.args[1]
            for call in session.execute.await_args_list
            if "UPDATE skillkind_profile" in str(call.args[0])
        )
        self.assertEqual(profile["skills"], "Sewing repairs")
        self.assertEqual(profile["categories"], state.categories[0])
        session.commit.assert_awaited_once()
