import reflex as rx

import datetime
import inspect
import unittest
from unittest.mock import patch

from test_utils import run_event
from app.countries import ISO2_NAMES, WORLD_COUNTRY_NAMES, resolve_nationality
from app.components import (
    help_hub_panel,
    discover_panel,
    contacts_panel,
    noncontact_panel,
    messages_panel,
    chat_controls,
)
from app.components.profile_tabs import profile_tabs
from app.components.unified_inbox import unified_conversation_list
from app.states.auth_state import AuthState
from app.states.help_hub_state import HelpHubState, REWARD_CHOICES
from app.states.map_picker_state import MapPickerState
from app.states.messaging_state import MessagingState
from app.app import index, theme_overrides


class CoordinatedRefinementTests(unittest.IsolatedAsyncioTestCase):
    def test_country_coverage(self):
        self.assertGreaterEqual(len(WORLD_COUNTRY_NAMES), 195)
        self.assertEqual(WORLD_COUNTRY_NAMES, sorted(set(WORLD_COUNTRY_NAMES)))
        for code, name in (
            ("VA", "Vatican City"),
            ("PS", "Palestine"),
            ("TL", "Timor-Leste"),
            ("KI", "Kiribati"),
            ("SS", "South Sudan"),
            ("GY", "Guyana"),
            ("KN", "Saint Kitts and Nevis"),
            ("UZ", "Uzbekistan"),
        ):
            self.assertEqual(ISO2_NAMES[code], name)
            self.assertEqual(resolve_nationality(name)[1], code)
        tree = str(help_hub_panel.job_location_section())
        for value in ("country", "Country", "select", "Vanuatu"):
            self.assertIn(value, tree)

    def test_filter_surfaces(self):
        source = inspect.getsource(discover_panel.filter_drawer)
        self.assertNotIn("bg-[#f5f5f5]", source)
        self.assertNotIn("centered_search_label", source)
        self.assertNotIn('"Search Everything"', source)
        self.assertLess(
            source.index('name="world_search"'),
            source.index("category_multiselect()"),
        )
        self.assertLess(
            source.index("category_multiselect()"),
            source.index("DiscoveryState.reward_filter_options"),
        )
        self.assertNotIn("set_city_filter.debounce(500)", source)
        for handler in (
            "save_current_search",
            "clear_filters",
            "WorldSearchState.submit",
        ):
            self.assertIn(handler, source)
        self.assertIn("disabled:opacity-60", source)
        self.assertIn("focus-visible:ring-[#e08b12]", source)
        self.assertIn('class_name="sr-only"', source)
        card = discover_panel.filter_drawer("w-full", compact=True)
        self.assertIsInstance(card, rx.Component)
        self.assertTrue(card.render())

    def test_form_copy_and_controls(self):
        source = inspect.getsource(help_hub_panel)
        for phrase in (
            "Address",
            "City",
            "What you can offer – required",
            "Please fill out all the fields",
        ):
            self.assertIn(phrase, source)
        form_source = inspect.getsource(help_hub_panel.post_help_form)
        self.assertNotIn('name="tools"', form_source)
        self.assertNotIn('name="knowledge_skills"', form_source)
        self.assertNotIn('field_label("Tools"', form_source)
        self.assertNotIn('field_label("Knowledge and Skills"', form_source)
        modes = inspect.getsource(help_hub_panel.mode_button)
        self.assertIn("border border-[#fba922]", modes)
        self.assertIn("border border-[#d4d4d4]", modes)
        self.assertIn("aria_pressed=selected", modes)
        date = inspect.getsource(help_hub_panel.specific_help_day_field)
        self.assertIn("on_click=HelpHubState.add_date", date)
        self.assertIn("border-[3px] border-[#fba922] bg-white", date)
        self.assertIn("h-4 w-4 text-black", date)
        self.assertIn(
            "no_validate=True", inspect.getsource(help_hub_panel.post_help_form)
        )
        rewards_by_value = {item["value"]: item for item in REWARD_CHOICES}
        self.assertEqual(rewards_by_value["money"]["label"], "Money")
        self.assertEqual(
            rewards_by_value["money"]["blurb"],
            "Set a budget or ask for a quote",
        )
        self.assertEqual(
            rewards_by_value["refreshments"]["blurb"], "Drinks and snacks"
        )
        self.assertEqual(
            rewards_by_value["activity"]["blurb"], "Cook, Hike, Surf..."
        )

    def test_rendered_location_controls(self):
        form = help_hub_panel.post_help_form()
        self.assertTrue(form.render())
        controls = {name: [] for name in ("address", "city", "country")}
        order = []

        def visit(component):
            if component.tag in ("input", "select", "textarea"):
                for name in controls:
                    if str(getattr(component, "name", "")) == str(
                        rx.Var.create(name)
                    ):
                        controls[name].append(component)
                        order.append(name)
            for child in component.children:
                visit(child)

        visit(form)
        self.assertEqual(order, ["address", "city", "country"])
        for name, matches in controls.items():
            with self.subTest(name=name):
                self.assertEqual(len(matches), 1)
                self.assertNotIn("required=", str(matches[0]))
        for name, placeholder in (
            ("address", "Address"),
            ("city", "City"),
        ):
            control = controls[name][0]
            self.assertEqual(control.tag, "input")
            self.assertEqual(str(control.type), str(rx.Var.create("text")))
            self.assertEqual(
                str(control.placeholder), str(rx.Var.create(placeholder))
            )
            for token in ("w-full", "border-[#f7d9a0]", "bg-[#ffffff]"):
                self.assertIn(token, str(control.class_name))
        country = controls["country"][0]
        self.assertEqual(country.tag, "select")
        for token in (
            "w-full",
            "border-[#f7d9a0]",
            "bg-[#ffffff]",
            "appearance-none",
        ):
            self.assertIn(token, str(country.class_name))
        self.assertEqual(str(country.value), str(HelpHubState.posting_country))
        self.assertEqual(
            [
                event.handler
                for event in country.event_triggers["on_change"].events
            ],
            [HelpHubState.set_posting_country],
        )
        blank = country.children[0]
        self.assertEqual(blank.tag, "option")
        self.assertEqual(str(blank.value), str(rx.Var.create("")))
        self.assertIn("Country", str(blank))
        self.assertIn("aria-label", str(country))

    async def test_missing_aggregation_and_clear_without_database(self):
        state = HelpHubState(_reflex_internal_init=True)
        auth = await state.get_state(AuthState)
        auth.subscriber_id = ""
        state.help_dates = []
        with patch(
            "reflex.asession",
            side_effect=AssertionError(
                "No database access in validation tests"
            ),
        ) as database:
            await run_event(state.create_help_request, {})
            self.assertEqual(
                state.missing_fields,
                [
                    "Job title",
                    "Job description",
                    "Job category",
                    "Date",
                    "Address",
                    "City",
                    "Country",
                    "Rewards",
                ],
            )
            await run_event(state.toggle_form)
            self.assertEqual(state.missing_fields, [])
            state.selected_rewards = [
                "accommodation",
                "guided_tour",
                "activity",
                "other_reward",
            ]
            state.day_mode = "flexible"
            state.flexible_days = ["Custom"]
            picker = await state.get_state(MapPickerState)
            picker.has_point = True
            picker.latitude = 46.2
            picker.longitude = 6.1
            await run_event(
                state.create_help_request,
                {"title": "Carry boxes"},
            )
            self.assertNotIn("Address", state.missing_fields)
            self.assertNotIn("Tools", state.missing_fields)
            self.assertNotIn("Knowledge and Skills", state.missing_fields)
            self.assertIn("Date", state.missing_fields)
            self.assertEqual(
                state.missing_fields[-4:],
                [
                    "Number of nights",
                    "Guided tour details",
                    "Activity details",
                    "Other reward details",
                ],
            )
            state.flexible_days = ["Any Day"]
            values = {
                "title": "Carry boxes",
                "description": "Carry boxes upstairs safely.",
                "accommodation_nights": "2",
                "guided_tour_details": "Old town",
                "activity_details": "Cooking",
                "other_reward_details": "Homemade bread",
                "specific_hour": "09",
                "specific_minute": "00",
                "duration_hours": "1",
                "duration_minutes_part": "0",
                "duration_period_count": "1",
                "duration_period_unit": "day",
            }
            with patch(
                "app.states.help_hub_state.normalize_categories",
                return_value=["moving"],
            ):
                await run_event(state.create_help_request, values)
            self.assertEqual(state.missing_fields, [])
            self.assertIn("session expired", state.error)
            picker.latitude = float("nan")
            await run_event(state.create_help_request, values)
            for label in ("Address", "City", "Country"):
                self.assertIn(label, state.missing_fields)
            await run_event(state.clear_feedback)
            self.assertEqual(state.missing_fields, [])
            database.assert_not_called()

    def test_chat_system_and_review_fit(self):
        for module in (contacts_panel, noncontact_panel):
            bubble = inspect.getsource(module.message_bubble)
            self.assertIn("correspondence_bubble", bubble)
        bubble = inspect.getsource(chat_controls._correspondence_bubble)
        self.assertNotIn("Show original", bubble)
        for value in (
            "#fff0d6",
            "#eaf2ff",
            "sent_at",
            "report_button",
            "text-black",
        ):
            self.assertIn(value, bubble)
        for factory in (
            contacts_panel.composer,
            noncontact_panel.reply_composer,
            messages_panel.composer,
        ):
            self.assertIn("COMPOSER_CLASS", inspect.getsource(factory))
            self.assertIn("Send", str(factory()))
        for factory in (
            contacts_panel.conversation_header,
            noncontact_panel.thread_header,
        ):
            self.assertNotIn("chat_safety(", inspect.getsource(factory))
            self.assertIn(
                'aria_label="Close conversation"', inspect.getsource(factory)
            )
        self.assertNotIn(
            "Add Contact", inspect.getsource(contacts_panel.conversation_panel)
        )
        row = inspect.getsource(messages_panel.review_category_row)
        self.assertNotIn("gah-inset-row", row)
        self.assertIn("min-w-0 max-w-full", row)
        self.assertIn("flex-wrap", row)
        self.assertIn("auto-fit", inspect.getsource(messages_panel.review_form))

    def test_scrollbar_scope(self):
        css = str(theme_overrides())
        for fragment in (
            "html:has(.gah-app-shell)",
            "body:has(.gah-app-shell)",
            "#root:has(.gah-app-shell)",
            "@media (max-width: 767px)",
            "scrollbar-width: none",
            "::-webkit-scrollbar",
            ".gah-member-section [class*=",
        ):
            self.assertIn(fragment, css)
        self.assertIn("overflow-y-auto", inspect.getsource(profile_tabs))

    def test_component_compilation(self):
        for factory in (
            help_hub_panel.post_help_form,
            lambda: discover_panel.filter_drawer("w-full"),
            messages_panel.job_conversation_panel,
            contacts_panel.conversation_panel,
            noncontact_panel.noncontact_conversation_view,
            messages_panel.review_form,
            lambda: rx.el.div(
                rx.foreach(
                    MessagingState.review_targets,
                    messages_panel.pending_review_card,
                )
            ),
            lambda: unified_conversation_list(messages_panel.reading_pane()),
            profile_tabs,
            index,
        ):
            with self.subTest(factory=factory):
                component = factory()
                self.assertIsInstance(component, rx.Component)
                self.assertTrue(component.render())
                self.assertTrue(str(component))


if __name__ == "__main__":
    unittest.main()
