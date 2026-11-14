import reflex as rx

from app.interface_i18n import ui, ui_template
from app.filter_categories import FilterCategory
from app.states.guest_map_state import GuestMapState, MAX_QUERY_LENGTH


def guest_mode_button(label: str, value: str, description: str) -> rx.Component:
    return rx.el.button(
        ui(label),
        type="button",
        title=ui(description),
        aria_label=ui(description),
        aria_pressed=rx.cond(
            GuestMapState.browse_mode == value, "true", "false"
        ),
        on_click=lambda: GuestMapState.set_browse_mode(value),
        class_name=rx.cond(
            GuestMapState.browse_mode == value,
            "gah-segment-control flex h-[31px] items-center rounded-full bg-[#fba922] px-[11px] text-sm font-bold text-black whitespace-nowrap",
            "gah-segment-control flex h-[31px] items-center rounded-full bg-white px-[11px] text-sm font-bold text-[#404040] whitespace-nowrap hover:text-black focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
    )


def guest_category_choice(item: FilterCategory) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.cond(
                GuestMapState.category_filters.contains(item["value"]),
                rx.icon("check", class_name="size-3 text-black"),
                rx.fragment(),
            ),
            class_name=rx.cond(
                GuestMapState.category_filters.contains(item["value"]),
                "flex size-4 shrink-0 items-center justify-center rounded-[4px] border border-[#fba922] bg-[#fba922]",
                "flex size-4 shrink-0 items-center justify-center rounded-[4px] border border-[#d4d4d4] bg-white",
            ),
        ),
        rx.icon(item["icon"], class_name="size-4 shrink-0 text-[#e08b12]"),
        rx.el.span(
            ui(item["label"]),
            class_name="min-w-0 flex-1 text-left text-sm font-semibold text-[#404040] [overflow-wrap:anywhere]",
        ),
        type="button",
        role="checkbox",
        aria_checked=rx.cond(
            GuestMapState.category_filters.contains(item["value"]),
            "true",
            "false",
        ),
        on_click=lambda: GuestMapState.toggle_category_choice(item["value"]),
        key=item["value"],
        class_name="flex w-full items-center gap-2 rounded-xl px-2 py-1.5 bg-white hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def guest_categories() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            ui("Job category"),
            html_for="gah-guest-category",
            class_name="sr-only text-[#404040]",
        ),
        rx.el.button(
            rx.el.span(
                rx.cond(
                    GuestMapState.category_filters.length() > 1,
                    ui_template(
                        "{count} categories selected",
                        "count",
                        GuestMapState.category_filters.length().to_string(),
                    ),
                    ui(GuestMapState.category_summary_label),
                ),
                class_name="min-w-0 flex-1 truncate text-left text-sm font-medium text-[#404040]",
            ),
            rx.icon(
                "chevron-down", class_name="size-4 shrink-0 text-[#e08b12]"
            ),
            id="gah-guest-category",
            type="button",
            aria_expanded=rx.cond(
                GuestMapState.category_list_open, "true", "false"
            ),
            aria_controls="gah-guest-category-options",
            on_click=GuestMapState.toggle_category_list,
            class_name="gah-filter-field flex h-9 w-full items-center gap-2 rounded-xl border border-gray-300 bg-white px-3 focus-visible:ring-2 focus-visible:ring-[#fba922]/30",
        ),
        rx.cond(
            GuestMapState.category_list_open,
            rx.el.div(
                rx.el.div(
                    rx.foreach(
                        GuestMapState.filter_category_options,
                        guest_category_choice,
                    ),
                    id="gah-guest-category-options",
                    role="group",
                    aria_label=ui("All categories"),
                    class_name="flex max-h-56 flex-col gap-0.5 overflow-y-auto overscroll-contain",
                ),
                rx.el.button(
                    ui("Clear categories"),
                    type="button",
                    on_click=GuestMapState.clear_category_choices,
                    class_name="mt-1.5 w-fit rounded-full border border-[#d4d4d4] bg-white px-2.5 py-1 text-xs font-bold text-[#404040] hover:border-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                class_name="mt-1.5 w-full rounded-xl border border-[#d4d4d4] bg-white p-1.5",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def guest_reward_option(item: dict[str, str]) -> rx.Component:
    return rx.el.option(ui(item["label"]), value=item["value"])


def guest_rewards() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            ui("Rewards"),
            html_for="gah-guest-reward",
            class_name="sr-only text-[#404040]",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    GuestMapState.reward_filter_options, guest_reward_option
                ),
                id="gah-guest-reward",
                value=GuestMapState.reward_filter,
                disabled=GuestMapState.browse_mode == "get",
                aria_label=ui("Filter by reward"),
                aria_describedby=rx.cond(
                    GuestMapState.browse_mode == "get",
                    "gah-guest-reward-na",
                    "",
                ),
                on_change=GuestMapState.set_reward_filter,
                class_name="gah-filter-field h-9 w-full appearance-none rounded-xl border border-gray-300 bg-white px-3 pr-9 text-sm font-medium text-[#404040] disabled:cursor-not-allowed disabled:opacity-60 focus-visible:ring-2 focus-visible:ring-[#fba922]/30",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[#e08b12]",
            ),
            class_name="relative w-full",
        ),
        rx.cond(
            GuestMapState.browse_mode == "get",
            rx.el.p(
                ui("Rewards"),
                " — ",
                ui("Not applicable"),
                id="gah-guest-reward-na",
                class_name="mt-1 text-xs font-medium text-[#404040]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def guest_filter_status() -> rx.Component:
    return rx.el.div(
        rx.cond(
            GuestMapState.load_message != "",
            rx.el.div(
                rx.el.p(
                    ui(GuestMapState.load_message),
                    role="alert",
                    class_name="text-xs font-medium text-[#404040]",
                ),
                rx.el.button(
                    ui("Try again"),
                    type="button",
                    on_click=GuestMapState.load_preview,
                    class_name="mt-1 w-fit rounded-full bg-white px-2 py-1 text-xs font-bold text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
            ),
            rx.cond(
                GuestMapState.is_loading,
                rx.el.p(
                    ui("Updating map…"),
                    role="status",
                    class_name="text-xs font-medium text-[#404040]",
                ),
                rx.cond(
                    GuestMapState.loaded & (GuestMapState.open_total == 0),
                    rx.el.p(
                        rx.cond(
                            GuestMapState.browse_mode == "get",
                            ui("No helpers match your filters"),
                            ui("No open jobs match your filters"),
                        ),
                        role="status",
                        class_name="text-xs font-medium text-[#404040]",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        aria_live="polite",
        class_name="w-full",
    )


def guest_filter_drawer() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                guest_mode_button(
                    "Go",
                    "give",
                    "Go — filter people requesting help and their jobs",
                ),
                guest_mode_button(
                    "Get", "get", "Get — filter people offering help"
                ),
                role="group",
                aria_label=ui(
                    "Filter people requesting help, or people offering help"
                ),
                class_name="gah-segment-group flex h-[31px] shrink-0 items-center rounded-full border border-[#d4d4d4] bg-white",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("map", class_name="size-3.5"),
                    aria_label=ui("Show results on the map"),
                    class_name="flex size-7 items-center justify-center rounded-full bg-[#fba922] text-black",
                ),
                rx.el.button(
                    rx.icon("list", class_name="size-3.5"),
                    rx.icon("lock", class_name="size-2.5"),
                    type="button",
                    disabled=True,
                    aria_disabled="true",
                    aria_label=f"{ui('Show results as a list')}: {ui('Register or sign in')}",
                    title=ui("Register or sign in"),
                    class_name="flex h-7 items-center gap-0.5 rounded-full bg-white px-1.5 text-[#6b7280] cursor-not-allowed",
                ),
                role="group",
                aria_label=ui("Map"),
                class_name="gah-segment-group flex h-7 shrink-0 items-center rounded-full border border-[#d4d4d4] bg-white",
            ),
            rx.el.button(
                rx.icon("x", class_name="size-4"),
                id="gah-guest-filter-close",
                type="button",
                aria_label=ui("Close Search filters"),
                on_click=GuestMapState.collapse_search,
                class_name="ml-auto flex size-8 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-[#b86e08] hover:bg-[#ffedcc] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="relative flex min-h-8 w-full items-center justify-start gap-1.5",
        ),
        rx.el.form(
            rx.el.label(
                ui("Search: People, Jobs, Places"),
                html_for="gah-guest-search",
                class_name="sr-only text-[#404040]",
            ),
            rx.el.input(
                id="gah-guest-search",
                name="guest_search",
                type="search",
                max_length=MAX_QUERY_LENGTH,
                placeholder=ui("People, jobs, places..."),
                default_value=GuestMapState.search_query,
                key=GuestMapState.search_query,
                class_name="gah-search-inner gah-filter-field min-w-0 flex-1 h-9 rounded-xl border-0 bg-white px-3 text-sm font-medium text-[#404040] placeholder:text-[#404040] outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]/30",
            ),
            rx.el.button(
                rx.icon("search", class_name="size-4"),
                type="submit",
                aria_label=ui("Search"),
                class_name="gah-search-submit flex size-9 shrink-0 items-center justify-center rounded-xl bg-white text-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            on_submit=GuestMapState.submit_search,
            class_name="gah-search-form mt-1 flex h-9 w-full items-center rounded-xl border border-gray-300 bg-white focus-within:border-[#fba922]",
        ),
        guest_categories(),
        guest_rewards(),
        rx.el.div(
            rx.el.button(
                rx.icon("bell-plus", class_name="size-3"),
                ui("Save search"),
                type="button",
                aria_label=ui("Save these search filters as an alert"),
                on_click=GuestMapState.open_join_prompt,
                class_name="w-fit flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-semibold text-[#6b7280] hover:bg-white hover:text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            rx.el.button(
                rx.icon("x", class_name="size-3"),
                ui("Clear filters"),
                type="button",
                aria_label=ui("Clear every filter"),
                on_click=GuestMapState.clear_filters,
                class_name="w-fit flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-semibold text-[#6b7280] hover:bg-white hover:text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="flex flex-wrap items-center justify-between gap-1",
        ),
        guest_filter_status(),
        id="gah-guest-filter-drawer",
        role="dialog",
        aria_modal=False,
        aria_label=ui("Search filters"),
        on_mount=rx.call_script("""
            (() => {
                window.gahGuestFilterCleanup?.();
                const close = event => {
                    if (event.key === 'Escape') {
                        event.preventDefault();
                        document.getElementById('gah-guest-filter-close')?.click();
                    }
                };
                document.addEventListener('keydown', close);
                window.gahGuestFilterCleanup = () => document.removeEventListener('keydown', close);
                requestAnimationFrame(() => document.getElementById('gah-guest-filter-close')?.focus());
            })();
        """),
        on_unmount=rx.call_script(
            "window.gahGuestFilterCleanup?.(); delete window.gahGuestFilterCleanup; document.getElementById('gah-guest-filter-open')?.focus({preventScroll:true});"
        ),
        class_name="gah-search-drawer pointer-events-auto fixed right-2 bottom-[calc(3.875rem+env(safe-area-inset-bottom))] z-30 flex w-[calc(100vw-1rem)] max-w-[23.75rem] max-h-[calc(100dvh-5rem-env(safe-area-inset-bottom))] min-h-0 flex-col gap-1.5 overflow-y-auto overscroll-contain rounded-tl-2xl border-0 bg-[#f4f8ff] p-3 font-['Inter'] text-[#404040]",
    )
