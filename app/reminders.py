"""Email reminders for agreed Go and Help tasks, 24 hours and 1 hour before.

One idempotent sweep does all the work:

1. Find accepted, still-future tasks whose 24-hour or 1-hour mark has just
   passed (within a small tolerance window, so a restart never fires a reminder
   from days ago).
2. Resolve both participants — poster and confirmed helper — and keep only
   active, non-banned members with a real email address.
3. Claim exactly one ``skillkind_task_reminder_delivery`` row per
   (help post, recipient, offset). The unique constraint plus ``ON CONFLICT DO
   NOTHING`` is the duplicate-send guard, and the claim is committed *before*
   the email is attempted, so a crash mid-send never causes a second email.
4. Send the branded reminder through the existing Resend helper and record the
   outcome: provider id and ``sent_at``, or a short, safe error note.

Nothing here logs email content, credentials, recipient addresses or exact
coordinates. The email itself carries only the task title, the scheduled time,
the general meeting place (location name / city), the other participant's
display name and a link back to the Inbox.
"""

import asyncio
import contextlib
import datetime
import logging

import reflex as rx
from sqlalchemy import text

from app.verification import public_base_url, send_branded_email

# Exactly two reminders per participant, per task.
REMINDER_OFFSETS: tuple[int, ...] = (1440, 60)
# How late a sweep may still send a reminder it missed (minutes).
TOLERANCE_MINUTES = 25
# Sweep cadence.
SWEEP_INTERVAL_SECONDS = 600.0
STARTUP_DELAY_SECONDS = 20.0
MAX_ROWS_PER_OFFSET = 200
ERROR_NOTE_MAX = 200


def _lead_label(offset_minutes: int) -> str:
    return "24 hours" if offset_minutes >= 1440 else "1 hour"


def _headline(offset_minutes: int, title: str) -> str:
    if offset_minutes >= 1440:
        return f"Tomorrow: {title}"
    return f"In one hour: {title}"


def _reminder_html(
    display_name: str,
    other_name: str,
    title: str,
    when_label: str,
    place: str,
    lead_label: str,
    inbox_link: str,
) -> str:
    greeting = (display_name or "").strip() or "traveller"
    place_row = ""
    if place:
        place_row = (
            '<p style="margin:8px 0 0 0;font-size:15px;line-height:1.6;'
            'color:#4b5563;"><strong>Where</strong> · ' + place + "</p>"
        )
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#ffffff;font-family:Inter,Helvetica,Arial,sans-serif;color:#111827;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #f7d9a0;border-radius:22px;">
      <tr>
        <td style="padding:28px 28px 8px 28px;">
          <p style="margin:0;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;font-weight:700;color:#e08b12;">Go and Help · reminder</p>
          <h1 style="margin:10px 0 0 0;font-size:24px;line-height:1.25;font-weight:700;color:#111827;">
            {_escape_html(title)} is {lead_label} away, {_escape_html(greeting)}
          </h1>
          <p style="margin:14px 0 0 0;font-size:15px;line-height:1.6;color:#4b5563;">
            <strong>When</strong> · {_escape_html(when_label)}
          </p>
          {place_row}
          <p style="margin:8px 0 0 0;font-size:15px;line-height:1.6;color:#4b5563;">
            <strong>With</strong> · {_escape_html(other_name)}
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:22px 28px 6px 28px;">
          <a href="{inbox_link}"
             style="display:inline-block;background:#e08b12;border:1px solid #e08b12;border-radius:999px;padding:14px 26px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;">
            Open your Inbox
          </a>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 28px 28px 28px;">
          <p style="margin:0;font-size:13px;line-height:1.6;color:#4b5563;">
            Confirm the meeting point in the app before you set off, meet in a
            public place, and tell someone where you are going.
          </p>
          <p style="margin:18px 0 0 0;font-size:12px;line-height:1.6;color:#4b5563;">
            — Go and Help, community in your hands
          </p>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _escape_html(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _reminder_text(
    display_name: str,
    other_name: str,
    title: str,
    when_label: str,
    place: str,
    lead_label: str,
    inbox_link: str,
) -> str:
    greeting = (display_name or "").strip() or "traveller"
    place_line = f"Where: {place}\n" if place else ""
    return (
        f"Hi {greeting},\n\n"
        f"{title} is {lead_label} away.\n\n"
        f"When: {when_label}\n"
        f"{place_line}"
        f"With: {other_name}\n\n"
        f"Open your Inbox: {inbox_link}\n\n"
        "Confirm the meeting point in the app before you set off, meet in a "
        "public place, and tell someone where you are going.\n\n"
        "— Go and Help, community in your hands"
    )


def _place_label(location_name: str, city: str) -> str:
    parts = [part for part in (location_name.strip(), city.strip()) if part]
    return ", ".join(parts)


def _when_label(starts_at: datetime.datetime) -> str:
    moment = starts_at
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=datetime.UTC)
    return moment.astimezone(datetime.UTC).strftime("%A, %b %d %Y · %H:%M UTC")


