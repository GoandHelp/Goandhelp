import reflex as rx

from app.interface_i18n import ui
from app.components.verification_notice import resend_form
from app.states.auth_state import AuthState
from app.states.verify_state import VerifyState


def mail_map_centerpiece() -> rx.Component:
    """Warm travel-journal centerpiece: a letter landing on a soft map."""
    return rx.el.div(
        rx.el.div(class_name="absolute inset-0 bg-white"),
        rx.el.div(
            class_name="absolute -left-8 top-1/3 h-16 w-2/3 rotate-[8deg] rounded-full bg-[#fba922]/60"
        ),
        rx.el.div(
            class_name="absolute right-3 bottom-4 h-20 w-28 rounded-3xl bg-[#f2bd5a]/50"
        ),
        rx.el.span(
            rx.icon("compass", class_name="h-4 w-4"),
            "N",
            class_name="absolute right-3 top-3 flex items-center gap-1 rounded-full border border-[#e5e5e5] bg-white/85 px-2.5 py-1 text-xs font-semibold text-[#4b5563]",
        ),
        rx.el.div(
            rx.el.span(
                class_name="absolute left-1/2 top-1/2 size-28 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#e08b12]/15 blur-[2px]"
            ),
            rx.el.span(
                class_name="absolute left-1/2 top-1/2 size-20 -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-[#fba922] bg-[#fff7e8]/70"
            ),
            rx.el.span(
                rx.match(
                    VerifyState.status,
                    (
                        "checking",
                        rx.spinner(class_name="h-6 w-6 text-[#111827]"),
                    ),
                    (
                        "success",
                        rx.icon("mail-check", class_name="h-7 w-7"),
                    ),
                    rx.icon("mail-warning", class_name="h-7 w-7"),
                ),
                class_name=rx.cond(
                    VerifyState.is_success,
                    "relative flex size-14 items-center justify-center rounded-2xl border-2 border-white bg-[#fba922] text-[#111827] rotate-[-4deg]",
                    "relative flex size-14 items-center justify-center rounded-2xl border-2 border-white bg-[#fff7e8] text-[#111827] rotate-[-4deg]",
                ),
            ),
            rx.el.span(
                rx.icon("map-pin", class_name="h-3 w-3"),
                ui("Map"),
                class_name="relative mt-3 w-fit flex items-center gap-1.5 rounded-full border border-[#e5e5e5] bg-white/90 px-2.5 py-1 text-[11px] font-semibold text-[#4b5563]",
            ),
            class_name="absolute inset-0 flex flex-col items-center justify-center",
        ),
        class_name="relative h-56 w-full overflow-hidden rounded-[2rem] border border-[#d4d4d4] bg-[#fff7e8] sm:h-72",
    )


def status_badge() -> rx.Component:
    return rx.match(
        VerifyState.status,
        (
            "checking",
            rx.el.span(
                rx.el.span(
                    class_name="size-2 rounded-full bg-[#fba922] animate-pulse"
                ),
                ui("Confirming your email…"),
                class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-[#b86e08]",
            ),
        ),
        (
            "success",
            rx.el.span(
                rx.icon("shield-check", class_name="h-3 w-3"),
                ui("Email confirmed — let's set up your account"),
                class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-[#b86e08]",
            ),
        ),
        rx.el.span(
            rx.icon("triangle-alert", class_name="h-3 w-3"),
            ui("This confirmation link no longer works"),
            class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-[#b86e08]",
        ),
    )


def success_actions() -> rx.Component:
    return rx.el.div(
        rx.el.a(
            rx.icon("arrow-right", class_name="h-4 w-4"),
            ui("Continue"),
            href="/",
            class_name="w-fit flex items-center gap-2 rounded-full border border-[#f2bd5a] bg-[#fff7e8] px-4 py-2.5 text-sm font-bold text-[#111827] transition-colors hover:bg-[#f2bd5a] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.el.p(
            ui(
                "Fifteen tap-first screens, no typing — then a short tour of the app."
            ),
            class_name="w-full text-xs font-medium text-[#4b5563]",
        ),
        class_name="mt-5 flex flex-wrap items-center gap-2",
    )


def problem_actions() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            ui("Send new link"),
            class_name="text-sm font-bold text-[#111827]",
        ),
        rx.el.p(
            ui(
                "Enter the email you signed up with. Links last one hour, work once, "
                "and we never reveal whether an address is registered."
            ),
            class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.el.div(resend_form("Send new link"), class_name="mt-3 w-full"),
        rx.cond(
            AuthState.resend_note,
            rx.el.p(
                ui(AuthState.resend_note),
                role="status",
                aria_live="polite",
                class_name="mt-2 text-xs font-semibold text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        rx.el.a(
            rx.icon("arrow-left", class_name="h-4 w-4"),
            ui("Back"),
            ui("Map"),
            href="/",
            class_name="mt-4 w-fit flex items-center gap-2 rounded-full border border-[#d4d4d4] bg-white px-4 py-2.5 text-sm font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
        ),
        class_name="mt-5 w-full rounded-2xl border border-[#fba922] bg-[#fff7e8] p-4 sm:p-5",
    )


def verify_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            status_badge(),
            rx.el.h1(
                ui(VerifyState.headline),
                class_name="mt-4 text-3xl font-bold leading-tight tracking-tight text-[#111827] sm:text-4xl",
            ),
            rx.el.p(
                ui(VerifyState.detail),
                role="status",
                aria_live="polite",
                class_name="mt-3 max-w-xl text-base font-medium leading-relaxed text-[#4b5563]",
            ),
            rx.cond(
                VerifyState.verified_email,
                rx.el.span(
                    rx.icon("mail", class_name="h-3 w-3"),
                    VerifyState.verified_email,
                    class_name="mt-4 w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#b86e08]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                VerifyState.is_checking,
                rx.el.div(
                    class_name="animate-pulse mt-5 h-11 w-56 rounded-full bg-[#e5e5e5]"
                ),
                rx.cond(
                    VerifyState.is_success,
                    success_actions(),
                    problem_actions(),
                ),
            ),
            class_name="w-full min-w-0 lg:flex-1",
        ),
        rx.el.div(
            mail_map_centerpiece(),
            rx.el.div(
                rx.icon(
                    "shield-check",
                    class_name="h-4 w-4 text-[#b86e08] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    ui(
                        "Confirmation links are single-use and stored only as a hashed "
                        "digest — we can never read your link back."
                    ),
                    class_name="text-sm font-medium leading-relaxed text-[#4b5563]",
                ),
                class_name="mt-4 flex items-start gap-2.5 rounded-2xl border border-[#e5e5e5] bg-white/70 px-4 py-3",
            ),
            class_name="w-full shrink-0 lg:w-[26rem]",
        ),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        on_mount=VerifyState.consume_token,
        class_name="flex w-full flex-col items-start gap-8 rounded-[2rem] border border-[#e5e5e5] bg-[#ffffff] p-5 sm:p-8 lg:flex-row",
    )
