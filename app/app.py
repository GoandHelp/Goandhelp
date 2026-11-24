import reflex as rx

from app.interface_i18n import ui

from app.components.block_dialog import block_dialog
from app.components.discover_panel import detail_panel
from app.components.skills_prompt import skills_prompt
from app.components.bottom_nav import bottom_nav
from app.components.footer import footer
from app.components.guest_map import guest_map_experience
from app.components.header import header, BRAND_LOGO_SRC, BRAND_LOGO_ALT
from app.components.member_map import member_map_experience
from app.components.onboarding import (
    guided_tour,
    onboarding_flow,
    first_request_celebration,
)
from app.components.paywall import paywall_modal
from app.components.policy_screens import policy_overlay
from app.components.profile_tabs import profile_tabs
from app.components.report_dialog import report_dialog
from app.components.reset_password_panel import reset_password_panel
from app.reminders import reminder_sweep_lifespan
from app.states.password_reset_state import PasswordResetState
from app.components.verify_panel import verify_panel
from app.states.auth_state import AuthState
from app.states.help_share_state import HelpShareState
from app.states.membership_state import MembershipState
from app.states.onboarding_state import OnboardingState
from app.states.profile_state import ProfileState

# Signed-in members with an unfinished progress row see onboarding
# instead of the product. Unverified temporary access can never qualify.
MUST_ONBOARD = AuthState.is_signed_in & OnboardingState.needs_onboarding

# LOADING GATE: while a signed-in session is being restored, onboarding progress
# may not be read
# from the database yet. Rendering the map/profile in that window would flash the
# product at an account that must still complete onboarding, so we keep showing
# the session skeleton until `progress_loaded` flips true.
AWAITING_ONBOARDING_LOAD = (
    AuthState.is_signed_in & OnboardingState.progress_pending
)
SESSION_LOADING = AuthState.checking_session | AWAITING_ONBOARDING_LOAD


def session_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=BRAND_LOGO_SRC,
                alt=BRAND_LOGO_ALT,
                class_name="h-full w-full rounded-full object-cover",
                id="gah-loading-logo-image",
            ),
            id="gah-loading-logo",
            class_name="absolute left-1/2 top-1/2 h-[100px] w-[100px] -translate-x-1/2 -translate-y-1/2 shrink-0 overflow-hidden rounded-full shadow-[0_2px_10px_rgba(70,55,38,0.10)]",
            on_mount=rx.call_script("""
                requestAnimationFrame(() => {
                    const logoImage = document.getElementById('gah-loading-logo-image');
                    if (!logoImage) return;
                    const motion = matchMedia('(prefers-reduced-motion: reduce)');
                    const pulse = logoImage.animate(
                        [{transform:'scale(1)'}, {transform:'scale(.9)'}, {transform:'scale(1)'}],
                        {duration: 3000, iterations: Infinity, easing: 'ease-in-out'}
                    );
                    const sync = () => { if (motion.matches) pulse.cancel(); else pulse.play(); };
                    sync();
                    motion.addEventListener('change', sync);
                    window.gahLoadingCleanup = () => {
                        pulse.cancel();
                        motion.removeEventListener('change', sync);
                        delete window.gahLoadingCleanup;
                    };
                });
            """),
            on_unmount=rx.call_script(
                "window.gahLoadingCleanup?.(); delete window.gahLoadingCleanup;"
            ),
        ),
        rx.el.div(
            rx.cond(
                AuthState.error != "",
                rx.el.p(
                    AuthState.error,
                    role="alert",
                    class_name="rounded-xl border border-[#f7d9a0] bg-white/90 px-4 py-3 text-sm font-medium text-[#374151]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                OnboardingState.error != "",
                rx.el.p(
                    OnboardingState.error,
                    role="alert",
                    class_name="rounded-xl border border-[#f7d9a0] bg-white/90 px-4 py-3 text-sm font-medium text-[#374151]",
                ),
                rx.fragment(),
            ),
            class_name="fixed bottom-[calc(5.5rem+env(safe-area-inset-bottom))] left-1/2 flex w-full max-w-sm -translate-x-1/2 flex-col items-center gap-3 px-4",
        ),
        bottom_nav(loading=True),
        rx.el.span(ui("Loading Go and Help…"), class_name="sr-only"),
        role="status",
        aria_live="polite",
        aria_label=ui("Loading Go and Help"),
        id="gah-session-loading",
        class_name="fixed inset-0 z-[100] flex h-dvh w-full items-center justify-center bg-linear-to-bl from-[#ffe2bd] to-[#d9e9d4] text-[#111827]",
    )


