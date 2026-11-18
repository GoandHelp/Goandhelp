import reflex as rx

from app.interface_i18n import ui


_COUNTED_TEMPLATES: dict[str, tuple[str, ...]] = {
    "Confirmed Help": (
        "{count} upcoming jobs",
        "{count} Confirmed job",
        "{count} Confirmed jobs",
    ),
    "Confirmed Helpers": (
        "{count} Confirmed helper",
        "{count} Confirmed helpers",
    ),
    "Events": ("{count} Event", "{count} Events"),
    "Hosted events": ("{count} Hosted event", "{count} Hosted events"),
    "Your help requests": ("{count} Help request", "{count} Help requests"),
    "Saved search alerts": (
        "{count} Search alerts",
        "{count} search alert",
        "{count} search alerts",
    ),
    "Bookmarked help requests": (
        "{count} Bookmarked help request",
        "{count} Bookmarked help requests",
    ),
    "Offers to help you": (
        "{count} Offer to help you",
        "{count} Offers to help you",
    ),
    "Requests for your help": (
        "{count} Request for your help",
        "{count} Requests for your help",
    ),
}


def styled_count_template(
    template: rx.Var[str], count: rx.Var[int]
) -> rx.Component:
    pieces = template.split("{count}")
    return rx.fragment(
        pieces[0],
        rx.el.span(count, class_name="text-[#e08b12]"),
        pieces[1],
    )


def _counted_template(
    title: str | rx.Var[str], count: rx.Var[int]
) -> rx.Var[str]:
    return rx.match(
        title,
        (
            "Confirmed Help",
            rx.cond(
                count == 0,
                _COUNTED_TEMPLATES["Confirmed Help"][0],
                rx.cond(
                    count == 1,
                    _COUNTED_TEMPLATES["Confirmed Help"][1],
                    _COUNTED_TEMPLATES["Confirmed Help"][2],
                ),
            ),
        ),
        (
            "Confirmed Helpers",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Confirmed Helpers"][0],
                _COUNTED_TEMPLATES["Confirmed Helpers"][1],
            ),
        ),
        (
            "Events",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Events"][0],
                _COUNTED_TEMPLATES["Events"][1],
            ),
        ),
        (
            "Hosted events",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Hosted events"][0],
                _COUNTED_TEMPLATES["Hosted events"][1],
            ),
        ),
        (
            "Your help requests",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Your help requests"][0],
                _COUNTED_TEMPLATES["Your help requests"][1],
            ),
        ),
        (
            "Saved search alerts",
            rx.cond(
                count == 0,
                _COUNTED_TEMPLATES["Saved search alerts"][0],
                rx.cond(
                    count == 1,
                    _COUNTED_TEMPLATES["Saved search alerts"][1],
                    _COUNTED_TEMPLATES["Saved search alerts"][2],
                ),
            ),
        ),
        (
            "Bookmarked help requests",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Bookmarked help requests"][0],
                _COUNTED_TEMPLATES["Bookmarked help requests"][1],
            ),
        ),
        (
            "Offers to help you",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Offers to help you"][0],
                _COUNTED_TEMPLATES["Offers to help you"][1],
            ),
        ),
        (
            "Requests for your help",
            rx.cond(
                count == 1,
                _COUNTED_TEMPLATES["Requests for your help"][0],
                _COUNTED_TEMPLATES["Requests for your help"][1],
            ),
        ),
        "",
    ).to(str)


def _localized_subtitle(subtitle: str | rx.Var[str]) -> rx.Var[str] | str:
    return rx.match(
        subtitle,
        ("Get ready to help others", ui("Get ready to help others")),
        ("People ready to help you", ui("People ready to help you")),
        (
            "Requests you have already posted",
            ui("Requests you have already posted"),
        ),
        ("Join many helping hands", ui("Join many helping hands")),
        ("Manage helpers for your event", ui("Manage helpers for your event")),
        (
            "Get notified with matching help requests",
            ui("Get notified with matching help requests"),
        ),
        (
            "Help requests you bookmarked in map or list view.",
            ui("Help requests you bookmarked in map or list view."),
        ),
        subtitle,
    )


def request_heading(
    title: str | rx.Var[str],
    count: rx.Var[int],
    subtitle: str | rx.Var[str] = "",
    icon: str = "",
) -> rx.Component:
    template = _counted_template(title, count)
    known_heading = rx.match(
        title,
        (
            "Confirmed Help",
            styled_count_template(ui(template), count),
        ),
        (
            "Confirmed Helpers",
            styled_count_template(ui(template), count),
        ),
        ("Events", styled_count_template(ui(template), count)),
        ("Hosted events", styled_count_template(ui(template), count)),
        (
            "Your help requests",
            styled_count_template(ui(template), count),
        ),
        (
            "Saved search alerts",
            styled_count_template(ui(template), count),
        ),
        (
            "Bookmarked help requests",
            styled_count_template(ui(template), count),
        ),
        ("Offers to help you", styled_count_template(ui(template), count)),
        (
            "Requests for your help",
            styled_count_template(ui(template), count),
        ),
        rx.fragment(
            rx.el.span(count, class_name="text-[#e08b12]"),
            " ",
            title,
        ),
    )
    localized_subtitle = _localized_subtitle(subtitle)
    return rx.el.div(
        rx.el.h3(
            known_heading,
            class_name="w-full px-2 text-center text-xl sm:text-2xl font-bold tracking-tight leading-tight text-[#111827]",
        ),
        rx.cond(
            subtitle != "",
            rx.el.p(
                localized_subtitle,
                class_name="mt-0 text-center text-sm font-medium text-[#4b5563]",
            ),
            rx.fragment(),
        ),
        class_name="mt-2 w-full min-w-0 mb-0",
    )
