import reflex as rx

from app.interface_i18n import ui
from app.components.header import brand_mark
from app.components.language_control import language_control


def footer() -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.el.div(
                brand_mark(
                    "size-9 rounded-xl border-2 border-[#e08b12] bg-[#fff7e8] object-cover"
                ),
                rx.el.div(
                    rx.el.p(
                        "Go and Help",
                        class_name="text-sm font-bold tracking-tight text-[#000000]",
                    ),
                    rx.el.p(
                        ui("Community in your hands"),
                        class_name="text-xs font-medium text-[#404040]",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-3",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("globe", class_name="h-3.5 w-3.5 text-[#e08b12]"),
                    ui("Language"),
                    class_name="flex items-center gap-1.5 text-xs font-semibold text-[#404040]",
                ),
                language_control(),
                class_name="flex items-center gap-2",
            ),
            class_name="w-full max-w-[100rem] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 px-4 sm:px-6 py-5",
        ),
        class_name="w-full border-t border-[#d4d4d4] bg-[#ffffff]",
    )
