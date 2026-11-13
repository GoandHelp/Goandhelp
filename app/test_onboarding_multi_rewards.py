import reflex as rx

import inspect
import json
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.components import onboarding as ui
from app.components import request_draft as fields
from app.states.onboarding_state import OnboardingState
from app.states.help_hub_state import REWARD_CHOICES
from app.test_first_request_onboarding import seed_draft
from app.request_draft import validate_request


class MultiRewardTests(unittest.IsolatedAsyncioTestCase):
    def state(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        seed_draft(state)
        state.request_reward = ""
        return state

    async def test_toggle_details_roundtrip_and_guards(self):
        state = self.state()
        with patch.object(
            OnboardingState, "_save_request_draft", AsyncMock()
        ) as save:
            for key in ("meal", "money", "other_reward"):
                await OnboardingState.toggle_request_reward.fn(state, key)
            await OnboardingState.set_request_reward_spec.fn(
                state, "meal", "A warm lunch"
            )
            await OnboardingState.set_request_reward_spec.fn(
                state, "other_reward", "x" * 200
            )
            self.assertEqual(
                len(state.request_reward_specs["other_reward"]), 120
            )
            answers = json.loads(json.dumps(state._request_answers()))
            state._reset()
            state._apply_answers(answers, {})
            self.assertEqual(
                list(state.request_rewards), ["meal", "money", "other_reward"]
            )
            self.assertEqual(
                dict(state.request_reward_specs),
                answers["request_reward_specs"],
            )
            await OnboardingState.toggle_request_reward.fn(state, "meal")
            self.assertNotIn("meal", state.request_reward_specs)
            before = save.await_count
            state.saving = True
            await OnboardingState.toggle_request_reward.fn(state, "money")
            await OnboardingState.set_request_reward_spec.fn(
                state, "other_reward", "Changed"
            )
            self.assertEqual(save.await_count, before)

    def test_legacy_and_free_restore(self):
        state = self.state()
        state._apply_answers(
            {
                "request_reward": "other_reward",
                "request_other": "Homegrown apples",
            },
            {},
        )
        self.assertEqual(list(state.request_rewards), ["other_reward"])
        self.assertEqual(
            state.request_reward_specs["other_reward"], "Homegrown apples"
        )
        state._apply_answers(
            {"request_rewards": [], "request_reward": "money"}, {}
        )
        self.assertEqual(list(state.request_rewards), [])
        self.assertEqual(state.request_reward, "")
        self.assertEqual(
            state._reward_payload({"reward_details": "Free"}),
            {"reward_details": "Free"},
        )

    async def test_numeric_payload_validation_and_multi_sql_parameters(self):
        state = self.state()
        state.request_rewards = ["meal", "money", "other_reward"]
        state.request_reward_specs = {
            "meal": "Vegetarian lunch",
            "other_reward": "Fresh apples",
        }
        with patch.object(OnboardingState, "_save_request_draft", AsyncMock()):
            for number in (25, 25.5):
                await OnboardingState.set_request_field.fn(
                    state, "request_budget", number
                )
                params = state._reward_payload({})
                self.assertEqual(params["reward_value"], Decimal(str(number)))
                self.assertEqual(params["reward_type"], "dinner")
                self.assertEqual(
                    params["reward_types"], "meal,money,other_reward"
                )
                self.assertEqual(params["other_details"], "Fresh apples")
                self.assertIn("Vegetarian lunch", params["reward_details"])
        state.request_quote = True
        state.request_rewards = [item["value"] for item in REWARD_CHOICES]
        state.request_reward_specs = {
            key: "a" * 120 for key in state.request_rewards if key != "money"
        }
        params = state._reward_payload({})
        self.assertLessEqual(len(params["reward_details"]), 255)
        self.assertIn("Helper quote requested", params["reward_details"])
        for item in REWARD_CHOICES:
            self.assertIn(item["label"], params["reward_details"])
        state.request_reward_specs["meal"] = ""
        with self.assertRaisesRegex(ValueError, "A meal"):
            state._reward_payload({})

    def test_summary_preserves_labels_and_money_in_every_selection(self):
        state = self.state()
        keys = [item["value"] for item in REWARD_CHOICES]
        for mask in range(1, 1 << len(keys)):
            state.request_rewards = [
                key for index, key in enumerate(keys) if mask & (1 << index)
            ]
            state.request_reward_specs = {
                key: "x" * 120
                for key in state.request_rewards
                if key != "money"
            }
            for quote in (False, True):
                state.request_quote = quote
                summary = state._reward_payload({})["reward_details"]
                self.assertLessEqual(len(summary), 255)
                for item in REWARD_CHOICES:
                    if item["value"] in state.request_rewards:
                        self.assertIn(item["label"], summary)
                if "money" in state.request_rewards:
                    expected = (
                        "Money (EUR — Helper quote requested)"
                        if quote
                        else "Money (EUR 25.50 budget)"
                    )
                    self.assertIn(expected, summary)

    def test_celebration_markers_are_synchronous_and_temporary(self):
        state = self.state()
        getter = OnboardingState.celebration_map_markers.fget
        self.assertFalse(inspect.iscoroutinefunction(getter))
        self.assertNotIn("DiscoveryState", inspect.getsource(getter))
        self.assertEqual(getter(state), [])
        state.first_request_post_id = 88
        state.request_latitude = 51.5
        state.request_longitude = -0.12
        self.assertEqual(getter(state), [])
        state.celebration_pending = True
        markers = getter(state)
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["id"], "p88")
        self.assertEqual(markers[0]["lat"], 51.5)
        self.assertEqual(markers[0]["lng"], -0.12)
        state.celebration_pending = False
        self.assertEqual(getter(state), [])

    def test_visual_and_transition_contracts(self):
        source = inspect.getsource(fields.compact_request_fields)
        self.assertNotIn('type="number"', source)
        for token in (
            'type="text"',
            'input_mode="decimal"',
            "pattern=",
            'auto_complete="off"',
        ):
            self.assertIn(token, source)
        rows = inspect.getsource(fields.onboarding_reward_row)
        for token in (
            "rx.el.strong",
            "font-bold",
            "font-normal",
            " – ",
            'role="checkbox"',
            "aria_checked",
        ):
            self.assertIn(token, rows)
        self.assertIn(
            "rx.foreach(REWARD_CHOICES, onboarding_reward_row)",
            inspect.getsource(fields.onboarding_rewards),
        )
        self.assertIn(
            "Please specify for each one below",
            inspect.getsource(fields.onboarding_rewards),
        )
        self.assertNotIn("Your first request is posted", inspect.getsource(ui))
        celebration = inspect.getsource(ui.first_request_celebration)
        self.assertIn("text-white", celebration)
        self.assertNotIn("bg-white", celebration)
        self.assertNotIn("rounded", celebration)
        self.assertIn("duration-600", celebration)
        self.assertIn("gah-gentle-spark", celebration)
        self.assertIn("prefers-reduced-motion: no-preference", celebration)
        self.assertIn("motion-reduce:", inspect.getsource(ui.fireworks_burst))
        timing = inspect.getsource(OnboardingState.celebrate_first_request.fn)
        self.assertLess(
            timing.index("sleep(2.0)"),
            timing.index("self.celebration_fading = True"),
        )
        self.assertLess(
            timing.index("sleep(0.6)"),
            timing.index("self.celebration_pending = False"),
        )
        post = inspect.getsource(OnboardingState.post_first_request.fn)
        self.assertIn("params = self._reward_payload(params)", post)
        self.assertNotIn("yield HelpHubState", post)
        preload = inspect.getsource(ui.onboarding_flow)
        self.assertEqual(preload.count('rel="preload"'), 1)
        self.assertEqual(preload.count('rel="prefetch"'), 1)
        self.assertTrue(
            all(".png" in value for value in ui.BACKGROUND_CLASSES.values())
        )


if __name__ == "__main__":
    unittest.main()
