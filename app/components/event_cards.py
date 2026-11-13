"""Shared community-event UI: calendar-led cards, composer and host queue.

These components are used by the Community › Events section and by the two
Help-page blocks (Others Events, Hosted Events). Nothing here imports the
Community or Help panels, so no circular import can appear.
"""

import reflex as rx

from app.interface_i18n import ui, ui_template
from app.avatars import animal_avatar

from app.components.disclosure import record_disclosure, record_summary
from app.components.request_heading import request_heading
from app.components.event_calendar import event_date_calendar
from app.components.geolocation import geolocation_request
from app.components.map_picker import map_picker
from app.components.notification_badge import corner_activity_dot
from app.states.notification_state import NotificationState

from app.components.feedback import (
    INPUT_CLASS,
    SELECT_CLASS,
    avatar_with_tick,
    error_banner,
    field_label,
    select_wrapper,
    success_banner,
)
from app.states.event_state import (
    EVENT_DISTANCE_HELP,
    EventCard,
    EventState,
    JoinRequestRow,
)
from app.states.auth_state import AuthState


def _avatar(path: rx.Var[str], seed: rx.Var[str]) -> rx.Var[str]:
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


# ---------------------------------------------------------------------------
# Calendar tile and status band
# ---------------------------------------------------------------------------


def date_tile(event: EventCard) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            event["month"],
            class_name="text-[10px] font-bold uppercase tracking-wide text-white/90",
        ),
        rx.el.span(
            event["day"],
            class_name="text-xl font-bold leading-none text-white",
        ),
        rx.el.span(
            event["weekday"],
            class_name="text-[10px] font-bold uppercase tracking-wide text-white/80",
        ),
        role="img",
        aria_label=event["date_label"],
        class_name="flex size-16 shrink-0 flex-col items-center justify-center gap-0.5 rounded-2xl bg-[#e08b12]",
    )


def status_band(event: EventCard) -> rx.Component:
    """Pending / confirmed / host band, always with the same geometry."""
    return rx.match(
        event["join_status"],
        (
            "pending",
            rx.el.p(
                rx.icon("hourglass", class_name="h-3.5 w-3.5"),
                ui("Request pending — the host will confirm or decline"),
                role="status",
                class_name="mt-3 flex w-full items-center gap-2 rounded-xl border border-[#d4d4d4] bg-[#fff7e8] px-3 py-2 text-[11px] font-bold text-[#e08b12]",
            ),
        ),
        (
            "confirmed",
            rx.el.p(
                rx.icon("circle-check-big", class_name="h-3.5 w-3.5"),
                ui("You are confirmed for this event"),
                role="status",
                class_name="mt-3 flex w-full items-center gap-2 rounded-xl border border-[#fba922] bg-[#fba922] px-3 py-2 text-[11px] font-bold text-[#111827]",
            ),
        ),
        (
            "declined",
            rx.el.p(
                rx.icon("circle-x", class_name="h-3.5 w-3.5"),
                ui("The host declined this request"),
                role="status",
                class_name="mt-3 flex w-full items-center gap-2 rounded-xl border border-[#f6c66f] bg-[#fff7e8] px-3 py-2 text-[11px] font-bold text-[#e08b12]",
            ),
        ),
        (
            "cancelled",
            rx.el.p(
                rx.icon("undo-2", class_name="h-3.5 w-3.5"),
                ui("You withdrew your request — you can ask again"),
                role="status",
                class_name="mt-3 flex w-full items-center gap-2 rounded-xl border border-[#d4d4d4] bg-[#ffffff] px-3 py-2 text-[11px] font-bold text-[#4b5563]",
            ),
        ),
        rx.fragment(),
    )


