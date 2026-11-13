"""Quiet helping-green activity dots — never counters.

One small high-contrast green dot with a white ring is the only unread marker
in the app: it sits in the corner of whichever container has new activity.
"""

import reflex as rx


def corner_activity_dot(
    active: rx.Var[bool] | bool,
    label: str = "New activity",
) -> rx.Component:
    """A green corner dot for any `relative` container with activity.

    The parent must carry `relative`. The dot is purely decorative apart from
    its accessible status label, so it never steals a touch target.
    """
    return rx.cond(
        active,
        rx.el.span(
            role="status",
            title=label,
            aria_label=label,
            class_name="pointer-events-none absolute right-2.5 top-2.5 size-2.5 shrink-0 rounded-full border-2 border-white bg-[#fba922]",
        ),
        rx.fragment(),
    )


def activity_dot(count: rx.Var[int]) -> rx.Component:
    """Small solid helping-green dot pinned to a relative parent's corner."""
    return rx.cond(
        count > 0,
        rx.el.span(
            aria_label="New activity",
            role="status",
            title="New activity",
            class_name="pointer-events-none absolute -right-0.5 -top-0.5 size-2.5 shrink-0 rounded-full border-2 border-white bg-[#fba922]",
        ),
        rx.fragment(),
    )
