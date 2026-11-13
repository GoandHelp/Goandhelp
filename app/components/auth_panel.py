import datetime

import reflex as rx

from app.interface_i18n import ui
from app.components.header import brand_mark
from app.components.feedback import (
    error_banner,
    field_label,
    select_wrapper,
    success_banner,
)
from app.components.verification_notice import verification_notice
from app.countries import PHONE_CODE_OPTIONS
from app.states.auth_state import AuthState, MIN_REGISTRATION_AGE

# --- Auth colour system: cobalt, white, helping green, deep navy only. -----
COBALT = "#e08b12"
GREEN = "#fba922"

# Crisp white form surfaces with a cobalt focus ring, used by every auth form.
INPUT_CLASS = (
    "w-full rounded-xl border border-[#f7d9a0] bg-white px-4 py-2.5 text-sm "
    "font-medium text-[#111827] placeholder-[#4b5563] transition-colors "
    "focus:border-[#e08b12] focus:ring-2 focus:ring-[#e08b12]/25 outline-hidden"
)
SELECT_CLASS = INPUT_CLASS + " appearance-none cursor-pointer pr-10 bg-white"

LEGAL_SECTIONS: list[dict[str, str]] = [
    {
        "number": "1",
        "title": "Terms and Conditions",
        "body": (
            "Go and Help connects members who offer help with members who need "
            "it. You must be 16 or over, give accurate details and keep your "
            "account to yourself. Agree tasks, rewards and meeting points inside "
            "the platform, turn up when you say you will, and treat every member "
            "with respect. Go and Help is not an employer and does not supervise "
            "work: you remain responsible for your own safety, permits, tax and "
            "insurance. Illegal requests, harassment, discrimination, spam and "
            "attempts to move payment or identity checks off-platform lead to "
            "removal. Ratings must reflect real, completed work."
        ),
    },
    {
        "number": "2",
        "title": "Privacy Policy",
        "body": (
            "We store the details you give us — first and family name, email, "
            "phone number, date of birth and profile content — to run your "
            "account, confirm your email and match you with nearby requests. "
            "Your date of birth is private account-verification data: we use it "
            "only to confirm you are 16 or over and never show it, or an age "
            "derived from it, to other members or guests. Guests only "
            "ever see job titles, categories and a rough area; exact meeting "
            "points, contact details and identities are unlocked for confirmed "
            "members involved in a task. We never sell your data and only share "
            "it with the services that deliver our emails and host the platform. "
            "You can update your profile, change your language, or ask us to "
            "delete your account and its data at any time."
        ),
    },
    {
        "number": "3",
        "title": "Cookies Policy",
        "body": (
            "Go and Help uses a small number of essential cookies and local "
            "storage entries to keep you signed in, remember your language and "
            "protect the sign-in form from abuse. We use privacy-friendly, "
            "aggregated measurement to understand which features members use, "
            "and no advertising or cross-site tracking cookies. Clearing your "
            "browser storage signs you out and resets these preferences."
        ),
    },
]

CURRENT_YEAR = datetime.date.today().year

DAY_OPTIONS: list[str] = [str(day) for day in range(1, 32)]

MONTH_OPTIONS: list[tuple[str, str]] = [
    ("1", "January"),
    ("2", "February"),
    ("3", "March"),
    ("4", "April"),
    ("5", "May"),
    ("6", "June"),
    ("7", "July"),
    ("8", "August"),
    ("9", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December"),
]

YEAR_OPTIONS: list[str] = [
    str(CURRENT_YEAR - offset) for offset in range(MIN_REGISTRATION_AGE, 120)
]

MODE_CARDS: list[dict[str, str]] = [
    {
        "icon": "hand-helping",
        "title": "Offer help",
        "blurb": "Lend a language, a car ride or a spare pair of hands to travellers nearby.",
    },
    {
        "icon": "map-pin",
        "title": "Get help",
        "blurb": "Post what you need — translation, directions, luggage, paperwork — and meet a local.",
    },
    {
        "icon": "users-round",
        "title": "Both ways",
        "blurb": "Trade skills as you travel and collect kindness points in your journal.",
    },
]


def mode_card(item: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-5 w-5 text-white"),
            class_name="flex items-center justify-center size-10 rounded-xl bg-[#e08b12] shrink-0",
        ),
        rx.el.div(
            rx.el.p(
                ui(item["title"]),
                class_name="text-sm font-bold text-[#111827]",
            ),
            rx.el.p(
                ui(item["blurb"]),
                class_name="text-sm font-medium text-[#4b5563] mt-1 leading-relaxed",
            ),
            class_name="min-w-0",
        ),
        rx.el.span(
            class_name="hidden sm:block h-8 w-1.5 shrink-0 rounded-full bg-[#fba922]",
        ),
        class_name="flex items-start gap-4 w-full rounded-2xl border border-[#f7d9a0] bg-white p-4 transition-colors hover:border-[#e08b12]",
    )


