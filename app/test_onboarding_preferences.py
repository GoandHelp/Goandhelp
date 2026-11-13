import reflex as rx

import inspect
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.components import onboarding
from app.models import LOCATION_MODE_HIDDEN
from app.skill_categories import CATEGORY_CHOICES
from app.states.onboarding_state import (
    OnboardingState,
    COUNTRY_OPTIONS,
    ONBOARDING_SCREENS,
    LANGUAGE_PRESETS,
    LOCATION_CHOICES,
    PERMISSION_ANSWERS,
    PERMISSION_TOPICS,
    SAFETY_COMMITMENTS,
)


class OnboardingPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.state = OnboardingState(_reflex_internal_init=True)
        self.state._reset()
        self.state.saving = False

    def test_exact_copy_and_render(self):
        self.assertEqual(
            [s["title"] for s in ONBOARDING_SCREENS[7:12]],
            [
                "How can you help?",
                "Languages",
                "Your location",
                "Community commitments",
                "Notifications permissions.",
            ],
        )
        self.assertEqual(
            ONBOARDING_SCREENS[7]["body"],
            "Select your Skills and Knowledge that you can help others with",
        )
        self.assertEqual(
            ONBOARDING_SCREENS[8]["body"],
            "In what languages can you give and get help?",
        )
        self.assertEqual(
            ONBOARDING_SCREENS[10]["body"], "Read them, then confirm you're in."
        )
        source = inspect.getsource(onboarding)
        for copy in (
            "You can change these later in your profile.",
            "When you request help, your location is shown approximately between 500m and 1km away from you.",
            "Only a confirmed helper is shown your accurate job location",
            "As a helper, setting your location to 'Approximate' allows a helpee to send you direct help requests. Showing your location is not necessary for helping others.",
            "Camera and photos permissions.",
            "I agree to these community rules",
        ):
            self.assertIn(copy, source)
        self.assertEqual(
            [x["title"] for x in SAFETY_COMMITMENTS],
            [
                "Kindness first",
                "Agree in the app",
                "Meet safely",
                "Report anything off",
            ],
        )
        self.assertEqual(
            next(
                x["label"]
                for x in LOCATION_CHOICES
                if x["value"] == LOCATION_MODE_HIDDEN
            ),
            "Off",
        )
        self.assertTrue(onboarding.onboarding_flow().render())

    def test_complete_skills_and_scrollable_languages(self):
        source = inspect.getsource(onboarding.screen_body)
        self.assertIn("rx.foreach(CATEGORY_CHOICES, category_card)", source)
        self.assertIn("rx.foreach(LANGUAGE_PRESETS, language_chip)", source)
        self.assertIn("overflow-y-auto", source)
        self.assertIn("h-64", source)
        self.assertIn("tab_index=0", source)
        self.assertIn('"check"', inspect.getsource(onboarding.language_chip))
        self.state.current_step = 8
        self.assertFalse(self.state.can_continue)
        for choice in CATEGORY_CHOICES:
            self.state.toggle_category(choice["value"])
        self.assertEqual(
            set(self.state.categories), {x["value"] for x in CATEGORY_CHOICES}
        )
        self.assertTrue(self.state.can_continue)
        self.state.set_custom_skill("  Bicycle repair, sewing, first aid  ")
        self.assertTrue(self.state.can_continue)
        self.state.current_step = 9
        self.assertFalse(self.state.can_continue)
        for language in LANGUAGE_PRESETS:
            self.state.toggle_language(language)
        self.assertEqual(set(self.state.languages), set(LANGUAGE_PRESETS))
        self.assertTrue(self.state.can_continue)

    def test_map_bounds_marker_and_gating(self):
        self.state.current_step = 10
        self.assertTrue(self.state.can_continue)
        self.state.choose_location("approximate")
        self.assertTrue(self.state.can_continue)
        self.assertEqual(self.state.location_markers, [])
        initial_center = list(self.state.map_center)
        initial_zoom = self.state.map_zoom
        self.state.set_location_point(0.0, 0.0)
        self.assertTrue(self.state.can_continue)
        self.assertEqual(len(self.state.location_markers), 1)
        self.assertTrue(self.state.location_markers[0]["draggable"])
        self.assertEqual(self.state.location_markers[0]["lat"], 0.0)
        self.assertEqual(self.state.location_markers[0]["lng"], 0.0)
        self.assertEqual(self.state.map_center, initial_center)
        self.assertEqual(self.state.map_zoom, initial_zoom)
        for lng, lat in [(180.0, 90.0), (-180.0, -90.0), (12.5, 42.5)]:
            self.state.set_location_point(lng, lat)
            self.assertEqual(self.state.map_center, initial_center)
            self.assertEqual(self.state.map_zoom, initial_zoom)
            self.assertEqual(self.state.location_markers[0]["lat"], lat)
            self.assertEqual(self.state.location_markers[0]["lng"], lng)
        last_valid_marker = dict(self.state.location_markers[0])
        for lng, lat in [
            (181.0, 0.0),
            (0.0, 91.0),
            (float("nan"), 0.0),
            (0.0, float("inf")),
        ]:
            self.state.set_location_point(lng, lat)
            self.assertEqual(self.state.map_center, initial_center)
            self.assertEqual(self.state.map_zoom, initial_zoom)
            self.assertEqual(self.state.location_markers, [last_valid_marker])
        self.state.choose_location("live")
        self.assertEqual(self.state.location_pref, "approximate")
        self.state.choose_location(LOCATION_MODE_HIDDEN)
        self.state.has_point = False
        self.assertTrue(self.state.can_continue)
        source = inspect.getsource(onboarding.location_screen)
        self.assertIn("on_map_click=OnboardingState.set_location_point", source)
        self.assertIn(
            "on_marker_drag=OnboardingState.set_location_point", source
        )
        self.assertIn("OPENFREEMAP_LIBERTY", source)
        self.assertNotIn("Live", source)

    def test_custom_answers_and_revised_controls(self):
        from app.models import CATEGORY_OTHER
        from app.components.openfreemap import _MAP_COMPONENT
        from app.components.map_picker import _map_options

        self.assertEqual(self.state.location_pref, LOCATION_MODE_HIDDEN)
        self.state.current_step = 8
        self.state.categories = [CATEGORY_OTHER]
        for blank_details in ("", "   "):
            with self.subTest(blank_details=repr(blank_details)):
                self.state.set_custom_skill(blank_details)
                self.assertTrue(self.state.can_continue)
        self.state.set_custom_skill("  Bicycle repair, sewing, first aid  ")
        self.assertTrue(self.state.can_continue)
        self.state.current_step = 9
        self.state.set_custom_language("  English  ")
        self.assertTrue(self.state.can_continue)
        answers = json.loads(json.dumps(self.state._answers()))
        self.state._reset()
        self.assertEqual(self.state.custom_skill, "")
        self.assertEqual(self.state.custom_language, "")
        self.state._apply_answers(answers, {})
        self.assertEqual(
            self.state.custom_skill, "Bicycle repair, sewing, first aid"
        )
        self.assertEqual(self.state.custom_language, "English")
        self.assertIn(
            "Bicycle repair, sewing, first aid",
            self.state.summary_rows[2]["value"],
        )
        self.assertEqual(self.state.summary_rows[3]["value"], "English")
        self.state.set_custom_skill("x" * 1000)
        self.state.set_custom_language("x" * 1000)
        self.assertEqual(len(self.state.custom_skill), 500)
        self.assertEqual(len(self.state.custom_language), 200)
        self.assertIn(
            'navigation_position="bottom-left"',
            inspect.getsource(onboarding.location_screen),
        )
        self.assertNotIn(
            "location_status", inspect.getsource(onboarding.location_screen)
        )
        self.assertNotIn(
            "Tap the map", inspect.getsource(onboarding.location_screen)
        )
        self.assertIn(
            'marker.id === "onboarding-private-profile"', _MAP_COMPONENT
        )
        self.assertIn(
            "border:0;box-shadow:none;background:#e08b12", _MAP_COMPONENT
        )
        self.assertIn(
            "onboarding-first-request", inspect.getsource(_map_options)
        )
        self.assertNotIn(
            "ready_confirmed",
            inspect.getsource(onboarding.first_request_screen),
        )
        self.assertIn(
            "border-0", inspect.getsource(onboarding.onboarding_actions)
        )
        self.assertIn(
            "justify-center", inspect.getsource(onboarding.permission_block)
        )
        self.assertTrue(onboarding.onboarding_flow().render())

    def test_exact_language_order(self):
        expected = "English, Mandarin Chinese, Hindi, Spanish, Standard Arabic, French, Bengali, Portuguese, Russian, Urdu, Indonesian, German, Japanese, Nigerian Pidgin, Egyptian Arabic, Marathi, Vietnamese, Telugu, Turkish, Western Punjabi, Swahili, Tagalog, Tamil, Yue Chinese, Wu Chinese, Korean, Persian, Hausa, Amharic, Italian, Gujarati, Bhojpuri, Burmese, Polish, Malayalam, Sundanese, Kannada, Maithili, Odia, Ukrainian, Igbo, Yoruba, Romanian, Dutch, Kurdish, Thai, Min Nan Chinese, Javanese, Pashto, Eastern Punjabi, Uzbek, Sindhi, Cebuano, Hungarian, Greek, Zulu, Czech, Swedish, Shona, Uyghur, Hmong, Somali, Hiligaynon, Quechua, Azerbaijani, Madurese, Sinhalese, Lao, Turkmen, Kyrgyz, Tswana, Xhosa, Isan, Assamese, Malagasy, Nepali, Saraiki, Northern Sotho, Chichewa, Akan, Lingala, Tigrinya, Hebrew, Slovak, Bulgarian, Danish, Finnish, Norwegian, Belarusian, Armenian, Georgian, Albanian, Maori, Tatar, Tajik, Balochi, Gan Chinese, Kinyarwanda, Wolof, Min Bei Chinese".split(
            ", "
        )
        priority = [
            "English",
            "Spanish",
            "French",
            "German",
            "Portuguese",
            "Chinese",
            "Russian",
            "Arabic",
            "Hindi",
            "Japanese",
        ]
        aliases = {"Mandarin Chinese": "Chinese", "Standard Arabic": "Arabic"}
        expected = [
            *priority,
            *sorted({aliases.get(x, x) for x in expected} - set(priority)),
        ]
        self.assertEqual(LANGUAGE_PRESETS, expected)
        self.assertEqual(len(LANGUAGE_PRESETS), len(set(LANGUAGE_PRESETS)))

    def test_english_selection_roundtrip_and_hidden_choice(self):
        self.assertEqual(LANGUAGE_PRESETS.count("English"), 1)
        self.state.current_step = 9
        self.state.toggle_language("English")
        self.assertTrue(self.state.can_continue)
        answers = json.loads(json.dumps(self.state._answers()))
        self.state._reset()
        self.state._apply_answers(answers, {})
        self.assertEqual(self.state.languages, ["English"])
        self.state.toggle_language("English")
        self.assertEqual(self.state.languages, [])
        self.state.choose_location("off")
        self.assertEqual(self.state.location_pref, LOCATION_MODE_HIDDEN)
        self.assertIn(
            'location_choice("Off", LOCATION_MODE_HIDDEN)',
            inspect.getsource(onboarding.location_screen),
        )
        choice = inspect.getsource(onboarding.location_choice)
        self.assertIn("ring-2 ring-[#e08b12] bg-[#fff7e8]", choice)
        self.assertNotIn("bg-white/80", choice)

    def test_permissions_and_commitment(self):
        self.assertEqual(
            [p["key"] for p in PERMISSION_TOPICS], ["notifications", "camera"]
        )
        self.assertEqual(
            [p["label"] for p in PERMISSION_ANSWERS], ["Turn on", "Not now"]
        )
        self.state.current_step = 11
        self.assertFalse(self.state.can_continue)
        self.state.toggle_safety()
        self.assertTrue(self.state.can_continue)
        self.state.current_step = 12
        self.assertFalse(self.state.can_continue)
        self.state.choose_permission("notifications", "allow_later")
        self.assertFalse(self.state.can_continue)
        self.state.choose_permission("camera", "invalid")
        self.assertFalse(self.state.can_continue)
        self.state.choose_permission("camera", "not_now")
        self.assertTrue(self.state.can_continue)
        self.assertEqual(self.state.perm_location, "")
        self.assertNotIn(
            '"location"', inspect.getsource(onboarding.permissions_screen)
        )

    def test_answer_round_trip_and_legacy_defaults(self):
        self.state.set_location_point(23.123456, -12.654321)
        self.state.choose_location("approximate")
        self.state.choose_permission("camera", "allow_later")
        answers = json.loads(json.dumps(self.state._answers()))
        permissions = self.state._permissions()
        self.state._apply_answers({}, {})
        self.assertFalse(self.state.has_point)
        self.state._apply_answers(answers, permissions)
        self.assertEqual(self.state.map_center, [23.123456, -12.654321])
        self.assertTrue(self.state.has_point)
        self.assertEqual(self.state._answers(), answers)
        self.assertEqual(self.state._permissions(), permissions)
        self.state._apply_answers(
            {"setup_version": 3, "location_pref": "approximate"}, {}
        )
        self.state.current_step = 10
        self.assertTrue(self.state.can_continue)
        for invalid in (None, "bad", True, float("nan"), 100):
            self.state._apply_answers(
                {"has_point": True, "latitude": invalid, "longitude": 0}, {}
            )
            self.assertFalse(self.state.has_point)


