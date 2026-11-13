import reflex as rx

from app.components.geolocation import geolocation_request
from app.states.profile_state import ProfileState


LOCATION_TAP_ON = (
    "gah-segment-control flex flex-1 shrink-0 basis-auto items-center justify-center gap-1.5 rounded-xl "
    "bg-[#fba922] px-2 py-2 text-[11px] font-bold text-white "
    "transition-colors disabled:opacity-60 outline-hidden "
    "focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
)
LOCATION_TAP_OFF = (
    "gah-segment-control flex flex-1 shrink-0 basis-auto items-center justify-center gap-1.5 rounded-xl "
    "bg-white px-2 py-2 text-[11px] font-bold text-black "
    "transition-colors hover:bg-[#fff7e8] disabled:opacity-60 "
    "outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
)


def location_tap(
    value: str, label: str, icon: str, compact: bool = False
) -> rx.Component:
    return rx.el.button(
        rx.icon(
            icon,
            class_name=rx.cond(
                value == "hidden",
                "h-3.5 w-3.5 shrink-0 text-black",
                "h-3.5 w-3.5 shrink-0",
            ),
        ),
        rx.el.span(
            label,
            class_name=rx.cond(
                value == "hidden",
                "whitespace-nowrap text-black",
                "whitespace-nowrap",
            ),
        ),
        type="button",
        role="radio",
        disabled=ProfileState.geo_busy,
        aria_checked=rx.cond(
            ProfileState.location_mode == value, "true", "false"
        ),
        aria_label=f"Show my location: {label}",
        on_click=lambda: ProfileState.set_location_mode(value),
        class_name=rx.cond(
            ProfileState.location_mode == value,
            rx.cond(
                compact,
                "gah-segment-control flex flex-1 shrink-0 basis-auto items-center justify-center gap-1 rounded-lg bg-[#fba922] px-2 py-1.5 text-[11px] font-bold text-[#111827] transition-colors disabled:opacity-60 outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40",
                LOCATION_TAP_ON,
            ),
            rx.cond(
                compact,
                "gah-segment-control flex flex-1 shrink-0 basis-auto items-center justify-center gap-1 rounded-lg bg-transparent px-2 py-1.5 text-[11px] font-bold text-[#404040] transition-colors hover:bg-white disabled:opacity-60 outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40",
                LOCATION_TAP_OFF,
            ),
        ),
    )


def location_selection(compact: bool = False) -> rx.Component:
    return rx.el.div(
        geolocation_request(
            request_token=ProfileState.geo_token,
            on_position=ProfileState.save_live_position,
            on_error=ProfileState.live_location_failed,
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    rx.cond(compact, "My location", "Show my location"),
                    class_name=rx.cond(
                        compact,
                        "text-xs font-semibold text-[#404040]",
                        "text-[13px] font-bold text-[#111827]",
                    ),
                ),
                class_name=rx.cond(
                    compact,
                    "flex w-fit items-center justify-start text-left",
                    "mb-1 flex w-full justify-center text-center",
                ),
            ),
            rx.el.div(
                location_tap("hidden", "Off", "eye-off", compact=compact),
                location_tap(
                    "approximate", "Approx", "circle-dot", compact=compact
                ),
                role="radiogroup",
                aria_label="Show my location",
                class_name=rx.cond(
                    compact,
                    "gah-segment-group flex min-w-fit flex-1 flex-row flex-wrap items-stretch gap-1 rounded-xl bg-white/80 p-0.5",
                    "gah-segment-group flex w-full flex-row items-stretch gap-1 rounded-2xl border border-[#d4d4d4] bg-white p-1",
                ),
            ),
            class_name=rx.cond(
                compact,
                "flex w-full flex-wrap items-center justify-start gap-x-2 gap-y-1.5",
                "flex flex-col w-full items-center",
            ),
        ),
        rx.cond(
            ProfileState.location_status,
            rx.el.p(
                ProfileState.location_status,
                role="status",
                class_name="mt-1.5 text-center text-xs font-semibold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ProfileState.location_error,
            rx.el.p(
                ProfileState.location_error,
                role="alert",
                class_name="mt-1.5 text-center text-xs font-bold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )
