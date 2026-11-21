"""Saved search alerts and bookmarked help requests, shown inside My requests."""

import reflex as rx

from app.interface_i18n import ui, ui_template

from app.components.disclosure import record_disclosure, record_summary
from app.components.request_heading import request_heading
from app.states.bookmark_state import BookmarkState, SavedRequest
from app.states.saved_search_state import SavedAlert, SavedSearchState


def _tile(icon: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-5 w-5 text-[#b86e08]"),
        class_name="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8]",
    )


def _heading(
    icon: str, title: str, count: rx.Var[int], subtitle: str = ""
) -> rx.Component:
    return request_heading(title, count, subtitle, icon)


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-20 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-20 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        class_name="gah-edge-stack mt-2 flex w-full flex-col gap-0",
    )


NOTICE_ROLE = {"error": "alert", "info": "status", "success": "status"}
NOTICE_CLASS = {
    "error": "mt-3 w-full rounded-2xl border border-[#e08b12] bg-[#fff7e8] px-3 py-2 text-xs font-semibold leading-relaxed text-[#b86e08]",
    "info": "mt-3 w-full rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-3 py-2 text-xs font-semibold text-[#b86e08]",
    "success": "mt-3 w-full rounded-2xl border border-[#e08b12] bg-[#fba922] px-3 py-2 text-xs font-semibold text-[#111827]",
}


def _notice(message: rx.Var[str], tone: str) -> rx.Component:
    return rx.cond(
        message,
        rx.el.p(
            message,
            role=NOTICE_ROLE[tone],
            class_name=NOTICE_CLASS[tone],
        ),
        rx.fragment(),
    )


# --------------------------------------------------------------------------
# Saved search alerts
# --------------------------------------------------------------------------


def alert_chip(label: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.cond(
            label.startswith("Distance:"),
            "w-fit rounded-full border border-[#e08b12] bg-[#fff7e8] px-2.5 py-1 text-[10px] font-bold text-black",
            "w-fit rounded-full bg-[#fff7e8] px-2.5 py-1 text-[10px] font-bold text-[#b86e08]",
        ),
    )


