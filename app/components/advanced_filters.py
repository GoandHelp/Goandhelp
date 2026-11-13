"""Premium advanced search controls inside the member map filter drawer."""

import reflex as rx

from app.interface_i18n import ui, ui_template

from app.components.feedback import select_wrapper
from app.states.discovery_state import DiscoveryState, FilterSummaryItem
from app.states.membership_state import MembershipState

# Match the Settings field typography.
SMALL_INPUT_CLASS = (
    "w-full rounded-xl border border-[#f7d9a0] bg-white px-3.5 py-2 "
    "text-sm font-medium text-[#404040] placeholder:text-[#404040] "
    "transition-colors focus:border-[#e08b12] focus:ring-2 "
    "focus:ring-[#fff7e8] outline-hidden"
)
SMALL_SELECT_CLASS = (
    SMALL_INPUT_CLASS + " appearance-none cursor-pointer pr-9 bg-white"
)


def _small_label_hint(hint: str | rx.Var[str]) -> rx.Var[str]:
    if isinstance(hint, rx.Var):
        return hint
    return ui(hint)


# Category, Place, Reward and the advanced fields all sit 5px in from the edge.
INDENT_STYLE: dict[str, str] = {"paddingLeft": "5px"}


def small_label(label: str, hint: str | rx.Var[str] = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(
            ui(label), class_name="text-[13px] font-bold text-[#111827]"
        ),
        rx.cond(
            hint != "",
            rx.el.span(
                _small_label_hint(hint),
                class_name="text-xs font-medium text-[#4b5563]",
            ),
            rx.fragment(),
        ),
        class_name="mb-1 flex items-baseline justify-between gap-3",
    )


def summary_chip(item: FilterSummaryItem) -> rx.Component:
    return rx.el.span(
        rx.cond(
            item["value"] == "",
            ui(item["source"]),
            ui_template(
                item["source"],
                "value",
                rx.cond(
                    item["localize_value"],
                    ui(item["value"]),
                    item["value"],
                ),
            ),
        ),
        class_name="text-xs font-semibold text-[#404040] [overflow-wrap:anywhere]",
    )


def localized_language_name(language: rx.Var[str]) -> rx.Var[str]:
    return rx.match(
        language,
        ("english", ui("English")),
        ("spanish", ui("Spanish")),
        ("french", ui("French")),
        ("portuguese", ui("Portuguese")),
        ("german", ui("German")),
        ("italian", ui("Italian")),
        ("arabic", ui("Arabic")),
        ("hindi", ui("Hindi")),
        ("chinese", ui("Chinese")),
        ("japanese", ui("Japanese")),
        language,
    )


def language_chip(language: rx.Var[str]) -> rx.Component:
    return rx.el.button(
        localized_language_name(language),
        type="button",
        aria_label=ui_template(
            "Filter by people who speak {language}",
            "language",
            localized_language_name(language),
        ),
        on_click=lambda: DiscoveryState.toggle_language_filter(language),
        class_name=rx.cond(
            DiscoveryState.language_filters.contains(language),
            "w-fit rounded-full border-2 border-[#e08b12] bg-[#fba922] px-2.5 py-1 text-sm font-semibold capitalize text-[#111827]",
            "w-fit rounded-full border border-[#fba922] bg-white px-2.5 py-1 text-sm font-semibold capitalize text-[#4b5563] transition-colors hover:border-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
    )


def subscribe_shield() -> rx.Component:
    """Free members see the controls, blurred, behind one Subscribe button."""
    return rx.el.div(
        rx.el.button(
            rx.icon("sparkles", class_name="h-3.5 w-3.5"),
            ui("Subscribe"),
            type="button",
            aria_label=ui(
                "Subscribe to unlock the advanced help search options"
            ),
            on_click=DiscoveryState.open_advanced_paywall,
            class_name="pointer-events-auto flex w-fit items-center gap-1.5 rounded-full bg-[#fba922] px-4 py-2 text-[13px] font-bold text-black transition-colors hover:bg-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        aria_hidden="false",
        class_name="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-white/60 backdrop-blur-[3px]",
    )


def advanced_controls() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            small_label("Last online"),
            select_wrapper(
                rx.el.select(
                    rx.foreach(
                        DiscoveryState.last_online_options,
                        lambda item: rx.el.option(
                            ui(item["label"]), value=item["value"]
                        ),
                    ),
                    value=DiscoveryState.last_online_filter,
                    on_change=DiscoveryState.set_last_online,
                    aria_label=ui("Filter by when a person was last online"),
                    class_name="w-full rounded-xl border border-[#fba922] bg-white px-3.5 py-2 text-sm font-medium text-[#404040] appearance-none cursor-pointer pr-9 outline-hidden focus:ring-2 focus:ring-[#e08b12]",
                )
            ),
            style=INDENT_STYLE,
            class_name="w-full",
        ),
        rx.el.div(
            small_label(
                "Combined rating",
                ui_template(
                    "Rating {value}%",
                    "value",
                    f"{DiscoveryState.rating_min}–{DiscoveryState.rating_max}",
                ),
            ),
            rx.el.div(
                rx.el.input(
                    type="range",
                    min="0",
                    max="100",
                    step="5",
                    value=DiscoveryState.rating_min.to_string(),
                    on_change=DiscoveryState.set_rating_min.throttle(100),
                    aria_label=ui("Minimum combined rating percentage"),
                    class_name="w-full accent-[#e08b12]",
                ),
                rx.el.input(
                    type="range",
                    min="0",
                    max="100",
                    step="5",
                    value=DiscoveryState.rating_max.to_string(),
                    on_change=DiscoveryState.set_rating_max.throttle(100),
                    aria_label=ui("Maximum combined rating percentage"),
                    class_name="w-full accent-[#fba922]",
                ),
                class_name="flex w-full flex-col gap-1",
            ),
            style=INDENT_STYLE,
            class_name="w-full",
        ),
        rx.el.div(
            small_label("Nationality"),
            rx.el.input(
                default_value=DiscoveryState.nationality_filter,
                placeholder=ui("Portuguese"),
                aria_label=ui("Filter by nationality"),
                on_change=DiscoveryState.set_nationality_filter.debounce(500),
                class_name="w-full rounded-xl border border-[#fba922] bg-white px-3.5 py-2 text-sm font-medium text-[#404040] placeholder:text-[#404040] outline-hidden focus:ring-2 focus:ring-[#e08b12]",
            ),
            style=INDENT_STYLE,
            class_name="w-full",
        ),
        rx.el.div(
            small_label("Spoken languages", "choose any"),
            rx.el.div(
                rx.foreach(DiscoveryState.language_options, language_chip),
                class_name="flex flex-wrap gap-1.5",
            ),
            style=INDENT_STYLE,
            class_name="w-full",
        ),
        class_name="grid grid-cols-1 gap-3 w-full",
    )


