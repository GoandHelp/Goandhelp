import reflex as rx

from app.interface_i18n import ui, ui_template, ui_template_multi
from app.avatars import animal_avatar

from app.components.language_control import browser_translatable_text
from app.components.help_hub_metadata import (
    localized_calendar_accessible_date,
    localized_calendar_month,
    localized_date_error,
    localized_date_trigger,
    localized_date_value,
    localized_duration_unit,
    localized_flexible_summary,
    localized_help_privacy,
    localized_rewards_summary,
    localized_selected_date_count,
)
from app.countries import WORLD_COUNTRY_NAMES
from app.components.disclosure import (
    disclosure_arrow,
    record_disclosure,
    record_summary,
)

from app.components.feedback import (
    INPUT_CLASS,
    SELECT_CLASS,
    select_wrapper,
    avatar_with_tick,
    error_banner,
    field_label,
    success_banner,
)
from app.components.help_post_panel import (
    category_section,
    photo_upload_section,
    square_photo_thumbnail,
    owner_delete_footer,
)
from app.components.event_cards import (
    hosted_events_section,
    others_events_section,
)
from app.components.map_picker import map_picker
from app.components.saved_items import (
    saved_requests_section,
    saved_searches_section,
)
from app.states.bookmark_state import BookmarkState
from app.states.event_state import EventState
from app.states.saved_search_state import SavedSearchState
from app.components.notification_badge import corner_activity_dot
from app.states.help_hub_state import (
    HelpHubState,
    ConfirmedHelper,
    HelperUpcoming,
)
from app.states.messaging_state import MessagingState
from app.states.help_post_state import HelpPostState, RecentPost
from app.states.auth_state import AuthState
from app.components.request_heading import (
    request_heading,
    styled_count_template,
)
from app.states.notification_state import NotificationState
from app.states.profile_state import ProfileState


def avatar_src(path: rx.Var[str], seed: rx.Var[str]) -> rx.Var[str]:
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


ICON_TILE = "flex shrink-0 items-center justify-center rounded-2xl bg-[#e08b12]"


def icon_tile(
    icon: str, tile_size: str = "size-11", glyph: str = "h-5 w-5"
) -> rx.Component:
    """Cobalt rounded tile with a white Lucide glyph — the Help page standard."""
    return rx.el.div(
        rx.icon(icon, class_name=f"{glyph} text-white"),
        class_name=f"{ICON_TILE} {tile_size}",
    )


def light_icon_tile(
    icon: str, tile_size: str = "size-10", glyph: str = "h-5 w-5"
) -> rx.Component:
    return rx.el.span(
        rx.icon(icon, class_name="size-3.5 text-[#e08b12]"),
        class_name="flex size-7 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8]",
    )


def green_icon_tile(
    icon: str, tile_size: str = "size-11", glyph: str = "h-5 w-5"
) -> rx.Component:
    return rx.el.span(
        rx.icon(icon, class_name="h-5 w-5 text-[#e08b12]"),
        class_name="flex size-11 shrink-0 items-center justify-center rounded-2xl border border-[#e08b12] bg-[#fff7e8]",
    )


def compact_section_heading(
    icon: str, title: str, count: rx.Var[int], subtitle: str = ""
) -> rx.Component:
    return request_heading(title, count, subtitle)


def inbox_style_shell(*children) -> rx.Component:
    """The exact Inbox `offers_block` / `confirmed_helpers_block` container."""
    return rx.el.section(
        *children,
        class_name="w-full bg-transparent",
    )


