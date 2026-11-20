import reflex as rx

from app.interface_i18n import ui, ui_template
from app.components import filter_layout as layout

from app.components.language_control import (
    browser_translatable_text,
    original_language_disclosure,
)

from app.components.block_dialog import block_member_button
from app.components.report_dialog import report_button
from app.models import REPORT_TARGET_JOB_MESSAGE, REPORT_TARGET_PROFILE
from app.states.contacts_state import ContactsState
from app.states.auth_state import AuthState
from app.components.event_cards import (
    discovery_event_list,
    event_detail_sheet,
)
from app.states.event_state import EventState
from app.components.bookmark_tab import bookmark_tab
from app.components.help_share import help_share
from app.components.header import signed_in_nav_menu
from app.components.feedback import (
    INPUT_CLASS,
    avatar_with_tick,
    error_banner,
    select_wrapper,
    success_banner,
)
from app.components.advanced_filters import (
    INDENT_STYLE,
    advanced_filters_block,
)
from app.components.location_selection import location_selection
from app.components.help_post_panel import category_icon
from app.components.openfreemap import open_free_map
from app.components.top_search import results_panel
from app.states.world_search_state import WorldSearchState
from app.states.discovery_state import (
    DirectRequest,
    ListPostGroup,
    DiscoveryState,
    HelperProfile,
)
from app.states.saved_search_state import SavedSearchState
from app.skill_categories import CATEGORY_GRADIENT


def helper_photo(helper: HelperProfile, class_name: str) -> rx.Component:
    return rx.image(src=helper["image_url"], alt="", class_name=class_name)


def option_item(item: dict[str, str]) -> rx.Component:
    return rx.el.option(ui(item["label"]), value=item["value"])


def urgency_pill(urgency: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        rx.icon("clock", class_name="h-3 w-3"),
        urgency,
        class_name=rx.cond(
            urgency == "urgent",
            "w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12] capitalize",
            rx.cond(
                urgency == "soon",
                "w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12] capitalize",
                "w-fit flex items-center gap-1.5 rounded-full bg-[#f5f5f5] px-3 py-1 text-xs font-semibold text-[#404040] capitalize",
            ),
        ),
    )


def sheet_mode_button(label: str, value: str, description: str) -> rx.Component:
    return rx.el.button(
        rx.el.span(ui(label), dir="auto"),
        type="button",
        title=ui(description),
        aria_label=ui(description),
        aria_pressed=rx.cond(DiscoveryState.map_mode == value, "true", "false"),
        on_click=lambda: DiscoveryState.set_map_mode(value),
        class_name=rx.cond(
            DiscoveryState.map_mode == value,
            layout.MODE_ON_CLASS,
            layout.MODE_OFF_CLASS,
        ),
    )


