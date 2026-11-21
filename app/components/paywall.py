"""Premium membership surfaces: paywall modal, status card and notices."""

import reflex as rx

from app.interface_i18n import ui
from app.components.header import BRAND_LOGO_SRC, BRAND_LOGO_ALT
from app.states.membership_state import MembershipState, NoticeItem
from app.skill_categories import CATEGORY_UPGRADE_REASON
from app.states.community_state import (
    FORUM_TOPIC_REASON,
    FORUM_COMMENT_REASON,
    FORUM_TOPIC_CAP,
    FORUM_COMMENT_CAP,
)

COFFEE_PLAN = "coffee_monthly"
DINNER_PLAN = "dinner_annual"
PAYMENT_ACTION_CLASS = "flex min-h-12 w-full items-center justify-center gap-2 rounded-full bg-[#fba922] bg-[linear-gradient(300deg,#fba922_0%,#ffda91_50%,#fba922_100%)] px-4 py-3 text-base font-bold text-[#111827] transition-[filter,background-color] hover:brightness-95 focus:outline-hidden focus-visible:ring-4 focus-visible:ring-[#fba922]/40 disabled:cursor-not-allowed disabled:bg-none disabled:bg-[#e5e5e5] disabled:text-[#111827]/70 disabled:brightness-100"


def benefit_marker(line: str) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "check",
            class_name="h-3.5 w-3.5 shrink-0 text-[#fba922]",
        ),
        rx.el.span(
            line,
            class_name="min-w-0 text-[12px] font-semibold leading-snug text-[#111827]",
        ),
        class_name="grid w-full grid-cols-[1rem_minmax(0,1fr)] items-start gap-4 text-left",
    )


def transit_ticket(
    selected: rx.Var[bool], tone: str = "purple"
) -> rx.Component:
    return rx.el.span(
        rx.el.span(
            rx.el.span(
                class_name="absolute left-0 top-1/2 size-2 -translate-x-1 -translate-y-1/2 rounded-full bg-white"
            ),
            rx.el.span(
                class_name="absolute right-0 top-1/2 size-2 translate-x-1 -translate-y-1/2 rounded-full bg-white"
            ),
            rx.icon("bus-front", class_name="size-4"),
            rx.el.span(
                rx.cond(tone == "green", "PASS", "TICKET"),
                class_name="text-[8px] font-bold tracking-[0.22em]",
            ),
            class_name=rx.cond(
                tone == "green",
                "relative flex h-9 w-[4.75rem] rotate-[-20deg] scale-[0.85] items-center justify-center gap-1 rounded-[6px] border-2 border-dashed border-[#e08b12] bg-[#fba922] text-[#111827]",
                "relative flex h-9 w-[4.75rem] rotate-[-20deg] scale-[0.85] items-center justify-center gap-1 rounded-[6px] border-2 border-dashed border-[#fba922] bg-white text-[#fba922]",
            ),
        ),
        aria_hidden="true",
        class_name="flex h-12 w-[5rem] shrink-0 items-center justify-center",
    )


def free_marker(line: str) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "minus",
            class_name="h-3.5 w-3.5 shrink-0 text-[#4b5563]",
        ),
        rx.el.span(
            line,
            class_name="min-w-0 text-left text-[12px] font-medium leading-snug text-[#4b5563]",
        ),
        class_name="grid w-full grid-cols-[1rem_minmax(0,1fr)] items-start gap-4 text-left",
    )


def ticket_to_ride_choice() -> rx.Component:
    return rx.el.button(
        rx.el.div(
            transit_ticket(MembershipState.coffee_selected, "purple"),
            rx.el.div(
                rx.el.p(
                    "Monthly Ticket",
                    class_name="text-base font-bold tracking-tight text-[#e08b12]",
                ),
                rx.el.p(
                    MembershipState.coffee_price_label,
                    class_name="text-sm font-semibold text-black",
                ),
                class_name="min-w-0 text-left",
            ),
            class_name="flex items-center gap-3",
        ),
        rx.el.p(
            "Unlock all benefits, cancel anytime",
            class_name="mt-2 w-full pl-[5.75rem] text-left text-[12px] font-medium leading-snug text-[#4b5563]",
        ),
        type="button",
        role="radio",
        aria_checked=rx.cond(MembershipState.coffee_selected, "true", "false"),
        aria_label="Choose the Monthly Ticket, $5 monthly",
        on_click=lambda: MembershipState.select_plan(COFFEE_PLAN),
        class_name=rx.cond(
            MembershipState.coffee_selected,
            "flex w-full flex-col rounded-[1.4rem] border-2 border-[#e08b12] bg-white p-4 text-left transition-colors",
            "flex w-full flex-col rounded-[1.4rem] border border-[#e5e5e5] bg-white p-4 text-left transition-colors hover:border-[#e08b12]",
        ),
    )


