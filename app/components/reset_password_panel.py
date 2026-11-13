"""The `/reset-password` panel: choose a new password from an emailed link."""

import reflex as rx

from app.interface_i18n import ui
from app.states.auth_state import AuthState
from app.components.feedback import (
    INPUT_CLASS,
    error_banner,
    field_label,
    success_banner,
)
from app.states.password_reset_state import PasswordResetState


def checking_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-6 w-48 rounded-full bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse mt-3 h-12 w-full rounded-xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse mt-3 h-12 w-full rounded-xl bg-[#e5e5e5]"
        ),
        class_name="w-full",
    )


def reset_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label("New password", "at least 6 characters"),
            rx.el.input(
                name="password",
                type="password",
                auto_complete="new-password",
                required=True,
                min_length=6,
                placeholder="••••••",
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label("Confirm new password"),
            rx.el.input(
                name="confirm_password",
                type="password",
                auto_complete="new-password",
                required=True,
                min_length=6,
                placeholder="••••••",
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        rx.el.button(
            rx.cond(
                PasswordResetState.is_busy,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Saving…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("key-round", class_name="h-4 w-4"),
                    ui("Save new password"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=PasswordResetState.is_busy,
            class_name="w-full rounded-xl bg-[#e08b12] px-6 py-3 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
        ),
        on_submit=PasswordResetState.submit_new_password,
        reset_on_submit=True,
        class_name="flex flex-col gap-3 w-full",
    )


def back_to_sign_in() -> rx.Component:
    return rx.el.button(
        rx.icon("log-in", class_name="h-4 w-4"),
        ui("Back to sign in"),
        type="button",
        on_click=PasswordResetState.go_to_sign_in,
        class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-full bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08]",
    )


def reset_password_panel() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            rx.icon("key-round", class_name="h-3.5 w-3.5"),
            ui("Password reset"),
            class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08]",
        ),
        rx.el.h1(
            ui("Choose a new password"),
            class_name="mt-3 text-3xl font-bold tracking-tight text-[#111827]",
        ),
        rx.cond(
            PasswordResetState.email_hint,
            rx.el.p(
                ui("Email"),
                ": ",
                rx.el.bdi(PasswordResetState.email_hint),
                class_name="mt-1 text-sm font-medium text-[#b86e08]",
            ),
            rx.el.p(
                ui("Set a new password and get back on the map."),
                class_name="mt-1 text-sm font-medium text-[#4b5563]",
            ),
        ),
        rx.el.div(class_name="my-5 h-px w-full bg-[#e5e5e5]"),
        rx.match(
            PasswordResetState.phase,
            ("checking", checking_card()),
            (
                "ready",
                rx.el.div(
                    error_banner(ui(PasswordResetState.error)),
                    reset_form(),
                    class_name="flex flex-col gap-3 w-full",
                ),
            ),
            (
                "done",
                rx.el.div(
                    success_banner(ui(PasswordResetState.success)),
                    back_to_sign_in(),
                    class_name="flex flex-col gap-4 w-full",
                ),
            ),
            rx.el.div(
                error_banner(ui(PasswordResetState.error)),
                back_to_sign_in(),
                class_name="flex flex-col gap-4 w-full",
            ),
        ),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        class_name="w-full max-w-xl mx-auto rounded-[2rem] border border-[#e5e5e5] bg-[#ffffff] p-6 sm:p-8",
    )