def theme_overrides() -> rx.Component:
    return rx.el.style(
        """
        html:has(.gah-app-shell), body:has(.gah-app-shell), #root:has(.gah-app-shell) { height: 100%; overflow: hidden; }
        .gah-member-section [class*="overflow-y-auto"], .gah-member-section textarea { scrollbar-width: none; -ms-overflow-style: none; }
        .gah-member-section [class*="overflow-y-auto"]::-webkit-scrollbar, .gah-member-section textarea::-webkit-scrollbar { width: 0; height: 0; }
        @media (max-width: 767px) {
            .gah-app-shell, .gah-app-shell *, [data-radix-popper-content-wrapper] * { scrollbar-width: none !important; -ms-overflow-style: none; }
            .gah-app-shell::-webkit-scrollbar, .gah-app-shell *::-webkit-scrollbar, [data-radix-popper-content-wrapper] *::-webkit-scrollbar { display: none; width: 0; height: 0; }
        }
        .gah-screen-scroll { scrollbar-width: none; -ms-overflow-style: none; }
        .gah-screen-scroll::-webkit-scrollbar { width: 0; height: 0; }
        .gah-auth-scroll { scrollbar-width: thin; scrollbar-color: #e08b12 #ffffff; }
        .gah-auth-scroll::-webkit-scrollbar { width: 10px; }
        .gah-auth-scroll::-webkit-scrollbar-track { background: #ffffff; border-radius: 999px; }
        .gah-auth-scroll::-webkit-scrollbar-thumb { background: #e08b12; border-radius: 999px; }
        .gah-auth-scroll::-webkit-scrollbar-thumb:hover { background: #b86e08; }
        .gah-auth-scroll::-webkit-scrollbar-button { display: none; width: 0; height: 0; }
        .membership-scroll { scrollbar-width: thin; scrollbar-color: #fba922 #ffffff; }
        .membership-scroll:hover { scrollbar-color: #e08b12 #ffffff; }
        .membership-scroll::-webkit-scrollbar { width: 10px; }
        .membership-scroll::-webkit-scrollbar-track { background: #ffffff; border-radius: 999px; }
        .membership-scroll::-webkit-scrollbar-thumb { background: #fba922; border-radius: 999px; }
        .membership-scroll::-webkit-scrollbar-thumb:hover { background: #e08b12; }
        .membership-scroll::-webkit-scrollbar-button { display: none; width: 0; height: 0; }
        .gah-app-shell { --gah-surface-shadow: 0 2px 12px rgba(17,24,39,.10); --gah-control-shadow: 0 1px 6px rgba(17,24,39,.10); }
        .gah-app-shell .gah-member-section { background: #ffffff; }
        .gah-app-shell :is(.gah-main-card, .gah-card, .gah-inset-row, details[class*="rounded-2xl"], :is(div,section,article,li)[class*="rounded"]:is([class~="bg-white"],[class~="bg-[#ffffff]"])):not([class*="rounded-full"]):not([role="group"]):not([role="radiogroup"]):not(:has(> input, > textarea, > select)):not(:has(.maplibregl-canvas)):not(.gah-edge-stack > *):not(.gah-profile-membership):not(.gah-onboarding *) { background: #ffffff; border: 0 !important; box-shadow: var(--gah-surface-shadow); }
        .gah-app-shell .gah-inset-row { border-radius: 14px; margin-inline: 0; }
        .gah-app-shell :is(button,a[class*="rounded"][class*="px-"]):not(.gah-edge-stack > button):not(.gah-review-toggle):not(.gah-brand-home):not(.gah-profile-disclosure):not(.gah-request-ask):not(.gah-rating-stars):not(.gah-map-utility):not(.gah-dock-control):not(.gah-segment-control):not(.gah-orange-control):not(.gah-conversation-toggle):not(.gah-search-submit):not(.gah-onboarding *) { border: 1px solid #e5e7eb !important; box-shadow: var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), var(--gah-control-shadow) !important; }
        .gah-app-shell button.gah-topic-filter { border: 0 !important; box-shadow: var(--tw-ring-shadow, 0 0 #0000), var(--gah-surface-shadow) !important; }
        .gah-app-shell button[aria-pressed="true"], .gah-app-shell button[aria-current="page"] { border-color: #fba922 !important; }
        .gah-app-shell .gah-primary-outline { background: #ffffff; color: #111827; }
        .gah-app-shell .gah-primary-outline:hover, .gah-app-shell .gah-primary-outline:focus-visible { background: #fff7e8; border-color: #fba922 !important; }
        .gah-app-shell :is(input,select,textarea) { border-color: #d1d5db; }
        .gah-app-shell :is(button, input:not(#onboarding-username), textarea, select, a, summary):focus-visible { outline: 2px solid #fba922 !important; outline-offset: 2px; --tw-ring-color: #fba922 !important; }
        .gah-app-shell .gah-primary-outline:focus-visible { outline-color: #fba922; }
        .gah-app-shell .gah-chat-composer, .gah-app-shell .gah-compose-body { background: #ffffff; border: 0 !important; box-shadow: 0 0 10px rgba(17,24,39,.12) !important; }
                .gah-app-shell .gah-edge-stack { gap: 0; border-radius: 14px; box-shadow: var(--gah-surface-shadow); }
                .gah-app-shell .gah-edge-stack > :is(article,li,button,details,section,div) { margin: 0; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
                .gah-app-shell .gah-edge-stack > :is(article,li,button,details,section,div) + :is(article,li,button,details,section,div) { border-top: 1px solid #e5e7eb !important; }
                .gah-app-shell .gah-edge-stack > :is(article,li,button,details,section,div):first-child { border-top-left-radius: 14px !important; border-top-right-radius: 14px !important; }
                .gah-app-shell .gah-edge-stack > :is(article,li,button,details,section,div):last-child { border-bottom-left-radius: 14px !important; border-bottom-right-radius: 14px !important; }
        .gah-app-shell .gah-edge-stack > details > summary { border-radius: inherit !important; box-shadow: none !important; }
        .gah-app-shell .gah-review-toggle { border: 0 !important; box-shadow: none !important; }
        button.gah-brand-home, .gah-app-shell button.gah-brand-home { background: transparent !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
        button.gah-brand-home > img { background: transparent; border: 0; box-shadow: none; }
        .gah-app-shell button.gah-profile-disclosure { border: 0 !important; box-shadow: none !important; }
        .gah-app-shell button.gah-request-ask { background: #fba922 !important; border: 1px solid #fba922 !important; box-shadow: none !important; }
                .gah-app-shell button.gah-request-ask:hover { background: #e08b12 !important; }
        .gah-app-shell .gah-search-drawer, .gah-app-shell #map-settings-sheet, .gah-app-shell #map-notifications-sheet { background: rgb(255 255 255 / .6) !important; }
        .gah-app-shell .gah-search-drawer .gah-filter-field, .gah-app-shell .gah-search-drawer .gah-filter-field > span { font-family: Inter, sans-serif; font-size: 14px !important; font-weight: 500 !important; color: #404040; }
        .gah-app-shell .gah-search-drawer .gah-filter-field { height: 40px !important; min-height: 40px; }
        .gah-app-shell .gah-search-drawer .gah-filter-field::placeholder { color: #404040; opacity: 1; }
        .gah-app-shell button.gah-rating-stars { background: transparent !important; border: 0 !important; box-shadow: none !important; }
        .gah-app-shell button.gah-rating-stars:focus-visible { outline: 2px solid #fba922; outline-offset: 2px; }
        .gah-app-shell .gah-profile-screen .gah-disclosure-arrow { background: white; }
        .gah-app-shell .gah-profile-membership { box-shadow: 0 -3px 12px rgba(17,24,39,.10); }
        .gah-app-shell input.gah-location-input:is(:focus, :focus-visible) { border: 1px solid #fba922 !important; outline: none !important; box-shadow: none !important; }
        .gah-app-shell button.gah-primary-outline { border-color: #fba922 !important; }
        .gah-app-shell .gah-chat-composer textarea { background: #ffffff; border: 0; box-shadow: none !important; }
        .gah-app-shell .gah-helper-hand { transform: rotate(45deg); }
        .gah-app-shell :is(input:not(#onboarding-username):not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="button"]):not([type="submit"]):not([type="file"]), textarea, select):is(:focus, :focus-visible) { border: 1px solid #fba922 !important; outline: none !important; box-shadow: none !important; --tw-ring-shadow: 0 0 #0000 !important; }
        .gah-app-shell button.gah-post-request, .gah-app-shell button.gah-primary-outline, .gah-app-shell button.gah-orange-control { border: 1px solid #fba922 !important; }
        .gah-app-shell button.gah-orange-control[aria-current="page"] { border: 1px solid #e08b12 !important; box-shadow: 0 2px 8px rgba(17,24,39,.10) !important; }
        .gah-app-shell button.gah-orange-control.gah-community-tab[aria-current="page"] { border: 1px solid #fba922 !important; box-shadow: none !important; }
        .gah-app-shell [class~="text-[11px]"] { font-size: 14px !important; line-height: 1.5; }
        .gah-app-shell :is(span,p,label)[class~="text-[11px]"] { max-width: 100%; white-space: normal; overflow-wrap: anywhere; height: auto; }
        .gah-app-shell button[class~="text-[11px]"] { height: auto; min-height: 1.75rem; white-space: normal; }
        .gah-app-shell .gah-nav-item[aria-current="page"] { color: #fba922 !important; }
        .gah-app-shell .gah-nav-item:not([aria-current="page"]) { color: #404040 !important; }
        .gah-app-shell button.gah-segment-control { border: 0 !important; box-shadow: none !important; }
        .gah-app-shell .gah-segment-group { box-shadow: var(--gah-control-shadow); }
        .gah-app-shell button.gah-dock-control, .gah-app-shell button.gah-map-utility { background: transparent !important; border: 0 !important; box-shadow: none !important; }
        .gah-app-shell button.gah-dock-control:focus-visible, .gah-app-shell button.gah-map-utility:focus-visible { outline: 2px solid #fba922; outline-offset: 2px; }
        .gah-app-shell .gah-bottom-dock { box-shadow: 0 -3px 12px rgba(17,24,39,.10); }
        .gah-app-shell button.gah-map-utility::before { content: none; }
        .gah-app-shell .gah-search-form .gah-search-inner:is(:focus, :focus-visible), .gah-app-shell .gah-search-form .gah-search-submit { border: 0 !important; box-shadow: none !important; outline: none !important; }
        :is(button,a)[aria-label^="Close"] { color: #b86e08 !important; background: #fff7e8 !important; border: 1px solid #f7d9a0 !important; }
        :is(button,a)[aria-label^="Close"] :is(svg,span) { color: #b86e08 !important; stroke: currentColor !important; }
        :is(button,a):is([aria-label^="Back"],.gah-close-back):not(.gah-inverse-text) { color: #fba922 !important; background: #fff7e8 !important; border-color: #fba922 !important; }
        :is(button,a):is([aria-label^="Back"],.gah-close-back):not(.gah-inverse-text) :is(svg,span) { color: #fba922 !important; stroke: currentColor; }
        .gah-app-shell button.gah-setting-choice[aria-checked="true"] { background: white !important; color: black !important; border: 2px solid #fba922 !important; }
        .gah-distance-range::-webkit-slider-runnable-track { height: 8px; border-radius: 999px; border: 1px solid #d1d5db; background: linear-gradient(to right, #fba922 0%, #fba922 var(--distance-progress,0%), white var(--distance-progress,0%), white 100%); }
        .gah-distance-range::-webkit-slider-thumb { appearance: none; width: 24px; height: 24px; margin-top: -9px; border-radius: 50%; border: 2px solid white; background: #fba922; }
        .gah-distance-range::-moz-range-track { height: 8px; border-radius: 999px; border: 1px solid #d1d5db; background: white; }
        .gah-distance-range::-moz-range-progress { height: 8px; border-radius: 999px; background: #fba922; }
        .gah-distance-range::-moz-range-thumb { width: 24px; height: 24px; border-radius: 50%; border: 2px solid white; background: #fba922; }
        [class~="rounded-3xl"] { border-radius: 22px !important; }
        [class~="rounded-2xl"] { border-radius: 14px !important; }
        [class~="rounded-[2rem]"] { border-radius: 30px !important; }
        """
    )


