import reflex as rx

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).parent


def source(path: str) -> str:
    return (ROOT / path).read_text()


def function(path: str, name: str) -> str:
    code = source(path)
    node = next(
        n
        for n in ast.walk(ast.parse(code))
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == name
    )
    return ast.get_source_segment(code, node) or ""


class InformationSheetContracts(unittest.TestCase):
    def test_job_structure(self):
        path = "components/discover_panel.py"
        panel = source(path)
        for removed in (
            "Job " + "passport",
            "Practical " + "snapshots",
            "Read the details, choose when",
            "Send to " + "Inbox",
        ):
            self.assertNotIn(removed, panel)
        body = function(path, "detail_body")
        self.assertNotIn("category_icon(", body)
        self.assertNotIn('selected_post["category_chips"]', body)
        order = [
            "poster_card()",
            'selected_post["description"]',
            "passport_photos()",
            '"Category"',
            "request_where_row()",
            '"When"',
            '"Reward"',
            '"Duration"',
            "accept_section()",
            "request_footer_actions()",
        ]
        positions = [body.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(body.count('"Reward"'), 1)
        metadata = body[
            body.index("request_where_row()") : body.index("accept_section()")
        ]
        self.assertIn("rounded-2xl", metadata)
        self.assertNotIn("bg-[#fafafa]", metadata)
        poster = function(path, "poster_card")
        for token in (
            "poster_image",
            "poster_verified",
            "poster_name",
            "poster_headline",
            "poster_languages",
            'selected_post["title"]',
            "detail_rating",
        ):
            self.assertIn(token, poster)
        footer = function(path, "request_footer_actions")
        self.assertIn("REPORT_TARGET_JOB_MESSAGE", footer)
        self.assertIn("detail_contact", footer)
        self.assertLess(
            body.index("accept_section()"),
            body.index("request_footer_actions()"),
        )
        self.assertNotIn("block_member_button", poster)
        self.assertNotIn("email", poster)
        photos = function(path, "passport_photos")
        self.assertIn("snap-x snap-mandatory", photos)
        self.assertNotIn("camera", photos)

    def test_close_and_helper_hierarchy(self):
        path = "components/discover_panel.py"
        close = function(path, "detail_panel")
        for token in (
            "size-8",
            "rounded-full",
            "bg-[#fff7e8]",
            "border-[#f7d9a0]",
            "text-[#b86e08]",
            "focus-visible:ring-2",
            'aria_label="Close details"',
        ):
            self.assertIn(token, close)
        self.assertNotIn('"Close",', close)
        helper = function(path, "helper_detail")
        tokens = [
            'selected_helper["image_url"]',
            'selected_helper["name"]',
            'selected_helper["handle"]',
            "Joined ",
            "detail_rating",
            'selected_helper["headline"]',
            '"Skills"',
            '"Availability"',
            "direct_help_section()",
            "original_language_disclosure(",
        ]
        positions = [helper.index(token) for token in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("Given ", helper)
        self.assertNotIn("Got ", helper)
        self.assertIn("REPORT_TARGET_PROFILE", helper)
        self.assertIn("Skills and knowledge", helper)
        self.assertLess(
            helper.index('selected_helper["handle"]'),
            helper.index("Skills and knowledge"),
        )
        self.assertLess(
            helper.index("Skills and knowledge"), helper.index('"Availability"')
        )
        self.assertNotIn("detail_contact(", helper)
        for private in ("email", "phone", "latitude", "longitude"):
            self.assertNotIn(private, helper)
        for token in (
            "report_button(",
            "block_member_button(",
            "ContactsState.send_request(",
            "ContactsState.is_requesting",
            "ContactsState.error",
            "ContactsState.success",
            "flex w-full flex-wrap items-center justify-center",
        ):
            self.assertIn(token, helper)
        self.assertLess(
            helper.index("original_language_disclosure("),
            helper.index("block_member_button("),
        )

    def test_inline_composers(self):
        path = "components/discover_panel.py"
        offer = function(path, "offer_help_section")
        self.assertNotIn("DiscoveryState.offer_open", offer)
        self.assertLess(
            offer.index("Offer how you can help"),
            offer.index("offer_estimates()"),
        )
        self.assertLess(
            offer.index("offer_estimates()"), offer.index('"Offer help"')
        )
        self.assertIn("w-fit", offer)
        estimates = function(path, "offer_estimates")
        for token in (
            "allow_price_quote",
            "allow_duration_estimate",
            "Give your cost estimate",
            "Give your duration estimate",
        ):
            self.assertIn(token, estimates)
        direct = function(path, "direct_help_section")
        self.assertIn("Send request", direct)
        self.assertIn("w-fit", direct)
        panel = function(path, "detail_panel")
        self.assertIn("success_banner(DiscoveryState.success)", panel)
        self.assertIn("error_banner(DiscoveryState.error)", panel)

    def test_handlers_and_authoritative_fields(self):
        path = "states/discovery_state.py"
        for name in ("_send_offer", "_send_direct_help"):
            handler = function(path, name)
            self.assertNotIn("focus_thread", handler)
            self.assertNotIn("active_tab", handler)
            self.assertNotIn("rx.redirect", handler)
            self.assertIn("are_members_blocked", handler)
            self.assertIn("skillkind_job_application", handler)
            self.assertIn("skillkind_member_notification", handler)
            self.assertIn("skillkind_message", handler)
            self.assertIn("self.success", handler)
        offer = function(path, "_send_offer")
        for field in (
            "reward_types",
            "reward_type",
            "reward_value",
            "reward_details",
            "duration_minutes",
            "reward_currency",
        ):
            self.assertIn(field, offer)
        self.assertIn(
            "self._offer_quote_lines(authoritative_post,",
            "".join(offer.split()),
        )
        self.assertIn("yield DiscoveryState.load_jobs", offer)
        self.assertIn("Offer sent to", offer)
        self.assertIn("Request sent to", function(path, "_send_direct_help"))
        report = source("states/content_report_state.py")
        self.assertIn("FROM skillkind_help_post WHERE id = :tid", report)
        self.assertIn("SELECT author_id", report)
        model = source("models.py")
        self.assertIn('REPORT_TARGET_JOB_MESSAGE = "job_message"', model)
        self.assertIn('REPORT_TARGET_JOB_MESSAGE: "Help request"', model)
        self.assertIn(
            "target_type IN ({_CONTENT_REPORT_TARGET_TYPES_SQL})", model
        )

    def test_job_report_existing_schema_target(self):
        from app.models import (
            CONTENT_REPORT_TARGET_TYPES,
            CONTENT_REPORT_TARGET_LABELS,
            REPORT_TARGET_JOB_MESSAGE,
            _CONTENT_REPORT_TARGET_TYPES_SQL,
        )
        from app.states.content_report_state import _TARGET_QUERIES

        self.assertEqual(REPORT_TARGET_JOB_MESSAGE, "job_message")
        self.assertEqual(
            CONTENT_REPORT_TARGET_TYPES,
            [
                "profile",
                "community_topic",
                "community_comment",
                "contact_message",
                "noncontact_message",
                "job_message",
            ],
        )
        self.assertNotIn("help_post", CONTENT_REPORT_TARGET_LABELS)
        self.assertNotIn("'help_post'", _CONTENT_REPORT_TARGET_TYPES_SQL)
        self.assertNotIn("help_post", _TARGET_QUERIES)
        self.assertEqual(
            " ".join(_TARGET_QUERIES[REPORT_TARGET_JOB_MESSAGE].split()),
            "SELECT author_id, LEFT(COALESCE(title, ''), 500) "
            "FROM skillkind_help_post WHERE id = :tid",
        )
        poster = function(
            "components/discover_panel.py", "request_footer_actions"
        )
        calls = [
            node
            for node in ast.walk(ast.parse(poster))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "report_button"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            [ast.unparse(arg) for arg in calls[0].args],
            [
                "REPORT_TARGET_JOB_MESSAGE",
                "DiscoveryState.selected_post['id']",
                "DiscoveryState.selected_post['title']",
            ],
        )
        for path in (
            "models.py",
            "states/content_report_state.py",
            "components/discover_panel.py",
        ):
            self.assertNotIn("REPORT_TARGET_HELP_POST", source(path))

    def test_unlimited_history_only(self):
        history = function(
            "states/help_hub_state.py", "_load_completed_history"
        )
        self.assertNotIn("LIMIT 40", history)
        self.assertIn("LIMIT 60", history)
        self.assertIn("DISTINCT ON (ct.helper_id)", history)
        self.assertIn(
            "ORDER BY latest.completed_at DESC NULLS LAST, latest.id DESC",
            history,
        )
        self.assertIn("LIMIT 40", source("states/admin_state.py"))
        self.assertIn("LIMIT 40", source("states/saved_search_state.py"))
        requests = function("components/help_hub_panel.py", "help_hub_panel")
        self.assertNotIn("past_helpers_section()", requests)
        self.assertNotIn("completed_jobs_section()", requests)


if __name__ == "__main__":
    unittest.main()
