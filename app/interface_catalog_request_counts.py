from collections import Counter
import re

from app.interface_catalog_request_count_headings import (
    REQUEST_COUNT_HEADING_ROWS,
)
from app.interface_catalog_request_count_subtitles import (
    REQUEST_COUNT_SUBTITLE_ROWS,
)
from app.interface_catalog_request_count_totals import (
    REQUEST_COUNT_TOTAL_ROWS,
)
from app.models import LANGUAGE_OPTIONS


REQUEST_COUNT_KEYS: tuple[str, ...] = (
    "{count} upcoming jobs",
    "{count} Confirmed job",
    "{count} Confirmed jobs",
    "{count} Confirmed helper",
    "{count} Confirmed helpers",
    "{count} Event",
    "{count} Events",
    "{count} Hosted event",
    "{count} Hosted events",
    "{count} Help request",
    "{count} Help requests",
    "{count} Search alerts",
    "{count} search alert",
    "{count} search alerts",
    "{count} Bookmarked help request",
    "{count} Bookmarked help requests",
    "{count} Offer to help you",
    "{count} Offers to help you",
    "{count} Request for your help",
    "{count} Requests for your help",
    "Get ready to help others",
    "People ready to help you",
    "Requests you have already posted",
    "Join many helping hands",
    "Manage helpers for your event",
    "Get notified with matching help requests",
    "Help requests you bookmarked in map or list view.",
    "{count} help given",
    "{count} help received",
    "Helped {count} time",
    "Helped {count} times",
    "Received help {count} time",
    "Received help {count} times",
    "{count} Requested",
    "{count} Open",
    "{count} Upcoming",
    "{count} people required",
    "{rating} out of 5 stars; {count} reviews",
    "Offered {date}",
)


REQUEST_COUNT_HEADING_KEYS: tuple[str, ...] = REQUEST_COUNT_KEYS[:20]
REQUEST_COUNT_SUBTITLE_KEYS: tuple[str, ...] = REQUEST_COUNT_KEYS[20:27]
REQUEST_COUNT_TOTAL_KEYS: tuple[str, ...] = REQUEST_COUNT_KEYS[27:]

_SECTIONS: tuple[tuple[tuple[str, ...], dict[str, str]], ...] = (
    (REQUEST_COUNT_HEADING_KEYS, REQUEST_COUNT_HEADING_ROWS),
    (REQUEST_COUNT_SUBTITLE_KEYS, REQUEST_COUNT_SUBTITLE_ROWS),
    (REQUEST_COUNT_TOTAL_KEYS, REQUEST_COUNT_TOTAL_ROWS),
)

_SLOT = re.compile(r"\{([a-z]+)\}")


def _native_row(code: str) -> dict[str, str]:
    row: dict[str, str] = {}
    for keys, rows in _SECTIONS:
        row.update(zip(keys, rows[code].split("|"), strict=True))
    for source, value in row.items():
        if not value.strip() or value.casefold() == source.casefold():
            raise ValueError(
                f"Request count entry is not native: {code} {source}"
            )
        if Counter(_SLOT.findall(source)) != Counter(_SLOT.findall(value)):
            raise ValueError(f"Request count slots differ: {code} {source}")
    return row


_LOCALES: tuple[str, ...] = tuple(
    code for code, _label in LANGUAGE_OPTIONS if code != "en"
)
for _keys, _rows in _SECTIONS:
    if set(_rows) != set(_LOCALES):
        raise ValueError("Request count locale rows are incomplete")

REQUEST_COUNT_CATALOGS: dict[str, dict[str, str]] = {
    code: _native_row(code) for code in _LOCALES
}
