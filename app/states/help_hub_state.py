"""Unified Help screen: post a request plus every help relationship."""

import datetime
import calendar
import math
import re
from decimal import Decimal
import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.countries import (
    WORLD_COUNTRY_NAMES,
    CURRENCY_OPTIONS,
    STRIPE_CURRENCIES,
    country_default_currency,
    supported_currency,
)
from app.help_languages import (
    LANGUAGE_CHOICES,
    LANGUAGE_CODES,
    encode_knowledge_with_period,
    decode_duration_period,
    decode_knowledge,
)
from app.directions import job_directions_url
from app.membership import (
    cap_message,
    check_post_allowance,
    post_interval_for_tier,
)
from app.models import (
    help_duration_label,
)
from app.skill_categories import (
    CATEGORY_UPGRADE_REASON,
    MAX_REQUEST_CATEGORIES,
    category_limit_message,
    join_categories,
    normalize_categories,
    primary_category,
    request_category_limit,
)
from app.states.auth_state import AuthState
from app.states.membership_state import MembershipState


REWARD_CHOICES: list[dict[str, str]] = [
    {
        "value": "money",
        "label": "Money",
        "blurb": "Set a budget or ask for a quote",
    },
    {
        "value": "refreshments",
        "label": "Refreshments",
        "blurb": "Drinks and snacks",
    },
    {
        "value": "meal",
        "label": "A meal",
        "blurb": "Lunch, Dinner, Cakes",
    },
    {
        "value": "accommodation",
        "label": "Accommodation",
        "blurb": "Work and stay",
    },
    {
        "value": "guided_tour",
        "label": "Guided tour",
        "blurb": "I will show you around",
    },
    {
        "value": "activity",
        "label": "Activity",
        "blurb": "Cook, Hike, Surf...",
    },
    {
        "value": "other_reward",
        "label": "Other reward",
        "blurb": "Anything else",
    },
]

REWARD_LABELS: dict[str, str] = {
    item["value"]: item["label"] for item in REWARD_CHOICES
}

# Map the new multi-select reward keys onto the legacy single reward_type
# column so old readers (map pins, discover, journal) keep working.
LEGACY_REWARD_TYPE: dict[str, str] = {
    "money": "money",
    "refreshments": "lunch",
    "meal": "dinner",
    "accommodation": "accommodation",
    "guided_tour": "guided_tours",
    "activity": "other",
    "other_reward": "other",
}

DETAIL_REWARDS: dict[str, str] = {
    "guided_tour": "guided_tour_details",
    "activity": "activity_details",
    "other_reward": "other_reward_details",
}


class HelperUpcoming(TypedDict):
    id: int
    post_id: int
    application_id: int
    proposal_id: int
    proposal_when: str
    proposal_mine: bool
    can_respond: bool
    title: str
    description: str
    location: str
    location_mode: str
    accepted_location: str
    dates: str
    start_time: str
    hours: str
    tools: str
    knowledge: str
    status: str
    other_id: int
    other_name: str
    other_avatar_seed: str
    other_avatar: str
    other_verified: bool
    # Finished, keyless navigation URL, or "" when no authorized point exists.
    directions_url: str


class ConfirmedHelper(TypedDict):
    id: int
    post_id: int
    application_id: int
    thread_id: int
    proposal_id: int
    proposal_when: str
    proposal_mine: bool
    can_respond: bool
    location_mode: str
    accepted_location: str
    needs_accepted: bool
    title: str
    description: str
    location: str
    dates: str
    start_time: str
    hours: str
    tools: str
    knowledge: str
    status: str
    helper_id: int
    helper_name: str
    helper_avatar_seed: str
    helper_handle: str
    helper_avatar: str
    helper_verified: bool
    helper_rating: float
    helper_rating_count: int
    schedule_time: str
    schedule_date: str
    directions_url: str


class HelpOffer(TypedDict):
    id: int
    post_id: int
    key: str
    title: str
    description: str
    location: str
    dates: str
    start_time: str
    hours: str
    tools: str
    knowledge: str
    pitch: str
    proposed: str
    applied: str
    helper_name: str
    helper_avatar_seed: str
    helper_handle: str
    helper_avatar: str
    helper_verified: bool


class CompletedJob(TypedDict):
    id: int
    post_id: int
    helper_id: int
    title: str
    location: str
    completed_date: str
    actual_duration: str
    reward_given: str
    story_note: str
    helper_name: str
    helper_handle: str
    helper_avatar: str
    helper_verified: bool
    helper_rating: float
    helper_rating_count: int
    thread_id: int


class PastHelper(TypedDict):
    helper_id: int
    helper_name: str
    helper_handle: str
    helper_avatar: str
    helper_verified: bool
    helper_rating: float
    helper_rating_count: int
    latest_title: str
    latest_completed_date: str
    completed_job_count: int
    thread_id: int


class DeclinedOffer(TypedDict):
    id: int
    title: str
    location: str
    dates: str
    responded: str
    helper_name: str
    helper_avatar_seed: str
    helper_avatar: str
    helper_verified: bool


def _location(place: str, city: str, country: str) -> str:
    parts = [p for p in (place, city, country) if p]
    return ", ".join(parts) or "Location to agree"


def _area_only(city: str, country: str) -> str:
    parts = [p for p in (city, country) if p]
    return ", ".join(parts) or "Approximate area"


def _helper_location(
    mode: str,
    accepted: str,
    place: str,
    city: str,
    country: str,
) -> str:
    """What an accepted helper may see for the job they were confirmed on.

    Public request coordinates and typed addresses are never revealed — not
    even for legacy `place` rows. The exact meeting address appears only once
    the helpee has shared it in the accepted-location card.
    """
    del mode, place
    if accepted.strip():
        return _location(accepted.strip(), city, country)
    return (
        f"{_area_only(city, country)} — exact meeting address still to be "
        "shared by the helpee"
    )


def _proposal_label(moment) -> str:
    """Readable label for a proposed or agreed date and time."""
    if moment is None:
        return ""
    return moment.strftime("%a, %b %d %Y · %H:%M")


