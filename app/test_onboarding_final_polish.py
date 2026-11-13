import reflex as rx

import inspect
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components import onboarding as ui
from app.components import membership_info, paywall, profile_tabs
from app.components.map_picker import map_picker
from app.components.request_draft import compact_request_fields
from app.states.onboarding_state import OnboardingState, ONBOARDING_SCREENS
from app.models import CATEGORY_OTHER, LOCATION_MODE_HIDDEN
from app.test_first_request_onboarding import (
    seed_draft,
    session_context,
    valid_params,
)
from app.test_onboarding_preferences import FinishHarness


class OnboardingVisualContracts(unittest.TestCase):
    def test_backgrounds_and_surfaces(self):
        self.assertEqual(set(ui.BACKGROUND_CLASSES), set(range(1, 14)))
        for step, classes in ui.BACKGROUND_CLASSES.items():
            self.assertIn("bg-cover bg-center", classes)
            self.assertEqual("woman_soft_people.png" in classes, step == 5)
        source = inspect.getsource(ui)
        self.assertEqual(source.count("bg-white/45"), 1)
        for opacity in (
            "bg-white/35",
            "bg-white/85",
            "bg-white/90",
        ):
            self.assertNotIn(opacity, source)
        for factory in (
            ui.country_screen,
            ui.setup_panel,
            ui.custom_answer,
            ui.category_card,
        ):
            self.assertIn("bg-white/80", inspect.getsource(factory))
        self.assertIn("bg-white/80", ui.COPY_PANEL)
        for classes in (ui.CHIP_ON, ui.CHIP_OFF):
            self.assertIn("bg-white ", classes)
            self.assertNotIn("bg-white/", classes)
        country = str(ui.country_screen())
        self.assertIn("bg-white px-4", country)
        body = inspect.getsource(ui.screen_body)
        self.assertIn('id="onboarding-languages"', body)
        self.assertIn("rounded-2xl bg-white/80 p-3", body)
        self.assertIn("bg-white px-3 py-2", inspect.getsource(ui.custom_answer))
        self.assertIn(
            "bg-transparent", inspect.getsource(ui.first_request_screen)
        )
        self.assertIn(
            "bg-transparent", inspect.getsource(compact_request_fields)
        )

    def test_story_and_layout(self):
        self.assertEqual(ONBOARDING_SCREENS[2]["title"], "Give help")
        self.assertEqual(ONBOARDING_SCREENS[5]["title"], "Help and travel")
        story = inspect.getsource(ui.story_screen)
        for removed in (
            "Help people locally or globally",
            "Events like",
            "Help the elderly, people in need or just the average person",
        ):
            self.assertNotIn(removed, story)
        self.assertIn('copy_panel("locally or globally")', story)
        self.assertIn('"Events"', story)
        self.assertIn('rx.el.p("A helper: Someone who gives help")', story)
        self.assertIn('rx.el.p("A helpee: someone who receives help")', story)
        self.assertIn("flex-col gap-3 rounded-2xl bg-white", story)
        self.assertIn(
            "Whether a second hand bicycle, vintage music records, lunch, cake or cash.",
            story,
        )
        body = inspect.getsource(ui.screen_body)
        self.assertIn("focus-within:border-[#e08b12]", body)
        self.assertNotIn("focus-within:ring", body)
        self.assertIn("border-0!", body)
        self.assertIn('hint="Optional"', body)
        self.assertIn(
            "ml-auto text-right text-xs", inspect.getsource(ui.custom_answer)
        )
        commitment = inspect.getsource(ui.commitment_row)
        self.assertEqual(commitment.count("text-sm"), 2)
        self.assertIn("text-[13px] font-bold text-[#e08b12]", body)
        self.assertIn(
            "mx-auto w-full max-w-md rounded-2xl bg-white",
            inspect.getsource(ui.permissions_screen),
        )

    def test_request_error_skip_and_map(self):
        body = inspect.getsource(ui.screen_body)
        self.assertIn("Skip for now", body)
        request = inspect.getsource(ui.first_request_screen)
        self.assertNotIn('"Post help request"', request)
        self.assertIn('role="alert"', request)
        self.assertIn("text-[#e08b12]", request)
        self.assertIn(
            "OnboardingState.current_step != 13",
            inspect.getsource(ui.onboarding_flow),
        )
        fields = inspect.getsource(compact_request_fields)
        self.assertIn("w-full text-left", fields)
        from app.components.request_draft import draft_select

        self.assertIn(
            "optional — defaults to Free", inspect.getsource(draft_select)
        )
        self.assertIn(
            'class_name="text-center text-sm font-semibold text-[#404040]"',
            fields,
        )
        self.assertIn(
            'class_name="mt-1 text-center text-xs text-[#525252]"', fields
        )
        picker = inspect.getsource(map_picker)
        self.assertIn('picker_key == "onboarding-first-request"', picker)
        self.assertIn("order-2 mx-auto", picker)
        self.assertIn("camera_updates=False", picker)
        self.assertIn(
            "camera_updates=False", inspect.getsource(ui.location_screen)
        )

    def test_subscription_gradient_and_states(self):
        classes = paywall.PAYMENT_ACTION_CLASS
        self.assertIn(
            "linear-gradient(300deg,#fba922_0%,#ffda91_50%,#fba922_100%)",
            classes,
        )
        for token in (
            "justify-center",
            "hover:brightness-95",
            "focus-visible:ring-4",
            "disabled:bg-none",
            "disabled:cursor-not-allowed",
        ):
            self.assertIn(token, classes)
        source = inspect.getsource(paywall.paywall_modal)
        self.assertIn("class_name=PAYMENT_ACTION_CLASS", source)
        self.assertIn("disabled=MembershipState.checkout_busy", source)
        self.assertIn("on_click=MembershipState.start_checkout", source)
        self.assertIn("aria_busy=", source)
        self.assertTrue(paywall.paywall_modal().render())

    def test_tour_verification_premium(self):
        tour = inspect.getsource(ui.guided_tour)
        self.assertIn("absolute right-3 top-3", tour)
        self.assertIn("mt-0 min-h-7 px-7", tour)
        self.assertIn("pt-3", ui.TOUR_CARD_CLASS)
        self.assertIn('aria_labelledby="gah-tour-title"', tour)
        self.assertIn('aria_describedby="gah-tour-description"', tour)
        guidance = profile_tabs.verification_guidance()
        self.assertEqual(guidance.tag, "details")
        self.assertEqual(guidance.children[0].tag, "summary")
        self.assertNotIn(
            "What the verification tick means", str(guidance.children[0])
        )
        self.assertIn(
            "What the verification tick means", str(guidance.children[1])
        )
        self.assertIn("font-normal", str(guidance.children[0]))
        note = profile_tabs.verification_note("", "Title", "Body")
        for token in ("rounded", "border", "bg-", "shadow"):
            self.assertNotIn(token, str(note.class_name))
        membership = inspect.getsource(
            membership_info.membership_information_section
        )
        self.assertIn("bg-[#fba922] hover:bg-[#e08b12]", membership)
        self.assertNotIn("bg-linear", membership)
        ticket = str(paywall.transit_ticket(rx.Var.create(True), "purple"))
        self.assertIn(
            "border-dashed border-[#fba922] bg-white text-[#fba922]", ticket
        )
        for factory in (
            membership_info.comparison_column,
            paywall.comparison_rail,
        ):
            self.assertIn("pl-3 sm:pl-5", inspect.getsource(factory))


