import datetime
import math
from decimal import Decimal

from app.countries import STRIPE_CURRENCIES, supported_currency
from app.skill_categories import CATEGORY_CHOICES
from app.states.help_hub_state import (
    HelpHubState,
    LEGACY_REWARD_TYPE,
    REWARD_LABELS,
    _date_ceiling,
)

REQUEST_TEXT_FIELDS = (
    "request_title",
    "request_description",
    "request_category",
    "request_date",
    "request_reward",
    "request_currency",
    "request_budget",
    "request_other",
)


def normalize_request_payload(value: object) -> str:
    """Keep primitive input text bounded; never stringify rich objects."""
    if type(value) is str:
        return value[:1000]
    if type(value) in (int, float, bool):
        return str(value)[:1000]
    return ""


def validate_request(
    title: str,
    description: str,
    category: str,
    day: str,
    reward: str,
    currency: str,
    budget: str,
    quote: bool,
    other: str,
    *,
    allow_free: bool = False,
) -> dict[str, str | datetime.datetime | Decimal]:
    title, description, other = (
        title.strip(),
        description.strip(),
        other.strip(),
    )
    if not 4 <= len(title) <= 160:
        raise ValueError("Job Title must contain 4–160 characters.")
    if not 15 <= len(description) <= 500:
        raise ValueError("Job description must contain 15–500 characters.")
    if category not in {item["value"] for item in CATEGORY_CHOICES}:
        raise ValueError("Choose one valid Job category.")
    try:
        chosen = datetime.date.fromisoformat(day)
    except ValueError as e:
        raise ValueError("Choose a valid date.") from e
    today = datetime.date.today()
    if not today <= chosen <= _date_ceiling(today):
        raise ValueError(
            "Date must be from today through two calendar years from today."
        )
    free = allow_free and not reward.strip()
    if not free and reward not in REWARD_LABELS:
        raise ValueError("Choose a valid reward.")
    if currency not in STRIPE_CURRENCIES:
        raise ValueError("Choose a supported currency.")
    if reward == "other_reward" and not 3 <= len(other) <= 500:
        raise ValueError("Describe your other reward in 3–500 characters.")
    value, money = HelpHubState._money_details(
        reward == "money", quote, budget, currency
    )
    if reward == "money":
        details = money
    else:
        details = "Free" if free else REWARD_LABELS[reward]
    other = other if reward == "other_reward" else ""
    if other:
        details = f"{details} — {other}"
    return {
        "title": title,
        "description": description,
        "category": category,
        "help_dates": chosen.isoformat(),
        "scheduled": datetime.datetime.combine(
            chosen, datetime.time(13, 0), datetime.UTC
        ),
        "start_time": "13:00",
        "reward_type": "gratitude_only" if free else LEGACY_REWARD_TYPE[reward],
        "reward_types": "gratitude_only" if free else reward,
        "reward_details": details[:255],
        "reward_value": value,
        "reward_currency": supported_currency(currency),
        "other_details": other,
    }


def valid_request_point(
    has_point: bool, latitude: float, longitude: float
) -> bool:
    return (
        has_point
        and math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


FIRST_REQUEST_INSERT = """
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
VALUES (:sid, :title, :description, :category, :category,
    :reward_type, :reward_details, :reward_value, :reward_currency,
    '', '', '', :latitude, :longitude, '', :latitude, :longitude,
    :scheduled, 60, :help_dates, :start_time,
    '', '', :reward_types, 0, '', '', :other_details,
    'flexible', 1, 'open', 0, now() + CAST(:lifetime AS interval),
    :priority, 'approximate')
RETURNING id
"""

EDITABLE_POST = """p.author_id = :sid AND p.status = 'open'
AND NOT EXISTS (SELECT 1 FROM skillkind_job_application a WHERE a.post_id = p.id)"""

EDIT_REQUEST_UPDATE = f"""
UPDATE skillkind_help_post p
SET title = :title, description = :description,
    category = :category, category_tags = :category,
    help_dates = :help_dates,
    scheduled_for = (CAST(:help_dates AS date) + COALESCE(
        (p.scheduled_for AT TIME ZONE 'UTC')::time, TIME '13:00')) AT TIME ZONE 'UTC',
    start_time = COALESCE(NULLIF(p.start_time, ''), '13:00'),
    reward_type = :reward_type, reward_types = :reward_types,
    reward_details = :reward_details, reward_value = :reward_value,
    reward_currency = :reward_currency, other_reward_details = :other_details,
    accommodation_nights = 0, guided_tour_details = '', activity_details = '',
    latitude = CASE WHEN :repin THEN :latitude ELSE p.latitude END,
    longitude = CASE WHEN :repin THEN :longitude ELSE p.longitude END,
    accepted_latitude = CASE WHEN :repin THEN :latitude ELSE p.accepted_latitude END,
    accepted_longitude = CASE WHEN :repin THEN :longitude ELSE p.accepted_longitude END,
    location_name = CASE WHEN :repin THEN '' ELSE p.location_name END,
    accepted_location_name = CASE WHEN :repin THEN '' ELSE p.accepted_location_name END,
    location_mode = CASE WHEN :repin THEN 'approximate' ELSE p.location_mode END,
    updated_at = now()
WHERE p.id = :pid AND {EDITABLE_POST}
RETURNING p.id
"""
