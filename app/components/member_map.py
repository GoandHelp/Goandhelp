"""Signed-in home map: the exact guest map geometry with member behaviour.

Nothing here opens an auth wall. The search runs the real grouped
`WorldSearchState` results, the map uses the member discovery board, and the
Give/Get toggle plus the round violet filters button drive existing member
controls.
"""

import reflex as rx

from app.interface_i18n import ui

from app.components.discover_panel import (
    filter_drawer,
    filter_dismiss_layer,
    helper_list,
    job_list,
    sheet_mode_button,
)
from app.components.bookmark_tab import bookmark_tab
from app.components.feedback import avatar_with_tick
from app.components.help_post_panel import category_icon
from app.components.help_share import help_share
from app.components.event_cards import event_detail_sheet, discovery_event_list
from app.states.event_state import EventState
from app.components.header import (
    BRAND_MAP_POSITION,
    brand_mark,
)
from app.components.openfreemap import open_free_map
from app.components.map_loading import map_loading_logo
from app.components.map_utility_icon import map_utility_icon
from app.components.map_utilities import map_utility_sheets
from app.states.notification_state import NotificationState
from app.states.discovery_state import DiscoveryState
from app.states.profile_state import ProfileState
from app.states.world_search_state import WorldSearchState
from app.states.onboarding_state import OnboardingState


def member_brand_lockup() -> rx.Component:
    return rx.el.button(
        brand_mark(),
        type="button",
        title="Go and Help — back to the map",
        aria_label="Go and Help — back to the map",
        on_click=ProfileState.return_to_map,
        class_name=rx.cond(
            WorldSearchState.expanded,
            f"gah-brand-home pointer-events-auto {BRAND_MAP_POSITION} hidden items-center gap-3 rounded-full transition-opacity hover:opacity-90 md:flex",
            f"gah-brand-home pointer-events-auto {BRAND_MAP_POSITION} flex w-fit items-center gap-3 rounded-full transition-opacity hover:opacity-90",
        ),
    )


UTILITY_BUTTON = "gah-map-utility isolate pointer-events-auto relative flex size-[43px] shrink-0 items-center justify-center rounded-full border-0 shadow-none bg-transparent text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#fba922]"


def member_control_stack() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            map_utility_icon("bell"),
            rx.cond(
                NotificationState.total_unread > 0,
                rx.el.span(
                    aria_hidden="true",
                    class_name="absolute right-[7px] top-[6px] size-2 rounded-full bg-[#ef4444] ring-1 ring-white",
                ),
                rx.fragment(),
            ),
            type="button",
            title=ui("Notifications"),
            aria_label=rx.cond(
                NotificationState.total_unread > 0,
                ui("Notifications — unread activity"),
                ui("Notifications"),
            ),
            aria_expanded=NotificationState.panel_open,
            aria_controls="map-notifications-sheet",
            on_click=NotificationState.toggle_panel,
            class_name=UTILITY_BUTTON,
        ),
        rx.el.button(
            map_utility_icon("cog"),
            type="button",
            title=ui("Settings"),
            aria_label=ui("Settings"),
            aria_expanded=ProfileState.settings_open,
            aria_controls="map-settings-sheet",
            on_click=NotificationState.toggle_map_settings,
            class_name=UTILITY_BUTTON,
        ),
        aria_label="Map tools",
        class_name="pointer-events-none fixed top-3 right-3 sm:right-[22px] z-40 flex flex-row items-center gap-1",
    )


def member_filters_button() -> rx.Component:
    """The larger, helping-green anchor of the map tool rail."""
    return rx.el.button(
        rx.icon(
            "sliders-horizontal",
            class_name="h-[30px] w-[30px] text-[#fba922]",
        ),
        rx.cond(
            DiscoveryState.filters_active,
            rx.el.span(
                aria_hidden="true",
                class_name="absolute right-1 top-1 size-2.5 rounded-full bg-[#fba922] ring-2 ring-white",
            ),
            rx.fragment(),
        ),
        type="button",
        title=ui("Open Search filters"),
        aria_label=ui("Open Search filters"),
        id="gah-map-filter-open",
        custom_attrs={"data-tour-target": "filters"},
        on_click=NotificationState.toggle_map_filters,
        aria_expanded=DiscoveryState.filter_panel_open,
        class_name="pointer-events-auto fixed bottom-[calc(4.9rem+env(safe-area-inset-bottom))] right-[22px] z-30 flex size-[54px] shrink-0 items-center justify-center rounded-full border-0 bg-white text-[#fba922] transition-colors hover:bg-white hover:text-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
    )


