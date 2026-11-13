"""Reusable exact-point picker: map click or browser current location.

The picker only ever holds ONE private exact point at a time, identified by the
`open_key` of the panel that opened it. Nothing here is published: callers read
`latitude` / `longitude` server-side and decide what (if anything) reaches a
public map, always through `app/location_privacy.py`.
"""

import reflex as rx

from app.components.openfreemap import MapMarker


class MapPickerState(rx.State):
    """One privately held latitude/longitude chosen by map pin or browser."""

    # Which picker panel is expanded ("" = none). Opening a different panel
    # clears the previous point so two forms can never share a stale pin.
    open_key: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    has_point: bool = False

    geo_token: int = 0
    geo_busy: bool = False
    status: str = ""
    error: str = ""

    center: list[float] = [10.0, 46.5]
    zoom: float = 4.0

    @rx.var
    def point_label(self) -> str:
        if not self.has_point:
            return "No pin dropped yet"
        return f"{self.latitude:.5f}, {self.longitude:.5f}"

    @rx.var
    def markers(self) -> list[MapMarker]:
        if not self.has_point:
            return []
        return [
            {
                "id": "picked-point",
                "lng": self.longitude,
                "lat": self.latitude,
                "label": "Your pin",
                "kind": "selected",
                "selected": True,
                "draggable": True,
                "icon": "hand-helping",
                "color": "#e08b12",
                "image_url": "",
            }
        ]

    def _reset_point(self) -> None:
        self.latitude = 0.0
        self.longitude = 0.0
        self.has_point = False
        self.status = ""
        self.error = ""
        self.geo_busy = False

    def _open_with_point(
        self,
        key: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        """Helper for other states: open a panel seeded with a saved point.

        Unlike `open_picker`, an existing pin for the SAME key is preserved and
        a supplied latitude/longitude is adopted, so opening the Profile
        location card never silently clears the member's saved point.
        """
        if self.open_key != key:
            self._reset_point()
        self.open_key = key
        if latitude is None or longitude is None:
            return
        self.latitude = max(-90.0, min(90.0, float(latitude)))
        self.longitude = max(-180.0, min(180.0, float(longitude)))
        self.has_point = True
        self.error = ""
        self.center = [self.longitude, self.latitude]
        self.zoom = max(self.zoom, 11.0)
        self.status = (
            "Showing your saved point. Drag the pin or tap the map, or use your "
            "current location."
        )

    def _close_key(self, key: str) -> None:
        """Collapse the panel only if `key` is the one currently open."""
        if self.open_key == key:
            self.open_key = ""

    @rx.event
    def open_picker(self, key: str):
        if self.open_key != key:
            self._reset_point()
        self.open_key = key

    @rx.event
    def close_picker(self):
        self.open_key = ""

    @rx.event
    def toggle_picker(self, key: str):
        if self.open_key == key:
            self.open_key = ""
            return
        if self.open_key != key:
            self._reset_point()
        self.open_key = key

    def _onboarding_pin_event(self):
        if self.open_key == "onboarding-first-request":
            from app.states.onboarding_state import OnboardingState

            return OnboardingState.capture_request_pin

    @rx.event
    def clear_point(self):
        self._reset_point()
        return self._onboarding_pin_event()

    @rx.event
    def set_point(self, lng: float, lat: float):
        """A click on the map: store the private exact point and mark it."""
        try:
            longitude = float(lng)
            latitude = float(lat)
        except (TypeError, ValueError):
            self.error = "That map point could not be read — tap the map again."
            return
        self.latitude = max(-90.0, min(90.0, latitude))
        self.longitude = max(-180.0, min(180.0, longitude))
        self.has_point = True
        self.error = ""
        self.geo_busy = False
        self.status = "Pin placed. Drag the pin or tap the map to adjust it."
        return self._onboarding_pin_event()

    @rx.event
    def use_my_location(self):
        """Browser current location as a one-tap pin shortcut."""
        self.error = ""
        self.status = "Asking your browser for your current position…"
        self.geo_busy = True
        self.geo_token = self.geo_token + 1

    @rx.event
    def position_found(
        self, latitude: float, longitude: float, accuracy: float
    ):
        self.latitude = max(-90.0, min(90.0, float(latitude)))
        self.longitude = max(-180.0, min(180.0, float(longitude)))
        self.has_point = True
        self.geo_busy = False
        self.error = ""
        metres = max(0, round(float(accuracy or 0)))
        self.status = (
            f"Pin set from your browser (accuracy about {metres} m). Drag the "
            "pin or tap the map to fine-tune it."
        )
        return self._onboarding_pin_event()

    @rx.event
    def position_failed(self, message: str):
        self.geo_busy = False
        self.status = ""
        self.error = message or (
            "We could not read your location. Tap the map to drop a pin "
            "instead."
        )