def category_choice_row(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.cond(
                DiscoveryState.category_filters.contains(item["value"]),
                rx.icon("check", class_name="h-3 w-3 text-black"),
                rx.fragment(),
            ),
            class_name=rx.cond(
                DiscoveryState.category_filters.contains(item["value"]),
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
            DiscoveryState.category_filters.contains(item["value"]),
            "true",
            "false",
        ),
        aria_label=ui(item["label"]),
        on_click=lambda: DiscoveryState.toggle_category_choice(item["value"]),
        class_name="flex w-full items-center gap-2 rounded-xl px-2 py-1.5 transition-colors hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def category_multiselect(compact: bool = False) -> rx.Component:
    """Multi-select category checklist: choices combine with OR."""
    return rx.el.div(
        rx.el.button(
            rx.el.span(
                rx.cond(
                    DiscoveryState.category_filters.length() == 0,
                    ui("All categories"),
                    rx.cond(
                        DiscoveryState.category_filters.length() == 1,
                        ui(DiscoveryState.category_summary_label),
                        ui_template(
                            "{count} categories selected",
                            "count",
                            DiscoveryState.category_filters.length().to_string(),
                        ),
                    ),
                ),
                class_name=rx.cond(
                    DiscoveryState.category_filters.length() > 0,
                    "min-w-0 flex-1 truncate text-left text-sm font-medium text-[#404040]",
                    "min-w-0 flex-1 truncate text-left text-sm font-medium text-[#404040]",
                ),
            ),
            rx.icon(
                rx.cond(
                    DiscoveryState.category_list_open,
                    "chevron-up",
                    "chevron-down",
                ),
                class_name="h-4 w-4 shrink-0 text-[#e08b12]",
            ),
            type="button",
            aria_expanded=rx.cond(
                DiscoveryState.category_list_open, "true", "false"
            ),
            aria_label=ui(
                "Choose one or more search categories, including Events"
            ),
            on_click=DiscoveryState.toggle_category_list,
            class_name=rx.cond(
                compact,
                layout.FIELD_CLASS,
                "gah-filter-field flex h-10 w-full items-center gap-2 rounded-xl border border-gray-300 bg-white px-3.5 text-sm font-medium text-[#404040] outline-hidden transition-colors focus:border-[#fba922] focus:ring-2 focus:ring-[#fba922]/30",
            ),
        ),
        rx.cond(
            DiscoveryState.category_list_open,
            rx.el.div(
                rx.el.div(
                    rx.foreach(
                        DiscoveryState.filter_category_options,
                        category_choice_row,
                    ),
                    role="group",
                    aria_label=ui("Search categories and Events"),
                    class_name="flex max-h-56 flex-col gap-0.5 overflow-y-auto",
                ),
                rx.cond(
                    DiscoveryState.category_filters.length() > 0,
                    rx.el.button(
                        rx.icon("x", class_name="h-3 w-3"),
                        ui("Clear categories"),
                        type="button",
                        aria_label=ui("Clear every selected category"),
                        on_click=DiscoveryState.clear_category_choices,
                        class_name="mt-1.5 flex w-fit items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-2.5 py-1 text-[10px] font-bold text-[#404040] transition-colors hover:border-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                class_name="mt-1.5 w-full rounded-xl border border-[#d4d4d4] bg-white p-1.5",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def distance_filter_label() -> rx.Var[str]:
    return rx.cond(
        DiscoveryState.distance_km <= 0,
        ui("Any"),
        rx.cond(
            DiscoveryState.distance_km >= DiscoveryState.distance_max_km,
            ui_template(
                "{distance}+ km",
                "distance",
                DiscoveryState.distance_max_km.to_string(),
            ),
            ui_template(
                "{distance} km",
                "distance",
                DiscoveryState.distance_km.to_string(),
            ),
        ),
    )


def distance_filter_block(compact: bool = False) -> rx.Component:
    """Free travel-radius slider, shown in both Give and Get modes."""
    return rx.el.div(
        layout.distance_row(distance_filter_label(), "gah-discover-distance"),
        rx.el.input(
            id="gah-discover-distance",
            type="range",
            min=DiscoveryState.distance_min_km.to_string(),
            max=DiscoveryState.distance_max_km.to_string(),
            step=DiscoveryState.distance_step_km.to_string(),
            default_value=DiscoveryState.distance_km.to_string(),
            key=DiscoveryState.distance_reset_token.to_string(),
            aria_label=ui("Distance in kilometres, zero means any distance"),
            aria_valuetext=distance_filter_label(),
            on_change=[
                DiscoveryState.set_distance_filter.throttle(100),
                DiscoveryState.commit_distance_filter.debounce(150),
            ],
            style={
                "--distance-progress": f"{((DiscoveryState.distance_km - DiscoveryState.distance_min_km) / (DiscoveryState.distance_max_km - DiscoveryState.distance_min_km) * 100):.2f}%"
            },
            class_name=rx.cond(
                compact,
                layout.RANGE_CLASS,
                "gah-distance-range -translate-y-1 h-10 w-full min-w-0 touch-none cursor-pointer appearance-none bg-transparent outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
        ),
        class_name=layout.DISTANCE_SPACING_CLASS,
    )


def sheet_view_button(value: str, icon: str, description: str) -> rx.Component:
    """Compact map/list switch used inside the Search filters header."""
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        type="button",
        title=ui(description),
        aria_label=ui(description),
        aria_pressed=rx.cond(
            DiscoveryState.view_mode == value, "true", "false"
        ),
        on_click=lambda: DiscoveryState.set_view_mode(value),
        class_name=rx.cond(
            DiscoveryState.view_mode == value,
            layout.VIEW_ON_CLASS,
            layout.VIEW_OFF_CLASS,
        ),
    )


def show_my_location_block(compact: bool = False) -> rx.Component:
    """`Show my location` — Off / Approximate, persisted immediately.

    The existing contextual pre-permission flow is preserved: the very same
    geolocation helper is mounted here, so choosing Approximate asks the
    browser for one foreground fix and only then stores the chosen mode.
    """
    return rx.el.div(
        rx.cond(
            DiscoveryState.distance_warning,
            rx.el.p(
                ui("Turn on your Approximate location first"),
                id="gah-distance-warning",
                key=DiscoveryState.distance_reset_token,
                role="status",
                aria_live="polite",
                on_mount=rx.call_script(
                    "requestAnimationFrame(() => { const el = document.getElementById('gah-distance-warning'); if (el && !matchMedia('(prefers-reduced-motion: reduce)').matches) el.animate([{opacity:0},{opacity:1},{opacity:0},{opacity:1}], {duration:1800, fill:'forwards'}); });"
                ),
                class_name="mb-2 w-full text-center text-xs font-semibold text-[#e08b12] opacity-100",
            ),
            rx.fragment(),
        ),
        rx.cond(
            compact, location_selection(compact=True), location_selection()
        ),
        class_name="w-full",
    )


def sheet_view_toggle() -> rx.Component:
    return rx.el.div(
        sheet_view_button("map", "map", "Show results on the map"),
        sheet_view_button("list", "list", "Show results as a list"),
        role="group",
        aria_label=ui("Switch between map view and list view"),
        custom_attrs={"data-tour-target": "view-toggle"},
        class_name=layout.VIEW_GROUP_CLASS,
    )


def filter_dismiss_layer() -> rx.Component:
    return rx.cond(
        DiscoveryState.filter_panel_open,
        rx.el.button(
            type="button",
            id="gah-filter-dismiss",
            aria_label=ui("Dismiss Search filters"),
            on_click=DiscoveryState.close_filters,
            on_scroll=DiscoveryState.close_filters,
            on_mount=rx.call_script("""
                requestAnimationFrame(() => {
                    const layer = document.getElementById('gah-filter-dismiss');
                    if (!layer) return;
                    const dismiss = () => layer.click();
                    layer.addEventListener('pointerdown', dismiss, {once:true});
                    layer.addEventListener('wheel', dismiss, {once:true, passive:true});
                    layer.addEventListener('touchmove', dismiss, {once:true, passive:true});
                });
            """),
            class_name="gah-map-utility fixed inset-0 z-[25] h-full w-full rounded-none border-0 bg-transparent! shadow-none! focus-visible:outline-2 focus-visible:outline-[#fba922]",
        ),
        rx.fragment(),
    )


def filter_drawer(class_name: str, compact: bool = False) -> rx.Component:
    """The Help Filters field kit, attached to the edge of the map."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        sheet_mode_button(
                            "Go",
                            "give",
                            "Go — filter people requesting help and their jobs",
                        ),
                        sheet_mode_button(
                            "Get",
                            "get",
                            "Get — filter people offering help",
                        ),
                        role="group",
                        aria_label=ui(
                            "Filter people requesting help, or people offering help"
                        ),
                        class_name=layout.MODE_GROUP_CLASS,
                    ),
                    sheet_view_toggle(),
                    class_name=layout.HEADER_TOGGLES_CLASS,
                ),
                rx.el.span(
                    ui("Search filters"),
                    custom_attrs={"data-tour-target": "filters-label"},
                    class_name="sr-only",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    type="button",
                    title=ui("Close Search filters"),
                    aria_label=ui("Close Search filters"),
                    id="gah-map-filter-close",
                    on_click=DiscoveryState.close_filters,
                    class_name=layout.CLOSE_CLASS,
                ),
                class_name=layout.HEADER_CLASS,
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.form(
                        rx.el.input(
                            name="world_search",
                            type="search",
                            placeholder=ui("People, jobs, places..."),
                            aria_label=ui("Search: People, Jobs, Places"),
                            default_value=WorldSearchState.query,
                            key=WorldSearchState.query,
                            class_name=rx.cond(
                                compact,
                                layout.SEARCH_INPUT_CLASS,
                                "gah-search-inner gah-filter-field min-w-0 flex-1 h-10 rounded-xl border-0 bg-transparent px-3.5 text-sm font-medium text-[#404040] placeholder:text-[#404040] outline-hidden focus-visible:outline-none!",
                            ),
                        ),
                        on_submit=[
                            WorldSearchState.submit,
                            WorldSearchState.expand,
                        ],
                        class_name=rx.cond(
                            compact,
                            layout.SEARCH_FORM_CLASS,
                            "gah-search-form flex h-10 w-full items-center rounded-xl border border-gray-300 bg-white focus-within:border-[#fba922]",
                        ),
                    ),
                    rx.cond(
                        WorldSearchState.show_panel,
                        results_panel(),
                        rx.fragment(),
                    ),
                    custom_attrs={
                        "data-tour-target": "search",
                        "data-tour-target-compact": "search-compact",
                    },
                    class_name="w-full",
                ),
                category_multiselect(compact),
                rx.el.div(
                    select_wrapper(
                        rx.el.select(
                            rx.foreach(
                                DiscoveryState.reward_filter_options,
                                option_item,
                            ),
                            value=DiscoveryState.reward_filter,
                            on_change=DiscoveryState.set_reward_filter,
                            aria_label=ui("Filter by reward"),
                            class_name=rx.cond(
                                compact,
                                layout.SELECT_CLASS,
                                "gah-filter-field h-10 w-full appearance-none cursor-pointer rounded-xl border border-gray-300 bg-white px-3.5 pr-9 text-sm font-medium text-[#404040] outline-hidden transition-colors focus:border-[#fba922] focus:ring-2 focus:ring-[#fba922]/30",
                            ),
                        )
                    ),
                    class_name="w-full",
                ),
                rx.el.div(
                    show_my_location_block(compact=compact),
                    class_name=layout.LOCATION_SPACING_CLASS,
                ),
                distance_filter_block(compact=compact),
                class_name=layout.BODY_CLASS,
            ),
            advanced_filters_block(),
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        SavedSearchState.is_saving,
                        rx.spinner(class_name="h-3 w-3"),
                        rx.icon("bell-plus", class_name="h-3 w-3"),
                    ),
                    ui("Save search"),
                    type="button",
                    disabled=SavedSearchState.is_saving,
                    aria_label=ui("Save these search filters as an alert"),
                    on_click=SavedSearchState.save_current_search,
                    class_name=layout.FOOTER_BUTTON_CLASS,
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-3 w-3"),
                    ui("Clear filters"),
                    type="button",
                    aria_label=ui("Clear every filter"),
                    disabled=~(
                        DiscoveryState.filters_active
                        | DiscoveryState.distance_warning
                    ),
                    on_click=DiscoveryState.clear_filters,
                    class_name=layout.FOOTER_BUTTON_CLASS,
                ),
                class_name=layout.FOOTER_CLASS,
            ),
            rx.cond(
                SavedSearchState.error,
                rx.el.p(
                    SavedSearchState.error,
                    role="alert",
                    class_name="w-full rounded-xl border border-[#d4d4d4] bg-[#fff7e8] px-2.5 py-1.5 text-[10px] font-bold leading-relaxed text-[#e08b12]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                SavedSearchState.success,
                rx.el.p(
                    SavedSearchState.success,
                    role="status",
                    class_name="w-full rounded-xl border border-[#fba922] bg-[#fba922] px-2.5 py-1.5 text-[10px] font-bold text-black",
                ),
                rx.fragment(),
            ),
            class_name=layout.CONTENT_CLASS,
        ),
        role="dialog",
        aria_label=ui("Search filters"),
        aria_modal=False,
        on_mount=rx.call_script("""
            (() => {
                window.gahFilterEscapeCleanup?.();
                const close = (event) => {
                    if (event.key !== 'Escape') return;
                    document.getElementById('gah-map-filter-close')?.click();
                    document.querySelector('#gah-map-filter-open, #gah-board-filter-open')?.focus();
                };
                document.addEventListener('keydown', close);
                window.gahFilterEscapeCleanup = () => document.removeEventListener('keydown', close);
            })();
        """),
        on_unmount=rx.call_script(
            "window.gahFilterEscapeCleanup?.(); delete window.gahFilterEscapeCleanup;"
        ),
        class_name=class_name,
    )


def mode_toggle_button(
    label: str, value: str, icon: str, description: str
) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        rx.el.span(label),
        type="button",
        aria_label=description,
        title=description,
        aria_pressed=rx.cond(DiscoveryState.map_mode == value, "true", "false"),
        on_click=lambda: DiscoveryState.set_map_mode(value),
        class_name=rx.cond(
            DiscoveryState.map_mode == value,
            "gah-segment-control flex h-8 items-center gap-1.5 rounded-full bg-[#fba922] px-3 text-xs font-bold text-[#000000] border border-white whitespace-nowrap",
            "gah-segment-control flex h-8 items-center gap-1.5 rounded-full px-3 text-xs font-bold text-[#404040] border border-transparent transition-colors hover:text-[#000000] whitespace-nowrap",
        ),
    )


def view_toggle_button(
    label: str, value: str, icon: str, description: str
) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        rx.el.span(label, class_name="hidden sm:inline"),
        type="button",
        aria_label=description,
        title=description,
        aria_pressed=rx.cond(
            DiscoveryState.view_mode == value, "true", "false"
        ),
        on_click=lambda: DiscoveryState.set_view_mode(value),
        class_name=rx.cond(
            DiscoveryState.view_mode == value,
            "gah-segment-control flex h-8 items-center gap-1.5 rounded-full bg-[#fba922] px-3 text-xs font-bold text-[#000000] whitespace-nowrap",
            "gah-segment-control flex h-8 items-center gap-1.5 rounded-full px-3 text-xs font-bold text-[#404040] transition-colors hover:text-[#000000] whitespace-nowrap",
        ),
    )


def discovery_controls() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                mode_toggle_button(
                    "Give",
                    "give",
                    "hand-helping",
                    "Give help — choose a job posted by someone who needs help",
                ),
                mode_toggle_button(
                    "Get",
                    "get",
                    "users-round",
                    "Get help — find a person who can offer help",
                ),
                role="group",
                aria_label="Choose whether to give help or get help",
                class_name="gah-segment-group flex h-9 w-fit items-center gap-1 rounded-full border border-[#d4d4d4] bg-white p-0.5",
            ),
            rx.el.div(
                view_toggle_button("Map View", "map", "map", "Map view"),
                view_toggle_button("List View", "list", "list", "List view"),
                role="group",
                aria_label="Switch between map view and list view",
                class_name="gah-segment-group flex h-9 w-fit items-center gap-1 rounded-full border border-[#d4d4d4] bg-white p-0.5",
            ),
            class_name="flex w-full flex-wrap items-center justify-between gap-2",
        ),
        rx.el.p(
            rx.cond(
                DiscoveryState.is_give_mode,
                "Give — choose a job and give your help to a neighbour who asked for it.",
                "Get — find a person you can get help from, and open their profile.",
            ),
            class_name="text-xs font-medium text-[#404040]",
        ),
        class_name="flex w-full flex-col gap-2 rounded-2xl border border-[#d4d4d4] bg-white p-3",
    )


def filter_button() -> rx.Component:
    return rx.el.button(
        rx.icon("menu", class_name="h-[30px] w-[30px]"),
        rx.cond(
            DiscoveryState.filters_active,
            rx.el.span(
                aria_hidden="true",
                class_name="absolute right-1 top-1 size-2.5 rounded-full bg-[#e08b12] ring-2 ring-white",
            ),
            rx.fragment(),
        ),
        type="button",
        on_click=DiscoveryState.toggle_filter_panel,
        aria_label=ui("Open Search filters"),
        id="gah-board-filter-open",
        class_name="gah-inverse-text absolute bottom-14 right-3 z-30 flex size-[54px] items-center justify-center rounded-full border-0 bg-white text-[#fba922] transition-colors hover:bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922] sm:bottom-3",
    )


def map_panel() -> rx.Component:
    return rx.el.div(
        filter_dismiss_layer(),
        rx.el.div(
            rx.el.div(
                open_free_map(
                    markers=(
                        rx.cond(
                            DiscoveryState.show_jobs
                            | DiscoveryState.show_helpers,
                            DiscoveryState.map_markers,
                            [],
                        )
                        + rx.cond(
                            DiscoveryState.show_events,
                            EventState.map_markers,
                            [],
                        )
                    ),
                    center=DiscoveryState.map_center,
                    zoom=DiscoveryState.map_zoom,
                    on_marker_select=DiscoveryState.select_marker,
                    on_interaction_start=DiscoveryState.handle_map_interaction,
                    viewport_points=DiscoveryState.viewport_points,
                    on_visible_points_change=DiscoveryState.update_visible_points,
                    class_name="absolute inset-0 h-full w-full",
                ),
                rx.cond(
                    (
                        DiscoveryState.show_jobs
                        & (DiscoveryState.posts.length() > 0)
                    )
                    | (
                        DiscoveryState.show_events
                        & (EventState.events.length() > 0)
                    )
                    | (
                        DiscoveryState.show_helpers
                        & (DiscoveryState.visible_helpers.length() > 0)
                    ),
                    rx.fragment(),
                    rx.el.div(
                        rx.icon(
                            "map-pin-off",
                            class_name="h-4 w-4 text-[#e08b12]",
                        ),
                        rx.el.p(
                            rx.cond(
                                DiscoveryState.show_events
                                & ~DiscoveryState.show_jobs
                                & ~DiscoveryState.show_helpers,
                                "No events match your filters",
                                rx.cond(
                                    DiscoveryState.show_jobs,
                                    "No open jobs match your filters",
                                    rx.cond(
                                        DiscoveryState.show_helpers,
                                        "No helpers match your filters",
                                        "No results match your filters",
                                    ),
                                ),
                            ),
                            class_name="text-xs font-semibold text-[#404040]",
                        ),
                        class_name="pointer-events-none absolute left-1/2 top-3 z-30 w-fit -translate-x-1/2 flex items-center gap-2 rounded-full border border-white/80 bg-[#ffffff]/90 px-3 py-1.5 backdrop-blur-md",
                    ),
                ),
                rx.cond(
                    DiscoveryState.filter_panel_open,
                    filter_drawer(
                        "gah-search-drawer absolute bottom-0 right-0 z-30 flex w-full max-w-md max-h-full flex-col overflow-y-auto overscroll-contain rounded-tl-2xl border-0 bg-white/60 p-4 origin-bottom-right text-[#404040] backdrop-blur-sm md:w-1/2"
                    ),
                    rx.fragment(),
                ),
                filter_button(),
                class_name="relative w-full h-[32rem] sm:h-[39rem] lg:h-[44rem] overflow-hidden border-y border-[#d4d4d4] bg-[#fff7e8]",
            ),
            class_name="w-full border-y border-[#d4d4d4] bg-white",
        ),
        class_name="relative left-1/2 w-screen -translate-x-1/2 z-0",
    )


def helper_row(helper: HelperProfile) -> rx.Component:
    return rx.el.button(
        helper_photo(
            helper,
            "size-12 rounded-full border-2 border-white bg-[#fff7e8] object-cover shrink-0",
        ),
        rx.el.div(
            rx.el.p(
                helper["name"],
                class_name="text-sm font-semibold text-black text-left",
            ),
            rx.cond(
                helper["handle"],
                rx.el.p(
                    helper["handle"],
                    class_name="text-[11px] font-bold text-[#b86e08] text-left",
                ),
                rx.fragment(),
            ),
            rx.cond(
                helper["headline"],
                rx.el.p(
                    helper["headline"],
                    class_name="text-xs font-medium text-[#404040] mt-1 text-left line-clamp-2",
                ),
                rx.el.p(
                    "A Go and Help neighbour you could get help from",
                    class_name="text-xs font-medium text-[#404040] mt-1 text-left italic",
                ),
            ),
            rx.el.div(
                rx.cond(
                    helper["city"],
                    rx.el.span(
                        rx.icon("map-pin", class_name="h-3 w-3"),
                        helper["city"],
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#f5f5f5] px-2.5 py-0.5 text-[11px] font-semibold text-[#404040]",
                    ),
                    rx.fragment(),
                ),
                detail_rating(helper["rating"], helper["reviews"]),
                class_name="flex flex-wrap items-center gap-1.5 mt-2",
            ),
            rx.el.div(
                rx.foreach(helper["category_chips"], category_pill),
                rx.foreach(helper["skill_chips"], skill_pill),
                class_name="flex flex-wrap items-center gap-1.5 mt-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        type="button",
        aria_label=f"Open the profile of {helper['name']}",
        title=f"Open the profile of {helper['name']}",
        on_click=lambda: DiscoveryState.open_member_profile(helper["id"]),
        class_name=rx.cond(
            DiscoveryState.selected_helper["id"] == helper["id"],
            "flex items-start gap-4 w-full rounded-2xl border-2 border-[#fba922] bg-[#fba922] p-4 text-left transition-colors",
            "flex items-start gap-4 w-full rounded-2xl border border-[#e5e5e5] bg-white p-4 text-left transition-colors hover:border-[#e08b12]",
        ),
    )


def helper_list() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            rx.match(
                DiscoveryState.visible_helpers.length(),
                (0, rx.el.span("No helpers nearby")),
                (
                    1,
                    rx.el.span(
                        rx.el.span("1", class_name="text-[#e08b12]"),
                        " helper nearby",
                    ),
                ),
                rx.el.span(
                    rx.el.span(
                        DiscoveryState.visible_helpers.length(),
                        class_name="text-[#e08b12]",
                    ),
                    " helpers nearby",
                ),
            ),
            class_name="mb-3 w-full text-center text-xl sm:text-2xl font-bold tracking-tight text-[#111827]",
        ),
        rx.cond(
            DiscoveryState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="flex flex-col gap-3 w-full",
            ),
            rx.cond(
                DiscoveryState.visible_helpers.length() > 0,
                rx.el.div(
                    rx.foreach(DiscoveryState.visible_helpers, helper_row),
                    class_name="flex flex-col gap-3 w-full",
                ),
                rx.el.div(
                    rx.icon(
                        "users-round",
                        class_name="h-6 w-6 text-[#404040] mb-2",
                    ),
                    rx.el.p(
                        "No helpers to show yet.",
                        class_name="text-sm font-semibold text-[#404040]",
                    ),
                    rx.el.p(
                        rx.cond(
                            DiscoveryState.viewport_ready,
                            "Move the map to find more neighbours in view.",
                            "Waiting for the map to locate visible neighbours.",
                        ),
                        class_name="text-sm font-medium text-[#404040] mt-1",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-white/60 px-6 py-10",
                ),
            ),
        ),
        class_name="w-full bg-transparent",
    )


def detail_rating(rating: rx.Var[float], count: rx.Var[int]) -> rx.Component:
    return rx.cond(
        count > 0,
        rx.el.div(
            rx.el.span(
                rx.foreach(
                    rx.Var.range(1, 6),
                    lambda step: rx.icon(
                        "star",
                        class_name=rx.cond(
                            step <= rating + 0.5,
                            "size-4 fill-[#fba922] text-[#fba922]",
                            "size-4 fill-none text-[#fba922]",
                        ),
                    ),
                ),
                role="img",
                aria_label=f"{rating:.1f} out of 5 stars",
                class_name="flex items-center gap-0.5",
            ),
            rx.el.span(f"{rating:.1f} · {count} reviews"),
            class_name="mt-1 flex flex-wrap items-center gap-1.5 text-sm font-normal text-[#b86e08]",
        ),
        rx.fragment(),
    )


def detail_contact(member_id: rx.Var[int]) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("user-plus", class_name="size-3.5"),
            rx.cond(
                ContactsState.is_requesting, ui("Sending…"), ui("Add contact")
            ),
            type="button",
            disabled=ContactsState.is_requesting,
            on_click=lambda: ContactsState.send_request(member_id, ""),
            class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#fba922] bg-white px-3 py-1.5 text-xs font-semibold text-[#b86e08] hover:bg-[#fff7e8] disabled:opacity-60",
        ),
        error_banner(ContactsState.error),
        success_banner(ContactsState.success),
        class_name="flex flex-col gap-2",
    )


def helper_detail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=DiscoveryState.selected_helper["image_url"],
                alt="",
                class_name="size-16 rounded-full border-2 border-white bg-[#fff7e8] object-cover shrink-0",
            ),
            rx.el.div(
                rx.el.h3(
                    DiscoveryState.selected_helper["name"],
                    class_name="text-xl font-bold tracking-tight text-black leading-snug",
                ),
                rx.cond(
                    DiscoveryState.selected_helper["handle"],
                    rx.el.p(
                        DiscoveryState.selected_helper["handle"],
                        class_name="text-xs font-bold text-[#b86e08] mt-0.5",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    DiscoveryState.selected_helper["joined"],
                    rx.el.p(
                        f"Joined {DiscoveryState.selected_helper['joined']}",
                        class_name="mt-1 text-xs font-semibold text-[#404040]",
                    ),
                    rx.fragment(),
                ),
                detail_rating(
                    DiscoveryState.selected_helper["rating"],
                    DiscoveryState.selected_helper["reviews"],
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-3 w-full rounded-xl bg-white p-3",
        ),
        rx.cond(
            (DiscoveryState.selected_helper["category_chips"].length() > 0)
            | (DiscoveryState.selected_helper["skill_chips"].length() > 0),
            rx.el.div(
                rx.el.p(
                    "Skills and knowledge",
                    class_name="text-sm font-bold text-[#404040]",
                ),
                rx.el.div(
                    rx.foreach(
                        DiscoveryState.selected_helper["category_chips"],
                        category_pill,
                    ),
                    rx.foreach(
                        DiscoveryState.selected_helper["skill_chips"],
                        skill_pill,
                    ),
                    class_name="mt-2 flex flex-wrap gap-1.5",
                ),
                class_name="w-full rounded-2xl bg-white p-4",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DiscoveryState.selected_helper["headline"],
            rx.el.div(
                rx.el.p(
                    f"About {DiscoveryState.selected_helper['name']}",
                    class_name="text-sm font-bold text-[#404040]",
                ),
                rx.el.p(
                    DiscoveryState.selected_helper["headline"],
                    custom_attrs={"translate": "yes"},
                    dir="auto",
                    class_name="mt-1 whitespace-pre-wrap text-base font-normal text-[#404040]",
                ),
                class_name="rounded-xl bg-white p-3",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            detail_meta_row(
                "map-pin",
                "Based in",
                rx.cond(
                    DiscoveryState.selected_helper["city"],
                    DiscoveryState.selected_helper["city"],
                    "City not shared yet",
                ),
            ),
            detail_meta_row(
                "languages",
                "Languages",
                rx.cond(
                    DiscoveryState.selected_helper["languages"],
                    DiscoveryState.selected_helper["languages"],
                    "Not listed",
                ),
            ),
            detail_meta_row(
                "wrench",
                "Skills",
                rx.cond(
                    DiscoveryState.selected_helper["skills"],
                    DiscoveryState.selected_helper["skills"],
                    "Not listed",
                ),
                user_authored=DiscoveryState.selected_helper["skills"] != "",
            ),
            detail_meta_row(
                "clock",
                "Availability",
                rx.cond(
                    DiscoveryState.selected_helper["availability"],
                    DiscoveryState.selected_helper["availability"],
                    "Ask them directly",
                ),
                user_authored=DiscoveryState.selected_helper["availability"]
                != "",
            ),
            class_name="flex flex-col gap-3 w-full rounded-2xl bg-white p-4",
        ),
        direct_help_section(),
        original_language_disclosure(
            DiscoveryState.selected_helper["headline"]
        ),
        rx.cond(
            DiscoveryState.selected_helper["id"] > 0,
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        rx.icon("user-plus", class_name="size-3.5"),
                        rx.cond(
                            ContactsState.is_requesting,
                            ui("Sending…"),
                            ui("Add contact"),
                        ),
                        type="button",
                        disabled=ContactsState.is_requesting,
                        on_click=ContactsState.send_request(
                            DiscoveryState.selected_helper["id"], ""
                        ),
                        class_name="flex w-fit items-center gap-1 rounded-full bg-white px-2 py-1.5 text-xs text-[#b86e08] disabled:opacity-60",
                    ),
                    report_button(
                        REPORT_TARGET_PROFILE,
                        DiscoveryState.selected_helper["id"],
                        DiscoveryState.selected_helper["name"],
                    ),
                    block_member_button(
                        DiscoveryState.selected_helper["id"],
                        DiscoveryState.selected_helper["name"],
                        "Block member",
                    ),
                    class_name="flex w-full flex-wrap items-center justify-center gap-1",
                ),
                error_banner(ContactsState.error),
                success_banner(ContactsState.success),
                class_name="flex w-full flex-col gap-2 rounded-xl bg-white p-3",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col gap-3 w-full [&_span]:font-normal [&_span]:text-base",
    )


def group_request_choice(post: dict[str, str]) -> rx.Component:
    return rx.el.button(
        category_icon(post["category"], "h-4 w-4"),
        rx.el.span(
            rx.cond(
                DiscoveryState.selected_post["id"] == post["id"],
                "Viewing this request",
                post["title"],
            ),
            class_name="min-w-0 flex-1 text-left text-sm font-semibold",
        ),
        rx.icon("chevron-right", class_name="size-4 shrink-0"),
        type="button",
        aria_label=f"Open {post['title']}",
        on_click=lambda: DiscoveryState.select_post(post["id"]),
        class_name=rx.cond(
            DiscoveryState.selected_post["id"] == post["id"],
            "flex w-full items-center gap-2 rounded-xl bg-[#fff7e8] px-3 py-2 text-[#111827]",
            "flex w-full items-center gap-2 rounded-xl bg-white px-3 py-2 text-[#111827] hover:bg-[#fff7e8]",
        ),
    )


def job_row(group: ListPostGroup, **props) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            avatar_with_tick(
                group["post"]["poster_image"],
                group["post"]["poster_verified"],
                "size-10 rounded-full bg-[#fff7e8] object-cover",
                "Request poster photo",
            ),
            rx.el.span(
                rx.el.span(
                    group["post"]["title"],
                    class_name="block text-sm font-bold text-[#111827] [overflow-wrap:anywhere]",
                ),
                rx.el.span(
                    group["post"]["poster_name"],
                    class_name="block text-xs font-medium text-[#6b7280]",
                ),
                rx.el.span(
                    group["post"]["poster_languages"],
                    class_name="block text-xs font-medium text-[#6b7280]",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.icon(
                rx.cond(
                    group["ids"].contains(DiscoveryState.selected_post["id"]),
                    "chevron-down",
                    "chevron-right",
                ),
                class_name="size-4 shrink-0 text-[#e08b12]",
            ),
            type="button",
            aria_expanded=group["ids"].contains(
                DiscoveryState.selected_post["id"]
            ),
            aria_label=f"Open {group['post']['title']} from {group['poster_name']}",
            on_click=lambda: DiscoveryState.select_post(group["post"]["id"]),
            class_name="flex w-full items-center gap-3 rounded-2xl bg-white px-3 py-3 text-left hover:bg-[#fff7e8]",
        ),
        class_name="relative w-full rounded-2xl bg-white shadow-[0_2px_10px_rgba(17,24,39,0.10)]",
        **props,
    )


def job_list() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            rx.match(
                DiscoveryState.list_post_groups.length(),
                (0, rx.el.span("No people need help nearby")),
                (
                    1,
                    rx.el.span(
                        rx.el.span("1", class_name="text-[#e08b12]"),
                        " person who needs help",
                    ),
                ),
                rx.el.span(
                    rx.el.span(
                        DiscoveryState.list_post_groups.length(),
                        class_name="text-[#e08b12]",
                    ),
                    " people who need help",
                ),
            ),
            class_name="mb-0.5 w-full text-center text-xl sm:text-2xl font-bold tracking-tight text-[#111827]",
        ),
        rx.el.p(
            "in your selected area",
            class_name="mb-2 text-center text-xs font-medium text-[#6b7280]",
        ),
        rx.cond(
            DiscoveryState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="flex flex-col gap-3 w-full",
            ),
            rx.cond(
                DiscoveryState.visible_posts.length() > 0,
                rx.el.div(
                    rx.foreach(DiscoveryState.list_post_groups, job_row),
                    class_name="flex flex-col gap-3 w-full",
                ),
                rx.el.div(
                    rx.icon(
                        "hand-helping",
                        class_name="h-6 w-6 text-[#404040] mb-2",
                    ),
                    rx.el.p(
                        "No jobs nearby right now",
                        class_name="text-sm font-semibold text-[#404040]",
                    ),
                    rx.el.p(
                        rx.cond(
                            DiscoveryState.viewport_ready,
                            "Move the map to find more requests in view.",
                            "Waiting for the map to locate visible requests.",
                        ),
                        class_name="text-sm font-medium text-[#404040] mt-1",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-white/60 px-6 py-10",
                ),
            ),
        ),
        class_name="w-full bg-transparent",
    )


def poster_card() -> rx.Component:
    return rx.el.div(
        avatar_with_tick(
            DiscoveryState.selected_post["poster_image"],
            DiscoveryState.selected_post["poster_verified"],
            "size-16 rounded-full bg-[#fff7e8] object-cover shrink-0",
            "Request poster photo",
            member_id=DiscoveryState.selected_post["poster_id"],
        ),
        rx.el.div(
            rx.el.h3(
                DiscoveryState.selected_post["title"],
                class_name="text-xl font-bold tracking-tight text-black leading-snug [overflow-wrap:anywhere]",
            ),
            rx.el.p(
                DiscoveryState.selected_post["poster_name"],
                class_name="mt-0.5 text-sm font-semibold text-[#404040]",
            ),
            rx.cond(
                DiscoveryState.selected_post["poster_headline"],
                browser_translatable_text(
                    DiscoveryState.selected_post["poster_headline"],
                    class_name="mt-1 text-xs font-medium text-[#404040] leading-relaxed",
                ),
                rx.fragment(),
            ),
            rx.cond(
                DiscoveryState.selected_post["poster_languages"],
                rx.el.p(
                    rx.icon(
                        "languages",
                        class_name="mr-1 inline h-3 w-3 text-[#b86e08]",
                    ),
                    DiscoveryState.selected_post["poster_languages"],
                    class_name="mt-1 text-xs font-medium text-[#404040]",
                ),
                rx.fragment(),
            ),
            detail_rating(
                DiscoveryState.selected_post["poster_rating"],
                DiscoveryState.selected_post["poster_reviews"],
            ),
            class_name="min-w-0 flex-1",
        ),
        class_name="flex w-full items-start gap-3",
    )


def request_footer_actions() -> rx.Component:
    return rx.cond(
        (DiscoveryState.selected_post["poster_id"] > 0)
        & (
            DiscoveryState.selected_post["poster_id"].to_string()
            != AuthState.subscriber_id
        ),
        rx.el.div(
            rx.el.div(
                detail_contact(DiscoveryState.selected_post["poster_id"]),
                report_button(
                    REPORT_TARGET_JOB_MESSAGE,
                    DiscoveryState.selected_post["id"],
                    DiscoveryState.selected_post["title"],
                ),
                class_name="flex w-full flex-wrap items-start justify-center gap-2",
            ),
            class_name="flex w-full justify-center border-t border-[#e5e5e5] pt-4",
        ),
        rx.fragment(),
    )


def request_action_stack(context: str | rx.Var[str]) -> rx.Component:
    return rx.el.div(
        help_share(
            DiscoveryState.selected_post["id"],
            DiscoveryState.selected_post["title"],
            context,
            "relative z-50",
        ),
        bookmark_tab(
            DiscoveryState.selected_post["id"],
            DiscoveryState.selected_post["title"],
            "relative z-40",
        ),
        role="group",
        aria_label="Share or bookmark this help request",
        class_name="relative ml-auto flex w-fit shrink-0 flex-row items-center gap-2",
    )


def accept_section() -> rx.Component:
    return rx.match(
        DiscoveryState.selected_post["my_status"],
        (
            "accepted",
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "circle-check-big",
                        class_name="h-4 w-4 text-black",
                    ),
                    rx.el.p(
                        "You accepted this job",
                        class_name="text-sm font-semibold text-black",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    f"A conversation with {DiscoveryState.selected_post['poster_name']} is open — agree the details there.",
                    class_name="text-sm font-medium text-black mt-1 leading-relaxed",
                ),
                class_name="w-full rounded-2xl border border-[#fba922] bg-[#fba922] p-4",
            ),
        ),
        (
            "pending",
            rx.el.div(
                rx.el.p(
                    "Your offer is waiting for a response",
                    class_name="text-sm font-semibold text-[#e08b12]",
                ),
                class_name="w-full rounded-2xl border border-[#d4d4d4] bg-[#fff7e8] p-4",
            ),
        ),
        rx.cond(
            DiscoveryState.selected_post["poster_id"].to_string()
            == AuthState.subscriber_id,
            rx.el.p(
                "This is your request",
                class_name="text-center text-sm font-medium text-[#6b7280]",
            ),
            offer_help_section(),
        ),
    )


def category_pill(label: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        label,
        class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
    )


def skill_pill(label: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        label,
        class_name="w-fit rounded-full border border-[#fba922] bg-[#fba922] px-2.5 py-1 text-[11px] font-semibold text-[#000000]",
    )


def offer_estimates() -> rx.Component:
    return rx.el.div(
        rx.cond(
            DiscoveryState.selected_post["allow_price_quote"],
            rx.el.div(
                rx.el.label(
                    rx.icon("coins", class_name="h-4 w-4 text-[#e08b12]"),
                    "Give your cost estimate",
                    html_for="offer-price",
                    class_name="flex items-center justify-center gap-2 text-center text-sm font-bold text-[#111827]",
                ),
                rx.el.div(
                    rx.el.input(
                        id="offer-price",
                        type="number",
                        min="1",
                        step="1",
                        input_mode="numeric",
                        placeholder="0",
                        default_value=DiscoveryState.offer_price,
                        on_change=DiscoveryState.set_offer_price_number,
                        class_name="min-w-0 w-1/2 max-w-36 appearance-none rounded-xl border border-gray-300 bg-white p-3 text-right text-[#111827] [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none",
                    ),
                    rx.el.span(
                        DiscoveryState.selected_post["reward_currency"],
                        class_name="text-sm font-bold text-[#e08b12]",
                    ),
                    class_name="mt-2 flex items-center justify-center gap-3",
                ),
                class_name="rounded-xl bg-white p-3 shadow-[0_2px_10px_rgba(17,24,39,0.10)]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DiscoveryState.selected_post["allow_duration_estimate"],
            rx.el.div(
                rx.el.p(
                    rx.icon("hourglass", class_name="h-4 w-4 text-[#e08b12]"),
                    "Give your duration estimate",
                    class_name="flex items-center justify-center gap-2 text-center text-sm font-bold text-[#111827]",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.select(
                                rx.foreach(
                                    rx.Var.range(0, 11),
                                    lambda value: rx.el.option(
                                        value, value=value.to_string()
                                    ),
                                ),
                                id="offer-hours",
                                value=DiscoveryState.offer_hours,
                                on_change=DiscoveryState.set_offer_hours,
                                aria_label="Hours of help",
                                class_name="w-20 appearance-none rounded-xl border border-gray-300 bg-white py-2 pl-3 pr-7 text-center text-[#111827]",
                            ),
                            rx.icon(
                                "chevron-down",
                                class_name="pointer-events-none absolute right-2 top-1/2 size-4 -translate-y-1/2 text-[#e08b12]",
                            ),
                            class_name="relative",
                        ),
                        rx.el.label(
                            "Hours",
                            html_for="offer-hours",
                            class_name="text-xs text-[#404040]",
                        ),
                        class_name="flex flex-col items-center gap-1",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.select(
                                rx.foreach(
                                    rx.Var.range(0, 12),
                                    lambda value: rx.el.option(
                                        value * 5, value=(value * 5).to_string()
                                    ),
                                ),
                                id="offer-minutes",
                                value=DiscoveryState.offer_minutes,
                                on_change=DiscoveryState.set_offer_minutes,
                                aria_label="Minutes of help",
                                class_name="w-20 appearance-none rounded-xl border border-gray-300 bg-white py-2 pl-3 pr-7 text-center text-[#111827]",
                            ),
                            rx.icon(
                                "chevron-down",
                                class_name="pointer-events-none absolute right-2 top-1/2 size-4 -translate-y-1/2 text-[#e08b12]",
                            ),
                            class_name="relative",
                        ),
                        rx.el.label(
                            "Minutes",
                            html_for="offer-minutes",
                            class_name="text-xs text-[#404040]",
                        ),
                        class_name="flex flex-col items-center gap-1",
                    ),
                    class_name="mt-2 flex items-start justify-center gap-3",
                ),
                rx.el.div(
                    rx.el.span(
                        "For", class_name="text-sm font-medium text-[#404040]"
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.foreach(
                                rx.Var.range(1, 32),
                                lambda value: rx.el.option(
                                    value, value=value.to_string()
                                ),
                            ),
                            value=DiscoveryState.offer_period_count,
                            on_change=DiscoveryState.set_offer_period_count,
                            aria_label="Number of days, weeks or months",
                            class_name="w-16 appearance-none rounded-xl border border-gray-300 bg-white py-2 pl-2 pr-6 text-center text-[#111827]",
                        ),
                        rx.icon(
                            "chevron-down",
                            class_name="pointer-events-none absolute right-1 top-1/2 size-3 -translate-y-1/2 text-[#e08b12]",
                        ),
                        class_name="relative",
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.el.option("Day", value="days"),
                            rx.el.option("Week", value="weeks"),
                            rx.el.option("Month", value="months"),
                            value=DiscoveryState.offer_period_unit,
                            on_change=DiscoveryState.set_offer_period_unit,
                            aria_label="Duration period unit",
                            class_name="appearance-none rounded-xl border border-gray-300 bg-white py-2 pl-3 pr-9 text-sm text-[#111827]",
                        ),
                        rx.icon(
                            "chevron-down",
                            class_name="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-[#e08b12]",
                        ),
                        class_name="relative",
                    ),
                    class_name="mt-2 flex flex-wrap items-center justify-center gap-2",
                ),
                class_name="rounded-xl bg-white p-3 shadow-[0_2px_10px_rgba(17,24,39,0.10)]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            (DiscoveryState.offer_validation != "")
            & (
                DiscoveryState.offer_validation
                != "Write a message of 5–2000 characters."
            ),
            rx.el.p(
                DiscoveryState.offer_validation,
                role="status",
                class_name="w-full text-center text-sm text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 flex flex-col gap-3",
    )


def offer_help_section() -> rx.Component:
    """Compose and send without leaving the information sheet."""
    return rx.el.div(
        rx.el.div(
            rx.icon("send", class_name="h-4 w-4 text-[#e08b12]"),
            rx.el.p(
                "Offer how you can help",
                class_name="text-sm font-bold text-[#000000]",
            ),
            class_name="flex items-center justify-center gap-2 text-center",
        ),
        rx.el.textarea(
            default_value=DiscoveryState.offer_draft,
            aria_label="Offer how you can help",
            rows="4",
            on_change=DiscoveryState.set_offer_draft.debounce(300),
            class_name="mt-3 w-full rounded-xl border border-[#fba922] bg-white p-3 text-[#111827] resize-y leading-relaxed",
        ),
        offer_estimates(),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    DiscoveryState.is_sending_offer,
                    rx.el.span(
                        rx.spinner(class_name="h-4 w-4"),
                        ui("Sending…"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                    rx.el.span(
                        rx.icon("send", class_name="h-4 w-4"),
                        ui("Offer help"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                ),
                type="button",
                disabled=~DiscoveryState.offer_can_send,
                on_click=DiscoveryState.send_offer,
                class_name="w-fit rounded-xl bg-[#fba922] px-5 py-3 text-sm font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            class_name="mt-3 flex items-center justify-center gap-2 w-full",
        ),
        class_name="w-full flex flex-col",
    )


def direct_request_option(item: DirectRequest) -> rx.Component:
    return rx.el.option(item["title"], value=item["id"].to_string())


def direct_help_section() -> rx.Component:
    """Inline composer: ask this helper about one of my active requests."""
    return rx.cond(
        DiscoveryState.direct_open,
        rx.el.div(
            rx.el.div(
                rx.icon("mail", class_name="h-4 w-4 text-[#b86e08]"),
                rx.el.p(
                    "Ask this helper directly",
                    class_name="text-sm font-bold text-[#000000]",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    type="button",
                    aria_label="Close the direct request composer",
                    on_click=DiscoveryState.close_direct_help,
                    class_name="ml-auto flex size-7 items-center justify-center rounded-full border border-[#d4d4d4] bg-white text-[#404040] transition-colors hover:text-[#b86e08]",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.cond(
                DiscoveryState.is_loading_direct,
                rx.el.div(
                    class_name="mt-3 animate-pulse h-24 w-full rounded-xl bg-[#e5e5e5]"
                ),
                rx.cond(
                    DiscoveryState.has_direct_requests,
                    rx.el.div(
                        rx.cond(
                            DiscoveryState.direct_warning,
                            rx.el.p(
                                DiscoveryState.direct_warning,
                                role="status",
                                class_name="rounded-xl border border-[#d4d4d4] bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#e08b12]",
                            ),
                            rx.fragment(),
                        ),
                        rx.el.div(
                            rx.el.label(
                                "Which help request?",
                                html_for="direct-help-request",
                                class_name="block text-sm font-semibold text-[#111827]",
                            ),
                            rx.el.p(
                                "Your active requests – required",
                                class_name="mb-2 text-xs text-[#404040]",
                            ),
                            rx.el.div(
                                rx.el.select(
                                    rx.el.option(
                                        "Choose a help request",
                                        value="",
                                    ),
                                    rx.foreach(
                                        DiscoveryState.direct_requests,
                                        direct_request_option,
                                    ),
                                    id="direct-help-request",
                                    value=DiscoveryState.direct_post_id.to_string(),
                                    on_change=DiscoveryState.select_direct_request,
                                    class_name="w-full appearance-none cursor-pointer rounded-xl border border-[#d4d4d4] bg-white py-3 pl-4 pr-9 text-sm font-semibold text-[#000000] outline-hidden focus:border-[#e08b12] focus:ring-2 focus:ring-[#fff7e8]",
                                ),
                                rx.icon(
                                    "chevron-down",
                                    class_name="h-4 w-4 text-[#404040] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
                                ),
                                class_name="relative w-full",
                            ),
                            class_name="w-full",
                        ),
                        rx.cond(
                            DiscoveryState.direct_post_id > 0,
                            rx.el.div(
                                rx.el.textarea(
                                    default_value=DiscoveryState.direct_draft,
                                    rows="4",
                                    on_change=DiscoveryState.set_direct_draft.debounce(
                                        300
                                    ),
                                    class_name=INPUT_CLASS
                                    + " resize-y leading-relaxed",
                                ),
                                rx.el.div(
                                    rx.el.button(
                                        rx.cond(
                                            DiscoveryState.is_sending_direct,
                                            rx.el.span(
                                                rx.spinner(
                                                    class_name="h-4 w-4"
                                                ),
                                                ui("Sending…"),
                                                class_name="flex items-center justify-center gap-2",
                                            ),
                                            rx.el.span(
                                                rx.icon(
                                                    "send", class_name="h-4 w-4"
                                                ),
                                                ui("Send request"),
                                                class_name="flex items-center justify-center gap-2",
                                            ),
                                        ),
                                        type="button",
                                        disabled=~DiscoveryState.direct_can_send
                                        | DiscoveryState.is_sending_direct,
                                        on_click=DiscoveryState.send_direct_help,
                                        class_name="w-fit rounded-xl bg-[#fba922] px-5 py-2.5 text-sm font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                                    ),
                                    class_name="flex w-full justify-end pt-2",
                                ),
                                class_name="w-full rounded-xl border border-[#f7d9a0] bg-white p-2",
                            ),
                            rx.fragment(),
                        ),
                        class_name="mt-3 flex flex-col gap-3 w-full",
                    ),
                    rx.el.div(
                        rx.el.p(
                            DiscoveryState.direct_notice,
                            class_name="text-sm font-semibold text-[#000000] leading-relaxed",
                        ),
                        rx.el.button(
                            rx.icon("notebook-pen", class_name="h-4 w-4"),
                            "Post a help request",
                            type="button",
                            on_click=DiscoveryState.go_to_ask_for_help,
                            class_name="mt-3 flex w-fit items-center gap-2 rounded-xl bg-[#e08b12] px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08]",
                        ),
                        class_name="mt-3 w-full rounded-xl border border-[#fff7e8] bg-[#fff7e8] p-4",
                    ),
                ),
            ),
            class_name="w-full rounded-2xl border border-[#fba922] bg-white p-4",
        ),
        rx.el.button(
            rx.icon("mail", class_name="h-4 w-4"),
            "Request Direct help",
            type="button",
            on_click=DiscoveryState.open_direct_help,
            class_name="mx-auto flex w-fit items-center justify-center gap-2 rounded-xl bg-[#e08b12] px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-[#b86e08]",
        ),
    )


def detail_meta_row(
    icon: str,
    label: str,
    value: rx.Var[str],
    user_authored: bool | rx.Var[bool] = False,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex items-center justify-center size-8 rounded-lg bg-[#fff7e8] shrink-0",
        ),
        rx.el.div(
            rx.el.span(
                rx.cond(label == "Reward", "", f"{label} – "),
                class_name="shrink-0 text-sm font-bold text-[#404040]",
            ),
            rx.cond(
                user_authored,
                browser_translatable_text(
                    value,
                    class_name="inline text-sm font-medium text-[#404040] leading-snug",
                ),
                rx.el.span(
                    value,
                    class_name="text-sm font-medium text-[#404040] leading-snug",
                ),
            ),
            class_name="min-w-0 flex-1 leading-snug",
        ),
        class_name="flex items-start gap-3 w-full",
    )


def request_where_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("map-pin", class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex size-8 shrink-0 items-center justify-center rounded-lg bg-[#fff7e8]",
        ),
        rx.el.div(
            rx.el.span(
                rx.el.span(
                    "Where – ",
                    class_name="text-sm font-bold text-[#404040]",
                ),
                DiscoveryState.selected_post["location"],
                class_name="min-w-0 max-w-full text-sm font-medium leading-snug text-[#404040] [overflow-wrap:anywhere]",
            ),
            rx.el.button(
                rx.icon("map-pin", class_name="h-3.5 w-3.5"),
                ui("Show on map"),
                type="button",
                on_click=lambda: DiscoveryState.show_post_on_map(
                    DiscoveryState.selected_post["id"]
                ),
                class_name="flex w-fit shrink-0 items-center gap-1 whitespace-nowrap rounded-full border border-[#f7d9a0] bg-[#fff7e8] px-2 py-1.5 text-xs font-semibold text-[#b86e08] hover:bg-[#ffedcc] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="flex min-w-0 flex-1 flex-wrap items-center gap-x-2 gap-y-1.5",
        ),
        class_name="flex w-full min-w-0 items-start gap-3",
    )


def detail_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            poster_card(),
            class_name=rx.cond(
                DiscoveryState.is_list_view,
                "w-full min-w-0",
                "w-full min-w-0 pr-10",
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    ui("Description"),
                    class_name="min-w-0 text-base font-bold leading-snug text-[#111827] [overflow-wrap:anywhere]",
                ),
                request_action_stack(
                    rx.cond(
                        DiscoveryState.is_list_view, "list-detail", "detail"
                    )
                ),
                class_name="flex w-full min-w-0 flex-wrap items-center justify-between gap-x-3 gap-y-2",
            ),
            browser_translatable_text(
                DiscoveryState.selected_post["description"],
                class_name="text-sm font-medium text-[#404040] leading-relaxed whitespace-pre-line",
            ),
            passport_photos(),
            class_name=rx.cond(
                DiscoveryState.is_list_view,
                "flex w-full flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-3 shadow-xs",
                "flex w-full flex-col gap-3 rounded-2xl border border-[#e5e5e5] bg-white p-4 shadow-xs",
            ),
        ),
        rx.el.div(
            detail_meta_row(
                "tag",
                "Category",
                DiscoveryState.selected_post["category_label"],
            ),
            request_where_row(),
            detail_meta_row(
                "calendar",
                "When",
                DiscoveryState.selected_post["scheduled_full"],
            ),
            detail_meta_row(
                "gift",
                "Reward",
                DiscoveryState.selected_post["reward_label"],
            ),
            detail_meta_row(
                "hourglass",
                "Duration",
                DiscoveryState.selected_post["duration_label"],
            ),
            class_name=rx.cond(
                DiscoveryState.is_list_view,
                "flex flex-col gap-3 w-full rounded-2xl border border-gray-200 bg-white p-3 shadow-xs",
                "flex flex-col gap-3 w-full rounded-2xl border border-[#e5e5e5] bg-white p-4 shadow-xs",
            ),
        ),
        rx.el.div(
            accept_section(),
            class_name=rx.cond(
                DiscoveryState.is_list_view,
                "w-full rounded-2xl border border-gray-200 bg-white p-3 shadow-xs",
                "w-full rounded-2xl border border-[#e5e5e5] bg-white p-4 shadow-xs",
            ),
        ),
        rx.cond(
            DiscoveryState.thread_id > 0,
            rx.el.div(
                rx.el.div(
                    rx.icon("send", class_name="h-4 w-4 text-[#e08b12]"),
                    rx.el.p(
                        f"Message to {DiscoveryState.thread_with}",
                        class_name="text-sm font-semibold text-black",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    DiscoveryState.thread_note,
                    class_name="text-sm font-medium text-[#404040] mt-2 italic leading-relaxed",
                ),
                class_name="w-full rounded-2xl border border-[#e5e5e5] bg-white p-4",
            ),
            rx.fragment(),
        ),
        request_footer_actions(),
        class_name="flex flex-col gap-4 w-full",
    )


def passport_photo(photo_path: rx.Var[str]) -> rx.Component:
    return rx.image(
        src=rx.get_upload_url(photo_path),
        alt=f"Photo of {DiscoveryState.selected_post['title']}",
        class_name="min-w-full w-full aspect-square object-cover shrink-0 snap-center bg-[#f5f5f5]",
        key=photo_path,
    )


def passport_photos() -> rx.Component:
    return rx.cond(
        DiscoveryState.selected_post["photos"].length() > 0,
        rx.el.div(
            rx.el.div(
                rx.foreach(
                    DiscoveryState.selected_post["photos"], passport_photo
                ),
                role="region",
                aria_label="Request photos — swipe to browse",
                tab_index=0,
                class_name="flex w-full min-w-0 overflow-x-auto touch-pan-x snap-x snap-mandatory [scrollbar-width:none] [&::-webkit-scrollbar]:hidden focus-visible:outline-2 focus-visible:outline-[#fba922]",
                key=DiscoveryState.selected_post["id"],
            ),
            class_name="w-full",
        ),
        rx.fragment(),
    )


def detail_panel() -> rx.Component:
    return rx.cond(
        DiscoveryState.drawer_open,
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        type="button",
                        aria_label="Close details",
                        on_click=DiscoveryState.clear_selection,
                        class_name="flex size-8 shrink-0 items-center justify-center rounded-full border border-[#f7d9a0] bg-[#fff7e8] text-[#b86e08] transition-colors hover:bg-[#ffedcc] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                    ),
                    class_name="absolute right-3 top-2 z-50 flex items-center",
                ),
                error_banner(DiscoveryState.error),
                success_banner(DiscoveryState.success),
                rx.cond(
                    ~DiscoveryState.has_helper_selection,
                    rx.el.div(
                        rx.cond(
                            DiscoveryState.is_list_view
                            & (
                                DiscoveryState.selected_poster_requests.length()
                                > 1
                            ),
                            rx.el.div(
                                rx.foreach(
                                    DiscoveryState.selected_poster_requests,
                                    group_request_choice,
                                ),
                                role="group",
                                aria_label="Choose another request from this poster",
                                class_name="flex w-full flex-col gap-1 pr-10",
                            ),
                            rx.fragment(),
                        ),
                        detail_body(),
                        class_name="flex flex-col gap-4 w-full",
                    ),
                    helper_detail(),
                ),
                class_name="relative flex flex-col gap-3 bg-white/90 px-3 pb-6 pt-3",
            ),
            role="dialog",
            aria_modal=False,
            aria_label="Member and request details",
            class_name="fixed inset-0 z-[50] h-dvh w-full overflow-y-auto overscroll-contain rounded-none bg-white bg-[url('/background_portrait_mobile.png')] bg-cover bg-center pb-[env(safe-area-inset-bottom)] text-[#111827]",
        ),
        rx.fragment(),
    )


def discover_panel() -> rx.Component:
    return rx.el.div(
        discovery_controls(),
        error_banner(DiscoveryState.error),
        success_banner(DiscoveryState.success),
        rx.cond(
            DiscoveryState.is_list_view,
            rx.el.div(
                rx.cond(DiscoveryState.show_jobs, job_list(), rx.fragment()),
                rx.cond(
                    DiscoveryState.show_events,
                    discovery_event_list(show_empty=DiscoveryState.events_only),
                    rx.fragment(),
                ),
                rx.cond(
                    DiscoveryState.show_helpers, helper_list(), rx.fragment()
                ),
                class_name="w-full pb-[calc(5rem+env(safe-area-inset-bottom))] sm:pb-8",
            ),
            map_panel(),
        ),
        event_detail_sheet(),
        on_mount=DiscoveryState.refresh_board,
        class_name="flex flex-col gap-4 w-full",
    )
