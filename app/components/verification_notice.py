import reflex as rx

from app.interface_i18n import ui
from app.components.feedback import INPUT_CLASS
from app.states.auth_state import AuthState

RESEND_HELPER_TEXT = (
    "Didn't receive your link? Check your junk mail or resend one."
)


def resend_form(button_label: str = "Resend") -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.label(
                ui("Email address"),
                html_for="resend-email",
                class_name="sr-only",
            ),
            rx.el.input(
                id="resend-email",
                name="email",
                type="email",
                placeholder="you@example.com",
                default_value=AuthState.pending_email,
                key=AuthState.pending_email,
                aria_label=ui("Email address"),
                class_name=INPUT_CLASS,
            ),
            class_name="w-full min-w-0",
        ),
        rx.el.p(
            ui(RESEND_HELPER_TEXT),
            id="resend-email-helper",
            class_name="w-full text-xs font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.button(
            rx.cond(
                AuthState.resend_busy,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Sending…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("mail-plus", class_name="h-4 w-4"),
                    ui(button_label),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=AuthState.resend_busy,
            aria_describedby="resend-email-helper",
            class_name="w-full sm:w-auto shrink-0 rounded-xl border border-[#e08b12] bg-[#e08b12] px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12] disabled:opacity-60",
        ),
        on_submit=AuthState.resend_verification,
        reset_on_submit=False,
        class_name="flex w-full flex-col items-stretch gap-2",
    )


def verification_notice() -> rx.Component:
    """Shown after registration or an unverified sign-in attempt."""
    return rx.cond(
        AuthState.awaiting_verification,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("mail-check", class_name="h-7 w-7 text-[#e08b12]"),
                    aria_hidden="true",
                    class_name="flex size-14 shrink-0 items-center justify-center rounded-2xl border border-[#e08b12] bg-[#fff7e8]",
                ),
                rx.el.div(
                    rx.cond(
                        AuthState.pending_email,
                        rx.el.p(
                            ui(
                                "We sent you a confirmation link. Open it to finish creating your account."
                            ),
                            rx.el.bdi(
                                AuthState.pending_email,
                                class_name="block break-all",
                            ),
                            class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                        ),
                        rx.el.p(
                            ui(
                                "We sent you a confirmation link. Open it to finish creating your account."
                            ),
                            class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                        ),
                    ),
                    class_name="min-w-0 flex-1",
                ),
                class_name="flex w-full items-start gap-3",
            ),
            resend_form(),
            rx.el.button(
                rx.icon("arrow-left", class_name="h-4 w-4"),
                ui("Back to sign in"),
                type="button",
                disabled=AuthState.resend_busy,
                on_click=AuthState.back_to_sign_in,
                class_name="flex w-fit items-center gap-2 rounded-full border border-[#e08b12] bg-white px-4 py-2 text-sm font-bold text-[#e08b12] hover:bg-[#fff7e8] disabled:opacity-60",
            ),
            rx.cond(
                AuthState.resend_note,
                rx.el.p(
                    ui(AuthState.resend_note),
                    role="status",
                    aria_live="polite",
                    class_name="text-xs font-semibold text-[#b86e08]",
                ),
                rx.fragment(),
            ),
            class_name="flex w-full flex-col gap-3 rounded-2xl bg-[#ffffff] p-4",
        ),
        rx.fragment(),
    )
