"""Keyless Google Maps directions links, built server-side only.

Coordinates never travel to the browser on their own: the only thing a page
ever receives is a finished universal Maps URL for a destination the signed-in
participant is already authorized to know.

The official universal URL is used, with `origin` deliberately omitted so the
device can supply the traveller's own position:

    https://www.google.com/maps/dir/?api=1&destination=<lat,lng>&dir_action=navigate

No API key and no SDK are involved.
"""

from urllib.parse import quote

DIRECTIONS_BASE = "https://www.google.com/maps/dir/?api=1"


def _usable(latitude, longitude) -> tuple[float, float] | None:
    """Bounds-checked (lat, lng) pair, or None when unusable."""
    if latitude is None or longitude is None:
        return None
    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return None
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        return None
    if lat == 0.0 and lng == 0.0:
        return None
    return lat, lng


def directions_url(latitude, longitude) -> str:
    """Universal navigation URL for one destination point, or ''."""
    point = _usable(latitude, longitude)
    if point is None:
        return ""
    destination = quote(f"{point[0]:.6f},{point[1]:.6f}", safe="")
    return f"{DIRECTIONS_BASE}&destination={destination}&dir_action=navigate"


def job_directions_url(
    location_mode: str,
    accepted_location_name: str,
    accepted_latitude,
    accepted_longitude,
    post_latitude,
    post_longitude,
) -> str:
    """Directions for a confirmed job, from the accepted exact point only.

    Public help-post coordinates are never usable for navigation — including
    legacy `place` rows — because they are only ever published approximately.
    Directions exist solely once the helpee has shared the exact meeting
    point with the confirmed helper; otherwise the URL is omitted.
    `location_mode`, `post_latitude` and `post_longitude` are accepted for
    call-site compatibility and deliberately ignored.
    """
    del location_mode, post_latitude, post_longitude
    if not str(accepted_location_name or "").strip():
        return ""
    return directions_url(accepted_latitude, accepted_longitude)
