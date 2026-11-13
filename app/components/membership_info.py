"""Free vs Premium membership comparison shown in Profile > More information."""

import reflex as rx

from app.states.membership_state import MembershipState


def benefit_line(line: rx.Var[str], icon: str, tone: str) -> rx.Component:
    return rx.el.li(
        rx.icon(
            icon,
            class_name=rx.cond(
                tone == "text-[#22c55e]",
                "mt-0.5 h-4 w-4 shrink-0 text-[#22c55e]",
                "mt-0.5 h-4 w-4 shrink-0 text-[#fba922]",
            ),
        ),
        rx.el.span(
            line,
            class_name="min-w-0 text-left text-[12px] font-semibold leading-relaxed text-[#35406f]",
        ),
        class_name="flex w-full items-start justify-start gap-4",
    )


def free_line(line: rx.Var[str]) -> rx.Component:
    return benefit_line(line, "check", "text-[#22c55e]")


def premium_line(line: rx.Var[str]) -> rx.Component:
    return benefit_line(line, "check-check", "text-[#fba922]")


def comparison_column(
    title: str,
    price: rx.Var[str] | str,
    icon: str,
    tile: str,
    lines: rx.Var[list[str]],
    renderer,
    is_current: rx.Var[bool],
    border: str,
    badge: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon(icon, class_name="h-4 w-4"), class_name=tile
                ),
                rx.el.h4(
                    title,
                    class_name=rx.cond(
                        border == "premium",
                        "text-sm font-bold tracking-tight text-[#fba922] text-left",
                        "text-sm font-bold tracking-tight text-[#22c55e] text-left",
                    ),
                ),
                rx.cond(
                    is_current,
                    rx.el.span("Your tier", class_name=badge),
                    rx.fragment(),
                ),
                class_name="flex w-full flex-wrap items-center justify-start gap-2",
            ),
            rx.el.p(
                price,
                class_name="pl-11 text-left text-[11px] font-bold text-[#68708f]",
            ),
            class_name="flex w-full flex-col items-start gap-2",
        ),
        rx.el.ul(
            rx.foreach(lines, renderer),
            class_name="mt-3 flex w-full min-w-0 flex-col gap-2 pl-3 sm:pl-5",
        ),
        class_name=rx.cond(
            border == "premium",
            "flex w-full min-w-0 flex-col bg-white px-4 py-4",
            "flex w-full min-w-0 flex-col border-t border-[#e5e7eb] bg-white px-4 py-4 md:border-t-0 md:border-l",
        ),
    )


def membership_information_section() -> rx.Component:
    """Accessible Free vs Premium comparison, stacked on small screens."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Membership information",
                    id="membership-information",
                    class_name="text-lg font-bold tracking-tight text-[#172044] text-center",
                ),
                rx.el.p(
                    "Unlock more as a Premium Member",
                    class_name="mt-0.5 text-xs font-medium leading-relaxed text-[#4b5563] text-center",
                ),
                class_name="min-w-0 w-full flex-1 text-center",
            ),
            class_name="flex w-full items-start gap-3",
        ),
        rx.el.div(
            comparison_column(
                "Premium members",
                f"{MembershipState.coffee_price_label} / $49 annually",
                "user-round-check",
                "flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8] text-[#fba922]",
                MembershipState.premium_benefits,
                premium_line,
                MembershipState.is_premium,
                "premium",
                "w-fit shrink-0 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-[#fba922]",
            ),
            comparison_column(
                "Free members",
                "Always free",
                "user",
                "flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#dcfce7] text-[#22c55e]",
                MembershipState.free_benefits,
                free_line,
                ~MembershipState.is_premium,
                "free",
                "w-fit shrink-0 rounded-full bg-[#dcfce7] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-[#22c55e]",
            ),
            role="group",
            aria_labelledby="membership-information",
            class_name="mt-3 grid w-full grid-cols-1 gap-0 overflow-hidden rounded-xl border border-[#e5e7eb] bg-white md:grid-cols-2",
        ),
        rx.cond(
            MembershipState.is_premium,
            rx.el.p(
                "Premium is active on this account, including the Metrics "
                "Information section on this page.",
                class_name="mt-3 text-center text-[11px] font-semibold text-[#fba922]",
            ),
            rx.el.button(
                rx.icon("arrow-up-right", class_name="h-4 w-4"),
                "See premium membership",
                type="button",
                aria_label="See premium membership options",
                on_click=lambda: MembershipState.open_paywall(""),
                class_name="gah-orange-control bg-[#fba922] hover:bg-[#e08b12] text-black shadow-[0_1px_6px_rgba(17,24,39,0.10)] border border-[#fba922] mx-auto mt-3 flex min-h-11 w-fit items-center gap-2 rounded-full px-5 py-2.5 text-sm font-bold transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
        ),
        aria_label="Membership information",
        class_name="gah-profile-membership w-full min-w-0 rounded-2xl bg-white px-4 py-4 sm:px-5",
    )