def annual_pass_choice() -> rx.Component:
    return rx.el.button(
        rx.el.div(
            transit_ticket(MembershipState.dinner_selected, "green"),
            rx.el.div(
                rx.el.p(
                    "Annual pass",
                    class_name="text-base font-bold tracking-tight text-[#fba922]",
                ),
                rx.el.p(
                    MembershipState.dinner_price_label,
                    class_name="text-sm font-semibold text-[#111827]",
                ),
                class_name="min-w-0 text-left",
            ),
            class_name="flex items-center gap-3",
        ),
        rx.el.p(
            "Unlock all benefits, cancel anytime",
            class_name="mt-2 w-full pl-[5.75rem] text-left text-[12px] font-medium leading-snug text-[#4b5563]",
        ),
        type="button",
        role="radio",
        aria_checked=rx.cond(MembershipState.dinner_selected, "true", "false"),
        aria_label="Choose the Annual pass, $49 annually",
        on_click=lambda: MembershipState.select_plan(DINNER_PLAN),
        class_name=rx.cond(
            MembershipState.dinner_selected,
            "flex w-full flex-col rounded-[1.4rem] border-2 border-[#e08b12] bg-white p-4 text-left transition-colors",
            "flex w-full flex-col rounded-[1.4rem] border border-[#e5e5e5] bg-white p-4 text-left transition-colors hover:border-[#e08b12]",
        ),
    )


def comparison_rail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                "Premium members get",
                class_name="text-center text-[11px] font-bold uppercase tracking-[0.12em] text-[#fba922]",
            ),
            rx.el.div(
                rx.foreach(MembershipState.premium_benefits, benefit_marker),
                class_name="mt-2 flex w-full min-w-0 flex-col gap-2 pl-3 sm:pl-5",
            ),
            class_name="w-full rounded-2xl border border-[#fba922] bg-white p-4",
        ),
        rx.el.div(
            rx.el.p(
                "Free stays free",
                class_name="text-center text-[11px] font-bold uppercase tracking-[0.12em] text-[#4b5563]",
            ),
            rx.el.div(
                rx.foreach(MembershipState.free_benefits, free_marker),
                class_name="mt-2 flex w-full min-w-0 flex-col gap-2 pl-3 sm:pl-5",
            ),
            class_name="w-full rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-4 text-center",
        ),
        class_name="grid grid-cols-1 gap-3 w-full",
    )


