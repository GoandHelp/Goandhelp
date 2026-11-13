import reflex as rx

import ast
import datetime
import inspect
import unittest

from app.components import (
    help_hub_panel as hub,
    event_cards,
    saved_items,
    header,
)
from app.components.request_heading import request_heading
from app.states.help_post_state import HelpPostState, RecentPost
from app.states.help_hub_state import HelpHubState
from app.app import theme_overrides


class RequestsPolishTests(unittest.TestCase):
    def test_hero_and_orange_tiles(self):
        button = hub.post_help_section().children[0]
        hero = str(button)
        button_classes = str(button.class_name).split()
        for token in (
            "w-fit",
            "mx-auto",
            "min-h-0",
            "justify-center",
            "bg-[#fba922]",
            "LucideArrowRight",
            "text-center",
            "aria-controls",
            "aria-expanded",
            "gah-request-ask",
            "toggle_form",
        ):
            self.assertIn(token, hero)
        self.assertNotIn(
            "Tell the community what you need, when, and what you can offer back.",
            hero,
        )
        for token in (
            "w-full",
            "min-h-24",
            "overflow-hidden",
            "w-screen",
            "h-24",
        ):
            self.assertNotIn(token, button_classes)
        css = str(theme_overrides())
        map_css = __import__("pathlib").Path("assets/map.css").read_text()
        self.assertNotIn("gah-ask-light-line", map_css)
        self.assertNotIn(".gah-request-ask::after", map_css)
        self.assertIn("button.gah-request-ask", css)
        hand = str(hub.green_icon_tile("hand-helping"))
        for token in ("bg-[#fff7e8]", "text-[#e08b12]", "border-[#e08b12]"):
            self.assertIn(token, hand)
        self.assertIn("text-[#b86e08]", str(hub.counts_summary()))
        summary = str(hub.help_summary_card("help given", rx.Var.create(2)))
        self.assertNotIn("bg-[#fff7e8]", summary)
        self.assertIn("rounded-xl", summary)
        self.assertIn("bg-white", summary)
        self.assertIn("shadow-[0_2px_12px_rgba(17,24,39,0.10)]", summary)
        self.assertIn("text-[#e08b12]", summary)
        for wording in (
            " help given",
            " help received",
            "Helped",
            "Received help",
            "time",
            "times",
        ):
            self.assertIn(wording, inspect.getsource(hub.help_summary_card))
        self.assertIn("text-base", summary)
        self.assertIn("sm:text-lg", summary)
        self.assertIn("rx.el.span", inspect.getsource(hub.help_summary_card))
        row = str(hub.help_summary_row())
        for token in ("grid-cols-2", "gap-x-6", "bg-white", "bg-transparent"):
            self.assertIn(token, row)
        self.assertNotIn("grid-cols-1", row)
        outer = hub.help_summary_row()
        self.assertEqual(len(outer.children), 2)
        for token in ("rounded", "border", "shadow", "bg-white"):
            self.assertNotIn(token, str(outer.class_name))
        for child in outer.children:
            self.assertIn("rounded-xl", str(child.class_name))
            self.assertIn("bg-white", str(child.class_name))
            self.assertIn("shadow-", str(child.class_name))
        requests = str(hub.help_hub_panel().render())
        self.assertNotIn("Past helpers", requests)
        self.assertNotIn("Completed jobs", requests)

    def test_headings_and_scope(self):
        for factory in (
            hub.compact_section_heading,
            event_cards._help_heading,
            saved_items._heading,
        ):
            rendered = str(factory("users", "Heading", rx.Var.create(2)))
            for token in (
                "text-center",
                "text-xl sm:text-2xl",
                "text-[#e08b12]",
            ):
                self.assertIn(token, rendered)
            self.assertNotIn("Icon", rendered)
            self.assertNotIn("absolute right", rendered)
            self.assertNotIn("rounded-full", rendered)
            self.assertEqual(
                factory("users", "Heading", rx.Var.create(2)).children[0].tag,
                "h3",
            )
        self.assertNotIn("rx.icon", inspect.getsource(request_heading))
        self.assertIn("Events", str(event_cards.others_events_section()))
        self.assertIn("Hosted events", str(event_cards.hosted_events_section()))
        feed_source = inspect.getsource(event_cards.events_feed)
        heading_source = feed_source.split("event_date_calendar()", 1)[0]
        self.assertIn("rx.el.h3(", heading_source)
        self.assertNotIn("calendar", heading_source)
        title_source = heading_source.split("rx.el.h3(", 1)[1].split(
            'class_name="relative flex w-full items-center px-10"', 1
        )[0]
        self.assertNotIn("rx.icon(", title_source)
        for factory, icon, title in (
            (event_cards.others_events_section, "calendar-check", "Events"),
            (
                event_cards.hosted_events_section,
                "calendar-days",
                "Hosted events",
            ),
        ):
            with self.subTest(section=factory.__name__):
                tree = ast.parse(inspect.getsource(factory))
                heading_calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_help_heading"
                ]
                self.assertEqual(len(heading_calls), 1)
                self.assertEqual(
                    ast.literal_eval(heading_calls[0].args[0]), icon
                )
                rendered_heading = str(factory().children[0])
                self.assertNotIn(icon, rendered_heading)
                self.assertNotIn("Icon", rendered_heading)
                self.assertIn(title, rendered_heading)
                self.assertIn("text-[#e08b12]", rendered_heading)
                self.assertNotIn("absolute left", rendered_heading)
                self.assertNotIn("absolute right", rendered_heading)
                self.assertNotIn("rounded-full", rendered_heading)
        self.assertIn("text-center", str(hub.recent_requests_section()))

    def test_helper_summary_and_body(self):
        summary = inspect.getsource(hub.confirmed_helper_summary)
        for token in (
            "helper_name",
            "helper_stars(row)",
            "title",
            "disclosure_arrow()",
            "rx.el.summary",
        ):
            self.assertIn(token, summary)
        for token in (
            "schedule_date",
            "schedule_time",
            "location",
            "Confirmed helper",
        ):
            self.assertNotIn(token, summary)
        stars = inspect.getsource(hub.helper_stars)
        for token in (
            "rx.Var.range(1, 6)",
            "helper_rating_count",
            "helper_rating",
            "fill-none",
            "fill-[#e08b12]",
            "No reviews yet",
            "aria_label",
        ):
            self.assertIn(token, stars)
        body = inspect.getsource(hub.confirmed_helper_card)
        self.assertNotIn("reviews)", body)
        for token in (
            "browser_translatable_text",
            "Date time and duration",
            "Where",
            "Tools",
            "Knowledge and skills",
            "Exact meeting place",
            "MessagingState.focus_thread",
        ):
            self.assertIn(token, body)
        self.assertTrue(
            str(
                rx.el.div(
                    rx.foreach(
                        HelpHubState.confirmed_helpers,
                        hub.confirmed_helper_record,
                    )
                )
            )
        )

    def test_own_summary_and_field_order(self):
        summary = inspect.getsource(hub.own_request_summary)
        for token in (
            "ProfileState.avatar_path",
            "AuthState.is_verified",
            "AuthState.display_name",
            "avatar_with_tick",
            "1 person required",
            "people required",
        ):
            self.assertIn(token, summary)
        self.assertNotIn("scheduled", summary)
        body = inspect.getsource(hub.own_request_body)
        fields = (
            "browser_translatable_text",
            "Date time and duration",
            "Where",
            "Tools",
            "Knowledge and skills",
            "Exact meeting place",
            "square_photo_thumbnail",
            "owner_delete_footer",
        )
        positions = [body.index(field) for field in fields]
        self.assertEqual(positions, sorted(positions))
        tree = ast.parse(inspect.getsource(header.page_title_icon))
        match_call = tree.body[0].body[1].value
        branches = {
            branch.elts[0].value: branch.elts[1]
            for branch in match_call.args
            if isinstance(branch, ast.Tuple)
        }
        for tab in ("help", "upcoming", "get_help"):
            with self.subTest(tab=tab):
                icon = branches[tab]
                self.assertEqual(
                    ast.literal_eval(icon.args[0]), "heart-handshake"
                )
                classes = next(
                    k.value for k in icon.keywords if k.arg == "class_name"
                )
                self.assertEqual(
                    ast.literal_eval(classes),
                    "h-5 w-5 shrink-0 -translate-y-[1px] text-[#404040]",
                )
        self.assertIn(
            '"community", rx.icon("users-round", class_name=PAGE_TITLE_ICON_CLASS)',
            inspect.getsource(header.page_title_icon),
        )

    def test_extended_mapping_and_populated_tree(self):
        row = [
            7,
            "Help move garden planters",
            "I need help moving two heavy planters from the front garden to the patio.",
            "labour",
            "lunch",
            "",
            "24 Willow Road",
            "Bristol",
            datetime.datetime(2026, 8, 2, 9, 30),
            "open",
            "flexible",
            None,
            1,
            90,
            "Gloves",
            "Careful lifting",
            "Front door",
            "",
            "09:30",
        ]
        post = HelpPostState._row_to_post(None, row, ["job.webp"])
        self.assertEqual(set(RecentPost.__annotations__), set(post))
        self.assertEqual(post["tools"], "Gloves")
        self.assertEqual(post["knowledge_skills"], "Careful lifting")
        self.assertEqual(post["accepted_location_name"], "Front door")
        self.assertIn("09:30", post["date_time_duration"])
        self.assertIn("1 hour 30 minutes", post["date_time_duration"])
        self.assertTrue(
            str(hub.own_request_record(rx.Var.create(post).to(RecentPost)))
        )
        row[8] = None
        row[13:19] = [None, None, None, None, "", ""]
        empty = HelpPostState._row_to_post(None, row, [])
        self.assertIn("Dates to agree", empty["date_time_duration"])
        self.assertIn("Duration to agree", empty["date_time_duration"])
        source = inspect.getsource(HelpPostState)
        for column in (
            "COALESCE(duration_minutes, 0)",
            "COALESCE(tools, '')",
            "COALESCE(knowledge_skills, '')",
            "COALESCE(accepted_location_name, '')",
        ):
            self.assertIn(column, source)

    def test_requests_loading_empty_and_list_branches_compile(self):
        for factory in (
            hub.help_hub_panel,
            hub.section_skeleton,
            hub.recent_requests_section,
        ):
            component = factory()
            self.assertTrue(component.render())
            self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
