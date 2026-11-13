"""Premium "Metrics Information" section for the member Profile screen.

Compact ranked rows and statistic cards only — no charting library. Every figure
comes from `ProfileMetricsState`, which gates each query server-side.
"""

import reflex as rx

from app.components.disclosure import disclosure_arrow
from app.filter_categories import FilterCategory
from app.states.membership_state import MembershipState
from app.states.profile_state import ProfileState
from app.states.profile_metrics_state import (
    MAX_RADIUS_KM,
    MIN_RADIUS_KM,
    ProfileMetricsState,
    RankRow,
    RequestViewRow,
)

CARD = "w-full min-w-0 rounded-2xl border border-[#e5e5e5] bg-white px-4 py-3.5"
TILE = (
    "flex size-9 shrink-0 items-center justify-center rounded-xl "
    "bg-[#fff7e8] text-[#e08b12]"
)


def metrics_block_heading(
    icon: str, title: str, note: rx.Var[str] | str
) -> rx.Component:
    return rx.el.div(
        rx.el.span(rx.icon(icon, class_name="h-4 w-4"), class_name=TILE),
        rx.el.div(
            rx.el.h3(
                title,
                class_name="text-sm font-bold tracking-tight text-[#111827]",
            ),
            rx.el.p(
                note,
                class_name="mt-0.5 text-[11px] font-medium leading-relaxed text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1",
        ),
        class_name="flex items-start gap-3",
    )


def empty_note(message: str) -> rx.Component:
    return rx.el.p(
        message,
        class_name="mt-3 w-full rounded-2xl border border-dashed border-[#e5e5e5] bg-white px-4 py-4 text-[12px] font-semibold text-[#4b5563]",
    )


def scope_pill(label: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        label,
        class_name="w-fit shrink-0 rounded-full bg-[#e7f0ff] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-[#e08b12]",
    )


def radius_slider(
    control_id: str,
    label: str,
    value: rx.Var[int],
    scope: rx.Var[str],
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                label,
                html_for=control_id,
                class_name="text-[11px] font-bold uppercase tracking-[0.1em] text-[#4b5563]",
            ),
            scope_pill(scope),
            class_name="flex w-full flex-wrap items-center justify-between gap-2",
        ),
        rx.el.input(
            id=control_id,
            type="range",
            min=str(MIN_RADIUS_KM),
            max=str(MAX_RADIUS_KM),
            step="10",
            value=value.to_string(),
            aria_label=label,
            aria_valuemin=MIN_RADIUS_KM,
            aria_valuemax=MAX_RADIUS_KM,
            aria_valuenow=value,
            on_change=on_change.throttle(200),
            class_name="mt-2 h-6 w-full min-w-0 cursor-pointer accent-[#e08b12]",
        ),
        rx.el.div(
            rx.el.span(
                f"{MIN_RADIUS_KM} km",
                class_name="text-[10px] font-semibold text-[#4b5563]",
            ),
            rx.el.span(
                rx.cond(
                    value > 0,
                    f"{value} km radius",
                    "No radius limit (worldwide)",
                ),
                class_name="text-[11px] font-bold text-[#111827]",
            ),
            rx.el.span(
                f"{MAX_RADIUS_KM} km",
                class_name="text-[10px] font-semibold text-[#4b5563]",
            ),
            class_name="mt-1 flex w-full items-center justify-between gap-2",
        ),
        class_name=CARD.replace("border border-[#e5e5e5]", ""),
    )


def ranked_row(row: RankRow, index: rx.Var[int]) -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.span(
                index + 1,
                class_name="w-5 shrink-0 text-[11px] font-bold text-[#4b5563]",
            ),
            rx.el.span(
                row["label"],
                class_name="min-w-0 flex-1 truncate text-[13px] font-bold text-[#111827]",
            ),
            rx.el.span(
                row["count"],
                class_name="shrink-0 text-[13px] font-bold tabular-nums text-[#e08b12]",
            ),
            class_name="flex w-full items-center gap-2",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 rounded-full bg-[#e08b12]",
                style={"width": row["width"]},
            ),
            class_name="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[#e7f0ff]",
        ),
        class_name="w-full min-w-0 py-2",
    )


def ranked_list(rows: rx.Var[list[RankRow]]) -> rx.Component:
    return rx.el.ul(
        rx.foreach(rows, lambda row, index: ranked_row(row, index)),
        class_name="mt-2 flex w-full flex-col divide-y divide-[#e5e5e5]",
    )


