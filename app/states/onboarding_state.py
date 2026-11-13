"""Required 13-screen onboarding plus the eight-step guided tour.

Everything here is database-backed by `skillkind_onboarding_progress`. The row is
created in the same transaction as registration (see AuthState.register), with an
idempotent insert during email verification as a second safety net. Legacy
accounts that have no row are never forced into onboarding and are never
backfilled.
"""

import asyncio
import json
import datetime
import logging
import math
import re

import reflex as rx
from sqlalchemy import text

from app.components.openfreemap import MapMarker
from app.countries import ISO2_NAMES, country_default_currency
from app.request_draft import (
    REQUEST_TEXT_FIELDS,
    FIRST_REQUEST_INSERT,
    normalize_request_payload,
    validate_request,
    valid_request_point,
)
from app.membership import (
    check_post_allowance,
    cap_message,
    post_interval_for_tier,
)
from app.skill_categories import request_category_limit
from app.states.help_hub_state import (
    _date_ceiling,
    REWARD_CHOICES,
    REWARD_LABELS,
    LEGACY_REWARD_TYPE,
    HelpHubState,
)
from app.models import (
    DEFAULT_LANGUAGE,
    GUIDED_TOUR_LAST_STEP,
    HELP_MODES,
    LANGUAGE_CODES,
    LOCATION_MODE_APPROXIMATE,
    LOCATION_MODE_HIDDEN,
    ONBOARDING_FIRST_STEP,
)
from app.skill_categories import (
    join_categories,
    normalize_categories,
    category_labels,
)

# UI totals are independent of the legacy database storage bounds.
TOTAL_STEPS = 13
TOUR_TOTAL_STEPS = 8

COUNTRY_OPTIONS: list[str] = sorted(set(ISO2_NAMES.values()))

