"""Community events: browsing, join requests and host decisions.

Everything is read from and written to the migrated
`skillkind_community_event` and `skillkind_event_join_request` tables. Every
authorization decision (who may create an event, who may confirm a join
request) is taken on the server against the database — never from client state.
"""

import datetime
import asyncio
import json
import re
from uuid import uuid4
import calendar
from zoneinfo import ZoneInfo, available_timezones
import logging
import math
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.location_privacy import approximate_point
from app.components.openfreemap import MapMarker

from app.models import (
    COMMUNITY_EVENT_DETAILS_MAX_WORDS,
    COMMUNITY_EVENT_TITLE_MAX_LENGTH,
    COMMUNITY_EVENT_TYPE_ICONS,
    COMMUNITY_EVENT_TYPE_LABELS,
    EVENT_REQUEST_CATEGORIES,
    EVENT_REQUEST_CATEGORY_LABELS,
    EVENT_REQUEST_CATEGORY_ICONS,
    EVENT_JOIN_CONFIRMED,
    EVENT_JOIN_PENDING,
    EVENT_TYPE_GATHERING,
    NOTIFICATION_KIND_HELP_CONFIRMED,
    NOTIFICATION_KIND_HELP_OFFER,
)
from app.states.auth_state import AuthState
from app.interface_i18n import translate
from app.interface_catalog_events import (
    EVENT_MONTH_KEYS,
    EVENT_WEEKDAY_KEYS,
    EVENT_WEEKDAY_SHORT_KEYS,
)
from app.states.map_picker_state import MapPickerState
from app.states.help_hub_state import (
    REWARD_CHOICES,
    REWARD_LABELS,
    HelpHubState,
)
from app.countries import CURRENCY_OPTIONS, STRIPE_CURRENCIES
from app.image_processing import read_image_upload, process_help_photo_bytes

EVENT_HELPERS_MAX = 100
EVENT_PHOTOS_MAX = 5


def _event_reward(
    choice: str, details: str, budget: str, currency: str, quote: bool
) -> str:
    details = details.strip()
    if choice not in REWARD_LABELS and choice != "":
        raise ValueError("Choose a reward from the list.")
    if not choice:
        return ""
    if choice == "other_reward" and not details:
        raise ValueError("Describe your Other reward.")
    summary = REWARD_LABELS[choice]
    if choice == "money":
        currency = currency.strip().upper()
        if currency not in STRIPE_CURRENCIES:
            raise ValueError("Choose a supported currency.")
        _, summary = HelpHubState._money_details(True, quote, budget, currency)
    result = f"{summary}: {details}" if details else summary
    if len(result) > 1000:
        raise ValueError("Reward and details must fit within 1,000 characters.")
    return result


def _helper_capacity(value: str) -> int:
    if (
        not value.isascii()
        or not value.isdigit()
        or not 1 <= int(value) <= EVENT_HELPERS_MAX
    ):
        raise ValueError(
            "Number of helpers must be a whole number between 1 and 100."
        )
    return int(value)


def _safe_event_photos(value: str) -> list[str]:
    try:
        paths = json.loads(value or "[]")
    except (ValueError, TypeError):
        return []
    if not isinstance(paths, list):
        return []
    return list(
        dict.fromkeys(
            path
            for path in paths
            if isinstance(path, str)
            and re.fullmatch(r"event_[0-9]+_[a-f0-9]{32}\.webp", path)
        )
    )[:EVENT_PHOTOS_MAX]


# Coarse public band for a community event point, in kilometres. The host's
# private exact coordinates never leave the server: only this deterministic,
# land-safe offset point is stored on the event row.
EVENT_POINT_BAND: tuple[float, float] = (4.0, 9.0)
EVENT_POINT_SALT = "community-event"

EVENT_DISTANCE_MIN = 1
EVENT_DISTANCE_MAX = 1000

EVENT_DISTANCE_HELP = "how far will you go to help"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two coarse points."""
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


class EventCard(TypedDict):
    id: int
    title: str
    details: str
    event_type: str
    type_label: str
    type_icon: str
    host_id: int
    host_name: str
    host_avatar_seed: str
    host_avatar: str
    host_verified: bool
    day: str
    month: str
    weekday: str
    time_label: str
    date_label: str
    place: str
    capacity: int
    confirmed_count: int
    capacity_label: str
    is_full: bool
    is_host: bool
    join_status: str
    status_label: str
    can_join: bool
    can_cancel: bool
    pending_count: int
    distance_label: str
    photo_paths: list[str]
    reward_details: str


class JoinRequestRow(TypedDict):
    id: int
    event_id: int
    event_title: str
    member_id: int
    member_name: str
    member_avatar_seed: str
    member_avatar: str
    member_verified: bool
    note: str
    created: str
    status: str


def _fmt_stamp(value) -> str:
    return value.strftime("%b %d, %Y · %H:%M") if value is not None else ""


def _words(value: str) -> int:
    return len([word for word in value.split() if word])


def _place(place_name: str, city: str, country: str) -> str:
    parts = [part for part in (place_name, city, country) if part]
    return " · ".join(parts) if parts else "Place shared by the host"


_CATEGORY_PREFIX = "[gah-event:v1:"


def _encode_details(category: str, details: str) -> str:
    if category not in EVENT_REQUEST_CATEGORIES:
        raise ValueError("Unknown event category")
    return f"{_CATEGORY_PREFIX}{category}]\n{details}"


def _decode_details(details: str, legacy_type: str) -> tuple[str, str]:
    category = legacy_type
    while details.startswith(_CATEGORY_PREFIX):
        header, separator, body = details.partition("\n")
        token = header[len(_CATEGORY_PREFIX) : -1]
        if token in EVENT_REQUEST_CATEGORIES and header.endswith("]"):
            category = token
        details = body if separator else ""
    return category, details


def _two_year_ceiling(now: datetime.datetime) -> datetime.datetime:
    try:
        return now.replace(year=now.year + 2)
    except ValueError:
        return now.replace(year=now.year + 2, day=28)


_RANGE_DATE_SENTINEL = "1970-01-01"


def _safe_range_dates(range_start: str, range_end: str) -> tuple[str, str]:
    """Return non-empty ISO dates for PostgreSQL's independently cast binds."""
    try:
        start = datetime.date.fromisoformat(
            (range_start or "").strip()
        ).isoformat()
    except ValueError:
        start = _RANGE_DATE_SENTINEL
    try:
        end = datetime.date.fromisoformat((range_end or "").strip()).isoformat()
    except ValueError:
        end = start
    return start, end


def _safe_timezone_name(value: str) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in available_timezones() else "UTC"


def _card(row, sid: int, distance_label: str = "") -> EventCard:
    starts = row[7]
    capacity = int(row[9] or 0)
    confirmed = int(row[10] or 0)
    host_id = int(row[11])
    event_type, details = _decode_details(
        row[3] or "", row[1] or EVENT_TYPE_GATHERING
    )
    join_status = str(row[16] or "")
    is_host = host_id == sid
    is_full = capacity > 0 and confirmed >= capacity
    return {
        "id": int(row[0]),
        "title": str(row[2] or "A Go and Help event"),
        "details": details,
        "event_type": event_type,
        "type_label": EVENT_REQUEST_CATEGORY_LABELS.get(
            event_type, COMMUNITY_EVENT_TYPE_LABELS.get(event_type, "Gathering")
        ),
        "type_icon": EVENT_REQUEST_CATEGORY_ICONS.get(
            event_type,
            COMMUNITY_EVENT_TYPE_ICONS.get(event_type, "party-popper"),
        ),
        "host_id": host_id,
        "host_name": str(row[12] or "A Go and Help neighbour"),
        "host_avatar_seed": str(row[13] or ""),
        "host_avatar": str(row[14] or ""),
        "host_verified": bool(row[15]),
        "day": starts.strftime("%d") if starts is not None else "--",
        "month": starts.strftime("%b").upper() if starts is not None else "TBA",
        "weekday": starts.strftime("%a") if starts is not None else "",
        "time_label": starts.strftime("%H:%M")
        if starts is not None
        else "Time to be announced",
        "date_label": _fmt_stamp(starts) or "Date to be announced",
        "place": _place(row[4] or "", row[5] or "", row[6] or ""),
        "capacity": capacity,
        "confirmed_count": confirmed,
        "capacity_label": (
            f"{confirmed} confirmed · no limit"
            if capacity == 0
            else f"{capacity} helpers needed · {confirmed}/{capacity} confirmed"
        ),
        "is_full": is_full,
        "is_host": is_host,
        "join_status": join_status,
        "status_label": {
            EVENT_JOIN_PENDING: "Request pending with the host",
            EVENT_JOIN_CONFIRMED: "You are confirmed",
            "declined": "The host declined this request",
            "cancelled": "You withdrew your request",
        }.get(join_status, ""),
        "can_join": (not is_host)
        and not is_full
        and join_status not in (EVENT_JOIN_PENDING, EVENT_JOIN_CONFIRMED),
        "can_cancel": (not is_host) and join_status == EVENT_JOIN_PENDING,
        "pending_count": int(row[17] or 0),
        "distance_label": distance_label,
        "photo_paths": _safe_event_photos(row[20]) if len(row) > 20 else [],
        "reward_details": str(row[21] or "") if len(row) > 21 else "",
    }