def phone_code_option(item: tuple[str, str]) -> rx.Component:
    return rx.el.option(
        item[1], value=item[0], class_name="text-[#111827] bg-white"
    )


def plain_option(value: str) -> rx.Component:
    return rx.el.option(
        value, value=value, class_name="text-[#111827] bg-white"
    )


def labelled_option(item: tuple[str, str]) -> rx.Component:
    return rx.el.option(
        ui(item[1]), value=item[0], class_name="text-[#111827] bg-white"
    )


def legal_section(item: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            rx.el.span(
                item["number"],
                class_name="flex size-5 shrink-0 items-center justify-center rounded-full bg-[#e08b12] text-[11px] font-bold text-white",
            ),
            ui(item["title"]),
            class_name="flex items-center gap-2 text-[13px] font-bold tracking-tight text-[#111827]",
        ),
        rx.el.p(
            ui(item["body"]),
            class_name="mt-1 break-words text-xs font-medium leading-relaxed text-[#4b5563]",
        ),
        class_name="w-full rounded-xl border border-[#f7d9a0] bg-white px-3 py-2.5",
    )


def legal_dialog() -> rx.Component:
    """Accessible legal-policies overlay shared by every auth surface."""
    return rx.cond(
        AuthState.legal_dialog_open,
        rx.el.div(
            rx.el.div(
                class_name="absolute inset-0 bg-[#111827]/60 backdrop-blur-sm",
                on_click=AuthState.close_legal_dialog,
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        ui("Go and Help legal policies"),
                        id="legal-dialog-title",
                        class_name="text-base font-bold tracking-tight text-[#111827]",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-3.5 w-3.5"),
                        type="button",
                        title=ui("Close"),
                        aria_label=ui("Close"),
                        on_click=AuthState.close_legal_dialog,
                        class_name="flex size-8 shrink-0 items-center justify-center rounded-full border border-[#f7d9a0] bg-white text-[#e08b12] transition-colors hover:border-[#e08b12] hover:bg-[#fff7e8]",
                    ),
                    class_name="flex items-start justify-between gap-3",
                ),
                rx.el.div(
                    rx.foreach(LEGAL_SECTIONS, legal_section),
                    class_name="flex w-full flex-col gap-2 overflow-y-auto",
                ),
                rx.el.button(
                    ui("Close"),
                    type="button",
                    on_click=AuthState.close_legal_dialog,
                    class_name="w-full rounded-xl bg-[#e08b12] px-4 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-[#b86e08]",
                ),
                role="dialog",
                aria_modal="true",
                aria_labelledby="legal-dialog-title",
                lang=AuthState.preferred_language,
                dir=AuthState.interface_direction,
                class_name="relative z-10 flex w-full max-w-lg max-h-[85vh] flex-col gap-3 overflow-y-auto rounded-[1.5rem] border border-[#e08b12] bg-[#fff7e8] p-4 sm:p-5",
            ),
            class_name="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-6",
        ),
        rx.fragment(),
    )


def phone_code_field(
    field_id: str,
    code_value: rx.Var[str],
    prefix: rx.Var[str],
    on_change: rx.event.EventType,
) -> rx.Component:
    """Real accessible select whose collapsed face shows only the dial prefix."""
    return rx.el.div(
        select_wrapper(
            rx.el.select(
                rx.foreach(PHONE_CODE_OPTIONS, phone_code_option),
                id=f"{field_id}-phone-code",
                name="phone_code",
                value=code_value,
                on_change=on_change,
                required=True,
                aria_label=ui("Country calling code"),
                class_name=SELECT_CLASS + " text-transparent",
            )
        ),
        rx.el.span(
            prefix,
            aria_hidden="true",
            class_name="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[13px] font-semibold text-[#111827]",
        ),
        class_name="relative w-full",
    )


