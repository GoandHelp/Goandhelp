"""Cadence maths and the lazy materializer for recurring help requests.

Every date calculation is timezone-safe: the schedule stores an IANA timezone
name, the cadence is advanced on the LOCAL wall clock (so a daily 09:00 job
stays at 09:00 across a DST change) and the result is converted back to UTC
before it ever touches the database.
"""

import calendar
import datetime
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import text

from app.membership import check_post_allowance, post_interval_for_tier
from app.models import (
    DEFAULT_SCHEDULE_TIMEZONE,
    RECURRENCE_BIWEEKLY,
    RECURRENCE_CADENCES,
    RECURRENCE_DAILY,
    RECURRENCE_MAX_INTERVAL,
    RECURRENCE_MONTHLY,
    RECURRENCE_WEEKLY,
)

# Tap-first cadence cards shown on the Ask for Help form.
CADENCE_CHOICES: list[dict[str, str]] = [
    {
        "value": RECURRENCE_DAILY,
        "label": "Daily",
        "blurb": "Same time every day",
    },
    {
        "value": RECURRENCE_WEEKLY,
        "label": "Weekly",
        "blurb": "Same weekday each week",
    },
    {
        "value": RECURRENCE_BIWEEKLY,
        "label": "Every two weeks",
        "blurb": "Same weekday, fortnightly",
    },
    {
        "value": RECURRENCE_MONTHLY,
        "label": "Monthly",
        "blurb": "Same date each month",
    },
]

CADENCE_LABELS: dict[str, str] = {
    item["value"]: item["label"] for item in CADENCE_CHOICES
}

# "Every two weeks" already carries its own multiplier, so no interval choice.
INTERVAL_CADENCES: tuple[str, ...] = (
    RECURRENCE_DAILY,
    RECURRENCE_WEEKLY,
    RECURRENCE_MONTHLY,
)

UNIT_LABELS: dict[str, str] = {
    RECURRENCE_DAILY: "day",
    RECURRENCE_WEEKLY: "week",
    RECURRENCE_BIWEEKLY: "two weeks",
    RECURRENCE_MONTHLY: "month",
}

# How many missed posts one lazy pass may create for a member at once.
MAX_CATCH_UP_POSTS = 5


def cadence_allows_interval(cadence: str) -> bool:
    return cadence in INTERVAL_CADENCES


def interval_choices(cadence: str) -> list[dict[str, str]]:
    unit = UNIT_LABELS.get(cadence, "time")
    options: list[dict[str, str]] = [{"value": "1", "label": f"Every {unit}"}]
    for count in range(2, 7):
        options.append({"value": str(count), "label": f"Every {count} {unit}s"})
    return options


def clean_cadence(value: str) -> str:
    return value if value in RECURRENCE_CADENCES else ""


def clean_interval(value: str | int, cadence: str) -> int:
    if not cadence_allows_interval(cadence):
        return 1
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    if count < 1 or count > RECURRENCE_MAX_INTERVAL:
        return 0
    return count


def cadence_summary(cadence: str, interval: int) -> str:
    """A short, human phrase for one cadence, e.g. 'Every 3 weeks'."""
    if cadence == RECURRENCE_BIWEEKLY:
        return "Every two weeks"
    unit = UNIT_LABELS.get(cadence, "time")
    if interval <= 1:
        return f"Every {unit}"
    return f"Every {interval} {unit}s"


def zone(name: str) -> ZoneInfo | datetime.tzinfo:
    try:
        return ZoneInfo(name or DEFAULT_SCHEDULE_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError) as e:
        logging.exception(f"Error: {e}")
        return datetime.UTC


def as_utc(value: datetime.datetime) -> datetime.datetime:
    """Treat a naive value as UTC; normalise anything else to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.UTC)
    return value.astimezone(datetime.UTC)


def next_occurrence(
    current: datetime.datetime,
    cadence: str,
    interval: int = 1,
    tz_name: str = DEFAULT_SCHEDULE_TIMEZONE,
) -> datetime.datetime:
    """The moment after `current` for this cadence, in UTC."""
    tz = zone(tz_name)
    local = as_utc(current).astimezone(tz).replace(tzinfo=None)
    step = max(1, min(int(interval or 1), RECURRENCE_MAX_INTERVAL))
    if cadence == RECURRENCE_DAILY:
        moved = local + datetime.timedelta(days=step)
    elif cadence == RECURRENCE_WEEKLY:
        moved = local + datetime.timedelta(weeks=step)
    elif cadence == RECURRENCE_BIWEEKLY:
        moved = local + datetime.timedelta(weeks=2)
    else:
        month_index = local.month - 1 + step
        year = local.year + month_index // 12
        month = month_index % 12 + 1
        day = min(local.day, calendar.monthrange(year, month)[1])
        moved = local.replace(year=year, month=month, day=day)
    # Re-attach the zone AFTER the wall-clock arithmetic so the local time of
    # day is preserved even across a daylight-saving transition.
    return moved.replace(tzinfo=tz).astimezone(datetime.UTC)


def local_date(value: datetime.datetime, tz_name: str) -> datetime.date:
    return as_utc(value).astimezone(zone(tz_name)).date()


COPY_POST_SQL = """
INSERT INTO skillkind_help_post
    (author_id, title, description, category, category_tags, reward_type,
     reward_details, reward_value, reward_currency, location_name, city,
     country, latitude, longitude, scheduled_for, duration_minutes, urgency,
     helpers_needed, status, view_count, expires_at, premium_priority,
     help_dates, start_time, tools, knowledge_skills, reward_types,
     accommodation_nights, guided_tour_details, activity_details,
     other_reward_details, location_mode, accepted_location_name,
     accepted_latitude, accepted_longitude)
