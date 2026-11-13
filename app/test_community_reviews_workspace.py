import inspect
import unittest

from test_utils import run_event

from app.components import (
    community_panel,
    event_cards,
    messages_panel,
    reviews_section,
)
from app.states.community_state import CommunityState
from app.states.messaging_state import EMPTY_THREAD, MessagingState
from app.states.profile_state import ProfileState


class CommunityReviewsWorkspaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_received_disclosures_are_independent_and_guard_unknown_ids(
        self,
    ):
        state = ProfileState()
        base = {
            "reviewer_id": 1,
            "reviewer_name": "Sam",
            "reviewer_seed": "1",
            "reviewer_avatar": "",
            "job_title": "Repair",
            "reviewer_verified": False,
            "rating": 4,
            "percent": 80,
            "comment": "",
            "response": "",
            "kindness_flag": False,
            "created": "Today",
            "categories": [],
        }
        state.received_reviews = [{**base, "id": 11}, {**base, "id": 12}]
        await run_event(state.toggle_received_review, 11)
        await run_event(state.toggle_received_review, 12)
        self.assertEqual(state.open_received_review_ids, [11, 12])
        await run_event(state.toggle_received_review, 11)
        self.assertEqual(state.open_received_review_ids, [12])
        await run_event(state.toggle_received_review, 99)
        self.assertEqual(state.open_received_review_ids, [12])

    async def test_pending_selection_keeps_existing_review_workflow(self):
        state = MessagingState()
        poster = {**EMPTY_THREAD, "id": 1, "task_id": 11, "my_role": "poster"}
        helper = {**EMPTY_THREAD, "id": 2, "task_id": 12, "my_role": "helper"}
        state.review_targets = [poster, helper]
        await run_event(state.close_review_target)
        self.assertFalse(state.review_target_open)
        self.assertEqual(
            [target["task_id"] for target in state.review_targets], [11, 12]
        )

    def test_review_composition_and_accessibility(self):
        summary = inspect.getsource(reviews_section.your_reviews_header)
        self.assertIn("ProfileState.combined_rating_avg", summary)
        self.assertIn("ProfileState.combined_star_states", summary)
        self.assertIn('"Review received"', summary)
        self.assertIn('"Reviews received"', summary)
        screen = inspect.getsource(reviews_section.community_reviews_section)
        self.assertLess(
            screen.index('"To review"'),
            screen.index("received_reviews_section()"),
        )
        self.assertIn("review_section()", screen)
        self.assertIn("MessagingState.load_review_targets", screen)
        self.assertNotIn(
            "Reviews about the help you give and receive live here.", screen
        )
        received = inspect.getsource(reviews_section.received_review_card)
        self.assertIn("aria_expanded=", received)
        self.assertIn("aria_controls=", received)
        self.assertIn("toggle_received_review", received)
        pending = inspect.getsource(messages_panel.pending_review_card)
        self.assertIn("review_form()", pending)
        self.assertIn("select_review_target", pending)
        self.assertIn("other_rating_count", pending)
        self.assertIn("aria_controls=", pending)
        self.assertIn('target["my_role"]', pending)
        self.assertNotIn("recently has completed your help request", pending)
        self.assertTrue(str(reviews_section.community_reviews_section()))

    def test_forum_keeps_gate_and_events_are_free_with_centered_actions(self):
        planner = inspect.getsource(event_cards.planner_block)
        forum = inspect.getsource(community_panel.community_section)
        self.assertIn("items-center justify-center gap-2 text-center", planner)
        self.assertIn("items-center justify-center gap-2 text-center", forum)
        self.assertIn(
            "EventState.toggle_composer",
            inspect.getsource(event_cards.planner_control),
        )
        self.assertIn("CommunityState.topic_allowance_available", forum)
        self.assertIn("CommunityState.toggle_composer", forum)
        self.assertIn(
            "border border-[#fba922]", community_panel.FOLDER_TAB_ACTIVE
        )
        self.assertNotIn("shadow", community_panel.FOLDER_TAB_ACTIVE)
        self.assertIn("shadow-", community_panel.FOLDER_TAB_INACTIVE)
        self.assertIn(
            "aria_current=", inspect.getsource(community_panel.folder_tab)
        )
        self.assertEqual(
            [item["label"] for item in CommunityState().sections],
            ["Forum", "Events", "Reviews"],
        )
        self.assertTrue(str(event_cards.planner_block()))
        self.assertTrue(str(community_panel.community_section()))


if __name__ == "__main__":
    unittest.main()
