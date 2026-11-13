"""Reusable map-pin picker panel: tap the map or use the browser location."""

import reflex as rx

from app.components.geolocation import geolocation_request
from app.components.openfreemap import OPENFREEMAP_LIBERTY, open_free_map
from app.states.map_picker_state import MapPickerState


def _point_chips(clear_label: str | rx.Var[str] = "Clear pin") -> rx.Component:
    return rx.el.div(
        rx.cond(
            MapPickerState.has_point,
            rx.el.button(
                rx.icon("x", class_name="h-3 w-3"),
                clear_label,
                type="button",
                on_click=MapPickerState.clear_point,
                class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f7d9a0] bg-white px-3 py-1.5 text-[11px] font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 flex flex-wrap items-center gap-2",
    )


def _map_options(picker_key: str) -> dict[str, str]:
    is_help_request = picker_key == "help-request"
    navigation_position = rx.cond(
        is_help_request | (picker_key == "onboarding-first-request"),
        "bottom-left",
        "top-left",
    )
    class_name = rx.cond(
        is_help_request,
        "gah-help-request-map h-64 sm:h-72 w-full [&_.maplibregl-ctrl-attrib:not([open]):not(.maplibregl-compact-show)_.maplibregl-ctrl-attrib-inner]:hidden!",
        "h-64 sm:h-72 w-full",
    )
    return {
        "navigation_position": navigation_position,
        "class_name": class_name,
    }


def map_picker(
    picker_key: str,
    heading: str | rx.Var[str],
    inline: bool = False,
    show_label: str | rx.Var[str] = "Use map pin",
    hide_label: str | rx.Var[str] = "Hide map pin",
    instructions: str
    | rx.Var[
        str
    ] = "Drag the pin or tap the map to place the exact point. It stays private: public maps only show an approximate area.",
    clear_label: str | rx.Var[str] = "Clear pin",
    finding_label: str | rx.Var[str] = "Finding you…",
    locate_label: str | rx.Var[str] = "Use my current location",
    status_text: str | rx.Var[str] = "",
    error_text: str | rx.Var[str] = "",
) -> rx.Component:
    """An optional inline editor bound to one private exact point."""
    return rx.el.div(
        rx.cond(
            inline,
            rx.fragment(),
            rx.el.button(
                rx.icon("map-pin", class_name="h-4 w-4"),
                rx.cond(
                    (MapPickerState.open_key == picker_key),
                    hide_label,
                    show_label,
                ),
                type="button",
                aria_expanded=rx.cond(
                    (MapPickerState.open_key == picker_key), "true", "false"
                ),
                aria_label=heading,
                on_click=lambda: MapPickerState.toggle_picker(picker_key),
                class_name=rx.cond(
                    (MapPickerState.open_key == picker_key),
                    "w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl bg-[#e08b12] px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08]",
                    "w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl border border-[#e08b12] bg-white px-4 py-2.5 text-sm font-bold text-[#b86e08] transition-colors hover:bg-[#fff7e8]",
                ),
            ),
        ),
        rx.cond(
            inline | (MapPickerState.open_key == picker_key),
            rx.el.div(
                geolocation_request(
                    request_token=MapPickerState.geo_token,
                    on_position=MapPickerState.position_found,
                    on_error=MapPickerState.position_failed,
                ),
                rx.cond(
                    inline,
                    rx.fragment(),
                    rx.el.div(
                        rx.el.p(
                            heading,
                            class_name="text-sm font-bold text-[#111827]",
                        ),
                        rx.el.p(
                            instructions,
                            class_name="mt-1 text-xs text-[#4b5563]",
                        ),
                    ),
                ),
                _point_chips(clear_label),
                rx.el.div(
                    open_free_map(
                        markers=MapPickerState.markers,
                        center=MapPickerState.center,
                        zoom=MapPickerState.zoom,
                        style_url=OPENFREEMAP_LIBERTY,
                        show_navigation_control=True,
                        attribution_visible=False,
                        camera_updates=False,
                        on_map_click=MapPickerState.set_point,
                        on_marker_drag=MapPickerState.set_point,
                        **_map_options(picker_key),
                    ),
                    aria_label=heading,
                    class_name=rx.cond(
                        inline,
                        "mt-3 -mx-5 sm:-mx-6 h-64 sm:h-72 w-[calc(100%+2.5rem)] sm:w-[calc(100%+3rem)] shrink-0 overflow-hidden rounded-2xl border border-[#f7d9a0]",
                        "mt-3 h-64 sm:h-72 w-full shrink-0 overflow-hidden rounded-2xl border border-[#f7d9a0]",
                    ),
                ),
                rx.el.button(
                    rx.cond(
                        MapPickerState.geo_busy,
                        rx.spinner(class_name="h-4 w-4"),
                        rx.icon("locate-fixed", class_name="h-4 w-4"),
                    ),
                    rx.cond(
                        MapPickerState.geo_busy,
                        finding_label,
                        locate_label,
                    ),
                    type="button",
                    disabled=MapPickerState.geo_busy,
                    on_click=MapPickerState.use_my_location,
                    class_name=rx.cond(
                        picker_key == "onboarding-first-request",
                        "order-2 mx-auto mt-3 min-h-11 w-fit flex items-center justify-center gap-2 rounded-full border border-[#b86e08] bg-[#fff7e8] px-4 py-2 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                        "mt-3 w-full sm:w-fit flex items-center justify-center gap-2 rounded-full bg-[#fba922] px-4 py-2 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                    ),
                ),
                rx.cond(
                    (MapPickerState.status != "") & ~rx.Var.create(inline),
                    rx.el.p(
                        rx.cond(
                            status_text, status_text, MapPickerState.status
                        ),
                        role="status",
                        class_name="mt-3 rounded-2xl border border-[#e08b12] bg-[#fff7e8] px-4 py-2.5 text-xs font-semibold leading-relaxed text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    MapPickerState.error,
                    rx.el.p(
                        rx.cond(error_text, error_text, MapPickerState.error),
                        role="alert",
                        class_name="mt-3 rounded-2xl border border-[#f7d9a0] bg-[#fff7e8] px-4 py-2.5 text-xs font-semibold leading-relaxed text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                class_name=rx.cond(
                    picker_key == "onboarding-first-request",
                    "mt-3 flex w-full flex-col",
                    "mt-3 w-full",
                ),
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )
