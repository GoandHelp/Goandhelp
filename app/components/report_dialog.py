"""The shared, compact `Report unsafe content` control and dialog."""

import reflex as rx

from app.components.feedback import (
    INPUT_CLASS,
    SELECT_CLASS,
    error_banner,
    field_label,
    select_wrapper,
)
from app.interface_i18n import ui
from app.states.auth_state import AuthState
from app.states.content_report_state import ContentReportState

REPORT_BUTTON_CLASS = (
    "w-fit max-w-full flex flex-wrap items-center justify-center gap-1.5 rounded-full border border-[#d4d4d4] "
    "bg-white px-3 py-1.5 text-xs font-semibold text-[#4b5563] "
    "transition-colors hover:border-[#e08b12] hover:text-[#b86e08] "
    "focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]"
)


def report_button(
    target_type: str,
    target_id: rx.Var[int] | int,
    target_hint: rx.Var[str] | str = "",
    label: str | rx.Var[str] = "Report",
    class_name: str = REPORT_BUTTON_CLASS,
    accessible_label: str | rx.Var[str] = "Report unsafe content privately",
    accessible_title: str
    | rx.Var[str] = "Report privately to the Go and Help safety team",
) -> rx.Component:
    """A small explicit control that opens the shared report dialog."""
    return rx.el.button(
        rx.icon("flag", class_name="h-3 w-3"),
        ui(label),
        type="button",
        aria_label=ui(accessible_label),
        title=ui(accessible_title),
        on_click=lambda: ContentReportState.open_report(
            target_type, target_id, target_hint
        ),
        class_name=class_name,
    )


def category_option(item: dict[str, str]) -> rx.Component:
    return rx.el.option(ui(item["label"]), value=item["value"])


def report_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label("What kind of problem is this?", "required"),
            select_wrapper(
                rx.el.select(
                    rx.el.option(
                        ui("Choose a safety category"), value="", disabled=True
                    ),
                    rx.foreach(
                        ContentReportState.category_options, category_option
                    ),
                    value=ContentReportState.category,
                    on_change=ContentReportState.set_category,
                    class_name=SELECT_CLASS,
                )
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label("What happened?", "20–2,000 characters"),
            rx.el.textarea(
                name="details",
                rows="4",
                required=True,
                placeholder=ui(
                    "Tell us what you saw, when it happened, and anything our team should know."
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="w-full",
        ),
        error_banner(ui(ContentReportState.error)),
        rx.el.p(
            rx.icon("lock", class_name="h-3 w-3 inline-block mr-1"),
            ui(
                "Reports stay private. The person you report is never told who sent it."
            ),
            class_name="text-[11px] font-medium text-[#b86e08] rounded-xl bg-[#fff7e8] px-3 py-2",
        ),
        rx.el.div(
            rx.el.button(
                ui("Cancel"),
                type="button",
                on_click=ContentReportState.close_report,
                class_name="w-full sm:w-fit rounded-full border border-[#d4d4d4] bg-white px-4 py-2.5 text-sm font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
            ),
            rx.el.button(
                rx.cond(
                    ContentReportState.is_sending,
                    rx.el.span(
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 shrink-0 animate-spin",
                        ),
                        ui("Sending…"),
                        class_name="flex flex-wrap items-center justify-center gap-2",
                    ),
                    rx.el.span(
                        rx.icon("shield-alert", class_name="h-4 w-4"),
                        ui("Send report"),
                        class_name="flex flex-wrap items-center justify-center gap-2",
                    ),
                ),
                type="submit",
                disabled=ContentReportState.is_sending,
                class_name="w-full sm:w-fit rounded-full bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
            ),
            class_name="flex flex-col-reverse sm:flex-row sm:justify-end items-stretch sm:items-center gap-2 w-full",
        ),
        on_submit=ContentReportState.submit_report,
        reset_on_submit=False,
        class_name="flex flex-col gap-3 w-full",
    )


def report_dialog() -> rx.Component:
    """The single overlay dialog, mounted once at the page root."""
    return rx.cond(
        ContentReportState.is_open,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            rx.icon("flag", class_name="h-4 w-4"),
                            ui("Safety"),
                            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-[#b86e08]",
                        ),
                        rx.el.h2(
                            ContentReportState.localized_dialog_title,
                            class_name="mt-2 text-xl font-bold tracking-tight text-[#111827]",
                        ),
                        rx.cond(
                            ContentReportState.target_hint,
                            rx.el.p(
                                f"“{ContentReportState.target_hint}”",
                                class_name="mt-1 text-xs font-medium italic text-[#4b5563] line-clamp-2",
                            ),
                            rx.fragment(),
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        type="button",
                        aria_label=ui("Close report form"),
                        on_click=ContentReportState.close_report,
                        class_name="flex size-9 shrink-0 items-center justify-center rounded-full border border-[#d4d4d4] bg-white text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
                    ),
                    class_name="flex items-start justify-between gap-3 w-full",
                ),
                rx.el.div(class_name="my-4 h-px w-full bg-[#e5e5e5]"),
                report_form(),
                role="dialog",
                aria_modal="true",
                aria_label=ui("Report unsafe content"),
                lang=AuthState.preferred_language,
                dir=AuthState.interface_direction,
                class_name="w-full min-w-0 max-w-lg max-h-[90dvh] overflow-y-auto overscroll-contain break-words rounded-[2rem] border border-[#e5e5e5] bg-[#ffffff] p-5 sm:p-6 dark:bg-[#1f2937] font-['Inter']",
            ),
            class_name="fixed inset-0 z-[60] flex items-center justify-center bg-[#111827]/50 p-4",
        ),
        rx.fragment(),
    )