PHONE_CODE_BINDINGS: dict[
    str, tuple[rx.Var[str], rx.Var[str], rx.event.EventType]
] = {
    "register": (
        AuthState.register_phone_code,
        AuthState.register_dial_prefix,
        AuthState.set_register_phone_code,
    ),
    "signin": (
        AuthState.signin_phone_code,
        AuthState.signin_dial_prefix,
        AuthState.set_signin_phone_code,
    ),
}


def _phone_input_row(
    field_id: str,
    hint: str,
    binding: tuple[rx.Var[str], rx.Var[str], rx.event.EventType],
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                ui("Phone"),
                html_for=f"{field_id}-phone-number",
                class_name="text-[13px] font-semibold text-[#111827]",
            ),
            rx.cond(
                hint != "",
                rx.el.span(
                    ui(hint),
                    class_name="text-[11px] font-medium text-[#4b5563]",
                ),
                rx.fragment(),
            ),
            class_name="flex items-baseline justify-between gap-3 mb-1",
        ),
        rx.el.div(
            phone_code_field(field_id, binding[0], binding[1], binding[2]),
            rx.el.input(
                id=f"{field_id}-phone-number",
                name="phone_number",
                type="tel",
                input_mode="tel",
                auto_complete="tel-national",
                placeholder="",
                required=True,
                aria_label=ui("Phone number without the country code"),
                class_name=INPUT_CLASS,
            ),
            class_name="grid grid-cols-[minmax(0,5.5rem)_minmax(0,1fr)] gap-2 w-full items-center",
        ),
        class_name="w-full",
    )


def phone_input_row(field_id: str, hint: str = "") -> rx.Component:
    """Collapsed dial-prefix code select plus a blank national number field."""
    return _phone_input_row(
        field_id,
        hint,
        PHONE_CODE_BINDINGS.get(field_id, PHONE_CODE_BINDINGS["register"]),
    )


def tab_button(label: str, tab: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4"),
        ui(label),
        type="button",
        on_click=lambda: AuthState.set_auth_tab(tab),
        class_name=rx.cond(
            AuthState.auth_tab == tab,
            "flex-1 flex items-center justify-center gap-2 rounded-xl border-0 bg-[#b86e08] shadow-sm px-3.5 py-2 text-[13px] font-bold text-white outline-hidden transition-colors focus-visible:ring-2 focus-visible:ring-[#e08b12]/40",
            "flex-1 flex items-center justify-center gap-2 rounded-xl border-0 bg-[#e08b12] px-3.5 py-2 text-[13px] font-semibold text-white outline-hidden transition-colors hover:bg-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]/40",
        ),
    )


def submit_button(label: str, busy_label: str) -> rx.Component:
    return rx.el.button(
        rx.cond(
            AuthState.is_busy,
            rx.el.span(
                rx.spinner(class_name="h-3.5 w-3.5"),
                ui(busy_label),
                class_name="flex items-center justify-center gap-2",
            ),
            rx.el.span(
                rx.icon("arrow-right", class_name="h-3.5 w-3.5"),
                ui(label),
                class_name="flex items-center justify-center gap-2",
            ),
        ),
        type="submit",
        disabled=AuthState.is_busy,
        class_name="w-full rounded-xl bg-[#e08b12] px-4 py-2.5 text-[13px] font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
    )


def go_and_help_submit_button() -> rx.Component:
    return rx.el.button(
        rx.cond(
            AuthState.is_busy,
            rx.el.span(
                rx.spinner(class_name="h-3.5 w-3.5"),
                ui("Creating your account…"),
                class_name="flex items-center justify-center gap-2",
            ),
            rx.el.span(
                ui("Let's go!"),
                class_name="flex items-center justify-center gap-2",
            ),
        ),
        type="submit",
        disabled=AuthState.is_busy,
        class_name="w-full rounded-xl bg-[#e08b12] px-4 py-2.5 text-[13px] font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
    )