SELECT p.author_id, p.title, p.description, p.category, p.category_tags,
       p.reward_type, p.reward_details, p.reward_value, p.reward_currency,
       p.location_name, p.city, p.country, p.latitude, p.longitude,
       :occurrence_at, p.duration_minutes, p.urgency, p.helpers_needed,
       'open', 0, now() + INTERVAL '{lifetime}', :priority,
       p.help_dates, p.start_time, p.tools, p.knowledge_skills,
       p.reward_types, p.accommodation_nights, p.guided_tour_details,
       p.activity_details, p.other_reward_details,
       'approximate',
       '', NULL, NULL
FROM skillkind_help_post p
WHERE p.id = :source_id AND p.author_id = :sid
RETURNING id
"""


async def materialize_due_schedules(asession, sid: int) -> int:
    """Create the posts every due active schedule of this member owes.

    Transaction-safe and idempotent: due schedules are locked with
    FOR UPDATE SKIP LOCKED, each generated post is recorded through the
    unique (schedule, occurrence_at) occurrence constraint, and the member's
    posting entitlement is re-checked before every insert. When the cap is
    reached the occurrence simply stays due — it is never bypassed.
    """
    created = 0
    now = datetime.datetime.now(datetime.UTC)
    due_rows = (
        await asession.execute(
            text(
                """
                SELECT id, source_post_id, cadence, interval_count,
                       timezone_name, next_occurrence_at, end_date,
                       occurrence_count
                FROM skillkind_recurring_help_schedule
                WHERE owner_id = :sid
                  AND status = 'active'
                  AND next_occurrence_at IS NOT NULL
                  AND next_occurrence_at <= now()
                ORDER BY next_occurrence_at ASC
                LIMIT 20
                FOR UPDATE SKIP LOCKED
                """
            ),
            {"sid": int(sid)},
        )
    ).all()
    if not due_rows:
        return 0

    capped = False
    for row in due_rows:
        schedule_id = int(row[0])
        source_id = int(row[1])
        cadence = str(row[2] or RECURRENCE_WEEKLY)
        interval = max(1, int(row[3] or 1))
        tz_name = str(row[4] or DEFAULT_SCHEDULE_TIMEZONE)
        occurrence_at = as_utc(row[5])
        end_date: datetime.date | None = row[6]
        count = int(row[7] or 0)
        finished = False

        while occurrence_at <= now and created < MAX_CATCH_UP_POSTS:
            if end_date is not None and (
                local_date(occurrence_at, tz_name) > end_date
            ):
                finished = True
                break
            allowed, premium, _used, _limit = await check_post_allowance(
                asession, int(sid)
            )
            if not allowed:
                # Leave this occurrence due; the cap is authoritative.
                capped = True
                break
            lifetime = post_interval_for_tier(premium)
            post_row = (
                await asession.execute(
                    text(COPY_POST_SQL.format(lifetime=lifetime)),
                    {
                        "occurrence_at": occurrence_at,
                        "priority": premium,
                        "source_id": source_id,
                        "sid": int(sid),
                    },
                )
            ).first()
            if post_row is None:
                finished = True
                break
            post_id = int(post_row[0])
            claimed = (
                await asession.execute(
                    text(
                        """
                        INSERT INTO skillkind_recurring_help_occurrence
                            (schedule_id, generated_post_id, occurrence_at)
                        VALUES (:schedule_id, :post_id, :occurrence_at)
                        ON CONFLICT ON CONSTRAINT
                            uq_recurring_occurrence_schedule_time
                        DO NOTHING
                        RETURNING id
                        """
                    ),
                    {
                        "schedule_id": schedule_id,
                        "post_id": post_id,
                        "occurrence_at": occurrence_at,
                    },
                )
            ).first()
            if claimed is None:
                # Another pass already generated this exact occurrence.
                await asession.execute(
                    text("DELETE FROM skillkind_help_post WHERE id = :pid"),
                    {"pid": post_id},
                )
            else:
                from app.field_requests import notify_field_helpers

                await notify_field_helpers(asession, post_id)
                created += 1
                count += 1
            occurrence_at = next_occurrence(
                occurrence_at, cadence, interval, tz_name
            )
            if end_date is not None and (
                local_date(occurrence_at, tz_name) > end_date
            ):
                finished = True
                break

        if finished:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_recurring_help_schedule
                    SET status = 'completed',
                        next_occurrence_at = NULL,
                        occurrence_count = :count,
                        last_occurrence_at = COALESCE(
                            :last_at, last_occurrence_at),
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = :schedule_id
                    """
                ),
                {
                    "schedule_id": schedule_id,
                    "count": count,
                    "last_at": None,
                },
            )
        else:
            await asession.execute(
                text(
                    """
                    UPDATE skillkind_recurring_help_schedule
                    SET next_occurrence_at = :next_at,
                        occurrence_count = :count,
                        last_occurrence_at = CASE
                            WHEN :count > occurrence_count THEN now()
                            ELSE last_occurrence_at END,
                        updated_at = now()
                    WHERE id = :schedule_id
                    """
                ),
                {
                    "schedule_id": schedule_id,
                    "next_at": occurrence_at,
                    "count": count,
                },
            )
        if capped or created >= MAX_CATCH_UP_POSTS:
            break

    await asession.commit()
    return created