def index() -> rx.Component:
    """Full-bleed map home for guests and members alike, plus the fixed dock."""
    return rx.el.main(
        theme_overrides(),
        rx.toast.provider(position="top-center"),
        rx.cond(
            SESSION_LOADING,
            session_skeleton(),
            rx.cond(
                AuthState.is_signed_in,
                rx.cond(
                    MUST_ONBOARD,
                    onboarding_flow(),
                    rx.cond(
                        ProfileState.on_map,
                        member_map_experience(),
                        profile_tabs(),
                    ),
                ),
                rx.fragment(
                    guest_map_experience(),
                    rx.el.div(
                        on_mount=HelpShareState.resolve, class_name="hidden"
                    ),
                ),
            ),
        ),
        rx.cond(
            AuthState.is_signed_in & ~MUST_ONBOARD & ~SESSION_LOADING,
            detail_panel(),
            rx.fragment(),
        ),
        rx.cond(
            AuthState.is_signed_in & ~MUST_ONBOARD & ~SESSION_LOADING,
            first_request_celebration(),
            rx.fragment(),
        ),
        paywall_modal(),
        policy_overlay(),
        report_dialog(),
        block_dialog(),
        skills_prompt(),
        rx.cond(MUST_ONBOARD | SESSION_LOADING, rx.fragment(), bottom_nav()),
        rx.cond(MUST_ONBOARD | SESSION_LOADING, rx.fragment(), guided_tour()),
        lang=AuthState.preferred_language,
        custom_attrs={"translate": "no"},
        class_name="gah-app-shell font-['Inter'] h-[100dvh] overflow-hidden w-full flex flex-col bg-[#ffffff] text-[#111827]",
    )


