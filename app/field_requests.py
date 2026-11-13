"""Private request matching and notification preference persistence."""

import reflex as rx

import json
import logging
import math
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import LEGACY_CATEGORY_ALIASES, TASK_CATEGORIES
from app.skill_categories import canonical_category

FIELD_KIND = "requests_in_my_field"
FIELD_SWITCH = "notify_requests_in_my_field"
FIELD_RADIUS = "requests_in_my_field_radius_km"


def permission_values(raw: object) -> dict:
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError) as e:
        logging.exception(f"Error: {e}")
        values = {}
    return dict(values) if isinstance(values, dict) else {}


def validate_field_radius(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Choose a whole-number radius from 1 to 1000 km.")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as e:
        raise ValueError(
            "Choose a whole-number radius from 1 to 1000 km."
        ) from e
    if (
        not math.isfinite(number)
        or not number.is_integer()
        or not 1 <= number <= 1000
    ):
        raise ValueError("Choose a whole-number radius from 1 to 1000 km.")
    return int(number)


def field_preferences(raw: object) -> tuple[bool, int]:
    values = permission_values(raw)
    enabled = values.get(FIELD_SWITCH)
    try:
        radius = validate_field_radius(values.get(FIELD_RADIUS, 20))
    except ValueError:
        radius = 20
    return (enabled if type(enabled) is bool else True), radius


async def persist_preference(
    session: AsyncSession, sid: int, key: str, value: bool | int
) -> dict:
    from app.models import ONBOARDING_LAST_STEP, GUIDED_TOUR_LAST_STEP

    await session.execute(
        text("""
        INSERT INTO skillkind_onboarding_progress
            (subscriber_id, current_step, completed_steps, answers_json,
             permissions_json, completed_at, tour_current_step, tour_completed_at, updated_at)
        VALUES (:sid, :last, :steps, '{}', '{}', now(), :tour, now(), now())
        ON CONFLICT (subscriber_id) DO NOTHING
    """),
        {
            "sid": sid,
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
        WHERE subscriber_id=:sid FOR UPDATE
    """),
            {"sid": sid},
        )
    ).scalar_one()
    permissions = permission_values(raw)
    if key == FIELD_RADIUS:
        permissions[key] = validate_field_radius(value)
    else:
        previous = permissions.get(key)
        permissions[key] = not (previous if type(previous) is bool else True)
    await session.execute(
        text("""
        UPDATE skillkind_onboarding_progress SET permissions_json=:permissions, updated_at=now()
        WHERE subscriber_id=:sid
    """),
        {"sid": sid, "permissions": json.dumps(permissions)},
    )
    return permissions


def _category_sql(token: str) -> str:
    aliases = {
        key.strip().lower().replace(" ", "_"): canonical_category(key)
        for key in [*TASK_CATEGORIES, *LEGACY_CATEGORY_ALIASES]
    }
    cases = " ".join(
        f"WHEN '{key}' THEN '{value}'"
        for key, value in aliases.items()
        if value
    )
    return f"CASE LOWER(REPLACE(TRIM({token}), ' ', '_')) {cases} ELSE '' END"


HELPER_MATCH_SQL = f"""
    FROM skillkind_help_post p
    JOIN skillkind_subscriber author ON author.id=p.author_id AND author.is_active=TRUE
    JOIN skillkind_subscriber helper ON helper.id<>p.author_id
        AND helper.is_active=TRUE AND helper.is_verified=TRUE
        AND helper.help_mode IN ('offer_help', 'both')
    JOIN skillkind_profile hp ON hp.subscriber_id=helper.id
    LEFT JOIN skillkind_onboarding_progress op ON op.subscriber_id=helper.id
    WHERE p.status='open' AND (p.expires_at IS NULL OR p.expires_at>now())
      AND NOT EXISTS (SELECT 1 FROM skillkind_completed_task ct WHERE ct.post_id=p.id)
      AND (SELECT COUNT(*) FROM skillkind_job_application a
           WHERE a.post_id=p.id AND a.status='accepted') < GREATEST(COALESCE(p.helpers_needed,1),1)
      AND p.latitude BETWEEN -90 AND 90 AND p.longitude BETWEEN -180 AND 180
      AND hp.latitude BETWEEN -90 AND 90 AND hp.longitude BETWEEN -180 AND 180
      AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
          WHERE (b.blocker_id=helper.id AND b.blocked_id=p.author_id)
             OR (b.blocked_id=helper.id AND b.blocker_id=p.author_id))
      AND EXISTS (
          SELECT 1 FROM unnest(string_to_array(COALESCE(hp.preferred_categories,''), ',')) h(token)
          CROSS JOIN unnest(string_to_array(
              CASE WHEN TRIM(COALESCE(p.category_tags,''))<>'' THEN p.category_tags
                   ELSE p.category END, ',')) c(token)
          WHERE {_category_sql("h.token")}<>''
            AND {_category_sql("h.token")}={_category_sql("c.token")}
      )
"""

DISTANCE_SQL = """6371.0088 * acos(LEAST(1.0, GREATEST(-1.0,
    sin(radians(CAST(hp.latitude AS double precision))) * sin(radians(CAST(p.latitude AS double precision)))
    + cos(radians(CAST(hp.latitude AS double precision))) * cos(radians(CAST(p.latitude AS double precision)))
    * cos(radians(CAST(hp.longitude AS double precision)-CAST(p.longitude AS double precision))))))"""


async def notify_field_helpers(session: AsyncSession, post_id: int) -> None:
    # Serialize deduplication on the source post, not on every recipient.
    await session.execute(
        text("SELECT id FROM skillkind_help_post WHERE id=:pid FOR UPDATE"),
        {"pid": post_id},
    )
    cursor = 0
    while True:
        rows = (
            await session.execute(
                text(f"""
            SELECT helper.id, op.permissions_json, {DISTANCE_SQL} AS distance
            {HELPER_MATCH_SQL} AND p.id=:pid AND helper.id>:cursor
              AND ({DISTANCE_SQL})<=1000
              AND NOT EXISTS (SELECT 1 FROM skillkind_member_notification n
                  WHERE n.recipient_id=helper.id AND n.help_post_id=p.id AND n.kind=:kind)
            ORDER BY helper.id LIMIT 500
        """),
                {"pid": post_id, "cursor": cursor, "kind": FIELD_KIND},
            )
        ).all()
        if not rows:
            break
        recipients = []
        for row in rows:
            enabled, radius = field_preferences(row[1])
            if enabled and float(row[2]) <= radius:
                recipients.append(
                    {
                        "recipient": int(row[0]),
                        "pid": post_id,
                        "kind": FIELD_KIND,
                    }
                )
        if recipients:
            await session.execute(
                text("""
                INSERT INTO skillkind_member_notification
                    (recipient_id, kind, title, body, actor_id, help_post_id, target_route)
                SELECT :recipient, :kind, 'New request in your field', '', p.author_id, p.id, 'discover'
                FROM skillkind_help_post p WHERE p.id=:pid
                  AND NOT EXISTS (SELECT 1 FROM skillkind_member_notification n
                      WHERE n.recipient_id=:recipient AND n.help_post_id=:pid AND n.kind=:kind)
            """),
                recipients,
            )
        cursor = int(rows[-1][0])


async def owned_field_matches(
    session: AsyncSession, sid: int
) -> list[tuple[int, int]]:
    raw = (
        await session.execute(
            text(
                "SELECT permissions_json FROM skillkind_onboarding_progress WHERE subscriber_id=:sid"
            ),
            {"sid": sid},
        )
    ).scalar_one_or_none()
    enabled, radius = field_preferences(raw)
    if not enabled:
        return []
    rows = (
        await session.execute(
            text(f"""
        SELECT p.id {HELPER_MATCH_SQL}
          AND helper.id=:sid AND ({DISTANCE_SQL})<=:radius
          AND EXISTS (SELECT 1 FROM skillkind_member_notification source
              WHERE source.recipient_id=:sid AND source.help_post_id=p.id
                AND source.kind=:kind AND source.is_read=FALSE)
        ORDER BY p.created_at DESC, p.id DESC LIMIT 100
    """),
            {"sid": sid, "radius": radius, "kind": FIELD_KIND},
        )
    ).all()
    post_ids = [int(row[0]) for row in rows]
    if not post_ids:
        return []
    notices = (
        await session.execute(
            text("""
        SELECT id, help_post_id FROM skillkind_member_notification
        WHERE recipient_id=:sid AND kind=:kind AND is_read=FALSE
          AND help_post_id=ANY(:posts) ORDER BY id DESC FOR UPDATE
    """),
            {"sid": sid, "kind": FIELD_KIND, "posts": post_ids},
        )
    ).all()
    return [(int(row[0]), int(row[1])) for row in notices]
