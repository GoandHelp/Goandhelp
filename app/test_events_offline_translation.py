import ast
import inspect
import re
import unittest
import unicodedata
from pathlib import Path
from string import Formatter
from unittest.mock import AsyncMock, patch

import reflex as rx

from app.components import event_cards, event_calendar
from app.interface_catalog_events import (
    EVENT_KEYS,
    EVENT_TEMPLATE_BUILDERS,
    EVENT_TRANSLATIONS,
)
from app.interface_catalog_events_discovery import (
    DISCOVERY_KEYS,
    DISCOVERY_LOCALES,
    DISCOVERY_TRANSLATIONS,
)
from app.interface_catalog_events_planner import (
    PLANNER_COPY_KEYS,
    PLANNER_COPY_LOCALES,
    PLANNER_COPY_TRANSLATIONS,
)
from app.interface_catalog_events_templates import (
    EVENT_TEMPLATE_ROWS,
    EVENT_TEMPLATE_TRANSLATIONS,
)
from app.interface_catalog_entry import ENTRY_CATALOGS
from app.interface_catalog_forum import FORUM_LABEL_CATALOGS
from app.interface_i18n import (
    CATALOGS,
    COMPLETE_KEYS,
    EVENT_CATALOGS,
    translate,
    ui_template,
)
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.event_state import EventCard, EventState, JoinRequestRow
from app.states.map_picker_state import MapPickerState


OFFERED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}

VALID_EVENT_TEMPLATE_FORMS = {
    "da": {"Start: {date}"},
    "nl": {"Start: {date}", "Begint: {date}"},
    "sv": {"Start: {date}"},
}


def sample_event() -> EventCard:
    return {
        "id": 11,
        "title": "Member title — keep original",
        "details": "Member description stays as written.",
        "event_type": "agriculture",
        "type_label": "Agriculture",
        "type_icon": "sprout",
        "host_id": 7,
        "host_name": "Host Name",
        "host_avatar_seed": "member-7",
        "host_avatar": "",
        "host_verified": True,
        "day": "15",
        "month": "JAN",
        "weekday": "Thu",
        "time_label": "18:30",
        "date_label": "Jan 15, 2026 · 18:30",
        "place": "Member place · Porto · Portugal",
        "capacity": 6,
        "confirmed_count": 2,
        "capacity_label": "6 helpers needed · 2/6 confirmed",
        "is_full": False,
        "is_host": False,
        "join_status": "pending",
        "status_label": "Request pending with the host",
        "can_join": False,
        "can_cancel": True,
        "pending_count": 1,
        "distance_label": "about 12 km away",
        "photo_paths": [],
        "reward_details": "A meal: Member-written reward details",
    }


def sample_request() -> JoinRequestRow:
    return {
        "id": 19,
        "event_id": 11,
        "event_title": "Member event title",
        "member_id": 23,
        "member_name": "ليلى",
        "member_avatar_seed": "member-23",
        "member_avatar": "",
        "member_verified": False,
        "note": "Original note {title}",
        "created": "Jan 15, 2026 · 18:30",
        "status": "pending",
    }