def birth_date_group() -> rx.Component:
    """Three mandatory birth-date controls: day, month and year."""
    return rx.el.fieldset(
        rx.el.legend(
            rx.el.span(
                ui("Date of birth"),
                class_name="text-[13px] font-semibold text-[#111827]",
            ),
            rx.el.span(
                ui("16+ only — kept private"),
                class_name="ml-2 text-[11px] font-medium text-[#4b5563]",
            ),
            class_name="mb-1 flex flex-wrap items-baseline gap-y-1",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    ui("Birth day"),
                    html_for="register-birth-day",
                    class_name="sr-only",
                ),
                select_wrapper(
                    rx.el.select(
                        rx.el.option(
                            ui("Day"),
                            value="",
                            disabled=True,
                            class_name="text-[#4b5563] bg-white",
                        ),
                        rx.foreach(DAY_OPTIONS, plain_option),
                        id="register-birth-day",
                        name="birth_day",
                        default_value="",
                        required=True,
                        aria_label=ui("Birth day"),
                        class_name=SELECT_CLASS,
                    )
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.label(
                    ui("Birth month"),
                    html_for="register-birth-month",
                    class_name="sr-only",
                ),
                select_wrapper(
                    rx.el.select(
                        rx.el.option(
                            ui("Month"),
                            value="",
                            disabled=True,
                            class_name="text-[#4b5563] bg-white",
                        ),
                        rx.foreach(MONTH_OPTIONS, labelled_option),
                        id="register-birth-month",
                        name="birth_month",
                        default_value="",
                        required=True,
                        aria_label=ui("Birth month"),
                        class_name=SELECT_CLASS,
                    )
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.label(
                    ui("Birth year"),
                    html_for="register-birth-year",
                    class_name="sr-only",
                ),
                select_wrapper(
                    rx.el.select(
                        rx.el.option(
                            ui("Year"),
                            value="",
                            disabled=True,
                            class_name="text-[#4b5563] bg-white",
                        ),
                        rx.foreach(YEAR_OPTIONS, plain_option),
                        id="register-birth-year",
                        name="birth_year",
                        default_value="",
                        required=True,
                        aria_label=ui("Birth year"),
                        class_name=SELECT_CLASS,
                    )
                ),
                class_name="w-full",
            ),
            class_name="grid grid-cols-3 gap-2 w-full",
        ),
        class_name="w-full border-0 p-0 m-0",
    )


