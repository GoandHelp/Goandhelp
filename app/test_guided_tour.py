import reflex as rx

import inspect
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.components import onboarding
from app.components.community_panel import folder_tab
from app.components.tour_pointer import (
    TOUR_POINTER_SCRIPT,
    TOUR_SCROLL_SCRIPT,
    tour_pointer,
)
from app.models import GUIDED_TOUR_LAST_STEP
from app.states.community_state import CommunityState
from app.states.discovery_state import DiscoveryState
from app.states.onboarding_state import (
    OnboardingState,
    TOUR_STEPS,
    TOUR_TOTAL_STEPS,
)
from app.states.profile_state import ProfileState


class GuidedTourTests(unittest.TestCase):
    def test_titles_copy_and_labels(self):
        self.assertEqual(TOUR_TOTAL_STEPS, 8)
        self.assertEqual(len(TOUR_STEPS), 8)
        self.assertEqual(
            [row["step"] for row in TOUR_STEPS], [str(n) for n in range(1, 9)]
        )
        self.assertEqual(
            [row["title"] for row in TOUR_STEPS],
            [
                "Your Profile",
                "Update your skills",
                "Search filters",
                "Request help and view upcoming help",
                "Message and accept help offers",
                "Community Forum",
                "Events",
                "Reviews",
            ],
        )
        self.assertEqual(
            TOUR_STEPS[4]["body"],
            "Message helpers and helpee's. Review offers and accept the helper who fits, confirm the task, time, place and reward together before meeting; an offer alone is not an agreement.",
        )
        self.assertEqual(
            TOUR_STEPS[0]["body"],
            "The place to update your Information, become a Premium member and read more about Go and Help",
        )
        self.assertEqual(
            TOUR_STEPS[1]["body"],
            "Choose the skills and knowledge you can share below. Relevant skills improve matching and help people trust that you can help.",
        )
        self.assertEqual(
            TOUR_STEPS[2]["body"],
            "Go or Get help with the toggle in search filters. Tailor your search criteria here then explore in map or list view",
        )
        self.assertEqual(
            TOUR_STEPS[3]["body"],
            "Manage your help requests and keep track of confirmed jobs, events and helpers.",
        )
        self.assertEqual(
            TOUR_STEPS[5]["body"],
            "Join Community Forum discussions to ask questions, share local knowledge and exchange ideas. Open a discussion to read replies and take part.",
        )
        self.assertEqual(
            TOUR_STEPS[6]["body"],
            "Discover or host Events for festivals, community projects, disaster relief and larger jobs. Bring people together, explore event details and coordinate helping as a group.",
        )
        self.assertEqual(
            TOUR_STEPS[7]["body"],
            "Explore received and given Reviews. After completed help, share honest ratings and experiences to build trust. Reviews help others choose confidently and contribute to your profile reputation.",
        )
        for word in (
            "festivals",
            "community projects",
            "disaster relief",
            "larger jobs",
            "host",
        ):
            self.assertIn(word, TOUR_STEPS[6]["body"])
        for word in (
            "received",
            "given",
            "trust",
            "ratings",
            "completed help",
            "profile reputation",
        ):
            self.assertIn(word, TOUR_STEPS[7]["body"])
        state = OnboardingState(_reflex_internal_init=True)
        for step in range(1, 9):
            state.tour_step = step
            self.assertEqual(state.tour_step_label, f"Tour {step} of 8")
            self.assertEqual(state.tour_is_last, step == 8)
            self.assertEqual(state.tour_card, TOUR_STEPS[step - 1])
        OnboardingState.restart_tour.fn(state)
        self.assertEqual(state.tour_step, 1)
        self.assertFalse(state.tour_complete)
        self.assertFalse(state.tour_hidden)

    def test_stable_callout_and_pointer(self):
        source = inspect.getsource(onboarding)
        self.assertNotIn("tour_number", source)
        self.assertNotIn("TOUR_POSITION", source)
        self.assertNotIn("tour_numbers", inspect.getsource(OnboardingState))
        classes = (
            f"{onboarding.TOUR_CARD_CLASS} {onboarding.TOUR_WRAPPER_CLASS}"
        )
        self.assertIsInstance(classes, str)
        for token in (
            "fixed",
            "left-1/2",
            "top-1/2",
            "-translate-x-1/2",
            "-translate-y-1/2",
            "bg-[#fff7e8]",
            "border-[#e08b12]",
            "safe-area-inset-bottom",
            "overflow-y-auto",
        ):
            self.assertIn(token, classes)
        self.assertIn('id="gah-tour-card"', source)
        self.assertIn("data-tour-focus", source)
        self.assertIn("data-tour-step", source)
        self.assertIn("gah-tour-pulse", source)
        self.assertIn("mask-image: radial-gradient", source)
        self.assertIn("prefers-reduced-motion: no-preference", source)
        self.assertIn('tour_is_last, "Finish", "Next"', source)
        pointer = str(tour_pointer())
        self.assertIn("pointer-events-none", pointer)
        self.assertIn("polyline", pointer)
        for token in (
            "getBoundingClientRect",
            "data-tour-target",
            "data-tour-focus",
            "MutationObserver",
            "ResizeObserver",
            "setAttribute('visibility', 'hidden')",
            "addEventListener('resize'",
            "addEventListener('scroll'",
            "removeEventListener('resize'",
            "removeEventListener('scroll'",
            "observer.disconnect()",
            "resize.disconnect()",
            "cancelAnimationFrame",
        ):
            self.assertIn(token, TOUR_POINTER_SCRIPT)
        self.assertIn("on_unmount", inspect.getsource(tour_pointer))
        self.assertNotIn("animate-bounce", source)
        self.assertTrue(onboarding.guided_tour().render())
        self.assertIn("p-[20px]", onboarding.TOUR_WRAPPER_CLASS)
        self.assertIn("backdrop-blur-[20px]", onboarding.TOUR_WRAPPER_CLASS)
        self.assertIn("pointer-events-none", onboarding.TOUR_WRAPPER_CLASS)
        self.assertNotIn("backdrop-blur", onboarding.TOUR_CARD_CLASS)
        self.assertIn("pointer-events-auto", onboarding.TOUR_CARD_CLASS)
        controls = inspect.getsource(onboarding.tour_controls)
        self.assertIn("grid-cols-[1fr_auto_1fr]", controls)
        self.assertIn("tour_step_label", controls)
        self.assertIn('aria_live="polite"', controls)
        self.assertIn("disabled=OnboardingState.tour_is_first", controls)
        card = inspect.getsource(onboarding.guided_tour)
        self.assertNotIn("tour_step_label", card)
        self.assertIn("mt-0 min-h-7 px-7 text-center text-base", card)
        for token in (
            "setTimeout",
            "clearTimeout",
            "gahTourScrollCleanup",
            "data-tour-target",
            "block: 'start'",
            "behavior: 'instant'",
            "scrollTo({top: 0",
            "new Event('resize')",
            "attempts < 30",
        ):
            self.assertIn(token, TOUR_SCROLL_SCRIPT)
        self.assertIn("gahTourScrollCleanup", inspect.getsource(tour_pointer))
        prompt = inspect.getsource(onboarding.tour_prompt)
        self.assertIn("Learn how to navigate the app", prompt)
        self.assertIn("Start tour", prompt)
        self.assertIn("dismiss_tour_prompt", prompt)
        self.assertIn('role="dialog"', prompt)
        self.assertIn('aria_labelledby="gah-tour-prompt-title"', prompt)

    def test_no_floating_search(self):
        from app.components.member_map import (
            tour_map_controls,
            member_filters_button,
        )

        source = inspect.getsource(tour_map_controls)
        self.assertNotIn("rx.el.form", source)
        self.assertNotIn("world_search", source)
        self.assertNotIn("WorldSearchState", source)
        self.assertEqual(TOUR_STEPS[2]["target"], "filters")
        self.assertIn(
            '"data-tour-target": "filters"',
            inspect.getsource(member_filters_button),
        )
        self.assertTrue(tour_map_controls().render())

    def test_targets_and_legacy_storage(self):
        self.assertEqual(
            [s["target"] for s in TOUR_STEPS],
            [
                "profile",
                "skills",
                "filters",
                "help",
                "inbox",
                "community-community",
                "community-events",
                "community-reviews",
            ],
        )
        for value in ("community", "events", "reviews"):
            self.assertIn(
                f"community-{value}",
                str(
                    folder_tab(
                        {
                            "value": value,
                            "label": value,
                            "icon": "users-round",
                        }
                    )
                ),
            )
        for file, target in (
            ("profile_tabs.py", "skills"),
            ("member_map.py", "mode"),
            ("member_map.py", "filters"),
            ("discover_panel.py", "view-toggle"),
            ("bottom_nav.py", "profile"),
        ):
            self.assertIn(
                f'"data-tour-target": "{target}"',
                Path(f"app/components/{file}").read_text(),
            )
        dock = Path("app/components/bottom_nav.py").read_text()
        self.assertIn('f"{tour_target}{value}"', dock)
        for target in ("help", "inbox", "community"):
            self.assertIn(f'"{target}"', dock)
        source = inspect.getsource(OnboardingState)
        self.assertIn('"step": min(step, GUIDED_TOUR_LAST_STEP)', source)
        self.assertIn(
            'answers = {**self._answers(), "tour_step": step}', source
        )
        self.assertLess(GUIDED_TOUR_LAST_STEP, TOUR_TOTAL_STEPS)
        state = OnboardingState(_reflex_internal_init=True)
        for step in (7, 8):
            state._apply_answers({"tour_step": step}, {})
            self.assertEqual(state.tour_step, step)
            self.assertEqual(state._answers()["tour_step"], step)
        state._apply_answers({"tour_step": 12}, {})
        self.assertEqual(state.tour_step, 8)