_CARD_SELECT = """
    SELECT e.id, e.event_type, e.title, e.details, e.place_name, e.city,
           e.country, e.starts_at, e.ends_at, e.capacity, e.confirmed_count,
           e.host_id, h.display_name, CONCAT('member-', h.id),
           COALESCE(pr.avatar_path, ''), COALESCE(h.is_verified, FALSE),
           COALESCE(jr.status, ''),
           (SELECT COUNT(*) FROM skillkind_event_join_request p
             WHERE p.event_id = e.id AND p.status = 'pending'),
           e.latitude, e.longitude, COALESCE(e.photo_paths, '[]'),
           COALESCE(e.reward_details, '')
    FROM skillkind_community_event e
    JOIN skillkind_subscriber h ON h.id = e.host_id
    LEFT JOIN skillkind_profile pr ON pr.subscriber_id = h.id
    LEFT JOIN skillkind_event_join_request jr
           ON jr.event_id = e.id AND jr.member_id = :sid
"""

_REQUEST_SELECT = """
    SELECT r.id, r.event_id, e.title, r.member_id, s.display_name, CONCAT('member-', s.id),
           COALESCE(pr.avatar_path, ''), COALESCE(s.is_verified, FALSE),
           COALESCE(r.note, ''), r.created_at, r.status
    FROM skillkind_event_join_request r
    JOIN skillkind_community_event e ON e.id = r.event_id
    JOIN skillkind_subscriber s ON s.id = r.member_id
    LEFT JOIN skillkind_profile pr ON pr.subscriber_id = s.id
"""


def _request_row(row) -> JoinRequestRow:
    return {
        "id": int(row[0]),
        "event_id": int(row[1]),
        "event_title": str(row[2] or ""),
        "member_id": int(row[3]),
        "member_name": str(row[4] or "A Go and Help neighbour"),
        "member_avatar_seed": str(row[5] or ""),
        "member_avatar": str(row[6] or ""),
        "member_verified": bool(row[7]),
        "note": str(row[8] or ""),
        "created": _fmt_stamp(row[9]),
        "status": str(row[10] or ""),
    }


def _localized_event_card(event: EventCard, language: str) -> EventCard:
    display = dict(event)
    month_number = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12,
    }.get(event["month"], 0)
    if month_number and event["day"].isdigit():
        year_part = event["date_label"].split(", ")[-1].split(" · ")[0]
        try:
            year = int(year_part)
            day = int(event["day"])
            date = datetime.date(year, month_number, day)
            month_name = translate(language, EVENT_MONTH_KEYS[month_number - 1])
            weekday = translate(language, EVENT_WEEKDAY_KEYS[date.weekday()])
            time_part = event["date_label"].partition(" · ")[2]
            display["month"] = month_name.upper()
            display["weekday"] = weekday
            display["date_label"] = f"{month_name} {day}, {year} · {time_part}"
        except (ValueError, IndexError):
            logging.exception("Unexpected error")
    display["type_label"] = translate(language, event["type_label"])
    display["status_label"] = translate(language, event["status_label"])
    for reward_label in REWARD_LABELS.values():
        source_prefix = f"{reward_label}:"
        if event["reward_details"].startswith(source_prefix):
            display["reward_details"] = (
                f"{translate(language, reward_label)}:"
                f"{event['reward_details'][len(source_prefix) :]}"
            )
            break
    if event["time_label"] == "Time to be announced":
        display["time_label"] = translate(language, event["time_label"])
    if event["date_label"] == "Date to be announced":
        display["date_label"] = translate(language, event["date_label"])
    if event["capacity"] == 0:
        display["capacity_label"] = translate(
            language, "{count} confirmed · no limit"
        ).format(count=event["confirmed_count"])
    else:
        display["capacity_label"] = translate(
            language,
            "{capacity} helpers needed · {confirmed}/{capacity} confirmed",
        ).format(capacity=event["capacity"], confirmed=event["confirmed_count"])
    if event["distance_label"] == "less than 1 km away":
        display["distance_label"] = translate(language, event["distance_label"])
    elif event["distance_label"].startswith("about "):
        distance = (
            event["distance_label"]
            .removeprefix("about ")
            .removesuffix(" km away")
        )
        display["distance_label"] = translate(
            language, "about {distance} km away"
        ).format(distance=distance)
    return display


def _localized_request_row(
    row: JoinRequestRow, language: str
) -> JoinRequestRow:
    display = dict(row)
    try:
        source_date, separator, source_time = row["created"].partition(" · ")
        date = datetime.datetime.strptime(source_date, "%b %d, %Y").date()
        display["created"] = (
            f"{translate(language, EVENT_MONTH_KEYS[date.month - 1])} "
            f"{date.day}, {date.year}{f' · {source_time}' if separator else ''}"
        )
    except ValueError:
        pass
    return display


def _localized_event_message(language: str, source: str) -> str:
    pin_accuracy = re.fullmatch(
        r"Pin set from your browser \(accuracy about (\d+) m\)\. Drag the pin or tap the map to fine-tune it\.",
        source,
    )
    if pin_accuracy:
        return translate(
            language,
            "Pin set from your browser (accuracy about {metres} m). Drag the pin or tap the map to fine-tune it.",
        ).format(metres=pin_accuracy.group(1))
    title_limit = re.fullmatch(
        r"Event titles can be at most (\d+) characters\.", source
    )
    if title_limit:
        return translate(
            language, "Titles can be at most {limit} characters."
        ).format(limit=title_limit.group(1))
    details_limit = re.fullmatch(
        r"The details are longer than (\d+) words\.", source
    )
    if details_limit:
        return translate(
            language,
            "That post is longer than {limit} words — please shorten it.",
        ).format(limit=details_limit.group(1))
    return translate(language, source)


