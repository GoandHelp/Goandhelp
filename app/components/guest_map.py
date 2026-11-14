import reflex as rx

from app.interface_i18n import ui
from app.components.auth_panel import (
    legal_dialog,
    local_preview_button,
    register_form,
    sign_in_form,
)
from app.components.feedback import error_banner, success_banner
from app.components.header import (
    BRAND_LOGO_ALT,
    BRAND_LOGO_SRC,
    BRAND_MAP_POSITION,
    brand_mark,
)
from app.components.openfreemap import open_free_map
from app.components.map_loading import map_loading_logo
from app.components.guest_filters import (
    guest_filter_drawer,
    guest_filter_status,
)
from app.components.map_utility_icon import map_utility_icon
from app.components.verification_notice import verification_notice
from app.states.auth_state import AuthState
from app.states.guest_map_state import GuestJob, GuestMapState


def guest_wall_tab(label: str, tab: str, icon: str) -> rx.Component:
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


MEMBER_BENEFITS: list[str] = [
    "Search for people and help around the world",
    "Post jobs you need help with",
    "Join the Go and Help community forum",
    "Direct message users",
    "Go and Help those who need you",
]


def member_benefit_line(line: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "✓",
            aria_hidden="true",
            class_name="shrink-0 text-[13px] font-bold leading-snug text-[#e08b12]",
        ),
        rx.el.span(
            ui(line),
            class_name="min-w-0 text-left text-[12px] font-semibold leading-snug text-[#111827]",
        ),
        class_name="flex w-full items-start gap-3",
    )


def member_benefits_box() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.foreach(MEMBER_BENEFITS, member_benefit_line),
            class_name="flex w-fit flex-col items-start gap-2.5",
        ),
        class_name="flex min-h-[9.5rem] w-full items-center justify-center rounded-2xl border border-[#f6c66f] bg-[#f4f8ff] px-5 py-5",
    )


def guest_wall_verification_body() -> rx.Component:
    """Calm, single-purpose email-check state (no benefits, tabs or forms)."""
    return rx.el.div(
        error_banner(AuthState.localized_error),
        success_banner(AuthState.localized_success),
        verification_notice(),
        class_name="flex w-full flex-col gap-3",
    )


def guest_wall_auth_body() -> rx.Component:
    """Normal acquisition state: benefits, tabs, forms and legal content."""
    return rx.el.div(
        member_benefits_box(),
        rx.el.div(
            guest_wall_tab("Register", "register", "user-round-plus"),
            guest_wall_tab("Sign in", "signin", "log-in"),
            role="tablist",
            aria_label=ui("Register or sign in"),
            class_name="flex items-center gap-1.5 rounded-2xl border border-[#f6c66f] bg-[#f4f8ff] p-1 w-full",
        ),
        error_banner(AuthState.localized_error),
        success_banner(AuthState.localized_success, white_text=True),
        rx.cond(
            AuthState.auth_tab == "register",
            register_form(),
            sign_in_form(),
        ),
        local_preview_button(),
        rx.el.p(
            ui("User information and data stored securely"),
            class_name="text-[10px] font-medium text-[#4b5563] text-center",
        ),
        legal_dialog(),
        class_name="flex w-full flex-col gap-3",
    )


def guest_job_detail() -> rx.Component:
    return rx.cond(
        GuestMapState.preview_title != "",
        rx.el.section(
            rx.el.h3(
                GuestMapState.preview_title,
                class_name="text-xl font-bold text-[#111827] break-words",
            ),
            rx.el.p(
                GuestMapState.preview_description,
                class_name="mt-2 text-sm leading-relaxed text-[#404040] break-words",
            ),
            rx.el.div(
                rx.el.div(class_name="size-12 rounded-full bg-gray-300"),
                rx.el.div(class_name="h-4 w-32 rounded-full bg-gray-300"),
                rx.el.div(class_name="h-3 w-full rounded-full bg-gray-200"),
                rx.el.div(class_name="h-3 w-3/4 rounded-full bg-gray-200"),
                aria_hidden="true",
                class_name="mt-4 flex flex-wrap items-center gap-3 blur-[3px] pointer-events-none select-none",
            ),
            class_name="w-full rounded-2xl border border-gray-200 bg-white p-4",
        ),
        rx.fragment(),
    )


