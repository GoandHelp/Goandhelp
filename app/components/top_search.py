"""Compact world search that layers over the member discovery map."""

import reflex as rx

from app.interface_i18n import ui
from app.states.world_search_state import (
    SearchGroup,
    SearchItem,
    WorldSearchState,
)


def search_glass_icon() -> rx.Component:
    return rx.el.svg(
        rx.el.circle(
            cx="10",
            cy="10",
            r="6.5",
            fill="none",
            stroke="white",
            stroke_width="2",
        ),
        rx.el.line(
            x1="15",
            y1="15",
            x2="21",
            y2="21",
            fill="none",
            stroke="white",
            stroke_width="2",
            stroke_linecap="round",
            stroke_linejoin="round",
        ),
        view_box="0 0 24 24",
        fill="none",
        aria_hidden="true",
        class_name="h-[18px] w-[18px]",
    )


def result_row(item: SearchItem) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.match(
                item["kind"],
                ("job", rx.icon("hand-helping", class_name="h-3.5 w-3.5")),
                ("person", rx.icon("user-round", class_name="h-3.5 w-3.5")),
                rx.icon("map-pin", class_name="h-3.5 w-3.5"),
            ),
            class_name=rx.cond(
                item["kind"] == "place",
                "flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-[#b86e08]",
                "flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-[#e08b12]",
            ),
        ),
        rx.el.span(
            rx.el.span(
                item["title"],
                class_name="block truncate text-left text-[13px] font-bold tracking-tight text-[#172044]",
            ),
            rx.cond(
                item["subtitle"],
                rx.el.span(
                    item["subtitle"],
                    class_name="block truncate text-left text-[11px] font-medium text-[#68708f]",
                ),
                rx.fragment(),
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "chevron-right", class_name="h-3.5 w-3.5 shrink-0 text-[#8c91aa]"
        ),
        type="button",
        on_click=lambda: WorldSearchState.choose(item["kind"], item["id"]),
        class_name="flex w-full items-center gap-2.5 rounded-xl px-2 py-2 text-left transition-colors hover:bg-[#f2f7ff] focus:bg-[#f2f7ff] focus:outline-hidden",
    )


def result_group(group: SearchGroup) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(group["icon"], class_name="h-3.5 w-3.5"),
            rx.el.span(
                group["label"],
                class_name="text-[11px] font-bold uppercase tracking-[0.12em]",
            ),
            rx.el.span(
                group["total"].to_string(),
                class_name="ml-auto rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-bold",
            ),
            class_name=rx.cond(
                group["kind"] == "place",
                "flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1.5 text-[#b86e08]",
                "flex items-center gap-2 rounded-full bg-[#f2f7ff] px-3 py-1.5 text-[#b86e08]",
            ),
        ),
        rx.el.div(
            rx.foreach(group["items"], result_row),
            class_name="flex flex-col",
        ),
        class_name="flex flex-col gap-1",
    )


def results_panel() -> rx.Component:
    return rx.cond(
        WorldSearchState.show_empty,
        rx.el.p(
            ui("No search matches"),
            class_name="mt-2 px-2 text-[12px] font-semibold text-[#404040]",
        ),
        rx.el.div(
            rx.cond(
                WorldSearchState.is_searching,
                rx.el.div(
                    rx.spinner(class_name="h-3.5 w-3.5"),
                    rx.el.span(
                        "Searching the world…",
                        class_name="text-[12px] font-semibold text-[#35406f]",
                    ),
                    class_name="flex items-center gap-2 px-2 py-2",
                ),
                rx.fragment(),
            ),
            rx.cond(
                WorldSearchState.has_results,
                rx.el.div(
                    rx.foreach(WorldSearchState.groups, result_group),
                    class_name="flex flex-col gap-2.5",
                ),
                rx.fragment(),
            ),
            role="listbox",
            aria_label="World search results",
            aria_live="polite",
            class_name="pointer-events-auto mt-2 max-h-[60vh] w-full overflow-y-auto rounded-2xl border border-[#c3d9ff] bg-white p-2",
        ),
    )


TOP_SEARCH_INPUT_BASE = (
    "min-w-0 bg-transparent text-left text-xs font-bold tracking-tight "
    "text-[#172044] outline-hidden placeholder:text-[#8c91aa]"
)


COLLAPSED_PLACEHOLDER = "Search..."
EXPANDED_PLACEHOLDER = "Search: People, Jobs, Places"


def top_search_variant(placeholder, visibility: str) -> rx.Component:
    """One placeholder width; exactly one variant is visible at any width."""
    return rx.el.input(
        type="search",
        placeholder=ui(placeholder),
        aria_label=ui("Search: People, Jobs, Places"),
        on_focus=WorldSearchState.expand,
        on_change=WorldSearchState.set_query.debounce(400),
        default_value=WorldSearchState.query,
        class_name=f"{visibility} {TOP_SEARCH_INPUT_BASE}",
    )


def member_top_search() -> rx.Component:
    """Compact search + grouped results, layered over the discovery map."""
    return rx.el.div(
        rx.el.form(
            rx.el.label(
                top_search_variant(
                    rx.cond(
                        WorldSearchState.expanded,
                        EXPANDED_PLACEHOLDER,
                        COLLAPSED_PLACEHOLDER,
                    ),
                    "block flex-1",
                ),
                rx.el.button(
                    search_glass_icon(),
                    type="submit",
                    aria_label=ui("Search: People, Jobs, Places"),
                    class_name="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#e08b12] text-white transition-colors hover:bg-[#b86e08]",
                ),
                class_name="flex h-10 w-full items-center gap-2 rounded-full border-0 bg-white py-1 pl-4 pr-1 text-[#172044] focus-within:ring-2 focus-within:ring-[#e08b12]/40",
            ),
            on_submit=WorldSearchState.submit,
            class_name="pointer-events-auto w-full",
        ),
        rx.cond(
            WorldSearchState.show_panel,
            results_panel(),
            rx.fragment(),
        ),
        class_name="pointer-events-none absolute left-3 right-3 top-3 z-30 flex w-auto flex-col sm:right-auto sm:w-[22rem]",
    )
