"""Browser geolocation as a tiny Reflex custom component.

No external geolocation service is involved: the exact coordinates come from the
visitor's own browser (`navigator.geolocation`) and are handed straight to a
server event. Browsers only expose this API over HTTPS (or localhost) and only
after the person grants permission, so both failure paths report a readable
message instead of failing silently.
"""

import reflex as rx


def _position_spec(
    latitude: rx.Var[float], longitude: rx.Var[float], accuracy: rx.Var[float]
) -> tuple[rx.Var[float], rx.Var[float], rx.Var[float]]:
    return (latitude, longitude, accuracy)


def _error_spec(message: rx.Var[str]) -> tuple[rx.Var[str]]:
    return (message,)


class GeolocationRequest(rx.Fragment):
    """Invisible helper: each new `request_token` asks for one exact fix."""

    request_token: rx.Var[int] = 0

    on_position: rx.EventHandler[_position_spec]
    on_error: rx.EventHandler[_error_spec]

    def add_imports(self):
        return {"react": [rx.ImportVar(tag="useEffect")]}

    def add_hooks(self) -> list[str]:
        token = str(self.request_token)
        on_position = str(rx.Var.create(self.event_triggers["on_position"]))
        on_error = str(rx.Var.create(self.event_triggers["on_error"]))
        return [
            f"""
            useEffect(() => {{
                const token = {token};
                if (!token) {{
                    return;
                }}
                const reportPosition = {on_position};
                const reportError = {on_error};
                if (
                    typeof navigator === "undefined" ||
                    !navigator.geolocation
                ) {{
                    reportError(
                        "This browser cannot share a location. Most browsers " +
                        "only allow it over a secure https:// address."
                    );
                    return;
                }}
                let cancelled = false;
                navigator.geolocation.getCurrentPosition(
                    (position) => {{
                        if (cancelled) {{ return; }}
                        reportPosition(
                            position.coords.latitude,
                            position.coords.longitude,
                            position.coords.accuracy || 0
                        );
                    }},
                    (error) => {{
                        if (cancelled) {{ return; }}
                        let message =
                            "We could not read your location. Please try again.";
                        if (error && error.code === 1) {{
                            message =
                                "Location permission was declined. Allow " +
                                "location for this site in your browser " +
                                "settings, then try again.";
                        }} else if (error && error.code === 2) {{
                            message =
                                "Your device could not work out a position " +
                                "right now. Move somewhere with a clearer " +
                                "signal and try again.";
                        }} else if (error && error.code === 3) {{
                            message =
                                "Finding your location timed out. Please try " +
                                "again.";
                        }}
                        reportError(message);
                    }},
                    {{
                        enableHighAccuracy: true,
                        timeout: 15000,
                        maximumAge: 0,
                    }}
                );
                return () => {{ cancelled = true; }};
            }}, [{token}]);
            """
        ]


geolocation_request = GeolocationRequest.create