def sign_up_wall() -> rx.Component:
    return rx.cond(
        GuestMapState.wall_open,
        rx.el.div(
            rx.el.div(
                class_name="absolute inset-0 bg-[#111827]/55 backdrop-blur-sm",
                on_click=GuestMapState.close_wall,
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.image(
                                src=BRAND_LOGO_SRC,
                                alt=BRAND_LOGO_ALT,
                                class_name="size-11 sm:size-12 shrink-0 rounded-full object-contain",
                            ),
                            rx.el.div(
                                rx.cond(
                                    AuthState.awaiting_verification,
                                    rx.el.span(
                                        rx.icon(
                                            "mail-check", class_name="h-3 w-3"
                                        ),
                                        ui("One step left"),
                                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.14em] text-[#b86e08]",
                                    ),
                                    rx.el.span(
                                        rx.icon("lock", class_name="h-3 w-3"),
                                        ui("Become a member"),
                                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.14em] text-[#e08b12]",
                                    ),
                                ),
                                rx.el.h2(
                                    rx.cond(
                                        AuthState.awaiting_verification,
                                        ui("Confirm your email"),
                                        ui("Join our Global Community"),
                                    ),
                                    id="guest-wall-title",
                                    class_name="mt-1.5 text-[17px] sm:text-xl font-bold tracking-tight text-[#111827] leading-tight",
                                ),
                                class_name="flex min-w-0 flex-col items-center text-center",
                            ),
                            class_name="contents",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            type="button",
                            title=ui("Close"),
                            aria_label=ui("Close"),
                            on_click=GuestMapState.close_wall,
                            class_name="flex size-8 shrink-0 items-center justify-center rounded-full border border-[#e08b12] bg-[#fff7e8] text-[#b86e08] transition-colors hover:border-[#b86e08] hover:bg-[#ffedcc] focus-visible:outline-[#e08b12]",
                        ),
                        class_name="grid w-full grid-cols-[3rem_minmax(0,1fr)_3rem] items-start gap-2",
                    ),
                    guest_job_detail(),
                    rx.cond(
                        AuthState.awaiting_verification,
                        rx.fragment(),
                        rx.cond(
                            GuestMapState.wall_reason,
                            rx.el.p(
                                ui(GuestMapState.wall_reason),
                                class_name="text-center text-[12px] font-medium text-[#4b5563] leading-relaxed",
                            ),
                            rx.fragment(),
                        ),
                    ),
                    rx.cond(
                        AuthState.awaiting_verification,
                        guest_wall_verification_body(),
                        guest_wall_auth_body(),
                    ),
                    class_name=rx.cond(
                        AuthState.awaiting_verification,
                        "membership-scroll flex w-full min-h-0 flex-col gap-3 overflow-y-auto overscroll-contain [overflow-anchor:none] px-4 pt-4 pb-3 sm:px-5 sm:pt-5 sm:pb-4 [&_input]:border-[#e08b12] [&_input]:focus:border-[#fba922]",
                        "gah-auth-scroll flex w-full min-h-0 flex-col gap-3 overflow-y-auto overscroll-contain [overflow-anchor:none] px-4 pt-4 pb-3 sm:px-5 sm:pt-5 sm:pb-4",
                    ),
                ),
                role="dialog",
                aria_modal="true",
                aria_labelledby="guest-wall-title",
                class_name=rx.cond(
                    AuthState.awaiting_verification,
                    "relative z-10 flex min-h-0 w-full max-w-lg max-h-[calc(100dvh-1.5rem)] flex-col overflow-hidden rounded-[2rem] border-0 bg-white sm:max-h-[calc(100dvh-3rem)]",
                    "relative z-10 flex min-h-0 w-full max-w-lg max-h-[calc(100dvh-1.5rem)] flex-col overflow-hidden rounded-[2rem] border border-[#e08b12] bg-white sm:max-h-[calc(100dvh-3rem)]",
                ),
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center overflow-hidden p-3 sm:p-6",
        ),
        rx.fragment(),
    )


def guest_map_brand_lockup() -> rx.Component:
    return rx.el.button(
        brand_mark(),
        type="button",
        title=ui("Register or sign in"),
        aria_label=ui("Register or sign in"),
        aria_haspopup="dialog",
        on_click=GuestMapState.go_to_map,
        class_name=rx.cond(
            GuestMapState.search_expanded,
            f"gah-brand-home pointer-events-auto {BRAND_MAP_POSITION} hidden items-center gap-3 rounded-full transition-opacity hover:opacity-90 md:flex",
            f"gah-brand-home pointer-events-auto {BRAND_MAP_POSITION} flex w-fit items-center gap-3 rounded-full transition-opacity hover:opacity-90",
        ),
    )


def guest_utility_button(icon: str, label: str) -> rx.Component:
    return rx.el.button(
        map_utility_icon(icon),
        type="button",
        title=ui(label),
        aria_label=ui(label),
        aria_haspopup="dialog",
        on_click=GuestMapState.open_wall(
            "Browse job titles as a visitor. Join or sign in to unlock job details."
        ),
        class_name="gah-map-utility isolate pointer-events-auto relative flex size-[43px] shrink-0 items-center justify-center rounded-full border-0 shadow-none bg-transparent text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#fba922]",
    )


def guest_control_stack() -> rx.Component:
    return rx.el.div(
        guest_utility_button("bell", "Notifications"),
        guest_utility_button("settings", "Settings"),
        aria_label=ui("Map"),
        class_name="pointer-events-none fixed top-3 right-3 sm:right-[22px] z-40 flex flex-row items-center gap-1",
    )