class EventState(rx.State):
    """Browse events, ask to join, plan events and answer join requests."""

    events: list[EventCard] = []
    selected_event: list[EventCard] = []
    event_markers: list[MapMarker] = []

    @rx.var
    async def map_markers(self) -> list[MapMarker]:
        auth = await self.get_state(AuthState)
        selected_id = self.selected_event[0]["id"] if self.selected_event else 0
        events = {
            event["id"]: event
            for event in (
                *self.events,
                *self.hosted_events,
                *self.joined_events,
            )
        }
        markers: list[MapMarker] = []
        for marker in self.event_markers:
            event_id = int(str(marker["id"]).removeprefix("e") or 0)
            event = events.get(event_id)
            label = marker["label"]
            if event is not None:
                label = f"{translate(auth.preferred_language, event['type_label'])} · {event['title']}"
            markers.append(
                {
                    **marker,
                    "label": label,
                    "selected": marker["id"] == f"e{selected_id}",
                }
            )
        return markers

    @rx.event
    def select_event(self, event_id: int):
        event = next(
            (
                item
                for item in (
                    *self.events,
                    *self.hosted_events,
                    *self.joined_events,
                )
                if item["id"] == event_id
            ),
            None,
        )
        self.selected_event = [event] if event is not None else []
        self.error = ""
        self.success = ""

    @rx.event
    def clear_event_selection(self):
        self.selected_event = []

    hosted_events: list[EventCard] = []
    joined_events: list[EventCard] = []
    hosted_pending: list[JoinRequestRow] = []
    hosted_confirmed: list[JoinRequestRow] = []

    composer_open: bool = False
    event_type_draft: str = EVENT_REQUEST_CATEGORIES[0]
    reward_choice: str = ""
    reward_choices: list[dict[str, str]] = REWARD_CHOICES
    reward_currency: str = "USD"
    currency_options: list[dict[str, str]] = CURRENCY_OPTIONS
    budget_quote_allowed: bool = False

    @rx.event
    def set_reward_choice(self, value: str):
        if not self.is_saving:
            self.reward_choice = value if value in REWARD_LABELS else ""

    @rx.event
    def set_reward_currency(self, value: str):
        if not self.is_saving:
            self.reward_currency = value

    @rx.event
    def toggle_budget_quote(self):
        if not self.is_saving:
            self.budget_quote_allowed = not self.budget_quote_allowed

    helper_options: list[int] = list(range(1, EVENT_HELPERS_MAX + 1))
    pending_photo_paths: list[str] = []
    photo_busy: bool = False
    photo_error: str = ""
    _planner_revision: int = 0
    _photo_sources: list[tuple[str, str, str]] = []

    # How far outside the member's home country events may still appear.
    event_distance_km: float = 100.0
    distance_slider_reset: int = 0
    distance_location_prompt: bool = False
    events_location_enabled: bool = False
    events_location_disabled: bool = False
    events_location_source: str = "none"
    events_geo_token: int = 0
    events_geo_busy: bool = False
    events_location_error: str = ""
    events_location_revision: int = 0
    _events_point: tuple[float, float] = (0.0, 0.0)
    _events_has_point: bool = False
    _events_owner: str = ""

    @rx.var
    async def events_location_on(self) -> bool:
        from app.states.profile_state import ProfileState

        profile = await self.get_state(ProfileState)
        return not self.events_location_disabled and (
            (profile.location_mode == "approximate" and profile.show_location)
            or self.events_location_enabled
        )

    def _clear_events_fix(self) -> None:
        self._events_point = (0.0, 0.0)
        self._events_has_point = False
        self.events_location_enabled = False
        self.events_geo_busy = False
        self.events_geo_token = 0
        self.events_location_source = "none"
        self.events_location_error = ""
        self.events_location_revision += 1

    def _check_events_owner(self, sid: str) -> None:
        if self._events_owner != sid:
            self._clear_events_fix()
            self.events_location_disabled = False
            self._events_owner = sid
            self.composer_open = False
            self.pending_photo_paths = []
            self.photo_busy = False
            self.photo_error = ""
            self._planner_revision += 1

    @staticmethod
    def _valid_filter_point(
        latitude: object, longitude: object
    ) -> tuple[float, float] | None:
        try:
            lat, lon = float(latitude), float(longitude)
        except (TypeError, ValueError, OverflowError):
            logging.exception("Unexpected error")
            return None
        if not (math.isfinite(lat) and math.isfinite(lon)):
            return None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return lat, lon

    def _filter_point(
        self, map_visible: bool, latitude: object, longitude: object
    ) -> tuple[float, float] | None:
        self.events_location_source = "none"
        if self.events_location_disabled:
            return None
        point = (
            self._valid_filter_point(latitude, longitude)
            if map_visible
            else None
        )
        if point is not None:
            self.events_location_source = "profile"
            return point
        if self.events_location_enabled and self._events_has_point:
            self.events_location_source = "session"
            return self._events_point
        return None

    @rx.event
    async def sync_map_location(self):
        from app.states.profile_state import ProfileState

        profile = await self.get_state(ProfileState)
        self._clear_events_fix()
        self.events_location_disabled = False
        visible = (
            profile.location_mode == "approximate" and profile.show_location
        )
        self.events_location_source = "profile" if visible else "none"
        self.distance_location_prompt = not visible
        return EventState.load_events

    @rx.event
    async def toggle_events_location(self):
        from app.states.profile_state import ProfileState

        sid = (await self.get_state(AuthState)).subscriber_id
        self._check_events_owner(sid)
        if not sid.isdigit():
            self.events_location_error = (
                "Please sign in to enable your location."
            )
            return
        profile = await self.get_state(ProfileState)
        visible = (
            profile.location_mode == "approximate" and profile.show_location
        )
        enabled = not self.events_location_disabled and (
            visible or self.events_location_enabled
        )
        self._clear_events_fix()
        self.events_location_disabled = enabled
        self.distance_location_prompt = enabled
        if enabled:
            return EventState.load_events
        if visible:
            self.events_location_source = "profile"
            return EventState.load_events
        self.events_location_enabled = True
        self.events_geo_busy = True
        self.events_geo_token = self.events_location_revision
        self.distance_location_prompt = False

    @rx.event
    async def events_position_found(
        self, latitude: float, longitude: float, accuracy: float
    ):
        sid = (await self.get_state(AuthState)).subscriber_id
        if sid != self._events_owner:
            self._check_events_owner(sid)
            return
        if (
            not self.events_geo_busy
            or not self.events_location_enabled
            or self.events_location_disabled
        ):
            return
        point = self._valid_filter_point(latitude, longitude)
        self.events_geo_busy = False
        if point is None:
            self._clear_events_fix()
            self.events_location_error = "That location could not be read. Enable my location to try again."
            self.distance_location_prompt = True
            return EventState.load_events
        self._events_point = point
        self._events_has_point = True
        self.events_location_source = "session"
        self.events_location_error = ""
        self.events_location_revision += 1
        return EventState.load_events

    @rx.event
    def events_position_failed(self, message: str):
        if not self.events_geo_busy:
            return
        self._clear_events_fix()
        self.events_location_error = (
            message
            or "We could not read your location. Enable my location to try again."
        )
        self.distance_location_prompt = True
        return EventState.load_events

    selected_date: str = ""
    selected_dates: list[str] = []
    calendar_mode: str = "single"
    range_start: str = ""
    range_end: str = ""
    calendar_open: bool = False
    calendar_month: str = ""
    calendar_today: str = ""
    calendar_timezone: str = "UTC"

    def _local_today(self) -> datetime.date:
        return datetime.datetime.now(ZoneInfo(self.calendar_timezone)).date()

    def _calendar_limits(self) -> tuple[datetime.date, datetime.date]:
        today = (
            datetime.date.fromisoformat(self.calendar_today)
            if self.calendar_today
            else self._local_today()
        )
        ceiling = today.replace(
            year=today.year + 2,
            day=min(
                today.day, calendar.monthrange(today.year + 2, today.month)[1]
            ),
        )
        return today, ceiling

    @rx.event
    def initialize_calendar(self, timezone: str):
        self.calendar_timezone = _safe_timezone_name(timezone)
        self.calendar_today = self._local_today().isoformat()
        if not self.calendar_month:
            self.calendar_month = self._local_today().replace(day=1).isoformat()
        return EventState.load_events

    @rx.var
    def has_date_filter(self) -> bool:
        return bool(self.selected_dates or self.range_start or self.range_end)

    @rx.var
    def calendar_selection_label(self) -> str:
        if self.calendar_mode == "single":
            dates = sorted(set(self.selected_dates))
            if not dates:
                return "Select your dates"
            if len(dates) == 1:
                return datetime.date.fromisoformat(dates[0]).strftime(
                    "%b %-d, %Y"
                )
            return f"{len(dates)} single days selected"
        if not self.range_start:
            return "Select your dates"
        start = datetime.date.fromisoformat(self.range_start).strftime(
            "%b %-d, %Y"
        )
        if not self.range_end:
            return f"Start: {start}"
        end = datetime.date.fromisoformat(self.range_end).strftime("%b %-d, %Y")
        return f"{start} – {end}"

    @rx.var
    def calendar_month_label(self) -> str:
        month = (
            datetime.date.fromisoformat(self.calendar_month)
            if self.calendar_month
            else self._local_today()
        )
        return month.strftime("%B %Y")

    @rx.var
    def calendar_can_previous(self) -> bool:
        low, _ = self._calendar_limits()
        return (
            bool(self.calendar_month)
            and self.calendar_month[:7] > low.isoformat()[:7]
        )

    @rx.var
    def calendar_can_next(self) -> bool:
        _, high = self._calendar_limits()
        return (
            not self.calendar_month
            or self.calendar_month[:7] < high.isoformat()[:7]
        )

    @rx.var
    def calendar_cells(self) -> list[dict[str, str | bool]]:
        low, high = self._calendar_limits()
        month = (
            datetime.date.fromisoformat(self.calendar_month)
            if self.calendar_month
            else low
        )
        return [
            {
                "date": day.isoformat(),
                "label": str(day.day),
                "accessible_label": day.strftime("%A %d %B %Y"),
                "disabled": not low <= day <= high or day.month != month.month,
                "today": day == low,
                "selected": self._day_selected(day),
            }
            for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
                month.year, month.month
            )
            for day in week
        ]

    @rx.var
    async def calendar_display_month(self) -> str:
        auth = await self.get_state(AuthState)
        month = (
            datetime.date.fromisoformat(self.calendar_month)
            if self.calendar_month
            else self._local_today()
        )
        return f"{translate(auth.preferred_language, EVENT_MONTH_KEYS[month.month - 1])} {month.year}"

    @rx.var
    async def calendar_display_weekdays(self) -> list[str]:
        auth = await self.get_state(AuthState)
        return [
            translate(auth.preferred_language, day)
            for day in EVENT_WEEKDAY_SHORT_KEYS
        ]

    @rx.var
    async def calendar_display_cells(self) -> list[dict[str, str | bool]]:
        auth = await self.get_state(AuthState)
        language = auth.preferred_language
        localized: list[dict[str, str | bool]] = []
        for cell in self.calendar_cells:
            date = datetime.date.fromisoformat(cell["date"])
            localized.append(
                {
                    **cell,
                    "accessible_label": translate(
                        language, "{weekday} {day} {month} {year}"
                    ).format(
                        weekday=translate(
                            language, EVENT_WEEKDAY_KEYS[date.weekday()]
                        ),
                        day=date.day,
                        month=translate(
                            language, EVENT_MONTH_KEYS[date.month - 1]
                        ),
                        year=date.year,
                    ),
                }
            )
        return localized

    @rx.var
    async def calendar_display_selection(self) -> str:
        auth = await self.get_state(AuthState)
        language = auth.preferred_language

        def formatted(value: str) -> str:
            date = datetime.date.fromisoformat(value)
            return f"{translate(language, EVENT_MONTH_KEYS[date.month - 1])} {date.day}, {date.year}"

        if self.calendar_mode == "single":
            dates = sorted(set(self.selected_dates))
            if not dates:
                return translate(language, "Select your dates")
            if len(dates) == 1:
                return formatted(dates[0])
            return translate(language, "{count} single days selected").format(
                count=len(dates)
            )
        if not self.range_start:
            return translate(language, "Select your dates")
        start = formatted(self.range_start)
        if not self.range_end:
            return translate(language, "Start: {date}").format(date=start)
        return translate(language, "{start} – {end}").format(
            start=start, end=formatted(self.range_end)
        )

    @rx.event
    def toggle_calendar(self):
        self.calendar_today = self._local_today().isoformat()
        self.calendar_open = not self.calendar_open
        if self.calendar_open:
            self.calendar_month = (
                datetime.date.fromisoformat(
                    self.selected_date or self.calendar_today
                )
                .replace(day=1)
                .isoformat()
            )

    @rx.event
    def close_calendar(self):
        self.calendar_open = False

    @rx.event
    def change_calendar_month(self, step: int):
        low, high = self._calendar_limits()
        current = (
            datetime.date.fromisoformat(self.calendar_month)
            if self.calendar_month
            else low
        )
        index = current.year * 12 + current.month - 1 + max(-1, min(1, step))
        target = datetime.date(index // 12, index % 12 + 1, 1)
        if low.replace(day=1) <= target <= high.replace(day=1):
            self.calendar_month = target.isoformat()

    def _day_selected(self, day: datetime.date) -> bool:
        value = day.isoformat()
        if self.calendar_mode == "single":
            return value in self.selected_dates
        if not self.range_start:
            return False
        start = datetime.date.fromisoformat(self.range_start)
        end = (
            datetime.date.fromisoformat(self.range_end)
            if self.range_end
            else start
        )
        return start <= day <= end

    @rx.event
    def set_calendar_mode(self, mode: str):
        self.calendar_mode = "range" if mode == "range" else "single"
        self.selected_date = ""
        self.selected_dates = []
        self.range_start = ""
        self.range_end = ""
        return EventState.load_events

    @rx.event
    def select_calendar_day(self, value: str):
        try:
            day = datetime.date.fromisoformat(value)
        except ValueError:
            return
        low, high = self._calendar_limits()
        if not low <= day <= high:
            return
        if self.calendar_mode == "single":
            values = set(self.selected_dates)
            if value in values:
                values.remove(value)
            else:
                values.add(value)
            self.selected_dates = sorted(values)
            self.selected_date = (
                self.selected_dates[-1] if self.selected_dates else ""
            )
        elif not self.range_start or self.range_end:
            self.range_start = value
            self.range_end = ""
            self.selected_date = value
        elif day < datetime.date.fromisoformat(self.range_start):
            self.range_start = value
            self.range_end = ""
            self.selected_date = value
        else:
            self.range_end = value
            self.selected_date = value
        self.calendar_open = True
        return EventState.load_events

    @rx.event
    def clear_date_filter(self):
        self.selected_date = ""
        self.selected_dates = []
        self.range_start = ""
        self.range_end = ""
        self.calendar_open = False
        return EventState.load_events

    def _query_bounds(
        self, now: datetime.datetime
    ) -> tuple[datetime.datetime, datetime.datetime]:
        zone = ZoneInfo(self.calendar_timezone)
        chosen = (
            self.selected_dates
            if self.calendar_mode == "single"
            else [self.range_start, self.range_end]
        )
        chosen = [item for item in chosen if item]
        if chosen:
            first = datetime.date.fromisoformat(min(chosen))
            last = datetime.date.fromisoformat(max(chosen))
            start = datetime.datetime.combine(first, datetime.time.min, zone)
            end = datetime.datetime.combine(
                last + datetime.timedelta(days=1), datetime.time.min, zone
            )
            return start.astimezone(datetime.UTC), end.astimezone(datetime.UTC)
        local = now.astimezone(zone)
        index = local.year * 12 + local.month
        year, month = index // 12, index % 12 + 1
        end = local.replace(
            year=year,
            month=month,
            day=min(local.day, calendar.monthrange(year, month)[1]),
        )
        return now, end.astimezone(datetime.UTC)

    is_loading: bool = False
    has_loaded: bool = False
    is_loading_mine: bool = False
    has_loaded_mine: bool = False
    is_saving: bool = False
    busy_event_id: int = 0
    busy_request_id: int = 0

    error: str = ""
    success: str = ""

    @rx.var
    async def localized_feedback(self) -> dict[str, str]:
        auth = await self.get_state(AuthState)
        picker = await self.get_state(MapPickerState)
        language = auth.preferred_language
        return {
            "error": _localized_event_message(language, self.error),
            "success": _localized_event_message(language, self.success),
            "photo_error": _localized_event_message(language, self.photo_error),
            "location_error": _localized_event_message(
                language, self.events_location_error
            ),
            "map_status": _localized_event_message(language, picker.status),
            "map_error": _localized_event_message(language, picker.error),
        }

    type_options: list[dict[str, str]] = [
        {
            "value": kind,
            "label": EVENT_REQUEST_CATEGORY_LABELS[kind],
            "icon": EVENT_REQUEST_CATEGORY_ICONS[kind],
        }
        for kind in EVENT_REQUEST_CATEGORIES
    ]

    # ------------------------------------------------------------------
    # Derived labels
    # ------------------------------------------------------------------

    @rx.var
    def event_count_label(self) -> str:
        count = len(self.events)
        if count == 1:
            return "1 upcoming event"
        return f"{count} upcoming events"

    @rx.var
    def event_distance_label(self) -> str:
        if self.event_distance_km >= EVENT_DISTANCE_MAX:
            return "1000 km+"
        return f"{int(self.event_distance_km)} km"

    @rx.event
    async def select_max_event_distance(self):
        from app.states.profile_state import ProfileState

        profile = await self.get_state(ProfileState)
        self.distance_location_prompt = not (
            not self.events_location_disabled
            and (
                (
                    profile.location_mode == "approximate"
                    and profile.show_location
                )
                or (self.events_location_enabled and self._events_has_point)
            )
        )
        self.event_distance_km = EVENT_DISTANCE_MAX
        self.distance_slider_reset += 1
        return EventState.load_events

    @rx.event
    async def set_event_distance_km(self, value: float):
        from app.states.profile_state import ProfileState

        profile = await self.get_state(ProfileState)
        self.distance_location_prompt = profile.location_mode == "hidden"
        try:
            requested = int(value)
        except (TypeError, ValueError, OverflowError):
            logging.exception("Unexpected error")
            requested = 100
        self.event_distance_km = max(
            EVENT_DISTANCE_MIN, min(EVENT_DISTANCE_MAX, requested)
        )
        return EventState.load_events

    @rx.var
    def pending_count_label(self) -> str:
        count = len(self.hosted_pending)
        if count == 1:
            return "1 request to review"
        return f"{count} requests to review"

    @rx.var
    async def localized_events(self) -> list[EventCard]:
        auth = await self.get_state(AuthState)
        return [
            _localized_event_card(event, auth.preferred_language)
            for event in self.events
        ]

    @rx.var
    async def localized_selected_event(self) -> list[EventCard]:
        auth = await self.get_state(AuthState)
        return [
            _localized_event_card(event, auth.preferred_language)
            for event in self.selected_event
        ]

    @rx.var
    async def localized_hosted_events(self) -> list[EventCard]:
        auth = await self.get_state(AuthState)
        return [
            _localized_event_card(event, auth.preferred_language)
            for event in self.hosted_events
        ]

    @rx.var
    async def localized_joined_events(self) -> list[EventCard]:
        auth = await self.get_state(AuthState)
        return [
            _localized_event_card(event, auth.preferred_language)
            for event in self.joined_events
        ]

    @rx.var
    async def localized_hosted_pending(self) -> list[JoinRequestRow]:
        auth = await self.get_state(AuthState)
        return [
            _localized_request_row(row, auth.preferred_language)
            for row in self.hosted_pending
        ]

    @rx.var
    async def localized_hosted_confirmed(self) -> list[JoinRequestRow]:
        auth = await self.get_state(AuthState)
        return [
            _localized_request_row(row, auth.preferred_language)
            for row in self.hosted_confirmed
        ]

    @rx.var
    async def localized_pending_count_label(self) -> str:
        auth = await self.get_state(AuthState)
        count = len(self.hosted_pending)
        template = (
            "{count} request to review"
            if count == 1
            else "{count} requests to review"
        )
        return translate(auth.preferred_language, template).format(count=count)

    @rx.var
    async def localized_type_options(self) -> list[dict[str, str]]:
        auth = await self.get_state(AuthState)
        return [
            {
                **option,
                "label": translate(auth.preferred_language, option["label"]),
            }
            for option in self.type_options
        ]

    @rx.var
    async def localized_reward_choices(self) -> list[dict[str, str]]:
        auth = await self.get_state(AuthState)
        return [
            {
                **option,
                "label": translate(auth.preferred_language, option["label"]),
            }
            for option in self.reward_choices
        ]

    # ------------------------------------------------------------------
    # Composer controls
    # ------------------------------------------------------------------

    @rx.event
    def set_event_type_draft(self, value: str):
        self.event_type_draft = (
            value
            if value in EVENT_REQUEST_CATEGORIES
            else EVENT_REQUEST_CATEGORIES[0]
        )

    @rx.event
    async def toggle_composer(self):
        auth = await self.get_state(AuthState)
        if not auth.is_signed_in:
            self.error = "Please sign in to plan an event."
            return
        if self.is_saving or self.photo_busy:
            return
        self._check_events_owner(auth.subscriber_id)
        self.composer_open = not self.composer_open
        self.error = ""
        self.success = ""
        picker = await self.get_state(MapPickerState)
        if self.composer_open:
            self._planner_revision += 1
            self.event_type_draft = EVENT_REQUEST_CATEGORIES[0]
            self.reward_choice = ""
            self.reward_currency = "USD"
            self.budget_quote_allowed = False
            self.pending_photo_paths = []
            self.photo_error = ""
            picker._reset_point()
            picker.open_key = "event-planner"
        elif picker.open_key == "event-planner":
            picker._reset_point()
            picker._close_key("event-planner")

    @rx.event
    async def close_composer(self):
        if not self.is_saving and not self.photo_busy:
            self.composer_open = False
            picker = await self.get_state(MapPickerState)
            if picker.open_key == "event-planner":
                picker._reset_point()
                picker._close_key("event-planner")

    @rx.event
    def reject_photos(self):
        self.photo_error = "Choose up to five static JPEG, PNG or WebP photos, at most 3 MB each."

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        auth = await self.get_state(AuthState)
        if (
            not auth.is_signed_in
            or not self.composer_open
            or self.photo_busy
            or self.is_saving
        ):
            return
        self.photo_error = ""
        remaining = EVENT_PHOTOS_MAX - len(self.pending_photo_paths)
        if not remaining or len(files) > remaining:
            self.photo_error = "Attach no more than five photos. Remove one before adding more."
            return
        self.photo_busy = True
        sources: list[tuple[str, str, str]] = []
        try:
            directory = rx.get_upload_dir()
            await asyncio.to_thread(
                directory.mkdir, parents=True, exist_ok=True
            )
            for file in files:
                raw = await read_image_upload(file)
                name = f"event_source_{uuid4().hex}"
                await asyncio.to_thread((directory / name).write_bytes, raw)
                sources.append(
                    (
                        name,
                        str(file.name or ""),
                        str(getattr(file, "content_type", "") or ""),
                    )
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            for source, _, _ in sources:
                await asyncio.to_thread(
                    (rx.get_upload_dir() / source).unlink, missing_ok=True
                )
            self.photo_error = (
                "Photos must be static JPEG, PNG or WebP, at most 3 MB each."
            )
            self.photo_busy = False
            return
        self._photo_sources = sources
        yield EventState.process_photos(
            sources, auth.subscriber_id, self._planner_revision
        )

    @rx.event(background=True)
    async def process_photos(
        self, sources: list[tuple[str, str, str]], sid: str, revision: int
    ):
        async with self:
            auth = await self.get_state(AuthState)
            if not (
                auth.is_signed_in
                and auth.subscriber_id == sid
                and self.photo_busy
                and revision == self._planner_revision
                and sources == self._photo_sources
            ):
                return
            if any(
                not re.fullmatch(r"event_source_[a-f0-9]{32}", source)
                for source, _, _ in sources
            ):
                return
            self._photo_sources = []
        accepted: list[str] = []
        rejected = False
        directory = rx.get_upload_dir()
        for source, original, mime in sources:
            try:
                raw = await asyncio.to_thread((directory / source).read_bytes)
                payload = await asyncio.to_thread(
                    process_help_photo_bytes, raw, original, mime
                )
                if payload is None:
                    raise ValueError("Invalid photo")
                name = f"event_{sid}_{uuid4().hex}.webp"
                await asyncio.to_thread((directory / name).write_bytes, payload)
                accepted.append(name)
            except Exception as e:
                logging.exception(f"Error: {e}")
                rejected = True
            finally:
                try:
                    await asyncio.to_thread(
                        (directory / source).unlink, missing_ok=True
                    )
                except Exception as e:
                    logging.exception(f"Error: {e}")
                    rejected = True
        async with self:
            auth = await self.get_state(AuthState)
            valid = (
                auth.is_signed_in
                and auth.subscriber_id == sid
                and revision == self._planner_revision
            )
            if valid:
                self.pending_photo_paths.extend(accepted)
                self.photo_busy = False
                self.photo_error = (
                    "Some photos could not be accepted. Use static JPEG, PNG or WebP, at most 3 MB each."
                    if rejected
                    else ""
                )
        if not valid:
            for name in accepted:
                await asyncio.to_thread(
                    (directory / name).unlink, missing_ok=True
                )
        yield rx.clear_selected_files("event-photos")

    @rx.event(background=True)
    async def remove_photo(self, name: str):
        async with self:
            if (
                self.photo_busy
                or self.is_saving
                or name not in self.pending_photo_paths
            ):
                return
            self.pending_photo_paths.remove(name)
            self.photo_error = ""
        try:
            await asyncio.to_thread(
                (rx.get_upload_dir() / name).unlink, missing_ok=True
            )
        except Exception as e:
            logging.exception(f"Error: {e}")

    @rx.event
    async def show_event_toast(self, source: str):
        auth = await self.get_state(AuthState)
        yield rx.toast(
            _localized_event_message(auth.preferred_language, source),
            duration=3000,
        )

    @rx.event
    def clear_feedback(self):
        self.error = ""
        self.success = ""

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_events(self):
        from app.states.profile_state import ProfileState

        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self._check_events_owner(sid)
        if not sid.isdigit():
            async with self:
                self.events = []
                self.event_markers = []
                self.selected_event = []
                self.is_loading = False
                self.has_loaded = True
                self.error = "Please sign in to see community events."
            return
        async with self:
            self.is_loading = True
            self.error = ""
            distance_km = float(self.event_distance_km)
            profile = await self.get_state(ProfileState)
            map_visible = (
                profile.location_mode == "approximate" and profile.show_location
            )
            location_revision = self.events_location_revision
            calendar_timezone = self.calendar_timezone
            selected_date = self.selected_date
            selected_dates = list(self.selected_dates)
            calendar_mode = self.calendar_mode
            range_start = self.range_start
            range_end = self.range_end
            effective_range_start, effective_range_end = _safe_range_dates(
                range_start, range_end
            )
            lower, upper = self._query_bounds(
                datetime.datetime.now(datetime.UTC)
            )

        async with rx.asession() as asession:
            me = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(home_country, ''),
                               CASE WHEN location_mode = 'approximate' AND show_location = TRUE THEN latitude END,
                               CASE WHEN location_mode = 'approximate' AND show_location = TRUE THEN longitude END
                        FROM skillkind_profile
                        WHERE subscriber_id = :sid
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).first()
            rows = (
                await asession.execute(
                    text(
                        _CARD_SELECT
                        + """
                        WHERE e.status = 'active'
                          AND e.starts_at >= :window_start
                          AND e.starts_at < :window_end
                          AND (
                            NOT :has_date_filter
                            OR (
                              :calendar_mode = 'single'
                              AND (e.starts_at AT TIME ZONE :calendar_timezone)::date = ANY(CAST(:selected_dates AS date[]))
                            )
                            OR (
                              :calendar_mode = 'range'
                              AND (e.starts_at AT TIME ZONE :calendar_timezone)::date >= CAST(:range_start AS date)
                              AND (e.starts_at AT TIME ZONE :calendar_timezone)::date <= CAST(:range_end AS date)
                            )
                          )
                          AND (COALESCE(e.capacity, 0) = 0
                               OR COALESCE(e.confirmed_count, 0) < e.capacity)
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                               WHERE (mb.blocker_id = :sid
                                      AND mb.blocked_id = e.host_id)
                                  OR (mb.blocker_id = e.host_id
                                      AND mb.blocked_id = :sid))
                        ORDER BY e.starts_at ASC NULLS LAST,
                                 e.created_at DESC
                        LIMIT 60
                        """
                    ),
                    {
                        "sid": int(sid),
                        "window_start": lower,
                        "window_end": upper,
                        "has_date_filter": bool(
                            selected_dates or range_start or range_end
                        ),
                        "calendar_mode": calendar_mode,
                        "calendar_timezone": calendar_timezone,
                        "selected_dates": selected_dates,
                        "range_start": effective_range_start,
                        "range_end": effective_range_end,
                    },
                )
            ).all()

        home_country = str(me[0] or "").strip().lower() if me else ""
        async with self:
            if (
                location_revision != self.events_location_revision
                or sid != (await self.get_state(AuthState)).subscriber_id
            ):
                return
            point = self._filter_point(
                map_visible, me[1] if me else None, me[2] if me else None
            )
        my_lat, my_lon = point if point is not None else (None, None)

        loaded: list[EventCard] = []
        markers: list[MapMarker] = []
        for row in rows:
            country = str(row[6] or "").strip().lower()
            event_lat = row[18] if len(row) > 18 else None
            event_lon = row[19] if len(row) > 19 else None
            gap: float | None = None
            if (
                event_lat is not None
                and event_lon is not None
                and my_lat is not None
                and my_lon is not None
            ):
                gap = haversine_km(
                    my_lat, my_lon, float(event_lat), float(event_lon)
                )
            same_country = bool(home_country) and country == home_country
            if (
                not same_country
                and event_lat is not None
                and event_lon is not None
            ):
                if gap is None or gap > distance_km:
                    continue
            label = ""
            if gap is not None:
                label = (
                    f"about {gap:.0f} km away"
                    if gap >= 1
                    else "less than 1 km away"
                )
            card = _card(row, int(sid), label)
            loaded.append(card)
            # Only versioned events attest to the safe public-point write path.
            if (
                str(row[3] or "").startswith(_CATEGORY_PREFIX)
                and event_lat is not None
                and event_lon is not None
                and math.isfinite(float(event_lat))
                and math.isfinite(float(event_lon))
                and -90 <= float(event_lat) <= 90
                and -180 <= float(event_lon) <= 180
            ):
                markers.append(
                    {
                        "id": f"e{card['id']}",
                        "lat": float(event_lat),
                        "lng": float(event_lon),
                        "kind": "event",
                        "label": f"{card['type_label']} · {card['title']}",
                        "icon": "star",
                        "color": "#dca126",
                        "ink": "#ffffff",
                        "image_url": "",
                        "selected": False,
                    }
                )
        async with self:
            if (
                selected_date != self.selected_date
                or selected_dates != self.selected_dates
                or calendar_mode != self.calendar_mode
                or range_start != self.range_start
                or range_end != self.range_end
                or distance_km != self.event_distance_km
                or calendar_timezone != self.calendar_timezone
                or location_revision != self.events_location_revision
                or sid != (await self.get_state(AuthState)).subscriber_id
            ):
                return
            selected_id = (
                self.selected_event[0]["id"] if self.selected_event else 0
            )
            self.selected_event = [
                event for event in loaded if event["id"] == selected_id
            ]
            self.event_markers = markers
            self.events = loaded
            self.is_loading = False
            self.has_loaded = True

    @rx.event(background=True)
    async def load_my_events(self):
        """Hosted events with their queue, plus events I am confirmed for."""
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
        if not sid.isdigit():
            async with self:
                self.hosted_events = []
                self.joined_events = []
                self.hosted_pending = []
                self.hosted_confirmed = []
                self.is_loading_mine = False
                self.has_loaded_mine = True
            return
        async with self:
            self.is_loading_mine = True

        async with rx.asession() as asession:
            hosted_rows = (
                await asession.execute(
                    text(
                        _CARD_SELECT
                        + """
                        WHERE e.host_id = :sid AND e.status = 'active'
                        ORDER BY e.starts_at ASC NULLS LAST,
                                 e.created_at DESC
                        LIMIT 60
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            joined_rows = (
                await asession.execute(
                    text(
                        _CARD_SELECT
                        + """
                        WHERE e.status = 'active'
                          AND jr.status = 'confirmed'
                        ORDER BY e.starts_at ASC NULLS LAST,
                                 e.created_at DESC
                        LIMIT 60
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            pending_rows = (
                await asession.execute(
                    text(
                        _REQUEST_SELECT
                        + """
                        WHERE r.host_id = :sid AND r.status = 'pending'
                        ORDER BY r.created_at ASC
                        LIMIT 200
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            confirmed_rows = (
                await asession.execute(
                    text(
                        _REQUEST_SELECT
                        + """
                        WHERE r.host_id = :sid AND r.status = 'confirmed'
                        ORDER BY r.confirmed_at ASC NULLS LAST,
                                 r.created_at ASC
                        LIMIT 200
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()

        async with self:
            self.hosted_events = [_card(r, int(sid)) for r in hosted_rows]
            self.joined_events = [_card(r, int(sid)) for r in joined_rows]
            self.hosted_pending = [_request_row(r) for r in pending_rows]
            self.hosted_confirmed = [_request_row(r) for r in confirmed_rows]
            self.is_loading_mine = False
            self.has_loaded_mine = True

    # ------------------------------------------------------------------
    # Join requests
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def request_to_join(self, event_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.busy_event_id = int(event_id)
        if not sid.isdigit():
            async with self:
                self.busy_event_id = 0
                self.error = "Please sign in to ask to join an event."
            return

        async with rx.asession() as asession:
            event = (
                await asession.execute(
                    text(
                        """
                        SELECT id, host_id, status, title, capacity, confirmed_count
                        FROM skillkind_community_event
                        WHERE id = :eid AND starts_at > now()
                        FOR UPDATE
                        """
                    ),
                    {"eid": int(event_id)},
                )
            ).first()
            if event is None or str(event[2]) != "active":
                async with self:
                    self.busy_event_id = 0
                    self.error = "That event is no longer open."
                yield EventState.load_events
                return
            if int(event[4] or 0) > 0 and int(event[5] or 0) >= int(event[4]):
                await asession.rollback()
                async with self:
                    self.busy_event_id = 0
                    self.error = "This event is full. There is no waiting list."
                yield EventState.load_events
                return
            host_id = int(event[1])
            if host_id == int(sid):
                async with self:
                    self.busy_event_id = 0
                    self.error = "You are hosting this event already."
                return
            blocked = (
                await asession.execute(
                    text(
                        """
                        SELECT 1 FROM skillkind_member_block
                        WHERE (blocker_id = :sid AND blocked_id = :host)
                           OR (blocker_id = :host AND blocked_id = :sid)
                        LIMIT 1
                        """
                    ),
                    {"sid": int(sid), "host": host_id},
                )
            ).first()
            if blocked is not None:
                async with self:
                    self.busy_event_id = 0
                    self.error = "This event is not available to you."
                yield EventState.load_events
                return
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT id, status FROM skillkind_event_join_request
                        WHERE event_id = :eid AND member_id = :sid
                        """
                    ),
                    {"eid": int(event_id), "sid": int(sid)},
                )
            ).first()
            if existing is not None and str(existing[1]) in (
                EVENT_JOIN_PENDING,
                EVENT_JOIN_CONFIRMED,
            ):
                async with self:
                    self.busy_event_id = 0
                    self.error = "You already asked to join this event."
                yield EventState.load_events
                return
            if existing is None:
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_event_join_request
                            (event_id, member_id, host_id, status, note)
                        VALUES (:eid, :sid, :host, 'pending', '')
                        """
                    ),
                    {"eid": int(event_id), "sid": int(sid), "host": host_id},
                )
            else:
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_event_join_request
                        SET status = 'pending', responded_at = NULL,
                            confirmed_at = NULL, declined_at = NULL,
                            cancelled_at = NULL, updated_at = now()
                        WHERE id = :rid
                        """
                    ),
                    {"rid": int(existing[0])},
                )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         target_route)
                    VALUES (:host, :kind, :title, :body, :sid, 'community')
                    """
                ),
                {
                    "host": host_id,
                    "sid": int(sid),
                    "kind": NOTIFICATION_KIND_HELP_OFFER,
                    "title": "Someone asked to join your event",
                    "body": f"A member asked to join “{str(event[3])[:180]}”.",
                },
            )
            await asession.commit()

        async with self:
            self.busy_event_id = 0
            self.success = (
                "Your request is with the host — you will hear back soon."
            )
        yield EventState.show_event_toast("Request sent to the host.")
        yield EventState.load_events
        yield EventState.load_my_events

    @rx.event(background=True)
    async def cancel_join_request(self, event_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.busy_event_id = int(event_id)
        if not sid.isdigit():
            async with self:
                self.busy_event_id = 0
                self.error = "Please sign in first."
            return
        async with rx.asession() as asession:
            result = await asession.execute(
                text(
                    """
                    UPDATE skillkind_event_join_request
                    SET status = 'cancelled', cancelled_at = now(),
                        updated_at = now()
                    WHERE event_id = :eid AND member_id = :sid
                      AND status = 'pending'
                    """
                ),
                {"eid": int(event_id), "sid": int(sid)},
            )
            await asession.commit()
        async with self:
            self.busy_event_id = 0
            if result.rowcount:
                self.success = "Your request was withdrawn."
            else:
                self.error = "There is no pending request to withdraw."
        yield EventState.load_events
        yield EventState.load_my_events

    # ------------------------------------------------------------------
    # Host decisions
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def confirm_request(self, request_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.busy_request_id = int(request_id)
        if not sid.isdigit():
            async with self:
                self.busy_request_id = 0
                self.error = "Please sign in first."
            return

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT r.event_id, r.member_id, r.status
                        FROM skillkind_event_join_request r
                        WHERE r.id = :rid AND r.host_id = :sid
                        """
                    ),
                    {"rid": int(request_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                await asession.rollback()
                async with self:
                    self.busy_request_id = 0
                    self.error = "That request is not yours to answer."
                yield EventState.load_my_events
                return
            if str(row[2]) != EVENT_JOIN_PENDING:
                await asession.rollback()
                async with self:
                    self.busy_request_id = 0
                    self.error = "That request was already answered."
                yield EventState.load_my_events
                return
            event = (
                await asession.execute(
                    text(
                        """
                        SELECT capacity, confirmed_count, status, title
                        FROM skillkind_community_event
                        WHERE id = :eid AND host_id = :sid
                        FOR UPDATE
                        """
                    ),
                    {"eid": int(row[0]), "sid": int(sid)},
                )
            ).first()
            if event is None or str(event[2]) != "active":
                await asession.rollback()
                async with self:
                    self.busy_request_id = 0
                    self.error = "That event is no longer active."
                yield EventState.load_my_events
                return
            capacity = int(event[0] or 0)
            confirmed = int(event[1] or 0)
            if capacity > 0 and confirmed >= capacity:
                await asession.rollback()
                async with self:
                    self.busy_request_id = 0
                    self.error = "This event is full. No more attendees can be confirmed."
                yield EventState.load_my_events
                return
            updated = await asession.execute(
                text(
                    """
                    UPDATE skillkind_event_join_request
                    SET status = 'confirmed', confirmed_at = now(),
                        responded_at = now(), updated_at = now()
                    WHERE id = :rid AND status = 'pending'
                    """
                ),
                {"rid": int(request_id)},
            )
            if not updated.rowcount:
                await asession.rollback()
                async with self:
                    self.busy_request_id = 0
                    self.error = "That request was already answered."
                yield EventState.load_my_events
                return
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_community_event
                    SET confirmed_count = COALESCE(confirmed_count, 0) + 1,
                        updated_at = now()
                    WHERE id = :eid
                    """
                ),
                {"eid": int(row[0])},
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         target_route)
                    VALUES (:member, :kind, :title, :body, :sid, 'community')
                    """
                ),
                {
                    "member": int(row[1]),
                    "sid": int(sid),
                    "kind": NOTIFICATION_KIND_HELP_CONFIRMED,
                    "title": "You are confirmed for an event",
                    "body": f"The host confirmed you for “{str(event[3])[:180]}”.",
                },
            )
            await asession.commit()

        async with self:
            self.busy_request_id = 0
            self.success = "Attendee confirmed."
        yield EventState.show_event_toast("Attendee confirmed.")
        yield EventState.load_my_events
        yield EventState.load_events

    @rx.event(background=True)
    async def decline_request(self, request_id: int):
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            self.error = ""
            self.success = ""
            self.busy_request_id = int(request_id)
        if not sid.isdigit():
            async with self:
                self.busy_request_id = 0
                self.error = "Please sign in first."
            return

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT r.event_id, r.member_id, r.status, e.title,
                               e.confirmed_count
                        FROM skillkind_event_join_request r
                        JOIN skillkind_community_event e ON e.id = r.event_id
                        WHERE r.id = :rid AND r.host_id = :sid
                        """
                    ),
                    {"rid": int(request_id), "sid": int(sid)},
                )
            ).first()
            if row is None:
                async with self:
                    self.busy_request_id = 0
                    self.error = "That request is not yours to answer."
                yield EventState.load_my_events
                return
            was_confirmed = str(row[2]) == EVENT_JOIN_CONFIRMED
            if str(row[2]) not in (EVENT_JOIN_PENDING, EVENT_JOIN_CONFIRMED):
                async with self:
                    self.busy_request_id = 0
                    self.error = "That request was already answered."
                yield EventState.load_my_events
                return
            updated = await asession.execute(
                text(
                    """
                    UPDATE skillkind_event_join_request
                    SET status = 'declined', declined_at = now(),
                        responded_at = now(), confirmed_at = NULL,
                        updated_at = now()
                    WHERE id = :rid AND status IN ('pending', 'confirmed')
                    """
                ),
                {"rid": int(request_id)},
            )
            if not updated.rowcount:
                await asession.rollback()
                async with self:
                    self.busy_request_id = 0
                    self.error = "That request was already answered."
                yield EventState.load_my_events
                return
            if was_confirmed:
                # Keep the denormalised tally honest, never below zero.
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_community_event
                        SET confirmed_count = GREATEST(confirmed_count - 1, 0),
                            updated_at = now()
                        WHERE id = :eid
                        """
                    ),
                    {"eid": int(row[0])},
                )
            await asession.execute(
                text(
                    """
                    INSERT INTO skillkind_member_notification
                        (recipient_id, kind, title, body, actor_id,
                         target_route)
                    VALUES (:member, :kind, :title, :body, :sid, 'community')
                    """
                ),
                {
                    "member": int(row[1]),
                    "sid": int(sid),
                    "kind": NOTIFICATION_KIND_HELP_CONFIRMED,
                    "title": "An event host answered your request",
                    "body": (
                        "Your request to join "
                        f"“{str(row[3])[:180]}” was declined."
                    ),
                },
            )
            await asession.commit()

        async with self:
            self.busy_request_id = 0
            self.success = "Request declined."
        yield EventState.load_my_events
        yield EventState.load_events

    # ------------------------------------------------------------------
    # Planning an event for signed-in members
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def create_event(self, form_data: dict[str, Any]):
        async with self:
            auth = await self.get_state(AuthState)
            sid = auth.subscriber_id if auth.is_signed_in else ""
            if self.is_saving or self.photo_busy:
                return
            self.is_saving = True
            photos = list(self.pending_photo_paths)
            reward_choice = self.reward_choice
            reward_currency = self.reward_currency
            budget_quote_allowed = self.budget_quote_allowed
            picker = await self.get_state(MapPickerState)
            selected_point = (
                EventState._valid_filter_point(
                    picker.latitude, picker.longitude
                )
                if picker.open_key == "event-planner" and picker.has_point
                else None
            )
            event_type = str(
                form_data.get("event_type") or self.event_type_draft
            )
            self.error = ""
            self.success = ""
        if not sid.isdigit():
            async with self:
                self.error = "Your session expired — please sign in again."
                self.is_saving = False
            return

        if event_type not in EVENT_REQUEST_CATEGORIES:
            async with self:
                self.error = "Choose an event category."
                self.is_saving = False
            return
        title = str(form_data.get("title") or "").strip()
        details = str(form_data.get("details") or "").strip()
        place_name = str(form_data.get("place_name") or "").strip()[:200]
        city = str(form_data.get("city") or "").strip()[:120]
        country = str(form_data.get("country") or "").strip()[:120]
        raw_start = str(form_data.get("starts_at") or "").strip()
        raw_end = str(form_data.get("ends_at") or "").strip()
        raw_capacity = str(form_data.get("capacity", "1")).strip()
        reward_details = ""

        starts_at: datetime.datetime | None = None
        ends_at: datetime.datetime | None = None
        problem = ""
        if not title:
            problem = "Give your event a title."
        elif len(title) > COMMUNITY_EVENT_TITLE_MAX_LENGTH:
            problem = (
                "Event titles can be at most "
                f"{COMMUNITY_EVENT_TITLE_MAX_LENGTH} characters."
            )
        elif not details:
            problem = "Tell people what the event is about."
        elif _words(details) > COMMUNITY_EVENT_DETAILS_MAX_WORDS:
            problem = (
                "The details are longer than "
                f"{COMMUNITY_EVENT_DETAILS_MAX_WORDS} words."
            )
        elif not city:
            problem = "Add the city so people can find your event."
        elif not raw_start:
            problem = "Choose when your event starts."
        if not problem:
            try:
                starts_at = datetime.datetime.fromisoformat(raw_start)
            except ValueError as e:
                logging.exception(f"Error: {e}")
                problem = "That start date and time could not be read."
        if not problem and starts_at is not None:
            starts_at = (
                starts_at.replace(tzinfo=datetime.UTC)
                if starts_at.tzinfo is None
                else starts_at.astimezone(datetime.UTC)
            )
            now = datetime.datetime.now(datetime.UTC)
            if not now < starts_at <= _two_year_ceiling(now):
                problem = (
                    "Choose a future start within the next two calendar years."
                )
        if not problem and raw_end:
            try:
                ends_at = datetime.datetime.fromisoformat(raw_end)
                ends_at = (
                    ends_at.replace(tzinfo=datetime.UTC)
                    if ends_at.tzinfo is None
                    else ends_at.astimezone(datetime.UTC)
                )
            except ValueError as e:
                logging.exception(f"Error: {e}")
                problem = "That end date and time could not be read."
        if not problem and ends_at is not None and starts_at is not None:
            if ends_at < starts_at:
                problem = "The event cannot end before it starts."
        if not problem:
            try:
                reward_details = _event_reward(
                    reward_choice,
                    str(form_data.get("reward_details") or ""),
                    str(form_data.get("money_budget") or ""),
                    reward_currency,
                    budget_quote_allowed,
                )
            except ValueError as e:
                problem = str(e)
        capacity = 1
        if not problem:
            try:
                capacity = _helper_capacity(raw_capacity)
            except ValueError as e:
                problem = str(e)
        if (
            len(photos) > EVENT_PHOTOS_MAX
            or _safe_event_photos(json.dumps(photos)) != photos
        ):
            problem = "Attach no more than five valid event photos."
        if any(not path.startswith(f"event_{sid}_") for path in photos):
            problem = "Please upload your event photos again."
        if problem:
            async with self:
                self.is_saving = False
                self.error = problem
            yield rx.call_script(
                "document.querySelector('#event-planner-screen [role=alert]')?.scrollIntoView({block:'center'})"
            )
            return

        async with self:
            self.is_saving = True

        try:
            async with rx.asession() as asession:
                new_row = (
                    await asession.execute(
                        text("""
                    INSERT INTO skillkind_community_event
                        (host_id, event_type, title, details, place_name,
                         city, country, starts_at, ends_at, capacity,
                         confirmed_count, status, photo_paths, reward_details)
                    VALUES (:sid, 'teamwork', :title, :details, :place, :city,
                            :country, :starts, :ends, :capacity, 0, 'active', :photos, :reward)
                    RETURNING id
                """),
                        {
                            "sid": int(sid),
                            "title": title,
                            "details": _encode_details(event_type, details),
                            "place": place_name,
                            "city": city,
                            "country": country,
                            "starts": starts_at,
                            "ends": ends_at,
                            "capacity": capacity,
                            "photos": json.dumps(photos),
                            "reward": reward_details,
                        },
                    )
                ).first()
                if new_row is None:
                    raise ValueError("Event was not created")
                event_id = int(new_row[0])
                host_point = (
                    await asession.execute(
                        text("""
                    SELECT latitude, longitude FROM skillkind_profile
                    WHERE subscriber_id = :sid
                """),
                        {"sid": int(sid)},
                    )
                ).first()
                source_point = selected_point
                if source_point is None and host_point is not None:
                    source_point = EventState._valid_filter_point(
                        host_point[0], host_point[1]
                    )
                if source_point is not None:
                    coarse = await asyncio.to_thread(
                        approximate_point,
                        event_id,
                        EVENT_POINT_SALT,
                        source_point[0],
                        source_point[1],
                        EVENT_POINT_BAND,
                    )
                    if coarse is not None:
                        await asession.execute(
                            text("""
                            UPDATE skillkind_community_event
                            SET latitude = :lat, longitude = :lon, updated_at = now()
                            WHERE id = :eid AND host_id = :sid
                        """),
                            {
                                "lat": coarse[0],
                                "lon": coarse[1],
                                "eid": event_id,
                                "sid": int(sid),
                            },
                        )
                await asession.commit()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_saving = False
                self.error = "We couldn't publish your event. Your form and photos are still here — please try again."
            yield rx.call_script(
                "document.querySelector('#event-planner-screen [role=alert]')?.scrollIntoView({block:'center'})"
            )
            return

        async with self:
            self.is_saving = False
            self.composer_open = False
            self.success = "Your event is live on the community board."
            self.pending_photo_paths = []
            self.photo_error = ""
            self.reward_choice = ""
            self.reward_currency = "USD"
            self.budget_quote_allowed = False
            picker = await self.get_state(MapPickerState)
            if picker.open_key == "event-planner":
                picker._reset_point()
                picker._close_key("event-planner")
        yield EventState.show_event_toast("Event published.")
        yield EventState.load_events
        yield EventState.load_my_events