DUE_RECIPIENTS_SQL = """
WITH job AS (
    SELECT
        p.id AS post_id,
        p.title AS title,
        COALESCE(p.location_name, '') AS location_name,
        COALESCE(p.city, '') AS city,
        COALESCE(p.duration_minutes, 60) AS duration_minutes,
        COALESCE(a.proposed_time, p.scheduled_for) AS starts_at,
        p.author_id AS author_id,
        a.helper_id AS helper_id,
        poster.display_name AS poster_name,
        helper.display_name AS helper_name
    FROM skillkind_help_post p
    JOIN skillkind_job_application a ON a.post_id = p.id
    JOIN skillkind_subscriber poster ON poster.id = p.author_id
    JOIN skillkind_subscriber helper ON helper.id = a.helper_id
    WHERE a.status = 'accepted'
      AND p.status IN ('open', 'matched')
      AND COALESCE(a.proposed_time, p.scheduled_for) IS NOT NULL
),
participant AS (
    SELECT post_id, title, location_name, city, duration_minutes, starts_at,
           author_id AS recipient_id, helper_name AS other_name
    FROM job
    UNION ALL
    SELECT post_id, title, location_name, city, duration_minutes, starts_at,
           helper_id AS recipient_id, poster_name AS other_name
    FROM job
)
SELECT r.post_id, r.title, r.location_name, r.city, r.duration_minutes,
       r.starts_at, r.recipient_id, s.email, s.display_name, r.other_name
FROM participant r
JOIN skillkind_subscriber s ON s.id = r.recipient_id
LEFT JOIN skillkind_task_reminder_delivery d
       ON d.help_post_id = r.post_id
      AND d.recipient_id = r.recipient_id
      AND d.offset_minutes = :offset
WHERE d.id IS NULL
  AND COALESCE(s.is_active, TRUE) = TRUE
  AND COALESCE(s.moderation_status, 'clear') <> 'banned'
  AND COALESCE(s.email, '') <> ''
  AND r.starts_at > now()
  AND (r.starts_at - (INTERVAL '1 minute' * :offset))
      BETWEEN now() - (INTERVAL '1 minute' * :tolerance) AND now()
ORDER BY r.starts_at ASC
LIMIT :row_limit
"""

CLAIM_SQL = """
INSERT INTO skillkind_task_reminder_delivery
    (help_post_id, recipient_id, offset_minutes, email, task_starts_at,
     scheduled_send_at, attempts, last_attempt_at)
VALUES
    (:post_id, :recipient_id, :offset, :email, :starts_at,
     :send_at, 1, now())
ON CONFLICT (help_post_id, recipient_id, offset_minutes) DO NOTHING
RETURNING id
"""


async def _claim_reminder(
    asession,
    post_id: int,
    recipient_id: int,
    offset: int,
    email: str,
    starts_at: datetime.datetime,
    send_at: datetime.datetime,
) -> int:
    """Insert the guard row; 0 means another sweep already owns this reminder."""
    row = (
        await asession.execute(
            text(CLAIM_SQL),
            {
                "post_id": post_id,
                "recipient_id": recipient_id,
                "offset": offset,
                "email": email[:255],
                "starts_at": starts_at,
                "send_at": send_at,
            },
        )
    ).first()
    return int(row[0]) if row is not None else 0