def section_heading(
    title: str, subtitle: str, icon: str, count: rx.Var[int]
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            icon_tile(icon),
            rx.el.div(
                rx.el.h2(
                    ui(title),
                    class_name="text-center text-xl sm:text-2xl font-bold tracking-tight text-[#111827] leading-tight",
                ),
                rx.el.p(
                    ui(subtitle),
                    class_name="mt-1 text-sm font-semibold text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 min-w-0 flex-1",
        ),
        rx.el.span(
            count,
            class_name="w-fit shrink-0 rounded-full bg-[#e08b12] px-3 py-1 text-xs font-bold text-white",
        ),
        class_name="flex w-full items-start justify-between gap-4",
    )


def info_strip(icon: str, label: str, value: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        icon_tile(icon, "size-8", "h-4 w-4"),
        rx.el.div(
            rx.el.p(
                label,
                class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
            ),
            rx.el.p(
                value,
                class_name="mt-0.5 text-sm font-semibold text-[#111827] leading-snug",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 min-w-0 rounded-2xl border border-[#f6c66f] bg-white px-3 py-2.5",
    )


def optional_strip(
    icon: str, label: str, value: rx.Var[str], fallback: str
) -> rx.Component:
    return rx.cond(
        value,
        info_strip(icon, label, value),
        info_strip(icon, label, fallback),
    )


def plain_detail(label: str, value: rx.Var[str]) -> rx.Component:
    """Editorial label/value pair: no icon, no border, whitespace only."""
    return rx.el.div(
        rx.el.dt(
            label,
            class_name="text-[10px] font-bold uppercase tracking-[0.12em] text-[#111827]",
        ),
        rx.el.dd(
            value,
            class_name="mt-1 text-sm font-semibold leading-relaxed text-[#111827]",
        ),
        class_name="min-w-0",
    )


def optional_plain_detail(
    label: str, value: rx.Var[str], fallback: str
) -> rx.Component:
    return rx.cond(
        value,
        plain_detail(label, value),
        plain_detail(label, fallback),
    )


def section_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        class_name="mt-2 flex flex-col gap-3 w-full",
    )


def section_shell(*children) -> rx.Component:
    return rx.el.section(
        *children,
        class_name=rx.cond(
            HelpHubState.form_open,
            "gah-main-card mx-auto w-full rounded-[2rem] bg-[#ffffff] px-5 py-[10px] sm:px-6 sm:py-[14px]",
            "gah-main-card mx-auto w-[calc(100%-30px)] rounded-[2rem] bg-[#ffffff] px-5 py-[10px] sm:px-6 sm:py-[14px]",
        ),
    )


# --------------------------------------------------------------------------
# 1. Post a help request (accordion)
# --------------------------------------------------------------------------


def date_chip(value: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        rx.el.span(
            rx.icon("calendar", class_name="h-3 w-3 text-white"),
            class_name="flex size-5 shrink-0 items-center justify-center rounded-full bg-[#e08b12]",
        ),
        localized_date_value(value),
        rx.el.button(
            rx.icon("x", class_name="h-3 w-3"),
            type="button",
            title=ui("Remove this day"),
            aria_label=ui("Remove this day"),
            on_click=lambda: HelpHubState.remove_date(value),
            class_name="ml-1 flex size-5 items-center justify-center rounded-full border border-[#f2bd5a] bg-white text-[#b86e08] transition-colors hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f6c66f] bg-white px-2.5 py-1 text-xs font-bold text-[#111827]",
    )


def calendar_day(cell: dict[str, str | bool]) -> rx.Component:
    return rx.el.button(
        cell["label"].to(str),
        type="button",
        disabled=cell["disabled"].to(bool),
        aria_label=localized_calendar_accessible_date(cell["date"].to(str)),
        aria_pressed=cell["selected"].to(bool),
        aria_current=rx.cond(cell["today"].to(bool), "date", "false"),
        on_click=HelpHubState.select_calendar_day(cell["date"].to(str)),
        class_name=rx.cond(
            cell["selected"].to(bool),
            "min-h-10 rounded-lg border border-[#fba922] bg-[#fba922] text-black text-sm disabled:opacity-30",
            rx.cond(
                cell["today"].to(bool),
                "min-h-10 rounded-lg border border-[#fba922] bg-[#fff7e8] text-[#e08b12] text-sm disabled:opacity-30",
                "min-h-10 rounded-lg border border-transparent bg-white text-gray-800 text-sm hover:bg-[#fff7e8] disabled:opacity-30 disabled:cursor-not-allowed",
            ),
        ),
    )


def inline_help_calendar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                rx.icon("chevron-left", class_name="size-4"),
                type="button",
                aria_label=ui("Previous month"),
                disabled=~HelpHubState.calendar_can_previous,
                on_click=HelpHubState.change_calendar_month(-1),
                class_name="size-9 flex items-center justify-center rounded-lg bg-white text-[#e08b12] disabled:opacity-30",
            ),
            rx.el.p(
                localized_calendar_month(HelpHubState.calendar_month),
                aria_live="polite",
                class_name="text-sm font-semibold text-gray-900",
            ),
            rx.el.button(
                rx.icon("chevron-right", class_name="size-4"),
                type="button",
                aria_label=ui("Next month"),
                disabled=~HelpHubState.calendar_can_next,
                on_click=HelpHubState.change_calendar_month(1),
                class_name="size-9 flex items-center justify-center rounded-lg bg-white text-[#e08b12] disabled:opacity-30",
            ),
            class_name="flex items-center justify-between w-full mb-2",
        ),
        rx.el.div(
            rx.foreach(
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                lambda day: rx.el.span(
                    ui(day),
                    class_name="text-center text-xs font-medium text-gray-600",
                ),
            ),
            rx.foreach(HelpHubState.calendar_cells, calendar_day),
            class_name="grid grid-cols-7 gap-1 w-full",
        ),
        rx.el.button(
            ui("Close calendar"),
            type="button",
            on_click=HelpHubState.close_calendar,
            class_name="mt-2 rounded-lg px-3 py-2 bg-white text-[#e08b12] text-sm",
        ),
        id="help-day-calendar",
        role="group",
        aria_label=ui("Choose a date"),
        class_name="mt-2 w-full rounded-xl border border-[#fba922] bg-white p-3",
    )


def specific_help_day_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.el.span(localized_date_trigger(HelpHubState.date_input)),
                    rx.icon(
                        "calendar-days", class_name="size-4 text-[#e08b12]"
                    ),
                    type="button",
                    id="help-day-input",
                    aria_label=ui("Choose a date"),
                    aria_expanded=HelpHubState.calendar_open,
                    aria_controls="help-day-calendar",
                    on_click=HelpHubState.toggle_calendar,
                    class_name="flex w-full items-center justify-between rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900",
                ),
                rx.cond(
                    HelpHubState.calendar_open,
                    inline_help_calendar(),
                    rx.fragment(),
                ),
                class_name="w-full min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-4 w-4 text-black"),
                ui("Add date"),
                type="button",
                on_click=HelpHubState.add_date,
                class_name="w-full sm:w-fit shrink-0 flex items-center justify-center gap-2 rounded-xl border-[3px] border-[#fba922] bg-white px-5 py-2.5 text-sm font-bold text-black transition-colors hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="flex flex-col sm:flex-row items-start gap-2 w-full",
        ),
        rx.cond(
            HelpHubState.help_dates.length() > 0,
            rx.el.div(
                rx.foreach(HelpHubState.help_dates, date_chip),
                class_name="mt-2 flex flex-wrap items-center justify-center gap-2",
            ),
            rx.el.p(
                ui("Choose then 'Add' as many dates as you need"),
                class_name="mt-2 text-center text-xs font-medium text-[#4b5563]",
            ),
        ),
        rx.el.p(
            localized_selected_date_count(HelpHubState.help_dates),
            class_name="mt-1.5 text-center text-xs font-bold text-[#e08b12]",
        ),
        rx.cond(
            HelpHubState.date_error,
            rx.el.p(
                localized_date_error(HelpHubState.date_error),
                class_name="mt-1 break-words text-start text-xs font-semibold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def mode_button(
    label: str, selected: rx.Var[bool], action: rx.event.EventType
) -> rx.Component:
    return rx.el.button(
        ui(label),
        type="button",
        aria_pressed=selected,
        on_click=action,
        class_name=rx.cond(
            selected,
            "gah-orange-control min-h-11 rounded-xl border border-[#fba922] bg-white px-4 py-2 text-sm font-semibold text-black focus-visible:ring-2 focus-visible:ring-[#fba922]",
            "min-h-11 rounded-xl border border-[#d4d4d4] bg-white px-4 py-2 text-sm font-semibold text-black hover:border-[#fba922] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
    )


def weekday_choice(day: str) -> rx.Component:
    return day_choice(
        f"{day}s",
        HelpHubState.custom_weekdays.contains(day),
        HelpHubState.toggle_weekday(day),
    )


def day_choice(
    label: rx.Var[str] | str, selected: rx.Var[bool], action: rx.event.EventType
) -> rx.Component:
    return rx.el.button(
        rx.icon(
            rx.cond(selected, "square-check", "square"),
            class_name="h-4 w-4 shrink-0 text-[#e08b12]",
        ),
        ui(label),
        type="button",
        role="checkbox",
        aria_checked=selected,
        on_click=action,
        class_name="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-left text-sm text-[#111827] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def help_day_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            field_label("Date", "required"),
            class_name="flex justify-start text-left",
        ),
        rx.el.div(
            mode_button(
                "Specific days",
                HelpHubState.day_mode == "specific",
                HelpHubState.set_day_mode("specific"),
            ),
            mode_button(
                "Flexible days",
                HelpHubState.day_mode == "flexible",
                HelpHubState.set_day_mode("flexible"),
            ),
            class_name="mb-3 flex justify-center gap-2",
        ),
        rx.cond(
            HelpHubState.day_mode == "specific",
            specific_help_day_field(),
            rx.el.div(
                rx.el.button(
                    rx.el.span(
                        localized_flexible_summary(
                            HelpHubState.flexible_days,
                            HelpHubState.custom_weekdays,
                        ),
                        class_name="min-w-0 flex-1 break-words text-start",
                    ),
                    disclosure_arrow(HelpHubState.flexible_days_open),
                    type="button",
                    aria_expanded=HelpHubState.flexible_days_open,
                    on_click=HelpHubState.toggle_flexible_days,
                    class_name="flex w-full items-center gap-2 rounded-xl border border-[#f6c66f] bg-white px-4 py-3 text-sm text-[#111827] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                rx.cond(
                    HelpHubState.flexible_days_open,
                    rx.el.div(
                        rx.foreach(
                            HelpHubState.flexible_day_choices,
                            lambda day: day_choice(
                                day,
                                HelpHubState.flexible_days.contains(day),
                                HelpHubState.toggle_flexible_day(day),
                            ),
                        ),
                        role="group",
                        aria_label=ui("Flexible days"),
                        class_name="mt-2 flex flex-col rounded-xl border border-[#f6c66f] bg-white p-1",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    HelpHubState.flexible_days.contains("Custom"),
                    rx.el.div(
                        rx.foreach(
                            HelpHubState.weekday_choices,
                            weekday_choice,
                        ),
                        role="group",
                        aria_label=ui("Custom weekdays"),
                        class_name="mt-2 flex flex-wrap gap-1",
                    ),
                    rx.fragment(),
                ),
                class_name="w-full",
            ),
        ),
        on_mount=HelpHubState.refresh_date_bounds,
        class_name="w-full",
    )


def clock_select(
    name: str, label: str, options: rx.Var[list[str]], default: str
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(options, lambda value: rx.el.option(value, value=value)),
            name=name,
            aria_label=ui(label),
            default_value=default,
            class_name="w-11 appearance-none rounded-xl border border-[#f6c66f] bg-white py-2 pl-1.5 pr-5 text-[11px] text-[#111827] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-2 top-3 h-3 w-3 text-[#e08b12]",
        ),
        class_name="relative",
    )


def start_time_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            field_label("Start time", "required"),
            class_name="flex justify-start text-left",
        ),
        rx.el.div(
            mode_button(
                "Specific time",
                HelpHubState.time_mode == "specific",
                HelpHubState.set_time_mode("specific"),
            ),
            mode_button(
                "Flexible times",
                HelpHubState.time_mode == "flexible",
                HelpHubState.set_time_mode("flexible"),
            ),
            class_name="mb-3 flex justify-center gap-2",
        ),
        rx.cond(
            HelpHubState.time_mode == "specific",
            rx.el.div(
                clock_select(
                    "specific_hour",
                    "Specific start hour",
                    HelpHubState.hour_choices,
                    "09",
                ),
                rx.el.span(":"),
                clock_select(
                    "specific_minute",
                    "Specific start minute",
                    HelpHubState.minute_choices,
                    "00",
                ),
                class_name="flex items-center justify-center gap-1 text-sm text-black",
            ),
            rx.el.div(
                rx.el.span(
                    ui("Any time between"),
                    class_name="shrink-0 text-[10px] font-semibold",
                ),
                clock_select(
                    "from_hour",
                    "Range start hour",
                    HelpHubState.hour_choices,
                    "09",
                ),
                rx.el.span(":"),
                clock_select(
                    "from_minute",
                    "Range start minute",
                    HelpHubState.minute_choices,
                    "00",
                ),
                rx.el.span(ui("and")),
                clock_select(
                    "to_hour", "Range end hour", HelpHubState.hour_choices, "17"
                ),
                rx.el.span(":"),
                clock_select(
                    "to_minute",
                    "Range end minute",
                    HelpHubState.minute_choices,
                    "00",
                ),
                class_name="flex flex-nowrap items-center gap-1 text-[10px] text-[#111827] whitespace-nowrap overflow-hidden",
            ),
        ),
        class_name="w-full",
    )