def _hours_label(minutes: int, knowledge: str | None = None) -> str:
    """Keep legacy callers compatible; include the period for help rows."""
    if knowledge is None:
        return help_duration_label(minutes)
    safe = max(int(minutes or 0), 0)
    if not safe:
        return "Duration to be agreed / quoted"
    count, unit = decode_duration_period(knowledge)
    hours, remainder = divmod(safe, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")
    if remainder:
        parts.append(
            f"{remainder} minute" if remainder == 1 else f"{remainder} minutes"
        )
    period = unit if count == 1 else f"{unit}s"
    return f"{' '.join(parts)} for {count} {period}"


FLEXIBLE_CHOICES = ["Any Day", "Any weekday", "Any weekend", "Custom"]
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _date_ceiling(today: datetime.date) -> datetime.date:
    year = today.year + 2
    return today.replace(
        year=year, day=min(today.day, calendar.monthrange(year, today.month)[1])
    )


def _flexible_tokens(choices: list[str], weekdays: list[str]) -> list[str]:
    if "Any Day" in choices:
        return ["Any Day"]
    result = [choice for choice in FLEXIBLE_CHOICES[1:3] if choice in choices]
    if "Custom" in choices:
        result.extend(day for day in WEEKDAYS if day in weekdays)
    return result


def _time_label(value: str) -> str:
    if value.startswith(("flex:", "flexible:")):
        return (
            f"Any time between {value.split(':', 1)[1].replace('-', ' and ')}"
        )
    return value


def _dates_label(help_dates: str, scheduled, start_time: str) -> str:
    if help_dates.startswith("flexible:"):
        days = help_dates.removeprefix("flexible:").split(",")
        label = ", ".join(
            f"{day}s" if day in WEEKDAYS else day
            for day in days
            if day in FLEXIBLE_CHOICES or day in WEEKDAYS
        )
        clock = _time_label(start_time.strip())
        return (
            f"{label or 'Flexible days'} · {clock}"
            if clock
            else label or "Flexible days"
        )
    labels: list[str] = []
    for raw in [p.strip() for p in help_dates.split(",") if p.strip()]:
        try:
            labels.append(
                datetime.date.fromisoformat(raw).strftime("%a, %b %d %Y")
            )
        except ValueError:
            labels.append(raw)
    if not labels and scheduled is not None:
        labels.append(scheduled.strftime("%a, %b %d %Y"))
    if not labels:
        return "Dates to agree"
    time_part = _time_label(start_time.strip())
    if not time_part and scheduled is not None:
        time_part = scheduled.strftime("%H:%M")
    joined = " · ".join(labels)
    return f"{joined} at {time_part}" if time_part else joined


def _agreed_label(scheduled, help_dates: str, start_time: str) -> str:
    """The agreed date and time for a confirmed job.

    `HelpPost.scheduled_for` is authoritative once a job is confirmed, so a
    confirmed reschedule is never masked by the original multi-day text.
    """
    if help_dates or start_time.startswith(("flex:", "flexible:")):
        return _dates_label(help_dates, scheduled, start_time)
    if scheduled is not None:
        return scheduled.strftime("%a, %b %d %Y at %H:%M")
    return _dates_label(help_dates, scheduled, start_time)


def _schedule_parts(
    scheduled,
    days: str,
    clock: str,
    minutes: int,
    knowledge: str | None = None,
) -> tuple[str, str]:
    duration = _hours_label(minutes, knowledge)
    if (
        scheduled is not None
        and not days.startswith("flexible:")
        and not clock.startswith(("flex:", "flexible:"))
    ):
        month = scheduled.strftime("%b").replace("Sep", "Sept")
        return (
            f"{duration} at {clock or scheduled.strftime('%H:%M')}",
            f"{scheduled.strftime('%A')} {scheduled.day} {month} {scheduled.year}",
        )
    return duration, _agreed_label(scheduled, days, clock)


class HelpHubState(rx.State):
    """Everything the unified Help screen needs."""

    missing_fields: list[str] = []
    form_open: bool = False
    is_saving: bool = False
    is_loading: bool = False
    has_loaded: bool = False
    error: str = ""
    success: str = ""

    day_mode: str = "specific"
    flexible_days: list[str] = []
    custom_weekdays: list[str] = []
    flexible_days_open: bool = False
    time_mode: str = "specific"
    flexible_day_choices: list[str] = FLEXIBLE_CHOICES
    weekday_choices: list[str] = WEEKDAYS
    hour_choices: list[str] = [f"{hour:02d}" for hour in range(24)]
    minute_choices: list[str] = [f"{minute:02d}" for minute in range(0, 60, 5)]
    date_min: str = datetime.date.today().isoformat()
    date_max: str = _date_ceiling(datetime.date.today()).isoformat()
    date_input: str = ""
    calendar_open: bool = False
    calendar_month: str = datetime.date.today().replace(day=1).isoformat()

    @rx.var
    def calendar_month_label(self) -> str:
        return datetime.date.fromisoformat(self.calendar_month).strftime(
            "%B %Y"
        )

    @rx.var
    def date_trigger_label(self) -> str:
        try:
            return datetime.date.fromisoformat(self.date_input).strftime(
                "%d/%m/%Y"
            )
        except ValueError:
            return "dd/mm/yyyy"

    @rx.var
    def calendar_can_previous(self) -> bool:
        return self.calendar_month[:7] > self.date_min[:7]

    @rx.var
    def calendar_can_next(self) -> bool:
        return self.calendar_month[:7] < self.date_max[:7]

    @rx.var
    def calendar_cells(self) -> list[dict[str, str | bool]]:
        month = datetime.date.fromisoformat(self.calendar_month)
        return [
            {
                "date": day.isoformat(),
                "label": str(day.day),
                "accessible_label": day.strftime("%A %d %B %Y"),
                "disabled": day.month != month.month
                or not self.date_min <= day.isoformat() <= self.date_max,
                "selected": day.isoformat() == self.date_input,
                "today": day.isoformat() == self.date_min,
            }
            for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
                month.year, month.month
            )
            for day in week
        ]

    @rx.event
    def toggle_calendar(self):
        self.refresh_date_bounds()
        self.calendar_open = not self.calendar_open
        if self.calendar_open:
            chosen = (
                self.date_input
                if self.date_min <= self.date_input <= self.date_max
                else self.date_min
            )
            self.calendar_month = (
                datetime.date.fromisoformat(chosen).replace(day=1).isoformat()
            )

    @rx.event
    def close_calendar(self):
        self.calendar_open = False

    @rx.event
    def change_calendar_month(self, delta: int):
        self.refresh_date_bounds()
        if delta not in (-1, 1):
            return
        current = datetime.date.fromisoformat(self.calendar_month)
        year, month = divmod(current.year * 12 + current.month - 1 + delta, 12)
        target = datetime.date(year, month + 1, 1).isoformat()
        if self.date_min[:7] <= target[:7] <= self.date_max[:7]:
            self.calendar_month = target

    @rx.event
    def select_calendar_day(self, value: str):
        self.refresh_date_bounds()
        if not any(
            cell["date"] == value and not cell["disabled"]
            for cell in self.calendar_cells
        ):
            return
        self.date_input = value
        self.date_error = ""
        self.calendar_open = False

    @rx.var
    def flexible_days_summary(self) -> str:
        return (
            ", ".join(
                _flexible_tokens(self.flexible_days, self.custom_weekdays)
            )
            or "Choose flexible days"
        )

    @rx.event
    def set_day_mode(self, mode: str):
        if mode in ("specific", "flexible"):
            self.day_mode = mode
            self.calendar_open = False
            self.date_error = ""
            self.flexible_days_open = False

    @rx.event
    def set_time_mode(self, mode: str):
        if mode in ("specific", "flexible"):
            self.time_mode = mode
            self.error = ""

    @rx.event
    def toggle_flexible_days(self):
        self.flexible_days_open = not self.flexible_days_open

    @rx.event
    def toggle_flexible_day(self, value: str):
        if value not in FLEXIBLE_CHOICES:
            return
        if value in self.flexible_days:
            self.flexible_days.remove(value)
        elif value == "Any Day":
            self.flexible_days = [value]
            self.custom_weekdays = []
        else:
            self.flexible_days = [
                v for v in self.flexible_days if v != "Any Day"
            ]
            self.flexible_days.append(value)
        self.date_error = ""

    @rx.event
    def toggle_weekday(self, value: str):
        if value not in WEEKDAYS or "Custom" not in self.flexible_days:
            return
        if value in self.custom_weekdays:
            self.custom_weekdays.remove(value)
        else:
            self.custom_weekdays.append(value)
        self.date_error = ""

    @rx.event
    def refresh_date_bounds(self):
        today = datetime.date.today()
        self.date_min = today.isoformat()
        self.date_max = _date_ceiling(today).isoformat()
        if (
            not self.date_min[:7]
            <= self.calendar_month[:7]
            <= self.date_max[:7]
        ):
            self.calendar_month = today.replace(day=1).isoformat()

    help_dates: list[str] = []
    date_error: str = ""
    selected_rewards: list[str] = []
    rewards_open: bool = False

    @rx.var
    def rewards_summary(self) -> str:
        labels = [
            REWARD_LABELS[value]
            for value in self.selected_rewards
            if value in REWARD_LABELS
        ]
        if not labels:
            return "Choose rewards"
        if len(labels) <= 2:
            return ", ".join(labels)
        return f"{len(labels)} rewards selected"

    @rx.event
    def toggle_rewards(self):
        self.rewards_open = not self.rewards_open

    @rx.event
    def close_rewards(self):
        self.rewards_open = False

    posting_country: str = ""
    reward_currency: str = "USD"
    currency_options: list[dict[str, str]] = CURRENCY_OPTIONS

    @rx.event
    def set_posting_country(self, value: str):
        self.posting_country = value if value in WORLD_COUNTRY_NAMES else ""
        self.reward_currency = country_default_currency(self.posting_country)

    @rx.event
    def set_reward_currency(self, value: str):
        self.reward_currency = supported_currency(value)
        if value.strip().upper() not in STRIPE_CURRENCIES:
            self.error = "Choose a supported currency. USD has been selected."

    budget_quote_allowed: bool = False
    duration_quote_allowed: bool = False

    @rx.event
    def toggle_budget_quote(self):
        self.budget_quote_allowed = (
            not self.budget_quote_allowed
            if "money" in self.selected_rewards
            else False
        )

    @rx.event
    def toggle_duration_quote(self):
        self.duration_quote_allowed = not self.duration_quote_allowed

    @staticmethod
    def _money_details(
        selected: bool, quote: bool, raw: str, currency: str = "USD"
    ) -> tuple[Decimal, str]:
        currency = supported_currency(currency)
        if not selected:
            return Decimal("0"), ""
        if quote:
            return Decimal("0"), f"Money ({currency} — Helper quote requested)"
        raw = raw.strip()
        if not re.fullmatch(r"[0-9]{1,8}(?:\.[0-9]{1,2})?", raw):
            raise ValueError(
                f"Enter your budget in {currency} with at most two decimal places, or allow a Helper quote."
            )
        amount = Decimal(raw)
        if not amount.is_finite() or not Decimal("0.01") <= amount <= Decimal(
            "99999999.99"
        ):
            raise ValueError(
                f"Enter a positive {currency} budget from 0.01 to 99999999.99, or allow a Helper quote."
            )
        return amount, f"Money ({currency} {amount:.2f} budget)"

    required_languages: list[str] = []
    languages_open: bool = False
    language_choices: list[dict[str, str]] = LANGUAGE_CHOICES

    @rx.var
    def required_languages_label(self) -> str:
        return (
            ", ".join(
                item["name"]
                for item in LANGUAGE_CHOICES
                if item["code"] in self.required_languages
            )
            or "Any language"
        )

    @rx.event
    def toggle_languages(self):
        self.languages_open = not self.languages_open

    @rx.event
    def toggle_required_language(self, code: str):
        if code == "":
            self.required_languages = []
        elif code in LANGUAGE_CODES:
            if code in self.required_languages:
                self.required_languages.remove(code)
            else:
                self.required_languages.append(code)

    # Ask for Help location privacy: `approximate` or `place`.
    job_location_mode: str = "approximate"

    # Accepted-job exact meeting location (helpee only).
    accepted_form_id: int = 0
    accepted_busy: bool = False
    accepted_error: str = ""
    accepted_notice: str = ""

    # Two-party rescheduling of a confirmed job.
    schedule_form_id: int = 0
    schedule_busy_id: int = 0
    schedule_error: str = ""
    schedule_notice: str = ""

    upcoming_help: list[HelperUpcoming] = []
    confirmed_helpers: list[ConfirmedHelper] = []
    help_offers: list[HelpOffer] = []
    declined_offers: list[DeclinedOffer] = []
    completed_jobs: list[CompletedJob] = []
    past_helpers: list[PastHelper] = []

    @staticmethod
    def _completed_job(r) -> CompletedJob:
        return {
            "id": int(r[0]),
            "post_id": int(r[1]),
            "helper_id": int(r[2]),
            "title": str(r[3] or "Help request"),
            "location": _area_only(str(r[4] or ""), str(r[5] or "")),
            "completed_date": r[6].strftime("%b %d, %Y")
            if r[6]
            else "Date not recorded",
            "actual_duration": _hours_label(int(r[7]))
            if r[7] and int(r[7]) > 0
            else "",
            "reward_given": str(r[8] or ""),
            "story_note": str(r[9] or ""),
            "helper_name": str(r[10] or "A Go and Help neighbour"),
            "helper_handle": f"@{str(r[11]).lstrip('@')}" if r[11] else "",
            "helper_avatar": str(r[12] or ""),
            "helper_verified": bool(r[13]),
            "helper_rating": float(r[14] or 0),
            "helper_rating_count": int(r[15] or 0),
            "thread_id": int(r[16] or 0),
        }

    @staticmethod
    def _past_helper(r) -> PastHelper:
        job = HelpHubState._completed_job(r)
        return {
            "helper_id": job["helper_id"],
            "helper_name": job["helper_name"],
            "helper_handle": job["helper_handle"],
            "helper_avatar": job["helper_avatar"],
            "helper_verified": job["helper_verified"],
            "helper_rating": job["helper_rating"],
            "helper_rating_count": job["helper_rating_count"],
            "latest_title": job["title"],
            "latest_completed_date": job["completed_date"],
            "completed_job_count": int(r[17] or 0),
            "thread_id": job["thread_id"],
        }

    async def _load_completed_history(
        self, asession, sid: str
    ) -> tuple[list[CompletedJob], list[PastHelper]]:
        # Profile helper aggregates are maintained by the reciprocal-review flow.
        fields = """
            ct.id, ct.post_id, ct.helper_id, p.title, p.city, p.country,
            ct.completed_at, COALESCE(ct.actual_duration_minutes, 0),
            ct.reward_given, ct.story_note, h.display_name, hp.username,
            hp.avatar_path, COALESCE(h.is_verified, FALSE),
            COALESCE(hp.helper_rating_avg, 0), COALESCE(hp.helper_rating_count, 0),
            COALESCE(mt.id, 0), COUNT(*) OVER (PARTITION BY ct.helper_id) AS completed_job_count
        """
        relationship = """
            FROM skillkind_completed_task ct
            JOIN skillkind_help_post p ON p.id = ct.post_id
            JOIN skillkind_subscriber h ON h.id = ct.helper_id
            LEFT JOIN skillkind_profile hp ON hp.subscriber_id = h.id
            LEFT JOIN skillkind_message_thread mt
              ON mt.post_id = ct.post_id AND mt.helper_id = ct.helper_id
             AND mt.poster_id = ct.poster_id
            WHERE ct.poster_id = :sid
              AND NOT EXISTS (
                  SELECT 1 FROM skillkind_member_block mb
                  WHERE (mb.blocker_id = :sid AND mb.blocked_id = ct.helper_id)
                     OR (mb.blocker_id = ct.helper_id AND mb.blocked_id = :sid)
              )
        """
        completed = (
            await asession.execute(
                text(f"""
            SELECT {fields} {relationship}
            ORDER BY ct.completed_at DESC NULLS LAST, ct.id DESC
            LIMIT 60
        """),
                {"sid": int(sid)},
            )
        ).all()
        helpers = (
            await asession.execute(
                text(f"""
            SELECT latest.* FROM (
                SELECT DISTINCT ON (ct.helper_id) {fields} {relationship}
                ORDER BY ct.helper_id, ct.completed_at DESC NULLS LAST, ct.id DESC
            ) latest
ORDER BY latest.completed_at DESC NULLS LAST, latest.id DESC
        """),
                {"sid": int(sid)},
            )
        ).all()
        return (
            [self._completed_job(r) for r in completed],
            [self._past_helper(r) for r in helpers],
        )

    reward_choices: list[dict[str, str]] = REWARD_CHOICES
    duration_hour_choices: list[str] = [str(value) for value in range(11)]
    duration_minute_choices: list[str] = [
        str(value) for value in range(0, 60, 5)
    ]
    duration_count_choices: list[str] = [str(value) for value in range(1, 8)]
    duration_period_count: int = 1
    duration_period_unit: str = "day"

    @staticmethod
    def _ascii_integer(value: str, minimum: int, maximum: int) -> int:
        if not value.isascii() or not value.isdecimal() or len(value) > 2:
            raise ValueError("Choose a valid whole number.")
        number = int(value)
        if not minimum <= number <= maximum:
            raise ValueError("Choose a number within the allowed range.")
        return number

    @staticmethod
    def _period_options(count: int) -> list[dict[str, str]]:
        return [
            {
                "value": unit,
                "label": unit.title() if count == 1 else f"{unit.title()}s",
            }
            for unit in ("day", "week", "month")
        ]

    @rx.var
    def duration_period_options(self) -> list[dict[str, str]]:
        return self._period_options(self.duration_period_count)

    @rx.event
    def set_duration_period_count(self, value: str):
        try:
            self.duration_period_count = self._ascii_integer(value, 1, 7)
        except ValueError:
            self.error = "Choose a duration period from 1 to 7."

    @rx.event
    def set_duration_period_unit(self, value: str):
        if value in ("day", "week", "month"):
            self.duration_period_unit = value
        else:
            self.error = "Choose Day, Week or Month."

    @staticmethod
    def _parse_duration(
        hours: str, minutes: str, count: str, unit: str
    ) -> tuple[int, int, str]:
        h = HelpHubState._ascii_integer(hours, 0, 10)
        m = HelpHubState._ascii_integer(minutes, 0, 55)
        periods = HelpHubState._ascii_integer(count, 1, 7)
        if m % 5 | (unit not in ("day", "week", "month")):
            raise ValueError(
                "Choose five-minute increments and a valid duration period."
            )
        return h * 60 + m, periods, unit

    @staticmethod
    def _parse_start_time(
        mode: str,
        hour: str,
        minute: str,
        end_hour: str = "",
        end_minute: str = "",
    ) -> tuple[datetime.time, str]:
        h = HelpHubState._ascii_integer(hour, 0, 23)
        m = HelpHubState._ascii_integer(minute, 0, 55)
        if m % 5:
            raise ValueError("Choose five-minute increments.")
        clock = datetime.time(h, m)
        if mode == "specific":
            return clock, clock.strftime("%H:%M")
        if mode != "flexible":
            raise ValueError("Choose a valid time mode.")
        eh = HelpHubState._ascii_integer(end_hour, 0, 23)
        em = HelpHubState._ascii_integer(end_minute, 0, 55)
        if em % 5 | (eh * 60 + em <= h * 60 + m):
            raise ValueError(
                "Range end must be later than its start, in five-minute increments."
            )
        return clock, f"flex:{h:02d}:{m:02d}-{eh:02d}:{em:02d}"

    # Remove Help Request flow (per-card select -> confirm -> server cancel).
    removal_selected_id: int = 0
    removal_selected_title: str = ""
    removal_busy: bool = False
    removal_error: str = ""
    removal_notice: str = ""

    @rx.var
    def removal_confirming(self) -> bool:
        return self.removal_selected_id > 0

    @rx.event
    def select_removal(self, post_id: int, title: str):
        self.removal_selected_id = int(post_id)
        self.removal_selected_title = title
        self.removal_error = ""
        self.removal_notice = ""

    @rx.event
    def cancel_removal(self):
        self.removal_selected_id = 0
        self.removal_selected_title = ""
        self.removal_error = ""

    @rx.event(background=True)
    async def confirm_removal(self):
        """Server-authoritative cancel of one own, still-removable request."""
        from app.states.discovery_state import DiscoveryState
        from app.states.help_post_state import HelpPostState

        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            post_id = int(self.removal_selected_id)
            title = self.removal_selected_title
            self.removal_error = ""
            self.removal_notice = ""
            if not sid.isdigit() or post_id <= 0:
                self.removal_error = (
                    "Choose one of your own help requests to remove."
                )
                return
            self.removal_busy = True
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_help_post AS p
                        SET status = 'cancelled'
                        WHERE p.id = :pid
                          AND p.author_id = :sid
                          AND p.status = 'open'
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_job_application a
                              WHERE a.post_id = p.id
                                AND a.status = 'accepted'
                          )
                        RETURNING p.id
                        """
                    ),
                    {"pid": post_id, "sid": int(sid)},
                )
            ).first()
            if row is None:
                await asession.rollback()
            else:
                await asession.commit()
        if row is None:
            async with self:
                self.removal_busy = False
                self.removal_error = (
                    "That request can no longer be removed — it is already "
                    "matched, completed or does not belong to you."
                )
            return
        async with self:
            self.removal_busy = False
            self.removal_selected_id = 0
            self.removal_selected_title = ""
            self.removal_notice = f'"{title}" was removed from the board.'
            # Optimistically drop the card so no stale request remains visible.
            help_state = await self.get_state(HelpPostState)
            help_state.recent_posts = [
                post
                for post in help_state.recent_posts
                if int(post["id"]) != post_id
            ]
            counts = dict(help_state.counts)
            help_state.counts = {
                "total": max(int(counts.get("total", 0)) - 1, 0),
                "open": max(int(counts.get("open", 0)) - 1, 0),
                "upcoming": max(int(counts.get("upcoming", 0)) - 1, 0),
            }
        yield rx.toast("Help request removed.", duration=4000)
        yield HelpHubState.load_help_hub
        yield HelpPostState.load_recent
        yield DiscoveryState.refresh_board
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile

    @rx.var
    def date_count_label(self) -> str:
        count = len(self.help_dates)
        if count == 0:
            return "No days chosen yet"
        return f"{count} day chosen" if count == 1 else f"{count} days chosen"

    @rx.var
    def job_location_description(self) -> str:
        """Privacy line shown with the request location fields."""
        return "For your privacy, users can only see your location as 0.5–1 km away from your real location. Your accurate location is only shown after you both agree on the help"

    @rx.event
    def set_job_location_mode(self, mode: str):
        """Kept for compatibility: a request is always approximate publicly."""
        del mode
        self.job_location_mode = "approximate"
        self.error = ""

    @rx.event
    def open_accepted_form(self, post_id: int):
        from app.states.map_picker_state import MapPickerState

        self.accepted_form_id = int(post_id)
        self.accepted_error = ""
        self.accepted_notice = ""
        return MapPickerState.open_picker(f"accepted-{int(post_id)}")

    @rx.event
    def close_accepted_form(self):
        from app.states.map_picker_state import MapPickerState

        self.accepted_form_id = 0
        self.accepted_error = ""
        return MapPickerState.close_picker

    @rx.event(background=True)
    async def save_accepted_location(self, form_data: dict[str, Any]):
        """Store the exact meeting place for one of my approximate requests.

        The UPDATE itself re-checks ownership and that an accepted application
        exists, so no client-supplied post id can ever reach another member's
        request.
        """
        from app.states.map_picker_state import MapPickerState

        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            post_id = int(self.accepted_form_id)
            picker = await self.get_state(MapPickerState)
            has_point = bool(picker.has_point)
            latitude = float(picker.latitude)
            longitude = float(picker.longitude)
            self.accepted_error = ""
            self.accepted_notice = ""
        address = str(form_data.get("accepted_address", "") or "").strip()
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif post_id <= 0:
            problem = "Choose the confirmed job you want to add a place to."
        elif len(address) < 4:
            problem = "Add the exact meeting address for your helper."
        elif not has_point:
            problem = (
                "Add the exact point too: use your current location or tap "
                "the map to drop a pin."
            )
        if problem:
            async with self:
                self.accepted_error = problem
            return
        async with self:
            self.accepted_busy = True
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_help_post AS p
                        SET accepted_location_name = :address,
                            accepted_latitude = :lat,
                            accepted_longitude = :lon,
                            updated_at = now()
                        WHERE p.id = :pid
                          AND p.author_id = :sid
                          AND EXISTS (
                              SELECT 1 FROM skillkind_job_application a
                              WHERE a.post_id = p.id
                                AND a.status = 'accepted'
                          )
                        RETURNING p.id
                        """
                    ),
                    {
                        "address": address[:200],
                        "lat": max(-90.0, min(90.0, latitude)),
                        "lon": max(-180.0, min(180.0, longitude)),
                        "pid": post_id,
                        "sid": int(sid),
                    },
                )
            ).first()
            if row is None:
                await asession.rollback()
            else:
                await asession.commit()
        if row is None:
            async with self:
                self.accepted_busy = False
                self.accepted_error = (
                    "We could not save that meeting place — the request must "
                    "be yours, use Approximate sharing and already have a "
                    "confirmed helper."
                )
            return
        async with self:
            self.accepted_busy = False
            self.accepted_form_id = 0
            self.accepted_notice = (
                "Exact meeting place saved. Only you and your confirmed "
                "helper can see it."
            )
            picker = await self.get_state(MapPickerState)
            picker.open_key = ""
            picker.has_point = False
            picker.latitude = 0.0
            picker.longitude = 0.0
            picker.status = ""
        yield rx.toast("Meeting place shared with your helper.", duration=4000)
        yield HelpHubState.load_help_hub

    @rx.event
    def open_schedule_form(self, application_id: int):
        return
        self.schedule_form_id = int(application_id)
        self.schedule_error = ""
        self.schedule_notice = ""

    @rx.event
    def close_schedule_form(self):
        self.schedule_form_id = 0
        self.schedule_error = ""

    @rx.event(background=True)
    async def propose_schedule(
        self, application_id: int, form_data: dict[str, Any]
    ):
        """Propose a new date and time for one confirmed job.

        The whole check-and-write runs in a single transaction, and the SQL
        itself proves the caller is exactly the poster or the helper on an
        accepted application, so no client id can reach another job.
        """
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            app_id = int(application_id)
            self.schedule_error = ""
            self.schedule_notice = ""
        return
        raw = str(form_data.get("proposed_for", "") or "").strip()
        proposed: datetime.datetime | None = None
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif app_id <= 0:
            problem = "Choose the confirmed job you want to reschedule."
        elif not raw:
            problem = "Pick the new date and time first."
        else:
            try:
                proposed = datetime.datetime.fromisoformat(raw)
            except ValueError:
                problem = "That date and time couldn't be read — pick it again."
        if not problem and proposed is not None:
            if proposed <= datetime.datetime.now():
                problem = "Choose a date and time in the future."
        if problem or proposed is None:
            async with self:
                self.schedule_error = problem
                self.schedule_form_id = app_id
            return
        async with self:
            self.schedule_busy_id = app_id
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.title, p.author_id, a.helper_id
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        WHERE a.id = :aid
                          AND a.status = 'accepted'
                          AND p.status IN ('open', 'matched')
                          AND (p.author_id = :sid OR a.helper_id = :sid)
                        """
                    ),
                    {"aid": app_id, "sid": int(sid)},
                )
            ).first()
            if row is None:
                await asession.rollback()
            else:
                post_id = int(row[0])
                title = str(row[1] or "a help request")
                other_id = (
                    int(row[3]) if int(row[2]) == int(sid) else int(row[2])
                )
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_job_schedule_proposal
                        SET status = 'superseded'
                        WHERE application_id = :aid AND status = 'pending'
                        """
                    ),
                    {"aid": app_id},
                )
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_job_schedule_proposal
                            (application_id, proposer_id, proposed_for, status)
                        VALUES (:aid, :sid, :when, 'pending')
                        """
                    ),
                    {"aid": app_id, "sid": int(sid), "when": proposed},
                )
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_member_notification
                            (recipient_id, kind, title, body, actor_id,
                             help_post_id, target_route)
                        VALUES (:other, 'schedule_proposed', :title, :body,
                                :sid, :pid, 'help')
                        """
                    ),
                    {
                        "other": other_id,
                        "sid": int(sid),
                        "pid": post_id,
                        "title": f"A new time was proposed: {title}"[:200],
                        "body": (
                            "Your helping partner proposed "
                            f"{_proposal_label(proposed)} for “{title}”. "
                            "Open Help to confirm or decline it."
                        )[:255],
                    },
                )
                await asession.commit()
        if row is None:
            async with self:
                self.schedule_busy_id = 0
                self.schedule_error = (
                    "We couldn't propose that time — this job must be a "
                    "confirmed help arrangement that you are part of."
                )
            return
        async with self:
            self.schedule_busy_id = 0
            self.schedule_form_id = 0
            self.schedule_notice = (
                f"{_proposal_label(proposed)} was proposed. The other person "
                "now needs to confirm it."
            )
        yield rx.toast("New time proposed.", duration=4000)
        yield HelpHubState.load_help_hub
        from app.states.notification_state import NotificationState

        yield NotificationState.load_notifications

    @rx.event(background=True)
    async def respond_to_schedule(self, proposal_id: int, accept: bool):
        """Retired: discuss changes in Inbox instead."""
        return
        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            pid = int(proposal_id)
            self.schedule_error = ""
            self.schedule_notice = ""
            if not sid.isdigit() or pid <= 0:
                self.schedule_error = (
                    "Your session expired — please sign in again."
                )
                return
            self.schedule_busy_id = pid
        agreed = bool(accept)
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT sp.proposer_id, sp.proposed_for, a.id, p.id,
                               p.title
                        FROM skillkind_job_schedule_proposal sp
                        JOIN skillkind_job_application a
                          ON a.id = sp.application_id
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        WHERE sp.id = :spid
                          AND sp.status = 'pending'
                          AND a.status = 'accepted'
                          AND sp.proposer_id <> :sid
                          AND (p.author_id = :sid OR a.helper_id = :sid)
                        """
                    ),
                    {"spid": pid, "sid": int(sid)},
                )
            ).first()
            if row is None:
                await asession.rollback()
            else:
                proposer_id = int(row[0])
                when = row[1]
                app_id = int(row[2])
                post_id = int(row[3])
                title = str(row[4] or "a help request")
                await asession.execute(
                    text(
                        """
                        UPDATE skillkind_job_schedule_proposal
                        SET status = :status, responder_id = :sid,
                            responded_at = now()
                        WHERE id = :spid AND status = 'pending'
                        """
                    ),
                    {
                        "status": "accepted" if agreed else "declined",
                        "sid": int(sid),
                        "spid": pid,
                    },
                )
                if agreed:
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_help_post
                            SET scheduled_for = :when,
                                help_dates = :day,
                                start_time = :clock,
                                updated_at = now()
                            WHERE id = :pid
                            """
                        ),
                        {
                            "when": when,
                            "day": when.date().isoformat(),
                            "clock": when.strftime("%H:%M"),
                            "pid": post_id,
                        },
                    )
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_job_application
                            SET proposed_time = :when
                            WHERE id = :aid
                            """
                        ),
                        {"when": when, "aid": app_id},
                    )
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_member_notification
                            (recipient_id, kind, title, body, actor_id,
                             help_post_id, target_route)
                        VALUES (:other, :kind, :title, :body, :sid, :pid,
                                'help')
                        """
                    ),
                    {
                        "other": proposer_id,
                        "sid": int(sid),
                        "pid": post_id,
                        "kind": (
                            "schedule_confirmed"
                            if agreed
                            else "schedule_declined"
                        ),
                        "title": (
                            f"New time confirmed: {title}"
                            if agreed
                            else f"New time declined: {title}"
                        )[:200],
                        "body": (
                            (
                                f"{_proposal_label(when)} is now the agreed "
                                f"time for “{title}”."
                            )
                            if agreed
                            else (
                                f"Your proposal of {_proposal_label(when)} "
                                f"for “{title}” was declined. The time you "
                                "already agreed stays as it is."
                            )
                        )[:255],
                    },
                )
                await asession.commit()
        if row is None:
            async with self:
                self.schedule_busy_id = 0
                self.schedule_error = (
                    "That proposal can no longer be answered — it may have "
                    "been replaced or already handled."
                )
            return
        async with self:
            self.schedule_busy_id = 0
            self.schedule_form_id = 0
            self.schedule_notice = (
                "New time confirmed — both of you now see the updated day."
                if agreed
                else "Proposal declined. Your agreed time is unchanged."
            )
        yield rx.toast(
            "New time confirmed." if agreed else "Proposal declined.",
            duration=4000,
        )
        yield HelpHubState.load_help_hub
        from app.states.notification_state import NotificationState

        yield NotificationState.load_notifications

    @rx.var
    def needs_nights(self) -> bool:
        return "accommodation" in self.selected_rewards

    @rx.var
    def needs_tour_details(self) -> bool:
        return "guided_tour" in self.selected_rewards

    @rx.var
    def needs_activity_details(self) -> bool:
        return "activity" in self.selected_rewards

    @rx.var
    def needs_other_details(self) -> bool:
        return "other_reward" in self.selected_rewards

    @rx.event
    def toggle_form(self):
        if self.is_saving:
            return
        self.form_open = not self.form_open
        self.rewards_open = False
        self.posting_country = ""
        self.reward_currency = "USD"
        self.budget_quote_allowed = False
        self.duration_quote_allowed = False
        self.calendar_open = False
        self.missing_fields = []
        self.error = ""
        self.success = ""

    @rx.event
    def set_date_input(self, value: str):
        self.date_input = value
        self.date_error = ""

    @rx.event
    def add_date_from_input(self, value: str):
        self.date_input = value
        self.date_error = ""
        return HelpHubState.add_date

    @rx.event
    def add_date(self):
        raw = self.date_input.strip()
        if not raw:
            self.date_error = "Pick a date first, then press Add date."
            return
        try:
            chosen = datetime.date.fromisoformat(raw)
        except ValueError:
            self.date_error = "That date couldn't be read — pick it again."
            return
        if (
            not datetime.date.today()
            <= chosen
            <= _date_ceiling(datetime.date.today())
        ):
            self.date_error = "Choose a date from today through two calendar years from today."
            return
        if raw in self.help_dates:
            self.date_error = "That date is already on your list."
            return
        self.help_dates = sorted([*self.help_dates, raw])
        self.date_input = ""
        self.date_error = ""

    @rx.event
    def remove_date(self, value: str):
        self.help_dates = [d for d in self.help_dates if d != value]
        self.date_error = ""

    @rx.event
    def toggle_reward(self, value: str):
        if value not in REWARD_LABELS:
            return
        if value in self.selected_rewards:
            self.selected_rewards = [
                r for r in self.selected_rewards if r != value
            ]
        else:
            self.selected_rewards = [*self.selected_rewards, value]
        if "money" not in self.selected_rewards:
            self.budget_quote_allowed = False
        self.error = ""

    @rx.event
    def clear_feedback(self):
        self.missing_fields = []
        self.error = ""
        self.success = ""

    @rx.event(background=True)
    async def load_help_hub(self):
        """Load every Help-screen dataset from the managed database.

        Idempotent: a second mount-triggered call while one is already in
        flight returns immediately, so loading state never flips twice and
        already-rendered content is never replaced.
        """
        async with self:
            if self.is_loading:
                return
            sid = (await self.get_state(AuthState)).subscriber_id
            if not sid.isdigit():
                self.upcoming_help = []
                self.confirmed_helpers = []
                self.help_offers = []
                self.declined_offers = []
                self.completed_jobs = []
                self.past_helpers = []
                self.is_loading = False
                self.has_loaded = True
                return
            self.is_loading = True
            self.error = ""
        try:
            await self._load_help_hub_data(sid)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.is_loading = False
                self.has_loaded = True
                self.completed_jobs = []
                self.past_helpers = []
                self.error = "We couldn't load your help requests just now. Please try again."

    async def _load_help_hub_data(self, sid: str) -> None:
        async with rx.asession() as asession:
            completed_jobs, past_helpers = await self._load_completed_history(
                asession, sid
            )
            helper_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.title, COALESCE(p.description, ''),
                               COALESCE(p.location_name, ''),
                               COALESCE(p.city, ''), COALESCE(p.country, ''),
                               COALESCE(p.help_dates, ''), p.scheduled_for,
                               COALESCE(p.start_time, ''),
                               COALESCE(p.duration_minutes, 60),
                               COALESCE(p.tools, ''),
                               COALESCE(p.knowledge_skills, ''),
                               a.status, p.status,
                               poster.display_name, CONCAT('member-', poster.id),
                               COALESCE(pp.avatar_path, ''),
                               COALESCE(p.location_mode, 'approximate'),
                               COALESCE(NULLIF(TRIM(p.accepted_location_name), ''), NULLIF(TRIM(p.location_name), ''), 'Pinned meeting point'),
                               COALESCE(poster.is_verified, FALSE),
                               a.id, NULL::bigint, NULL::timestamp, NULL::bigint,
                               p.latitude, p.longitude,
                               COALESCE(p.accepted_latitude, p.latitude), COALESCE(p.accepted_longitude, p.longitude),
                               poster.id
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        JOIN skillkind_subscriber poster
                          ON poster.id = p.author_id
                        LEFT JOIN skillkind_profile pp
                          ON pp.subscriber_id = poster.id
                        WHERE a.helper_id = :sid
                          AND a.status = 'accepted'
                          AND p.status IN ('open', 'matched')
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = p.author_id
                                     AND mb.blocked_id = a.helper_id)
                                 OR (mb.blocker_id = a.helper_id
                                     AND mb.blocked_id = p.author_id)
                          )
                        ORDER BY COALESCE(a.proposed_time, p.scheduled_for)
                                 ASC NULLS LAST
                        LIMIT 20
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            confirmed_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, p.title, COALESCE(p.description, ''),
                               COALESCE(p.location_name, ''),
                               COALESCE(p.city, ''), COALESCE(p.country, ''),
                               COALESCE(p.help_dates, ''), p.scheduled_for,
                               COALESCE(p.start_time, ''),
                               COALESCE(p.duration_minutes, 60),
                               COALESCE(p.tools, ''),
                               COALESCE(p.knowledge_skills, ''),
                               h.display_name, CONCAT('member-', h.id),
                               COALESCE(hp.username, ''),
                               COALESCE(hp.avatar_path, ''),
                               p.id,
                               COALESCE(p.location_mode, 'approximate'),
                               COALESCE(NULLIF(TRIM(p.accepted_location_name), ''), NULLIF(TRIM(p.location_name), ''), 'Pinned meeting point'),
                               COALESCE(h.is_verified, FALSE),
                               NULL, NULL, NULL,
                               p.latitude, p.longitude,
                               p.accepted_latitude, p.accepted_longitude,
                               COALESCE(hp.helper_rating_avg, 0),
                               COALESCE(hp.helper_rating_count, 0),
                               COALESCE(mt.id, 0) AS thread_id,
                               h.id AS helper_id
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        JOIN skillkind_subscriber h ON h.id = a.helper_id
                        LEFT JOIN skillkind_profile hp
                          ON hp.subscriber_id = h.id
                        LEFT JOIN skillkind_message_thread mt
                          ON mt.post_id = a.post_id
                         AND mt.helper_id = a.helper_id
                        WHERE p.author_id = :sid
                          AND a.status = 'accepted'
                          AND p.status IN ('open', 'matched')
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = p.author_id
                                     AND mb.blocked_id = a.helper_id)
                                 OR (mb.blocker_id = a.helper_id
                                     AND mb.blocked_id = p.author_id)
                          )
                        ORDER BY COALESCE(a.proposed_time, p.scheduled_for)
                                 ASC NULLS LAST
                        LIMIT 20
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
            offer_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, p.title, COALESCE(p.description, ''),
                               COALESCE(p.location_name, ''),
                               COALESCE(p.city, ''), COALESCE(p.country, ''),
                               COALESCE(p.help_dates, ''), p.scheduled_for,
                               COALESCE(p.start_time, ''),
                               COALESCE(p.duration_minutes, 60),
                               COALESCE(p.tools, ''),
                               COALESCE(p.knowledge_skills, ''),
                               COALESCE(a.pitch, ''), a.proposed_time,
                               a.created_at,
                               h.display_name, CONCAT('member-', h.id),
                               COALESCE(hp.username, ''),
                               COALESCE(hp.avatar_path, ''),
                               COALESCE(h.is_verified, FALSE),
                               p.id
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        JOIN skillkind_subscriber h ON h.id = a.helper_id
                        LEFT JOIN skillkind_profile hp
                          ON hp.subscriber_id = h.id
                        WHERE p.author_id = :sid
                          AND a.status = 'pending'
                          AND (
                              SELECT opener.sender_id
                              FROM skillkind_message_thread origin
                              JOIN skillkind_message opener ON opener.thread_id = origin.id
                              WHERE origin.post_id = a.post_id AND origin.helper_id = a.helper_id
                              ORDER BY opener.sent_at ASC, opener.id ASC LIMIT 1
                          ) = a.helper_id
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
            declined_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, p.title,
                               COALESCE(p.location_name, ''),
                               COALESCE(p.city, ''), COALESCE(p.country, ''),
                               COALESCE(p.help_dates, ''), p.scheduled_for,
                               COALESCE(p.start_time, ''),
                               COALESCE(a.responded_at, a.created_at),
                               h.display_name, CONCAT('member-', h.id),
                               COALESCE(hp.avatar_path, ''),
                               COALESCE(h.is_verified, FALSE)
                        FROM skillkind_job_application a
                        JOIN skillkind_help_post p ON p.id = a.post_id
                        JOIN skillkind_subscriber h ON h.id = a.helper_id
                        LEFT JOIN skillkind_profile hp
                          ON hp.subscriber_id = h.id
                        WHERE p.author_id = :sid
                          AND a.status = 'declined'
                          AND p.status NOT IN ('cancelled', 'deleted')
                          AND NOT EXISTS (
                              SELECT 1 FROM skillkind_member_block mb
                              WHERE (mb.blocker_id = p.author_id
                                     AND mb.blocked_id = a.helper_id)
                                 OR (mb.blocker_id = a.helper_id
                                     AND mb.blocked_id = p.author_id)
                          )
                        ORDER BY COALESCE(a.responded_at, a.created_at) DESC
                        LIMIT 20
                        """
                    ),
                    {"sid": int(sid)},
                )
            ).all()
        async with self:
            if (await self.get_state(AuthState)).subscriber_id != sid:
                self.completed_jobs = []
                self.past_helpers = []
                self.is_loading = False
                return
            self.completed_jobs = completed_jobs
            self.past_helpers = past_helpers
            self.upcoming_help = [
                {
                    "id": int(r[0]),
                    "post_id": int(r[0]),
                    "application_id": int(r[20]),
                    "proposal_id": int(r[21]) if r[21] is not None else 0,
                    "proposal_when": _proposal_label(r[22]),
                    "proposal_mine": bool(
                        r[23] is not None and int(r[23]) == int(sid)
                    ),
                    "can_respond": bool(
                        r[21] is not None
                        and r[23] is not None
                        and int(r[23]) != int(sid)
                    ),
                    "title": str(r[1] or "Help request"),
                    "description": str(r[2] or ""),
                    "location": _helper_location(
                        str(r[17] or "approximate"),
                        str(r[18] or ""),
                        str(r[3] or ""),
                        str(r[4] or ""),
                        str(r[5] or ""),
                    ),
                    "location_mode": str(r[17] or "approximate"),
                    "accepted_location": str(r[18] or ""),
                    "dates": _agreed_label(
                        r[7], str(r[6] or ""), str(r[8] or "")
                    ),
                    "start_time": str(r[8] or ""),
                    "hours": _hours_label(int(r[9] or 0), str(r[11] or "")),
                    "tools": str(r[10] or ""),
                    "knowledge": decode_knowledge(str(r[11] or ""))[0],
                    "status": (
                        "Matched"
                        if str(r[13] or "") == "matched"
                        else "Accepted"
                    ),
                    "other_id": int(r[28] or 0),
                    "other_name": str(r[14] or "A Go and Help neighbour"),
                    "other_avatar_seed": str(r[15] or "neighbour"),
                    "other_avatar": str(r[16] or ""),
                    "other_verified": bool(r[19]),
                    "directions_url": job_directions_url(
                        str(r[17] or "approximate"),
                        str(r[18] or ""),
                        r[26],
                        r[27],
                        r[24],
                        r[25],
                    ),
                }
                for r in helper_rows
            ]
            self.confirmed_helpers = [
                {
                    "id": int(r[0]),
                    "post_id": int(r[16]),
                    "application_id": int(r[0]),
                    "thread_id": int(r[29] or 0),
                    "proposal_id": int(r[20]) if r[20] is not None else 0,
                    "proposal_when": _proposal_label(r[21]),
                    "proposal_mine": bool(
                        r[22] is not None and int(r[22]) == int(sid)
                    ),
                    "can_respond": bool(
                        r[20] is not None
                        and r[22] is not None
                        and int(r[22]) != int(sid)
                    ),
                    "location_mode": str(r[17] or "approximate"),
                    "accepted_location": str(r[18] or ""),
                    "needs_accepted": bool(not str(r[18] or "").strip()),
                    "title": str(r[1] or "Help request"),
                    "description": str(r[2] or ""),
                    "location": _location(
                        str(r[3] or ""), str(r[4] or ""), str(r[5] or "")
                    ),
                    "dates": _agreed_label(
                        r[7], str(r[6] or ""), str(r[8] or "")
                    ),
                    "start_time": str(r[8] or ""),
                    "hours": _hours_label(int(r[9] or 0)),
                    "tools": str(r[10] or ""),
                    "knowledge": decode_knowledge(str(r[11] or ""))[0],
                    "status": "Confirmed",
                    "helper_rating": float(r[27] or 0),
                    "helper_rating_count": int(r[28] or 0),
                    "helper_id": int(r[30] or 0),
                    "schedule_time": _schedule_parts(
                        r[7],
                        str(r[6] or ""),
                        str(r[8] or ""),
                        int(r[9] or 0),
                        str(r[11] or ""),
                    )[0],
                    "schedule_date": _schedule_parts(
                        r[7], str(r[6] or ""), str(r[8] or ""), int(r[9] or 0)
                    )[1],
                    "helper_name": str(r[12] or "A Go and Help neighbour"),
                    "helper_avatar_seed": str(r[13] or "neighbour"),
                    "helper_handle": f"@{r[14]}" if r[14] else "",
                    "helper_avatar": str(r[15] or ""),
                    "helper_verified": bool(r[19]),
                    "directions_url": job_directions_url(
                        str(r[17] or "approximate"),
                        str(r[18] or ""),
                        r[25],
                        r[26],
                        r[23],
                        r[24],
                    ),
                }
                for r in confirmed_rows
            ]
            self.help_offers = [
                {
                    "id": int(r[0]),
                    "post_id": int(r[20] or 0),
                    "key": str(int(r[0])),
                    "title": str(r[1] or "Help request"),
                    "description": str(r[2] or ""),
                    "location": _location(
                        str(r[3] or ""), str(r[4] or ""), str(r[5] or "")
                    ),
                    "dates": _dates_label(
                        str(r[6] or ""), r[7], str(r[8] or "")
                    ),
                    "start_time": str(r[8] or ""),
                    "hours": _hours_label(int(r[9] or 0)),
                    "tools": str(r[10] or ""),
                    "knowledge": decode_knowledge(str(r[11] or ""))[0],
                    "pitch": str(r[12] or ""),
                    "proposed": r[13].strftime("%a, %b %d %Y · %H:%M")
                    if r[13] is not None
                    else "No time proposed yet",
                    "applied": r[14].strftime("%b %d, %Y · %H:%M")
                    if r[14] is not None
                    else "",
                    "helper_name": str(r[15] or "A Go and Help neighbour"),
                    "helper_avatar_seed": str(r[16] or "neighbour"),
                    "helper_handle": f"@{r[17]}" if r[17] else "",
                    "helper_avatar": str(r[18] or ""),
                    "helper_verified": bool(r[19]),
                }
                for r in offer_rows
            ]
            self.declined_offers = [
                {
                    "id": int(r[0]),
                    "title": str(r[1] or "Help request"),
                    "location": _location(
                        str(r[2] or ""), str(r[3] or ""), str(r[4] or "")
                    ),
                    "dates": _dates_label(
                        str(r[5] or ""), r[6], str(r[7] or "")
                    ),
                    "responded": r[8].strftime("%b %d, %Y")
                    if r[8] is not None
                    else "",
                    "helper_name": str(r[9] or "A Go and Help neighbour"),
                    "helper_avatar_seed": str(r[10] or "neighbour"),
                    "helper_avatar": str(r[11] or ""),
                    "helper_verified": bool(r[12]),
                }
                for r in declined_rows
            ]
            self.is_loading = False
            self.has_loaded = True

    @rx.event(background=True)
    async def create_help_request(self, form_data: dict[str, Any]):
        """Validate and insert a help request using the new Help fields."""
        from app.states.help_post_state import HelpPostState
        from app.states.map_picker_state import MapPickerState

        async with self:
            sid = (await self.get_state(AuthState)).subscriber_id
            if self.is_saving:
                return
            dates = list(self.help_dates)
            day_mode = self.day_mode
            time_mode = self.time_mode
            flexible_days = list(self.flexible_days)
            custom_weekdays = list(self.custom_weekdays)
            rewards = list(self.selected_rewards)
            reward_currency = supported_currency(self.reward_currency)
            budget_quote_allowed = self.budget_quote_allowed
            duration_quote_allowed = self.duration_quote_allowed
            saved_period_count = self.duration_period_count
            saved_period_unit = self.duration_period_unit
            required_languages = list(self.required_languages)
            help_state = await self.get_state(HelpPostState)
            photo_paths = list(help_state.pending_photo_paths)
            categories = normalize_categories(help_state.selected_categories)
            # Public location is always approximate, whatever any client
            # payload or leftover state says.
            location_mode = "approximate"
            picker = await self.get_state(MapPickerState)
            has_point = bool(picker.has_point)
            job_latitude = float(picker.latitude)
            job_longitude = float(picker.longitude)
            has_point = (
                has_point
                and math.isfinite(job_latitude)
                and math.isfinite(job_longitude)
                and -90 <= job_latitude <= 90
                and -180 <= job_longitude <= 180
            )

        missing: list[str] = []
        for key, label in (
            ("title", "Job title"),
            ("description", "Job description"),
        ):
            if not str(form_data.get(key, "") or "").strip():
                missing.append(label)
        if not categories:
            missing.append("Job category")
        day_valid = False
        if day_mode == "specific":
            today = datetime.date.today()
            for raw in dates:
                try:
                    chosen = datetime.date.fromisoformat(raw)
                    day_valid = day_valid or today <= chosen <= _date_ceiling(
                        today
                    )
                except ValueError:
                    pass
        elif day_mode == "flexible":
            day_valid = bool(_flexible_tokens(flexible_days, custom_weekdays))
            if "Custom" in flexible_days and "Any Day" not in flexible_days:
                day_valid = day_valid and any(
                    day in WEEKDAYS for day in custom_weekdays
                )
        if not day_valid:
            missing.append("Date")
        if not has_point:
            for key, label in (
                ("address", "Address"),
                ("city", "City"),
                ("country", "Country"),
            ):
                if not str(form_data.get(key, "") or "").strip():
                    missing.append(label)
        if not rewards:
            missing.append("Rewards")
        for reward, key, label in (
            ("accommodation", "accommodation_nights", "Number of nights"),
            ("guided_tour", "guided_tour_details", "Guided tour details"),
            ("activity", "activity_details", "Activity details"),
            ("other_reward", "other_reward_details", "Other reward details"),
        ):
            if (
                reward in rewards
                and not str(form_data.get(key, "") or "").strip()
            ):
                missing.append(label)
        if (
            "money" in rewards
            and not budget_quote_allowed
            and not str(form_data.get("money_budget", "") or "").strip()
        ):
            missing.append("Enter your budget")
        async with self:
            self.missing_fields = missing
            self.error = ""
            self.success = ""
            if missing:
                self.form_open = True
        if missing:
            return

        # At least one category is always required; the upper bound is checked
        # again against the database membership record before the INSERT.
        if not categories or len(categories) > MAX_REQUEST_CATEGORIES:
            async with self:
                self.error = (
                    "Pick at least one category so helpers know what kind of "
                    "task this is."
                )
                self.success = ""
                self.form_open = True
            return

        title = str(form_data.get("title", "") or "").strip()
        description = str(form_data.get("description", "") or "").strip()
        start_time = ""
        tools = ""
        knowledge = ""
        address = str(form_data.get("address", "") or "").strip()
        city = str(form_data.get("city", "") or "").strip()
        country = str(form_data.get("country", "") or "").strip()
        nights_raw = str(
            form_data.get("accommodation_nights", "") or ""
        ).strip()
        tour_details = str(
            form_data.get("guided_tour_details", "") or ""
        ).strip()
        activity_details = str(
            form_data.get("activity_details", "") or ""
        ).strip()
        other_details = str(
            form_data.get("other_reward_details", "") or ""
        ).strip()

        today = datetime.date.today()
        ceiling = _date_ceiling(today)
        valid_dates: list[str] = []
        schedule_problem = ""
        if day_mode == "specific":
            for raw in dates:
                try:
                    parsed = datetime.date.fromisoformat(raw)
                except ValueError:
                    schedule_problem = "Choose valid dates."
                    break
                if not today <= parsed <= ceiling:
                    schedule_problem = "Dates must be from today through two calendar years from today."
                    break
                valid_dates.append(parsed.isoformat())
            valid_dates = sorted(set(valid_dates))
            if not valid_dates:
                schedule_problem = "Add at least one date."
            encoded_dates = ",".join(valid_dates)
            anchor = (
                datetime.date.fromisoformat(valid_dates[0])
                if valid_dates
                else today
            )
        elif day_mode == "flexible":
            tokens = _flexible_tokens(flexible_days, custom_weekdays)
            if not tokens:
                schedule_problem = "Choose at least one flexible day option."
            elif (
                "Custom" in flexible_days
                and "Any Day" not in flexible_days
                and not any(day in WEEKDAYS for day in custom_weekdays)
            ):
                schedule_problem = "Choose at least one weekday for Custom."
            encoded_dates = f"flexible:{','.join(tokens)}"
            anchor = today + datetime.timedelta(days=1)
            for offset in range(7):
                candidate = today + datetime.timedelta(days=offset + 1)
                weekday = candidate.weekday()
                if (
                    "Any Day" in tokens
                    or ("Any weekday" in tokens and weekday < 5)
                    or ("Any weekend" in tokens and weekday >= 5)
                    or WEEKDAYS[weekday] in tokens
                ):
                    anchor = candidate
                    break
        else:
            schedule_problem = "Choose Specific days or Flexible days."
            encoded_dates = ""
            anchor = today
        clock = datetime.time(0, 0)
        try:
            prefix = "specific" if time_mode == "specific" else "from"
            clock, start_time = self._parse_start_time(
                time_mode,
                str(form_data.get(f"{prefix}_hour", "")),
                str(form_data.get(f"{prefix}_minute", "")),
                str(form_data.get("to_hour", "")),
                str(form_data.get("to_minute", "")),
            )
        except ValueError:
            schedule_problem = "Choose hours 00–23 and five-minute increments, with a range end later than its start."

        duration_problem = ""
        duration_minutes, period_count, period_unit = 0, 1, "day"
        try:
            if duration_quote_allowed:
                period_count, period_unit = (
                    saved_period_count,
                    saved_period_unit,
                )
            else:
                duration_minutes, period_count, period_unit = (
                    self._parse_duration(
                        str(form_data.get("duration_hours", "")),
                        str(form_data.get("duration_minutes_part", "")),
                        str(form_data.get("duration_period_count", "")),
                        str(form_data.get("duration_period_unit", "")),
                    )
                )
        except ValueError:
            duration_problem = "Choose 0–10 hours, minutes in steps of 5, and 1–7 days, weeks or months."
        money_problem = ""
        reward_value, money_summary = Decimal("0"), ""
        try:
            reward_value, money_summary = self._money_details(
                "money" in rewards,
                budget_quote_allowed,
                str(form_data.get("money_budget", "") or ""),
                reward_currency,
            )
        except ValueError as error:
            money_problem = str(error)
        nights = 0
        problem = ""
        if not sid.isdigit():
            problem = "Your session expired — please sign in again."
        elif len(title) < 4:
            problem = "Give your request a Job title (4+ characters)."
        elif len(title) > 160:
            problem = "Keep the Job title under 160 characters."
        elif len(description) < 15:
            problem = "Add a Job description with a little more detail."
        elif len(description) > 500:
            problem = "Keep the Job description under 500 characters."
        elif schedule_problem:
            problem = schedule_problem
        elif duration_problem:
            problem = duration_problem
        elif money_problem:
            problem = money_problem
        elif not has_point and not all((address, city, country)):
            problem = (
                "Add Address, City and Country, or pin the exact meeting point."
            )
        elif any(code not in LANGUAGE_CODES for code in required_languages):
            problem = "Choose languages from the supplied list."
        elif not rewards or any(
            reward not in REWARD_LABELS for reward in rewards
        ):
            problem = "Choose at least one valid reward you can offer."
        elif len(photo_paths) > 5:
            problem = "Attach no more than five photos."
        if not problem and "accommodation" in rewards:
            if not nights_raw.isdigit() or int(nights_raw) < 1:
                problem = "Add how many nights of accommodation you can offer."
            else:
                nights = int(nights_raw)
        if not problem and "guided_tour" in rewards and len(tour_details) < 3:
            problem = "Describe the guided tour you can offer."
        if not problem and "activity" in rewards and len(activity_details) < 3:
            problem = "Describe the activity you can offer."
        if not problem and "other_reward" in rewards and len(other_details) < 3:
            problem = "Describe your other reward."
        if problem:
            async with self:
                self.error = problem
                self.success = ""
                self.form_open = True
            return

        if "guided_tour" not in rewards:
            tour_details = ""
        if "activity" not in rewards:
            activity_details = ""
        if "other_reward" not in rewards:
            other_details = ""

        scheduled = datetime.datetime.combine(anchor, clock)
        primary_reward = LEGACY_REWARD_TYPE.get(rewards[0], "other")
        summary_parts = [
            money_summary if key == "money" else REWARD_LABELS.get(key, key)
            for key in rewards
        ]
        if nights:
            summary_parts = [
                f"Accommodation ({nights} nights)"
                if part == "Accommodation"
                else part
                for part in summary_parts
            ]
        extra = [
            detail
            for detail in (tour_details, activity_details, other_details)
            if detail
        ]
        reward_summary = ", ".join(summary_parts)
        if extra:
            reward_summary = f"{reward_summary} — {'; '.join(extra)}"
        reward_summary = reward_summary[:255]

        async with self:
            if self.is_saving:
                return
            self.is_saving = True
            self.error = ""
            self.success = ""
        try:
            async with rx.asession() as asession:
                async with asession.begin():
                    allowed, premium, _used, limit = await check_post_allowance(
                        asession, int(sid)
                    )
                    category_limit = request_category_limit(premium)
                    if not allowed or len(categories) > category_limit:
                        message = (
                            cap_message(premium, limit)
                            if not allowed
                            else category_limit_message(category_limit)
                        )
                        async with self:
                            self.error = message
                            self.form_open = True
                            membership = await self.get_state(MembershipState)
                            if not premium:
                                membership.paywall_open = True
                                membership.upgrade_reason = (
                                    message
                                    if not allowed
                                    else CATEGORY_UPGRADE_REASON
                                )
                        return
                    helpers_needed = 1
                    if premium:
                        raw_helpers = str(
                            form_data.get("helpers_needed", "1")
                        ).strip()
                        if (
                            not raw_helpers.isascii()
                            or not raw_helpers.isdecimal()
                            or not 1 <= int(raw_helpers) <= 500
                        ):
                            async with self:
                                self.error = "Number of people required must be a whole number from 1 to 500."
                                self.form_open = True
                            return
                        helpers_needed = int(raw_helpers)
                    lifetime = post_interval_for_tier(premium)
                    post_id = (
                        await asession.execute(
                            text(f"""
                        INSERT INTO skillkind_help_post
                            (author_id, title, description, category, category_tags,
                             reward_type, reward_details, reward_value, reward_currency,
                             location_name, city, country, latitude, longitude,
                             accepted_location_name, accepted_latitude, accepted_longitude,
                             scheduled_for, duration_minutes, help_dates, start_time,
                             tools, knowledge_skills, reward_types, accommodation_nights,
                             guided_tour_details, activity_details, other_reward_details,
                             urgency, helpers_needed, status, view_count, expires_at,
                             premium_priority, location_mode)
                        VALUES (:sid, :title, :description, :category, :category_tags,
                             :reward_type, :reward_details, :reward_value, :reward_currency,
                             :address, :city, :country, :latitude, :longitude,
                             :address, :latitude, :longitude,
                             :scheduled, :duration, :help_dates, :start_time,
                             :tools, :knowledge, :reward_types, :nights,
                             :tour_details, :activity_details, :other_details,
                             'flexible', :helpers_needed, 'open', 0,
                             now() + INTERVAL '{lifetime}', :priority, :location_mode)
                        RETURNING id
                    """),
                            {
                                "sid": int(sid),
                                "title": title,
                                "description": description,
                                "category": primary_category(categories),
                                "category_tags": join_categories(
                                    categories, category_limit
                                ),
                                "reward_type": primary_reward,
                                "reward_details": reward_summary,
                                "reward_value": reward_value,
                                "reward_currency": reward_currency,
                                "address": address[:200],
                                "city": city[:120],
                                "country": country[:120],
                                "latitude": job_latitude if has_point else None,
                                "longitude": job_longitude
                                if has_point
                                else None,
                                "scheduled": scheduled,
                                "duration": duration_minutes,
                                "help_dates": encoded_dates,
                                "start_time": start_time,
                                "tools": tools,
                                "knowledge": encode_knowledge_with_period(
                                    knowledge,
                                    required_languages,
                                    period_count,
                                    period_unit,
                                ),
                                "reward_types": ",".join(rewards)[:255],
                                "nights": nights,
                                "tour_details": tour_details[:500],
                                "activity_details": activity_details[:500],
                                "other_details": other_details[:500],
                                "helpers_needed": helpers_needed,
                                "priority": premium,
                                "location_mode": location_mode
                                if has_point
                                else "place",
                            },
                        )
                    ).scalar_one()
                    from app.field_requests import notify_field_helpers

                    await notify_field_helpers(asession, int(post_id))
                    if photo_paths:
                        await asession.execute(
                            text("""
                            INSERT INTO skillkind_help_post_photo (help_post_id, path, display_order)
                            VALUES (:post_id, :path, :position)
                        """),
                            [
                                {
                                    "post_id": post_id,
                                    "path": path,
                                    "position": index,
                                }
                                for index, path in enumerate(photo_paths)
                            ],
                        )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "We couldn't save your request and photos. Your form is still here — please try again."
                self.form_open = True
            return
        finally:
            async with self:
                self.is_saving = False

        async with self:
            notification_language = (
                await self.get_state(AuthState)
            ).preferred_language
            self.is_saving = False
            self.form_open = False
            self.missing_fields = []
            self.day_mode = "specific"
            self.budget_quote_allowed = False
            self.duration_quote_allowed = False
            self.time_mode = "specific"
            self.duration_period_count = 1
            self.duration_period_unit = "day"
            self.flexible_days = []
            self.custom_weekdays = []
            self.flexible_days_open = False
            self.date_error = ""
            self.help_dates = []
            self.calendar_open = False
            self.date_input = ""
            self.selected_rewards = []
            self.rewards_open = False
            self.posting_country = ""
            self.reward_currency = "USD"
            self.required_languages = []
            self.languages_open = False
            self.job_location_mode = "approximate"
            picker = await self.get_state(MapPickerState)
            picker.open_key = ""
            picker.has_point = False
            picker.latitude = 0.0
            picker.longitude = 0.0
            picker.status = ""
            picker.error = ""
            self.success = (
                f'"{title}" is live — helpers nearby can offer their hands now.'
            )
            help_state = await self.get_state(HelpPostState)
            help_state.pending_photo_paths = []
            help_state.photo_notice = ""
            help_state.photo_error = ""
            help_state.selected_category = ""
            help_state.selected_categories = []
            help_state.category_dropdown_open = False
            help_state.error = ""
        from app.interface_i18n import translate

        yield rx.toast(
            translate(notification_language, "Help request posted."),
            duration=4000,
        )
        yield HelpHubState.load_help_hub
        yield HelpPostState.load_recent
        from app.states.profile_state import ProfileState

        yield ProfileState.load_profile