async def sweep_task_reminders(
    tolerance_minutes: int = TOLERANCE_MINUTES,
) -> dict[str, int]:
    """Send every due 24h / 1h task reminder exactly once.

    Independently callable and safe to run concurrently or repeatedly. Returns a
    small counter summary: ``claimed``, ``sent``, ``failed``, ``skipped``.
    """
    summary: dict[str, int] = {
        "claimed": 0,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
    }
    base_url = public_base_url()
    inbox_link = f"{base_url}/?screen=inbox"
    for offset in REMINDER_OFFSETS:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(DUE_RECIPIENTS_SQL),
                    {
                        "offset": offset,
                        "tolerance": max(1, int(tolerance_minutes)),
                        "row_limit": MAX_ROWS_PER_OFFSET,
                    },
                )
            ).all()
        for row in rows:
            post_id = int(row[0])
            title = str(row[1] or "Your Go and Help task")
            place = _place_label(row[2] or "", row[3] or "")
            starts_at = row[5]
            recipient_id = int(row[6])
            email = str(row[7] or "")
            recipient_name = str(row[8] or "")
            other_name = str(row[9] or "A Go and Help neighbour")
            if not email or starts_at is None:
                summary["skipped"] += 1
                continue
            send_at = starts_at - datetime.timedelta(minutes=offset)
            claim_id = 0
            async with rx.asession() as asession:
                claim_id = await _claim_reminder(
                    asession,
                    post_id,
                    recipient_id,
                    offset,
                    email,
                    starts_at,
                    send_at,
                )
                await asession.commit()
            if claim_id <= 0:
                summary["skipped"] += 1
                continue
            summary["claimed"] += 1
            lead_label = _lead_label(offset)
            when_label = _when_label(starts_at)
            ok, provider_id, note = await send_branded_email(
                email,
                _headline(offset, title),
                _reminder_html(
                    recipient_name,
                    other_name,
                    title,
                    when_label,
                    place,
                    lead_label,
                    inbox_link,
                ),
                _reminder_text(
                    recipient_name,
                    other_name,
                    title,
                    when_label,
                    place,
                    lead_label,
                    inbox_link,
                ),
                "task_reminder",
            )
            async with rx.asession() as asession:
                if ok:
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_task_reminder_delivery
                            SET sent_at = now(),
                                provider_message_id = :provider_id,
                                last_error = '',
                                last_error_at = NULL
                            WHERE id = :row_id
                            """
                        ),
                        {
                            "provider_id": (provider_id or "")[:120],
                            "row_id": claim_id,
                        },
                    )
                    summary["sent"] += 1
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE skillkind_task_reminder_delivery
                            SET last_error = :note,
                                last_error_at = now()
                            WHERE id = :row_id
                            """
                        ),
                        {
                            "note": (note or "Delivery failed.")[
                                :ERROR_NOTE_MAX
                            ],
                            "row_id": claim_id,
                        },
                    )
                    summary["failed"] += 1
                await asession.commit()
        logging.info(
            f"Task reminder sweep: offset={offset} candidates={len(rows)}"
        )
    return summary


async def reminder_sweep_lifespan(
    initial_delay: float = STARTUP_DELAY_SECONDS,
    interval_seconds: float = SWEEP_INTERVAL_SECONDS,
) -> None:
    """Lifespan task: sweep shortly after startup, then on a fixed interval.

    Never blocks startup (it sleeps first) and survives individual sweep
    failures. Shutdown cancellation during the startup sleep or recurring loop
    returns cleanly without escaping into lifespan cleanup logs.
    """
    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.sleep(initial_delay)
        while True:
            try:
                summary = await sweep_task_reminders()
                logging.info(f"Task reminder sweep summary: {summary}")
            except Exception as e:  # noqa: BLE001
                logging.exception(f"Task reminder sweep failed: {e}")
            await asyncio.sleep(interval_seconds)