def reward_checkbox(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.cond(
                HelpHubState.selected_rewards.contains(item["value"]),
                rx.icon("check", class_name="h-3.5 w-3.5 text-[#e08b12]"),
                rx.fragment(),
            ),
            class_name=rx.cond(
                HelpHubState.selected_rewards.contains(item["value"]),
                "flex size-5 shrink-0 items-center justify-center rounded-md border border-[#e08b12] bg-[#fff7e8]",
                "flex size-5 shrink-0 items-center justify-center rounded-md border-2 border-[#d4d4d4] bg-white",
            ),
        ),
        rx.el.span(
            rx.el.strong(ui(item["label"]), class_name="font-bold"),
            " – ",
            rx.el.span(ui(item["blurb"]), class_name="font-normal"),
            class_name="min-w-0 text-left text-sm leading-relaxed text-[#111827]",
        ),
        type="button",
        role="checkbox",
        aria_checked=rx.cond(
            HelpHubState.selected_rewards.contains(item["value"]),
            "true",
            "false",
        ),
        aria_label=ui(item["label"]),
        on_click=lambda: HelpHubState.toggle_reward(item["value"]),
        class_name=rx.cond(
            HelpHubState.selected_rewards.contains(item["value"]),
            "gah-orange-control flex w-full items-start gap-3 rounded-2xl border border-[#fba922] bg-[#fff7e8] p-4 transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            "flex w-full items-start gap-3 rounded-2xl border border-[#e5e5e5] bg-white p-4 transition-colors hover:border-[#fba922] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
    )


def quote_control(
    selected: rx.Var[bool], action: rx.event.EventType, label: str
) -> rx.Component:
    return rx.el.button(
        rx.icon(
            rx.cond(selected, "square-check", "square"),
            class_name="size-5 shrink-0 text-[#e08b12]",
        ),
        ui(label),
        type="button",
        role="checkbox",
        aria_checked=selected,
        on_click=action,
        class_name="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-3 py-3 text-center text-sm font-medium text-gray-900 focus-visible:outline-[#fba922]",
    )


def money_details_field() -> rx.Component:
    return rx.cond(
        HelpHubState.selected_rewards.contains("money"),
        rx.el.div(
            rx.el.label(
                ui("Currency"),
                html_for="reward-currency",
                class_name="text-sm font-bold text-gray-900",
            ),
            select_wrapper(
                rx.el.select(
                    rx.foreach(
                        HelpHubState.currency_options,
                        lambda item: rx.el.option(
                            item["label"], value=item["value"]
                        ),
                    ),
                    id="reward-currency",
                    name="reward_currency",
                    value=HelpHubState.reward_currency,
                    on_change=HelpHubState.set_reward_currency,
                    class_name=SELECT_CLASS,
                )
            ),
            rx.el.label(
                ui("Enter your budget"),
                html_for="money-budget",
                class_name="text-sm font-bold text-gray-900",
            ),
            rx.el.div(
                rx.el.span(
                    HelpHubState.reward_currency,
                    class_name="text-sm font-semibold text-[#e08b12]",
                ),
                rx.el.input(
                    id="money-budget",
                    name="money_budget",
                    type="number",
                    min="0.01",
                    step="0.01",
                    max="99999999.99",
                    input_mode="decimal",
                    placeholder="0.00",
                    disabled=HelpHubState.budget_quote_allowed,
                    required=~HelpHubState.budget_quote_allowed,
                    class_name="w-full rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-[#fba922] disabled:cursor-not-allowed disabled:bg-gray-100 disabled:opacity-50",
                ),
                class_name="flex w-full items-center gap-3",
            ),
            quote_control(
                HelpHubState.budget_quote_allowed,
                HelpHubState.toggle_budget_quote,
                "Ask helper for an estimate price",
            ),
            rx.el.p(
                ui("Go and Help receives an 8% fee"),
                class_name="text-center text-sm font-medium text-[#e08b12]",
            ),
            class_name="flex w-full flex-col gap-2 rounded-xl bg-white p-3",
        ),
        rx.fragment(),
    )


def conditional_reward_fields() -> rx.Component:
    return rx.el.div(
        rx.cond(
            HelpHubState.needs_nights,
            rx.el.div(
                field_label("Number of nights", "required for accommodation"),
                rx.el.input(
                    name="accommodation_nights",
                    type="number",
                    min="1",
                    max="365",
                    step="1",
                    placeholder="2",
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpHubState.needs_tour_details,
            rx.el.div(
                field_label("Guided tour details", "required"),
                rx.el.input(
                    name="guided_tour_details",
                    placeholder=ui(
                        "A half-day walk through the old town and the port"
                    ),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpHubState.needs_activity_details,
            rx.el.div(
                field_label("Activity details", "required"),
                rx.el.input(
                    name="activity_details",
                    placeholder=ui(
                        "Surf lesson with my board, or a river swim after work"
                    ),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpHubState.needs_other_details,
            rx.el.div(
                field_label("Other reward details", "required"),
                rx.el.input(
                    name="other_reward_details",
                    placeholder=ui(
                        "I.e. Home-made Olive Oil and a ride to Milan"
                    ),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.fragment(),
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
    )


def rewards_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("gift", class_name="h-4 w-4 text-[#fba922]"),
            rx.el.h3(
                ui("Rewards"), class_name="text-base font-bold text-[#111827]"
            ),
            rx.el.span(
                ui("What you can offer – required"),
                class_name="ml-auto text-right text-xs text-black",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.button(
                rx.el.span(
                    localized_rewards_summary(HelpHubState.selected_rewards),
                    class_name="min-w-0 flex-1 break-words text-start",
                ),
                disclosure_arrow(HelpHubState.rewards_open),
                type="button",
                aria_label=ui("Choose one or more rewards"),
                aria_expanded=HelpHubState.rewards_open,
                aria_controls="help-reward-options",
                on_click=HelpHubState.toggle_rewards,
                class_name="flex min-h-11 w-full items-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-4 py-3 text-sm font-medium text-[#404040] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            rx.cond(
                HelpHubState.rewards_open,
                rx.el.div(
                    rx.foreach(HelpHubState.reward_choices, reward_checkbox),
                    rx.el.button(
                        ui("Done"),
                        type="button",
                        on_click=HelpHubState.close_rewards,
                        custom_attrs={"data-rewards-close": "true"},
                        class_name="mx-auto w-fit rounded-full bg-[#fff7e8] px-4 py-2 text-sm font-medium text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#fba922]",
                    ),
                    id="help-reward-options",
                    role="group",
                    aria_label=ui("Rewards — select multiple"),
                    class_name="mt-2 flex w-full flex-col gap-2 rounded-xl border border-[#f6c66f] bg-white p-2",
                ),
                rx.fragment(),
            ),
            id="help-rewards-boundary",
            on_mount=rx.call_script("""
                (() => {
                    const boundary = document.getElementById('help-rewards-boundary');
                    if (!boundary) return;
                    const close = (event) => {
                        const trigger = boundary.querySelector('[aria-controls="help-reward-options"]');
                        if (trigger?.getAttribute('aria-expanded') !== 'true') return;
                        const escape = event.type === 'keydown' && event.key === 'Escape';
                        if (event.type === 'keydown' && !escape) return;
                        if (!escape && boundary.contains(event.target)) return;
                        boundary.querySelector('[data-rewards-close]')?.click();
                        if (escape) { event.preventDefault(); trigger.focus(); }
                    };
                    document.addEventListener('click', close);
                    document.addEventListener('keydown', close);
                    window.gahRewardsCleanup = () => {
                        document.removeEventListener('click', close);
                        document.removeEventListener('keydown', close);
                    };
                })();
            """),
            on_unmount=rx.call_script(
                "window.gahRewardsCleanup?.(); delete window.gahRewardsCleanup;"
            ),
            class_name="w-full",
        ),
        conditional_reward_fields(),
        money_details_field(),
        class_name="flex flex-col gap-3 w-full",
    )


def job_location_section() -> rx.Component:
    """Location heading, map, privacy status, then address fields."""
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                ui("Location of this help request"),
                class_name="w-full text-center text-base font-bold text-[#111827]",
            ),
            class_name="w-full",
        ),
        map_picker(
            "help-request",
            ui("Pin the exact spot for your help request"),
            inline=True,
        ),
        rx.el.p(
            rx.icon("shield-check", class_name="mr-2 inline h-4 w-4"),
            localized_help_privacy(HelpHubState.job_location_description),
            role="status",
            class_name="mt-3 w-full break-words rounded-2xl border border-[#fba922] bg-[#fff7e8] px-4 py-3 text-start text-xs font-semibold leading-relaxed text-[#e08b12]",
        ),
        rx.el.div(
            field_label("Address", "required when no map pin"),
            rx.el.input(
                type="text",
                name="address",
                placeholder=ui("Address"),
                class_name=INPUT_CLASS,
            ),
            class_name="mt-4 w-full",
        ),
        rx.el.div(
            field_label("City", "required when no map pin"),
            rx.el.input(
                type="text",
                name="city",
                placeholder=ui("City"),
                class_name=INPUT_CLASS,
            ),
            class_name="mt-3 w-full",
        ),
        rx.el.div(
            field_label("Country", "required when no map pin"),
            select_wrapper(
                rx.el.select(
                    rx.el.option(ui("Country"), value=""),
                    rx.foreach(
                        WORLD_COUNTRY_NAMES,
                        lambda country: rx.el.option(country, value=country),
                    ),
                    name="country",
                    aria_label=ui("Country"),
                    value=HelpHubState.posting_country,
                    on_change=HelpHubState.set_posting_country,
                    class_name=SELECT_CLASS,
                )
            ),
            class_name="mt-3 w-full",
        ),
        class_name="w-full bg-white",
    )


def required_language_row(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.cond(
            item["code"] == "",
            rx.icon(
                "globe",
                aria_hidden=True,
                class_name="size-4 shrink-0 text-[#e08b12]",
            ),
            rx.fragment(
                rx.icon(
                    rx.cond(
                        HelpHubState.required_languages.contains(item["code"]),
                        "square-check",
                        "square",
                    ),
                    aria_hidden=True,
                    class_name="size-4 text-[#e08b12]",
                ),
                rx.el.span(item["flag"], aria_hidden="true"),
            ),
        ),
        rx.el.span(item["name"]),
        type="button",
        role="checkbox",
        aria_checked=rx.cond(
            item["code"] == "",
            HelpHubState.required_languages.length() == 0,
            HelpHubState.required_languages.contains(item["code"]),
        ),
        on_click=lambda: HelpHubState.toggle_required_language(item["code"]),
        class_name="flex min-h-11 w-full items-center gap-2 rounded-lg bg-white px-3 text-left text-sm text-[#111827] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def required_languages_field() -> rx.Component:
    return rx.el.div(
        field_label("Required Language"),
        rx.el.button(
            rx.el.span(
                HelpHubState.required_languages_label,
                class_name="min-w-0 flex-1 text-left",
            ),
            disclosure_arrow(HelpHubState.languages_open),
            type="button",
            aria_expanded=HelpHubState.languages_open,
            aria_label=ui("Choose required languages"),
            on_click=HelpHubState.toggle_languages,
            class_name="flex w-full items-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-4 py-3 text-sm text-[#111827] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.cond(
            HelpHubState.languages_open,
            rx.el.div(
                rx.foreach(
                    HelpHubState.language_choices, required_language_row
                ),
                role="group",
                aria_label=ui("Required languages"),
                class_name="mt-2 max-h-64 overflow-y-auto rounded-xl border border-[#d4d4d4] bg-white p-1",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def duration_period_select() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                HelpHubState.duration_period_options,
                lambda item: rx.el.option(
                    localized_duration_unit(item["label"]),
                    value=item["value"],
                ),
            ),
            name="duration_period_unit",
            aria_label=ui("Duration period unit"),
            value=HelpHubState.duration_period_unit,
            on_change=HelpHubState.set_duration_period_unit,
            class_name="w-20 appearance-none rounded-xl border border-[#f6c66f] bg-white py-2 pl-2 pr-5 text-[11px] text-black focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-2 top-3 h-3 w-3 text-[#e08b12]",
        ),
        class_name="relative",
    )


def duration_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            field_label("Duration"),
            class_name="flex justify-start text-left",
        ),
        rx.el.fieldset(
            rx.el.div(
                clock_select(
                    "duration_hours",
                    ui("Duration hours"),
                    HelpHubState.duration_hour_choices,
                    "0",
                ),
                rx.el.span(ui("Hours"), class_name="text-xs text-black"),
                class_name="flex flex-col items-center gap-1.5",
            ),
            rx.el.div(
                clock_select(
                    "duration_minutes_part",
                    ui("Duration minutes"),
                    HelpHubState.duration_minute_choices,
                    "0",
                ),
                rx.el.span(ui("Minutes"), class_name="text-xs text-black"),
                class_name="flex flex-col items-center gap-1.5",
            ),
            rx.el.div(
                rx.el.span(ui("For")),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            HelpHubState.duration_count_choices,
                            lambda value: rx.el.option(value, value=value),
                        ),
                        name="duration_period_count",
                        aria_label=ui("Duration period count"),
                        value=HelpHubState.duration_period_count.to_string(),
                        on_change=HelpHubState.set_duration_period_count,
                        class_name="w-11 appearance-none rounded-xl border border-[#f6c66f] bg-white py-2 pl-1.5 pr-5 text-[11px] text-black focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute right-2 top-3 h-3 w-3 text-[#e08b12]",
                    ),
                    class_name="relative",
                ),
                duration_period_select(),
                class_name="flex items-center gap-1.5",
            ),
            disabled=HelpHubState.duration_quote_allowed,
            class_name="flex w-full min-w-0 flex-nowrap items-start justify-center-safe gap-2 overflow-x-auto pb-1 text-xs text-black disabled:opacity-50 disabled:[&_select]:cursor-not-allowed",
        ),
        quote_control(
            HelpHubState.duration_quote_allowed,
            HelpHubState.toggle_duration_quote,
            "Ask helper for an estimate duration",
        ),
        class_name="w-full",
    )


def post_help_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label("Job title", "required"),
            rx.el.input(
                name="title",
                placeholder=ui("Two hands to carry boxes up three flights"),
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label("Job description", "required — max 500 characters"),
            rx.el.textarea(
                name="description",
                rows="5",
                max_length=500,
                placeholder=ui(
                    "I'm moving out of a fourth-floor flat and need someone strong for a couple of hours…"
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="w-full",
        ),
        category_section(),
        photo_upload_section(),
        help_day_field(),
        start_time_field(),
        duration_field(),
        job_location_section(),
        rewards_field(),
        rx.cond(
            HelpHubState.missing_fields.length() > 0,
            rx.el.div(
                rx.el.p(
                    ui("Please fill out all the fields"),
                    class_name="font-semibold text-[#e08b12]",
                ),
                rx.foreach(
                    HelpHubState.missing_fields,
                    lambda label: rx.el.p(
                        f"– {label}", class_name="text-[#e08b12]"
                    ),
                ),
                role="alert",
                aria_live="polite",
                class_name="w-full rounded-xl bg-[#fff7e8] px-4 py-3 text-sm text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.cond(
                HelpHubState.is_saving,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Posting your request…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("send", class_name="h-4 w-4"),
                    ui("Post help request"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=HelpHubState.is_saving,
            class_name="gah-post-request gah-primary-outline mx-auto w-fit rounded-xl border border-[#fba922] bg-white px-6 py-3 text-sm font-bold text-black transition-colors hover:bg-[#fff7e8] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#111827]",
        ),
        no_validate=True,
        on_submit=HelpHubState.create_help_request,
        reset_on_submit=False,
        class_name="flex flex-col gap-5 w-full bg-transparent",
    )


def post_help_section() -> rx.Component:
    return rx.el.section(
        rx.el.button(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            ui("Ask for Help"),
                            class_name="text-lg font-bold tracking-tight text-[#111827] leading-tight",
                        ),
                        rx.icon(
                            "arrow-right",
                            aria_hidden=True,
                            class_name="size-4 shrink-0 text-[#111827]",
                        ),
                        class_name="flex items-center justify-center gap-2",
                    ),
                    class_name="flex w-full min-w-0 flex-col items-center text-center",
                ),
                class_name="mx-auto flex w-full min-w-0 max-w-md flex-col items-center justify-center",
            ),
            type="button",
            aria_expanded=rx.cond(HelpHubState.form_open, "true", "false"),
            aria_label=ui("Ask for Help"),
            aria_controls="gah-ask-help-form",
            on_click=HelpHubState.toggle_form,
            class_name="gah-request-ask mx-auto flex min-h-0 w-fit max-w-full items-center justify-center rounded-2xl border border-[#fba922] bg-[#fba922] px-4 py-3 text-[#111827] transition-colors hover:bg-[#e08b12] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12]",
        ),
        error_banner(HelpHubState.error),
        success_banner(HelpHubState.success),
        rx.cond(
            HelpHubState.form_open,
            section_shell(
                rx.el.div(
                    post_help_form(),
                    id="gah-ask-help-form",
                    class_name="w-full bg-white py-4",
                ),
            ),
            rx.fragment(),
        ),
        class_name="flex w-full flex-col gap-4 bg-transparent",
    )


# --------------------------------------------------------------------------
# 2. Your upcoming help
# --------------------------------------------------------------------------


def person_header(
    name: rx.Var[str],
    avatar_seed: rx.Var[str],
    avatar: rx.Var[str],
    handle: rx.Var[str] | str,
    badge: rx.Var[str] | str,
    badge_class: str,
    verified: rx.Var[bool] | bool = False,
) -> rx.Component:
    return rx.el.div(
        avatar_with_tick(
            avatar_src(avatar, avatar_seed),
            verified,
            "size-14 shrink-0 rounded-full bg-[#fff7e8] object-cover ring-2 ring-[#fff7e8]",
            ui("Profile photo"),
        ),
        rx.el.div(
            rx.el.p(
                name,
                class_name="text-base font-bold text-[#111827] leading-tight",
            ),
            rx.cond(
                handle,
                rx.el.span(
                    handle,
                    class_name="mt-1 w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#b86e08]",
                ),
                rx.fragment(),
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.span(ui(badge), class_name=badge_class),
        class_name="flex w-full items-start gap-3",
    )


def changes_guidance() -> rx.Component:
    return rx.el.p(
        rx.icon("messages-square", class_name="h-3.5 w-3.5 shrink-0"),
        ui("Discuss any changes directly with your helping partner in Inbox."),
        class_name="mt-3 flex items-center gap-2 text-xs font-medium text-[#4b5563]",
    )


def directions_block(row: dict[str, str]) -> rx.Component:
    """Open the agreed meeting point in an external map, when authorized.

    The link is only rendered when the server built a usable destination for
    this participant: a public place, or an exact meeting point the helpee has
    already shared. Nothing else is exposed.
    """
    return rx.cond(
        row["directions_url"],
        rx.el.div(
            rx.el.a(
                rx.icon("navigation", class_name="h-4 w-4"),
                ui("Get directions"),
                href=row["directions_url"],
                target="_blank",
                rel="noopener noreferrer",
                aria_label=ui(
                    "Get directions to this help job in an external map, opens in a new tab"
                ),
                class_name="gah-primary-outline w-fit flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#111827]",
            ),
            class_name="w-fit",
        ),
        rx.fragment(),
    )


def upcoming_help_card(job: HelperUpcoming) -> rx.Component:
    return record_disclosure(
        record_summary(
            avatar_with_tick(
                avatar_src(job["other_avatar"], job["other_avatar_seed"]),
                job["other_verified"],
                "size-10 shrink-0 rounded-full bg-[#fff7e8] object-cover",
                ui("Profile photo"),
                member_id=job["other_id"].to(int),
            ),
            f"{job['other_name']} · {job['title']}",
            f"{job['dates']} · {job['location']}",
            job["status"],
        ),
        upcoming_help_body(job),
        key=job["id"],
    )


def upcoming_help_body(job: HelperUpcoming) -> rx.Component:
    return rx.el.div(
        corner_activity_dot(
            NotificationState.unread_help_post_ids.contains(job["id"]),
            ui("New activity on this job"),
        ),
        browser_translatable_text(
            job["description"],
            class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.div(
            info_strip("map-pin", ui("Where"), job["location"]),
            info_strip("calendar", ui("Help days"), job["dates"]),
            info_strip("clock", ui("Hours required"), job["hours"]),
            optional_strip(
                "wrench", ui("Tools"), job["tools"], ui("No tools listed")
            ),
            optional_strip(
                "graduation-cap",
                ui("Knowledge and skills"),
                job["knowledge"],
                ui("No special skills needed"),
            ),
            class_name="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        directions_block(job),
        changes_guidance(),
        class_name="relative w-full bg-white",
    )


def upcoming_help_section() -> rx.Component:
    return inbox_style_shell(
        compact_section_heading(
            "notebook-pen",
            "Confirmed Help",
            HelpHubState.upcoming_help.length(),
            "Get ready to help others",
        ),
        rx.cond(
            HelpHubState.is_loading & ~HelpHubState.has_loaded,
            section_skeleton(),
            rx.cond(
                HelpHubState.upcoming_help.length() > 0,
                rx.el.div(
                    rx.foreach(HelpHubState.upcoming_help, upcoming_help_card),
                    class_name="gah-edge-stack mt-2 flex flex-col gap-0 w-full",
                ),
                rx.fragment(),
            ),
        ),
    )


# --------------------------------------------------------------------------
# 3. Upcoming Helpers
# --------------------------------------------------------------------------


def helper_stars(row: ConfirmedHelper) -> rx.Component:
    return rx.el.span(
        rx.foreach(
            rx.Var.range(1, 6),
            lambda number: rx.icon(
                "star",
                aria_hidden=True,
                class_name=rx.cond(
                    (row["helper_rating_count"] > 0)
                    & (row["helper_rating"] >= number),
                    "size-3.5 fill-[#e08b12] text-[#e08b12]",
                    "size-3.5 fill-none text-[#e08b12]",
                ),
            ),
        ),
        role="img",
        aria_label=rx.cond(
            row["helper_rating_count"] > 0,
            ui_template_multi(
                "{rating} out of 5 stars; {count} reviews",
                {
                    "rating": f"{row['helper_rating']:.1f}",
                    "count": row["helper_rating_count"].to(int).to_string(),
                },
            ),
            ui("No reviews yet"),
        ),
        class_name="inline-flex shrink-0 items-center gap-0.5",
    )


def confirmed_helper_summary(row: ConfirmedHelper) -> rx.Component:
    return rx.el.summary(
        avatar_with_tick(
            avatar_src(row["helper_avatar"], row["helper_name"]),
            row["helper_verified"],
            "size-10 shrink-0 rounded-full object-cover",
            ui("Helper photo"),
            member_id=row["helper_id"],
        ),
        rx.el.span(
            rx.el.span(
                rx.el.span(
                    row["helper_name"],
                    class_name="text-sm font-bold text-[#111827]",
                ),
                helper_stars(row),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.span(
                row["title"],
                class_name="mt-1 block text-sm font-medium text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1 break-words",
        ),
        disclosure_arrow(),
        class_name="flex w-full cursor-pointer list-none items-center gap-3 p-4 text-left hover:bg-[#f9fafb] focus-visible:outline-2 focus-visible:outline-[#e08b12] [&::-webkit-details-marker]:hidden",
    )


def confirmed_helper_record(row: ConfirmedHelper) -> rx.Component:
    return record_disclosure(
        confirmed_helper_summary(row),
        confirmed_helper_card(row, True),
        key=f"{row['post_id']}-{row['thread_id']}",
    )


def confirmed_helper_card(
    row: ConfirmedHelper, compact: bool = False
) -> rx.Component:
    return rx.el.article(
        corner_activity_dot(
            NotificationState.unread_help_post_ids.contains(row["post_id"]),
            ui("New activity on this job"),
        ),
        rx.el.div(
            rx.image(
                src=avatar_src(row["helper_avatar"], row["helper_name"]),
                alt=ui("Helper photo"),
                class_name="size-14 shrink-0 rounded-full bg-[#fff7e8] object-cover",
            ),
            rx.el.div(
                rx.el.p(
                    row["helper_name"],
                    class_name="text-base font-bold text-[#111827]",
                ),
                rx.el.div(
                    rx.cond(
                        row["helper_handle"] != "",
                        rx.el.span(row["helper_handle"]),
                        rx.fragment(),
                    ),
                    rx.cond(
                        row["helper_rating_count"] > 0,
                        rx.el.span(
                            rx.icon("star", class_name="size-4 text-[#e08b12]"),
                            f"{row['helper_rating']:.1f} ({row['helper_rating_count']})",
                            class_name="flex items-center gap-1",
                        ),
                        rx.el.span(ui("New helper")),
                    ),
                    class_name="mt-1 flex flex-wrap items-center gap-3 text-sm text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name=rx.cond(compact, "hidden", "flex items-start gap-3"),
        ),
        rx.cond(
            compact,
            rx.fragment(),
            rx.el.h3(
                row["title"],
                class_name="mt-4 text-base font-bold text-[#111827] leading-snug",
            ),
        ),
        browser_translatable_text(
            row["description"],
            class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.dl(
            rx.el.div(
                rx.el.dt(
                    ui("Date time and duration"),
                    class_name="text-sm font-bold text-[#111827]",
                ),
                rx.el.dd(
                    rx.el.span(row["schedule_time"]),
                    rx.el.span(row["schedule_date"]),
                    class_name="mt-1 flex flex-wrap gap-x-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                ),
                class_name="col-span-full",
            ),
            plain_detail(ui("Where"), row["location"]),
            optional_plain_detail(
                ui("Tools"), row["tools"], ui("No tools listed")
            ),
            optional_plain_detail(
                ui("Knowledge and skills"),
                row["knowledge"],
                ui("No special skills needed"),
            ),
            optional_plain_detail(
                ui("Exact meeting place"),
                row["accepted_location"],
                ui("Not shared yet"),
            ),
            class_name="mt-5 grid w-full grid-cols-1 gap-4 [&_dt]:text-sm [&_dt]:normal-case [&_dt]:tracking-normal [&_dd]:font-medium [&_dd]:text-[#4b5563]",
        ),
        rx.el.div(
            rx.cond(
                row["thread_id"] > 0,
                rx.el.button(
                    rx.icon("message-circle", class_name="size-4"),
                    ui("Message Helper"),
                    type="button",
                    on_click=MessagingState.focus_thread(row["thread_id"]),
                    class_name="gah-primary-outline flex w-fit items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                rx.fragment(),
            ),
            class_name="mt-4 flex flex-wrap items-center gap-2",
        ),
        class_name=rx.cond(
            compact,
            "relative w-full bg-white",
            "relative -mx-4 sm:-mx-5 w-[calc(100%+2rem)] sm:w-[calc(100%+2.5rem)] border-y border-[#e5e5e5] bg-white px-4 py-5 sm:px-5",
        ),
    )


# Confirmed helpers and incoming offers are presented in the Inbox › Helpers
# folder; these cards are rendered from app/components/messages_panel.py.


# --------------------------------------------------------------------------
# 4. Help offers from others
# --------------------------------------------------------------------------


def help_offer_card(
    offer: dict[str, str], stacked: bool = False, detail_body: bool = False
) -> rx.Component:
    return rx.el.article(
        corner_activity_dot(
            NotificationState.unread_help_post_ids.contains(offer["post_id"]),
            ui("New activity on this request"),
        ),
        rx.cond(
            detail_body,
            rx.fragment(),
            rx.el.div(
                person_header(
                    offer["helper_name"],
                    offer["helper_avatar_seed"],
                    offer["helper_avatar"],
                    offer["helper_handle"],
                    "Waiting on you",
                    "w-fit shrink-0 rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold text-[#b86e08]",
                    offer["helper_verified"],
                ),
                rx.el.p(
                    ui_template("Offered {date}", "date", offer["applied"]),
                    class_name="mt-1 text-xs text-[#4b5563]",
                ),
            ),
        ),
        rx.el.h3(
            offer["title"],
            class_name="mt-4 text-base font-bold text-[#111827] leading-snug",
        ),
        browser_translatable_text(
            offer["description"],
            class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.div(
            info_strip("map-pin", ui("Where"), offer["location"]),
            info_strip("calendar", ui("Help days"), offer["dates"]),
            info_strip("clock", ui("Hours required"), offer["hours"]),
            info_strip(
                "calendar-check", ui("Helper proposes"), offer["proposed"]
            ),
            optional_strip(
                "wrench", ui("Tools"), offer["tools"], ui("No tools listed")
            ),
            optional_strip(
                "graduation-cap",
                ui("Knowledge and skills"),
                offer["knowledge"],
                ui("No special skills needed"),
            ),
            class_name="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        rx.el.div(
            field_label(
                "Note to this helper", "optional — sent to their inbox"
            ),
            rx.el.textarea(
                rows="2",
                placeholder=ui(
                    "See you at the market gate at 9am — thank you!"
                ),
                on_change=lambda value: ProfileState.set_response_draft(
                    offer["key"], value
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="mt-4 w-full",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("circle-check-big", class_name="h-4 w-4"),
                ui("Confirm"),
                type="button",
                disabled=ProfileState.deciding_id == offer["id"],
                on_click=lambda: ProfileState.confirm_application(offer["id"]),
                class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("circle-x", class_name="h-4 w-4"),
                ui("Deny"),
                type="button",
                disabled=ProfileState.deciding_id == offer["id"],
                on_click=lambda: ProfileState.deny_application(offer["id"]),
                class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-5 py-2.5 text-sm font-bold text-[#404040] transition-colors hover:bg-[#fff7e8] disabled:opacity-60",
            ),
            class_name="mt-4 flex flex-col sm:flex-row sm:items-center gap-2 w-full",
        ),
        rx.cond(
            offer["pitch"],
            rx.el.div(
                icon_tile("message-circle", "size-8", "h-4 w-4"),
                rx.el.p(
                    f"“{offer['pitch']}”",
                    class_name="text-sm font-medium italic leading-relaxed text-[#111827]",
                ),
                class_name="mt-3 flex items-start gap-2.5 bg-white px-4 py-3",
            ),
            rx.el.p(
                ui("This helper didn't add a message."),
                class_name="mt-3 text-sm font-medium italic text-[#4b5563]",
            ),
        ),
        class_name=rx.cond(
            stacked,
            "relative w-full min-w-0 bg-white p-5",
            "relative w-full rounded-3xl border border-[#fba922] bg-white p-5",
        ),
    )


# --------------------------------------------------------------------------
# 5. Your upcoming helpers
# --------------------------------------------------------------------------


def upcoming_helpees_section() -> rx.Component:
    return inbox_style_shell(
        compact_section_heading(
            "users",
            "Confirmed Helpers",
            HelpHubState.confirmed_helpers.length(),
            "People ready to help you",
        ),
        success_banner(HelpHubState.accepted_notice),
        success_banner(HelpHubState.schedule_notice),
        rx.cond(
            HelpHubState.is_loading & ~HelpHubState.has_loaded,
            section_skeleton(),
            rx.cond(
                HelpHubState.confirmed_helpers.length() > 0,
                rx.el.div(
                    rx.foreach(
                        HelpHubState.confirmed_helpers, confirmed_helper_record
                    ),
                    class_name="gah-edge-stack mt-2 flex flex-col gap-0 w-full",
                ),
                rx.fragment(),
            ),
        ),
    )


# --------------------------------------------------------------------------
# 6. Your help requests (with server-side removal)
# --------------------------------------------------------------------------


def counts_summary() -> rx.Component:
    """One responsive same-line summary of the poster's request totals."""
    return rx.el.div(
        rx.el.span(
            rx.el.span(
                ui_template(
                    "{count} Requested",
                    "count",
                    HelpPostState.counts["total"].to_string(),
                ),
                class_name="whitespace-nowrap",
            ),
            class_name="flex w-full min-w-0 justify-center text-center items-center rounded-xl bg-white px-2 py-2 text-xs font-bold text-[#b86e08] shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
        ),
        rx.el.span(
            rx.el.span(
                ui_template(
                    "{count} Open",
                    "count",
                    HelpPostState.counts["open"].to_string(),
                ),
                class_name="whitespace-nowrap",
            ),
            class_name="flex w-full min-w-0 justify-center text-center items-center rounded-xl bg-white px-2 py-2 text-xs font-bold text-[#b86e08] shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
        ),
        rx.el.span(
            rx.el.span(
                ui_template(
                    "{count} Upcoming",
                    "count",
                    HelpPostState.counts["upcoming"].to_string(),
                ),
                class_name="whitespace-nowrap",
            ),
            class_name="flex w-full min-w-0 justify-center text-center items-center rounded-xl bg-white px-2 py-2 text-xs font-bold text-[#b86e08] shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
        ),
        role="status",
        aria_label=ui("Your help request totals"),
        class_name="mt-3 grid grid-cols-3 w-full items-center gap-1 sm:gap-4",
    )


def own_request_summary(post: RecentPost) -> rx.Component:
    return rx.el.summary(
        avatar_with_tick(
            avatar_src(ProfileState.avatar_path, ProfileState.avatar_seed),
            AuthState.is_verified,
            "size-10 shrink-0 rounded-full object-cover",
            ui("Your profile photo"),
        ),
        rx.el.span(
            rx.el.span(
                AuthState.display_name,
                class_name="block text-sm font-bold text-[#111827]",
            ),
            rx.el.span(
                post["title"],
                class_name="block text-sm font-medium text-[#111827]",
            ),
            rx.el.span(
                post["location"], class_name="mt-1 block text-sm text-[#4b5563]"
            ),
            rx.el.span(
                post["status"],
                " · ",
                rx.cond(
                    post["helpers_needed"] == 1,
                    ui("1 person required"),
                    styled_count_template(
                        ui("{count} people required"),
                        post["helpers_needed"].to(int),
                    ),
                ),
                class_name="mt-1 block text-sm font-semibold text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1 break-words",
        ),
        disclosure_arrow(),
        class_name="flex w-full cursor-pointer list-none items-center gap-3 p-4 text-left hover:bg-[#f9fafb] focus-visible:outline-2 focus-visible:outline-[#e08b12] [&::-webkit-details-marker]:hidden",
    )


def own_request_body(post: RecentPost) -> rx.Component:
    return rx.el.div(
        corner_activity_dot(
            NotificationState.unread_help_post_ids.contains(post["id"]),
            ui("New activity on this help request"),
        ),
        browser_translatable_text(
            post["description"],
            class_name="text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.dl(
            plain_detail(
                ui("Date time and duration"), post["date_time_duration"]
            ),
            optional_plain_detail(
                ui("Where"), post["location"], ui("Location to agree")
            ),
            optional_plain_detail(
                ui("Tools"), post["tools"], ui("No tools listed")
            ),
            optional_plain_detail(
                ui("Knowledge and skills"),
                post["knowledge_skills"],
                ui("No special skills listed"),
            ),
            optional_plain_detail(
                ui("Exact meeting place"),
                post["accepted_location_name"],
                ui("Not shared yet"),
            ),
            class_name="mt-4 grid w-full grid-cols-1 gap-4 [&_dt]:text-sm [&_dt]:normal-case [&_dt]:tracking-normal [&_dd]:font-medium [&_dd]:text-[#4b5563]",
        ),
        rx.cond(
            post["photos"].length() > 0,
            rx.el.div(
                rx.foreach(post["photos"], square_photo_thumbnail),
                class_name="mt-4 grid grid-cols-4 sm:grid-cols-10 gap-1.5 w-full",
            ),
            rx.fragment(),
        ),
        owner_delete_footer(post),
        class_name="relative w-full bg-white",
    )


def own_request_record(post: RecentPost) -> rx.Component:
    return record_disclosure(
        own_request_summary(post),
        own_request_body(post),
        key=post["id"],
    )


def recent_requests_section() -> rx.Component:
    return inbox_style_shell(
        request_heading(
            "Your help requests",
            HelpPostState.counts["total"],
            "Requests you have already posted",
        ),
        counts_summary(),
        rx.cond(
            HelpHubState.removal_notice,
            rx.el.p(
                HelpHubState.removal_notice,
                role="status",
                class_name="mt-3 w-full rounded-2xl border border-[#fba922] bg-[#fff7e8] px-3 py-2 text-xs font-semibold text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpHubState.removal_error,
            rx.el.p(
                HelpHubState.removal_error,
                role="alert",
                class_name="mt-3 w-full rounded-2xl border border-[#f2bd5a] bg-[#fff7e8] px-3 py-2 text-xs font-semibold leading-relaxed text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpPostState.is_loading & ~HelpPostState.has_loaded,
            section_skeleton(),
            rx.cond(
                HelpPostState.recent_posts.length() > 0,
                rx.el.div(
                    rx.foreach(
                        HelpPostState.recent_posts,
                        own_request_record,
                    ),
                    class_name="gah-edge-stack mt-2 flex w-full flex-col gap-0",
                ),
                rx.fragment(),
            ),
        ),
    )


def help_summary_card(title: str, value: rx.Var[int]) -> rx.Component:
    template = rx.cond(
        title == "help given",
        rx.cond(
            value == 0,
            ui("{count} help given"),
            rx.cond(
                value == 1,
                ui("Helped {count} time"),
                ui("Helped {count} times"),
            ),
        ),
        rx.cond(
            value == 0,
            ui("{count} help received"),
            rx.cond(
                value == 1,
                ui("Received help {count} time"),
                ui("Received help {count} times"),
            ),
        ),
    )
    return rx.el.p(
        styled_count_template(template, value),
        class_name="w-full rounded-xl bg-white px-3 py-4 text-center text-base sm:text-lg font-bold leading-tight text-black shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
    )


def help_summary_row() -> rx.Component:
    """Compact help-given / help-received summary under Ask for Help."""
    return rx.el.div(
        help_summary_card(
            "help given",
            ProfileState.stats["tasks_helped"],
        ),
        help_summary_card(
            "help received",
            ProfileState.stats["tasks_received"],
        ),
        role="group",
        aria_label=ui("Your help summary"),
        class_name="grid grid-cols-2 gap-x-6 sm:gap-x-12 w-full bg-transparent",
    )


def help_hub_panel() -> rx.Component:
    return rx.el.div(
        post_help_section(),
        help_summary_row(),
        recent_requests_section(),
        upcoming_help_section(),
        upcoming_helpees_section(),
        others_events_section(),
        hosted_events_section(),
        saved_searches_section(),
        saved_requests_section(),
        on_mount=[
            HelpHubState.load_help_hub,
            HelpPostState.load_recent,
            SavedSearchState.load_alerts,
            BookmarkState.load_bookmarks,
            EventState.load_my_events,
        ],
        class_name="gah-requests-panel flex w-full min-w-0 flex-col gap-8 sm:gap-10 [&>section>div:first-child:has(>h3)]:mb-4 sm:[&>section>div:first-child:has(>h3)]:mb-5 [&>section>div:first-child>p]:mt-1.5 sm:[&>section>div:first-child>p]:mt-2 [&>section>p:first-of-type]:mt-1.5 sm:[&>section>p:first-of-type]:mt-2 [&>section>button_p]:mt-1.5 sm:[&>section>button_p]:mt-2",
    )