def paywall_header() -> rx.Component:
    """Company logo on the left, centred word-mark lockup on the right."""
    return rx.el.div(
        rx.image(
            src=BRAND_LOGO_SRC,
            alt=BRAND_LOGO_ALT,
            class_name="size-11 sm:size-12 shrink-0 rounded-full object-contain",
        ),
        rx.el.div(
            rx.el.h2(
                "Go and Help",
                id="paywall-title",
                class_name="text-xl sm:text-2xl font-bold tracking-tight leading-tight text-[#111827]",
            ),
            rx.el.p(
                ui("Community in your hands"),
                class_name="text-[12px] font-semibold text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1 -translate-x-[3px] text-left",
        ),
        class_name="flex items-center gap-3",
    )


def paywall_modal() -> rx.Component:
    """In-app premium membership surface, opened from any gated action."""
    return rx.cond(
        MembershipState.paywall_open,
        rx.el.div(
            rx.el.div(
                class_name="absolute inset-0 bg-[#111827]/55 backdrop-blur-sm",
                on_click=MembershipState.close_paywall,
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        paywall_header(),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            type="button",
                            title="Close membership panel",
                            aria_label="Close membership panel",
                            on_click=MembershipState.close_paywall,
                            class_name="flex size-8 shrink-0 items-center justify-center rounded-full border border-[#d4d4d4] bg-white text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                        ),
                        class_name="flex items-start justify-between gap-3",
                    ),
                    rx.el.h3(
                        "Become a Premium Member",
                        class_name="text-center text-2xl sm:text-3xl font-bold tracking-tight leading-tight text-[#fba922]",
                    ),
                    rx.el.p(
                        rx.cond(
                            MembershipState.upgrade_reason
                            == CATEGORY_UPGRADE_REASON,
                            "Unlock multiple categories to your help request and increase your chances of receiving help",
                            rx.cond(
                                MembershipState.upgrade_reason != "",
                                rx.match(
                                    MembershipState.upgrade_reason,
                                    (
                                        FORUM_TOPIC_REASON,
                                        ui(FORUM_TOPIC_REASON),
                                    ),
                                    (
                                        FORUM_COMMENT_REASON,
                                        ui(FORUM_COMMENT_REASON),
                                    ),
                                    MembershipState.upgrade_reason,
                                ),
                                "Select Monthly or Yearly. Both unlock all benefits",
                            ),
                        ),
                        class_name="text-center text-[12px] font-semibold leading-relaxed text-[#4b5563]",
                    ),
                    rx.match(
                        MembershipState.upgrade_reason,
                        (
                            FORUM_TOPIC_REASON,
                            rx.el.p(
                                ui(FORUM_TOPIC_CAP),
                                class_name="text-center text-xs font-medium text-[#4b5563]",
                            ),
                        ),
                        (
                            FORUM_COMMENT_REASON,
                            rx.el.p(
                                ui(FORUM_COMMENT_CAP),
                                class_name="text-center text-xs font-medium text-[#4b5563]",
                            ),
                        ),
                        rx.fragment(),
                    ),
                    rx.el.div(
                        ticket_to_ride_choice(),
                        annual_pass_choice(),
                        role="radiogroup",
                        aria_label="Choose your membership",
                        class_name="grid grid-cols-1 gap-3 w-full sm:grid-cols-2",
                    ),
                    comparison_rail(),
                    rx.cond(
                        MembershipState.error,
                        rx.el.p(
                            MembershipState.error,
                            role="alert",
                            class_name="w-full rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-3.5 py-2.5 text-[12px] font-semibold leading-relaxed text-[#e08b12]",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.button(
                        rx.cond(
                            MembershipState.checkout_busy,
                            rx.spinner(class_name="h-4 w-4"),
                            rx.icon("credit-card", class_name="h-4 w-4"),
                        ),
                        rx.cond(
                            MembershipState.checkout_busy,
                            "Opening secure checkout…",
                            "Start My Subscription",
                        ),
                        type="button",
                        disabled=MembershipState.checkout_busy,
                        aria_label=(
                            "Start My Subscription — continue to secure "
                            "Stripe checkout"
                        ),
                        aria_busy=rx.cond(
                            MembershipState.checkout_busy, "true", "false"
                        ),
                        on_click=MembershipState.start_checkout,
                        class_name=PAYMENT_ACTION_CLASS,
                    ),
                    rx.el.p(
                        "Payments are handled by Stripe.",
                        class_name="text-center text-[10px] font-medium text-[#4b5563]",
                    ),
                    class_name="membership-scroll flex w-full max-h-[inherit] flex-col gap-3 overflow-y-auto overscroll-contain p-4 sm:p-5",
                    style={"scrollbarGutter": "stable", "maxHeight": "90vh"},
                ),
                role="dialog",
                aria_modal="true",
                aria_labelledby="paywall-title",
                class_name="relative z-10 w-full max-w-xl max-h-[90vh] overflow-hidden rounded-[2rem] border-2 border-[#e08b12] bg-[#ffffff]",
            ),
            class_name="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-6",
        ),
        rx.fragment(),
    )


def membership_status_card() -> rx.Component:
    """Profile entry point: current tier plus the upgrade / manage actions."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.cond(
                    MembershipState.is_premium,
                    rx.el.span(
                        rx.icon("badge-check", class_name="h-3.5 w-3.5"),
                        MembershipState.tier_name,
                        class_name="w-fit flex items-center gap-2 rounded-full bg-[#fba922] px-3 py-1 text-xs font-semibold text-[#111827]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    MembershipState.is_premium,
                    rx.el.h2(
                        "Your premium membership is active.",
                        class_name="mt-3 text-xl font-bold tracking-tight text-[#111827]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    MembershipState.is_premium,
                    rx.el.p(
                        MembershipState.post_limit_label,
                        class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    MembershipState.renewal_label,
                    rx.el.p(
                        MembershipState.renewal_label,
                        class_name="mt-1 text-xs font-semibold text-[#111827]",
                    ),
                    rx.fragment(),
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.cond(
                    MembershipState.is_premium,
                    rx.fragment(),
                    rx.el.button(
                        rx.icon("ticket", class_name="h-4 w-4"),
                        "See Premium Membership",
                        type="button",
                        aria_label="Open the premium membership panel",
                        on_click=lambda: MembershipState.open_paywall(""),
                        class_name="flex w-full sm:w-fit items-center justify-center gap-2 rounded-full border border-[#e08b12] bg-[#fba922] px-4 py-2.5 text-sm font-bold text-[#111827] transition-colors hover:bg-[#e08b12] hover:text-[#111827]",
                    ),
                ),
                rx.cond(
                    MembershipState.has_billing_account,
                    rx.el.button(
                        rx.icon("receipt", class_name="h-4 w-4"),
                        "Manage or cancel",
                        type="button",
                        aria_label="Manage or cancel your membership in Stripe",
                        on_click=MembershipState.open_billing_portal,
                        class_name="flex w-full sm:w-fit items-center justify-center gap-2 rounded-full border border-[#d4d4d4] bg-white px-4 py-2.5 text-sm font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                class_name="flex w-full sm:w-fit shrink-0 flex-col gap-2",
            ),
            class_name="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 w-full",
        ),
        rx.cond(
            MembershipState.error,
            rx.el.p(
                MembershipState.error,
                role="alert",
                class_name="mt-3 w-full rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-3.5 py-2.5 text-xs font-semibold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-[2rem] border border-[#e5e5e5] bg-[#ffffff] p-5 sm:p-6",
    )


def notice_row(notice: NoticeItem) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "alarm-clock",
                class_name="mt-0.5 h-4 w-4 shrink-0 text-[#e08b12]",
            ),
            rx.el.div(
                rx.el.p(
                    notice["title"],
                    class_name="text-sm font-bold text-[#111827]",
                ),
                rx.el.p(
                    notice["body"],
                    class_name="mt-1 text-xs font-medium leading-relaxed text-[#4b5563]",
                ),
                rx.el.p(
                    notice["created"],
                    class_name="mt-1 text-[10px] font-semibold uppercase tracking-wide text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-2",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("sparkles", class_name="h-3.5 w-3.5"),
                "Upgrade",
                type="button",
                aria_label="Open the premium membership panel",
                on_click=lambda: MembershipState.open_paywall(
                    "Premium posts stay visible for a whole year."
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1.5 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12]",
            ),
            rx.el.button(
                "Dismiss",
                type="button",
                aria_label="Dismiss this membership notice",
                on_click=lambda: MembershipState.dismiss_notice(notice["id"]),
                class_name="w-fit rounded-full border border-[#d4d4d4] bg-white px-3 py-1.5 text-xs font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12]",
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        class_name="w-full rounded-2xl border border-[#d4d4d4] bg-[#ffffff] p-4",
    )


def membership_notices_panel() -> rx.Component:
    """Unread expiry / membership notices with a direct upgrade CTA."""
    return rx.cond(
        MembershipState.has_notices,
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Membership notices",
                    class_name="text-base font-bold tracking-tight text-[#111827]",
                ),
                rx.el.span(
                    MembershipState.notice_count_label,
                    class_name="w-fit rounded-full bg-[#fba922] px-3 py-1 text-xs font-semibold text-[#111827]",
                ),
                class_name="flex flex-wrap items-center justify-between gap-2 w-full",
            ),
            rx.el.div(
                rx.foreach(
                    MembershipState.notices,
                    lambda notice: notice_row(notice),
                ),
                class_name="mt-3 flex w-full flex-col gap-3",
            ),
            class_name="w-full rounded-[2rem] border border-[#e5e5e5] bg-white p-5 sm:p-6",
        ),
        rx.fragment(),
    )


def premium_lock_button(label: str, reason: str) -> rx.Component:
    """A visibly locked control that opens the paywall when used."""
    return rx.el.button(
        rx.icon("lock", class_name="h-3.5 w-3.5"),
        label,
        type="button",
        aria_label=f"{label} — premium membership required",
        on_click=lambda: MembershipState.open_paywall(reason),
        class_name="w-fit flex items-center gap-1.5 rounded-full border border-dashed border-[#e08b12] bg-[#fba922] px-3 py-1.5 text-xs font-semibold text-[#111827] transition-colors hover:border-[#e08b12]",
    )
