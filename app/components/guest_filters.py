import reflex as rx

from app.interface_i18n import ui, ui_template
from app.components import filter_layout as layout
from app.filter_categories import FilterCategory
from app.skill_categories import CATEGORY_GRADIENT
from app.states.guest_map_state import GuestMapState, MAX_QUERY_LENGTH


def guest_mode_button(label: str, value: str, description: str) -> rx.Component:
    return rx.el.button(
        rx.el.span(ui(label), dir="auto"),
        type="button",
        title=ui(description),
        aria_label=ui(description),
        aria_pressed=rx.cond(
            GuestMapState.browse_mode == value, "true", "false"
        ),
        on_click=lambda: GuestMapState.set_browse_mode(value),
        class_name=rx.cond(
            GuestMapState.browse_mode == value,
            layout.MODE_ON_CLASS,
            layout.MODE_OFF_CLASS,
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
        rx.el.span(
            rx.icon(item["icon"], class_name="size-4 text-white"),
            aria_hidden="true",
            style={
                "--category-fill": item["color"],
                "background": CATEGORY_GRADIENT,
            },
            class_name="flex size-7 shrink-0 items-center justify-center rounded-full text-white",
        ),
        rx.el.span(
            ui(item["label"]),
            class_name="min-w-0 flex-1 text-left text-[11px] font-semibold text-[#000000] [overflow-wrap:anywhere]",
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
        class_name="flex w-full items-center gap-2 rounded-xl px-2 py-1.5 transition-colors hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
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
                rx.cond(
                    GuestMapState.category_list_open,
                    "chevron-up",
                    "chevron-down",
                ),
                class_name="size-4 shrink-0 text-[#e08b12]",
            ),
            id="gah-guest-category",
            type="button",
            aria_expanded=rx.cond(
                GuestMapState.category_list_open, "true", "false"
            ),
            aria_controls="gah-guest-category-options",
            on_click=GuestMapState.toggle_category_list,
            class_name=layout.FIELD_CLASS,
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
                class_name=layout.SELECT_CLASS,
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
                class_name="sr-only",
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


def guest_location_row() -> rx.Component:
    return rx.el.div(
        rx.el.span(ui("My location"), class_name=layout.LOCATION_LABEL_CLASS),
        rx.el.div(
            rx.el.button(
                rx.icon(
                    "eye-off", class_name="h-3.5 w-3.5 shrink-0 text-black"
                ),
                rx.el.span(
                    ui("Off"),
                    class_name="min-w-0 text-black [overflow-wrap:anywhere]",
                ),
                type="button",
                role="radio",
                aria_checked="true",
                aria_label=ui("Show my location: Off"),
                class_name=layout.LOCATION_ON_CLASS,
            ),
            rx.el.button(
                rx.icon("circle-dot", class_name="h-3.5 w-3.5 shrink-0"),
                rx.el.span(
                    ui("Approx"), class_name="min-w-0 [overflow-wrap:anywhere]"
                ),
                type="button",
                role="radio",
                aria_checked="false",
                aria_label=f"{ui('Show my location: Approx')}: {ui('Register or sign in')}",
                title=ui("Register or sign in"),
                on_click=GuestMapState.open_join_prompt,
                class_name=layout.LOCATION_OFF_CLASS,
            ),
            role="radiogroup",
            aria_label=ui("Show my location"),
            class_name=layout.LOCATION_GROUP_CLASS,
        ),
        class_name=layout.LOCATION_ROW_CLASS,
    )


def guest_distance_block() -> rx.Component:
    return rx.el.div(
        layout.distance_row(ui("Any"), "gah-guest-distance"),
        rx.el.input(
            id="gah-guest-distance",
            type="range",
            min="0",
            max="500",
            step="5",
            default_value="0",
            key="0",
            aria_label=f"{ui('Distance in kilometres, zero means any distance')}: {ui('Register or sign in')}",
            aria_valuetext=ui("Any"),
            title=ui("Register or sign in"),
            on_change=GuestMapState.gate_distance_filter.throttle(100),
            class_name=layout.RANGE_CLASS,
        ),
        class_name=layout.DISTANCE_SPACING_CLASS,
    )


def guest_filter_drawer() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
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
                        class_name=layout.MODE_GROUP_CLASS,
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("map", class_name="size-3.5"),
                            type="button",
                            aria_pressed="true",
                            aria_label=ui("Show results on the map"),
                            title=ui("Show results on the map"),
                            on_click=lambda: GuestMapState.set_view_mode("map"),
                            class_name=layout.VIEW_ON_CLASS,
                        ),
                        rx.el.button(
                            rx.icon("list", class_name="size-3.5"),
                            type="button",
                            aria_pressed="false",
                            on_click=GuestMapState.open_join_prompt,
                            aria_label=f"{ui('Show results as a list')}: {ui('Register or sign in')}",
                            title=ui("Register or sign in"),
                            class_name=layout.VIEW_OFF_CLASS,
                        ),
                        role="group",
                        aria_label=ui("Switch between map view and list view"),
                        class_name=layout.VIEW_GROUP_CLASS,
                    ),
                    class_name=layout.HEADER_TOGGLES_CLASS,
                ),
                rx.el.button(
                    rx.icon("x", class_name="size-4"),
                    id="gah-guest-filter-close",
                    type="button",
                    aria_label=ui("Close Search filters"),
                    on_click=GuestMapState.collapse_search,
                    title=ui("Close Search filters"),
                    class_name=layout.CLOSE_CLASS,
                ),
                class_name=layout.HEADER_CLASS,
            ),
            rx.el.div(
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
                        class_name=layout.SEARCH_INPUT_CLASS,
                    ),
                    rx.el.button(
                        rx.icon("search", class_name="size-4"),
                        type="submit",
                        aria_label=ui("Search"),
                        class_name="gah-search-submit flex size-10 shrink-0 items-center justify-center rounded-xl bg-white text-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                    ),
                    on_submit=GuestMapState.submit_search,
                    class_name=layout.SEARCH_FORM_CLASS,
                ),
                guest_categories(),
                guest_rewards(),
                rx.el.div(
                    guest_location_row(),
                    class_name=layout.LOCATION_SPACING_CLASS,
                ),
                guest_distance_block(),
                class_name=layout.BODY_CLASS,
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("bell-plus", class_name="size-3"),
                    ui("Save search"),
                    type="button",
                    aria_label=ui("Save these search filters as an alert"),
                    on_click=GuestMapState.clear_filters,
                    disabled=~GuestMapState.filters_active,
                    class_name=layout.FOOTER_BUTTON_CLASS,
                ),
                rx.el.button(
                    rx.icon("x", class_name="size-3"),
                    ui("Clear filters"),
                    type="button",
                    aria_label=ui("Clear every filter"),
                    on_click=GuestMapState.clear_filters,
                    class_name="w-fit flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-semibold text-[#6b7280] hover:bg-white hover:text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                class_name=layout.FOOTER_CLASS,
            ),
            guest_filter_status(),
            class_name=layout.CONTENT_CLASS,
        ),
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
            "window.gahGuestFilterCleanup?.(); delete window.gahGuestFilterCleanup; requestAnimationFrame(() => document.getElementById('gah-guest-filter-open')?.focus({preventScroll:true}));"
        ),
        class_name=layout.DRAWER_CLASS,
    )
