"""Editable profile, local area preferences and activity summary."""

import json
import logging
import re
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

import reflex as rx
from sqlalchemy import text

from app.calendar_export import (
    CALENDAR_FILENAME,
    CalendarEvent,
    build_ics,
    event_uid,
)
from app.countries import resolve_nationality
from app.image_processing import (
    ALLOWED_IMAGE_SUFFIXES,
    AVATAR_SUFFIX,
    process_avatar_bytes,
    read_image_upload,
)
from app.member_blocks import BLOCK_UNAVAILABLE_MESSAGE, are_members_blocked
from app.models import (
    CATEGORY_LABELS,
    REVIEW_HELPER_CATEGORY_LABELS,
    REVIEW_POSTER_CATEGORY_LABELS,
    TASK_CATEGORIES,
)
from app.skill_categories import category_labels, normalize_categories
from app.states.auth_state import AuthState, hash_password
from app.states.messaging_state import (
    decode_review_content,
    review_released_sql,
)
from app.verification import public_base_url


# Shared map-pin picker panel key for the Profile location disclosure.
PROFILE_PICKER_KEY = "profile_location"


def _parse_coordinate_pair(raw: str) -> tuple[float | None, float | None, str]:
    """Parse one `latitude, longitude` string server-side.

    Returns (latitude, longitude, problem). An empty value is valid and yields
    (None, None, ""). Exact values stay private: only the caller decides what,
    if anything, is ever derived for a public map.
    """
    value = (raw or "").strip().replace(";", ",")
    if not value:
        return None, None, ""
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) == 1:
        parts = [part for part in parts[0].split() if part]
    if len(parts) != 2:
        return (
            None,
            None,
            "Write coordinates as latitude, longitude — for example "
            "41.157944, -8.629105.",
        )
    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return (
            None,
            None,
            "Coordinates must be two numbers, like 41.157944, -8.629105.",
        )
    if latitude < -90 or latitude > 90:
        return None, None, "Latitude must be between -90 and 90."
    if longitude < -180 or longitude > 180:
        return None, None, "Longitude must be between -180 and 180."
    return latitude, longitude, ""


def _review_categories(
    direction: str, scores: list[int]
) -> list[dict[str, str]]:
    labels = (
        REVIEW_POSTER_CATEGORY_LABELS
        if direction == "poster_to_helper"
        else REVIEW_HELPER_CATEGORY_LABELS
    )
    return [
        {"label": label, "score": str(score)}
        for label, score in zip(labels, scores)
    ]


USERNAME_PATTERN = re.compile(r"^[a-z0-9._]{3,30}$")


class ActivityStats(TypedDict):
    posts_created: int
    posts_open: int
    applications_sent: int
    applications_accepted: int
    tasks_helped: int
    tasks_received: int
    messages_sent: int
    reviews_received: int


class JournalEntry(TypedDict):
    title: str
    status: str
    category: str
    created: str


class ReceivedReview(TypedDict):
    id: int
    reviewer_id: int
    reviewer_name: str
    reviewer_seed: str
    reviewer_avatar: str
    job_title: str
    reviewer_verified: bool
    rating: int
    percent: int
    comment: str
    response: str
    kindness_flag: bool
    created: str
    categories: list[dict[str, str]]


class PendingApplication(TypedDict):
    id: int
    key: str
    post_id: int
    post_title: str
    post_status: str
    category_label: str
    reward: str
    reward_details: str
    location: str
    scheduled: str
    proposed_time: str
    applied: str
    pitch: str
    helper_name: str
    helper_avatar_seed: str
    helper_verified: bool
    helper_handle: str
    helper_avatar: str
    helper_nationality: str
    helper_flag: str
    helper_score: int
    helper_reviews: int
    helper_helped: int


class UpcomingJob(TypedDict):
    id: int
    role_label: str
    other_name: str
    title: str
    category: str
    category_label: str
    reward: str
    reward_details: str
    location: str
    scheduled: str
    proposed_available: str
    status: str
    conversation_hint: str
    # Export metadata only: whether this job carries a real datetime, so the
    # calendar control can be honest about what will be exported.
    has_schedule: bool


REWARD_LABELS: dict[str, str] = {
    "lunch": "Lunch",
    "dinner": "Dinner",
    "accommodation": "Accommodation",
    "guided_tours": "Guided tours",
    "workshops": "Workshops",
    "lessons": "Lessons",
    "other": "Other",
}


EMPTY_STATS: ActivityStats = {
    "posts_created": 0,
    "posts_open": 0,
    "applications_sent": 0,
    "applications_accepted": 0,
    "tasks_helped": 0,
    "tasks_received": 0,
    "messages_sent": 0,
    "reviews_received": 0,
}