def request_row(row: RequestViewRow) -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.p(
                row["title"],
                class_name="min-w-0 flex-1 truncate text-[13px] font-bold text-[#111827]",
            ),
            rx.el.span(
                row["status_label"],
                class_name="w-fit shrink-0 rounded-full bg-[#e7f0ff] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] text-[#e08b12]",
            ),
            class_name="flex w-full items-center gap-2",
        ),
        rx.el.div(
            rx.el.span(
                rx.icon("eye", class_name="h-3.5 w-3.5"),
                rx.el.span(row["views"], class_name="font-bold tabular-nums"),
                rx.el.span("views", class_name="font-semibold"),
                class_name="flex items-center gap-1.5 text-[12px] text-[#4b5563]",
            ),
            rx.el.span(
                rx.icon("users", class_name="h-3.5 w-3.5"),
                rx.el.span(
                    row["competitors"], class_name="font-bold tabular-nums"
                ),
                rx.el.span("similar open requests", class_name="font-semibold"),
                class_name="flex items-center gap-1.5 text-[12px] text-[#4b5563]",
            ),
            class_name="mt-1 flex w-full flex-wrap items-center gap-x-4 gap-y-1",
        ),
        class_name="w-full min-w-0 py-2.5",
    )


def stat_tile(
    icon: str, label: str, value: rx.Var[str], note: rx.Var[str]
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(rx.icon(icon, class_name="h-4 w-4"), class_name=TILE),
            rx.el.p(
                label,
                class_name="min-w-0 flex-1 text-[11px] font-bold uppercase tracking-[0.1em] text-[#4b5563]",
            ),
            class_name="flex items-center gap-2.5",
        ),
        rx.el.p(
            rx.cond(value != "", value, "No data yet"),
            class_name="mt-2 truncate text-xl font-bold tracking-tight text-[#111827]",
        ),
        rx.el.p(
            note,
            class_name="mt-1 text-[11px] font-medium leading-relaxed text-[#4b5563]",
        ),
        class_name=CARD,
    )


def category_choice(item: FilterCategory) -> rx.Component:
    return rx.el.option(item["label"], value=item["value"])


def views_block() -> rx.Component:
    return rx.el.div(
        metrics_block_heading(
            "eye",
            "Your requests: views and competition",
            "Real view counts on your recent help requests, plus how many other open requests share a category with them.",
        ),
        radius_slider(
            "metrics-competitor-radius",
            "Competitor radius",
            ProfileMetricsState.competitor_radius_km,
            ProfileMetricsState.competitor_scope_label,
            ProfileMetricsState.set_competitor_radius,
        ),
        rx.cond(
            ProfileMetricsState.request_rows.length() > 0,
            rx.el.ul(
                rx.foreach(ProfileMetricsState.request_rows, request_row),
                class_name="mt-3 flex w-full flex-col divide-y divide-[#e5e5e5] rounded-2xl border border-[#e5e5e5] bg-white px-4 py-1",
            ),
            empty_note(
                "You have no help requests yet, so there are no views to "
                "report. Post a request and its real view count will appear "
                "here."
            ),
        ),
        class_name="flex w-full min-w-0 flex-col gap-3",
    )


def searched_categories_block() -> rx.Component:
    return rx.el.div(
        metrics_block_heading(
            "search",
            "Popular searched categories",
            "The categories members actually filtered for, ranked by real search activity.",
        ),
        radius_slider(
            "metrics-search-radius",
            "Searched-category radius",
            ProfileMetricsState.search_radius_km,
            ProfileMetricsState.search_scope_label,
            ProfileMetricsState.set_search_radius,
        ),
        rx.cond(
            ProfileMetricsState.searched_categories.length() > 0,
            ranked_list(ProfileMetricsState.searched_categories),
            empty_note(
                "No category searches have been recorded in this area yet."
            ),
        ),
        class_name="flex w-full min-w-0 flex-col gap-3",
    )


def request_categories_block() -> rx.Component:
    return rx.el.div(
        metrics_block_heading(
            "list-ordered",
            "Popular help request categories",
            "The categories people are really asking for help with.",
        ),
        radius_slider(
            "metrics-request-radius",
            "Help-request-category radius",
            ProfileMetricsState.request_radius_km,
            ProfileMetricsState.request_scope_label,
            ProfileMetricsState.set_request_radius,
        ),
        rx.cond(
            ProfileMetricsState.request_categories.length() > 0,
            ranked_list(ProfileMetricsState.request_categories),
            empty_note("No help requests have been posted in this area yet."),
        ),
        class_name="flex w-full min-w-0 flex-col gap-3",
    )


