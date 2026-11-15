import reflex as rx

from app.interface_i18n import ui
from app.states.discovery_state import DiscoveryState


def error_banner(message: rx.Var[str] | str) -> rx.Component:
    return rx.cond(
        message,
        rx.el.div(
            rx.icon(
                "circle-alert", class_name="h-4 w-4 text-[#b86e08] shrink-0"
            ),
            rx.el.p(message, class_name="text-sm font-medium text-[#b86e08]"),
            role="alert",
            class_name="flex items-start gap-2 rounded-xl border border-[#e08b12] bg-[#fff7e8] px-4 py-3 w-full",
        ),
        rx.fragment(),
    )


def success_banner(
    message: rx.Var[str] | str, white_text: bool = False, centered: bool = False
) -> rx.Component:
    return rx.cond(
        message,
        rx.el.div(
            rx.icon(
                "circle-check-big",
                class_name=rx.cond(
                    white_text,
                    "h-4 w-4 text-white shrink-0",
                    "h-4 w-4 text-[#111827] shrink-0",
                ),
            ),
            rx.el.p(
                message,
                class_name=rx.cond(
                    white_text,
                    "gah-inverse-text text-sm font-medium text-white",
                    "text-sm font-medium text-[#111827]",
                ),
            ),
            role="status",
            class_name=rx.cond(
                centered,
                "flex items-center justify-center text-center gap-2 rounded-xl border border-[#fba922] bg-[#fba922] px-4 py-3 w-full",
                "flex items-start gap-2 rounded-xl border border-[#fba922] bg-[#fba922] px-4 py-3 w-full",
            ),
        ),
        rx.fragment(),
    )


def _avatar_interface_label(value: str | rx.Var[str]) -> str | rx.Var[str]:
    if isinstance(value, str) and value in {
        "Email verified",
        "Traveller avatar",
        "Contact profile photo",
        "Open member profile",
    }:
        return ui(value)
    return value


def verified_badge(
    verified: rx.Var[bool] | bool,
    label: str | rx.Var[str] = "Email verified",
) -> rx.Component:
    """Small tick overlaid on an avatar when the email address is confirmed.

    This never asserts a real-world identity: the title says `Email verified`.
    """
    return rx.cond(
        verified,
        rx.el.span(
            rx.icon("check", class_name="h-2.5 w-2.5 text-white"),
            title=_avatar_interface_label(label),
            aria_label=_avatar_interface_label(label),
            role="img",
            class_name="absolute -bottom-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full border-2 border-white bg-[#22c55e]",
        ),
        rx.fragment(),
    )


def verified_tick(
    verified: rx.Var[bool] | bool,
    class_name: str = "size-4",
    label: str | rx.Var[str] = "Email verified",
) -> rx.Component:
    """Compact green tick shown inline beside a member's display name.

    Always means email verification only — never identity verification.
    """
    return rx.cond(
        verified,
        rx.el.span(
            rx.icon("check", class_name="h-2.5 w-2.5 text-white"),
            title=_avatar_interface_label(label),
            aria_label=_avatar_interface_label(label),
            role="img",
            class_name=(
                "shrink-0 flex items-center justify-center rounded-full "
                "bg-[#22c55e] " + class_name
            ),
        ),
        rx.fragment(),
    )


def verified_chip(verified: rx.Var[bool] | bool) -> rx.Component:
    """Labelled `Email verified` pill — never called identity verification."""
    return rx.cond(
        verified,
        rx.el.span(
            rx.icon("badge-check", class_name="h-3 w-3 text-white"),
            ui("Email verified"),
            title=ui(
                "Email verified — confirms control of the email address, not real-world identity."
            ),
            aria_label=ui(
                "Email verified — confirms control of the email address, not real-world identity."
            ),
            class_name="w-fit flex items-center gap-1 rounded-full bg-[#22c55e] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white",
        ),
        rx.fragment(),
    )


def avatar_with_tick(
    src: rx.Var[str] | str,
    verified: rx.Var[bool] | bool,
    class_name: str,
    alt: str | rx.Var[str] = "Traveller avatar",
    member_id: rx.Var[int] | int = 0,
    accessible_label: str | rx.Var[str] = "Open member profile",
    verification_label: str | rx.Var[str] = "Email verified",
) -> rx.Component:
    """An avatar image with the small email-verified tick when applicable."""
    return rx.el.div(
        rx.cond(
            member_id > 0,
            rx.el.a(
                rx.image(
                    src=src,
                    alt=_avatar_interface_label(alt),
                    class_name=class_name,
                ),
                href="#",
                aria_label=_avatar_interface_label(accessible_label),
                on_click=DiscoveryState.open_member_profile(
                    member_id
                ).stop_propagation.prevent_default,
                class_name="block rounded-full focus-visible:outline-2 focus-visible:outline-[#fba922]",
            ),
            rx.image(
                src=src, alt=_avatar_interface_label(alt), class_name=class_name
            ),
        ),
        verified_badge(verified, verification_label),
        class_name="relative w-fit shrink-0",
    )


def field_label(label: str, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(
            ui(label), class_name="text-sm font-semibold text-[#111827]"
        ),
        rx.cond(
            hint != "",
            rx.el.span(
                ui(hint), class_name="text-xs font-medium text-[#4b5563]"
            ),
            rx.fragment(),
        ),
        class_name="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 mb-1.5",
    )


INPUT_CLASS = (
    "w-full rounded-xl border border-[#f7d9a0] bg-[#ffffff] px-4 py-2.5 text-sm "
    "font-medium text-[#111827] placeholder:text-[#4b5563] transition-colors "
    "focus:border-[#fba922] focus:ring-0 focus:shadow-none focus:outline-none outline-hidden"
)

SELECT_CLASS = (
    INPUT_CLASS + " appearance-none cursor-pointer pr-10 bg-[#ffffff]"
)


def select_wrapper(select: rx.Component) -> rx.Component:
    return rx.el.div(
        select,
        rx.icon(
            "chevron-down",
            class_name="h-4 w-4 text-[#4b5563] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
        ),
        class_name="relative w-full",
    )
