import reflex as rx

import inspect
import unittest
from pathlib import Path

from app.states.discovery_state import DiscoveryState, EMPTY_HELPER, EMPTY_POST
from app.components.discover_panel import (
    detail_panel,
    helper_detail,
    detail_rating,
    offer_estimates,
)
from app.components.event_cards import event_detail_sheet
from app.components.openfreemap import _MAP_COMPONENT


class MapMemberSheetTests(unittest.TestCase):
    def test_mode_specific_markers(self):
        state = DiscoveryState(_reflex_internal_init=True)
        state.helpers = [
            {
                **EMPTY_HELPER,
                "id": 7,
                "name": "Member",
                "image_url": "https://example.invalid/member-photo.png",
            }
        ]
        state.posts = [{**EMPTY_POST, "id": 8, "poster_id": 9}]
        state.map_mode = "get"
        self.assertEqual([m["kind"] for m in state.map_markers], ["helper"])
        self.assertEqual(
            state.helper_map_markers[0]["image_url"],
            "https://example.invalid/member-photo.png",
        )
        state.map_mode = "give"
        self.assertEqual([m["kind"] for m in state.map_markers], ["job"])
        source = Path("app/components/member_map.py").read_text()
        self.assertNotIn("home_map_markers", source)
        self.assertIn('map_utility_icon("cog")', source)

    def test_load_helpers_declares_subscriber_alias_before_profile_join(self):
        source = inspect.getsource(DiscoveryState._load_helpers)
        self.assertIn(
            "FROM skillkind_subscriber s\n                        LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id",
            source,
        )
        self.assertNotIn(
            "FROM\n                        LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id",
            source,
        )

    def test_load_jobs_declares_post_alias_before_subscriber_join(self):
        source = inspect.getsource(DiscoveryState._load_jobs)
        main_query = source.split("SELECT p.id, p.title", 1)[1].split(
            "            count_rows =", 1
        )[0]
        self.assertRegex(
            main_query,
            r"FROM\s+skillkind_help_post\s+p\s+"
            r"JOIN\s+skillkind_subscriber\s+s\s+ON\s+s\.id\s*=\s*p\.author_id\b",
        )

    def test_completion_and_estimate_contracts(self):
        source = Path("app/states/discovery_state.py").read_text()
        main = source[source.index("    async def _load_jobs") :]
        shared = source[
            source.index("    async def open_shared_post") : source.index(
                "    def clear_selection"
            )
        ]
        main_where, counts = main.split("            count_rows =", 1)
        counts = counts.split("            post_ids =", 1)[0]
        direct = inspect.getsource(DiscoveryState.open_direct_help.fn)
        for query in (main_where, counts, shared, direct):
            self.assertEqual(query.count("skillkind_completed_task"), 1)
            self.assertRegex(
                query,
                r"AND NOT EXISTS\s*\(\s*SELECT 1 FROM skillkind_completed_task ct\s+WHERE ct\.post_id = p\.id\s*\)",
            )
        self.assertIn("COALESCE(p.reward_currency, 'USD')", main)
        self.assertEqual(DiscoveryState._normalized_offer_price("12"), "12")
        estimate = inspect.getsource(offer_estimates)
        self.assertIn("Give your cost estimate", estimate)
        self.assertIn('selected_post["reward_currency"]', estimate)
        state = DiscoveryState(_reflex_internal_init=True)
        state.direct_post_id = 1
        state.direct_draft = "Could you help?"
        state.direct_warning = "Make sure this person has the skills and knowledge required for this job"
        self.assertTrue(state.direct_can_send)

    def test_sheets_and_rating_render(self):
        for component in (
            detail_panel,
            helper_detail,
            event_detail_sheet,
            offer_estimates,
        ):
            self.assertIsInstance(component(), rx.Component)
        self.assertIsInstance(
            detail_rating(rx.Var.create(4.0), rx.Var.create(3)), rx.Component
        )
        for component in (detail_panel, event_detail_sheet):
            source = inspect.getsource(component)
            for token in (
                "fixed top-0 right-0",
                "max-w-[22rem]",
                "sm:max-w-[26rem]",
                "rounded-bl-2xl",
                "overflow-y-auto",
                "env(safe-area-inset-bottom)",
            ):
                self.assertIn(token, source)
        helper = inspect.getsource(helper_detail)
        self.assertNotIn("This neighbour", helper)
        self.assertNotIn("Given ", helper)
        self.assertNotIn("Got ", helper)
        self.assertLess(
            helper.index("direct_help_section()"),
            helper.index("original_language_disclosure("),
        )
        self.assertNotIn("points", helper)
        self.assertIn("range(1, 6)", inspect.getsource(detail_rating))

    def test_marker_and_dock(self):
        helper = _MAP_COMPONENT.split('marker.kind === "helper") {', 1)[
            1
        ].split('marker.kind === "job"', 1)[0]
        self.assertIn("width:45px;height:45px", helper)
        self.assertIn("border:0;", helper)
        self.assertIn("box-shadow:none", helper)
        self.assertIn("marker.image_url && marker.image_url.length > 0", helper)
        self.assertIn("photo.src = marker.image_url", helper)
        self.assertIn(
            'photo.style.cssText = "width:100%;height:100%;object-fit:cover;border-radius:999px;"',
            helper,
        )
        self.assertIn("photo.onerror", helper)
        self.assertIn(
            'pin.innerHTML = goAndHelpIconSvg("hand-helping", 30)', helper
        )
        self.assertIn(
            'if (marker.selected) pin.style.outline = "2px solid #e08b12"',
            helper,
        )
        self.assertIn('el.setAttribute("aria-label", name)', _MAP_COMPONENT)
        dock = Path("app/components/bottom_nav.py").read_text()
        self.assertIn("border-[3px] border-white", dock)
        self.assertNotIn("w-full border-t", dock)

    def test_public_loading_privacy(self):
        source = Path("app/states/discovery_state.py").read_text()
        public = source.split("    async def open_member_profile", 1)[1].split(
            "    # ---", 1
        )[0]
        for private in ("pr.latitude", "pr.longitude", "s.email", "pr.phone"):
            self.assertNotIn(private, public)
        self.assertIn("s.is_active = TRUE", public)
        self.assertRegex(
            public, r"AND\s+\{not_blocked_author_sql\(['\"]s\.id['\"]\)\}"
        )
        self.assertIn('"member_id": member_id', public)
        self.assertIn("tasks_received_count", public)
        self.assertIn('seed = f"member-{member_id}"', public)
        for path in Path("app/components").glob("*.py"):
            self.assertNotIn("notionists-neutral", path.read_text(), str(path))


if __name__ == "__main__":
    unittest.main()