def advanced_disclosure_bar() -> rx.Component:
    """Free members only: the locked Advanced Search disclosure bar."""
    return rx.el.button(
        rx.el.span(
            rx.icon("telescope", class_name="h-4 w-4 shrink-0"),
            rx.el.span(
                ui("More filters"),
                class_name="min-w-0 text-[13px] font-bold leading-snug [overflow-wrap:anywhere]",
            ),
            class_name="flex min-w-0 items-center gap-2",
        ),
        rx.el.span(
            rx.cond(
                MembershipState.is_premium,
                rx.fragment(),
                rx.el.span(
                    rx.el.span(ui("Premium")),
                    rx.icon("lock", class_name="h-3 w-3"),
                    aria_label=ui("Premium feature"),
                    class_name="w-fit flex items-center gap-1 rounded-full bg-[#fba922] px-2.5 py-0.5 text-xs font-bold text-[#111827]",
                ),
            ),
            rx.icon(
                rx.cond(
                    DiscoveryState.advanced_expanded,
                    "chevron-up",
                    "chevron-down",
                ),
                class_name="h-4 w-4 shrink-0",
            ),
            class_name="flex shrink-0 items-center gap-2",
        ),
        type="button",
        aria_expanded=rx.cond(
            DiscoveryState.advanced_expanded, "true", "false"
        ),
        aria_label=ui("More filters"),
        on_click=DiscoveryState.toggle_advanced_expanded,
        class_name="flex w-full items-center justify-between gap-2 rounded-lg px-1 py-1 text-xs font-semibold text-[#596273] transition-colors hover:text-[#b86e08] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def advanced_filters_block() -> rx.Component:
    """Keep advanced filters in a secondary disclosure for every membership tier."""
    return rx.el.div(
        advanced_disclosure_bar(),
        rx.cond(
            DiscoveryState.advanced_expanded,
            rx.cond(
                MembershipState.is_premium,
                rx.el.div(
                    advanced_controls(),
                    class_name="w-full rounded-xl border border-[#dce5f5] bg-white/70 p-3",
                ),
                rx.el.div(
                    advanced_controls(),
                    subscribe_shield(),
                    class_name="relative w-full rounded-xl border border-[#dce5f5] bg-white/70 p-3",
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            DiscoveryState.advanced_expanded & DiscoveryState.filters_active,
            rx.el.div(
                rx.foreach(
                    DiscoveryState.active_filter_summary_items, summary_chip
                ),
                aria_label=ui("Active filters"),
                class_name="flex flex-wrap items-center gap-x-3 gap-y-1 w-full",
            ),
            rx.fragment(),
        ),
        class_name="flex w-full flex-col gap-1.5",
    )