# Spoken languages are matching data, independent of the interface preference.
LANGUAGE_PRESETS: list[str] = (
    "English, Mandarin Chinese, Hindi, Spanish, Standard Arabic, French, Bengali, Portuguese, Russian, Urdu, Indonesian, German, Japanese, Nigerian Pidgin, Egyptian Arabic, Marathi, Vietnamese, Telugu, Turkish, Western Punjabi, Swahili, Tagalog, Tamil, Yue Chinese, Wu Chinese, Korean, Persian, Hausa, Amharic, Italian, Gujarati, Bhojpuri, Burmese, Polish, Malayalam, Sundanese, Kannada, Maithili, Odia, Ukrainian, Igbo, Yoruba, Romanian, Dutch, Kurdish, Thai, Min Nan Chinese, Javanese, Pashto, Eastern Punjabi, Uzbek, Sindhi, Cebuano, Hungarian, Greek, Zulu, Czech, Swedish, Shona, Uyghur, Hmong, Somali, Hiligaynon, Quechua, Azerbaijani, Madurese, Sinhalese, Lao, Turkmen, Kyrgyz, Tswana, Xhosa, Isan, Assamese, Malagasy, Nepali, Saraiki, Northern Sotho, Chichewa, Akan, Lingala, Tigrinya, Hebrew, Slovak, Bulgarian, Danish, Finnish, Norwegian, Belarusian, Armenian, Georgian, Albanian, Maori, Tatar, Tajik, Balochi, Gan Chinese, Kinyarwanda, Wolof, Min Bei Chinese".split(
        ", "
    )
)
LANGUAGE_PRIORITY = [
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
LANGUAGE_ALIASES = {"Mandarin Chinese": "Chinese", "Standard Arabic": "Arabic"}
LANGUAGE_PRESETS = [
    *LANGUAGE_PRIORITY,
    *sorted(
        {LANGUAGE_ALIASES.get(label, label) for label in LANGUAGE_PRESETS}
        - set(LANGUAGE_PRIORITY)
    ),
]
CUSTOM_SKILL_LIMIT = 500
CUSTOM_LANGUAGE_LIMIT = 200


MODE_CHOICES: list[dict[str, str]] = [
    {
        "value": "offer_help",
        "label": "Offer help",
        "icon": "hand-helping",
        "blurb": "You mostly want to lend a hand to people nearby.",
    },
    {
        "value": "receive_help",
        "label": "Get help",
        "icon": "map-pin",
        "blurb": "You mostly want to ask for practical help where you are.",
    },
    {
        "value": "both",
        "label": "Both ways",
        "icon": "users-round",
        "blurb": "Give and receive — trade skills as you go.",
    },
]


LOCATION_CHOICES: list[dict[str, str]] = [
    {
        "value": LOCATION_MODE_HIDDEN,
        "label": "Off",
        "icon": "eye-off",
        "blurb": "Nobody sees where you are. You can still browse everything.",
    },
    {
        "value": LOCATION_MODE_APPROXIMATE,
        "label": "Approximate",
        "icon": "circle-dot",
        "blurb": "Members see a soft area, never your exact address.",
    },
]

SAFETY_COMMITMENTS: list[dict[str, str]] = [
    {
        "icon": "shield-check",
        "title": "Kindness first",
        "body": "No harassment, discrimination or pressure — ever.",
    },
    {
        "icon": "handshake",
        "title": "Agree in the app",
        "body": "Task, time, place and reward are agreed before you meet.",
    },
    {
        "icon": "map-pin",
        "title": "Meet safely",
        "body": "Public places for first meetings, and share your plan.",
    },
    {
        "icon": "flag",
        "title": "Report anything off",
        "body": "Use report and block; we read every report.",
    },
]

PERMISSION_TOPICS: list[dict[str, str]] = [
    {
        "key": "notifications",
        "icon": "bell",
        "title": "Notifications",
        "body": "This choice controls notifications sent to your phone/device for messages, accepted offers and check-in reminders. In-app notifications are always on.",
    },
    {
        "key": "camera",
        "icon": "camera",
        "title": "Camera & photos",
        "body": "For your profile photo and clear pictures of a task.",
    },
]

PERMISSION_ANSWERS: list[dict[str, str]] = [
    {"value": "allow_later", "label": "Turn on"},
    {"value": "not_now", "label": "Not now"},
]

# Copy for the 13 screens. Later functional bodies remain in place.
ONBOARDING_SCREENS: list[dict[str, str]] = [
    {"title": "Welcome to Go and Help", "body": ""},
    {"title": "What is Go and Help?", "body": ""},
    {"title": "Give help", "body": ""},
    {"title": "Get help", "body": ""},
    {"title": "Offer a reward", "body": ""},
    {"title": "Help and travel", "body": ""},
    {"title": "Join or create an Event for larger projects", "body": ""},
    {
        "title": "How can you help?",
        "body": "Select your Skills and Knowledge that you can help others with",
    },
    {
        "title": "Languages",
        "body": "In what languages can you give and get help?",
    },
    {
        "title": "Your location",
        "body": "",
    },
    {
        "title": "Community commitments",
        "body": "Read them, then confirm you're in.",
    },
    {"title": "Notifications permissions.", "body": ""},
    {"title": "Need help with a job?", "body": ""},
]

TOUR_STEPS: list[dict[str, str]] = [
    {
        "step": "1",
        "title": "Your Profile",
        "body": "The place to update your Information, become a Premium member and read more about Go and Help",
        "target": "profile",
    },
    {
        "step": "2",
        "title": "Update your skills",
        "body": "Choose the skills and knowledge you can share below. Relevant skills improve matching and help people trust that you can help.",
        "target": "skills",
    },
    {
        "step": "3",
        "title": "Search filters",
        "body": "Go or Get help with the toggle in search filters. Tailor your search criteria here then explore in map or list view",
        "target": "filters",
    },
    {
        "step": "4",
        "title": "Request help and view upcoming help",
        "body": "Manage your help requests and keep track of confirmed jobs, events and helpers.",
        "target": "help",
    },
    {
        "step": "5",
        "title": "Message and accept help offers",
        "body": "Message helpers and helpee's. Review offers and accept the helper who fits, confirm the task, time, place and reward together before meeting; an offer alone is not an agreement.",
        "target": "inbox",
    },
    {
        "step": "6",
        "title": "Community Forum",
        "body": "Join Community Forum discussions to ask questions, share local knowledge and exchange ideas. Open a discussion to read replies and take part.",
        "target": "community-community",
    },
    {
        "step": "7",
        "title": "Events",
        "body": "Discover or host Events for festivals, community projects, disaster relief and larger jobs. Bring people together, explore event details and coordinate helping as a group.",
        "target": "community-events",
    },
    {
        "step": "8",
        "title": "Reviews",
        "body": "Explore received and given Reviews. After completed help, share honest ratings and experiences to build trust. Reviews help others choose confidently and contribute to your profile reputation.",
        "target": "community-reviews",
    },
]


def parse_steps(raw: str) -> list[int]:
    """Normalized finished-step numbers held in `completed_steps`."""
    out: list[int] = []
    for part in str(raw or "").split(","):
        token = part.strip()
        if token.isdigit():
            value = int(token)
            if ONBOARDING_FIRST_STEP <= value <= TOTAL_STEPS:
                if value not in out:
                    out.append(value)
    return sorted(out)


class OnboardingState(rx.State):
    """Server-side truth for required onboarding and the guided tour."""

    interface_language: str = DEFAULT_LANGUAGE
    language_confirmed: bool = False

    @rx.var
    def needs_language_choice(self) -> bool:
        return not self.language_confirmed

    @rx.event(background=True)
    async def confirm_interface_language(self):
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            if (
                self.saving
                or auth.language_saving
                or not auth.subscriber_id.isdigit()
            ):
                return
            sid = auth.subscriber_id
            language = auth.preferred_language
            if language not in LANGUAGE_CODES:
                return
            self.saving = True
            self.error = ""
        try:
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "UPDATE skillkind_subscriber SET preferred_language = :language WHERE id = :sid"
                    ),
                    {"sid": int(sid), "language": language},
                )
                await session.execute(
                    text("""
                        UPDATE skillkind_onboarding_progress
                        SET answers_json = (CAST(COALESCE(NULLIF(answers_json, ''), '{}') AS jsonb)
                            || CAST(:patch AS jsonb))::text, updated_at = now()
                        WHERE subscriber_id = :sid
                    """),
                    {
                        "sid": int(sid),
                        "patch": json.dumps(
                            {
                                "preferred_language": language,
                                "interface_language_confirmed": True,
                            }
                        ),
                    },
                )
                await session.commit()
            async with self:
                auth = await self.get_state(AuthState)
                if auth.subscriber_id == sid:
                    self.interface_language = language
                    self.language_confirmed = True
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Could not save language. Please try again."
        finally:
            async with self:
                self.saving = False

    has_row: bool = False
    is_complete: bool = False
    # Explicit loading gate: the root page must never render the product for a
    # signed-in session until `progress_loaded` is True, otherwise an account
    # with an unfinished row would briefly see the map instead of onboarding.
    progress_loaded: bool = False
    loading_progress: bool = False
    current_step: int = ONBOARDING_FIRST_STEP
    completed_steps: list[int] = []
    saving: bool = False
    error: str = ""

    # Tap-first answers.
    username: str = ""
    username_feedback: str = ""

    @rx.event
    async def set_username(self, value: str):
        self.username = value.strip().lower()
        self.username_feedback = "Checking availability…"
        from app.states.auth_state import AuthState

        auth = await self.get_state(AuthState)
        try:
            async with rx.asession() as session:
                problem = await self._username_problem(
                    session, self.username, int(auth.subscriber_id or 0)
                )
            self.username_feedback = problem or "Username available"
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.username_feedback = "Could not check availability. Try again."

    async def _username_problem(self, session, username: str, sid: int) -> str:
        import re

        if not re.fullmatch(r"[a-z0-9._]{3,30}", username):
            return (
                "Use 3–30 lowercase letters, numbers, periods or underscores."
            )
        taken = (
            await session.execute(
                text(
                    "SELECT subscriber_id FROM skillkind_profile WHERE LOWER(username) = :username AND subscriber_id <> :sid LIMIT 1"
                ),
                {"username": username, "sid": sid},
            )
        ).first()
        return "That username is already taken." if taken else ""

    mode: str = ""
    categories: list[str] = []
    languages: list[str] = []
    custom_skill: str = ""
    custom_language: str = ""

    @rx.event
    def set_custom_skill(self, value: str):
        if not self.saving:
            self.custom_skill = " ".join(value.split())[
                :CUSTOM_SKILL_LIMIT
            ].strip()
            return OnboardingState.persist_skills_draft

    @rx.event
    async def persist_skills_draft(self):
        from app.states.auth_state import AuthState

        auth = await self.get_state(AuthState)
        if (
            not auth.is_signed_in
            or not auth.subscriber_id.isdigit()
            or not self.has_row
            or self.is_complete
        ):
            return
        try:
            async with rx.asession() as session:
                await session.execute(
                    text("""
                        UPDATE skillkind_onboarding_progress
                        SET answers_json = CAST(COALESCE(NULLIF(answers_json, ''), '{}') AS jsonb)
                            || CAST(:draft AS jsonb), updated_at = now()
                        WHERE subscriber_id = :sid AND completed_at IS NULL
                    """),
                    {
                        "sid": int(auth.subscriber_id),
                        "draft": json.dumps(
                            {
                                "categories": self.categories,
                                "custom_skill": self.custom_skill,
                            }
                        ),
                    },
                )
                await session.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Could not save your details. Keep this page open and try Next again."

    @rx.event
    def set_custom_language(self, value: str):
        if not self.saving:
            self.custom_language = " ".join(value.split())[
                :CUSTOM_LANGUAGE_LIMIT
            ].strip()

    def _profile_languages(self) -> str:
        return ", ".join(
            dict.fromkeys(
                [
                    *self.languages,
                    *(
                        [self.custom_language.strip()]
                        if self.custom_language.strip()
                        else []
                    ),
                ]
            )
        )

    def _profile_skills(self) -> str:
        return self.custom_skill.strip()[:CUSTOM_SKILL_LIMIT]

    home_country: str = ""
    location_pref: str = LOCATION_MODE_HIDDEN
    latitude: float = 0.0
    longitude: float = 0.0
    has_point: bool = False
    map_center: list[float] = [10.0, 46.5]
    map_zoom: float = 4.0
    location_status: str = (
        "Tap the map to place your private pin, or choose Off."
    )

    @rx.var
    def location_markers(self) -> list[MapMarker]:
        if not self.has_point:
            return []
        return [
            {
                "id": "onboarding-private-profile",
                "lat": self.latitude,
                "lng": self.longitude,
                "label": "Your private profile pin",
                "kind": "selected",
                "selected": True,
                "draggable": True,
                "icon": "hand-helping",
                "color": "#e08b12",
                "image_url": "",
            }
        ]

    def _valid_point(self) -> bool:
        return (
            self.has_point
            and math.isfinite(self.latitude)
            and math.isfinite(self.longitude)
            and -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
        )

    @rx.event
    def set_location_point(self, lng: float, lat: float):
        if self.saving:
            return
        if not (
            math.isfinite(lng)
            and math.isfinite(lat)
            and -180 <= lng <= 180
            and -90 <= lat <= 90
        ):
            self.location_status = "Choose a point within the map bounds."
            return
        self.error = ""
        self.longitude = lng
        self.latitude = lat
        self.has_point = True
        self.location_pref = LOCATION_MODE_APPROXIMATE
        self.location_status = (
            "Private pin placed. Drag it or tap the map to adjust."
        )

    safety_ack: bool = False
    perm_location: str = ""
    perm_notifications: str = ""
    perm_camera: str = ""
    ready_confirmed: bool = False

    request_title: str = ""
    request_description: str = ""
    request_category: str = ""
    request_date: str = ""
    request_reward: str = ""
    request_rewards: list[str] = []
    request_reward_specs: dict[str, str] = {}

    @rx.event
    async def toggle_request_reward(self, reward: str):
        if (
            self.saving
            or self.is_complete
            or self.first_request_post_id
            or reward not in REWARD_LABELS
        ):
            return
        if reward in self.request_rewards:
            self.request_rewards = [
                key for key in self.request_rewards if key != reward
            ]
            self.request_reward_specs.pop(reward, None)
        else:
            self.request_rewards = [*self.request_rewards, reward]
        self.request_reward = (
            self.request_rewards[0] if self.request_rewards else ""
        )
        await self._save_request_draft()

    @rx.event
    async def set_request_reward_spec(self, reward: str, value: str):
        if (
            self.saving
            or self.is_complete
            or self.first_request_post_id
            or reward == "money"
            or reward not in self.request_rewards
        ):
            return
        self.request_reward_specs[reward] = " ".join(value.split())[:120]
        await self._save_request_draft()

    def _reward_payload(self, params: dict) -> dict:
        rewards = self.request_rewards or (
            [self.request_reward]
            if self.request_reward in REWARD_LABELS
            else []
        )
        if not rewards:
            return params
        parts: list[str] = []
        value, money = HelpHubState._money_details(
            "money" in rewards,
            self.request_quote,
            self.request_budget,
            self.request_currency,
        )
        for key in rewards:
            if key not in REWARD_LABELS:
                raise ValueError("Choose a valid reward.")
            if key == "money":
                parts.append(money)
                continue
            specification = self.request_reward_specs.get(
                key, self.request_other if key == "other_reward" else ""
            ).strip()
            if not 3 <= len(specification) <= 120:
                raise ValueError(
                    f"Specify {REWARD_LABELS[key]} in 3–120 characters."
                )
            parts.append(f"{REWARD_LABELS[key]}: {specification}")
        summary = "; ".join(parts)
        if len(summary) > 255:
            non_money_keys = [key for key in rewards if key != "money"]
            base_parts = [
                money if key == "money" else f"{REWARD_LABELS[key]}: "
                for key in rewards
            ]
            remaining = max(0, 255 - len("; ".join(base_parts)))
            share = remaining // max(len(non_money_keys), 1)
            shortened: list[str] = []
            for key in rewards:
                if key == "money":
                    shortened.append(money)
                    continue
                spec = self.request_reward_specs.get(
                    key, self.request_other if key == "other_reward" else ""
                ).strip()
                if len(spec) <= share:
                    shown = spec
                elif share >= 1:
                    shown = f"{spec[: share - 1]}…"
                else:
                    shown = ""
                shortened.append(f"{REWARD_LABELS[key]}: {shown}")
            summary = "; ".join(shortened)[:255]
        params.update(
            reward_type=LEGACY_REWARD_TYPE[rewards[0]],
            reward_types=",".join(rewards),
            reward_details=summary,
            reward_value=value,
            other_details=self.request_reward_specs.get(
                "other_reward", self.request_other
            )
            if "other_reward" in rewards
            else "",
        )
        return params

    request_currency: str = "USD"
    request_budget: str = ""
    request_other: str = ""
    request_quote: bool = False
    request_latitude: float = 0.0
    request_longitude: float = 0.0
    request_has_point: bool = False
    first_request_post_id: int = 0

    @rx.var
    def request_date_min(self) -> str:
        return datetime.date.today().isoformat()

    @rx.var
    def request_date_max(self) -> str:
        return _date_ceiling(datetime.date.today()).isoformat()

    @rx.event
    async def prepare_first_request(self):
        from app.states.map_picker_state import MapPickerState

        picker = await self.get_state(MapPickerState)
        picker._reset_point()
        picker.open_key = "onboarding-first-request"
        if valid_request_point(
            self.request_has_point,
            self.request_latitude,
            self.request_longitude,
        ):
            picker._open_with_point(
                "onboarding-first-request",
                self.request_latitude,
                self.request_longitude,
            )

    @rx.event
    async def set_request_field(
        self, field: str, value: str | int | float | bool | None
    ):
        if (
            self.saving
            or self.first_request_post_id
            or field not in REQUEST_TEXT_FIELDS
        ):
            return
        setattr(self, field, normalize_request_payload(value))
        await self._save_request_draft()

    @rx.event
    async def toggle_request_quote(self):
        if self.saving or self.first_request_post_id:
            return
        self.request_quote = not self.request_quote
        await self._save_request_draft()

    @rx.event
    async def capture_request_pin(self):
        from app.states.map_picker_state import MapPickerState

        picker = await self.get_state(MapPickerState)
        if (
            picker.open_key != "onboarding-first-request"
            or self.first_request_post_id
            or self.saving
        ):
            return
        self.request_has_point = valid_request_point(
            picker.has_point, picker.latitude, picker.longitude
        )
        self.request_latitude = (
            picker.latitude if self.request_has_point else 0.0
        )
        self.request_longitude = (
            picker.longitude if self.request_has_point else 0.0
        )
        await self._save_request_draft()

    def _request_answers(
        self,
    ) -> dict[str, str | bool | float | int | list[str] | dict[str, str]]:
        return {
            **{field: getattr(self, field) for field in REQUEST_TEXT_FIELDS},
            "request_rewards": self.request_rewards,
            "request_reward_specs": self.request_reward_specs,
            "request_quote": self.request_quote,
            "request_latitude": self.request_latitude,
            "request_longitude": self.request_longitude,
            "request_has_point": self.request_has_point,
            "first_request_post_id": self.first_request_post_id,
        }

    async def _save_request_draft(self):
        if not self.has_row or self.is_complete:
            return
        from app.states.auth_state import AuthState

        auth = await self.get_state(AuthState)
        if not auth.is_signed_in or not auth.subscriber_id.isdigit():
            return
        try:
            async with rx.asession() as session:
                await session.execute(
                    text("""
                    UPDATE skillkind_onboarding_progress
                    SET answers_json = CAST(COALESCE(NULLIF(answers_json, ''), '{}') AS jsonb)
                        || CAST(:draft AS jsonb), updated_at = now()
                    WHERE subscriber_id = :sid AND completed_at IS NULL
                      AND COALESCE(CAST(COALESCE(NULLIF(answers_json, ''), '{}') AS jsonb)
                          ->> 'first_request_post_id', '0') = '0'
                """),
                    {
                        "sid": int(auth.subscriber_id),
                        "draft": json.dumps(self._request_answers()),
                    },
                )
                await session.commit()
            self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                "Could not save your draft. Keep this page open and try again."
            )

    @rx.event
    async def post_first_request(self):
        from app.states.auth_state import AuthState

        if self.saving:
            return
        if self.first_request_post_id:
            yield OnboardingState.complete_onboarding
            return
        auth = await self.get_state(AuthState)
        if (
            not auth.is_signed_in
            or not auth.subscriber_id.isdigit()
            or not self.has_row
            or self.is_complete
        ):
            self.error = "Please sign in to complete your onboarding."
            return
        self.saving = True
        self.error = ""
        yield
        try:
            if not self.request_date.strip():
                self.request_date = datetime.date.today().isoformat()
            params = validate_request(
                self.request_title,
                self.request_description,
                self.request_category,
                self.request_date,
                "money"
                if "money" in self.request_rewards
                else (
                    self.request_rewards[0]
                    if self.request_rewards
                    else self.request_reward
                ),
                self.request_currency,
                self.request_budget,
                self.request_quote,
                self.request_reward_specs.get(
                    "other_reward", self.request_other
                ),
                allow_free=True,
            )
            params = self._reward_payload(params)
            if not valid_request_point(
                self.request_has_point,
                self.request_latitude,
                self.request_longitude,
            ):
                raise ValueError("Place a private map pin for this request.")
            sid = int(auth.subscriber_id)
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text("""
                    SELECT answers_json FROM skillkind_onboarding_progress
                    WHERE subscriber_id = :sid AND completed_at IS NULL FOR UPDATE
                """),
                        {"sid": sid},
                    )
                ).first()
                if row is None:
                    raise ValueError(
                        "Your onboarding is no longer available. Refresh to continue."
                    )
                saved = json.loads(str(row[0] or "{}"))
                post_id = int(saved.get("first_request_post_id", 0) or 0)
                if not post_id:
                    allowed, premium, _used, limit = await check_post_allowance(
                        session, sid
                    )
                    if not allowed:
                        raise ValueError(cap_message(premium, limit))
                    if 1 > request_category_limit(premium):
                        raise ValueError(
                            "Your membership does not allow this category selection."
                        )
                    params.update(
                        sid=sid,
                        latitude=self.request_latitude,
                        longitude=self.request_longitude,
                        lifetime=post_interval_for_tier(premium),
                        priority=premium,
                    )
                    post_id = int(
                        (
                            await session.execute(
                                text(FIRST_REQUEST_INSERT), params
                            )
                        ).scalar_one()
                    )
                    from app.field_requests import notify_field_helpers

                    await notify_field_helpers(session, post_id)
                answers = {
                    **saved,
                    **self._answers(),
                    "first_request_post_id": post_id,
                }
                finished = sorted({*self.completed_steps, 13})
                await session.execute(
                    text("""
                    UPDATE skillkind_onboarding_progress
                    SET current_step = 13, answers_json = :answers,
                        completed_steps = :finished, updated_at = now()
                    WHERE subscriber_id = :sid
                """),
                    {
                        "sid": sid,
                        "answers": json.dumps(answers),
                        "finished": ",".join(str(x) for x in finished),
                    },
                )
                await session.commit()
            self.first_request_post_id = post_id
            self.completed_steps = finished
            self.current_step = 13
        except ValueError as e:
            self.error = str(e)
            return
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "We couldn't post your request. Your draft is kept; please try again."
            return
        finally:
            self.saving = False
        yield OnboardingState.complete_onboarding

    celebration_fading: bool = False
    celebration_visible: bool = False
    celebration_pending: bool = False
    celebration_generation: int = 0
    celebration_camera_duration: int = 0

    # Guided tour.
    tour_prompt_visible: bool = False
    tour_step: int = 0
    tour_complete: bool = False
    tour_hidden: bool = False

    # ---------------------------------------------------------------- vars
    @rx.var
    def needs_onboarding(self) -> bool:
        # Only meaningful once the row has actually been read from the database.
        return self.progress_loaded and self.has_row and not self.is_complete

    @rx.var
    def progress_pending(self) -> bool:
        """True while onboarding progress has not been resolved yet."""
        return not self.progress_loaded

    @rx.var
    def progress_width(self) -> str:
        pct = int(
            round(
                min(max(self.current_step, 1), TOTAL_STEPS) * 100 / TOTAL_STEPS
            )
        )
        return f"{max(pct, 6)}%"

    @rx.var
    def step_label(self) -> str:
        from app.interface_i18n import translate

        return f"{translate(self.interface_language, 'Step')} {min(max(self.current_step, 1), TOTAL_STEPS)} / {TOTAL_STEPS}"

    @rx.var
    def screen(self) -> dict[str, str]:
        index = min(max(self.current_step, 1), TOTAL_STEPS) - 1
        return ONBOARDING_SCREENS[index]

    @rx.var
    def is_first_step(self) -> bool:
        return self.current_step <= ONBOARDING_FIRST_STEP

    @rx.var
    def is_last_step(self) -> bool:
        return self.current_step >= TOTAL_STEPS

    @rx.var
    def can_continue(self) -> bool:
        step = self.current_step
        if step == 1:
            return bool(
                self.home_country in COUNTRY_OPTIONS
                and re.fullmatch(r"[a-z0-9._]{3,30}", self.username)
                and self.username_feedback in ("", "Username available")
            )
        if 2 <= step <= 7:
            return True
        if step == 8:
            return bool(normalize_categories(self.categories))
        if step == 9:
            return bool(self.languages or self.custom_language.strip())
        if step == 10:
            return self.location_pref in (
                LOCATION_MODE_HIDDEN,
                LOCATION_MODE_APPROXIMATE,
            )
        if step == 11:
            return self.safety_ack
        if step == 12:
            return bool(
                self.perm_notifications in ("allow_later", "not_now")
                and self.perm_camera in ("allow_later", "not_now")
            )
        return True

    @rx.var
    def continue_label(self) -> str:
        if self.current_step >= TOTAL_STEPS:
            return "Let's go and help!"
        return "Continue"

    @rx.var
    def summary_rows(self) -> list[dict[str, str]]:
        modes = {
            "offer_help": "Offering help",
            "receive_help": "Getting help",
            "both": "Both ways",
        }
        return [
            {
                "icon": "at-sign",
                "label": "Username",
                "value": f"@{self.username}",
            },
            {
                "icon": "route",
                "label": "Taking part",
                "value": modes.get(self.mode, "Both ways"),
            },
            {
                "icon": "sparkles",
                "label": "Skills",
                "value": ", ".join(
                    [
                        *category_labels(self.categories),
                        *(
                            [self._profile_skills()]
                            if self._profile_skills()
                            else []
                        ),
                    ]
                )
                or "—",
            },
            {
                "icon": "languages",
                "label": "Languages",
                "value": self._profile_languages() or "—",
            },
            {
                "icon": "house",
                "label": "Nationality",
                "value": self.home_country or "—",
            },
            {
                "icon": "shield",
                "label": "Location sharing",
                "value": (self.location_pref or "off").capitalize(),
            },
        ]

    # ------------------------------------------------------------ tour vars
    @rx.var
    def tour_visible(self) -> bool:
        return (
            self.has_row
            and self.is_complete
            and not self.tour_complete
            and not self.tour_hidden
            and not self.tour_prompt_visible
            and not self.celebration_pending
            and self.tour_step >= 1
        )

    @rx.var
    def tour_card(self) -> dict[str, str]:
        index = min(max(self.tour_step, 1), TOUR_TOTAL_STEPS) - 1
        return TOUR_STEPS[index]

    @rx.var
    def tour_is_first(self) -> bool:
        return self.tour_step <= 1

    @rx.var
    def tour_is_last(self) -> bool:
        return self.tour_step >= TOUR_TOTAL_STEPS

    @rx.var
    def tour_step_label(self) -> str:
        from app.interface_i18n import translate

        return f"{translate(self.interface_language, 'Tour')} {self.tour_step} / {TOUR_TOTAL_STEPS}"

    @rx.var
    def tour_can_restart(self) -> bool:
        return self.has_row and self.is_complete

    # ------------------------------------------------------------- setters
    @rx.event
    def choose_mode(self, value: str):
        self.mode = value if value in HELP_MODES else ""

    @rx.event
    def toggle_category(self, value: str):
        if self.saving or self.is_complete:
            return
        if value in self.categories:
            self.categories = [c for c in self.categories if c != value]
        else:
            self.categories = normalize_categories([*self.categories, value])
        return OnboardingState.persist_skills_draft

    @rx.event
    def toggle_language(self, value: str):
        if value in self.languages:
            self.languages = [x for x in self.languages if x != value]
            return
        self.languages = [*self.languages, value]

    @rx.event
    def choose_country(self, value: str):
        if self.saving or self.is_complete or value not in COUNTRY_OPTIONS:
            return
        self.home_country = value
        if not self.first_request_post_id:
            self.request_currency = country_default_currency(value)

    @rx.event
    def choose_location(self, value: str):
        if value == "off":
            value = LOCATION_MODE_HIDDEN
        if not self.saving and value in (
            LOCATION_MODE_APPROXIMATE,
            LOCATION_MODE_HIDDEN,
        ):
            self.location_pref = value
            self.error = ""

    @rx.event
    def toggle_safety(self):
        self.safety_ack = not self.safety_ack

    @rx.event
    def choose_permission(self, topic: str, value: str):
        if value not in ("allow_later", "not_now"):
            return
        if topic == "notifications":
            self.perm_notifications = value
        elif topic == "camera":
            self.perm_camera = value

    @rx.event
    def toggle_ready(self):
        self.ready_confirmed = not self.ready_confirmed

    # --------------------------------------------------------------- helpers
    def _answers(self) -> dict[str, object]:
        return {
            **self._request_answers(),
            "setup_version": 3,
            "preferred_language": self.interface_language,
            "interface_language_confirmed": self.language_confirmed,
            "username": self.username,
            "tour_step": self.tour_step,
            "tour_hidden": self.tour_hidden,
            "mode": self.mode,
            "categories": self.categories,
            "languages": self.languages,
            "custom_skill": self.custom_skill,
            "custom_language": self.custom_language,
            "home_country": self.home_country,
            "location_pref": self.location_pref,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "has_point": self.has_point,
            "safety_ack": self.safety_ack,
            "ready_confirmed": self.ready_confirmed,
        }

    def _permissions(self) -> dict[str, str]:
        return {
            "location": self.perm_location,
            "notifications": self.perm_notifications,
            "camera": self.perm_camera,
        }

    def _apply_answers(self, answers: dict, permissions: dict):
        saved_language = str(answers.get("preferred_language", "") or "")
        self.interface_language = (
            saved_language
            if saved_language in LANGUAGE_CODES
            else DEFAULT_LANGUAGE
        )
        self.language_confirmed = (
            answers.get("interface_language_confirmed") is True
        )
        # Missing or invalid values retain the legacy column fallback set on load.
        saved_tour_step = answers.get("tour_step")
        if type(saved_tour_step) is int and 0 <= saved_tour_step <= 12:
            self.tour_step = min(saved_tour_step, TOUR_TOTAL_STEPS)
        self.tour_hidden = answers.get("tour_hidden") is True
        self.username = str(answers.get("username", "") or "").strip().lower()
        self.username_feedback = ""
        self.mode = str(answers.get("mode", "") or "")
        raw_categories = answers.get("categories", [])
        self.categories = normalize_categories(
            [str(x) for x in raw_categories]
            if isinstance(raw_categories, list)
            else []
        )
        raw_languages = answers.get("languages", [])
        self.languages = (
            list(
                dict.fromkeys(
                    LANGUAGE_ALIASES.get(str(x), str(x)) for x in raw_languages
                )
            )
            if isinstance(raw_languages, list)
            else []
        )
        self.custom_skill = " ".join(
            str(answers.get("custom_skill", "") or "").split()
        )[:CUSTOM_SKILL_LIMIT].strip()
        self.custom_language = " ".join(
            str(answers.get("custom_language", "") or "").split()
        )[:CUSTOM_LANGUAGE_LIMIT].strip()
        self.home_country = str(answers.get("home_country", "") or "")
        for field in REQUEST_TEXT_FIELDS:
            setattr(self, field, str(answers.get(field, "") or "")[:1000])
        raw_rewards = answers.get(
            "request_rewards",
            [self.request_reward] if self.request_reward else [],
        )
        self.request_rewards = (
            list(
                dict.fromkeys(
                    key
                    for key in raw_rewards
                    if isinstance(key, str) and key in REWARD_LABELS
                )
            )
            if isinstance(raw_rewards, list)
            else []
        )
        raw_specs = answers.get("request_reward_specs", {})
        self.request_reward_specs = (
            {
                key: " ".join(str(raw_specs.get(key, "")).split())[:120]
                for key in self.request_rewards
                if key != "money"
            }
            if isinstance(raw_specs, dict)
            else {}
        )
        if (
            "other_reward" in self.request_rewards
            and not self.request_reward_specs.get("other_reward")
        ):
            self.request_reward_specs["other_reward"] = self.request_other[:120]
        self.request_reward = (
            self.request_rewards[0] if self.request_rewards else ""
        )
        self.request_currency = str(
            answers.get("request_currency")
            or country_default_currency(self.home_country)
        )
        self.request_quote = answers.get("request_quote") is True
        self.first_request_post_id = max(
            0, int(answers.get("first_request_post_id", 0) or 0)
        )
        self.request_has_point = False
        self.request_latitude = 0.0
        self.request_longitude = 0.0
        rlat, rlng = (
            answers.get("request_latitude"),
            answers.get("request_longitude"),
        )
        if (
            type(rlat) in (int, float)
            and type(rlng) in (int, float)
            and valid_request_point(
                answers.get("request_has_point") is True, rlat, rlng
            )
        ):
            self.request_has_point = True
            self.request_latitude, self.request_longitude = (
                float(rlat),
                float(rlng),
            )
        saved_location = str(answers.get("location_pref", "") or "")
        self.location_pref = (
            saved_location
            if saved_location
            in (LOCATION_MODE_APPROXIMATE, LOCATION_MODE_HIDDEN)
            else LOCATION_MODE_HIDDEN
        )
        self.latitude = 0.0
        self.longitude = 0.0
        self.has_point = False
        self.map_center = [10.0, 46.5]
        self.map_zoom = 4.0
        self.location_status = (
            "Tap the map to place your private pin, or choose Off."
        )
        lat, lng = answers.get("latitude"), answers.get("longitude")
        if (
            answers.get("has_point") is True
            and type(lat) in (int, float)
            and type(lng) in (int, float)
            and math.isfinite(lat)
            and math.isfinite(lng)
            and -90 <= lat <= 90
            and -180 <= lng <= 180
        ):
            self.latitude, self.longitude = float(lat), float(lng)
            self.has_point = True
            self.map_center = [self.longitude, self.latitude]
            self.map_zoom = 11.0
            self.location_status = (
                "Your private pin is restored. Drag it or tap to adjust."
            )
        self.safety_ack = bool(answers.get("safety_ack", False))
        self.ready_confirmed = bool(answers.get("ready_confirmed", False))
        self.perm_location = str(permissions.get("location", "") or "")
        self.perm_notifications = str(
            permissions.get("notifications", "") or ""
        )
        self.perm_camera = str(permissions.get("camera", "") or "")

    def _reset(self):
        self.celebration_generation += 1
        self.celebration_visible = False
        self.celebration_fading = False
        self.celebration_pending = False
        self.celebration_camera_duration = 0
        self.tour_prompt_visible = False
        self.has_row = False
        self.is_complete = False
        self.progress_loaded = False
        self.loading_progress = False
        self.current_step = ONBOARDING_FIRST_STEP
        self.completed_steps = []
        self.tour_step = 0
        self.tour_complete = False
        self.tour_hidden = False
        self.error = ""
        self._apply_answers({}, {})

    # ---------------------------------------------------------------- load
    async def _resolve_progress(self, subscriber_id: str, verified: bool):
        """Fully resolve onboarding state for one account, before returning.

        This is the single source of truth for onboarding hydration. It clears
        any stale values, marks loading, reads the row and applies it, and only
        then flips `progress_loaded`. Callers MUST await it while holding the
        state lock (directly inside `async with self:` / after `get_state`) so no
        render can happen between session hydration and onboarding hydration.

        Outcomes:
          * signed out or access-disabled -> reset, progress_loaded = True
          * legacy account with no row -> has_row False, progress_loaded = True
          * database failure -> fails CLOSED: progress_loaded stays False so the
            root gate keeps showing the loading state instead of the product.
        """
        sid = str(subscriber_id or "")
        # Clear anything held from a previous account before loading, so stale
        # progress can never leak across sessions.
        self._reset()
        self.loading_progress = True
        from app.states.auth_state import ALLOW_UNVERIFIED_SIGN_IN

        if not sid.isdigit() or (not verified and not ALLOW_UNVERIFIED_SIGN_IN):
            self._reset()
            self.progress_loaded = True
            return
        try:
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT current_step, completed_steps, answers_json,
                                   permissions_json, completed_at,
                                   tour_current_step, tour_completed_at
                            FROM skillkind_onboarding_progress
                            WHERE subscriber_id = :sid
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).first()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not load onboarding progress: {e}")
            # Fail closed: never expose the member product on a load error.
            self.has_row = False
            self.is_complete = False
            self.progress_loaded = False
            self.loading_progress = True
            self.error = (
                "We couldn't load your setup just now. Please refresh in a "
                "moment — your progress is safe."
            )
            return
        self._apply_progress_row(row)

    def _apply_progress_row(self, row):
        """Apply an already-fetched row without database I/O."""
        self._reset()
        if row is None:
            # Legacy verified account: no row means "never onboarded", and it is
            # never backfilled here.
            self._reset()
            self.progress_loaded = True
            return
        try:
            answers = json.loads(str(row[2] or "{}")) or {}
        except ValueError:
            answers = {}
        try:
            permissions = json.loads(str(row[3] or "{}")) or {}
        except ValueError:
            permissions = {}
        self.has_row = True
        self.current_step = min(
            max(int(row[0] or 1), ONBOARDING_FIRST_STEP), TOTAL_STEPS
        )
        self.completed_steps = parse_steps(str(row[1] or ""))
        if isinstance(answers, dict) and answers.get("setup_version") not in (
            2,
            3,
        ):
            old_to_new = {
                1: 1,
                2: 2,
                3: 3,
                4: 4,
                5: 5,
                6: 6,
                7: 6,
                8: 7,
                9: 8,
                10: 9,
                11: 9,
                12: 9,
                13: 10,
                14: 11,
                15: 12,
            }
            self.current_step = old_to_new.get(int(row[0] or 1), 1)
            self.completed_steps = sorted(
                {
                    old_to_new[int(s)]
                    for s in str(row[1] or "").split(",")
                    if s.strip().isdigit()
                    and int(s) in old_to_new
                    and int(s) not in (6, 10, 11)
                }
            )
        if not isinstance(answers, dict) or answers.get("setup_version") != 3:
            # Earlier sequences have different meanings; retain every answer,
            # but let unfinished members read the new story from its beginning.
            self.current_step = 1
            self.completed_steps = []
        if int(row[0] or 1) == 14:
            self.current_step = TOTAL_STEPS
        self.tour_step = min(max(int(row[5] or 0), 0), GUIDED_TOUR_LAST_STEP)
        self._apply_answers(
            answers if isinstance(answers, dict) else {},
            permissions if isinstance(permissions, dict) else {},
        )
        self.is_complete = row[4] is not None
        # Existing in-progress members keep their exact step, with no new gate.
        if self.is_complete or self.current_step > 1 or self.completed_steps:
            self.language_confirmed = True
        if not self.is_complete and (
            self.home_country not in COUNTRY_OPTIONS
            or not re.fullmatch(r"[a-z0-9._]{3,30}", self.username)
        ):
            self.current_step = 1
        self.tour_complete = row[6] is not None
        if not isinstance(answers, dict) or "tour_hidden" not in answers:
            self.tour_hidden = self.is_complete
        self.tour_prompt_visible = (
            self.is_complete
            and not self.tour_complete
            and not self.tour_hidden
            and self.tour_step == 0
        )
        self.error = ""
        self.loading_progress = False
        self.progress_loaded = True

    @rx.event(background=True)
    async def load_progress(self):
        """Thin wrapper: read the session, then resolve progress fully."""
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            await self._resolve_progress(auth.subscriber_id, auth.is_verified)

    @rx.event(background=True)
    async def start_for_subscriber(self, subscriber_id: int):
        """Create (or keep) the progress row for a just-verified account."""
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_onboarding_progress
                            (subscriber_id, current_step, completed_steps,
                             answers_json, permissions_json, tour_current_step)
                        VALUES (:sid, 1, '', '{}', '{}', 0)
                        ON CONFLICT (subscriber_id) DO NOTHING
                        """
                    ),
                    {"sid": int(subscriber_id)},
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not start onboarding: {e}")
            return
        async with self:
            self.error = ""
        yield OnboardingState.load_progress

    # ------------------------------------------------------------ navigation
    @rx.event
    def go_back(self):
        if not self.saving and self.current_step > ONBOARDING_FIRST_STEP:
            self.current_step -= 1
            self.error = ""

    @rx.event(background=True)
    async def go_next(self):
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            verified = auth.is_verified
            step = self.current_step
            username = self.username
            allowed = (
                self.can_continue
                and self.has_row
                and not self.saving
                and not auth.language_saving
            )
            self.interface_language = auth.preferred_language
            self.error = ""
            if (
                step == 10
                and self.location_pref == LOCATION_MODE_APPROXIMATE
                and not self._valid_point()
            ):
                self.error = "Please zoom in and place your location on the map"
                return
        if not allowed or not sid.isdigit():
            return
        if step == 1:
            try:
                async with rx.asession() as session:
                    problem = await self._username_problem(
                        session, username, int(sid)
                    )
            except Exception as e:
                logging.exception(f"Error: {e}")
                problem = "Could not check your username. Try again."
            if problem:
                async with self:
                    self.username_feedback = problem
                    self.error = problem
                return
        if step >= TOTAL_STEPS:
            yield OnboardingState.post_first_request
            return
        async with self:
            self.saving = True
            finished = sorted({*self.completed_steps, step})
            answers = json.dumps(self._answers())
            permissions = json.dumps(self._permissions())
        next_step = step + 1
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_onboarding_progress
                        SET current_step = :next_step,
                            completed_steps = :finished,
                            answers_json = :answers,
                            permissions_json = :permissions,
                            updated_at = now()
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {
                        "next_step": next_step,
                        "finished": ",".join(str(x) for x in finished),
                        "answers": answers,
                        "permissions": permissions,
                        "sid": int(sid),
                    },
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not save onboarding step: {e}")
            async with self:
                self.saving = False
                self.error = "We couldn't save that step. Please try again."
            return
        async with self:
            self.completed_steps = finished
            self.current_step = next_step
            self.saving = False

    @rx.event(background=True)
    async def complete_onboarding(self):
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            if (
                not auth.is_signed_in
                or not sid.isdigit()
                or not self.has_row
                or self.is_complete
                or self.saving
                or self.current_step != TOTAL_STEPS
                or auth.language_saving
            ):
                return
            self.saving = True
        async for update in self._finish(int(sid)):
            yield update

    async def _finish(self, sid: int):
        """Atomically apply every answer, then offer the optional tour."""
        async with self:
            if self.is_complete:
                self.saving = False
                return
            country = self.home_country
            if country not in COUNTRY_OPTIONS:
                self.current_step = 1
                self.saving = False
                self.error = "Choose your nationality from the country list."
                return
            username = self.username.strip().lower()
            if self.location_pref not in (
                LOCATION_MODE_HIDDEN,
                LOCATION_MODE_APPROXIMATE,
            ) or (
                self.location_pref == LOCATION_MODE_APPROXIMATE
                and not self._valid_point()
            ):
                self.current_step = 10
                self.saving = False
                self.error = "Please zoom in and place your location on the map"
                return
            latitude = self.latitude
            longitude = self.longitude
        categories = join_categories(self.categories)
        languages = self._profile_languages()
        skills = self._profile_skills()
        mode = self.mode if self.mode in HELP_MODES else "both"
        location_mode = (
            self.location_pref
            if self.location_pref
            in (
                LOCATION_MODE_HIDDEN,
                LOCATION_MODE_APPROXIMATE,
            )
            else LOCATION_MODE_HIDDEN
        )
        visible = location_mode != LOCATION_MODE_HIDDEN
        async with self:
            from app.states.auth_state import AuthState

            auth = await self.get_state(AuthState)
            language_code = (
                auth.preferred_language
                if auth.preferred_language in LANGUAGE_CODES
                else DEFAULT_LANGUAGE
            )
            self.interface_language = language_code
        finished = list(range(ONBOARDING_FIRST_STEP, TOTAL_STEPS + 1))
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_subscriber
                        SET help_mode = :mode, preferred_language = :language
                        WHERE id = :sid
                        """
                    ),
                    {"mode": mode, "language": language_code, "sid": sid},
                )
                # Fixed username namespace; held until commit or rollback.
                await asession.execute(
                    text(
                        """
                        SELECT pg_advisory_xact_lock(
                            1936419182,
                            CAST(hashtextextended(:username, 0) & 2147483647 AS integer)
                        )
                        """
                    ),
                    {"username": username},
                )
                problem = await self._username_problem(asession, username, sid)
                if problem:
                    await asession.rollback()
                    async with self:
                        self.saving = False
                        self.current_step = 1
                        self.username_feedback = problem
                        self.error = problem
                    return
                updated = await asession.execute(
                    text(
                        """
                        UPDATE skillkind_profile
                        SET username = :username, preferred_categories = :categories,
                            languages = :languages, skills = :skills,
                            home_country = :country, nationality = :country,
                            location_mode = :location_mode,
                            show_location = :visible,
                            latitude = CASE WHEN :visible THEN :latitude ELSE latitude END,
                            longitude = CASE WHEN :visible THEN :longitude ELSE longitude END,
                            location_updated_at = CASE WHEN :visible THEN now() ELSE location_updated_at END
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {
                        "username": username,
                        "categories": categories,
                        "languages": languages,
                        "skills": skills,
                        "country": country,
                        "location_mode": location_mode,
                        "visible": visible,
                        "latitude": latitude if visible else None,
                        "longitude": longitude if visible else None,
                        "sid": sid,
                    },
                )
                if updated.rowcount == 0:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_profile
                                (subscriber_id, username, headline, bio, avatar_seed,
                                 home_city, home_country, nationality, current_city,
                                 languages, skills,
                                 preferred_categories,
                                 location_mode, show_location,
                                 latitude, longitude, location_updated_at,
                                 helper_rating_avg, helper_rating_count,
                                 traveller_rating_avg, traveller_rating_count,
                                 tasks_helped_count, tasks_received_count,
                                 kindness_points)
                            VALUES
                                (:sid, :username, '', '', :seed, '', :country, :country, '',
                                 :languages, :skills, :categories,
                                 :location_mode, :visible,
                                 :latitude, :longitude, CASE WHEN :visible THEN now() ELSE NULL END,
                                 0, 0, 0, 0, 0, 0, 0)
                            """
                        ),
                        {
                            "sid": sid,
                            "seed": str(sid),
                            "username": username,
                            "country": country,
                            "languages": languages,
                            "skills": skills,
                            "categories": categories,
                            "location_mode": location_mode,
                            "visible": visible,
                            "latitude": latitude if visible else None,
                            "longitude": longitude if visible else None,
                        },
                    )
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_onboarding_progress
                        SET current_step = :last_step,
                            completed_steps = :finished,
                            answers_json = :answers,
                            permissions_json = :permissions,
                            completed_at = now(),
                            tour_current_step = 0,
                            updated_at = now()
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {
                        "last_step": TOTAL_STEPS,
                        "finished": ",".join(str(x) for x in finished),
                        "answers": json.dumps(
                            {
                                **self._answers(),
                                "tour_step": 0,
                                "tour_hidden": False,
                            }
                        ),
                        "permissions": json.dumps(self._permissions()),
                        "sid": sid,
                    },
                )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not complete onboarding: {e}")
            async with self:
                self.saving = False
                self.error = (
                    "We couldn't finish your setup just now. Please try again."
                )
            return
        async with self:
            self.completed_steps = finished
            self.is_complete = True
            self.saving = False
            self.tour_step = 0
            self.tour_complete = False
            self.tour_hidden = False
            self.celebration_pending = self.first_request_post_id > 0
            self.tour_prompt_visible = not self.celebration_pending
            celebrate = self.celebration_pending
        from app.states.auth_state import AuthState
        from app.states.profile_state import ProfileState

        async with self:
            auth = await self.get_state(AuthState)
            auth.help_mode = mode
            auth.preferred_language = language_code
        if celebrate:
            yield OnboardingState.celebrate_first_request
        else:
            yield ProfileState.load_profile

    @rx.var
    def celebration_map_markers(self) -> list[MapMarker]:
        if self.celebration_pending and self.first_request_post_id > 0:
            return [
                {
                    "id": f"p{self.first_request_post_id}",
                    "lat": self.request_latitude,
                    "lng": self.request_longitude,
                    "label": self.request_title,
                    "kind": "job",
                    "selected": True,
                    "draggable": False,
                    "icon": "hand-helping",
                    "color": "#e08b12",
                    "image_url": "",
                }
            ]
        return []

    @rx.event(background=True)
    async def celebrate_first_request(self):
        from app.states.auth_state import AuthState
        from app.states.discovery_state import (
            DiscoveryState,
            MODE_GIVE,
            VIEW_MAP,
        )
        from app.states.profile_state import ProfileState

        async with self:
            if (
                not self.is_complete
                or not self.celebration_pending
                or self.celebration_visible
            ):
                return
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            if not auth.is_signed_in:
                return
            generation = self.celebration_generation
            discovery = await self.get_state(DiscoveryState)
            profile = await self.get_state(ProfileState)
            profile.active_tab = "discover"
            profile.settings_open = False
            discovery.map_mode = MODE_GIVE
            discovery.view_mode = VIEW_MAP
            discovery.filter_panel_open = False
            discovery.clear_selection()
            discovery.map_center = [
                self.request_longitude,
                self.request_latitude,
            ]
            discovery.map_zoom = 9.0
            self.celebration_camera_duration = 600
            self.celebration_fading = False
            self.celebration_visible = True
        yield DiscoveryState.refresh_board
        await asyncio.sleep(0.7)
        async with self:
            auth = await self.get_state(AuthState)
            if (
                generation != self.celebration_generation
                or auth.subscriber_id != sid
            ):
                return
            discovery = await self.get_state(DiscoveryState)
            self.celebration_camera_duration = 2300
            discovery.map_zoom = 13.0
        await asyncio.sleep(2.0)
        async with self:
            auth = await self.get_state(AuthState)
            if (
                generation != self.celebration_generation
                or auth.subscriber_id != sid
                or not auth.is_signed_in
            ):
                return
            self.celebration_fading = True
        await asyncio.sleep(0.6)
        async with self:
            auth = await self.get_state(AuthState)
            if (
                generation != self.celebration_generation
                or auth.subscriber_id != sid
                or not auth.is_signed_in
            ):
                return
            self.celebration_visible = False
            self.celebration_fading = False
            self.celebration_pending = False
            self.celebration_camera_duration = 0
            self.tour_prompt_visible = (
                not self.tour_hidden and not self.tour_complete
            )

    # ------------------------------------------------------------- the tour
    @rx.event
    def start_tour(self):
        if (
            not self.has_row
            or not self.is_complete
            or not self.tour_prompt_visible
        ):
            return rx.noop()
        self.tour_prompt_visible = False
        self.tour_hidden = False
        self.tour_step = 1
        return [
            OnboardingState.apply_tour_target,
            OnboardingState.persist_tour(1, False),
        ]

    @rx.event
    def dismiss_tour_prompt(self):
        if not self.tour_prompt_visible:
            return rx.noop()
        self.tour_prompt_visible = False
        self.tour_hidden = True
        return OnboardingState.persist_tour_hidden

    @rx.event(background=True)
    async def persist_tour_hidden(self):
        from app.states.auth_state import AuthState

        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            signed_in = auth.is_signed_in
            hidden = self.tour_hidden
        if not signed_in or not sid.isdigit():
            return
        try:
            async with rx.asession() as session:
                await session.execute(
                    text("""
                        UPDATE skillkind_onboarding_progress
                        SET answers_json = CAST(COALESCE(NULLIF(answers_json, ''), '{}') AS jsonb)
                            || CAST(:draft AS jsonb), updated_at = now()
                        WHERE subscriber_id = :sid AND completed_at IS NOT NULL
                    """),
                    {
                        "sid": int(sid),
                        "draft": json.dumps({"tour_hidden": hidden}),
                    },
                )
                await session.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")

    @rx.event
    async def apply_tour_target(self):
        """Navigate the real product to whatever the current step points at."""
        from app.states.discovery_state import DiscoveryState
        from app.states.profile_state import ProfileState

        profile = await self.get_state(ProfileState)
        discovery = await self.get_state(DiscoveryState)
        tabs = {
            1: "profile",
            2: "profile",
            3: "discover",
            4: "help",
            5: "inbox",
            6: "community",
            7: "community",
            8: "community",
        }
        profile.active_tab = tabs.get(self.tour_step, "discover")
        discovery.filter_panel_open = self.tour_step == 3
        profile.skills_open = self.tour_step == 2
        events = []
        if self.tour_step in (6, 7, 8):
            from app.states.community_state import CommunityState

            community = await self.get_state(CommunityState)
            section = {
                6: "community",
                7: "events",
                8: "reviews",
            }[self.tour_step]
            section_events = community.set_section(section)
            if isinstance(section_events, list):
                events.extend(section_events)
            elif section_events is not None:
                events.append(section_events)
        from app.components.tour_pointer import TOUR_SCROLL_SCRIPT

        target = TOUR_STEPS[min(max(self.tour_step, 1), TOUR_TOTAL_STEPS) - 1][
            "target"
        ]
        events.append(
            rx.call_script(
                TOUR_SCROLL_SCRIPT.replace("__TARGET__", json.dumps(target))
            )
        )
        return events

    @rx.event(background=True)
    async def persist_tour(self, step: int, finished: bool):
        from app.states.auth_state import AuthState

        step = min(max(step, 0), TOUR_TOTAL_STEPS)
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            answers = {**self._answers(), "tour_step": step}
        if not sid.isdigit():
            return
        params = {
            "step": min(step, GUIDED_TOUR_LAST_STEP),
            "answers": json.dumps(answers),
            "sid": int(sid),
        }
        try:
            async with rx.asession() as asession:
                if finished:
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_onboarding_progress
                            SET tour_current_step = :step,
                                answers_json = :answers,
                                tour_completed_at = now(),
                                updated_at = now()
                            WHERE subscriber_id = :sid
                            """
                        ),
                        params,
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_onboarding_progress
                            SET tour_current_step = :step,
                                answers_json = :answers,
                                tour_completed_at = NULL,
                                updated_at = now()
                            WHERE subscriber_id = :sid
                            """
                        ),
                        params,
                    )
                await asession.commit()
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Could not save tour progress: {e}")

    @rx.event
    def tour_next(self):
        if self.tour_step >= TOUR_TOTAL_STEPS:
            return OnboardingState.tour_finish
        self.tour_step += 1
        return [
            OnboardingState.apply_tour_target,
            OnboardingState.persist_tour(self.tour_step, False),
        ]

    @rx.event
    def tour_back(self):
        if self.tour_step <= 1:
            return rx.noop()
        self.tour_step -= 1
        return [
            OnboardingState.apply_tour_target,
            OnboardingState.persist_tour(self.tour_step, False),
        ]

    @rx.event
    async def tour_finish(self):
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState

        profile = await self.get_state(ProfileState)
        discovery = await self.get_state(DiscoveryState)
        profile.active_tab = "discover"
        profile.skills_open = False
        discovery.filter_panel_open = False
        self.tour_complete = True
        self.tour_hidden = False
        self.tour_prompt_visible = False
        step = TOUR_TOTAL_STEPS
        self.tour_step = step
        return [
            OnboardingState.persist_tour(step, True),
        ]

    @rx.event
    async def tour_dismiss(self):
        """Hide the tour, retaining its saved step for a manual restart."""
        self.tour_hidden = True
        self.tour_prompt_visible = False
        from app.states.profile_state import ProfileState
        from app.states.discovery_state import DiscoveryState

        profile = await self.get_state(ProfileState)
        discovery = await self.get_state(DiscoveryState)
        profile.skills_open = False
        discovery.filter_panel_open = False
        return [
            OnboardingState.persist_tour_hidden,
            rx.toast(
                "Tour hidden. Restart it any time from Profile settings.",
                duration=3500,
            ),
        ]

    @rx.event
    def restart_tour(self):
        self.tour_step = 1
        self.tour_complete = False
        self.tour_hidden = False
        self.tour_prompt_visible = False
        return [
            OnboardingState.apply_tour_target,
            OnboardingState.persist_tour(1, False),
        ]
