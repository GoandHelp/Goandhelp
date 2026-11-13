import reflex as rx


def request_heading(
    title: str, count: rx.Var[int], subtitle: str = "", icon: str = ""
) -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            rx.cond(
                (title == "Confirmed Help") & (count == 0),
                rx.fragment(
                    rx.el.span("0", class_name="text-[#e08b12]"),
                    " upcoming jobs",
                ),
                rx.fragment(
                    rx.el.span(count, class_name="text-[#e08b12]"),
                    " ",
                    rx.match(
                        title,
                        (
                            "Confirmed Help",
                            rx.cond(
                                count == 1, "Confirmed job", "Confirmed jobs"
                            ),
                        ),
                        (
                            "Confirmed Helpers",
                            rx.cond(
                                count == 1,
                                "Confirmed helper",
                                "Confirmed helpers",
                            ),
                        ),
                        ("Events", rx.cond(count == 1, "Event", "Events")),
                        (
                            "Hosted events",
                            rx.cond(
                                count == 1, "Hosted event", "Hosted events"
                            ),
                        ),
                        (
                            "Your help requests",
                            rx.cond(
                                count == 1, "Help request", "Help requests"
                            ),
                        ),
                        (
                            "Saved search alerts",
                            rx.match(
                                count,
                                (0, "Search alerts"),
                                (1, "search alert"),
                                "search alerts",
                            ),
                        ),
                        (
                            "Bookmarked help requests",
                            rx.cond(
                                count == 1,
                                "Bookmarked help request",
                                "Bookmarked help requests",
                            ),
                        ),
                        (
                            "Offers to help you",
                            rx.cond(
                                count == 1,
                                "Offer to help you",
                                "Offers to help you",
                            ),
                        ),
                        (
                            "Requests for your help",
                            rx.cond(
                                count == 1,
                                "Request for your help",
                                "Requests for your help",
                            ),
                        ),
                        title,
                    ),
                ),
            ),
            class_name="w-full px-2 text-center text-xl sm:text-2xl font-bold tracking-tight leading-tight text-[#111827]",
        ),
        rx.cond(
            subtitle != "",
            rx.el.p(
                subtitle,
                class_name="mt-0 text-center text-sm font-medium text-[#4b5563]",
            ),
            rx.fragment(),
        ),
        class_name="mt-2 w-full min-w-0 mb-0",
    )