def register_fields() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    ui("First name"),
                    html_for="register-first-name",
                    class_name="mb-1 block text-[13px] font-semibold text-[#111827]",
                ),
                rx.el.input(
                    id="register-first-name",
                    name="first_name",
                    type="text",
                    auto_complete="given-name",
                    required=True,
                    placeholder="Maya",
                    aria_label=ui("First name"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.label(
                    ui("Family name"),
                    html_for="register-family-name",
                    class_name="mb-1 block text-[13px] font-semibold text-[#111827]",
                ),
                rx.el.input(
                    id="register-family-name",
                    name="family_name",
                    type="text",
                    auto_complete="family-name",
                    required=True,
                    placeholder="De Silva",
                    aria_label=ui("Family name"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full",
        ),
        rx.el.div(
            field_label("Email"),
            rx.el.input(
                name="email",
                type="email",
                auto_complete="email",
                required=True,
                placeholder="you@example.com",
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        phone_input_row("register", ""),
        birth_date_group(),
        rx.el.div(
            rx.el.div(
                field_label("Password", "6+ characters"),
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
                field_label("Confirm password"),
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
            class_name="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full",
        ),
        class_name="flex w-full min-w-0 flex-col gap-3 pl-[5px]",
    )


def register_form() -> rx.Component:
    return rx.el.form(
        register_fields(),
        rx.el.label(
            rx.el.input(
                type="checkbox",
                name="terms_consent",
                required=True,
                class_name="peer absolute inset-0 z-10 m-0 h-full w-full cursor-pointer opacity-0",
                default_value="accepted",
                key="accepted",
            ),
            rx.el.span(
                rx.icon("check", class_name="size-3.5 text-black"),
                aria_hidden="true",
                class_name="flex size-5 shrink-0 items-center justify-center rounded-sm border border-black! bg-white peer-checked:bg-[#fba922] [&>svg]:invisible peer-checked:[&>svg]:visible peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-[#e08b12]",
            ),
            ui("I agree to the Terms and User Agreement (required)"),
            class_name="relative mx-auto inline-flex w-fit max-w-full cursor-pointer items-center justify-center gap-2 text-center text-[13px] text-[#111827]",
        ),
        go_and_help_submit_button(),
        on_submit=AuthState.register,
        reset_on_submit=False,
        class_name="flex w-full min-w-0 flex-col gap-3",
    )


def forgot_password_block() -> rx.Component:
    """`Forgot password?` and its generic, non-enumerating reply."""
    return rx.el.div(
        rx.el.button(
            rx.icon("key-round", class_name="h-3.5 w-3.5"),
            ui("Forgot password?"),
            type="button",
            on_click=rx.cond(
                AuthState.forgot_open,
                AuthState.close_forgot_password,
                AuthState.open_forgot_password,
            ),
            class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f7d9a0] bg-white px-3 py-1.5 text-xs font-bold text-[#e08b12] transition-colors hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40",
        ),
        rx.cond(
            AuthState.forgot_open,
            rx.el.form(
                rx.el.div(
                    field_label(
                        "Your email", "we send a single-use reset link"
                    ),
                    rx.el.input(
                        name="reset_email",
                        type="email",
                        auto_complete="email",
                        required=True,
                        placeholder="you@example.com",
                        class_name=INPUT_CLASS,
                    ),
                    class_name="w-full",
                ),
                rx.el.button(
                    rx.cond(
                        AuthState.forgot_busy,
                        rx.el.span(
                            rx.spinner(class_name="h-4 w-4"),
                            ui("Sending link…"),
                            class_name="flex items-center justify-center gap-2",
                        ),
                        rx.el.span(
                            rx.icon("mail", class_name="h-4 w-4"),
                            ui("Email me a reset link"),
                            class_name="flex items-center justify-center gap-2",
                        ),
                    ),
                    type="submit",
                    disabled=AuthState.forgot_busy,
                    class_name="w-full rounded-xl bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
                ),
                rx.cond(
                    AuthState.forgot_note,
                    rx.el.p(
                        ui(AuthState.forgot_note),
                        role="status",
                        class_name="rounded-xl bg-[#fba922] px-3 py-2 text-xs font-semibold text-[#111827]",
                    ),
                    rx.fragment(),
                ),
                on_submit=AuthState.request_password_reset,
                reset_on_submit=False,
                class_name="mt-3 flex flex-col gap-3 w-full rounded-2xl border border-[#f7d9a0] bg-[#fff7e8] p-4",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def sign_in_form() -> rx.Component:
    return rx.el.form(
        rx.el.style(
            """
            #gah-sign-in-form input:is([type="email"], [type="password"]) {
                background-color: #ffffff !important;
                color: #111827 !important;
                opacity: 1;
            }
            #gah-sign-in-form input:is([type="email"], [type="password"]):autofill,
            #gah-sign-in-form input:is([type="email"], [type="password"]):-webkit-autofill,
            #gah-sign-in-form input:is([type="email"], [type="password"]):-webkit-autofill:hover,
            #gah-sign-in-form input:is([type="email"], [type="password"]):-webkit-autofill:focus {
                -webkit-text-fill-color: #111827 !important;
                box-shadow: 0 0 0 1000px #ffffff inset !important;
                -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
                caret-color: #111827;
            }
            """
        ),
        rx.el.div(
            field_label("Email"),
            rx.el.input(
                name="email",
                type="email",
                auto_complete="email",
                required=True,
                placeholder="you@example.com",
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label("Password"),
            rx.el.input(
                name="password",
                type="password",
                auto_complete="current-password",
                required=True,
                placeholder="••••••",
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        submit_button("Sign in", "Signing in…"),
        on_submit=AuthState.sign_in,
        id="gah-sign-in-form",
        reset_on_submit=False,
        class_name="flex flex-col gap-3 w-full",
    )


def local_preview_button() -> rx.Component:
    """Subtle localhost-only shortcut into the signed-in member experience."""
    return rx.cond(
        AuthState.is_local_development,
        rx.el.div(
            rx.el.button(
                rx.icon("flask-conical", class_name="h-3.5 w-3.5"),
                ui("Preview member experience"),
                type="button",
                disabled=AuthState.is_busy,
                on_click=AuthState.preview_as_local_member,
                class_name="w-full flex items-center justify-center gap-2 rounded-xl border border-[#fba922] bg-[#fba922] px-4 py-2.5 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            rx.el.p(
                ui(
                    "Local development preview only — no account is verified and "
                    "nothing is saved."
                ),
                class_name="mt-1.5 text-[11px] font-medium text-[#4b5563] text-center",
            ),
            class_name="w-full",
        ),
        rx.fragment(),
    )


def auth_card_verification_body() -> rx.Component:
    """Awaiting-verification card: confirmation, resend and error feedback only."""
    return rx.el.div(
        error_banner(AuthState.localized_error),
        success_banner(AuthState.localized_success),
        verification_notice(),
        class_name="flex w-full flex-col gap-4",
    )


def auth_card_form_body() -> rx.Component:
    """Normal register / sign-in card body."""
    return rx.el.div(
        rx.el.div(
            tab_button("Register", "register", "user-round-plus"),
            tab_button("Sign in", "signin", "log-in"),
            role="tablist",
            aria_label=ui("Register or sign in"),
            class_name="flex items-center gap-1.5 rounded-2xl border border-[#f7d9a0] bg-[#fff7e8] p-1 w-full",
        ),
        error_banner(AuthState.localized_error),
        success_banner(AuthState.localized_success, white_text=True),
        rx.cond(
            AuthState.auth_tab == "register",
            register_form(),
            rx.el.div(
                sign_in_form(),
                forgot_password_block(),
                class_name="flex flex-col gap-4 w-full",
            ),
        ),
        local_preview_button(),
        class_name="flex w-full flex-col gap-4",
    )


def auth_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                brand_mark(),
                rx.el.span(
                    "Go and Help",
                    class_name="text-lg font-bold tracking-tight text-[#e08b12] leading-tight",
                ),
                class_name="flex w-fit items-center gap-3",
            ),
            rx.cond(
                AuthState.awaiting_verification,
                rx.el.div(
                    rx.el.span(
                        rx.icon("mail-check", class_name="h-3 w-3"),
                        ui("One step left"),
                        class_name="mt-4 w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-bold text-[#b86e08]",
                    ),
                    rx.el.h1(
                        ui("Confirm your email"),
                        class_name="mt-5 text-4xl sm:text-5xl font-bold tracking-tight text-[#111827]",
                    ),
                    class_name="flex w-full flex-col",
                ),
                rx.el.div(
                    rx.el.span(
                        rx.icon("user-round-plus", class_name="h-3 w-3"),
                        ui("Registration & profiles"),
                        class_name="mt-4 w-fit flex items-center gap-2 rounded-full bg-[#fba922] px-3 py-1 text-xs font-bold text-[#111827]",
                    ),
                    rx.el.h1(
                        ui("Trade a skill, keep a story."),
                        class_name="mt-5 text-4xl sm:text-5xl font-bold tracking-tight text-[#111827]",
                    ),
                    rx.el.p(
                        ui(
                            "Create a Go and Help account to post the help you need, offer the skill you have, "
                            "and keep a warm journal of every favour returned."
                        ),
                        class_name="mt-3 text-base font-medium text-[#4b5563] leading-relaxed",  # noqa: E501
                    ),
                    rx.el.div(
                        rx.foreach(MODE_CARDS, mode_card),
                        class_name="mt-8 flex flex-col gap-3 w-full",
                    ),
                    class_name="flex w-full flex-col",
                ),
            ),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        rx.el.div(
            rx.cond(
                AuthState.awaiting_verification,
                auth_card_verification_body(),
                auth_card_form_body(),
            ),
            legal_dialog(),
            class_name="w-full lg:w-[26rem] shrink-0 flex flex-col gap-4 rounded-3xl border border-[#f7d9a0] bg-white p-5 sm:p-7",
        ),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        class_name="w-full flex flex-col lg:flex-row items-start gap-10",
    )