def category_insights_block() -> rx.Component:
    return rx.el.div(
        metrics_block_heading(
            "sparkles",
            "Category insights",
            "Choose a request category to see the words that appeared in requests that found a helper, and who took part.",
        ),
        rx.el.div(
            rx.el.label(
                "Request category",
                html_for="metrics-category",
                class_name="text-[11px] font-bold uppercase tracking-[0.1em] text-[#4b5563]",
            ),
            rx.el.div(
                rx.el.select(
                    rx.foreach(
                        ProfileMetricsState.category_options, category_choice
                    ),
                    id="metrics-category",
                    value=ProfileMetricsState.selected_category,
                    on_change=ProfileMetricsState.set_selected_category,
                    aria_label="Request category for metrics",
                    class_name="h-11 w-full min-w-0 appearance-none rounded-xl border border-[#e5e5e5] bg-white px-3.5 pr-10 text-[13px] font-bold text-[#111827] focus:border-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#8fb4ff]",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#e08b12]",
                ),
                class_name="relative mt-2 w-full",
            ),
            class_name=CARD,
        ),
        rx.el.div(
            rx.el.h4(
                "Successful keywords",
                class_name="text-[13px] font-bold text-[#111827]",
            ),
            rx.el.p(
                "Words used most often in requests that reached matched or completed status, or that had an offer accepted.",
                class_name="mt-0.5 text-[11px] font-medium leading-relaxed text-[#4b5563]",
            ),
            rx.cond(
                ProfileMetricsState.keywords.length() > 0,
                ranked_list(ProfileMetricsState.keywords),
                empty_note(
                    "There are not enough successful requests in this "
                    "category yet to show reliable keywords."
                ),
            ),
            class_name="w-full min-w-0 rounded-2xl border border-[#e5e5e5] bg-white px-4 py-3.5",
        ),
        rx.el.div(
            stat_tile(
                "hand-helping",
                "Average helper age",
                ProfileMetricsState.helper_age_label,
                ProfileMetricsState.helper_age_note,
            ),
            stat_tile(
                "flag",
                "Average Helper nationality",
                ProfileMetricsState.helper_nationality,
                ProfileMetricsState.helper_nationality_note,
            ),
            stat_tile(
                "hand-heart",
                "Average helpee age",
                ProfileMetricsState.helpee_age_label,
                ProfileMetricsState.helpee_age_note,
            ),
            stat_tile(
                "globe",
                "Average Helpee nationality",
                ProfileMetricsState.helpee_nationality,
                ProfileMetricsState.helpee_nationality_note,
            ),
            class_name="grid w-full grid-cols-1 gap-3 sm:grid-cols-2",
        ),
        class_name="flex w-full min-w-0 flex-col gap-3",
    )


def metrics_loading() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-16 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-32 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        class_name="flex w-full flex-col gap-3",
    )


def metrics_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "info", class_name="mt-0.5 h-4 w-4 shrink-0 text-[#e08b12]"
            ),
            rx.el.p(
                ProfileMetricsState.location_note,
                class_name="text-[12px] font-semibold leading-relaxed text-[#e08b12]",
            ),
            class_name="flex w-full items-start gap-2 rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-4 py-3",
        ),
        rx.cond(
            ProfileMetricsState.error != "",
            rx.el.div(
                rx.icon(
                    "circle-alert",
                    class_name="mt-0.5 h-4 w-4 shrink-0 text-[#e08b12]",
                ),
                rx.el.p(
                    ProfileMetricsState.error,
                    class_name="text-[12px] font-semibold leading-relaxed text-[#e08b12]",
                ),
                role="alert",
                class_name="flex w-full items-start gap-2 rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-4 py-3",
            ),
            rx.fragment(),
        ),
        views_block(),
        searched_categories_block(),
        request_categories_block(),
        category_insights_block(),
        class_name="flex w-full min-w-0 flex-col gap-5",
    )


def metrics_disclosure_header() -> rx.Component:
    """Header geometry copied from the `My skills and knowledge` disclosure."""
    return rx.el.button(
        rx.el.span(
            rx.icon(
                "chart-no-axes-column", class_name="h-4 w-4 text-[#fba922]"
            ),
            class_name="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8] text-[#fba922]",
        ),
        rx.el.span(
            rx.el.span(
                "Metrics Information",
                class_name="block text-left text-lg font-bold tracking-tight text-[#111827]",
            ),
            rx.el.span(
                "These figures are here for one reason: to help your help "
                "requests get answered — the right category, the right words "
                "and the right moment.",
                class_name="mt-0.5 block text-left text-xs font-medium leading-relaxed text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1",
        ),
        disclosure_arrow(ProfileState.metrics_open),
        type="button",
        aria_expanded=rx.cond(ProfileState.metrics_open, "true", "false"),
        aria_controls="gah-my-metrics",
        on_click=ProfileState.toggle_metrics,
        class_name="gah-profile-disclosure flex w-full items-center gap-3 bg-white px-1 py-1 text-left transition-colors hover:opacity-90 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
    )


def metrics_section() -> rx.Component:
    """Premium-only metrics, as a collapsible white Profile disclosure."""
    return rx.cond(
        MembershipState.is_premium,
        rx.el.section(
            metrics_disclosure_header(),
            rx.cond(
                ProfileState.metrics_open,
                rx.el.div(
                    rx.cond(
                        ProfileMetricsState.is_loading
                        & ~ProfileMetricsState.loaded,
                        metrics_loading(),
                        metrics_body(),
                    ),
                    id="gah-my-metrics",
                    class_name="mt-4 flex w-full min-w-0 flex-col",
                ),
                rx.fragment(),
            ),
            on_mount=ProfileMetricsState.load_metrics,
            aria_label="Metrics information",
            class_name="gah-profile-row w-full min-w-0 bg-white p-5 sm:p-6",
        ),
        rx.fragment(),
    )