def membership_result_card() -> rx.Component:
    """Server-verified outcome of a Stripe Checkout Session."""
    return rx.el.div(
        rx.match(
            MembershipState.verify_state,
            (
                "verifying",
                rx.el.div(
                    rx.spinner(class_name="h-5 w-5"),
                    rx.el.p(
                        ui("Confirming your payment with Stripe…"),
                        class_name="text-sm font-semibold text-[#4b5563]",
                    ),
                    role="status",
                    class_name="flex items-center gap-3",
                ),
            ),
            (
                "ok",
                rx.el.div(
                    rx.el.span(
                        rx.icon("badge-check", class_name="h-5 w-5"),
                        class_name="flex size-10 items-center justify-center rounded-2xl bg-[#fff7e8] text-[#e08b12]",
                    ),
                    rx.el.h1(
                        ui("Premium Membership"),
                        class_name="mt-3 text-2xl font-bold tracking-tight text-[#111827]",
                    ),
                    rx.el.p(
                        MembershipState.verify_message,
                        class_name="mt-1 text-sm font-medium text-[#4b5563]",
                    ),
                    rx.el.p(
                        MembershipState.post_limit_label,
                        class_name="mt-2 w-fit rounded-full bg-[#fba922] px-3 py-1 text-xs font-bold text-[#111827]",
                    ),
                    class_name="flex flex-col items-start",
                ),
            ),
            (
                "error",
                rx.el.div(
                    rx.el.span(
                        rx.icon("triangle-alert", class_name="h-5 w-5"),
                        class_name="flex size-10 items-center justify-center rounded-2xl bg-[#fff7e8] text-[#e08b12]",
                    ),
                    rx.el.h1(
                        ui("We couldn't confirm that membership"),
                        class_name="mt-3 text-xl font-bold tracking-tight text-[#111827]",
                    ),
                    rx.el.p(
                        MembershipState.verify_message,
                        role="alert",
                        class_name="mt-1 text-sm font-medium text-[#4b5563]",
                    ),
                    class_name="flex flex-col items-start",
                ),
            ),
            rx.el.p(
                ui(
                    "Open this page from your Stripe checkout to confirm a membership."
                ),
                class_name="text-sm font-medium text-[#4b5563]",
            ),
        ),
        rx.el.a(
            rx.icon("map", class_name="h-4 w-4"),
            ui("Back to the map"),
            href="/",
            class_name="mt-5 flex w-fit items-center gap-2 rounded-full bg-[#e08b12] px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08]",
        ),
        class_name="w-full max-w-xl rounded-[2rem] border border-[#f7d9a0] bg-[#ffffff] p-6 sm:p-8",
    )