def alert_card(alert: SavedAlert, **props) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    alert["summary"],
                    class_name="text-sm font-bold leading-snug text-[#111827]",
                ),
                rx.el.p(
                    ui_template("Saved {date}", "date", alert["created"]),
                    class_name="mt-0.5 text-[11px] font-semibold text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.cond(alert["is_enabled"], ui("Alerts on"), ui("Paused")),
                class_name=rx.cond(
                    alert["is_enabled"],
                    "ml-auto w-fit shrink-0 rounded-full bg-[#fba922] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.08em] text-[#111827]",
                    "ml-auto w-fit shrink-0 rounded-full bg-[#f2f5fb] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.08em] text-[#4b5563]",
                ),
            ),
            class_name="flex w-full items-start gap-3",
        ),
        rx.cond(
            alert["chips"].length() > 0,
            rx.el.div(
                rx.foreach(alert["chips"], alert_chip),
                aria_label=ui("Filters saved with this search"),
                class_name="mt-2 flex flex-wrap gap-1.5",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("map", class_name="h-3.5 w-3.5"),
                ui("Open on map"),
                type="button",
                aria_label=ui("Run this saved search on the map"),
                on_click=lambda: SavedSearchState.apply_alert(alert["id"]),
                class_name="gah-primary-outline flex w-fit items-center gap-1.5 rounded-full px-3.5 py-2 text-[11px] font-bold transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            rx.el.button(
                rx.icon(
                    rx.cond(alert["is_enabled"], "bell-off", "bell"),
                    class_name="h-3.5 w-3.5",
                ),
                rx.cond(alert["is_enabled"], ui("Turn off"), ui("Turn on")),
                type="button",
                disabled=SavedSearchState.busy_id == alert["id"],
                aria_pressed=rx.cond(alert["is_enabled"], "true", "false"),
                aria_label=ui("Enable or disable alerts for this saved search"),
                on_click=lambda: SavedSearchState.toggle_alert(alert["id"]),
                class_name="gah-primary-outline flex w-fit items-center gap-1.5 rounded-full px-3.5 py-2 text-[11px] font-bold transition-colors disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                ui("Delete"),
                type="button",
                disabled=SavedSearchState.busy_id == alert["id"],
                aria_label=ui("Delete this saved search"),
                on_click=lambda: SavedSearchState.delete_alert(alert["id"]),
                class_name="flex w-fit items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3.5 py-2 text-[11px] font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        class_name="w-full rounded-none border-0 bg-white p-3.5",
        **props,
    )


def saved_searches_section() -> rx.Component:
    return rx.el.section(
        _heading(
            "bell-ring",
            "Saved search alerts",
            SavedSearchState.alert_count,
            ui("Get notified with matching help requests"),
        ),
        _notice(SavedSearchState.error, "error"),
        _notice(SavedSearchState.success, "info"),
        rx.cond(
            SavedSearchState.is_loading & ~SavedSearchState.has_loaded,
            _skeleton(),
            rx.cond(
                SavedSearchState.alerts.length() > 0,
                rx.el.div(
                    rx.foreach(
                        SavedSearchState.alerts,
                        lambda alert: alert_card(
                            alert, key=alert["id"].to_string()
                        ),
                    ),
                    class_name="gah-edge-stack mt-2 flex w-full flex-col gap-0",
                ),
                rx.cond(
                    SavedSearchState.has_loaded,
                    rx.el.p(
                        ui("No saved search alerts yet."),
                        class_name="mt-3 text-sm font-medium text-[#4b5563]",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        aria_label=ui("Saved search alerts"),
        class_name="w-full bg-transparent",
    )


# --------------------------------------------------------------------------
# Bookmarked help requests
# --------------------------------------------------------------------------


def saved_request_pill(icon: str, value: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        rx.icon(icon, class_name="h-3 w-3"),
        value,
        class_name="flex w-fit items-center gap-1.5 rounded-full bg-[#f2f5fb] px-2.5 py-1 text-[10px] font-bold text-[#404040]",
    )


def saved_request_note_form(request: SavedRequest) -> rx.Component:
    return rx.el.form(
        rx.el.label(
            ui("Private note"),
            html_for=f"saved-note-{request['id']}",
            class_name="text-[11px] font-bold uppercase tracking-[0.08em] text-[#404040]",
        ),
        rx.el.p(
            ui(
                "Only you can see this note. Jot down what to ask, or why you saved this request."
            ),
            id=f"saved-note-help-{request['id']}",
            class_name="mt-0.5 text-[10px] font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.textarea(
            id=f"saved-note-{request['id']}",
            name="note",
            rows="2",
            max_length="255",
            default_value=request["note"],
            key=f"saved-note-{request['id']}-{request['note']}",
            placeholder=ui(
                "e.g. Ask if tools are provided, offer Saturday morning."
            ),
            aria_describedby=f"saved-note-help-{request['id']}",
            class_name="mt-2 w-full resize-y rounded-xl border border-[#d4d4d4] bg-[#ffffff] px-3 py-2 text-xs font-medium leading-relaxed text-[#111827] placeholder:text-[#4b5563] focus:border-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        rx.el.div(
            rx.el.span(
                ui("255 characters max"),
                class_name="text-[10px] font-semibold text-[#4b5563]",
            ),
            rx.el.button(
                rx.icon("notebook-pen", class_name="h-3.5 w-3.5"),
                rx.cond(
                    BookmarkState.note_busy_id == request["id"],
                    ui("Saving..."),
                    ui("Save note"),
                ),
                type="submit",
                disabled=BookmarkState.note_busy_id == request["id"],
                aria_label=ui("Save your private note for this help request"),
                class_name="flex w-fit items-center gap-1.5 rounded-full bg-[#e08b12] px-3.5 py-2 text-[11px] font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            class_name="mt-2 flex flex-wrap items-center justify-between gap-2",
        ),
        on_submit=lambda form_data: BookmarkState.save_note(
            request["id"], form_data
        ),
        on_click=rx.noop().stop_propagation,
        class_name="mt-3 w-full rounded-2xl border border-[#d4d4d4] bg-[#ffffff] p-3",
    )


def saved_request_summary(request: SavedRequest) -> rx.Component:
    return record_summary(
        _tile("bookmark"),
        request["title"],
        f"{request['scheduled']} · {request['location']}",
        f"{request['category_label']} · {request['status']}",
    )


def saved_request_card(request: SavedRequest, **props) -> rx.Component:
    return record_disclosure(
        saved_request_summary(request),
        saved_request_body(request),
        **props,
    )


def saved_request_body(request: SavedRequest) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            saved_request_pill("compass", request["category_label"]),
            saved_request_pill("gift", request["reward_label"]),
            class_name="flex flex-wrap items-center gap-1.5",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("map", class_name="h-3.5 w-3.5"),
                ui("Open on map"),
                type="button",
                aria_label=ui("Open this bookmarked help request on the map"),
                on_click=lambda: BookmarkState.open_on_map(request["id"]),
                class_name="gah-primary-outline flex w-fit items-center gap-1.5 rounded-full px-3.5 py-2 text-[11px] font-bold transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            rx.el.button(
                rx.icon("bookmark-x", class_name="h-3.5 w-3.5"),
                ui("Remove"),
                type="button",
                disabled=BookmarkState.busy_id == request["id"],
                aria_label=ui(
                    "Remove this request from your bookmarked help requests"
                ),
                on_click=lambda: BookmarkState.toggle_bookmark(request["id"]),
                class_name="flex w-fit items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3.5 py-2 text-[11px] font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            rx.el.span(
                ui_template("Saved {date}", "date", request["saved"]),
                class_name="text-[10px] font-semibold text-[#4b5563] sm:ml-auto",
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        saved_request_note_form(request),
        class_name="w-full bg-white",
    )


def saved_requests_section() -> rx.Component:
    return rx.el.section(
        _heading(
            "bookmark",
            "Bookmarked help requests",
            BookmarkState.saved_count,
            ui("Help requests you bookmarked in map or list view."),
        ),
        _notice(BookmarkState.error, "error"),
        _notice(BookmarkState.success, "success"),
        rx.cond(
            BookmarkState.is_loading & ~BookmarkState.has_loaded,
            _skeleton(),
            rx.cond(
                BookmarkState.saved_requests.length() > 0,
                rx.el.div(
                    rx.foreach(
                        BookmarkState.saved_requests,
                        lambda request: saved_request_card(
                            request, key=request["id"].to_string()
                        ),
                    ),
                    class_name="gah-edge-stack mt-2 flex w-full flex-col gap-0",
                ),
                rx.cond(
                    BookmarkState.has_loaded,
                    rx.el.p(
                        ui("No bookmarked help requests yet."),
                        class_name="mt-3 text-sm font-medium text-[#4b5563]",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        aria_label=ui("Bookmarked help requests"),
        class_name="w-full bg-transparent",
    )