class EventsCatalogCoverageTests(unittest.IsolatedAsyncioTestCase):
    def test_exact_static_locale_and_key_sets(self):
        self.assertEqual(len(OFFERED_LOCALES), 36)
        self.assertEqual(set(EVENT_TRANSLATIONS), OFFERED_LOCALES | {"ha"})
        self.assertTrue(set(EVENT_KEYS) <= set(COMPLETE_KEYS))
        for code in OFFERED_LOCALES:
            with self.subTest(locale=code):
                self.assertEqual(set(EVENT_CATALOGS[code]), set(EVENT_KEYS))
                self.assertTrue(set(EVENT_KEYS) <= set(CATALOGS[code]))
                self.assertTrue(
                    set(EVENT_TRANSLATIONS[code]) <= set(EVENT_KEYS)
                )
                for source in EVENT_KEYS:
                    value = CATALOGS[code][source]
                    self.assertTrue(value.strip(), (code, source))
                    self.assertNotIn("\ufffd", value)
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                    self.assertFalse(
                        value.startswith((f"[{code}]", f"{code}:"))
                    )
                    source_words = re.sub(r"\{[^{}]+\}", "", source)
                    if len(source) > 30 and source_words.strip(" –"):
                        allowed_forms = VALID_EVENT_TEMPLATE_FORMS.get(
                            code, set()
                        )
                        if source in allowed_forms:
                            self.assertIn(value, allowed_forms, (code, source))
                        else:
                            self.assertNotEqual(value, source, (code, source))
                self.assertEqual(
                    translate("en", "Plan an event"), "Plan an event"
                )

    def test_discovery_catalog_has_exact_locale_and_phrase_coverage(self):
        expected_locales = OFFERED_LOCALES | {"ha"}
        self.assertEqual(set(DISCOVERY_LOCALES), expected_locales)
        self.assertEqual(set(DISCOVERY_TRANSLATIONS), expected_locales)
        self.assertEqual(len(DISCOVERY_KEYS), 47)
        self.assertTrue(set(DISCOVERY_KEYS) <= set(EVENT_KEYS))
        boundary = "Show events up to 1000 kilometres away"
        for code, entries in DISCOVERY_TRANSLATIONS.items():
            with self.subTest(locale=code):
                self.assertEqual(set(entries), set(DISCOVERY_KEYS))
                for source in DISCOVERY_KEYS:
                    self.assertTrue(entries[source].strip(), (code, source))
                    self.assertNotEqual(entries[source], source, (code, source))
                    self.assertNotEqual(
                        EVENT_TRANSLATIONS[code][source], source
                    )
                self.assertIn("1000", entries[boundary])

    def test_planner_catalog_has_exact_locale_and_phrase_coverage(self):
        self.assertEqual(len(PLANNER_COPY_KEYS), 35)
        self.assertEqual(
            set(PLANNER_COPY_TRANSLATIONS), OFFERED_LOCALES | {"ha"}
        )
        self.assertEqual(PLANNER_COPY_LOCALES, OFFERED_LOCALES | {"ha"})
        self.assertTrue(set(PLANNER_COPY_KEYS) <= set(EVENT_KEYS))
        for code, entries in PLANNER_COPY_TRANSLATIONS.items():
            with self.subTest(locale=code):
                self.assertEqual(set(entries), set(PLANNER_COPY_KEYS))
                self.assertTrue(
                    set(PLANNER_COPY_KEYS) <= set(EVENT_TRANSLATIONS[code])
                )
                for source, value in entries.items():
                    self.assertEqual(EVENT_TRANSLATIONS[code][source], value)
                    self.assertTrue(value.strip(), source)
                    self.assertNotEqual(value, source, source)
                    self.assertNotIn("TODO", value)
                    self.assertNotIn("TRANSLATE_ME", value)
                    self.assertFalse(
                        value.startswith((f"[{code}]", f"{code}:"))
                    )

    def test_planner_translations_preserve_representative_constraints(self):
        expectations = {
            "es": {
                "For example: 25.00": "Por ejemplo: 25,00",
                "Required · up to 160 characters": "Obligatorio · hasta 160 caracteres",
                "Required · up to 2000 words": "Obligatorio · hasta 2000 palabras",
            },
            "fr": {
                "UTC · a future date within two years": "UTC · une date future dans les deux prochaines années",
                "Optional · up to 5 static JPEG, PNG or WebP photos · 3 MB per source photo. Avoid addresses or private information in photos.": "Facultatif · jusqu’à 5 photos statiques JPEG, PNG ou WebP · 3 Mo par photo d’origine. Évitez d’inclure des adresses ou des informations privées dans les photos.",
            },
            "de": {
                "Positive amount · up to two decimal places, or ask for a quote.": "Positiver Betrag · höchstens zwei Nachkommastellen, oder bitte um ein Angebot.",
            },
        }
        for code, phrases in expectations.items():
            for source, expected in phrases.items():
                self.assertEqual(
                    PLANNER_COPY_TRANSLATIONS[code][source], expected
                )
        photo_key = "Optional · up to 5 static JPEG, PNG or WebP photos · 3 MB per source photo. Avoid addresses or private information in photos."
        for code, entries in PLANNER_COPY_TRANSLATIONS.items():
            with self.subTest(locale=code):
                for source, required_numbers in (
                    (photo_key, {3, 5}),
                    ("Required · up to 160 characters", {160}),
                    ("Required · up to 2000 words", {2000}),
                ):
                    translated = entries[source]
                    found_numbers = {
                        int(
                            "".join(
                                str(unicodedata.digit(character))
                                for character in number
                            )
                        )
                        for number in re.findall(r"\d+", translated)
                    }
                    self.assertTrue(
                        required_numbers <= found_numbers,
                        (code, source, translated),
                    )
                self.assertTrue(
                    all(
                        token in entries[photo_key]
                        for token in ("JPEG", "PNG", "WebP")
                    )
                )
                self.assertTrue(
                    entries[
                        "Positive amount · up to two decimal places, or ask for a quote."
                    ]
                )
                self.assertTrue(entries["UTC · a future date within two years"])
        self.assertEqual(
            PLANNER_COPY_TRANSLATIONS["zh"][photo_key],
            "可选 · 最多上传 5 张静态 JPEG、PNG 或 WebP 照片 · 每张原始照片不超过 3 MB。请勿在照片中包含地址或私人信息。",
        )

    def test_planner_catalog_does_not_claim_shared_context_labels(self):
        self.assertFalse(
            set(PLANNER_COPY_KEYS) & {"Money", "Other", "Guided tour"}
        )

    def test_authored_parameter_templates_have_exact_locale_and_key_coverage(
        self,
    ):
        self.assertEqual(
            set(EVENT_TEMPLATE_TRANSLATIONS), OFFERED_LOCALES | {"ha"}
        )
        self.assertTrue(set(EVENT_TEMPLATE_ROWS) <= set(EVENT_KEYS))
        for code, entries in EVENT_TEMPLATE_TRANSLATIONS.items():
            with self.subTest(locale=code):
                self.assertEqual(set(entries), set(EVENT_TEMPLATE_ROWS))
                for source, translated in entries.items():
                    self.assertTrue(translated.strip())
                    source_words = re.sub(r"\{[^{}]+\}", "", source)
                    if source_words.strip(" –"):
                        allowed_forms = VALID_EVENT_TEMPLATE_FORMS.get(
                            code, set()
                        )
                        if source in allowed_forms:
                            self.assertIn(translated, allowed_forms)
                        else:
                            self.assertNotEqual(translated, source)

    def test_every_event_template_keeps_its_named_slots(self):
        formatter = Formatter()
        template_sources = [
            source
            for source in EVENT_KEYS
            if any(
                field
                for _text, field, _spec, _conversion in formatter.parse(source)
            )
        ]
        self.assertTrue(set(EVENT_TEMPLATE_BUILDERS) <= set(EVENT_KEYS))
        for code in OFFERED_LOCALES:
            for source in template_sources:
                expected = [
                    field
                    for _text, field, _spec, _conversion in formatter.parse(
                        source
                    )
                    if field
                ]
                translated = translate(code, source)
                actual = [
                    field
                    for _text, field, _spec, _conversion in formatter.parse(
                        translated
                    )
                    if field
                ]
                self.assertCountEqual(
                    actual, expected, (code, source, translated)
                )
        expression = ui_template(
            "Open event {title}", "title", "ليلى {original}"
        )
        self.assertIsInstance(expression, rx.Var)
        self.assertIn("split", str(expression))
        self.assertIn("join", str(expression))

    def test_all_event_components_construct_and_render(self):
        event = sample_event()
        request = sample_request()
        components = (
            event_cards.date_tile(event),
            event_cards.status_band(event),
            event_cards.event_meta(event),
            event_cards.event_card(event),
            event_cards.pending_request_card(request),
            event_cards.confirmed_attendee_card(request),
            event_cards.event_composer(),
            event_cards.event_planner_screen(),
            event_cards.event_detail_sheet(),
            event_cards.events_feed(),
            event_cards.events_section(),
            event_cards.hosted_event_body(event),
            event_cards.hosted_events_section(),
            event_calendar.event_calendar_day(
                {
                    key: rx.Var.create(value)
                    for key, value in {
                        "date": "2026-01-15",
                        "label": "15",
                        "accessible_label": "Thursday 15 January 2026",
                        "disabled": False,
                        "today": False,
                        "selected": True,
                    }.items()
                }
            ),
            event_calendar.event_date_calendar(),
        )
        for component in components:
            with self.subTest(component=component):
                self.assertIsInstance(component, rx.Component)
                self.assertIsInstance(component.render(), dict)

    async def test_hydrated_language_switch_changes_display_only(self):
        state = EventState(_reflex_internal_init=True)
        auth = AuthState(_reflex_internal_init=True)
        original = sample_event()
        state.events = [dict(original)]
        state.selected_event = [dict(original)]
        state.hosted_pending = [sample_request()]
        state.event_type_draft = "festival_volunteers"
        state.reward_choice = "meal"
        state.reward_currency = "USD"
        state.selected_dates = ["2026-01-15"]
        state.selected_date = "2026-01-15"
        state.calendar_month = "2026-01-01"
        state.calendar_today = "2026-01-01"
        state.calendar_timezone = "UTC"
        state.range_start = "2026-01-15"
        state.range_end = "2026-01-20"
        state.error = "Give your event a title."
        state.success = "Your event is live on the community board."
        state.photo_error = "Choose up to five static JPEG, PNG or WebP photos, at most 3 MB each."
        state.pending_photo_paths = ["event_42_" + "a" * 32 + ".webp"]
        before = (
            state.events,
            state.selected_event,
            state.hosted_pending,
            state.event_type_draft,
            state.reward_choice,
            state.reward_currency,
            state.selected_dates,
            state.selected_date,
            state.calendar_month,
            state.calendar_timezone,
            state.range_start,
            state.range_end,
            state.error,
            state.success,
            state.photo_error,
            state.pending_photo_paths,
        )
        getter = inspect.getattr_static(EventState, "localized_events")
        selected_getter = inspect.getattr_static(
            EventState, "localized_selected_event"
        )
        pending_getter = inspect.getattr_static(
            EventState, "localized_hosted_pending"
        )
        calendar_getter = inspect.getattr_static(
            EventState, "calendar_display_cells"
        )
        selection_getter = inspect.getattr_static(
            EventState, "calendar_display_selection"
        )
        feedback_getter = inspect.getattr_static(
            EventState, "localized_feedback"
        )
        with patch.object(
            EventState,
            "get_state",
            new=AsyncMock(
                side_effect=lambda cls: (
                    auth
                    if cls is AuthState
                    else MapPickerState(_reflex_internal_init=True)
                )
            ),
        ):
            for code in OFFERED_LOCALES:
                auth.preferred_language = code
                cards = await getter.fget(state)
                selected = await selected_getter.fget(state)
                pending = await pending_getter.fget(state)
                cells = await calendar_getter.fget(state)
                selection = await selection_getter.fget(state)
                feedback = await feedback_getter.fget(state)
                self.assertEqual(cards[0]["title"], original["title"])
                self.assertEqual(cards[0]["details"], original["details"])
                self.assertEqual(cards[0]["place"], original["place"])
                self.assertTrue(
                    cards[0]["reward_details"].endswith(
                        "Member-written reward details"
                    )
                )
                self.assertEqual(
                    state.events[0]["reward_details"],
                    original["reward_details"],
                )
                self.assertEqual(cards[0]["event_type"], "agriculture")
                self.assertEqual(
                    cards[0]["type_label"], translate(code, "Agriculture")
                )
                self.assertEqual(
                    cards[0]["month"], translate(code, "January").upper()
                )
                self.assertEqual(selected[0]["title"], original["title"])
                self.assertEqual(pending[0]["member_name"], "ليلى")
                self.assertEqual(
                    pending[0]["event_title"], "Member event title"
                )
                self.assertEqual(pending[0]["note"], "Original note {title}")
                self.assertEqual(
                    cells[0]["date"], state.calendar_cells[0]["date"]
                )
                self.assertIn(
                    translate(code, "January"), cells[14]["accessible_label"]
                )
                self.assertTrue(selection)
                self.assertEqual(
                    feedback["error"],
                    translate(code, "Give your event a title."),
                )
                self.assertEqual(state.error, "Give your event a title.")
                self.assertEqual(
                    state.success, "Your event is live on the community board."
                )
                self.assertEqual(state.event_type_draft, "festival_volunteers")
                self.assertEqual(state.reward_choice, "meal")
                self.assertEqual(state.reward_currency, "USD")
                self.assertEqual(state.selected_dates, ["2026-01-15"])
                self.assertEqual(state.pending_photo_paths, before[-1])
        self.assertEqual(
            before,
            (
                state.events,
                state.selected_event,
                state.hosted_pending,
                state.event_type_draft,
                state.reward_choice,
                state.reward_currency,
                state.selected_dates,
                state.selected_date,
                state.calendar_month,
                state.calendar_timezone,
                state.range_start,
                state.range_end,
                state.error,
                state.success,
                state.photo_error,
                state.pending_photo_paths,
            ),
        )

    def test_privacy_and_request_feedback_are_full_phrases(self):
        privacy = (
            "Share exact meeting details privately with confirmed helpers."
        )
        inactive = "That event is no longer active."
        for code in OFFERED_LOCALES:
            with self.subTest(locale=code):
                self.assertNotEqual(
                    translate(code, privacy),
                    translate(code, "Show original language"),
                )
                self.assertNotEqual(
                    translate(code, privacy), translate(code, "Your location")
                )
                self.assertNotEqual(
                    translate(code, inactive), translate(code, "Events")
                )
                self.assertNotEqual(
                    translate(code, "Choose an event date"),
                    "Choose an event date",
                )
        representative_phrases = {
            "zh": {
                privacy: "请与已确认的帮手私下分享准确的见面详情。",
                inactive: "此活动已不再进行。",
            },
            "ja": {
                privacy: "確認済みのヘルパーと正確な待ち合わせ場所を非公開で共有してください。",
                inactive: "このイベントは終了しています。",
            },
        }
        for code, phrases in representative_phrases.items():
            for source, expected in phrases.items():
                self.assertEqual(translate(code, source), expected)

    def test_event_merge_preserves_forum_and_onboarding_shared_phrases(self):
        shared_groups = (FORUM_LABEL_CATALOGS, ENTRY_CATALOGS)
        for code in OFFERED_LOCALES:
            for group in shared_groups:
                for key, value in group[code].items():
                    if key in {"Money", "Other", "Guided tour"}:
                        self.assertEqual(
                            CATALOGS[code][key], value, (code, key)
                        )

    def test_visible_event_copy_keys_are_registered(self):
        for filename in (
            "app/components/event_cards.py",
            "app/components/event_calendar.py",
        ):
            tree = ast.parse(Path(filename).read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(
                    node.func, ast.Name
                ):
                    continue
                if node.func.id not in {"ui", "ui_template"} or not node.args:
                    continue
                if isinstance(node.args[0], ast.Constant):
                    self.assertIn(node.args[0].value, COMPLETE_KEYS, filename)

    def test_planner_escape_uses_stable_close_id_and_keeps_focus_trap(self):
        source = inspect.getsource(event_cards.event_planner_screen)
        self.assertIn('id="gah-event-planner-close"', source)
        self.assertIn("#gah-event-planner-close", source)
        self.assertIn("screen.addEventListener('keydown', trap)", source)
        self.assertIn("screen.removeEventListener('keydown', trap)", source)
        self.assertNotIn('[aria-label="Close event planner"]', source)


if __name__ == "__main__":
    unittest.main()