def membership_success_page() -> rx.Component:
    return rx.el.main(
        theme_overrides(),
        header(),
        rx.el.section(
            rx.el.div(
                membership_result_card(),
                class_name="w-full max-w-[100rem] mx-auto px-4 sm:px-6 py-8 flex justify-center",
            ),
            class_name="w-full flex-1 bg-[#ffffff]",
        ),
        footer(),
        class_name="font-['Inter'] min-h-screen w-full flex flex-col bg-[#ffffff] text-[#111827]",
    )


def verify_page() -> rx.Component:
    return rx.el.main(
        theme_overrides(),
        header(),
        rx.el.section(
            rx.el.div(
                verify_panel(),
                class_name="w-full max-w-[100rem] mx-auto px-4 sm:px-6 py-6 sm:py-8",
            ),
            class_name="w-full flex-1 bg-[#ffffff]",
        ),
        footer(),
        class_name="font-['Inter'] min-h-screen w-full flex flex-col bg-[#ffffff] text-[#111827]",
    )


def reset_password_page() -> rx.Component:
    return rx.el.main(
        theme_overrides(),
        header(),
        rx.el.section(
            rx.el.div(
                reset_password_panel(),
                class_name="w-full max-w-[100rem] mx-auto px-4 sm:px-6 py-8",
            ),
            class_name="w-full flex-1 bg-[#ffffff]",
        ),
        footer(),
        class_name="font-['Inter'] min-h-screen w-full flex flex-col bg-[#ffffff] text-[#111827]",
    )


