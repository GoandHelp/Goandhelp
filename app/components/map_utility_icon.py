import reflex as rx


def filled_bell_icon() -> rx.Component:
    return rx.el.span(
        rx.el.svg(
            rx.el.path(
                d="M18 3 C12.5 3 8 7.5 8 13 V20 C8 22.5 6.8 24.7 4.8 26.4 L4 27.2 V29 H13.5 C13.5 29 13.6 29.8 13.9 30.5 C14.7 32.5 16.2 34 18 34 C19.8 34 21.3 32.5 22.1 30.5 C22.4 29.8 22.5 29 22.5 29 H32 V27.2 L31.2 26.4 C29.2 24.7 28 22.5 28 20 V13 C28 7.5 23.5 3 18 3 Z",
                fill="#fba922",
            ),
            view_box="0 0 36 36",
            width="36",
            height="36",
            aria_hidden="true",
            class_name="size-[36px]",
        ),
        aria_hidden="true",
        class_name="pointer-events-none flex size-[36px] items-center justify-center",
    )


def filled_settings_icon() -> rx.Component:
    return rx.el.span(
        rx.el.svg(
            rx.el.path(
                d="M15 2 H21 L22.2 5.2 L25.2 6.5 L28.1 4.9 L31.1 7.9 L29.5 10.8 L30.8 13.8 L34 15 V21 L30.8 22.2 L29.5 25.2 L31.1 28.1 L28.1 31.1 L25.2 29.5 L22.2 30.8 L21 34 H15 L13.8 30.8 L10.8 29.5 L7.9 31.1 L4.9 28.1 L6.5 25.2 L5.2 22.2 L2 21 V15 L5.2 13.8 L6.5 10.8 L4.9 7.9 L7.9 4.9 L10.8 6.5 L13.8 5.2 Z M18 12.5 A5.5 5.5 0 1 0 18 23.5 A5.5 5.5 0 1 0 18 12.5 Z",
                fill="#fba922",
                fill_rule="evenodd",
            ),
            view_box="0 0 36 36",
            width="36",
            height="36",
            aria_hidden="true",
            class_name="size-[36px]",
        ),
        aria_hidden="true",
        class_name="pointer-events-none relative block size-[36px]",
    )


def map_utility_icon(icon: str) -> rx.Component:
    return rx.el.span(
        rx.match(
            icon,
            ("bell", filled_bell_icon()),
            ("cog", filled_settings_icon()),
            ("settings", filled_settings_icon()),
            filled_bell_icon(),
        ),
        aria_hidden="true",
        class_name="pointer-events-none relative block size-[36px]",
    )