class GuidedTourPromptTests(unittest.TestCase):
    def test_start_and_close_are_mutually_exclusive(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.has_row = True
        state.is_complete = True
        state.tour_prompt_visible = True
        self.assertFalse(state.tour_visible)
        events = OnboardingState.start_tour.fn(state)
        self.assertFalse(state.tour_prompt_visible)
        self.assertTrue(state.tour_visible)
        self.assertEqual(state.tour_step, 1)
        self.assertEqual(events[0], OnboardingState.apply_tour_target)
        self.assertEqual(
            str(events[1]), str(OnboardingState.persist_tour(1, False))
        )
        state._reset()
        state.has_row = True
        state.is_complete = True
        state.tour_prompt_visible = True
        self.assertEqual(
            OnboardingState.dismiss_tour_prompt.fn(state),
            OnboardingState.persist_tour_hidden,
        )
        self.assertTrue(state.tour_hidden)
        self.assertFalse(state.tour_prompt_visible)
        self.assertFalse(state.tour_visible)
        self.assertEqual(state.tour_step, 0)
        self.assertNotEqual(OnboardingState.start_tour.fn(state), events)
        OnboardingState.restart_tour.fn(state)
        self.assertTrue(state.tour_visible)
        self.assertFalse(state.tour_hidden)
        state._reset()
        self.assertFalse(state.tour_prompt_visible)

    def test_reload_honors_prompt_dismissal_and_existing_tour(self):
        state = OnboardingState(_reflex_internal_init=True)
        for answers, expected_prompt in (
            ({"setup_version": 3, "tour_step": 0, "tour_hidden": False}, True),
            ({"setup_version": 3, "tour_step": 0, "tour_hidden": True}, False),
            ({"setup_version": 3, "tour_step": 3, "tour_hidden": False}, False),
            ({"setup_version": 3, "tour_step": 1}, False),
        ):
            state._apply_progress_row(
                (13, "1,13", json.dumps(answers), "{}", "2026-01-01", 0, None)
            )
            self.assertEqual(state.tour_prompt_visible, expected_prompt)
            self.assertEqual(
                state.tour_visible,
                answers.get("tour_step") == 3,
            )


class GuidedTourRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_dismissal_persists_only_tour_visibility(self):
        state = OnboardingState(_reflex_internal_init=True)
        state.tour_hidden = True
        session = AsyncMock()
        session.__aenter__.return_value = session
        with (
            patch.object(
                OnboardingState,
                "get_state",
                AsyncMock(
                    return_value=SimpleNamespace(
                        subscriber_id="7", is_signed_in=True
                    )
                ),
            ),
            patch.object(rx, "asession", return_value=session),
        ):
            await OnboardingState.persist_tour_hidden.fn(state)
        sql, params = session.execute.await_args.args
        self.assertIn("answers_json", str(sql))
        self.assertEqual(json.loads(params["draft"]), {"tour_hidden": True})
        session.commit.assert_awaited_once()

    async def test_every_live_destination(self):
        profile = SimpleNamespace(active_tab="", skills_open=False)
        discovery = SimpleNamespace(filter_panel_open=False)
        community = SimpleNamespace(set_section=Mock(return_value=[]))
        states = {
            ProfileState: profile,
            DiscoveryState: discovery,
            CommunityState: community,
        }
        for step in range(1, 9):
            fake = SimpleNamespace(
                tour_step=step,
                get_state=AsyncMock(side_effect=lambda cls: states[cls]),
            )
            events = await OnboardingState.apply_tour_target.fn(fake)
            self.assertIn(TOUR_STEPS[step - 1]["target"], str(events[-1]))
            expected = (
                ["profile"] * 2
                + ["discover", "help", "inbox"]
                + ["community"] * 3
            )
            self.assertEqual(profile.active_tab, expected[step - 1])
            self.assertEqual(discovery.filter_panel_open, step == 3)
            self.assertEqual(profile.skills_open, step == 2)
            if step >= 6:
                community.set_section.assert_called_with(
                    {
                        6: "community",
                        7: "events",
                        8: "reviews",
                    }[step]
                )
        source = inspect.getsource(CommunityState.set_section.fn)
        for handler in (
            "load_topics",
            "load_events",
            "mark_events_read",
            "mark_reviews_read",
        ):
            self.assertIn(handler, source)

    async def test_finish_returns_to_map_and_persists(self):
        profile = SimpleNamespace(active_tab="community", skills_open=True)
        discovery = SimpleNamespace(filter_panel_open=True)
        states = {ProfileState: profile, DiscoveryState: discovery}
        fake = SimpleNamespace(
            tour_step=8,
            tour_complete=False,
            tour_hidden=True,
            get_state=AsyncMock(side_effect=lambda cls: states[cls]),
        )
        with patch.object(rx, "toast") as toast:
            events = await OnboardingState.tour_finish.fn(fake)
        toast.assert_not_called()
        self.assertTrue(fake.tour_complete)
        self.assertFalse(fake.tour_hidden)
        self.assertEqual(fake.tour_step, 8)
        self.assertEqual(profile.active_tab, "discover")
        self.assertFalse(profile.skills_open)
        self.assertFalse(discovery.filter_panel_open)
        self.assertIn("persist_tour", str(events[0]))
        self.assertEqual(len(events), 1)
        self.assertEqual(
            str(events[0]), str(OnboardingState.persist_tour(8, True))
        )
        state = OnboardingState(_reflex_internal_init=True)
        state.tour_step = 7
        OnboardingState.tour_next.fn(state)
        self.assertEqual(state.tour_step, 8)
        self.assertEqual(
            OnboardingState.tour_next.fn(state), OnboardingState.tour_finish
        )
        state.tour_step = 1
        OnboardingState.tour_back.fn(state)
        self.assertEqual(state.tour_step, 1)


if __name__ == "__main__":
    unittest.main()
