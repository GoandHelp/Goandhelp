import reflex as rx

import ast
import inspect
from pathlib import Path
import unittest

from app.app import index, theme_overrides
from app.components import (
    chat_controls,
    community_panel,
    contacts_panel,
    discover_panel,
)
from app.components import event_cards, header, messages_panel, noncontact_panel
from app.states.event_state import EVENT_DISTANCE_HELP
from app.states.unified_inbox_state import UnifiedInboxState


class WhiteOrangeRedesignTests(unittest.TestCase):
    def test_scoped_surfaces_and_controls(self):
        css = inspect.getsource(theme_overrides)
        self.assertIn(".gah-member-section { background: #ffffff;", css)
        self.assertNotIn("linear-gradient(135deg, #f3f7fe", css)
        self.assertNotIn("#f3fff5", css)
        self.assertIn("linear-gradient(to right, #fba922", css)
        self.assertNotIn("radial-gradient(", css)
        self.assertIn(".gah-map-utility::before { content: none; }", css)
        self.assertIn("0 2px 12px rgba(17,24,39,.10)", css)
        self.assertIn("0 1px 6px rgba(17,24,39,.10)", css)
        self.assertIn("border: 1px solid #e5e7eb", css)
        self.assertIn(".gah-topic-filter { border: 0", css)
        self.assertIn("text-[11px]", css)
        self.assertIn("font-size: 14px !important", css)
        self.assertIn("white-space: normal", css)
        self.assertIn(":not(:has(.maplibregl-canvas))", css)
        self.assertNotIn(
            "gradient", inspect.getsource(discover_panel.map_panel)
        )
        for path in (Path(__file__).parent / "components").glob("*.py"):
            source = path.read_text()
            self.assertNotIn("#19c33c", source, path.name)
            if path.name == "header.py":
                declarations = [
                    node
                    for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name)
                        and target.id == "BRAND_TEXT_CLASS"
                        for target in node.targets
                    )
                ]
                self.assertEqual(len(declarations), 1, path.name)
                declaration = ast.get_source_segment(source, declarations[0])
                self.assertIsNotNone(declaration, path.name)
                self.assertEqual(source.count("#23de49"), 1, path.name)
                self.assertEqual(declaration.count("#23de49"), 1, path.name)
                map_classes = ast.literal_eval(declarations[0].value)
                self.assertIn("from-[#23de49]", map_classes.split())
                self.assertIn("to-[#fba922]", map_classes.split())
                self.assertIn(
                    "text-[#fba922]", header.MAP_BRAND_TEXT_CLASS.split()
                )
                self.assertNotIn("gradient", header.MAP_BRAND_TEXT_CLASS)
                self.assertNotIn("#23de49", header.MAP_BRAND_TEXT_CLASS)
            else:
                self.assertNotIn("#23de49", source, path.name)
            if path.name == "paywall.py":
                approved = "bg-[linear-gradient(300deg,#fba922_0%,#ffda91_50%,#fba922_100%)]"
                declarations = [
                    node
                    for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name)
                        and target.id == "PAYMENT_ACTION_CLASS"
                        for target in node.targets
                    )
                ]
                self.assertEqual(len(declarations), 1, path.name)
                self.assertIn(
                    approved, ast.literal_eval(declarations[0].value).split()
                )
                self.assertEqual(source.count(approved), 1, path.name)
                self.assertNotIn(
                    "gradient", source.replace(approved, ""), path.name
                )
            else:
                self.assertNotIn("bg-[linear-gradient", source, path.name)

    def test_brand_and_topics(self):
        self.assertEqual(header.BRAND_LOGO_SRC, "/GO%20AND%20HELP%20LOGO.png")
        self.assertIn("circular multicolour", header.BRAND_LOGO_ALT)
        self.assertIn("helping-hands", header.BRAND_LOGO_ALT)
        self.assertIn("text-[#fba922]", header.MAP_BRAND_TEXT_CLASS)
        self.assertNotIn("gradient", header.BRAND_TEXT_CLASS)
        for classes in (
            community_panel.SUBJECT_CARD_ON,
            community_panel.SUBJECT_CARD_OFF,
            community_panel.SUBJECT_ICON_ON,
            community_panel.SUBJECT_ICON_OFF,
        ):
            self.assertIn("gah-topic-filter", classes)
            self.assertIn("border-0", classes)
            self.assertNotIn("border-[#", classes)
            self.assertIn("rgba(17,24,39,0.10)", classes)
        self.assertIn(
            "text-sm", inspect.getsource(community_panel.subject_folder_grid)
        )

    def test_correspondence_structure(self):
        bubble = inspect.getsource(chat_controls.correspondence_bubble)
        self.assertIn("max-w-[85%]", bubble)
        self.assertIn("#fff0d6", bubble)
        self.assertIn("#eaf2ff", bubble)
        self.assertIn("flex-col items-end", bubble)
        self.assertIn("items-start", bubble)
        self.assertIn("text-right text-xs", bubble)
        self.assertIn("text-left text-xs", bubble)
        self.assertGreater(
            bubble.index('msg["sent_at"]'), bubble.index("rounded-bl-sm")
        )
        for module in (messages_panel, contacts_panel, noncontact_panel):
            self.assertIn(
                "correspondence_bubble",
                inspect.getsource(module.message_bubble),
            )
        self.assertIn("report_button", bubble)
        self.assertNotIn("Show original", bubble)
        self.assertIn("relative", chat_controls.COMPOSER_CLASS)
        self.assertNotIn("focus-within", chat_controls.COMPOSER_CLASS)
        self.assertIn("absolute bottom-2 right-2", chat_controls.SEND_CLASS)
        self.assertIn("pb-16", chat_controls.MESSAGE_INPUT_CLASS)
        self.assertIn("w-full", chat_controls.MESSAGE_INPUT_CLASS)
        self.assertIn("max-h-40", chat_controls.MESSAGE_INPUT_CLASS)

    def test_headings_outside_surface_bodies(self):
        for factory in (
            messages_panel.compose_area,
            messages_panel.offers_block,
            messages_panel.helpee_requests_block,
        ):
            component = factory()
            self.assertNotIn("gah-main-card", str(component.class_name))
            self.assertNotIn("rounded", str(component.class_name))
            heading = (
                component.children[0].children[1]
                if factory is messages_panel.compose_area
                else component.children[0]
            )
            rendered_heading = str(heading)
            if factory is messages_panel.compose_area:
                self.assertEqual(heading.tag, "h3")
                for token in ("text-base", "sm:text-lg", "font-semibold"):
                    self.assertIn(token, str(heading.class_name))
                self.assertEqual(
                    str(heading.children[0]),
                    str(messages_panel.envelope_star()),
                )
                self.assertIn("text-center", rendered_heading)
            else:
                self.assertIn("text-xl sm:text-2xl", rendered_heading)
                self.assertIn("text-center", rendered_heading)
                self.assertEqual(len(heading.children), 1)
                button = heading.children[0]
                self.assertEqual(button.tag, "button")
                self.assertEqual(len(button.children), 2)
                label, arrow = button.children
                self.assertEqual(label.tag, "span")
                self.assertNotIn("Icon", str(label))
                self.assertNotIn("Lucide", str(label))
                self.assertEqual(arrow.tag, "span")
                self.assertEqual(len(arrow.children), 1)
                opened = (
                    UnifiedInboxState.offers_open
                    if factory is messages_panel.offers_block
                    else UnifiedInboxState.requests_open
                )
                self.assertEqual(
                    str(arrow.children[0]),
                    str(messages_panel.disclosure_arrow(opened)),
                )
                self.assertNotIn(
                    "rx.icon",
                    inspect.getsource(messages_panel.inbox_disclosure),
                )
            self.assertNotIn("gah-main-card", rendered_heading)
            self.assertNotIn("gah-main-card", inspect.getsource(factory))
        feed = event_cards.events_feed()
        self.assertNotIn("gah-main-card", str(feed.class_name))
        self.assertIn("Upcoming events", str(feed.children[0]))
        self.assertIn("Refresh events", str(feed.children[0]))
        self.assertIn("Select your dates", str(feed.children[1]))
        self.assertNotIn("gah-main-card", str(feed.children[3].class_name))
        self.assertIn("gah-edge-stack", str(feed.children[3]))
        source = inspect.getsource(event_cards.events_feed)
        self.assertEqual(source.count('"Upcoming events"'), 1)
        self.assertEqual(source.count("EventState.event_count_label"), 0)
        self.assertEqual(source.count('aria_label="Refresh events"'), 1)
        self.assertEqual(EVENT_DISTANCE_HELP, "how far will you go to help")
        distance = str(event_cards.event_distance_control())
        self.assertIn("text-xl", distance)
        self.assertIn("sm:text-2xl", distance)
        self.assertIn("text-center", distance)
        self.assertNotIn(
            "text-sm font-medium leading-relaxed",
            inspect.getsource(event_cards.event_distance_control),
        )

    def test_component_compilation(self):
        for factory in (
            index,
            community_panel.community_panel,
            event_cards.events_section,
            messages_panel.messages_panel,
            messages_panel.job_conversation_panel,
            contacts_panel.conversation_panel,
            noncontact_panel.noncontact_conversation_view,
            header.header,
        ):
            with self.subTest(component=factory.__name__):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
