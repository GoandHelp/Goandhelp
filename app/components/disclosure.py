import reflex as rx


def record_summary(
    leading: rx.Component,
    title: rx.Var[str] | str,
    metadata: rx.Var[str] | str,
    status: rx.Var[str] | str,
) -> rx.Component:
    return rx.el.summary(
        leading,
        rx.el.span(
            rx.el.span(
                title,
                class_name="block text-sm font-bold text-black break-words",
            ),
            rx.el.span(
                metadata,
                class_name="mt-1 block text-xs font-medium text-[#e08b12] break-words",
            ),
            rx.el.span(
                status,
                class_name="mt-1 block text-[11px] font-semibold text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1",
        ),
        disclosure_arrow(),
        class_name="flex w-full cursor-pointer list-none items-center gap-3 rounded-2xl p-4 text-left hover:bg-[#f9fafb] focus-visible:outline-2 focus-visible:outline-[#e08b12] [&::-webkit-details-marker]:hidden",
    )


def record_disclosure(
    summary: rx.Component, body: rx.Component, **props
) -> rx.Component:
    return rx.el.details(
        summary,
        rx.el.div(
            body, class_name="w-full border-t border-[#e5e5e5] px-4 pb-4 pt-3"
        ),
        class_name="relative w-full rounded-2xl border border-[#e5e5e5] bg-white text-black [&[open]>summary>span:last-child_svg]:rotate-180",
        **props,
    )


def disclosure_arrow(
    open_var: rx.Var[bool] | bool = False, close_icon: str = "chevron-up"
) -> rx.Component:
    return rx.el.span(
        rx.icon(
            rx.cond(open_var, close_icon, "chevron-down"),
            class_name="size-4 transition-transform group-open/verification:rotate-180 motion-reduce:transition-none",
        ),
        aria_hidden=True,
        class_name="gah-disclosure-arrow flex size-7 shrink-0 items-center justify-center rounded-full border border-[#d4d4d4] bg-white text-[#4b5563]",
    )
