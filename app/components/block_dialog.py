"""The shared Block safety control and its confirmation dialog."""

import reflex as rx

from app.interface_i18n import ui, ui_template
from app.components.feedback import error_banner
from app.states.auth_state import AuthState
from app.states.block_state import BlockState

from app.components.report_dialog import REPORT_BUTTON_CLASS

BLOCK_BUTTON_CLASS = REPORT_BUTTON_CLASS


def block_member_button(
    member_id: rx.Var[int] | int,
    member_name: rx.Var[str] | str = "",
    label: str | rx.Var[str] = "Block",
    class_name: str = BLOCK_BUTTON_CLASS,
    accessible_label: str | rx.Var[str] = "Block this member privately",
    accessible_title: str
    | rx.Var[str] = "Block privately — they are never told",
) -> rx.Component:
    """Opens the one shared confirmation dialog for a concrete other member."""
    return rx.el.button(
        rx.icon("user-minus", class_name="h-3 w-3"),
        ui(label),
        type="button",
        aria_label=ui(accessible_label),
        title=ui(accessible_title),
        on_click=lambda: BlockState.open_block(member_id, member_name),
        class_name=class_name,
    )


def _plain_point(icon: str, copy: str) -> rx.Component:
    return rx.el.li(
        rx.icon(icon, class_name="h-3.5 w-3.5 shrink-0 text-[#b86e08] mt-0.5"),
        rx.el.span(ui(copy), class_name="min-w-0 flex-1"),
        class_name="flex items-start gap-2 text-xs font-medium leading-relaxed text-[#4b5563] dark:text-gray-200",
    )


def _dialog_body() -> rx.Component:
    return rx.el.div(
        rx.el.ul(
            _plain_point(
                "eye-off",
                "Their posts, discussions and comments will be hidden from you.",
            ),
            _plain_point(
                "message-square-off",
                "Neither of you can send contact requests or messages while "
                "the block is in place.",
            ),
            _plain_point(
                "lock",
                "They are not notified and are never told that you blocked "
                "them.",
            ),
            _plain_point(
                "rotate-ccw",
                "You can unblock them later from Profile › Blocked members.",
            ),
            role="list",
            class_name="flex flex-col gap-2 rounded-2xl bg-[#fff7e8] p-4 dark:bg-[#111827]",
        ),
        error_banner(ui(BlockState.error)),
        rx.el.div(
            rx.el.button(
                ui("Cancel"),
                type="button",
                on_click=BlockState.close_block,
                class_name="w-full sm:w-fit rounded-full border border-[#f7d9a0] bg-white px-4 py-2.5 text-sm font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
            ),
            rx.el.button(
                rx.cond(
                    BlockState.is_blocking,
                    rx.el.span(
                        rx.spinner(class_name="h-4 w-4"),
                        ui("Blocking…"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                    rx.el.span(
                        rx.icon("user-minus", class_name="h-4 w-4"),
                        ui("Confirm block"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                ),
                type="button",
                disabled=BlockState.is_blocking,
                on_click=BlockState.confirm_block,
                class_name="w-full sm:w-fit rounded-full bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
            ),
            class_name="flex flex-col-reverse sm:flex-row sm:justify-end items-stretch sm:items-center gap-2 w-full",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def block_dialog() -> rx.Component:
    """The single overlay dialog, mounted once in the signed-in app shell."""
    return rx.cond(
        BlockState.is_open,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            rx.icon("user-minus", class_name="h-4 w-4"),
                            ui("Safety"),
                            class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f7d9a0] bg-[#fff7e8] px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-[#e08b12]",
                        ),
                        rx.el.h2(
                            rx.cond(
                                BlockState.target_name.strip().length() > 0,
                                ui_template(
                                    "Block {name}?",
                                    "name",
                                    BlockState.target_name,
                                ),
                                ui("Block this member?"),
                            ),
                            class_name="mt-2 text-xl font-bold tracking-tight text-[#111827] dark:text-white",
                        ),
                        rx.el.p(
                            ui(
                                "Blocking is private and takes effect straight "
                                "away."
                            ),
                            class_name="mt-1 text-xs font-medium text-[#4b5563] dark:text-gray-200",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        type="button",
                        aria_label=ui("Close block confirmation"),
                        on_click=BlockState.close_block,
                        class_name="flex size-9 shrink-0 items-center justify-center rounded-full border border-[#f7d9a0] bg-white text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                    ),
                    class_name="flex items-start justify-between gap-3 w-full",
                ),
                rx.el.div(class_name="my-4 h-px w-full bg-[#f7d9a0]"),
                _dialog_body(),
                role="dialog",
                aria_modal="true",
                lang=AuthState.preferred_language,
                dir=AuthState.interface_direction,
                aria_label=ui("Confirm blocking this member"),
                class_name="w-full max-w-md max-h-[90dvh] overflow-y-auto rounded-[2rem] border border-[#f7d9a0] bg-[#ffffff] p-5 sm:p-6 dark:bg-[#1f2937]",
            ),
            class_name="fixed inset-0 z-[60] flex items-center justify-center bg-[#111827]/50 p-4",
        ),
        rx.fragment(),
    )
