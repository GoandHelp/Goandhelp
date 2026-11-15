import reflex as rx

from app.states.help_share_state import HelpShareState
from app.interface_i18n import ui, ui_template


def help_share(
    post_id: rx.Var[int],
    title: rx.Var[str],
    context: str,
    position: str = "absolute right-10 top-2 z-30",
) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("share-2", class_name="size-3.5"),
            type="button",
            title=ui_template("Share {title}", "title", title),
            aria_label=ui_template("Share {title}", "title", title),
            aria_expanded=HelpShareState.active_key == f"{context}-{post_id}",
            on_click=HelpShareState.toggle(
                post_id, title, context
            ).stop_propagation,
            class_name="flex size-7 items-center justify-center rounded-lg border border-[#d4d4d4] bg-white text-[#e08b12] hover:bg-[#fff7e8] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
        ),
        rx.cond(
            HelpShareState.active_key == f"{context}-{post_id}",
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        ui("Share request"),
                        class_name="text-xs font-bold text-black",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="size-4"),
                        type="button",
                        aria_label=ui("Close share options"),
                        on_click=HelpShareState.close,
                        class_name="flex size-7 items-center justify-center rounded-full text-[#e08b12] hover:bg-[#fff7e8] focus-visible:outline-2",
                    ),
                    class_name="flex items-center justify-between gap-2",
                ),
                rx.foreach(
                    HelpShareState.links,
                    lambda link: rx.el.a(
                        link["label"],
                        rx.icon("external-link", class_name="size-3"),
                        href=link["href"],
                        target="_blank",
                        rel="noopener noreferrer",
                        aria_label=ui_template(
                            "Share via {service} (opens a new window)",
                            "service",
                            link["label"],
                        ),
                        class_name="flex min-h-9 items-center justify-between rounded-lg px-2 text-xs font-medium text-[#e08b12] hover:bg-[#fff7e8] focus-visible:outline-2",
                    ),
                ),
                rx.el.button(
                    rx.icon("copy", class_name="size-3.5"),
                    ui("Copy link"),
                    type="button",
                    on_click=rx.set_clipboard(HelpShareState.url),
                    class_name="flex min-h-9 w-full items-center justify-center gap-2 rounded-full bg-[#fba922] text-xs font-bold text-black hover:bg-[#e08b12] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
                ),
                role="group",
                aria_label=ui("Share this help request"),
                class_name="absolute right-0 top-9 z-50 w-44 break-words rounded-xl border border-[#f7d9a0] bg-white p-2",
            ),
            rx.fragment(),
        ),
        class_name=position,
    )
