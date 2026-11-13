import reflex as rx


def map_loading_logo() -> rx.Component:
    return rx.el.div(
        "Updating map…",
        role="status",
        aria_live="polite",
        aria_label="Updating map",
        class_name="sr-only",
    )