def guest_job_row(job: GuestJob) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon("hand-helping", class_name="h-4 w-4 text-white"),
            class_name="flex size-9 shrink-0 items-center justify-center rounded-full border-2 border-white bg-[#fba922]",
        ),
        rx.el.span(
            rx.el.span(
                job["title"],
                class_name="block whitespace-normal break-words text-left text-sm font-bold tracking-tight text-[#111827]",
            ),
            rx.el.span(
                rx.el.span(
                    class_name="block h-2 w-4/5 rounded-full bg-gray-300"
                ),
                rx.el.span(
                    class_name="block h-3 w-16 rounded-full bg-[#fba922]/30"
                ),
                rx.el.span(
                    class_name="block h-3 w-20 rounded-full bg-gray-200"
                ),
                aria_hidden="true",
                class_name="pointer-events-none mt-2 flex flex-wrap items-center gap-2 blur-[3px] select-none",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon("lock", class_name="h-4 w-4 shrink-0 text-[#fba922]"),
        type="button",
        aria_label=f"{ui('Register or sign in')}: {job['title']}",
        aria_haspopup="dialog",
        on_click=GuestMapState.open_wall_for_marker(job["code"]),
        class_name="flex w-full items-center gap-3 rounded-2xl border border-gray-200 bg-white px-3 py-3 transition-colors hover:border-[#fba922] hover:bg-[#fff7e8]",
    )


def guest_list_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                ui("Browse open job titles"),
                class_name="text-base font-bold tracking-tight text-[#111827]",
            ),
            rx.el.p(
                ui(
                    "Browse job titles as a visitor. Join or sign in to unlock job details."
                ),
                class_name="mt-1 text-xs font-medium leading-relaxed text-[#4b5563]",
            ),
            class_name="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3",
        ),
        rx.el.p(
            ui(GuestMapState.load_message),
            role="status",
            class_name="text-sm leading-relaxed text-[#4b5563]",
        ),
        rx.cond(
            GuestMapState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-14 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-14 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-14 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="flex w-full flex-col gap-2",
            ),
            rx.cond(
                GuestMapState.has_jobs,
                rx.el.div(
                    rx.foreach(GuestMapState.jobs, guest_job_row),
                    class_name="flex w-full flex-col gap-2",
                ),
                rx.el.div(
                    rx.icon(
                        "hand-helping",
                        class_name="h-6 w-6 text-[#4b5563] mb-2",
                    ),
                    rx.el.p(
                        ui("No open jobs right now."),
                        class_name="text-sm font-bold text-[#111827]",
                    ),
                    rx.el.p(
                        ui("New requests appear here as neighbours post them."),
                        class_name="mt-1 text-xs font-medium text-[#4b5563]",
                    ),
                    class_name="flex w-full flex-col items-center justify-center rounded-2xl border border-dashed border-[#c6d2e8] bg-white px-6 py-10 text-center",
                ),
            ),
        ),
        class_name="gah-screen-scroll absolute inset-0 z-20 flex flex-col gap-3 overflow-y-auto bg-white px-3 pb-[calc(5rem+env(safe-area-inset-bottom))] pt-[12rem] sm:px-6",
    )


def guest_filters_button() -> rx.Component:
    """Open the read-only guest Search filters without an account wall."""
    return rx.el.button(
        rx.icon(
            "sliders-horizontal",
            class_name="h-[30px] w-[30px] text-[#fba922]",
        ),
        type="button",
        title=ui("Open Search filters"),
        aria_label=ui("Search filters"),
        id="gah-guest-filter-open",
        aria_controls="gah-guest-filter-drawer",
        aria_expanded=rx.cond(GuestMapState.search_expanded, "true", "false"),
        on_click=GuestMapState.expand_search,
        class_name="pointer-events-auto absolute bottom-[91px] right-[22px] z-30 flex size-[54px] items-center justify-center rounded-full border-0 bg-white text-[#fba922] transition-colors hover:bg-white hover:text-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
    )


def guest_map_canvas() -> rx.Component:
    return rx.el.div(
        open_free_map(
            markers=GuestMapState.map_markers,
            center=GuestMapState.map_center,
            zoom=GuestMapState.map_zoom,
            on_marker_select=GuestMapState.open_wall_for_marker,
            on_interaction_start=GuestMapState.collapse_search,
            on_guest_control=GuestMapState.open_join_prompt,
            show_navigation_control=False,
            class_name="absolute inset-0 h-full w-full",
        ),
        rx.cond(
            GuestMapState.search_expanded,
            guest_filter_drawer(),
            rx.el.div(
                guest_filter_status(),
                class_name="pointer-events-none absolute top-24 left-3 z-20 max-w-[calc(100%-1.5rem)] rounded-xl bg-white/95 px-3 py-1.5 [&_button]:pointer-events-auto",
            ),
        ),
        guest_map_brand_lockup(),
        guest_control_stack(),
        rx.cond(
            ~GuestMapState.search_expanded,
            guest_filters_button(),
            rx.fragment(),
        ),
        rx.cond(
            GuestMapState.is_loading,
            map_loading_logo(),
            rx.fragment(),
        ),
        class_name="relative h-[100dvh] min-h-[26rem] w-full overflow-hidden bg-[#fff7e8]",
    )


def guest_map_experience() -> rx.Component:
    return rx.el.section(
        guest_map_canvas(),
        sign_up_wall(),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        on_mount=GuestMapState.load_preview,
        class_name="relative w-full flex-1",
    )
