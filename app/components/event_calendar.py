import reflex as rx

from app.interface_i18n import ui
from app.states.auth_state import AuthState
from app.states.event_state import EventState


def event_calendar_day(cell: dict[str, str | bool]) -> rx.Component:
    return rx.el.button(
        cell["label"].to(str),
        type="button",
        disabled=cell["disabled"].to(bool),
        aria_label=cell["accessible_label"].to(str),
        aria_pressed=cell["selected"].to(bool),
        aria_current=rx.cond(cell["today"].to(bool), "date", "false"),
        on_click=EventState.select_calendar_day(cell["date"].to(str)),
        class_name=rx.cond(
            cell["selected"].to(bool),
            "gah-orange-control min-h-10 rounded-lg border border-[#fba922] bg-[#fba922] text-black text-sm disabled:opacity-30",
            rx.cond(
                cell["today"].to(bool),
                "gah-orange-control min-h-10 rounded-lg border border-[#fba922] bg-[#fff7e8] text-[#e08b12] text-sm disabled:opacity-30",
                "min-h-10 rounded-lg border border-transparent bg-white text-gray-800 text-sm hover:bg-[#fff7e8] disabled:opacity-30 disabled:cursor-not-allowed",
            ),
        ),
    )


def event_date_calendar() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.span(
                rx.cond(
                    EventState.has_date_filter,
                    EventState.calendar_display_selection,
                    ui("Select your dates"),
                )
            ),
            rx.icon("calendar-days", class_name="size-4 text-[#e08b12]"),
            type="button",
            aria_label=ui("Select your dates"),
            aria_expanded=EventState.calendar_open,
            aria_controls="event-date-grid",
            on_click=EventState.toggle_calendar,
            class_name="flex w-full items-center justify-between rounded-xl border border-[#e5e7eb] bg-white px-4 py-3 text-sm font-medium text-black shadow-sm hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.cond(
            EventState.calendar_open,
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        rx.icon("x", class_name="size-4"),
                        type="button",
                        id="gah-event-calendar-close",
                        aria_label=ui("Close event calendar"),
                        on_click=EventState.close_calendar,
                        class_name="absolute right-2 top-2 flex size-8 items-center justify-center rounded-full border border-[#fba922] bg-[#fff7e8] text-[#e08b12]",
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("chevron-left", class_name="size-4"),
                            type="button",
                            aria_label=ui("Previous month"),
                            disabled=~EventState.calendar_can_previous,
                            on_click=EventState.change_calendar_month(-1),
                            class_name="size-9 flex items-center justify-center rounded-lg bg-white text-[#e08b12] disabled:opacity-30",
                        ),
                        rx.el.p(
                            EventState.calendar_display_month,
                            aria_live="polite",
                            class_name="text-sm font-semibold text-gray-900",
                        ),
                        rx.el.button(
                            rx.icon("chevron-right", class_name="size-4"),
                            type="button",
                            aria_label=ui("Next month"),
                            disabled=~EventState.calendar_can_next,
                            on_click=EventState.change_calendar_month(1),
                            class_name="size-9 flex items-center justify-center rounded-lg bg-white text-[#e08b12] disabled:opacity-30",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    class_name="relative mb-2 flex w-full justify-center",
                ),
                rx.el.div(
                    rx.foreach(
                        EventState.calendar_display_weekdays,
                        lambda day: rx.el.span(
                            day,
                            class_name="text-center text-xs font-medium text-gray-600",
                        ),
                    ),
                    rx.foreach(
                        EventState.calendar_display_cells, event_calendar_day
                    ),
                    class_name="grid grid-cols-7 gap-1 w-full",
                ),
                rx.el.div(
                    rx.el.button(
                        ui("Single days"),
                        type="button",
                        aria_pressed=EventState.calendar_mode == "single",
                        on_click=EventState.set_calendar_mode("single"),
                        class_name=rx.cond(
                            EventState.calendar_mode == "single",
                            "rounded-xl border border-[#fba922] bg-[#fff7e8] px-3 py-2 text-sm text-[#e08b12]",
                            "rounded-xl border border-[#fba922] bg-white px-3 py-2 text-sm text-black",
                        ),
                    ),
                    rx.el.button(
                        ui("Days between"),
                        type="button",
                        aria_pressed=EventState.calendar_mode == "range",
                        on_click=EventState.set_calendar_mode("range"),
                        class_name=rx.cond(
                            EventState.calendar_mode == "range",
                            "rounded-xl border border-[#fba922] bg-[#fff7e8] px-3 py-2 text-sm text-[#e08b12]",
                            "rounded-xl border border-[#fba922] bg-white px-3 py-2 text-sm text-black",
                        ),
                    ),
                    class_name="mt-3 flex justify-center gap-2",
                ),
                id="event-date-grid",
                role="group",
                aria_label=ui("Choose an event date"),
                class_name="mt-2 w-full rounded-xl border border-[#e5e7eb] bg-white p-3 shadow-sm",
            ),
            rx.fragment(),
        ),
        rx.cond(
            EventState.has_date_filter,
            rx.el.button(
                ui("Clear date filter"),
                type="button",
                on_click=EventState.clear_date_filter,
                class_name="gah-orange-control mt-2 rounded-lg border border-[#fba922] bg-[#fff7e8] px-3 py-2 text-sm text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        on_mount=rx.call_script(
            "Intl.DateTimeFormat().resolvedOptions().timeZone",
            callback=EventState.initialize_calendar,
        ),
        id="gah-event-calendar",
        dir=AuthState.interface_direction,
        class_name="w-full",
    )