def group_post_row(post: dict[str, str], **props) -> rx.Component:
    """One request in the poster sheet, with its own bookmark tab beside it."""
    return rx.el.div(
        group_post_button(post),
        help_share(
            post["id"], post["title"], "group", "absolute right-10 top-1.5 z-30"
        ),
        bookmark_tab(
            post["id"], post["title"], "absolute right-1.5 top-1.5 z-20"
        ),
        class_name="relative w-full",
        **props,
    )


def group_post_button(post: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            category_icon(post["category"], "h-4 w-4 text-[#e08b12]"),
            class_name="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#fff7e8]",
        ),
        rx.el.span(
            rx.el.span(
                post["title"],
                class_name="block truncate text-left text-[13px] font-bold text-[#172044]",
            ),
            rx.el.span(
                rx.el.span(
                    post["category_label"],
                    class_name="w-fit rounded-full bg-[#fff7e8] px-2 py-0.5 text-[9px] font-bold text-[#b86e08]",
                ),
                rx.el.span(
                    post["reward_label"],
                    class_name="w-fit rounded-full bg-[#fff7e8] px-2 py-0.5 text-[9px] font-bold text-[#b86e08]",
                ),
                class_name="mt-1 flex flex-wrap items-center gap-1.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon("chevron-right", class_name="h-4 w-4 shrink-0 text-[#e08b12]"),
        type="button",
        aria_label=f"Open the details for {post['title']}",
        on_click=lambda: DiscoveryState.select_post_from_group(post["id"]),
        class_name="flex w-full items-center gap-2.5 rounded-2xl border border-[#f7d9a0] bg-white px-3 py-2.5 pr-20 transition-colors hover:border-[#e08b12] hover:bg-[#fff7e8]",
    )


def member_group_sheet() -> rx.Component:
    """Every currently loaded request from one poster, behind one marker."""
    return rx.cond(
        DiscoveryState.group_open,
        rx.el.div(
            rx.el.div(
                avatar_with_tick(
                    DiscoveryState.group_poster_post["poster_image"],
                    DiscoveryState.group_poster_post["poster_verified"],
                    "size-10 rounded-full bg-[#fff7e8] object-cover",
                    "Request poster photo",
                    member_id=DiscoveryState.group_poster_post["poster_id"],
                ),
                rx.el.div(
                    rx.el.p(
                        DiscoveryState.group_poster_name,
                        class_name="truncate text-sm font-bold text-[#172044]",
                    ),
                    rx.el.p(
                        DiscoveryState.group_count_label,
                        class_name="text-[11px] font-semibold text-[#4e587c]",
                    ),
                    class_name="min-w-0 flex-1",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    type="button",
                    title="Close this poster's requests",
                    aria_label="Close this poster's requests",
                    on_click=DiscoveryState.close_poster_group,
                    class_name="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#e08b12] text-white transition-colors hover:bg-[#b86e08]",
                ),
                class_name="flex items-center justify-between gap-3",
            ),
            rx.el.div(
                rx.foreach(DiscoveryState.group_posts, group_post_row),
                class_name="mt-3 flex w-full flex-col gap-2",
            ),
            role="dialog",
            aria_label="Help requests from one poster",
            class_name="gah-screen-scroll pointer-events-auto absolute bottom-[calc(9rem+env(safe-area-inset-bottom))] left-3 right-3 z-40 mx-auto max-h-[50vh] max-w-md overflow-y-auto rounded-[1.6rem] border border-[#f7d9a0] bg-white/97 p-4 backdrop-blur-sm",
        ),
        rx.fragment(),
    )


def member_list_view() -> rx.Component:
    return rx.el.div(
        rx.cond(DiscoveryState.show_jobs, job_list(), rx.fragment()),
        rx.cond(
            DiscoveryState.show_events,
            discovery_event_list(show_empty=DiscoveryState.events_only),
            rx.fragment(),
        ),
        rx.cond(DiscoveryState.show_helpers, helper_list(), rx.fragment()),
        class_name="gah-screen-scroll absolute inset-0 z-20 flex flex-col gap-3 overflow-y-auto bg-white px-3 pb-[calc(5rem+env(safe-area-inset-bottom))] pt-[6.5rem] sm:px-6",
    )


def member_filter_sheet() -> rx.Component:
    """Show the compact floating member filter card above the map dock."""
    return rx.cond(
        DiscoveryState.filter_panel_open,
        filter_drawer(
            "gah-search-drawer pointer-events-auto fixed right-2 bottom-[calc(3.875rem+env(safe-area-inset-bottom))] z-30 flex w-[calc(100vw-1rem)] max-w-[23.75rem] max-h-[calc(100dvh-5rem-env(safe-area-inset-bottom))] min-h-0 flex-col overflow-y-auto overscroll-contain rounded-tl-2xl border-0 bg-[#f4f7ff] p-3 font-['Inter'] text-[#404040] backdrop-blur-sm",
            compact=True,
        ),
        rx.fragment(),
    )


def member_map_canvas() -> rx.Component:
    return rx.el.div(
        open_free_map(
            markers=(
                rx.cond(
                    DiscoveryState.show_jobs | DiscoveryState.show_helpers,
                    DiscoveryState.map_markers,
                    [],
                )
                + rx.cond(
                    DiscoveryState.show_jobs,
                    OnboardingState.celebration_map_markers,
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
            camera_duration=OnboardingState.celebration_camera_duration,
            on_marker_select=DiscoveryState.select_marker,
            on_interaction_start=DiscoveryState.handle_map_interaction,
            viewport_points=DiscoveryState.viewport_points,
            on_visible_points_change=DiscoveryState.update_visible_points,
            show_navigation_control=False,
            class_name="absolute inset-0 h-full w-full",
        ),
        rx.cond(
            DiscoveryState.is_list_view,
            member_list_view(),
            rx.fragment(),
        ),
        member_brand_lockup(),
        member_control_stack(),
        member_filters_button(),
        member_group_sheet(),
        rx.cond(
            DiscoveryState.is_loading & ~DiscoveryState.is_list_view,
            map_loading_logo(),
            rx.fragment(),
        ),
        class_name="relative h-[100dvh] min-h-[26rem] w-full overflow-hidden bg-[#fff7e8]",
    )


def tour_map_controls() -> rx.Component:
    """Expose direction actions; the filters tour uses the real map drawer."""
    return rx.cond(
        OnboardingState.tour_visible,
        rx.match(
            OnboardingState.tour_step,
            (
                5,
                rx.el.div(
                    sheet_mode_button(
                        "Go", "give", "Go — find people requesting help"
                    ),
                    sheet_mode_button(
                        "Get", "get", "Get — find people offering help"
                    ),
                    role="group",
                    aria_label="Go give, or Get help",
                    custom_attrs={"data-tour-target": "mode"},
                    class_name="gah-segment-group fixed left-4 top-24 z-40 flex w-fit items-center rounded-full border border-[#e08b12] bg-white p-1",
                ),
            ),
            rx.fragment(),
        ),
        rx.fragment(),
    )


def member_map_experience() -> rx.Component:
    return rx.el.section(
        member_map_canvas(),
        filter_dismiss_layer(),
        member_filter_sheet(),
        tour_map_controls(),
        map_utility_sheets(),
        event_detail_sheet(),
        on_mount=[
            DiscoveryState.refresh_board,
            NotificationState.load_notifications,
        ],
        class_name="relative w-full flex-1",
    )