class FinishHarness:
    def __init__(self, state):
        self.state = state

    def __getattr__(self, name):
        return getattr(self.state, name)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, state_type):
        return SimpleNamespace(help_mode="", preferred_language="")

    async def _username_problem(self, session, username, sid):
        return ""


class OnboardingCoordinatePersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_update_and_insert_coordinate_sql(self):
        for mode in ("approximate", LOCATION_MODE_HIDDEN):
            for rowcount in (0, 1):
                with self.subTest(mode=mode, rowcount=rowcount):
                    state = OnboardingState(_reflex_internal_init=True)
                    state._reset()
                    state.saving = False
                    state.username = "test.member"
                    state.home_country = COUNTRY_OPTIONS[0]
                    state.set_custom_skill("Bicycle repair, sewing, first aid")
                    from app.models import CATEGORY_OTHER

                    state.categories = [CATEGORY_OTHER, "arts"]
                    state.languages = ["Hindi"]
                    state.set_custom_language("English")
                    state.set_location_point(12.25, 44.5)
                    state.choose_location(mode)
                    session = AsyncMock()
                    session.execute.return_value = SimpleNamespace(
                        rowcount=rowcount
                    )
                    session.__aenter__.return_value = session
                    with patch.object(rx, "asession", return_value=session):
                        async for _ in OnboardingState._finish(
                            FinishHarness(state), 42
                        ):
                            pass
                    session.commit.assert_awaited_once()
                    calls = [
                        (str(c.args[0]), c.args[1])
                        for c in session.execute.await_args_list
                    ]
                    profile_calls = [
                        (sql, params)
                        for sql, params in calls
                        if "skillkind_profile" in sql
                    ]
                    self.assertEqual(
                        len(profile_calls), 2 if rowcount == 0 else 1
                    )
                    for sql, params in profile_calls:
                        self.assertEqual(params["location_mode"], mode)
                        self.assertEqual(
                            params["skills"],
                            "Bicycle repair, sewing, first aid",
                        )
                        self.assertEqual(params["languages"], "Hindi, English")
                        self.assertIn(":skills", sql)
                        self.assertIn("latitude", sql)
                        self.assertIn("longitude", sql)
                        self.assertIn("location_updated_at", sql)
                        self.assertIn("CASE WHEN :visible THEN now()", sql)
                        self.assertEqual(
                            params["visible"], mode == "approximate"
                        )
                        self.assertEqual(
                            params["latitude"],
                            44.5 if mode == "approximate" else None,
                        )
                        self.assertEqual(
                            params["longitude"],
                            12.25 if mode == "approximate" else None,
                        )
                    progress = next(
                        params
                        for sql, params in calls
                        if "skillkind_onboarding_progress" in sql
                    )
                    self.assertEqual(
                        json.loads(progress["answers"])["latitude"], 44.5
                    )
                    self.assertEqual(
                        json.loads(progress["answers"])["location_pref"], mode
                    )

    async def test_missing_approximate_point_cannot_finish(self):
        state = OnboardingState(_reflex_internal_init=True)
        state._reset()
        state.home_country = COUNTRY_OPTIONS[0]
        state.location_pref = "approximate"
        harness = FinishHarness(state)
        with patch.object(rx, "asession") as session:
            async for _ in OnboardingState._finish(harness, 42):
                pass
        session.assert_not_called()
        self.assertEqual(harness.current_step, 10)
        self.assertFalse(harness.saving)


if __name__ == "__main__":
    unittest.main()