def map_page() -> rx.Component:
    """Lightweight alias that redirects to the arrival page."""
    return rx.el.main(
        rx.el.p(
            ui("Opening the map…"),
            class_name="text-sm font-medium text-[#4b5563]",
        ),
        class_name="font-['Inter'] flex h-dvh w-full items-center justify-center bg-[#ffffff]",
    )


_app_kwargs = dict(
    stylesheets=[
        "https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css",
        "/map.css",
        "/dark_mode.css",
    ],
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)


app = rx.App(**_app_kwargs)
# Periodic 24h / 1h task reminder sweep.
# blocked, and it is cancelled cleanly when the backend shuts down.
app.register_lifespan_task(reminder_sweep_lifespan)
app.add_page(index, route="/", on_load=AuthState.load_session)
app.add_page(map_page, route="/map", on_load=rx.redirect("/"))
app.add_page(
    membership_success_page,
    route="/membership/success",
    title="Membership confirmed — Go and Help",
    on_load=[AuthState.load_session, MembershipState.verify_checkout],
)
app.add_page(
    verify_page,
    route="/verify",
    title="Confirm your email — Go and Help",
)
app.add_page(
    reset_password_page,
    route="/reset-password",
    title="Choose a new password — Go and Help",
    on_load=PasswordResetState.load_reset,
)