class OnboardingBehaviorContracts(unittest.IsolatedAsyncioTestCase):
    async def test_free_reward_is_onboarding_only_and_persisted(self):
        with self.assertRaises(ValueError):
            valid_params(reward="")
        result = valid_params(reward="", allow_free=True)
        self.assertEqual(result["reward_type"], "gratitude_only")
        self.assertEqual(result["reward_details"], "Free")
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        seed_draft(state)
        state.request_reward = ""
        state.has_row = True
        state.current_step = 13
        state.request_has_point = True
        state.request_latitude, state.request_longitude = 51.5, -0.12

        async def execute(sql, params):
            if "SELECT answers_json" in str(sql):
                return SimpleNamespace(first=lambda: ("{}",))
            return SimpleNamespace(scalar_one=lambda: 88)

        session = SimpleNamespace(
            execute=AsyncMock(side_effect=execute), commit=AsyncMock()
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
            patch("reflex.asession", return_value=session_context(session)),
            patch(
                "app.states.onboarding_state.check_post_allowance",
                AsyncMock(return_value=(True, False, 0, 2)),
            ),
        ):
            async for _ in OnboardingState.post_first_request.fn(state):
                pass
        insert = next(
            call.args[1]
            for call in session.execute.await_args_list
            if "INSERT INTO skillkind_help_post" in str(call.args[0])
        )
        self.assertEqual(insert["reward_type"], "gratitude_only")
        self.assertEqual(insert["reward_types"], "gratitude_only")
        self.assertEqual(insert["reward_details"], "Free")
        self.assertEqual(insert["reward_value"], 0)
        self.assertEqual(state.current_step, 13)

    async def test_partial_request_validates_before_database(self):
        for field in ("request_title", "request_description", "request_other"):
            state = OnboardingState(_reflex_internal_init=True)
            state._reset()
            state.has_row = True
            state.current_step = 13
            setattr(state, field, "Started")
            with self.assertNoLogs(level="ERROR"):
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
                    patch("reflex.asession") as session,
                ):
                    async for _ in OnboardingState.post_first_request.fn(state):
                        pass
            session.assert_not_called()
            self.assertTrue(state.error)
            self.assertFalse(state.saving)
            self.assertEqual(state.current_step, 13)

    async def test_unexpected_first_request_failure_is_logged_and_sanitized(
        self,
    ):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.has_row = True
        state.current_step = 13
        sentinel = "unexpected validation runtime failure"
        with self.assertLogs(level="ERROR") as logs:
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
                patch("reflex.asession") as session,
                patch(
                    "app.states.onboarding_state.validate_request",
                    side_effect=RuntimeError(sentinel),
                ),
            ):
                async for _ in OnboardingState.post_first_request.fn(state):
                    pass
        session.assert_not_called()
        self.assertFalse(state.saving)
        self.assertEqual(state.current_step, 13)
        self.assertEqual(
            state.error,
            "We couldn't post your request. Your draft is kept; please try again.",
        )
        self.assertNotIn(sentinel, state.error)
        self.assertTrue(any(sentinel in record for record in logs.output))
        self.assertTrue(
            any(
                record.exc_info is not None
                and sentinel in str(record.exc_info[1])
                for record in logs.records
            )
        )

    async def test_empty_skip_advances_and_saves(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.has_row = True
        state.current_step = 13
        self.assertTrue(state.can_continue)
        self.assertEqual(state.continue_label, "Let's go and help!")
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
            patch("reflex.asession", return_value=session),
        ):
            events = []
            async for event in OnboardingState.go_next.fn(harness):
                events.append(event)
        self.assertEqual(harness.current_step, 13)
        self.assertEqual(events, [OnboardingState.post_first_request])
        session.commit.assert_not_awaited()

    async def test_custom_skill_and_privacy_roundtrip(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.categories = [CATEGORY_OTHER]
        state.set_custom_skill("Bicycle repair, sewing, first aid")
        answers = json.loads(json.dumps(state._answers()))
        state._reset()
        state._apply_answers(answers, {})
        self.assertEqual(
            state._profile_skills(), "Bicycle repair, sewing, first aid"
        )
        state.current_step = 10
        self.assertTrue(state.can_continue)
        state.choose_location("off")
        self.assertEqual(state.location_pref, LOCATION_MODE_HIDDEN)
        self.assertTrue(state.can_continue)
        state.choose_location("approximate")
        state.choose_location(LOCATION_MODE_HIDDEN)
        self.assertEqual(state.location_pref, LOCATION_MODE_HIDDEN)
        self.assertTrue(state.can_continue)
        state.choose_location("approximate")
        self.assertTrue(state.can_continue)
        center = list(state.map_center)
        state.set_location_point(12.0, 45.0)
        self.assertTrue(state.can_continue)
        self.assertEqual(state.map_center, center)
        state.latitude = float("nan")
        self.assertTrue(state.can_continue)