class ProfileState(rx.State):
    active_tab: str = "discover"
    is_loading: bool = False
    is_saving: bool = False
    loaded: bool = False
    error: str = ""
    success: str = ""
    password_error: str = ""
    password_success: str = ""
    password_busy: bool = False

    headline: str = ""
    bio: str = ""
    avatar_seed: str = ""
    avatar_path: str = ""
    avatar_busy: bool = False
    avatar_error: str = ""
    username: str = ""
    nationality: str = ""
    nationality_code: str = ""
    nationality_flag: str = ""
    languages: str = ""
    skills: str = ""
    availability_note: str = ""

    home_city: str = ""
    home_country: str = ""
    current_city: str = ""
    # Structured street address parts (private; only ever used to describe the
    # member's own area to themselves).
    road_and_number: str = ""
    town: str = ""
    postcode: str = ""
    latitude: str = ""
    longitude: str = ""
    travel_radius_km: int = 10
    # Location sharing is a two-state privacy control: `hidden` (Off) or
    # `approximate`. Nothing exact is ever published. `show_location` is kept
    # in sync as (mode != 'hidden') so every existing query keeps working.
    show_location: bool = False
    location_busy: bool = False
    location_mode: str = "hidden"
    # Mode to persist once the browser returns a fresh one-shot exact fix.
    pending_location_mode: str = "approximate"
    location_status: str = ""
    location_error: str = ""
    geo_busy: bool = False
    # Bumped to ask the browser for exactly one fresh high-accuracy fix.
    geo_token: int = 0
    location_updated_label: str = ""
    selected_categories: list[str] = []
    category_options: list[str] = TASK_CATEGORIES

    helper_rating_avg: float = 0.0
    helper_rating_count: int = 0
    traveller_rating_avg: float = 0.0
    traveller_rating_count: int = 0
    combined_rating_avg: float = 0.0
    combined_rating_count: int = 0
    kindness_points: int = 0

    stats: ActivityStats = EMPTY_STATS
    entries: list[JournalEntry] = []
    received_reviews: list[ReceivedReview] = []
    open_received_review_ids: list[int] = []
    upcoming_jobs: list[UpcomingJob] = []
    pending_applications: list[PendingApplication] = []
    response_drafts: dict[str, str] = {}
    deciding_id: int = 0
    # Phone numbers are never shared with other users. This field is kept
    # only so legacy rows can be forced back to FALSE; it is never set true.
    show_phone_to_members: bool = False
    # My Profile disclosures (collapsed on arrival).
    information_open: bool = False
    skills_open: bool = False
    missing_skills_open: bool = False
    metrics_open: bool = False
    settings_open: bool = False
    notify_help_offers: bool = True
    notify_requests_in_my_field: bool = True
    requests_in_my_field_radius_km: int = 20
    field_radius_reset_token: int = 0
    notify_messages: bool = True
    notify_schedule_changes: bool = True
    notify_community_activity: bool = True
    notify_reminders: bool = True
    notification_preferences_busy: bool = False
    notification_preferences_error: str = ""
    notification_preferences_notice: str = ""
    # Private safety disclosure: the member's own blocked list.
    blocked_open: bool = False
    location_open: bool = False
    # Local, browser-only display preferences.
    appearance: str = rx.LocalStorage("system", name="gah_appearance")
    date_format: str = rx.LocalStorage("dmy", name="gah_date_format")
    distance_units: str = rx.LocalStorage("km", name="gah_distance_units")
    time_format: str = rx.LocalStorage("24h", name="gah_time_format")
    reduced_motion: str = rx.LocalStorage("off", name="gah_reduced_motion")
    # Calendar (.ics) export feedback.
    calendar_busy: bool = False
    calendar_error: str = ""
    calendar_notice: str = ""

    @rx.var
    def scheduled_job_count(self) -> int:
        """Upcoming jobs that carry a real date and time to export."""
        return len(
            [job for job in self.upcoming_jobs if job.get("has_schedule")]
        )

    @rx.event
    async def export_calendar(self):
        """Download the signed-in member's own accepted tasks as one .ics file.

        Every appointment is resolved server-side from the session's subscriber
        id: no client-supplied job id is ever trusted, and no coordinates leave
        the app.
        """
        auth = await self.get_state(AuthState)
        sid = auth.subscriber_id
        self.calendar_error = ""
        self.calendar_notice = ""
        if not sid.isdigit():
            self.calendar_error = (
                "Your session expired — please sign in again to export your "
                "calendar."
            )
            return
        self.calendar_busy = True
        rows = []
        try:
            async with rx.asession() as asession:
                rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT p.id, a.id, p.title,
                                   COALESCE(p.description, ''),
                                   COALESCE(p.location_name, ''),
                                   COALESCE(p.city, ''),
                                   COALESCE(p.country, ''),
                                   COALESCE(a.proposed_time, p.scheduled_for),
                                   COALESCE(p.duration_minutes, 60),
                                   CASE
                                       WHEN p.author_id = :sid
                                       THEN helper.display_name
                                       ELSE poster.display_name
                                   END
                            FROM skillkind_help_post p
                            JOIN skillkind_job_application a
                                ON a.post_id = p.id
                            JOIN skillkind_subscriber poster
                                ON poster.id = p.author_id
                            JOIN skillkind_subscriber helper
                                ON helper.id = a.helper_id
                            WHERE (p.author_id = :sid OR a.helper_id = :sid)
                              AND (a.status = 'accepted' OR p.status = 'matched')
                              AND a.status NOT IN ('declined', 'withdrawn')
                              AND COALESCE(a.proposed_time, p.scheduled_for)
                                  IS NOT NULL
                            ORDER BY
                                COALESCE(a.proposed_time, p.scheduled_for) ASC
                            LIMIT 100
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).all()
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.calendar_busy = False
            self.calendar_error = (
                "We couldn't build your calendar file just now. Please try "
                "again in a moment."
            )
            return
        base_url = public_base_url()
        events: list[CalendarEvent] = []
        for row in rows:
            starts_at = row[7]
            if starts_at is None:
                continue
            place = ", ".join(
                [
                    str(value)
                    for value in (row[4], row[5], row[6])
                    if str(value or "").strip()
                ]
            )
            description_parts = [
                f"With {str(row[9] or 'a Go and Help neighbour')}.",
                str(row[3] or "").strip(),
                "Confirm the final details in your Go and Help Inbox.",
            ]
            events.append(
                {
                    "uid": event_uid(int(row[0]), int(row[1])),
                    "starts_at": starts_at,
                    "duration_minutes": int(row[8] or 60),
                    "title": f"Go and Help: {str(row[2] or 'Help task')}",
                    "location": place,
                    "description": "\n".join(
                        part for part in description_parts if part
                    ),
                    "url": f"{base_url}/",
                }
            )
        self.calendar_busy = False
        if not events:
            self.calendar_error = (
                "There is nothing to export yet — no accepted job has a "
                "confirmed date and time."
            )
            return
        self.calendar_notice = (
            f"{len(events)} appointment(s) saved to {CALENDAR_FILENAME}."
        )
        return rx.download(data=build_ics(events), filename=CALENDAR_FILENAME)

    @rx.var
    def help_given_label(self) -> str:
        """Grammatical phrase for the number of times you helped someone."""
        count = int(self.stats["tasks_helped"])
        if count <= 0:
            return "No help given"
        if count == 1:
            return "1 help given"
        return f"{count} helps given"

    @rx.var
    def help_received_label(self) -> str:
        """Grammatical phrase for the number of times you were helped."""
        count = int(self.stats["tasks_received"])
        if count <= 0:
            return "No help received"
        if count == 1:
            return "1 help received"
        return f"{count} helps received"

    @rx.var
    def phone_visibility_label(self) -> str:
        """Phone numbers are private: there is nothing to opt into."""
        return "Your number can not be shared with other users"

    @rx.event
    def toggle_information(self):
        self.information_open = not self.information_open

    @rx.event
    def toggle_settings(self):
        self.settings_open = not self.settings_open
        if self.settings_open:
            return ProfileState.load_notification_preferences

    @rx.event(background=True)
    async def load_notification_preferences(self):
        from app.states.notification_state import notification_preferences
        from app.field_requests import field_preferences

        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            if not auth.is_signed_in or not sid.isdigit():
                return
        try:
            async with rx.asession() as session:
                raw = (
                    await session.execute(
                        text(
                            "SELECT permissions_json FROM skillkind_onboarding_progress WHERE subscriber_id = :sid"
                        ),
                        {"sid": int(sid)},
                    )
                ).scalar_one_or_none()
            preferences = notification_preferences(raw)
            async with self:
                if (
                    await self.get_state(AuthState)
                ).subscriber_id != sid or self.notification_preferences_busy:
                    return
                for key, enabled in preferences.items():
                    setattr(self, key, enabled)
                _, radius = field_preferences(raw)
                self.requests_in_my_field_radius_km = radius
                self.field_radius_reset_token += 1
                self.notification_preferences_error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if (await self.get_state(AuthState)).subscriber_id == sid:
                    self.notification_preferences_error = "We couldn't load your preferences. Please reopen Settings to retry."

    @rx.event
    def set_field_request_radius(self, value: float):
        from app.field_requests import validate_field_radius

        try:
            radius = validate_field_radius(value)
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.notification_preferences_error = str(e)
            return
        self.requests_in_my_field_radius_km = radius
        return ProfileState.save_field_request_radius(radius)

    @rx.event(background=True)
    async def save_field_request_radius(self, radius: int):
        from app.field_requests import (
            FIELD_RADIUS,
            persist_preference,
            validate_field_radius,
        )

        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            if not auth.is_signed_in or not sid.isdigit():
                return
        try:
            radius = validate_field_radius(radius)
            async with rx.asession() as session:
                await persist_preference(
                    session, int(sid), FIELD_RADIUS, radius
                )
                await session.commit()
            async with self:
                if (await self.get_state(AuthState)).subscriber_id == sid:
                    self.notification_preferences_error = ""
                    self.notification_preferences_notice = (
                        "Notification radius saved."
                    )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if (await self.get_state(AuthState)).subscriber_id == sid:
                    self.notification_preferences_notice = ""
                    self.notification_preferences_error = (
                        "Could not save the radius. Please try again."
                    )

    @rx.event(background=True)
    async def toggle_notification_preference(self, key: str):
        from app.models import ONBOARDING_LAST_STEP, GUIDED_TOUR_LAST_STEP
        from app.states.notification_state import (
            NOTIFICATION_PREFERENCE_KEYS,
            NotificationState,
            notification_preferences,
        )

        if key not in NOTIFICATION_PREFERENCE_KEYS:
            return
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            if (
                not auth.is_signed_in
                or not sid.isdigit()
                or self.notification_preferences_busy
            ):
                return
            self.notification_preferences_busy = True
            self.notification_preferences_error = ""
            self.notification_preferences_notice = "Saving…"
        try:
            async with rx.asession() as session:
                await session.execute(
                    text("""
                    INSERT INTO skillkind_onboarding_progress
                        (subscriber_id, current_step, completed_steps, answers_json,
                         permissions_json, completed_at, tour_current_step,
                         tour_completed_at, updated_at)
                    VALUES (:sid, :last, :steps, '{}', '{}', now(), :tour, now(), now())
                    ON CONFLICT (subscriber_id) DO NOTHING
                """),
                    {
                        "sid": int(sid),
                        "last": ONBOARDING_LAST_STEP,
                        "steps": ",".join(
                            str(i) for i in range(1, ONBOARDING_LAST_STEP + 1)
                        ),
                        "tour": GUIDED_TOUR_LAST_STEP,
                    },
                )
                raw = (
                    await session.execute(
                        text("""
                    SELECT permissions_json FROM skillkind_onboarding_progress
                    WHERE subscriber_id = :sid FOR UPDATE
                """),
                        {"sid": int(sid)},
                    )
                ).scalar_one()
                preferences = notification_preferences(raw)
                from app.field_requests import permission_values

                permissions = permission_values(raw)
                permissions[key] = not preferences[key]
                await session.execute(
                    text("""
                    UPDATE skillkind_onboarding_progress
                    SET permissions_json = :permissions, updated_at = now()
                    WHERE subscriber_id = :sid
                """),
                    {"sid": int(sid), "permissions": json.dumps(permissions)},
                )
                await session.commit()
            async with self:
                if (await self.get_state(AuthState)).subscriber_id != sid:
                    return
                for name, enabled in notification_preferences(
                    permissions
                ).items():
                    setattr(self, name, enabled)
                self.notification_preferences_busy = False
                self.notification_preferences_notice = (
                    "Notification preferences saved."
                )
            yield NotificationState.load_notifications
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if (await self.get_state(AuthState)).subscriber_id == sid:
                    self.notification_preferences_busy = False
                    self.notification_preferences_notice = ""
                    self.notification_preferences_error = (
                        "We couldn't save that change. Please try again."
                    )

    @rx.event
    def toggle_blocked(self):
        """Expand the private blocked-member list, loading it on open."""
        from app.states.block_state import BlockState

        self.blocked_open = not self.blocked_open
        if self.blocked_open:
            return BlockState.load_blocked_members

    @rx.event
    async def toggle_location(self):
        """Expand `My location` inline — never navigate anywhere.

        Opening the card seeds the shared map-pin picker from the saved profile
        coordinates so the pin the member already chose is still there.
        """
        from app.states.map_picker_state import MapPickerState

        self.location_open = not self.location_open
        self.error = ""
        self.success = ""
        picker = await self.get_state(MapPickerState)
        if not self.location_open:
            picker._close_key(PROFILE_PICKER_KEY)
            return
        latitude: float | None = None
        longitude: float | None = None
        try:
            if self.latitude.strip() and self.longitude.strip():
                latitude = float(self.latitude.strip())
                longitude = float(self.longitude.strip())
        except ValueError:
            latitude = None
            longitude = None
        picker._open_with_point(PROFILE_PICKER_KEY, latitude, longitude)

    @rx.event
    def set_appearance(self, value: str):
        self.appearance = (
            value if value in ("light", "dark", "system") else "system"
        )

    @rx.event
    def set_date_format(self, value: str):
        self.date_format = value if value in ("dmy", "mdy", "ymd") else "dmy"

    @rx.event
    def set_distance_units(self, value: str):
        self.distance_units = "mi" if value == "mi" else "km"

    @rx.event
    def set_time_format(self, value: str):
        self.time_format = "12h" if value == "12h" else "24h"

    @rx.var
    def date_format_label(self) -> str:
        return {
            "dmy": "Day–Month–Year",
            "mdy": "Month–Day–Year",
            "ymd": "Year–Month–Day",
        }.get(self.date_format, "Day–Month–Year")

    @rx.var
    def date_format_example(self) -> str:
        return {
            "dmy": "31–12–2025",
            "mdy": "12–31–2025",
            "ymd": "2025–12–31",
        }.get(self.date_format, "31–12–2025")

    @rx.var
    def settings_summary(self) -> str:
        appearance = {
            "light": "Day",
            "dark": "Night",
            "system": "System",
        }.get(self.appearance, "System")
        units = "Miles" if self.distance_units == "mi" else "Kilometres"
        clock = "12-hour" if self.time_format == "12h" else "24-hour"
        return (
            f"{appearance} appearance · {self.date_format_label} dates · "
            f"{units} · {clock} clock · Interface language"
        )

    @rx.var
    def location_card_summary(self) -> str:
        """Subtitle for the `My location` disclosure card."""
        city = self.current_city.strip()
        place = city if city else "No city set yet"
        return f"{place} – Address and map"

    @rx.var
    def location_mode_label(self) -> str:
        return {
            "hidden": "Off — your location is hidden",
            "approximate": "Approximate — shown 0.5–1 km away to all users",
        }.get(self.location_mode, "Off — your location is hidden")

    @rx.var
    def location_safety_note(self) -> str:
        """Foreground-only reassurance shown under the two-state control."""
        return (
            "Your approximate location of 0.5–1 km away is only shown to others "
            "when you select 'approximate'. Go and Help never tracks you in the background."
        )

    @rx.var
    def current_city_label(self) -> str:
        city = self.current_city.strip()
        if city:
            return city
        return "No city saved yet — add one in My information or Local area"

    @rx.var
    def combined_rating_percent(self) -> int:
        """Combined helper + helpee rating as a 0-100 percentage."""
        if self.combined_rating_count <= 0:
            return 0
        return max(0, min(100, round(self.combined_rating_avg / 5 * 100)))

    @rx.var
    def combined_rating_label(self) -> str:
        """Concise numeric context beside the five-star row."""
        if self.combined_rating_count <= 0:
            return "0 reviews"
        reviews = (
            "1 review"
            if self.combined_rating_count == 1
            else f"{self.combined_rating_count} reviews"
        )
        return f"{self.combined_rating_avg:.1f} out of 5 · {reviews}"

    @rx.var
    def combined_star_states(self) -> list[str]:
        """Five entries of 'full', 'half' or 'empty' from real review rows."""
        if self.combined_rating_count <= 0:
            return ["empty"] * 5
        states: list[str] = []
        for step in range(1, 6):
            remainder = self.combined_rating_avg - (step - 1)
            if remainder >= 0.75:
                states.append("full")
            elif remainder >= 0.25:
                states.append("half")
            else:
                states.append("empty")
        return states

    @rx.var
    def credential_chips(self) -> list[str]:
        """Languages and skills shown beneath the name, when present."""
        return (self.language_list + self.skill_list)[:6]

    @rx.var
    def handle_label(self) -> str:
        return f"@{self.username}" if self.username else "@ claim your handle"

    @rx.var
    def pending_count(self) -> int:
        return len(self.pending_applications)

    @rx.var
    def language_list(self) -> list[str]:
        return [p.strip() for p in self.languages.split(",") if p.strip()]

    @rx.var
    def skill_list(self) -> list[str]:
        return [p.strip() for p in self.skills.split(",") if p.strip()]

    @rx.var
    def selected_category_labels(self) -> list[str]:
        """Readable chips for every skill category this member selected."""
        return category_labels(self.selected_categories)

    @rx.var
    def skills_summary(self) -> str:
        chips = self.selected_category_labels
        extra = len(self.skill_list)
        if not chips and extra == 0:
            return "Choose the categories you can help with, and add anything else you know."
        parts = ", ".join(chips) if chips else "No categories yet"
        if extra:
            return f"{parts} · {extra} other skills listed"
        return parts

    @rx.event
    def close_missing_skills(self):
        self.missing_skills_open = False

    @rx.event
    async def open_required_skills(self):
        from app.states.discovery_state import DiscoveryState
        from app.states.map_picker_state import MapPickerState

        self.missing_skills_open = False
        self.active_tab = "profile"
        self.skills_open = True
        self.location_open = False
        (await self.get_state(DiscoveryState)).filter_panel_open = False
        (await self.get_state(MapPickerState))._close_key(PROFILE_PICKER_KEY)
        yield
        yield rx.call_script("""(() => {
            let attempts = 0;
            const focusSkills = () => {
                const box = document.getElementById('gah-skills-box');
                if (box) {
                    box.scrollIntoView({block: 'start', behavior: 'auto'});
                    box.focus({preventScroll: true});
                } else if (++attempts < 120) requestAnimationFrame(focusSkills);
            };
            requestAnimationFrame(focusSkills);
        })()""")

    async def _has_saved_skills(self, sid: str) -> bool:
        try:
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text(
                            "SELECT preferred_categories, skills FROM skillkind_profile "
                            "WHERE subscriber_id = :sid LIMIT 1"
                        ),
                        {"sid": int(sid)},
                    )
                ).first()
            return bool(
                row
                and (
                    normalize_categories(str(row[0] or "").split(","))
                    or str(row[1] or "").strip()
                )
            )
        except Exception as e:
            logging.exception(f"Error: {e}")
            raise

    @rx.event
    async def seed_profile_picker(self):
        from app.states.map_picker_state import MapPickerState

        picker = await self.get_state(MapPickerState)
        lat, lon, problem = _parse_coordinate_pair(self.coordinates_value)
        if not problem:
            picker._open_with_point(PROFILE_PICKER_KEY, lat, lon)

    @rx.event
    def toggle_skills(self):
        self.skills_open = not self.skills_open
        self.error = ""
        self.success = ""

    @rx.event
    def toggle_metrics(self):
        """Open or close the Premium `Metrics Information` disclosure."""
        self.metrics_open = not self.metrics_open

    @rx.var
    def active_tab_label(self) -> str:
        labels = {
            "profile": "My Profile",
            "help": "Requests",
            "upcoming": "Requests",
            "get_help": "Requests",
            "community": "Community",
            "inbox": "Inbox",
            "discover": "Discover jobs",
            "post": "Ask for help",
            "people": "Find people",
            "contacts": "Contacts",
            "details": "Profile details",
            "messages": "Messages",
            "area": "My Profile",
            "activity": "Activity",
            "admin": "Backend",
        }
        return labels.get(self.active_tab, "Discover jobs")

    def _row_to_upcoming_job(self, row) -> UpcomingJob:
        category = str(row[4] or "")
        reward_type = str(row[5] or "")
        location_parts = [
            str(value or "") for value in (row[8], row[9], row[10]) if value
        ]
        location = ", ".join(location_parts) or "Location to agree"
        scheduled = (
            row[11].strftime("%A, %b %d %Y · %H:%M")
            if row[11] is not None
            else "Time to agree"
        )
        proposed_available = (
            row[12].strftime("%A, %b %d %Y · %H:%M")
            if row[12] is not None
            else "No availability proposed yet"
        )
        return {
            "id": int(row[0]),
            "role_label": str(row[1] or ""),
            "other_name": str(row[2] or "A Go and Help neighbour"),
            "title": str(row[3] or "Help appointment"),
            "category": category,
            "category_label": CATEGORY_LABELS.get(
                category, category.replace("_", " ").title()
            ),
            "reward": REWARD_LABELS.get(
                reward_type, reward_type.replace("_", " ").title()
            ),
            "reward_details": str(row[6] or ""),
            "location": location,
            "scheduled": scheduled,
            "proposed_available": proposed_available,
            "status": str(row[13] or "matched").title(),
            "conversation_hint": str(
                row[14] or "Open Messages to agree the final details."
            ),
            "has_schedule": row[11] is not None or row[12] is not None,
        }

    @rx.var
    def on_map(self) -> bool:
        """True while the signed-in home map is the active screen."""
        return self.active_tab == "discover"

    @staticmethod
    def _normalize_tab(tab: str) -> str:
        """Upcoming and Get help are folded into the combined Help surface."""
        if tab in ("upcoming", "get_help"):
            return "help"
        if tab == "area":
            return "profile"
        return tab

    @rx.event
    def set_active_tab(self, tab: str):
        self.active_tab = self._normalize_tab(tab)
        self.error = ""
        self.success = ""
        if self.active_tab != "profile":
            self.location_open = False

    @rx.event
    async def open_reviews(self):
        """Open Community Reviews from the profile rating button."""
        from app.states.community_state import CommunityState

        community = await self.get_state(CommunityState)
        self.set_active_tab("community")
        return community.set_section("reviews")

    @rx.event
    def close_section_overlay(self):
        """Return to the map screen from any member section."""
        self.active_tab = "discover"
        self.error = ""
        self.success = ""

    async def _dismiss_navigation_surfaces(self):
        from app.states.block_state import BlockState
        from app.states.content_report_state import ContentReportState
        from app.states.discovery_state import DiscoveryState
        from app.states.event_state import EventState
        from app.states.guest_map_state import GuestMapState
        from app.states.help_share_state import HelpShareState
        from app.states.map_picker_state import MapPickerState
        from app.states.membership_state import MembershipState
        from app.states.notification_state import NotificationState
        from app.states.policy_state import PolicyState
        from app.states.unified_inbox_state import UnifiedInboxState
        from app.states.world_search_state import WorldSearchState

        discovery = await self.get_state(DiscoveryState)
        discovery.clear_selection()
        discovery.is_loading_direct = False
        discovery.filter_panel_open = False
        discovery.category_list_open = False
        (await self.get_state(EventState)).selected_event = []
        (await self.get_state(NotificationState)).panel_open = False
        (await self.get_state(WorldSearchState)).expanded = False
        self.settings_open = False
        self.missing_skills_open = False
        inbox = await self.get_state(UnifiedInboxState)
        inbox.view = "inbox"
        inbox.messages_open = False
        inbox.open_offer_ids = []
        inbox.offers_open = False
        inbox.requests_open = False
        await inbox._clear_selections()
        from app.states.messaging_state import MessagingState

        (await self.get_state(MessagingState)).pending_thread_id = 0
        (await self.get_state(MembershipState)).paywall_open = False
        (await self.get_state(PolicyState)).close_policy()
        (await self.get_state(ContentReportState)).close_report()
        (await self.get_state(BlockState)).close_block()
        (await self.get_state(HelpShareState)).close()
        (await self.get_state(MapPickerState)).close_picker()
        guest = await self.get_state(GuestMapState)
        guest.close_wall()

    @rx.event
    async def return_to_map(self):
        """Members return to the map; visitors see the existing join prompt."""
        from app.states.guest_map_state import GuestMapState
        from app.states.discovery_state import DiscoveryState

        auth = await self.get_state(AuthState)
        if not auth.is_signed_in:
            guest_map = await self.get_state(GuestMapState)
            guest_map.open_join_prompt()
            return

        await self._dismiss_navigation_surfaces()
        self.active_tab = "discover"
        self.error = ""
        self.success = ""
        # The logo always lands on the map itself, never a list of results.
        (await self.get_state(DiscoveryState)).view_mode = "map"

    @rx.event
    async def navigate_from_bottom_nav(self, tab: str, reason: str):
        from app.states.guest_map_state import GuestMapState

        from app.states.membership_state import MembershipState

        from app.states.notification_state import NotificationState

        auth = await self.get_state(AuthState)
        tab = self._normalize_tab(tab)
        if auth.is_signed_in:
            await self._dismiss_navigation_surfaces()
            self.active_tab = tab
            self.error = ""
            self.success = ""
            if tab == "help":
                # Optimistically clear the green Help dot, then persist it.
                notifications = await self.get_state(NotificationState)
                notifications.help_unread = 0
                yield NotificationState.mark_help_read
            elif tab == "profile":
                from app.states.profile_metrics_state import ProfileMetricsState

                yield MembershipState.load_membership
                yield ProfileMetricsState.load_metrics
            return
        auth.set_auth_tab("signin")
        guest_map = await self.get_state(GuestMapState)
        trimmed = (reason or "").strip()
        if trimmed:
            guest_map.wall_open = True
            guest_map.wall_reason = trimmed
        else:
            # Unified guest join prompt for every non-Map dock action.
            guest_map.wall_open = True
            guest_map.wall_reason = ""

    @rx.var
    def has_exact_coordinates(self) -> bool:
        return self.latitude.strip() != "" and self.longitude.strip() != ""

    @rx.var
    def coordinates_value(self) -> str:
        """The combined `latitude, longitude` value for the single field."""
        lat = self.latitude.strip()
        lon = self.longitude.strip()
        if not lat or not lon:
            return ""
        return f"{lat}, {lon}"

    @rx.event(background=True)
    async def set_location_mode(self, mode: str):
        """Off / Approximate — persisted immediately, one-shot only.

        Approximate needs a private exact source point: when none is stored
        yet the browser is asked for exactly one fix (a foreground
        `getCurrentPosition` call started by this tap), and the chosen mode is
        persisted as soon as that fix arrives. Legacy `live` is mapped to
        `approximate`; nothing exact is ever published.
        """
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            has_point = (
                self.latitude.strip() != "" and self.longitude.strip() != ""
            )
            self.location_error = ""
            self.location_status = ""
            self.error = ""
            self.success = ""
        target = (
            "approximate"
            if mode in ("approximate", "live", "refresh")
            else "hidden"
        )
        if not sid.isdigit():
            async with self:
                self.location_error = (
                    "Your session expired — please sign in again."
                )
            return
        if target == "approximate":
            try:
                eligible = await self._has_saved_skills(sid)
            except Exception as e:
                logging.exception(f"Error: {e}")
                async with self:
                    self.location_error = (
                        "We couldn't check your skills. Please try again."
                    )
                return
            async with self:
                if (await self.get_state(AuthState)).subscriber_id != sid:
                    return
                if not eligible:
                    self.missing_skills_open = True
                    self.geo_busy = False
                    return
                self.missing_skills_open = False
        if target == "approximate" and (not has_point or mode == "refresh"):
            async with self:
                self.pending_location_mode = target
                self.geo_busy = True
                self.location_status = "Asking your browser for your position…"
                self.geo_token = self.geo_token + 1
            return
        visible = target != "hidden"
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_profile
                    SET location_mode = :mode,
                        show_location = :visible,
                        location_updated_at = CASE
                            WHEN :visible = TRUE THEN now()
                            ELSE location_updated_at
                        END,
                        updated_at = now()
                    WHERE subscriber_id = :sid
                    """
                ),
                {"mode": target, "visible": visible, "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.location_mode = target
            from app.states.discovery_state import DiscoveryState

            discovery = await self.get_state(DiscoveryState)
            discovery.distance_warning = False
            if target != "approximate":
                discovery.distance_km = 0
                discovery.distance_reset_token += 1
            self.show_location = visible
            self.geo_busy = False
            if visible:
                self.location_updated_label = "Updated just now"
                self.location_status = "Your Approximate location is shown between 500m and 1km away."
            else:
                self.location_status = ""
        from app.states.event_state import EventState

        yield EventState.sync_map_location
        yield DiscoveryState.refresh_board

    @rx.event
    def request_live_location(self):
        """One-shot refresh of the private source point, started by a tap.

        The name is kept to avoid churn; the semantics are a single foreground
        `getCurrentPosition` request that always saves into approximate mode.
        """
        return ProfileState.set_location_mode("refresh")

    @rx.event(background=True)
    async def save_live_position(
        self, latitude: float, longitude: float, accuracy: float
    ):
        """Persist the one-shot exact fix privately, in approximate mode."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            target = "approximate"
            if not self.geo_busy:
                return
        if not sid.isdigit():
            async with self:
                self.geo_busy = False
                self.location_error = (
                    "Your session expired — please sign in again."
                )
            return
        try:
            eligible = await self._has_saved_skills(sid)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.geo_busy = False
                self.location_error = (
                    "We couldn't check your skills. Please try again."
                )
            return
        if not eligible:
            async with self:
                self.geo_busy = False
                self.missing_skills_open = True
            return
        lat = max(-90.0, min(90.0, float(latitude)))
        lon = max(-180.0, min(180.0, float(longitude)))
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_profile
                    SET latitude = :lat, longitude = :lon,
                        location_mode = :mode, show_location = TRUE,
                        location_updated_at = now(), updated_at = now()
                    WHERE subscriber_id = :sid
                    """
                ),
                {"lat": lat, "lon": lon, "mode": target, "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.latitude = f"{lat:.6f}"
            self.longitude = f"{lon:.6f}"
            self.location_mode = target
            self.show_location = True
            self.geo_busy = False
            self.location_error = ""
            self.location_updated_label = "Updated just now"
            self.location_status = (
                "Your Approximate location is shown between 500m and 1km away."
            )
        from app.states.event_state import EventState
        from app.states.discovery_state import DiscoveryState

        yield EventState.sync_map_location
        yield DiscoveryState.refresh_board

    @rx.event
    def live_location_failed(self, message: str):
        self.geo_busy = False
        self.location_status = ""
        self.location_error = message or (
            "We could not read your location. Please try again."
        )

    @rx.event
    def set_response_draft(self, app_key: str, value: str):
        self.response_drafts[app_key] = value

    @rx.event
    def toggle_category(self, category: str):
        """Multi-select across every current category — no cap for helpers."""
        if category in self.selected_categories:
            self.selected_categories = [
                item for item in self.selected_categories if item != category
            ]
        else:
            self.selected_categories = normalize_categories(
                [*self.selected_categories, category]
            )
        self.error = ""
        self.success = ""

    @rx.event(background=True)
    async def save_skills(self, form_data: dict[str, Any]):
        """Persist `preferred_categories` and the free-text `skills` column."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            categories = normalize_categories(self.selected_categories)
        other = str(form_data.get("skills", "") or "").strip()
        other = ", ".join(
            part.strip() for part in other.split(",") if part.strip()
        )[:500]
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif not categories and len(other) < 3:
            problem = (
                "Choose at least one category, or describe your other skills "
                "and knowledge."
            )
        if problem:
            async with self:
                self.error = problem
                self.success = ""
                self.skills_open = True
            return
        async with self:
            self.is_saving = True
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_profile
                    SET preferred_categories = :categories,
                        skills = :skills,
                        updated_at = now()
                    WHERE subscriber_id = :sid
                    """
                ),
                {
                    "categories": ",".join(categories),
                    "skills": other,
                    "sid": int(sid),
                },
            )
            await asession.commit()
        async with self:
            self.selected_categories = categories
            self.skills = other
            self.is_saving = False
            self.success = "Skills and knowledge saved."
        yield rx.toast("Skills and knowledge saved.", duration=3000)

    @rx.event(background=True)
    async def change_password(self, form_data: dict[str, Any]):
        current = str(form_data.get("current_password", "") or "")
        password = str(form_data.get("new_password", "") or "")
        confirm = str(form_data.get("confirm_password", "") or "")
        async with self:
            if self.password_busy:
                return
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            problem = ""
            if not auth.is_signed_in or not sid.isascii() or not sid.isdigit():
                problem = "Your session expired — please sign in again."
            elif not current:
                problem = "Enter your current password."
            elif len(password) < 6:
                problem = "Passwords need at least 6 characters."
            elif password != confirm:
                problem = "The two passwords don't match."
            elif password == current:
                problem = "Choose a new password different from your current password."
            self.password_error = problem
            self.password_success = ""
            if problem:
                return
            self.password_busy = True
        updated = None
        try:
            async with rx.asession() as session:
                try:
                    updated = (
                        await session.execute(
                            text("""
                            UPDATE skillkind_subscriber
                            SET password_hash = :new_hash
                            WHERE id = :sid AND password_hash = :current_hash
                              AND is_active = TRUE
                            RETURNING id
                        """),
                            {
                                "sid": int(sid),
                                "current_hash": hash_password(current),
                                "new_hash": hash_password(password),
                            },
                        )
                    ).first()
                    if updated is None:
                        await session.rollback()
                    else:
                        await session.execute(
                            text("""
                                UPDATE skillkind_password_reset_token
                                SET invalidated_at = now()
                                WHERE subscriber_id = :sid
                                  AND used_at IS NULL
                                  AND invalidated_at IS NULL
                            """),
                            {"sid": int(sid)},
                        )
                        await session.commit()
                except Exception as e:
                    logging.exception(f"Error: {e}")
                    await session.rollback()
                    raise
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if (await self.get_state(AuthState)).subscriber_id == sid:
                    self.password_busy = False
                    self.password_error = "We couldn't save that password just now. Please try again."
            return
        async with self:
            if (await self.get_state(AuthState)).subscriber_id != sid:
                return
            self.password_busy = False
            if updated is None:
                self.password_error = "Current password is incorrect."
                return
            self.password_error = ""
            self.password_success = "Your password has been changed."
            language = (await self.get_state(AuthState)).preferred_language
        from app.interface_i18n import translate

        yield rx.toast(translate(language, "Password changed."), duration=4000)

    @rx.event
    def clear_profile(self):
        self.password_error = ""
        self.password_success = ""
        self.password_busy = False
        self.notify_help_offers = True
        self.notify_messages = True
        self.notify_schedule_changes = True
        self.notify_community_activity = True
        self.notify_reminders = True
        self.notification_preferences_busy = False
        self.notification_preferences_error = ""
        self.notification_preferences_notice = ""
        self.active_tab = "discover"
        self.loaded = False
        self.is_loading = False
        self.error = ""
        self.success = ""
        self.headline = ""
        self.bio = ""
        self.avatar_seed = ""
        self.avatar_path = ""
        self.avatar_error = ""
        self.avatar_busy = False
        self.username = ""
        self.nationality = ""
        self.nationality_code = ""
        self.nationality_flag = ""
        self.languages = ""
        self.skills = ""
        self.availability_note = ""
        self.home_city = ""
        self.home_country = ""
        self.current_city = ""
        self.road_and_number = ""
        self.town = ""
        self.postcode = ""
        self.latitude = ""
        self.longitude = ""
        self.travel_radius_km = 10
        self.location_open = False
        self.show_location = False
        self.location_busy = False
        self.location_mode = "hidden"
        self.pending_location_mode = "approximate"
        self.location_status = ""
        self.location_error = ""
        self.location_updated_label = ""
        self.geo_busy = False
        self.selected_categories = []
        self.skills_open = False
        self.missing_skills_open = False
        self.helper_rating_avg
        self.helper_rating_count = 0
        self.traveller_rating_avg = 0.0
        self.traveller_rating_count = 0
        self.combined_rating_avg = 0.0
        self.combined_rating_count = 0
        self.kindness_points = 0
        self.stats = EMPTY_STATS
        self.entries = []
        self.received_reviews = []
        self.open_received_review_ids = []
        self.upcoming_jobs = []
        self.pending_applications = []
        self.response_drafts = {}
        self.deciding_id = 0
        self.calendar_busy = False
        self.calendar_error = ""
        self.calendar_notice = ""

    @rx.event
    def toggle_received_review(self, review_id: int):
        if review_id in self.open_received_review_ids:
            self.open_received_review_ids = [
                value
                for value in self.open_received_review_ids
                if value != review_id
            ]
        elif any(review["id"] == review_id for review in self.received_reviews):
            self.open_received_review_ids = [
                *self.open_received_review_ids,
                review_id,
            ]

    @rx.event(background=True)
    async def load_profile(self):
        async with self:
            if self.is_loading:
                return
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id
            owner_seed = f"member-{sid}"
            if not sid.isdigit():
                self.loaded = False
                self.is_loading = False
                self.upcoming_jobs = []
                self.pending_applications = []
                return
            self.is_loading = True
            self.error = ""
        try:
            await self._load_profile_data(sid, owner_seed)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                self.loaded = False
                self.error = (
                    "We couldn't load your profile just now. Please try again."
                )
            return
        yield ProfileState.load_notification_preferences

    async def _load_profile_data(self, sid: str, owner_seed: str) -> None:
        async with rx.asession() as asession:
            profile_row = (
                await asession.execute(
                    text(
                        """
                        SELECT headline, bio, CONCAT('member-', subscriber_id), home_city, home_country,
                               current_city, latitude, longitude, travel_radius_km,
                               languages, skills, preferred_categories,
                               availability_note,
                               COALESCE(helper_rating_avg, 0), COALESCE(helper_rating_count, 0),
                               COALESCE(traveller_rating_avg, 0), COALESCE(traveller_rating_count, 0),
                               COALESCE(kindness_points, 0),
                               COALESCE(username, ''),
                               COALESCE(avatar_path, ''),
                               COALESCE(nationality, ''),
                               COALESCE(show_location, FALSE),
                               COALESCE(location_mode, 'hidden'),
                               location_updated_at,
                               COALESCE(show_phone_to_members, FALSE),
                               COALESCE(road_and_number, ''),
                               COALESCE(town, ''),
                               COALESCE(postcode, '')
                        FROM skillkind_profile
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
            stats_row = (
                await asession.execute(
                    text(
                        f"""
                        SELECT
                            (SELECT COUNT(*) FROM skillkind_help_post WHERE author_id = :sid),
                            (SELECT COUNT(*) FROM skillkind_help_post WHERE author_id = :sid AND status = 'open'),
                            (SELECT COUNT(*) FROM skillkind_job_application WHERE helper_id = :sid),
                            (SELECT COUNT(*) FROM skillkind_job_application WHERE helper_id = :sid AND status = 'accepted'),
                            (SELECT COUNT(*) FROM skillkind_completed_task WHERE helper_id = :sid),
                            (SELECT COUNT(*) FROM skillkind_completed_task WHERE poster_id = :sid),
                            (SELECT COUNT(*) FROM skillkind_message WHERE sender_id = :sid),
                            (SELECT COUNT(*) FROM skillkind_review r WHERE r.reviewee_id = :sid AND {review_released_sql()})
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
            rating_row = (
                await asession.execute(
                    text(
                        f"""
                        SELECT COALESCE(AVG(r.rating), 0), COUNT(*)
                        FROM skillkind_review r
                        WHERE r.reviewee_id = :sid AND r.rating IS NOT NULL
                          AND {review_released_sql()}
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
            entry_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT title, status, category, created_at
                        FROM skillkind_help_post
                        WHERE author_id = :sid
                        ORDER BY created_at DESC
                        LIMIT 5
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            review_rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT r.id, reviewer.display_name, reviewer.id,
                               r.direction, COALESCE(r.rating, 0),
                               COALESCE(r.comment, ''),
                               COALESCE(r.kindness_flag, FALSE), r.created_at,
                               COALESCE(r.category_one, 0),
                               COALESCE(r.category_two, 0),
                               COALESCE(r.category_three, 0),
                               COALESCE(r.category_four, 0),
                               COALESCE(reviewer.is_verified, FALSE),
                               COALESCE(p.title, ''),
                               COALESCE(rp.avatar_path, '')
                        FROM skillkind_review r
                        JOIN skillkind_subscriber reviewer
                          ON reviewer.id = r.reviewer_id
                        JOIN skillkind_completed_task ct
                          ON ct.id = r.completed_task_id
                        JOIN skillkind_help_post p ON p.id = ct.post_id
                        LEFT JOIN skillkind_profile rp
                          ON rp.subscriber_id = reviewer.id
                        WHERE r.reviewee_id = :sid AND {review_released_sql()}
                        ORDER BY r.created_at DESC
                        LIMIT 8
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            try:
                upcoming_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT
                                p.id,
                                CASE
                                    WHEN p.author_id = :sid
                                    THEN 'You posted this job'
                                    ELSE 'You are helping'
                                END,
                                CASE
                                    WHEN p.author_id = :sid
                                    THEN helper.display_name
                                    ELSE poster.display_name
                                END,
                                p.title,
                                p.category,
                                p.reward_type,
                                COALESCE(p.reward_details, ''),
                                a.status,
                                p.location_name,
                                p.city,
                                p.country,
                                p.scheduled_for,
                                a.proposed_time,
                                CASE
                                    WHEN a.status = 'accepted'
                                         AND p.status = 'matched'
                                    THEN 'accepted · matched'
                                    WHEN a.status = 'accepted'
                                    THEN 'accepted'
                                    ELSE 'matched'
                                END,
                                CASE
                                    WHEN p.author_id = :sid
                                    THEN 'Your helper is on the way — open Messages to agree the final details.'
                                    ELSE 'Your offer is in — open Messages to confirm the meeting.'
                                END
                            FROM skillkind_help_post p
                            JOIN skillkind_job_application a
                              ON a.post_id = p.id
                            JOIN skillkind_subscriber poster
                              ON poster.id = p.author_id
                            JOIN skillkind_subscriber helper
                              ON helper.id = a.helper_id
                            WHERE (p.author_id = :sid OR a.helper_id = :sid)
                              AND (a.status = 'accepted' OR p.status = 'matched')
                              AND a.status NOT IN ('declined', 'withdrawn')
                              AND NOT EXISTS (
                                  SELECT 1 FROM skillkind_member_block mb
                                  WHERE (mb.blocker_id = p.author_id
                                         AND mb.blocked_id = a.helper_id)
                                     OR (mb.blocker_id = a.helper_id
                                         AND mb.blocked_id = p.author_id)
                              )
                            ORDER BY
                                COALESCE(a.proposed_time, p.scheduled_for) ASC NULLS LAST,
                                p.created_at DESC
                            LIMIT 20
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).all()
            except Exception as e:
                logging.exception(f"Error: {e}")
                raise
            try:
                pending_rows = (
                    await asession.execute(
                        text(
                            f"""
                            SELECT a.id, p.id, p.title, p.status, p.category,
                                   p.reward_type, COALESCE(p.reward_details, ''),
                                   COALESCE(p.location_name, ''),
                                   COALESCE(p.city, ''), COALESCE(p.country, ''),
                                   p.scheduled_for, a.proposed_time, a.created_at,
                                   COALESCE(a.pitch, ''),
                                   h.display_name, CONCAT('member-', h.id),
                                   COALESCE(hp.username, ''),
                                   COALESCE(hp.avatar_path, ''),
                                   COALESCE(hp.nationality, ''),
                                   (SELECT COALESCE(AVG(r.rating), 0) FROM skillkind_review r
                                    WHERE r.reviewee_id = h.id AND r.direction = 'poster_to_helper'
                                      AND {review_released_sql()}),
                                   (SELECT COUNT(*) FROM skillkind_review r
                                    WHERE r.reviewee_id = h.id AND r.direction = 'poster_to_helper'
                                      AND {review_released_sql()}),
                                   COALESCE(hp.tasks_helped_count, 0),
                                   COALESCE(h.is_verified, FALSE)
                            FROM skillkind_job_application a
                            JOIN skillkind_help_post p ON p.id = a.post_id
                            JOIN skillkind_subscriber h ON h.id = a.helper_id
                            LEFT JOIN skillkind_profile hp
                              ON hp.subscriber_id = h.id
                            WHERE p.author_id = :sid
                              AND a.status = 'pending'
                              AND p.status IN ('open', 'matched')
                              AND NOT EXISTS (
                                  SELECT 1 FROM skillkind_member_block mb
                                  WHERE (mb.blocker_id = :sid
                                         AND mb.blocked_id = a.helper_id)
                                     OR (mb.blocker_id = a.helper_id
                                         AND mb.blocked_id = :sid)
                              )
                            ORDER BY a.created_at ASC
                            LIMIT 30
                            """
                        ),
                        {"sid": int(sid)},
                    )
                ).all()
            except Exception as e:
                logging.exception(f"Error: {e}")
                raise
        async with self:
            if (await self.get_state(AuthState)).subscriber_id != sid:
                self.is_loading = False
                return
            if profile_row is not None:
                self.headline = str(profile_row[0] or "")
                self.bio = str(profile_row[1] or "")
                self.avatar_seed = f"member-{sid}"
                self.home_city = str(profile_row[3] or "")
                self.home_country = str(profile_row[4] or "")
                self.current_city = str(profile_row[5] or "")
                self.latitude = (
                    ""
                    if profile_row[6] is None
                    else f"{float(profile_row[6]):.6f}"
                )
                self.longitude = (
                    ""
                    if profile_row[7] is None
                    else f"{float(profile_row[7]):.6f}"
                )
                self.travel_radius_km = int(profile_row[8] or 10)
                self.road_and_number = str(profile_row[25] or "")
                self.town = str(profile_row[26] or "")
                self.postcode = str(profile_row[27] or "")
                self.languages = str(profile_row[9] or "")
                self.skills = str(profile_row[10] or "")
                self.selected_categories = [
                    c.strip()
                    for c in str(profile_row[11] or "").split(",")
                    if c.strip()
                ]
                self.availability_note = str(profile_row[12] or "")
                self.helper_rating_avg = float(profile_row[13])
                self.helper_rating_count = int(profile_row[14])
                self.traveller_rating_avg = float(profile_row[15])
                self.traveller_rating_count = int(profile_row[16])
                self.kindness_points = int(profile_row[17])
                self.username = str(profile_row[18] or "")
                self.avatar_path = str(profile_row[19] or "")
                self.show_location = bool(profile_row[21])
                # Phone numbers are private for everyone, whatever a legacy
                # row says.
                self.show_phone_to_members = False
                stored_mode = str(profile_row[22] or "hidden")
                # Legacy rows may still say 'fixed' or 'live': both are read
                # as approximate, and are only ever published approximately.
                if stored_mode in ("fixed", "live"):
                    stored_mode = "approximate"
                self.location_mode = (
                    stored_mode
                    if stored_mode in ("hidden", "approximate")
                    else "hidden"
                )
                self.location_updated_label = (
                    ""
                    if profile_row[23] is None
                    else profile_row[23].strftime("Updated %b %d, %Y at %H:%M")
                )
                resolved = resolve_nationality(
                    str(profile_row[20] or "").strip() or self.home_country
                )
                self.nationality = resolved[0]
                self.nationality_code = resolved[1]
                self.nationality_flag = resolved[2]
                self.loaded = True
            else:
                self.avatar_seed = f"member-{sid}"
                self.loaded = False
                self.error = (
                    "We couldn't find your profile page — try signing in again."
                )
            if rating_row is not None:
                self.combined_rating_avg = float(rating_row[0] or 0)
                self.combined_rating_count = int(rating_row[1] or 0)
            else:
                self.combined_rating_avg = 0.0
                self.combined_rating_count = 0
            if stats_row is not None:
                self.stats = {
                    "posts_created": int(stats_row[0] or 0),
                    "posts_open": int(stats_row[1] or 0),
                    "applications_sent": int(stats_row[2] or 0),
                    "applications_accepted": int(stats_row[3] or 0),
                    "tasks_helped": int(stats_row[4] or 0),
                    "tasks_received": int(stats_row[5] or 0),
                    "messages_sent": int(stats_row[6] or 0),
                    "reviews_received": int(stats_row[7] or 0),
                }
            self.entries = [
                {
                    "title": str(r[0]),
                    "status": str(r[1]),
                    "category": CATEGORY_LABELS.get(
                        r[2] or "",
                        str(r[2] or "").replace("_", " ").title(),
                    ),
                    "created": r[3].strftime("%b %d, %Y")
                    if r[3] is not None
                    else "",
                }
                for r in entry_rows
            ]
            self.received_reviews = [
                {
                    "id": int(r[0]),
                    "reviewer_id": int(r[2]),
                    "reviewer_name": str(r[1] or "A Go and Help neighbour"),
                    "reviewer_seed": str(r[2]),
                    "reviewer_verified": bool(r[12]),
                    "job_title": str(r[13] or ""),
                    "reviewer_avatar": str(r[14] or ""),
                    "rating": int(r[4] or 0),
                    "percent": max(
                        0, min(100, round(int(r[4] or 0) / 5 * 100))
                    ),
                    "comment": decode_review_content(r[5])[0],
                    "response": decode_review_content(r[5])[1],
                    "kindness_flag": bool(r[6]),
                    "created": r[7].strftime("%b %d, %Y")
                    if r[7] is not None
                    else "",
                    "categories": _review_categories(
                        str(r[3] or ""),
                        [
                            int(r[8] or 0),
                            int(r[9] or 0),
                            int(r[10] or 0),
                            int(r[11] or 0),
                        ],
                    ),
                }
                for r in review_rows
            ]
            self.upcoming_jobs = [
                self._row_to_upcoming_job(row) for row in upcoming_rows
            ]
            self.pending_applications = [
                self._row_to_pending(row) for row in pending_rows
            ]
            self.is_loading = False

    def _row_to_pending(self, row) -> PendingApplication:
        category = str(row[4] or "")
        reward_type = str(row[5] or "")
        location_parts = [
            str(value or "") for value in (row[7], row[8], row[9]) if value
        ]
        helper_country = resolve_nationality(str(row[18] or ""))
        avg = float(row[19] or 0)
        return {
            "id": int(row[0]),
            "key": str(int(row[0])),
            "post_id": int(row[1]),
            "post_title": str(row[2] or "Help request"),
            "post_status": str(row[3] or "open"),
            "category_label": CATEGORY_LABELS.get(
                category, category.replace("_", " ").title()
            ),
            "reward": REWARD_LABELS.get(
                reward_type, reward_type.replace("_", " ").title()
            ),
            "reward_details": str(row[6] or ""),
            "location": ", ".join(location_parts) or "Location to agree",
            "scheduled": row[10].strftime("%A, %b %d %Y · %H:%M")
            if row[10] is not None
            else "Time to agree",
            "proposed_time": row[11].strftime("%A, %b %d %Y · %H:%M")
            if row[11] is not None
            else "No time proposed yet",
            "applied": row[12].strftime("%b %d, %Y · %H:%M")
            if row[12] is not None
            else "",
            "pitch": str(row[13] or ""),
            "helper_name": str(row[14] or "A Go and Help neighbour"),
            "helper_avatar_seed": str(row[15] or "neighbour"),
            "helper_verified": bool(row[22]),
            "helper_handle": f"@{row[16]}" if row[16] else "",
            "helper_avatar": str(row[17] or ""),
            "helper_nationality": helper_country[0],
            "helper_flag": helper_country[2],
            "helper_score": max(0, min(100, round(avg / 5 * 100))),
            "helper_reviews": int(row[20] or 0),
            "helper_helped": int(row[21] or 0),
        }

    @rx.event
    async def handle_avatar_upload(self, files: list[rx.UploadFile]):
        """Store an auto-oriented, cropped, compressed WebP profile photo."""
        if not files:
            return
        auth = await self.get_state(AuthState)
        sid = auth.subscriber_id
        if not sid.isdigit():
            self.avatar_error = "Your session expired — please sign in again."
            return
        upload = files[0]
        suffix = Path(upload.name).suffix.lower()
        content_type = str(getattr(upload, "content_type", "") or "").lower()
        if suffix not in ALLOWED_IMAGE_SUFFIXES:
            self.avatar_error = "Use JPEG/JPG, PNG or WebP, maximum 3 MB. No video or animation; stored photos are under 1 MB."
            return
        self.avatar_busy = True
        self.avatar_error = ""
        try:
            raw = await read_image_upload(upload)
            payload = process_avatar_bytes(raw, upload.name, content_type)
        except ValueError:
            self.avatar_busy = False
            self.avatar_error = "Use a static JPEG/JPG, PNG or WebP photo no larger than 3 MB. No video."
            return
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.avatar_busy = False
            self.avatar_error = "Use a static JPEG/JPG, PNG or WebP photo no larger than 3 MB. No video."
            return
        if payload is None:
            self.avatar_busy = False
            self.avatar_error = (
                "We couldn't read that image — try another photo."
            )
            return
        filename = f"avatar_{uuid4().hex}{AVATAR_SUFFIX}"
        try:
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            with (upload_dir / filename).open("wb") as output_file:
                output_file.write(payload)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.avatar_busy = False
            self.avatar_error = "We couldn't save that photo. Please try again."
            return
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_profile
                    SET avatar_path = :path, updated_at = now()
                    WHERE subscriber_id = :sid
                    """
                ),
                {"path": filename, "sid": int(sid)},
            )
            await asession.commit()
        self.avatar_path = filename
        self.avatar_busy = False
        self.success = "Profile photo updated."
        return rx.toast("Profile photo updated.", duration=3000)

    @rx.event(background=True)
    async def confirm_application(self, application_id: int):
        """Accept one helper under the post lock, closing only at capacity."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.response_drafts.get(str(application_id), "").strip()
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.deciding_id = application_id
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            await asession.execute(
                text("""
                SELECT p.id FROM skillkind_help_post p
                WHERE p.id = (SELECT post_id FROM skillkind_job_application WHERE id = :aid)
                  AND p.author_id = :sid FOR UPDATE
            """),
                {"aid": application_id, "sid": int(sid)},
            )
            row = (
                await asession.execute(
                    text(
                        """
SELECT a.id, a.post_id, a.helper_id, p.title,
                               COALESCE(p.helpers_needed, 1), p.status,
                               (SELECT COUNT(*) FROM skillkind_job_application accepted
                                WHERE accepted.post_id = p.id AND accepted.status = 'accepted')
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        WHERE a.id = :aid AND p.author_id = :sid
                          AND a.status = 'pending'
                        """
                    ),
                    {"aid": application_id, "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.deciding_id = 0
                    self.error = (
                        "That request is no longer waiting for your answer."
                    )
                return
            post_id = int(row[1])
            helper_id = int(row[2])
            title = str(row[3] or "your help request")
            if str(row[5]) != "open" or int(row[6] or 0) >= max(
                1, int(row[4] or 1)
            ):
                await asession.rollback()
                async with self:
                    self.deciding_id = 0
                    self.error = "This request is closed or all helper places are filled."
                yield ProfileState.load_profile
                return
            if await are_members_blocked(asession, int(sid), helper_id):
                await asession.rollback()
                async with self:
                    self.deciding_id = 0
                    self.response_drafts.pop(str(application_id), None)
                    self.error = BLOCK_UNAVAILABLE_MESSAGE
                yield ProfileState.load_profile
                return
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_job_application
                    SET status = 'accepted', responded_at = now()
                    WHERE id = :aid AND status = 'pending'
                    """
                ),
                {"aid": application_id},
            )
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_job_application
                    SET status = 'declined', responded_at = now()
                    WHERE post_id = :pid AND id <> :aid
                      AND status = 'pending'
                      AND (SELECT COUNT(*) FROM skillkind_job_application a
                           WHERE a.post_id = :pid AND a.status = 'accepted') >=
                          (SELECT GREATEST(COALESCE(helpers_needed, 1), 1)
                           FROM skillkind_help_post WHERE id = :pid)
                    """
                ),
                {"pid": post_id, "aid": application_id},
            )
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_help_post
                    SET status = CASE WHEN
                        (SELECT COUNT(*) FROM skillkind_job_application a
                         WHERE a.post_id = :pid AND a.status = 'accepted') >=
                        GREATEST(COALESCE(helpers_needed, 1), 1)
                        THEN 'matched' ELSE 'open' END, updated_at = now()
                    WHERE id = :pid AND author_id = :sid
                    """
                ),
                {"pid": post_id, "sid": int(sid)},
            )
            # Tell the accepted helper, in this same transaction. The pending
            # status guard above means a retry can never duplicate this row.
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         help_post_id, target_route)
                    VALUES (:helper, 'help_confirmed', :title, :body,
                            :sid, :pid, '')
                    """
                ),
                {
                    "helper": helper_id,
                    "sid": int(sid),
                    "pid": post_id,
                    "title": f"You're confirmed to help: {title}"[:200],
                    "body": (
                        f"Your offer to help with “{title}” was accepted. "
                        "Open Help to see the day, place and hours."
                    )[:255],
                },
            )
            thread_id = await self._ensure_thread(
                asession, post_id, int(sid), helper_id, title
            )
            if note and thread_id:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_message (thread_id, sender_id, body)
                        VALUES (:tid, :sid, :body)
                        """
                    ),
                    {"tid": thread_id, "sid": int(sid), "body": note},
                )
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_message_thread
                        SET last_message_at = now(), is_archived = FALSE
                        WHERE id = :tid
                        """
                    ),
                    {"tid": thread_id},
                )
            await asession.commit()
        async with self:
            self.deciding_id = 0
            self.response_drafts.pop(str(application_id), None)
            self.success = f"Helper confirmed for “{title}”."
        yield rx.toast("Helper confirmed.", duration=4000)
        yield ProfileState.load_profile
        from app.states.help_hub_state import HelpHubState

        yield HelpHubState.load_help_hub
        from app.states.messaging_state import MessagingState

        yield MessagingState.load_threads

    @rx.event(background=True)
    async def deny_application(self, application_id: int):
        """Decline only this application, optionally sending the response note."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            note = self.response_drafts.get(str(application_id), "").strip()
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
            return
        async with self:
            self.deciding_id = application_id
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, a.post_id, a.helper_id, p.title
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        WHERE a.id = :aid AND p.author_id = :sid
                          AND a.status = 'pending'
                        """
                    ),
                    {"aid": application_id, "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.deciding_id = 0
                    self.error = (
                        "That request is no longer waiting for your answer."
                    )
                return
            post_id = int(row[1])
            helper_id = int(row[2])
            title = str(row[3] or "your help request")
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_job_application
                    SET status = 'declined', responded_at = now()
                    WHERE id = :aid
                    """
                ),
                {"aid": application_id},
            )
            # The decline itself stands; the kind note is a communication and
            # is only written when the pair is not blocked either way.
            note_allowed = note and not await are_members_blocked(
                asession, int(sid), helper_id
            )
            if note_allowed:
                thread_id = await self._ensure_thread(
                    asession, post_id, int(sid), helper_id, title
                )
                if thread_id:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO skillkind_message
                                (thread_id, sender_id, body)
                            VALUES (:tid, :sid, :body)
                            """
                        ),
                        {"tid": thread_id, "sid": int(sid), "body": note},
                    )
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_message_thread
                            SET last_message_at = now(), is_archived = FALSE
                            WHERE id = :tid
                            """
                        ),
                        {"tid": thread_id},
                    )
            await asession.commit()
        async with self:
            self.deciding_id = 0
            self.response_drafts.pop(str(application_id), None)
            self.success = "Request declined with a kind note."
        yield rx.toast("Participation request declined.", duration=3500)
        yield ProfileState.load_profile
        from app.states.help_hub_state import HelpHubState

        yield HelpHubState.load_help_hub
        from app.states.messaging_state import MessagingState

        yield MessagingState.load_threads

    async def _ensure_thread(
        self,
        asession,
        post_id: int,
        poster_id: int,
        helper_id: int,
        subject: str,
    ) -> int:
        """Return the job thread id, creating or reopening it as needed."""
        existing = (
            await asession.execute(
                text(
                    """
                    SELECT id FROM skillkind_message_thread
                    WHERE post_id = :pid AND helper_id = :hid
                    """
                ),
                {"pid": post_id, "hid": helper_id},
            )
        ).first()
        if existing is not None:
            thread_id = int(existing[0])
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_message_thread
                    SET is_archived = FALSE
                    WHERE id = :tid
                    """
                ),
                {"tid": thread_id},
            )
            return thread_id
        try:
            created = (
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_message_thread
                            (post_id, poster_id, helper_id, subject,
                             is_archived, last_message_at)
                        VALUES (:pid, :poster, :hid, :subject, FALSE, now())
                        RETURNING id
                        """
                    ),
                    {
                        "pid": post_id,
                        "poster": poster_id,
                        "hid": helper_id,
                        "subject": subject[:200],
                    },
                )
            ).first()
        except Exception as e:
            logging.exception(f"Error: {e}")
            return 0
        return int(created[0]) if created is not None else 0

    @rx.event(background=True)
    async def save_details(self, form_data: dict[str, Any]):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            home_country = str(
                form_data.get("home_country", self.home_country) or ""
            ).strip()[:100]
            # Never shareable: always persisted as FALSE.
            show_phone = False
        phone = str(form_data.get("phone", "") or "").strip()
        bio = str(form_data.get("bio", "") or "").strip()
        languages = str(form_data.get("languages", "") or "").strip()
        handle = str(form_data.get("username", "") or "").strip().lower()
        problem = ""
        if handle and not USERNAME_PATTERN.match(handle):
            problem = (
                "Handles are 3–30 characters, lowercase letters, numbers, "
                "dots or underscores."
            )
        if not problem:
            if not sid.isdigit():
                problem = "Your session expired — please sign in again."
            elif len(bio) > 2000:
                problem = (
                    "That biography is a little long — trim it under 2000 "
                    "characters."
                )
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_saving = True
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            if handle:
                taken = (
                    await asession.execute(
                        text(
                            """
                            SELECT subscriber_id FROM skillkind_profile
                            WHERE username = :handle AND subscriber_id <> :sid
                            """
                        ),
                        {"handle": handle, "sid": int(sid)},
                    )
                ).first()
                if taken is not None:
                    async with self:
                        self.is_saving = False
                        self.success = ""
                        self.error = (
                            f"@{handle} is already claimed by another "
                            "traveller — try a different handle."
                        )
                    return
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_subscriber
                    SET phone = :phone
                    WHERE id = :sid
                    """
                ),
                {"phone": phone, "sid": int(sid)},
            )
            try:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_profile
                        SET bio = :bio,
                            home_country = :home_country,
                            languages = :languages,
                            username = :handle,
                            show_phone_to_members = :show_phone,
                            updated_at = now()
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {
                        "bio": bio,
                        "home_country": home_country,
                        "languages": languages,
                        "handle": handle,
                        "show_phone": show_phone,
                        "sid": int(sid),
                    },
                )
                await asession.commit()
            except Exception as e:
                logging.exception(f"Error: {e}")
                await asession.rollback()
                async with self:
                    self.is_saving = False
                    self.success = ""
                    self.error = (
                        f"@{handle} is already claimed — pick another handle."
                        if handle
                        else "We couldn't save your profile. Please try again."
                    )
                return
        async with self:
            self.username = handle
            self.home_country = home_country
            self.bio = bio
            self.languages = languages
            self.is_saving = False
            self.show_phone_to_members = False
            self.success = "Profile details saved."
            auth = await self.get_state(AuthState)
            auth.phone = phone
        yield rx.toast("Profile details saved.", duration=3000)

    @rx.event(background=True)
    async def save_area(self, form_data: dict[str, Any]):
        """Persist the Profile location details form (address + exact point)."""
        from app.states.map_picker_state import MapPickerState

        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        home_country = str(form_data.get("home_country", "") or "").strip()
        current_city = str(form_data.get("current_city", "") or "").strip()
        road_and_number = str(
            form_data.get("road_and_number", "") or ""
        ).strip()
        town = str(form_data.get("town", "") or "").strip()
        postcode = str(form_data.get("postcode", "") or "").strip()
        coords_raw = str(form_data.get("coordinates", "") or "").strip()
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif not road_and_number:
            problem = "Road and Number are required. Please enter your street address."
        elif not current_city:
            problem = "City is required. Please enter your city."
        elif not town:
            problem = "Town is required. Please enter your town."
        elif not home_country:
            problem = "Country is required. Please enter your country."
        latitude, longitude, coord_problem = _parse_coordinate_pair(coords_raw)
        if not problem and coord_problem:
            problem = coord_problem
        # A pin dropped in the shared picker wins unless the member typed a
        # different coordinate pair by hand.
        async with self:
            current_mode = self.location_mode
            stored_lat = self.latitude.strip()
            stored_lon = self.longitude.strip()
            picker = await self.get_state(MapPickerState)
            picker_has_point = (
                picker.open_key == PROFILE_PICKER_KEY and picker.has_point
            )
            picker_lat = picker.latitude
            picker_lon = picker.longitude
        typed_is_unchanged = latitude is None or (
            f"{latitude:.6f}" == stored_lat and f"{longitude:.6f}" == stored_lon
        )
        if not problem and picker_has_point and typed_is_unchanged:
            latitude = picker_lat
            longitude = picker_lon
        if (
            not problem
            and current_mode in ("approximate", "live")
            and (latitude is None or longitude is None)
        ):
            problem = (
                "Approximate sharing needs an exact latitude and longitude to "
                "work from privately. Add both, or set My location to Off."
            )
        if problem:
            async with self:
                self.error = problem
                self.success = ""
            return
        async with self:
            self.is_saving = True
            self.error = ""
            self.success = ""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_profile
                    SET home_country = :home_country,
                        current_city = :current_city,
                        road_and_number = :road_and_number,
                        town = :town,
                        postcode = :postcode,
                        latitude = :latitude,
                        longitude = :longitude,
                        location_updated_at = CASE
                            WHEN :moved = TRUE THEN now()
                            ELSE location_updated_at
                        END,
                        updated_at = now()
                    WHERE subscriber_id = :sid
                    """
                ),
                {
                    "home_country": home_country,
                    "current_city": current_city,
                    "road_and_number": road_and_number,
                    "town": town,
                    "postcode": postcode,
                    "latitude": latitude,
                    "longitude": longitude,
                    "moved": latitude is not None and longitude is not None,
                    "sid": int(sid),
                },
            )
            await asession.commit()
        async with self:
            self.home_country = home_country
            self.current_city = current_city
            self.road_and_number = road_and_number
            self.town = town
            self.postcode = postcode
            self.latitude = "" if latitude is None else f"{latitude:.6f}"
            self.longitude = "" if longitude is None else f"{longitude:.6f}"
            self.is_saving = False
            if latitude is not None and longitude is not None:
                self.location_updated_label = "Updated just now"
                picker = await self.get_state(MapPickerState)
                picker._open_with_point(PROFILE_PICKER_KEY, latitude, longitude)
            self.success = "Location details saved."