def event_meta(event: EventCard) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            rx.icon(event["type_icon"], class_name="h-3 w-3"),
            event["type_label"],
            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
        ),
        rx.el.span(
            rx.icon("clock", class_name="h-3 w-3"),
            event["time_label"],
            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
        ),
        rx.el.span(
            rx.icon("map-pin", class_name="h-3 w-3"),
            event["place"],
            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
        ),
        rx.el.span(
            rx.icon("users-round", class_name="h-3 w-3"),
            event["capacity_label"],
            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-2.5 py-1 text-[11px] font-bold text-[#111827]",
        ),
        rx.cond(
            event["distance_label"],
            rx.el.span(
                rx.icon("navigation", class_name="h-3 w-3"),
                event["distance_label"],
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 flex flex-wrap items-center gap-1.5",
    )


def host_row(event: EventCard) -> rx.Component:
    return rx.el.div(
        avatar_with_tick(
            _avatar(event["host_avatar"], event["host_avatar_seed"]),
            event["host_verified"],
            "size-9 rounded-full bg-[#fff7e8] object-cover",
            ui("Host photo"),
            member_id=event["host_id"],
        ),
        rx.el.div(
            rx.el.p(
                ui("Hosted by"),
                class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
            ),
            rx.el.p(
                event["host_name"],
                class_name="text-sm font-bold text-[#111827] leading-tight",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.cond(
            event["is_host"],
            rx.el.span(
                ui("You host this"),
                class_name="w-fit shrink-0 rounded-full bg-[#e08b12] px-2.5 py-1 text-[11px] font-bold text-white",
            ),
            rx.fragment(),
        ),
        class_name="mt-4 flex w-full items-center gap-2.5 rounded-2xl border border-[#f6c66f] bg-white px-3 py-2.5",
    )


def join_action(event: EventCard) -> rx.Component:
    """Join / withdraw affordance for non-hosts, disabled while working."""
    return rx.cond(
        event["is_host"],
        rx.fragment(),
        rx.el.div(
            rx.cond(
                event["can_join"],
                rx.el.button(
                    rx.cond(
                        EventState.busy_event_id == event["id"],
                        rx.spinner(class_name="h-4 w-4"),
                        rx.icon("user-round-plus", class_name="h-4 w-4"),
                    ),
                    ui("Join event"),
                    type="button",
                    aria_label=ui_template(
                        "Ask to join {title}", "title", event["title"]
                    ),
                    disabled=EventState.busy_event_id == event["id"],
                    on_click=lambda: EventState.request_to_join(event["id"]),
                    class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl bg-[#fba922] px-5 py-2.5 text-sm font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#111827]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                event["can_cancel"],
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    ui("Withdraw request"),
                    type="button",
                    aria_label=ui_template(
                        "Withdraw your request to join {title}",
                        "title",
                        event["title"],
                    ),
                    disabled=EventState.busy_event_id == event["id"],
                    on_click=lambda: EventState.cancel_join_request(
                        event["id"]
                    ),
                    class_name="w-full sm:w-fit flex items-center justify-center gap-1.5 rounded-xl border border-[#d4d4d4] bg-white px-4 py-2.5 text-xs font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                rx.fragment(),
            ),
            class_name="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full",
        ),
    )


def event_body(event: EventCard) -> rx.Component:
    return rx.fragment(
        rx.el.div(
            rx.foreach(
                event["photo_paths"],
                lambda path: rx.image(
                    src=rx.get_upload_url(path),
                    alt=ui("Event photo"),
                    class_name="h-36 w-full rounded-2xl bg-[#fff7e8] object-cover",
                ),
            ),
            class_name="mt-3 grid w-full grid-cols-2 gap-2",
        ),
        rx.cond(
            event["reward_details"],
            rx.el.p(
                ui("Reward / what is provided:"),
                rx.el.span(event["reward_details"]),
                class_name="mt-3 whitespace-pre-line text-sm font-medium text-[#4b5563]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            event["details"],
            rx.el.p(
                event["details"],
                class_name="mt-3 text-sm font-medium leading-relaxed text-[#4b5563] whitespace-pre-line",
            ),
            rx.fragment(),
        ),
        host_row(event),
        status_band(event),
        join_action(event),
    )


def request_event_summary(event: EventCard) -> rx.Component:
    return record_summary(
        date_tile(event),
        event["title"],
        f"{event['date_label']} · {event['time_label']} · {event['place']}",
        f"{event['capacity_label']} · {rx.cond(event['is_host'], ui('You host this'), event['status_label'])}",
    )


def request_event_body(event: EventCard) -> rx.Component:
    return rx.el.div(event_meta(event), event_body(event), class_name="w-full")


def others_event_record(event: EventCard, **props) -> rx.Component:
    return record_disclosure(
        request_event_summary(event),
        request_event_body(event),
        **props,
    )


def event_card(event: EventCard, **props) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            date_tile(event),
            rx.el.div(
                rx.el.h3(
                    rx.el.button(
                        event["title"],
                        type="button",
                        aria_label=ui_template(
                            "Open event {title}", "title", event["title"]
                        ),
                        on_click=lambda: EventState.select_event(event["id"]),
                        class_name="gah-segment-control rounded-lg bg-transparent text-left text-[#111827] hover:text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#fba922]",
                    ),
                    class_name="text-base font-bold leading-snug text-[#111827]",
                ),
                rx.el.p(
                    event["date_label"],
                    class_name="mt-1 text-xs font-semibold text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex w-full items-start gap-3",
        ),
        event_meta(event),
        event_body(event),
        **props,
        dir=AuthState.interface_direction,
        class_name="flex w-full flex-col rounded-none border-0 bg-white p-5",
    )


# ---------------------------------------------------------------------------
# Host queue
# ---------------------------------------------------------------------------


def request_person(row: JoinRequestRow) -> rx.Component:
    return rx.el.div(
        avatar_with_tick(
            _avatar(row["member_avatar"], row["member_avatar_seed"]),
            row["member_verified"],
            "size-10 rounded-full bg-[#fff7e8] object-cover",
            ui("Member photo"),
            member_id=row["member_id"],
        ),
        rx.el.div(
            rx.el.p(
                row["member_name"],
                class_name="text-sm font-bold text-[#111827] leading-tight",
            ),
            rx.el.p(
                row["event_title"],
                class_name="mt-0.5 text-[11px] font-semibold text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.span(
            row["created"],
            class_name="w-fit shrink-0 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#4b5563]",
        ),
        class_name="flex w-full items-start gap-3",
    )


def pending_request_card(row: JoinRequestRow, **props) -> rx.Component:
    return rx.el.article(
        request_person(row),
        rx.cond(
            row["note"],
            rx.el.p(
                f"“{row['note']}”",
                class_name="mt-3 text-sm font-medium italic leading-relaxed text-[#4b5563]",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    EventState.busy_request_id == row["id"],
                    rx.spinner(class_name="h-4 w-4"),
                    rx.icon("circle-check-big", class_name="h-4 w-4"),
                ),
                ui("Confirm"),
                type="button",
                aria_label=ui_template(
                    "Confirm {name} for this event", "name", row["member_name"]
                ),
                disabled=EventState.busy_request_id == row["id"],
                on_click=lambda: EventState.confirm_request(row["id"]),
                class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            rx.el.button(
                rx.icon("circle-x", class_name="h-4 w-4"),
                ui("Decline"),
                type="button",
                aria_label=ui_template(
                    "Decline {name} for this event", "name", row["member_name"]
                ),
                disabled=EventState.busy_request_id == row["id"],
                on_click=lambda: EventState.decline_request(row["id"]),
                class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-5 py-2.5 text-sm font-bold text-[#4b5563] transition-colors hover:bg-[#fff7e8] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full",
        ),
        **props,
        dir=AuthState.interface_direction,
        class_name="flex w-full flex-col rounded-none border-0 bg-[#ffffff] p-4",
    )


def confirmed_attendee_card(row: JoinRequestRow, **props) -> rx.Component:
    return rx.el.article(
        request_person(row),
        rx.el.div(
            rx.el.span(
                rx.icon("circle-check-big", class_name="h-3 w-3"),
                ui("Confirmed attendee"),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-2.5 py-1 text-[11px] font-bold text-[#111827]",
            ),
            rx.el.button(
                rx.icon("user-round-minus", class_name="h-3.5 w-3.5"),
                ui("Remove"),
                type="button",
                aria_label=ui_template(
                    "Remove {name} from this event", "name", row["member_name"]
                ),
                disabled=EventState.busy_request_id == row["id"],
                on_click=lambda: EventState.decline_request(row["id"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3 py-1.5 text-[11px] font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        **props,
        class_name="flex w-full flex-col rounded-none border-0 bg-[#ffffff] p-4",
    )


# ---------------------------------------------------------------------------
# Plan an event composer
# ---------------------------------------------------------------------------


def type_choice(item: dict[str, str]) -> rx.Component:
    return rx.el.option(item["label"], value=item["value"])


def event_detail_sheet() -> rx.Component:
    return rx.cond(
        EventState.localized_selected_event,
        rx.el.section(
            rx.el.button(
                rx.icon("x", class_name="h-4 w-4"),
                ui("Close event"),
                type="button",
                on_click=EventState.clear_event_selection,
                class_name="mb-3 ml-auto flex w-fit items-center gap-2 rounded-full bg-[#e08b12] px-3 py-2 text-xs font-bold text-white hover:bg-[#b86e08]",
            ),
            error_banner(EventState.localized_feedback["error"]),
            success_banner(EventState.localized_feedback["success"]),
            rx.foreach(EventState.localized_selected_event, event_card),
            role="dialog",
            aria_label=ui("Event details"),
            dir=AuthState.interface_direction,
            class_name="fixed top-0 right-0 z-40 w-full max-w-[22rem] sm:max-w-[26rem] max-h-[calc(100dvh-3.875rem-env(safe-area-inset-bottom))] overflow-y-auto overscroll-contain rounded-none rounded-bl-2xl bg-white p-3 text-[#111827]",
        ),
        rx.fragment(),
    )


def planner_field(
    label: str | rx.Var[str],
    field_id: str,
    control: rx.Component,
    hint: str | rx.Var[str] = "",
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=field_id,
            class_name="mb-2 block text-sm font-semibold text-[#111827]",
        ),
        control,
        rx.cond(
            hint,
            rx.el.p(hint, class_name="mt-2 text-xs font-medium text-[#4b5563]"),
            rx.fragment(),
        ),
        class_name="w-full rounded-2xl bg-[#fffaf2] p-4 sm:p-5",
    )


def event_photo_tile(path: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.image(
            src=rx.get_upload_url(path),
            alt=ui("Attached event photo"),
            class_name="aspect-square w-full rounded-2xl bg-[#fff7e8] object-cover",
        ),
        rx.el.button(
            rx.icon("x", class_name="size-4"),
            type="button",
            aria_label=ui("Remove event photo"),
            on_click=lambda: EventState.remove_photo(path),
            disabled=EventState.photo_busy | EventState.is_saving,
            class_name="absolute right-1 top-1 flex size-8 items-center justify-center rounded-full bg-white text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#fba922] disabled:opacity-50",
        ),
        key=path,
        class_name="relative w-full",
    )


def event_photo_upload() -> rx.Component:
    return rx.el.section(
        rx.el.h3(
            ui("Upload Photos"),
            id="event-photo-label",
            class_name="text-sm font-semibold text-[#111827]",
        ),
        rx.el.p(
            ui(
                "Optional · up to 5 static JPEG, PNG or WebP photos · 3 MB per source photo. Avoid addresses or private information in photos."
            ),
            class_name="mt-1 text-xs font-medium text-[#4b5563]",
        ),
        rx.upload.root(
            rx.el.button(
                rx.icon("camera", class_name="size-6 text-[#e08b12]"),
                rx.cond(
                    EventState.photo_busy,
                    ui("Processing photos…"),
                    ui("Choose or drop photos"),
                ),
                type="button",
                disabled=EventState.photo_busy
                | EventState.is_saving
                | (EventState.pending_photo_paths.length() >= 5),
                on_click=rx.call_script(
                    "document.querySelector('#event-photos input[type=file]')?.click()"
                ).stop_propagation,
                class_name="flex min-h-28 w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[#fba922] bg-white p-4 text-sm font-semibold text-[#111827] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#fba922] disabled:opacity-50",
            ),
            id="event-photos",
            accept={
                "image/jpeg": [".jpg", ".jpeg"],
                "image/png": [".png"],
                "image/webp": [".webp"],
            },
            multiple=True,
            max_files=5,
            max_size=3_000_000,
            disabled=EventState.photo_busy
            | EventState.is_saving
            | (EventState.pending_photo_paths.length() >= 5),
            on_drop=EventState.handle_upload(
                rx.upload_files(upload_id="event-photos")
            ),
            class_name="mt-3 w-full",
        ),
        error_banner(EventState.localized_feedback["photo_error"]),
        rx.el.p(
            ui_template(
                "{count} / 5 attached",
                "count",
                EventState.pending_photo_paths.length().to_string(),
            ),
            role="status",
            class_name="mt-2 text-xs font-semibold text-[#b86e08]",
        ),
        rx.el.div(
            rx.foreach(EventState.pending_photo_paths, event_photo_tile),
            class_name="mt-2 grid w-full grid-cols-2 gap-2 sm:grid-cols-5",
        ),
        aria_labelledby="event-photo-label",
        class_name="w-full rounded-2xl bg-[#fffaf2] p-4 sm:p-5",
    )


def event_reward_fields() -> rx.Component:
    return rx.el.section(
        planner_field(
            ui("Reward / what is provided"),
            "event-reward-choice",
            select_wrapper(
                rx.el.select(
                    rx.el.option(ui("No reward selected (optional)"), value=""),
                    rx.foreach(
                        EventState.localized_reward_choices, type_choice
                    ),
                    id="event-reward-choice",
                    value=EventState.reward_choice,
                    on_change=EventState.set_reward_choice,
                    disabled=EventState.is_saving,
                    class_name=SELECT_CLASS,
                )
            ),
        ),
        rx.el.div(
            planner_field(
                ui("Currency"),
                "event-currency",
                select_wrapper(
                    rx.el.select(
                        rx.foreach(EventState.currency_options, type_choice),
                        id="event-currency",
                        value=EventState.reward_currency,
                        on_change=EventState.set_reward_currency,
                        disabled=EventState.is_saving,
                        class_name=SELECT_CLASS,
                    )
                ),
            ),
            rx.el.button(
                rx.icon(
                    rx.cond(
                        EventState.budget_quote_allowed,
                        "square-check",
                        "square",
                    ),
                    class_name="size-4 shrink-0 text-[#e08b12]",
                ),
                ui("Ask for a Helper quote"),
                type="button",
                role="checkbox",
                aria_checked=EventState.budget_quote_allowed,
                on_click=EventState.toggle_budget_quote,
                disabled=EventState.is_saving,
                class_name="flex min-h-11 w-full items-center gap-2 rounded-xl bg-[#fff7e8] px-4 py-3 text-sm font-semibold text-[#111827] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            rx.el.div(
                planner_field(
                    ui("Enter your budget"),
                    "event-money-budget",
                    rx.el.input(
                        id="event-money-budget",
                        name="money_budget",
                        input_mode="decimal",
                        placeholder=ui("For example: 25.00"),
                        max_length=11,
                        disabled=(EventState.reward_choice != "money")
                        | EventState.budget_quote_allowed,
                        class_name=INPUT_CLASS,
                    ),
                    ui(
                        "Positive amount · up to two decimal places, or ask for a quote."
                    ),
                ),
                class_name=rx.cond(
                    EventState.budget_quote_allowed, "hidden", "w-full"
                ),
            ),
            class_name=rx.cond(
                EventState.reward_choice == "money",
                "flex w-full flex-col gap-3 text-[#111827]",
                "hidden",
            ),
        ),
        rx.el.div(
            planner_field(
                rx.cond(
                    EventState.reward_choice == "other_reward",
                    ui("Describe your Other reward (required)"),
                    ui("Reward details (optional)"),
                ),
                "event-reward",
                rx.el.textarea(
                    id="event-reward",
                    name="reward_details",
                    max_length=900,
                    rows="3",
                    required=EventState.reward_choice == "other_reward",
                    disabled=EventState.reward_choice == "",
                    placeholder=ui("Describe what helpers will receive"),
                    class_name=INPUT_CLASS,
                ),
                ui(
                    "Share exact meeting details privately with confirmed helpers."
                ),
            ),
            class_name=rx.cond(
                EventState.reward_choice != "", "w-full", "hidden"
            ),
        ),
        class_name="flex w-full flex-col gap-3",
    )


def event_composer() -> rx.Component:
    return rx.el.form(
        error_banner(EventState.localized_feedback["error"]),
        planner_field(
            ui("Event heading"),
            "event-title",
            rx.el.input(
                id="event-title",
                name="title",
                required=True,
                max_length=160,
                auto_focus=True,
                placeholder=ui("Give your event a clear title"),
                class_name=INPUT_CLASS,
            ),
            ui("Required · up to 160 characters"),
        ),
        planner_field(
            ui("Description"),
            "event-details",
            rx.el.textarea(
                id="event-details",
                name="details",
                required=True,
                rows="5",
                placeholder=ui(
                    "What will helpers do? What should they expect or bring?"
                ),
                class_name="w-full resize-y rounded-xl border border-[#f7d9a0] bg-white px-4 py-3 text-sm font-medium leading-relaxed text-[#111827] focus-visible:outline-2 focus-visible:outline-[#fba922]",
            ),
            ui("Required · up to 2000 words"),
        ),
        rx.el.div(
            planner_field(
                ui("Starts"),
                "event-start",
                rx.el.input(
                    id="event-start",
                    name="starts_at",
                    type="datetime-local",
                    required=True,
                    class_name=INPUT_CLASS,
                ),
                ui("UTC · a future date within two years"),
            ),
            planner_field(
                ui("Ends"),
                "event-end",
                rx.el.input(
                    id="event-end",
                    name="ends_at",
                    type="datetime-local",
                    class_name=INPUT_CLASS,
                ),
                ui("Optional · not before the start"),
            ),
            class_name="grid w-full grid-cols-1 gap-4 sm:grid-cols-2",
        ),
        planner_field(
            ui("Job category"),
            "event-category",
            select_wrapper(
                rx.el.select(
                    rx.foreach(EventState.localized_type_options, type_choice),
                    id="event-category",
                    name="event_type",
                    required=True,
                    default_value=EventState.event_type_draft,
                    key=EventState.event_type_draft,
                    class_name=SELECT_CLASS,
                )
            ),
        ),
        planner_field(
            ui("Number of helpers"),
            "event-helpers",
            select_wrapper(
                rx.el.select(
                    rx.foreach(
                        EventState.helper_options,
                        lambda number: rx.el.option(
                            number, value=number.to_string()
                        ),
                    ),
                    id="event-helpers",
                    name="capacity",
                    required=True,
                    default_value="1",
                    class_name=SELECT_CLASS,
                )
            ),
        ),
        event_photo_upload(),
        planner_field(
            ui("Approximate place"),
            "event-place",
            rx.el.input(
                id="event-place",
                name="place_name",
                max_length=200,
                placeholder=ui("Near the park or market square"),
                class_name=INPUT_CLASS,
            ),
            ui(
                "Never enter an exact address. Drop a private pin below; only an approximate public area is saved. Without a pin, your profile's coarse area is used."
            ),
        ),
        rx.el.section(
            rx.el.h3(
                ui("Location of this event"),
                class_name="text-sm font-semibold text-[#111827]",
            ),
            rx.el.p(
                ui(
                    "Tap the map or use your current location. The exact pin stays private; public maps show only an approximate location."
                ),
                class_name="mt-2 text-xs font-medium text-[#4b5563]",
            ),
            map_picker(
                "event-planner",
                ui("Location of this event"),
                inline=True,
                show_label=ui("Use map pin"),
                hide_label=ui("Hide map pin"),
                instructions=ui(
                    "Drag the pin or tap the map to place the exact point. It stays private: public maps only show an approximate area."
                ),
                clear_label=ui("Clear pin"),
                finding_label=ui("Finding you…"),
                locate_label=ui("Use my current location"),
                status_text=EventState.localized_feedback["map_status"],
                error_text=EventState.localized_feedback["map_error"],
            ),
            class_name="w-full rounded-2xl bg-[#fffaf2] px-5 py-4 sm:px-6 sm:py-5",
        ),
        rx.el.div(
            planner_field(
                ui("City"),
                "event-city",
                rx.el.input(
                    id="event-city",
                    name="city",
                    required=True,
                    max_length=120,
                    placeholder=ui("City or town"),
                    class_name=INPUT_CLASS,
                ),
            ),
            planner_field(
                ui("Country"),
                "event-country",
                rx.el.input(
                    id="event-country",
                    name="country",
                    max_length=120,
                    placeholder=ui("Country"),
                    class_name=INPUT_CLASS,
                ),
                ui("Optional"),
            ),
            class_name="grid w-full grid-cols-1 gap-4 sm:grid-cols-2",
        ),
        event_reward_fields(),
        rx.el.button(
            rx.icon("calendar-plus", class_name="size-4"),
            rx.cond(
                EventState.is_saving,
                ui("Publishing your event…"),
                ui("Publish event"),
            ),
            type="submit",
            disabled=EventState.is_saving | EventState.photo_busy,
            class_name="gah-orange-control flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[#fba922] px-6 py-3 text-sm font-bold text-[#111827] hover:bg-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12] disabled:opacity-50",
        ),
        on_submit=EventState.create_event,
        reset_on_submit=False,
        class_name="mx-auto flex w-full max-w-3xl flex-col gap-4 pb-8",
    )


def event_planner_screen() -> rx.Component:
    return rx.el.section(
        rx.el.header(
            rx.el.button(
                rx.icon("arrow-left", class_name="size-5"),
                ui("Back"),
                type="button",
                aria_label=ui("Back to Events"),
                on_click=EventState.close_composer,
                disabled=EventState.is_saving | EventState.photo_busy,
                class_name="gah-close-back flex min-h-11 items-center gap-2 rounded-full bg-[#fff7e8] px-4 text-sm font-bold text-[#b86e08] disabled:opacity-50",
            ),
            rx.el.h2(
                ui("Plan an event"),
                id="event-planner-heading",
                class_name="text-center text-xl font-bold text-[#111827] sm:text-2xl",
            ),
            rx.el.button(
                rx.icon("x", class_name="size-5"),
                type="button",
                id="gah-event-planner-close",
                aria_label=ui("Close event planner"),
                on_click=EventState.close_composer,
                disabled=EventState.is_saving | EventState.photo_busy,
                class_name="flex size-11 items-center justify-center rounded-full bg-[#fff7e8] text-[#b86e08] disabled:opacity-50",
            ),
            class_name="flex shrink-0 items-center justify-between gap-3 border-b border-[#f7d9a0] bg-white px-4 py-3 sm:px-6",
        ),
        rx.el.div(
            rx.el.p(
                ui(
                    "Bring helping hands together. Planning and joining events is free."
                ),
                class_name="mx-auto mb-5 w-full max-w-3xl text-sm font-medium text-[#4b5563]",
            ),
            event_composer(),
            class_name="min-h-0 w-full flex-1 overflow-y-auto overscroll-contain px-4 py-5 pb-[calc(2rem+env(safe-area-inset-bottom))] sm:px-6",
        ),
        id="event-planner-screen",
        role="dialog",
        aria_modal=True,
        aria_labelledby="event-planner-heading",
        on_mount=rx.call_script("""requestAnimationFrame(() => {
            const screen = document.getElementById('event-planner-screen');
            if (!screen) return;
            const previous = document.activeElement;
            screen.querySelector('#event-title')?.focus();
            const trap = e => {
                if (e.key === 'Escape') { screen.querySelector('#gah-event-planner-close')?.click(); return; }
                if (e.key !== 'Tab') return;
                const items = [...screen.querySelectorAll('button:not(:disabled),input:not(:disabled):not([type=file]),textarea,select')];
                const first = items[0], last = items[items.length - 1];
                if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
                else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
            };
            screen.addEventListener('keydown', trap);
            window.gahEventPlannerCleanup = () => { screen.removeEventListener('keydown', trap); previous?.focus(); };
        });"""),
        on_unmount=rx.call_script(
            "window.gahEventPlannerCleanup?.(); delete window.gahEventPlannerCleanup;"
        ),
        dir=AuthState.interface_direction,
        class_name="fixed inset-0 z-[60] flex h-dvh w-full flex-col overflow-hidden bg-white font-['Inter'] text-[#111827]",
    )


def planner_control() -> rx.Component:
    return rx.el.button(
        rx.icon("calendar-plus", class_name="h-4 w-4 shrink-0 text-[#fba922]"),
        ui("Plan an event"),
        type="button",
        aria_label=ui("Plan an event"),
        aria_expanded=EventState.composer_open,
        on_click=EventState.toggle_composer,
        class_name="gah-primary-outline w-fit shrink-0 flex items-center gap-1.5 whitespace-normal rounded-full border border-[#fba922] bg-white px-3 py-1.5 text-xs font-bold text-black transition-colors hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def discovery_event_list(
    show_empty: bool | rx.Var[bool] = False,
) -> rx.Component:
    return rx.el.section(
        rx.cond(
            EventState.localized_events.length() > 0,
            rx.fragment(
                rx.el.h2(
                    ui("Events"),
                    class_name="mb-3 text-xl font-bold text-[#111827]",
                ),
                rx.el.div(
                    rx.foreach(
                        EventState.localized_events,
                        lambda event: rx.el.div(
                            rx.el.button(
                                rx.icon(
                                    "calendar-days",
                                    class_name="size-4 text-[#b86e08]",
                                ),
                                ui("Open event details"),
                                type="button",
                                aria_label=ui_template(
                                    "Open event {title}",
                                    "title",
                                    event["title"],
                                ),
                                on_click=lambda: EventState.select_event(
                                    event["id"]
                                ),
                                class_name="flex min-h-11 w-full items-center gap-2 bg-[#fff7e8] px-5 text-sm font-bold text-[#111827] hover:bg-[#fff0d6] focus-visible:ring-2 focus-visible:ring-[#fba922]",
                            ),
                            event_card(event),
                            key=event["id"],
                            class_name="w-full bg-white",
                        ),
                    ),
                    class_name="gah-edge-stack flex w-full flex-col",
                ),
            ),
            rx.cond(
                show_empty,
                events_empty(
                    ui("No events match your filters"),
                    ui(
                        "Try clearing the Events filter or adjusting your search to see more."
                    ),
                ),
                rx.fragment(),
            ),
        ),
        dir=AuthState.interface_direction,
        class_name="w-full bg-white",
    )


def events_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-44 w-full rounded-3xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-44 w-full rounded-3xl bg-[#e5e5e5]"
        ),
        class_name="gah-edge-stack mt-4 flex flex-col gap-0 w-full",
    )


def events_empty(
    title: str | rx.Var[str], body: str | rx.Var[str]
) -> rx.Component:
    return rx.el.div(
        rx.icon("calendar", class_name="h-6 w-6 text-[#fba922] mb-2"),
        rx.el.p(ui(title), class_name="text-sm font-bold text-[#111827]"),
        rx.el.p(
            ui(body),
            class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        class_name="gah-edge-stack mt-4 flex flex-col gap-0 items-center justify-center text-center w-full bg-white px-6 py-12",
    )


# ---------------------------------------------------------------------------
# Community › Events section
# ---------------------------------------------------------------------------


def planner_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            corner_activity_dot(
                NotificationState.events_unread > 0, ui("Unread event activity")
            ),
            class_name="relative w-full",
        ),
        rx.el.div(
            planner_control(),
            rx.el.p(
                ui("Plan and join events for free"),
                class_name="min-w-0 text-center text-sm font-medium text-[#404040]",
            ),
            class_name="flex w-full flex-col items-center justify-center gap-2 text-center",
        ),
        rx.cond(
            AuthState.is_signed_in & EventState.composer_open,
            event_planner_screen(),
            rx.fragment(),
        ),
        class_name="w-full bg-transparent px-5 pb-3 sm:px-6",
    )


def events_location_control() -> rx.Component:
    return rx.el.div(
        rx.cond(
            EventState.events_geo_busy,
            geolocation_request(
                request_token=EventState.events_geo_token,
                on_position=EventState.events_position_found,
                on_error=EventState.events_position_failed,
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.span(
                ui("Enable my location"),
                id="gah-events-location-label",
                class_name="text-sm font-semibold text-[#111827]",
            ),
            rx.el.button(
                rx.el.span(
                    class_name=rx.cond(
                        EventState.events_location_on,
                        "block size-5 translate-x-5 rounded-full bg-white transition-transform motion-reduce:transition-none",
                        "block size-5 translate-x-0 rounded-full bg-white transition-transform motion-reduce:transition-none",
                    ),
                ),
                type="button",
                role="switch",
                aria_label=ui("Enable my location"),
                aria_labelledby="gah-events-location-label",
                aria_describedby="gah-events-location-help",
                aria_checked=rx.cond(
                    EventState.events_location_on, "true", "false"
                ),
                on_click=EventState.toggle_events_location,
                class_name=rx.cond(
                    EventState.events_location_on,
                    "gah-segment-control flex h-8 w-12 shrink-0 items-center rounded-full bg-[#fba922] p-1 text-[#111827] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12]",
                    "gah-segment-control flex h-8 w-12 shrink-0 items-center rounded-full bg-[#6b7280] p-1 text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12]",
                ),
            ),
            class_name="flex min-h-11 w-full items-center justify-between gap-3",
        ),
        rx.el.p(
            ui(
                "Uses your shared map location, or a private browser fix for Events only. This switch never changes your map visibility."
            ),
            id="gah-events-location-help",
            class_name="mt-1 text-xs font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.cond(
            EventState.events_geo_busy,
            rx.el.p(
                ui("Finding your location…"),
                role="status",
                class_name="mt-2 text-xs font-medium text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            EventState.events_location_error,
            rx.el.p(
                EventState.localized_feedback["location_error"],
                role="alert",
                class_name="mt-2 text-xs font-semibold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 w-full border-t border-[#f7d9a0] pt-3",
    )


def event_distance_control() -> rx.Component:
    """Accessible `Event distance` slider for cross-border event discovery."""
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                ui("Event distance"),
                html_for="gah-event-distance",
                class_name="text-center text-xl font-bold leading-tight text-[#111827] sm:text-2xl",
            ),
            rx.el.span(
                EventState.event_distance_label,
                role="status",
                class_name="w-fit rounded-full border border-[#e08b12] bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-black",
            ),
            class_name="flex w-full flex-wrap items-center justify-center gap-2",
        ),
        rx.el.input(
            id="gah-event-distance",
            type="range",
            min="1",
            max="1000",
            step="1",
            default_value=EventState.event_distance_km.to_string(),
            key=EventState.distance_slider_reset.to_string(),
            aria_label=ui("Event distance in kilometres"),
            aria_valuetext=EventState.event_distance_label,
            on_change=EventState.set_event_distance_km.throttle(100),
            style={
                "--distance-progress": f"{(EventState.event_distance_km - 1) / 999 * 100:.2f}%"
            },
            class_name="gah-distance-range mt-2 h-6 w-full appearance-none bg-transparent accent-[#fba922]",
        ),
        rx.el.div(
            rx.el.span(
                "1 km", class_name="text-xs font-semibold text-[#4b5563]"
            ),
            rx.el.button(
                "1000 km+",
                type="button",
                aria_label=ui("Show events up to 1000 kilometres away"),
                aria_pressed=EventState.event_distance_km >= 1000,
                on_click=EventState.select_max_event_distance,
                class_name="w-fit min-h-10 rounded-lg border border-[#e5e7eb] bg-white px-3 py-2 text-xs font-bold text-[#b86e08] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="mt-1 flex w-full items-center justify-between gap-3",
        ),
        events_location_control(),
        class_name="mt-3 w-full rounded-2xl border border-[#e5e7eb] bg-white p-3 shadow-sm",
    )


def events_feed() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    rx.cond(
                        EventState.localized_events.length() > 0,
                        rx.el.span(
                            EventState.localized_events.length(),
                            " ",
                            class_name="text-[#e08b12]",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        EventState.localized_events.length() == 1,
                        ui("Upcoming event"),
                        ui("Upcoming events"),
                    ),
                    class_name="w-full text-center text-xl sm:text-2xl font-bold tracking-tight text-black leading-tight",
                ),
                class_name="relative flex w-full items-center px-10",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                    type="button",
                    aria_label=ui("Refresh events"),
                    on_click=EventState.load_events,
                    class_name="flex items-center justify-center size-8 rounded-full border border-[#d4d4d4] bg-white text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                class_name="absolute right-0 top-1/2 -translate-y-1/2 flex items-center gap-2",
            ),
            class_name="relative flex min-h-8 items-center w-full",
        ),
        event_date_calendar(),
        event_distance_control(),
        rx.el.div(
            rx.cond(
                EventState.is_loading & ~EventState.has_loaded,
                events_skeleton(),
                rx.cond(
                    EventState.localized_events.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            EventState.localized_events,
                            lambda item: event_card(item, key=item["id"]),
                        ),
                        class_name="gah-edge-stack flex flex-col gap-0 w-full",
                    ),
                    events_empty(
                        ui("No events on the board yet"),
                        ui(
                            "When a member plans a gathering or a teamwork event near you, it will show up here with its date and place."
                        ),
                    ),
                ),
            ),
            class_name="w-full bg-transparent",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def host_queue_block() -> rx.Component:
    """Pending join requests for the events this member hosts."""
    return rx.cond(
        EventState.localized_hosted_events.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "clipboard-check", class_name="h-4 w-4 text-[#e08b12]"
                    ),
                    rx.el.h3(
                        ui("Requests to join your events"),
                        class_name="text-sm font-bold text-[#111827]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.span(
                    EventState.localized_pending_count_label,
                    class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
                ),
                class_name="flex flex-wrap items-center justify-between gap-3 w-full",
            ),
            rx.cond(
                EventState.is_loading_mine & ~EventState.has_loaded_mine,
                events_skeleton(),
                rx.cond(
                    EventState.localized_hosted_pending.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            EventState.localized_hosted_pending,
                            lambda row: pending_request_card(
                                row, key=row["id"]
                            ),
                        ),
                        class_name="gah-edge-stack mt-4 flex flex-col gap-0 w-full",
                    ),
                    events_empty(
                        ui("No requests waiting"),
                        ui(
                            "Every join request for your events lands here for you to confirm or decline."
                        ),
                    ),
                ),
            ),
            class_name="w-full bg-transparent",
        ),
        rx.fragment(),
    )


def events_section() -> rx.Component:
    return rx.el.div(
        error_banner(EventState.localized_feedback["error"]),
        success_banner(EventState.localized_feedback["success"]),
        planner_block(),
        host_queue_block(),
        events_feed(),
        event_detail_sheet(),
        on_mount=[
            EventState.load_events,
            EventState.load_my_events,
        ],
        dir=AuthState.interface_direction,
        class_name="flex flex-col gap-5 w-full",
    )


# ---------------------------------------------------------------------------
# Help page blocks
# ---------------------------------------------------------------------------


def _help_shell(*children) -> rx.Component:
    return rx.el.section(
        *children, class_name="w-full bg-transparent [&_.gah-edge-stack]:mt-2"
    )


def _help_heading(
    icon: str, title: str, count: rx.Var[int], subtitle: str = ""
) -> rx.Component:
    return request_heading(title, count, subtitle, icon)


def others_events_section() -> rx.Component:
    """Events hosted by other members where this member is confirmed."""
    return _help_shell(
        _help_heading(
            "calendar-check",
            ui("Events"),
            EventState.localized_joined_events.length(),
            ui("Join many helping hands"),
        ),
        rx.cond(
            EventState.is_loading_mine & ~EventState.has_loaded_mine,
            events_skeleton(),
            rx.cond(
                EventState.localized_joined_events.length() > 0,
                rx.el.div(
                    rx.foreach(
                        EventState.localized_joined_events,
                        lambda item: others_event_record(item, key=item["id"]),
                    ),
                    class_name="gah-edge-stack mt-2 flex flex-col gap-0 w-full",
                ),
                rx.fragment(),
            ),
        ),
    )


def hosted_event_block(event: EventCard, **props) -> rx.Component:
    return record_disclosure(
        request_event_summary(event),
        hosted_event_body(event),
        **props,
    )


def hosted_event_body(event: EventCard, **props) -> rx.Component:
    """One hosted event with its own pending queue and attendee list."""
    return rx.el.div(
        request_event_body(event),
        rx.el.div(
            rx.el.p(
                ui("Requests for this event"),
                class_name="text-[11px] font-bold uppercase tracking-wide text-[#4b5563]",
            ),
            rx.cond(
                EventState.localized_hosted_pending.length() > 0,
                rx.el.div(
                    rx.foreach(
                        EventState.localized_hosted_pending,
                        lambda row: rx.cond(
                            row["event_id"] == event["id"],
                            pending_request_card(row),
                            rx.fragment(),
                        ),
                    ),
                    class_name="gah-edge-stack mt-2 flex flex-col gap-0 w-full",
                ),
                rx.el.p(
                    ui("No requests waiting for this event."),
                    class_name="mt-2 text-xs font-medium text-[#4b5563]",
                ),
            ),
            rx.el.p(
                ui("Confirmed attendees"),
                class_name="mt-4 text-[11px] font-bold uppercase tracking-wide text-[#4b5563]",
            ),
            rx.cond(
                EventState.localized_hosted_confirmed.length() > 0,
                rx.el.div(
                    rx.foreach(
                        EventState.localized_hosted_confirmed,
                        lambda row: rx.cond(
                            row["event_id"] == event["id"],
                            confirmed_attendee_card(row),
                            rx.fragment(),
                        ),
                    ),
                    class_name="gah-edge-stack mt-2 flex flex-col gap-0 w-full",
                ),
                rx.el.p(
                    ui("Nobody is confirmed for this event yet."),
                    class_name="mt-2 text-xs font-medium text-[#4b5563]",
                ),
            ),
            class_name="mt-3 w-full rounded-2xl border border-[#f6c66f] bg-white p-4",
        ),
        **props,
        dir=AuthState.interface_direction,
        class_name="flex w-full flex-col",
    )


def hosted_events_section() -> rx.Component:
    """Events this member created, with the host decision controls."""
    return _help_shell(
        _help_heading(
            "calendar-days",
            ui("Hosted events"),
            EventState.localized_hosted_events.length(),
            ui("Manage helpers for your event"),
        ),
        error_banner(EventState.localized_feedback["error"]),
        success_banner(EventState.localized_feedback["success"]),
        rx.cond(
            EventState.is_loading_mine & ~EventState.has_loaded_mine,
            events_skeleton(),
            rx.cond(
                EventState.localized_hosted_events.length() > 0,
                rx.el.div(
                    rx.foreach(
                        EventState.localized_hosted_events,
                        lambda item: hosted_event_block(item, key=item["id"]),
                    ),
                    class_name="gah-edge-stack mt-2 flex flex-col gap-0 w-full",
                ),
                rx.fragment(),
            ),
        ),
    )
