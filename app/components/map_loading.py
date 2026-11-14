import reflex as rx

from app.interface_i18n import ui


def map_loading_logo() -> rx.Component:
    return rx.el.div(
        ui("Updating map…"),
        role="status",
        aria_live="polite",
        aria_label=ui("Updating map"),
        class_name="sr-only",
    )
