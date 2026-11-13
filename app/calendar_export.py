"""Standards-compliant iCalendar (.ics) building for Go and Help tasks.

The travellers' pocket calendar: one VEVENT per agreed job, written in UTC with
CRLF line endings so phones, laptops and webmail all read it the same way. This
module is pure text formatting — it never touches the database, never receives a
client-supplied identifier and never carries exact coordinates.
"""

import datetime
from typing import TypedDict

CALENDAR_FILENAME = "go-and-help-tasks.ics"
CALENDAR_PRODID = "-//Go and Help//Task calendar//EN"
DEFAULT_DURATION_MINUTES = 60
MAX_DURATION_MINUTES = 24 * 60
UID_DOMAIN = "goandhelp.app"


class CalendarEvent(TypedDict):
    """One agreed appointment, already resolved server-side."""

    uid: str
    starts_at: datetime.datetime
    duration_minutes: int
    title: str
    location: str
    description: str
    url: str


def event_uid(post_id: int, application_id: int) -> str:
    """Stable UID: the same job always exports as the same calendar entry."""
    return f"task-{int(post_id)}-offer-{int(application_id)}@{UID_DOMAIN}"


def _as_utc(moment: datetime.datetime) -> datetime.datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=datetime.UTC)
    return moment.astimezone(datetime.UTC)


def format_utc(moment: datetime.datetime) -> str:
    return _as_utc(moment).strftime("%Y%m%dT%H%M%SZ")


def escape_text(value: str) -> str:
    """Escape per RFC 5545: backslash, semicolon, comma and newlines."""
    cleaned = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("\\", "\\\\")
    cleaned = cleaned.replace(";", "\\;").replace(",", "\\,")
    return cleaned.replace("\n", "\\n")


def _fold(line: str) -> list[str]:
    """Fold a content line to 75 octets, continuing with a single space."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]
    pieces: list[str] = []
    chunk = bytearray()
    limit = 73
    for character in line:
        raw = character.encode("utf-8")
        if len(chunk) + len(raw) > limit:
            pieces.append(chunk.decode("utf-8"))
            chunk = bytearray()
            limit = 72
        chunk.extend(raw)
    if chunk:
        pieces.append(chunk.decode("utf-8"))
    return [pieces[0]] + [f" {piece}" for piece in pieces[1:]]


def _safe_duration(minutes: int) -> int:
    try:
        value = int(minutes)
    except (TypeError, ValueError):
        value = DEFAULT_DURATION_MINUTES
    if value <= 0:
        value = DEFAULT_DURATION_MINUTES
    return min(value, MAX_DURATION_MINUTES)


def build_ics(
    events: list[CalendarEvent], now: datetime.datetime | None = None
) -> str:
    """Return a complete UTF-8 iCalendar document with CRLF line endings."""
    stamp = format_utc(now or datetime.datetime.now(datetime.UTC))
    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{CALENDAR_PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_text('Go and Help tasks')}",
        "X-WR-TIMEZONE:UTC",
    ]
    for event in events:
        starts_at = _as_utc(event["starts_at"])
        ends_at = starts_at + datetime.timedelta(
            minutes=_safe_duration(event["duration_minutes"])
        )
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event['uid']}",
                f"DTSTAMP:{stamp}",
                f"DTSTART:{format_utc(starts_at)}",
                f"DTEND:{format_utc(ends_at)}",
                f"SUMMARY:{escape_text(event['title'])}",
            ]
        )
        if event.get("location"):
            lines.append(f"LOCATION:{escape_text(event['location'])}")
        if event.get("description"):
            lines.append(f"DESCRIPTION:{escape_text(event['description'])}")
        if event.get("url"):
            lines.append(f"URL:{escape_text(event['url'])}")
        lines.extend(
            [
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    folded: list[str] = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"
