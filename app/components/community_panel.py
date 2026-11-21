import reflex as rx

from app.avatars import animal_avatar
from app.states.auth_state import AuthState

from app.interface_i18n import ui, ui_template
from app.components.event_cards import events_section
from app.components.transient_surfaces import transient_surface_listeners
from app.components.reviews_section import community_reviews_section
from app.components.feedback import (
    INPUT_CLASS,
    SELECT_CLASS,
    avatar_with_tick,
    error_banner,
    field_label,
    select_wrapper,
    success_banner,
)
from app.components.noncontact_panel import message_control
from app.components.notification_badge import corner_activity_dot
from app.components.block_dialog import block_member_button
from app.components.report_dialog import report_button
from app.models import (
    REPORT_TARGET_COMMUNITY_COMMENT,
    REPORT_TARGET_COMMUNITY_TOPIC,
    REPORT_TARGET_PROFILE,
)
from app.states.community_state import (
    CommentItem,
    TopicItem,
    CommunityState,
)
from app.states.contacts_state import ContactsState, PersonResult
from app.states.membership_state import MembershipState
from app.states.notification_state import NotificationState


def person_avatar(path: rx.Var[str], seed: rx.Var[str]) -> rx.Var[str]:
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


# ---------------------------------------------------------------------------
# Section switcher
# ---------------------------------------------------------------------------


FOLDER_TAB_ACTIVE = (
    "gah-community-tab gah-orange-control relative flex flex-1 basis-0 min-w-0 lg:flex-none lg:basis-auto lg:w-36 "
    "flex-col items-center justify-center gap-1 rounded-full border border-[#fba922] "
    "bg-white text-black px-2 py-[5px] transition-colors "
    "outline-hidden focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
)
FOLDER_TAB_INACTIVE = (
    "gah-community-tab relative flex flex-1 basis-0 min-w-0 lg:flex-none lg:basis-auto lg:w-36 "
    "flex-col items-center justify-center gap-1 rounded-full border border-[#d4d4d4] "
    "bg-white text-[#404040] px-2 py-[5px] transition-colors shadow-[0_2px_8px_rgba(17,24,39,0.10)] hover:bg-white "
    "hover:border-[#fba922] outline-hidden focus:outline-hidden "
    "focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
)
FOLDER_TAB_ROW = "flex w-full min-w-0 flex-wrap items-center justify-start gap-2 lg:justify-end"
FOLDER_ROW_WRAP = "flex w-full items-center bg-white py-2"


def folder_tab(item: dict[str, str]) -> rx.Component:
    """Rounded section button with its existing unread indicator."""
    return rx.el.button(
        corner_activity_dot(
            rx.match(
                item["value"],
                ("events", NotificationState.events_unread > 0),
                ("reviews", NotificationState.reviews_unread > 0),
                ("community", NotificationState.forum_unread > 0),
                False,
            ),
            ui_template(
                "New activity in {section}", "section", ui(item["label"])
            ),
        ),
        rx.icon(item["icon"], class_name="h-5 w-5 shrink-0"),
        rx.el.span(
            ui(item["label"]),
            class_name="min-w-0 text-center text-xs sm:text-sm font-bold leading-snug [overflow-wrap:anywhere]",
        ),
        type="button",
        aria_current=rx.cond(
            CommunityState.section == item["value"], "page", "false"
        ),
        on_click=lambda: CommunityState.set_section(item["value"]),
        custom_attrs={"data-tour-target": f"community-{item['value']}"},
        class_name=rx.cond(
            CommunityState.section == item["value"],
            FOLDER_TAB_ACTIVE,
            FOLDER_TAB_INACTIVE,
        ),
    )


def community_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.foreach(CommunityState.sections, folder_tab),
                role="tablist",
                aria_label=ui("Community"),
                class_name=FOLDER_TAB_ROW,
            ),
            class_name=FOLDER_ROW_WRAP,
        ),
        class_name="gah-community-sticky-header sticky top-0 z-30 w-full shrink-0 bg-white pb-2 text-black before:content-[''] before:absolute before:inset-x-0 before:bottom-full before:h-5 before:pointer-events-none before:bg-inherit",
    )


# ---------------------------------------------------------------------------
# Section 1 — Search
# ---------------------------------------------------------------------------


def search_field(
    label: str,
    hint: str,
    icon: str,
    placeholder: str,
    value: rx.Var[str],
    handler,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(field_label(label, hint), class_name="pl-5"),
        rx.el.div(
            rx.icon(
                icon,
                class_name="h-4 w-4 text-[#404040] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            rx.el.input(
                default_value=value,
                placeholder=placeholder,
                on_change=handler.debounce(500),
                class_name=INPUT_CLASS + " pl-10",
            ),
            class_name="relative w-full",
        ),
        class_name="w-full",
    )


def country_option(name: rx.Var[str]) -> rx.Component:
    return rx.el.option(value=name)


def nationality_field() -> rx.Component:
    """Nationality with a real country suggestion list and inline validation."""
    return rx.el.div(
        rx.el.div(field_label("Nationality", "optional"), class_name="pl-5"),
        rx.el.div(
            rx.icon(
                "globe",
                class_name="h-4 w-4 text-[#404040] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            rx.el.input(
                default_value=ContactsState.search_country,
                placeholder="Portugal",
                list="gah-country-suggestions",
                auto_complete="off",
                aria_label=ui("Nationality"),
                aria_invalid=rx.cond(
                    ContactsState.country_error, "true", "false"
                ),
                on_change=ContactsState.set_search_country.debounce(400),
                class_name=INPUT_CLASS + " pl-10",
            ),
            rx.el.datalist(
                rx.foreach(ContactsState.country_options, country_option),
                id="gah-country-suggestions",
            ),
            class_name="relative w-full",
        ),
        rx.cond(
            ContactsState.country_error,
            rx.el.p(
                ContactsState.country_error,
                role="alert",
                class_name="mt-1.5 text-xs font-semibold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def search_filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            search_field(
                "Name",
                "optional",
                "user-round-search",
                "Maya",
                ContactsState.search_query,
                ContactsState.set_search_query,
            ),
            search_field(
                "Username",
                "optional",
                "at-sign",
                "maya.lisbon",
                ContactsState.search_username,
                ContactsState.set_search_username,
            ),
            nationality_field(),
            search_field(
                "City",
                "optional",
                "map-pin",
                "Porto",
                ContactsState.search_city,
                ContactsState.set_search_city,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
        ),
        rx.el.div(
            rx.el.p(
                "Search from one or multiple fields",
                class_name="w-full text-center text-xs font-semibold text-[#404040]",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    ui("Clear"),
                    type="button",
                    on_click=ContactsState.clear_search,
                    class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3 py-1.5 text-xs font-semibold text-[#404040] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                    "Search again",
                    type="button",
                    on_click=ContactsState.search_people,
                    class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#e08b12] transition-colors hover:bg-[#fff7e8]",
                ),
                class_name="flex flex-wrap items-center justify-center gap-2",
            ),
            class_name="flex flex-col items-center justify-center gap-3",
        ),
        class_name="gah-main-card w-full p-5 sm:p-6",
    )


def result_card(person: PersonResult) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            avatar_with_tick(
                person_avatar(person["avatar_path"], person["avatar_seed"]),
                person["verified"],
                "size-14 rounded-full bg-[#fff7e8] object-cover shrink-0 ring-2 ring-[#fff7e8]",
                "Profile photo",
                member_id=person["id"],
            ),
            rx.el.div(
                rx.el.p(
                    person["name"],
                    class_name="text-base font-bold text-[#000000] leading-tight",
                ),
                rx.el.div(
                    rx.cond(
                        person["handle"],
                        rx.el.span(
                            person["handle"],
                            class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                        ),
                        rx.el.span(
                            "no handle yet",
                            class_name="w-fit rounded-full border border-dashed border-[#d4d4d4] px-2.5 py-0.5 text-[11px] font-semibold text-[#404040]",
                        ),
                    ),
                    rx.cond(
                        person["nationality"],
                        rx.el.span(
                            rx.icon("globe", class_name="h-3 w-3"),
                            person["nationality"],
                            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#e08b12]",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        person["city"],
                        rx.el.span(
                            rx.icon("map-pin", class_name="h-3 w-3"),
                            person["city"],
                            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#e08b12]",
                        ),
                        rx.fragment(),
                    ),
                    class_name="mt-1.5 flex flex-wrap items-center gap-1.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.cond(
            person["headline"],
            rx.el.p(
                person["headline"],
                class_name="mt-3 text-sm font-medium leading-relaxed text-[#404040] line-clamp-2",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.cond(
                person["can_request"],
                rx.el.button(
                    rx.icon("user-round-plus", class_name="h-3.5 w-3.5"),
                    ui("Add contact"),
                    type="button",
                    disabled=ContactsState.is_requesting,
                    on_click=lambda: ContactsState.send_request(
                        person["id"], ""
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#e08b12] px-3.5 py-2 text-xs font-bold text-white transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                ),
                rx.fragment(),
            ),
            rx.cond(
                person["can_respond"],
                rx.el.button(
                    rx.icon("check", class_name="h-3.5 w-3.5"),
                    "Accept their request",
                    type="button",
                    disabled=ContactsState.is_responding,
                    on_click=lambda: ContactsState.accept_request(
                        person["link_id"]
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3.5 py-2 text-xs font-bold text-black transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                ),
                rx.fragment(),
            ),
            rx.cond(
                person["is_contact"],
                rx.el.span(
                    rx.icon("circle-check-big", class_name="h-3.5 w-3.5"),
                    "Already contacts",
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3.5 py-2 text-xs font-semibold text-black",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                person["status_label"],
                class_name="text-[11px] font-semibold text-[#404040]",
            ),
            report_button(
                REPORT_TARGET_PROFILE,
                person["id"],
                person["name"],
                "Report profile",
            ),
            block_member_button(person["id"], person["name"]),
            class_name="mt-4 flex flex-wrap items-center gap-2",
        ),
        message_control(person["id"], person["name"]),
        class_name="w-full rounded-3xl border border-[#d4d4d4] bg-white p-5",
    )


def search_results() -> rx.Component:
    return rx.cond(
        ContactsState.is_searching,
        rx.el.div(
            rx.el.div(
                class_name="animate-pulse h-40 w-full rounded-3xl bg-[#e5e5e5]"
            ),
            rx.el.div(
                class_name="animate-pulse h-40 w-full rounded-3xl bg-[#e5e5e5]"
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-4 w-full",
        ),
        rx.cond(
            ContactsState.has_searched,
            rx.cond(
                ContactsState.search_results.length() > 0,
                rx.el.div(
                    rx.foreach(ContactsState.search_results, result_card),
                    class_name="grid grid-cols-1 xl:grid-cols-2 gap-4 w-full items-start",
                ),
                rx.el.div(
                    rx.icon(
                        "user-round-search",
                        class_name="h-6 w-6 text-[#e08b12] mb-2",
                    ),
                    rx.el.p(
                        "Nobody matches that yet",
                        class_name="text-sm font-bold text-[#000000]",
                    ),
                    rx.el.p(
                        "Try a shorter name, just the @username, or search by country only.",
                        class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#404040]",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full rounded-[2rem] border border-dashed border-[#d4d4d4] bg-[#ffffff] px-6 py-12",
                ),
            ),
            rx.el.div(
                rx.icon("compass", class_name="h-6 w-6 text-[#e08b12] mb-2"),
                rx.el.p(
                    "Start with any single detail",
                    class_name="text-sm font-bold text-[#000000]",
                ),
                rx.el.p(
                    "A first name, a handle, a country or a city — that's all you need "
                    "to find someone on the board.",
                    class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#404040]",
                ),
                class_name="flex flex-col items-center justify-center text-center w-full rounded-[2rem] border border-dashed border-[#d4d4d4] bg-[#fff7e8]/40 px-6 py-12",
            ),
        ),
    )


def search_section() -> rx.Component:
    return rx.el.div(
        error_banner(ContactsState.error),
        success_banner(ContactsState.success),
        search_filters(),
        search_results(),
        class_name="flex flex-col gap-5 w-full",
    )


# ---------------------------------------------------------------------------
# Section 3 — Community discussions
# ---------------------------------------------------------------------------


def subject_option(item: dict[str, str]) -> rx.Component:
    return rx.el.option(ui(item["label"]), value=item["value"])


# Idle subjects are cobalt on white; a selected subject is white on
# helping-green. No green focus or click outline is ever left behind.
SUBJECT_CARD_ON = "gah-topic-filter flex h-full w-full min-h-[2.875rem] items-center justify-center gap-2 rounded-xl border-0 shadow-[0_2px_12px_rgba(17,24,39,0.10)] bg-[#fba922] px-2 py-1.5 text-sm font-bold text-black transition-colors outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
SUBJECT_CARD_OFF = "gah-topic-filter flex h-full w-full min-h-[2.875rem] items-center justify-center gap-2 rounded-xl border-0 shadow-[0_2px_12px_rgba(17,24,39,0.10)] bg-white px-2 py-1.5 text-sm font-bold text-[#404040] transition-colors hover:bg-[#fff7e8] outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
SUBJECT_ICON_ON = "gah-topic-filter flex h-11 min-w-11 w-full items-center justify-center rounded-xl border-0 shadow-[0_2px_12px_rgba(17,24,39,0.10)] bg-[#fba922] text-black transition-colors outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
SUBJECT_ICON_OFF = "gah-topic-filter flex h-11 min-w-11 w-full items-center justify-center rounded-xl border-0 shadow-[0_2px_12px_rgba(17,24,39,0.10)] bg-white text-[#e08b12] transition-colors hover:bg-[#fff7e8] outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"

# Even, justified columns so no ragged gap is left at the right edge.
SUBJECT_CARD_GRID = (
    "hidden min-[680px]:grid w-full grid-cols-4 lg:grid-cols-6 "
    "items-stretch gap-2"
)
SUBJECT_ICON_GRID = "grid w-full grid-cols-5 sm:grid-cols-6 items-stretch gap-2"


def subject_selected(value: rx.Var[str]) -> rx.Var[bool]:
    return CommunityState.selected_subject_filters.contains(value)


def subject_filter_button(item: dict[str, str]) -> rx.Component:
    """A desktop subject card that toggles independently of the others."""
    return rx.el.button(
        rx.icon(
            item["icon"],
            stroke_width=1.5,
            class_name="h-6 w-6 shrink-0 text-black",
        ),
        rx.el.span(ui(item["label"]), class_name="min-w-0 break-words"),
        type="button",
        aria_pressed=rx.cond(subject_selected(item["value"]), "true", "false"),
        on_click=lambda: CommunityState.toggle_subject_filter(item["value"]),
        class_name=rx.cond(
            subject_selected(item["value"]),
            SUBJECT_CARD_ON,
            SUBJECT_CARD_OFF,
        ),
    )


def subject_icon_button(item: dict[str, str]) -> rx.Component:
    """Compact icon-only subject toggle with a minimum 44px tap target."""
    return rx.el.button(
        rx.icon(
            item["icon"],
            stroke_width=1.5,
            class_name="h-6 w-6 shrink-0 text-black",
        ),
        type="button",
        title=ui(item["label"]),
        aria_label=ui(item["label"]),
        aria_pressed=rx.cond(subject_selected(item["value"]), "true", "false"),
        on_click=lambda: CommunityState.toggle_subject_filter(item["value"]),
        class_name=rx.cond(
            subject_selected(item["value"]),
            SUBJECT_ICON_ON,
            SUBJECT_ICON_OFF,
        ),
    )


def subject_checklist_row(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.icon(
            rx.cond(
                CommunityState.selected_subject_filters.contains(item["value"]),
                "square-check",
                "square",
            ),
            class_name="size-4 text-black",
        ),
        rx.icon(item["icon"], class_name="size-4 text-black"),
        rx.el.span(ui(item["label"])),
        type="button",
        role="checkbox",
        aria_checked=CommunityState.selected_subject_filters.contains(
            item["value"]
        ),
        on_click=lambda: CommunityState.toggle_subject_filter(item["value"]),
        class_name="flex min-h-11 w-full items-center gap-2 rounded-lg bg-white px-3 text-left text-sm text-black hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def subject_dropdown() -> rx.Component:
    return rx.el.div(
        rx.cond(
            CommunityState.subject_list_open,
            rx.el.button(
                ui("Close topic filters"),
                id="gah-forum-dropdown-close",
                type="button",
                tab_index=-1,
                on_click=CommunityState.close_subject_list,
                class_name="hidden",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.el.span(
                CommunityState.forum_display.get("filter_label", ""),
                class_name="min-w-0 flex-1 text-left",
            ),
            rx.icon("chevron-down", class_name="size-4 text-black"),
            type="button",
            aria_expanded=CommunityState.subject_list_open,
            aria_label=ui("Filter topics"),
            on_click=CommunityState.toggle_subject_list,
            class_name="flex w-full items-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-4 py-3 text-sm text-black focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.cond(
            CommunityState.subject_list_open,
            rx.el.div(
                rx.el.button(
                    rx.icon(
                        rx.cond(
                            CommunityState.has_subject_filters,
                            "square",
                            "square-check",
                        ),
                        class_name="size-4 text-black",
                    ),
                    rx.icon("layout-grid", class_name="size-4 text-black"),
                    ui("All topics"),
                    type="button",
                    role="checkbox",
                    aria_checked=~CommunityState.has_subject_filters,
                    on_click=CommunityState.clear_subject_filter,
                    class_name="flex min-h-11 w-full items-center gap-2 rounded-lg bg-white px-3 text-sm text-black hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                rx.foreach(
                    CommunityState.subject_options, subject_checklist_row
                ),
                role="group",
                aria_label=ui("Topics"),
                class_name="mt-2 max-h-72 overflow-y-auto rounded-xl border border-[#d4d4d4] bg-white p-1",
            ),
            rx.fragment(),
        ),
        id="gah-forum-dropdown",
        class_name="w-full",
    )


def subject_icon_row() -> rx.Component:
    """Multi-toggle icon grid, evenly distributed across the full width."""
    return rx.el.div(
        rx.el.button(
            rx.icon(
                "layout-grid",
                stroke_width=1.5,
                class_name="h-6 w-6 shrink-0 text-black",
            ),
            type="button",
            title=ui("All topics"),
            aria_label=ui("All topics"),
            aria_pressed=rx.cond(
                CommunityState.has_subject_filters, "false", "true"
            ),
            on_click=CommunityState.clear_subject_filter,
            class_name=rx.cond(
                CommunityState.has_subject_filters,
                SUBJECT_ICON_OFF,
                SUBJECT_ICON_ON,
            ),
        ),
        rx.foreach(CommunityState.subject_options, subject_icon_button),
        role="group",
        aria_label=ui("Pinned subjects"),
        class_name=SUBJECT_ICON_GRID,
    )


def subject_mobile_controls() -> rx.Component:
    return rx.el.div(
        subject_icon_row(),
        class_name="flex flex-col gap-2 w-full min-[680px]:hidden",
    )


def subject_folder_grid() -> rx.Component:
    """Pinned subject categories used to navigate and filter the feed."""
    return rx.el.div(
        rx.el.div(subject_dropdown(), class_name="mb-3 w-full sm:max-w-sm"),
        rx.el.div(
            rx.el.button(
                rx.icon(
                    "layout-grid",
                    stroke_width=1.5,
                    class_name="h-6 w-6 shrink-0 text-black",
                ),
                rx.el.span(ui("All topics")),
                type="button",
                aria_pressed=rx.cond(
                    CommunityState.has_subject_filters, "false", "true"
                ),
                on_click=CommunityState.clear_subject_filter,
                class_name=rx.cond(
                    CommunityState.has_subject_filters,
                    SUBJECT_CARD_OFF,
                    SUBJECT_CARD_ON,
                ),
            ),
            rx.foreach(CommunityState.subject_options, subject_filter_button),
            role="group",
            aria_label=ui("Subjects — choose any number"),
            class_name=SUBJECT_CARD_GRID,
        ),
        subject_mobile_controls(),
        rx.el.p(
            CommunityState.forum_display.get("filter_summary", ""),
            role="status",
            class_name="mt-2 text-sm font-semibold leading-snug text-[#404040]",
        ),
        class_name="w-full",
    )


def topic_composer() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            field_label(
                "Discussion subject",
                "required",
            ),
            select_wrapper(
                rx.el.select(
                    rx.el.option(
                        ui("Choose a subject"), value="", disabled=True
                    ),
                    rx.foreach(CommunityState.subject_options, subject_option),
                    value=CommunityState.subject_draft,
                    on_change=CommunityState.set_subject_draft,
                    class_name=SELECT_CLASS,
                )
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label(
                "Title", CommunityState.forum_display.get("title_hint", "")
            ),
            rx.el.input(
                default_value=CommunityState.title_draft,
                key=CommunityState.draft_version,
                placeholder=ui("Where do you find long-term work exchanges?"),
                on_change=CommunityState.set_title_draft.debounce(300),
                class_name=INPUT_CLASS,
            ),
            rx.el.p(
                CommunityState.forum_display.get("title_limit", ""),
                class_name=rx.cond(
                    CommunityState.title_over_limit,
                    "mt-1 text-xs font-bold text-[#e08b12]",
                    "mt-1 text-xs font-medium text-[#404040]",
                ),
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label(
                "Your post", CommunityState.forum_display.get("body_hint", "")
            ),
            rx.el.textarea(
                default_value=CommunityState.body_draft,
                key=CommunityState.draft_version,
                rows="6",
                placeholder=ui(
                    "Tell the board what happened, what you learned, or what you need."
                ),
                on_change=CommunityState.set_body_draft.debounce(300),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            rx.el.p(
                CommunityState.forum_display.get("body_limit", ""),
                class_name=rx.cond(
                    CommunityState.body_over_limit,
                    "mt-1 text-xs font-bold text-[#e08b12]",
                    "mt-1 text-xs font-medium text-[#404040]",
                ),
            ),
            class_name="w-full",
        ),
        rx.el.button(
            rx.cond(
                CommunityState.is_posting,
                rx.el.span(
                    rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                    ui("Posting…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("pin", class_name="h-4 w-4"),
                    ui("Post the discussion"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="button",
            disabled=CommunityState.is_posting | ~CommunityState.can_post_topic,
            on_click=CommunityState.create_topic,
            class_name="w-full sm:w-fit rounded-xl bg-[#e08b12] px-6 py-3 text-sm font-bold text-white transition-colors hover:bg-[#e08b12] disabled:opacity-60",
        ),
        class_name="gah-main-card flex flex-col gap-4 w-full rounded-2xl bg-[#ffffff] p-4 sm:p-5",
    )


def topic_card(topic: TopicItem) -> rx.Component:
    return rx.el.button(
        corner_activity_dot(
            NotificationState.unread_topic_ids.contains(topic["id"]),
            ui("Unread replies on this discussion"),
        ),
        rx.el.div(
            avatar_with_tick(
                person_avatar(
                    topic["author_avatar"], topic["author_avatar_seed"]
                ),
                topic["author_verified"],
                "size-10 rounded-full bg-[#fff7e8] object-cover shrink-0",
                ui("Author photo"),
                member_id=topic["author_id"],
                accessible_label=ui("Open member profile"),
                verification_label=ui("Email verified"),
            ),
            rx.el.div(
                rx.el.p(
                    topic["title"],
                    class_name="text-base font-bold text-[#000000] text-left leading-snug line-clamp-2",
                ),
                rx.el.div(
                    rx.el.span(
                        topic["author_name"],
                        class_name="text-xs font-semibold text-[#404040]",
                    ),
                    rx.cond(
                        topic["author_handle"],
                        rx.el.span(
                            topic["author_handle"],
                            class_name="text-xs font-bold text-[#e08b12]",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        topic["created"],
                        class_name="text-xs font-medium text-[#404040]",
                    ),
                    class_name="mt-1 flex flex-wrap items-center gap-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("message-circle", class_name="h-3 w-3"),
                topic["comment_count"],
                aria_label=rx.cond(
                    topic["comment_count"] == 1,
                    ui_template(
                        "{count} reply",
                        "count",
                        topic["comment_count"].to_string(),
                    ),
                    ui_template(
                        "{count} replies",
                        "count",
                        topic["comment_count"].to_string(),
                    ),
                ),
                class_name="w-fit shrink-0 flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.span(
            rx.icon(topic["subject_icon"], class_name="h-3 w-3 text-black"),
            ui(topic["subject"]),
            class_name="mt-3 w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-bold text-[#e08b12]",
        ),
        rx.el.p(
            topic["preview"],
            class_name="mt-3 text-sm font-medium text-[#404040] text-left leading-relaxed line-clamp-3 whitespace-pre-line",
        ),
        rx.el.span(
            rx.icon("arrow-right", class_name="h-3 w-3"),
            ui("Read more"),
            class_name="mt-3 w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold text-[#e08b12]",
        ),
        type="button",
        on_click=lambda: CommunityState.open_topic(topic["id"]),
        class_name=rx.cond(
            CommunityState.selected_topic["id"] == topic["id"],
            "relative flex flex-col w-full rounded-none border-0 bg-[#fba922] p-5 text-left transition-colors",
            "relative flex flex-col w-full rounded-none border-0 bg-white p-5 text-left transition-colors",
        ),
    )


def comment_card(comment: CommentItem) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar_with_tick(
                person_avatar(
                    comment["author_avatar"], comment["author_avatar_seed"]
                ),
                comment["author_verified"],
                "size-9 rounded-full bg-[#fff7e8] object-cover shrink-0",
                ui("Author photo"),
                member_id=comment["author_id"],
                accessible_label=ui("Open member profile"),
                verification_label=ui("Email verified"),
            ),
            rx.el.div(
                rx.el.p(
                    comment["author_name"],
                    class_name="text-sm font-bold text-[#000000] leading-tight",
                ),
                rx.el.div(
                    rx.cond(
                        comment["author_handle"],
                        rx.el.span(
                            comment["author_handle"],
                            class_name="text-[11px] font-bold text-[#e08b12]",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        comment["created"],
                        class_name="text-[11px] font-medium text-[#404040]",
                    ),
                    class_name="mt-0.5 flex flex-wrap items-center gap-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                comment["mine"],
                rx.el.span(
                    ui("You"),
                    class_name="w-fit shrink-0 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                ),
                rx.fragment(),
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.p(
            comment["body"],
            class_name="mt-2 text-sm font-medium leading-relaxed text-[#404040] whitespace-pre-line",
        ),
        rx.cond(
            comment["mine"],
            rx.fragment(),
            rx.el.div(
                report_button(
                    REPORT_TARGET_COMMUNITY_COMMENT,
                    comment["id"],
                    comment["body"],
                    ui("Report comment"),
                    accessible_label=ui("Report unsafe content privately"),
                    accessible_title=ui(
                        "Report privately to the Go and Help safety team"
                    ),
                ),
                rx.cond(
                    comment["author_id"] > 0,
                    block_member_button(
                        comment["author_id"],
                        comment["author_name"],
                        ui("Block member"),
                        accessible_label=ui("Block this member privately"),
                        accessible_title=ui(
                            "Block privately — they are never told"
                        ),
                    ),
                    rx.fragment(),
                ),
                class_name="mt-3 flex flex-wrap items-center gap-2",
            ),
        ),
        class_name=rx.cond(
            comment["mine"],
            "gah-inset-row w-full bg-[#ffffff] p-4",
            "gah-inset-row w-full bg-white p-4",
        ),
    )


def comment_composer() -> rx.Component:
    return rx.el.div(
        field_label(
            "Add a comment",
            CommunityState.forum_display.get("comment_hint", ""),
        ),
        rx.cond(
            CommunityState.forum_premium,
            rx.fragment(),
            rx.el.p(
                CommunityState.forum_display.get("comment_allowance", ""),
                class_name="text-xs font-medium text-[#404040]",
            ),
        ),
        rx.el.textarea(
            default_value=CommunityState.comment_draft,
            key=CommunityState.comment_version,
            rows="3",
            placeholder=ui("Share what worked for you…"),
            on_change=CommunityState.set_comment_draft.debounce(300),
            class_name=INPUT_CLASS + " resize-y leading-relaxed",
        ),
        rx.el.div(
            rx.el.p(
                CommunityState.forum_display.get("comment_limit", ""),
                class_name=rx.cond(
                    CommunityState.comment_over_limit,
                    "text-xs font-bold text-[#e08b12]",
                    "text-xs font-medium text-[#404040]",
                ),
            ),
            rx.el.button(
                rx.cond(
                    CommunityState.is_commenting,
                    rx.el.span(
                        rx.icon(
                            "loader-circle", class_name="h-4 w-4 animate-spin"
                        ),
                        ui("Posting…"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                    rx.el.span(
                        rx.icon("send", class_name="h-4 w-4"),
                        ui("Post comment"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                ),
                type="button",
                disabled=CommunityState.is_commenting
                | ~CommunityState.can_post_comment,
                on_click=CommunityState.add_comment,
                class_name="w-full sm:w-fit rounded-xl bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            class_name="mt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 w-full",
        ),
        class_name="w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-[#ffffff] p-4",
    )


def locked_comment_prompt() -> rx.Component:
    """Compact violet outlined affordance instead of a comment composer."""
    return rx.el.button(
        rx.el.span(
            rx.icon("lock", class_name="h-3.5 w-3.5"),
            ui("Go premium to comment more"),
            class_name="flex items-center gap-1.5 text-xs font-bold text-black",
        ),
        rx.el.span(
            ui(
                "Free members can post 10 comments total per UTC calendar month across all discussions."
            ),
            class_name="mt-1 text-xs font-medium text-[#404040] text-left",
        ),
        rx.el.span(
            rx.icon("sparkles", class_name="h-3 w-3"),
            ui("Continue with unlimited replies"),
            class_name="mt-2 w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1 text-[11px] font-bold text-black",
        ),
        type="button",
        aria_label=ui("Unlock forum replies with premium membership"),
        on_click=CommunityState.open_comment_paywall,
        class_name="flex flex-col w-full rounded-2xl border border-[#fba922] bg-white px-4 py-3 text-left transition-colors hover:bg-[#fff7e8]",
    )


def topic_detail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    CommunityState.selected_topic["title"],
                    class_name="min-w-0 flex-1 break-words text-xl sm:text-2xl font-bold text-[#000000] leading-tight",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    type="button",
                    aria_label=f"{ui('Close')} — {ui('Forum')}",
                    title=f"{ui('Close')} — {ui('Forum')}",
                    on_click=CommunityState.close_topic,
                    class_name="flex size-11 shrink-0 items-center justify-center rounded-full border border-[#d4d4d4] bg-white text-[#404040] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]/40",
                ),
                class_name="flex w-full min-w-0 items-start justify-between gap-3",
            ),
            rx.el.div(
                rx.el.span(
                    CommunityState.selected_topic["author_name"],
                    class_name="text-xs font-semibold text-[#404040]",
                ),
                rx.cond(
                    CommunityState.selected_topic["author_handle"],
                    rx.el.span(
                        CommunityState.selected_topic["author_handle"],
                        class_name="text-xs font-bold text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                rx.el.span(
                    CommunityState.selected_topic["created"],
                    class_name="text-xs font-medium text-[#404040]",
                ),
                rx.el.div(
                    rx.icon("folder-open", class_name="h-3 w-3 shrink-0"),
                    ui(CommunityState.selected_topic["subject"]),
                    class_name="inline-flex min-h-7 min-w-0 items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold text-[#e08b12] [overflow-wrap:anywhere]",
                ),
                rx.el.div(
                    CommunityState.forum_display.get("replies", ""),
                    class_name="inline-flex min-h-7 min-w-0 items-center rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold text-[#e08b12] [overflow-wrap:anywhere]",
                ),
                class_name="mt-3 flex w-full flex-wrap items-center gap-2",
            ),
            class_name="flex w-full min-w-0 flex-col",
        ),
        rx.el.p(
            CommunityState.selected_topic["body"],
            class_name="mt-4 text-sm font-medium leading-relaxed text-[#404040] whitespace-pre-line",
        ),
        rx.el.div(class_name="my-4 h-px w-full bg-[#d4d4d4]"),
        rx.cond(
            CommunityState.is_loading_topic,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-20 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-20 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="flex flex-col gap-3 w-full",
            ),
            rx.cond(
                CommunityState.comments.length() > 0,
                rx.el.div(
                    rx.foreach(CommunityState.comments, comment_card),
                    class_name="flex flex-col gap-3 w-full",
                ),
                rx.el.div(
                    rx.icon(
                        "message-circle",
                        class_name="h-5 w-5 text-[#e08b12] mb-2",
                    ),
                    rx.el.p(
                        ui("No replies yet"),
                        class_name="text-sm font-bold text-[#000000]",
                    ),
                    rx.el.p(
                        ui(
                            "Be the first to answer — a short, kind reply goes a long way."
                        ),
                        class_name="mt-1 text-sm font-medium text-[#404040]",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-white/60 px-6 py-8",
                ),
            ),
        ),
        rx.el.div(
            rx.cond(
                CommunityState.comment_allowance_available,
                comment_composer(),
                locked_comment_prompt(),
            ),
            class_name="mt-4 w-full",
        ),
        rx.cond(
            CommunityState.selected_topic["mine"],
            rx.fragment(),
            rx.el.div(
                report_button(
                    REPORT_TARGET_COMMUNITY_TOPIC,
                    CommunityState.selected_topic["id"],
                    CommunityState.selected_topic["title"],
                    ui("Report discussion"),
                    accessible_label=ui("Report unsafe content privately"),
                    accessible_title=ui(
                        "Report privately to the Go and Help safety team"
                    ),
                ),
                block_member_button(
                    CommunityState.selected_topic["author_id"],
                    CommunityState.selected_topic["author_name"],
                    ui("Block member"),
                    accessible_label=ui("Block this member privately"),
                    accessible_title=ui(
                        "Block privately — they are never told"
                    ),
                ),
                class_name="mt-5 flex w-full flex-wrap items-center gap-2 border-t border-[#e5e5e5] pt-4",
            ),
        ),
        class_name="gah-main-card w-full rounded-2xl p-5 sm:p-6",
    )


def topic_feed() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    ui("Filter forum topics"),
                    class_name="w-full text-center text-xl sm:text-2xl font-bold tracking-tight text-black leading-tight",
                ),
                class_name="relative flex w-full items-center px-10",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon(
                        "refresh-cw", class_name="h-3.5 w-3.5 text-[#404040]"
                    ),
                    type="button",
                    aria_label=ui("Refresh discussions"),
                    on_click=CommunityState.load_topics,
                    class_name="flex items-center justify-center size-8 rounded-full border border-[#d4d4d4] bg-white text-[#404040] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                ),
                class_name="absolute right-0 top-1/2 -translate-y-1/2 flex items-center gap-2",
            ),
            class_name="relative flex min-h-8 items-center w-full",
        ),
        rx.el.div(subject_folder_grid(), class_name="mt-4 w-full"),
        rx.cond(
            CommunityState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-40 w-full rounded-3xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-40 w-full rounded-3xl bg-[#e5e5e5]"
                ),
                class_name="gah-edge-stack flex flex-col gap-0 w-full mt-4",
            ),
            rx.cond(
                CommunityState.topics.length() > 0,
                rx.el.div(
                    rx.foreach(CommunityState.topics, topic_card),
                    class_name="gah-edge-stack flex flex-col gap-0 w-full mt-4",
                ),
                rx.el.div(
                    rx.icon("pin", class_name="h-6 w-6 text-[#fba922] mb-2"),
                    rx.el.p(
                        ui("No discussions pinned yet"),
                        class_name="text-sm font-bold text-[#000000]",
                    ),
                    rx.el.p(
                        ui(
                            "Try All topics, or start a discussion. Questions, wisdoms and stories belong here."
                        ),
                        class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#404040]",
                    ),
                    class_name="gah-edge-stack mt-4 flex flex-col gap-0 items-center justify-center text-center w-full bg-white px-6 py-12",
                ),
            ),
        ),
        class_name="w-full bg-transparent",
    )


def community_section() -> rx.Component:
    return rx.el.div(
        error_banner(
            rx.match(
                CommunityState.error,
                (
                    "Titles can be at most 200 characters.",
                    CommunityState.forum_display.get("title_error", ""),
                ),
                (
                    "That post is longer than 5000 words — please shorten it.",
                    CommunityState.forum_display.get("body_error", ""),
                ),
                (
                    "Comments are limited to 1000 words.",
                    CommunityState.forum_display.get("comment_error", ""),
                ),
                ui(CommunityState.error),
            )
        ),
        success_banner(ui(CommunityState.success)),
        rx.el.div(
            rx.el.div(
                rx.cond(
                    CommunityState.topic_allowance_available,
                    rx.el.button(
                        rx.cond(
                            CommunityState.composer_open,
                            rx.icon(
                                "chevron-up",
                                class_name="h-3.5 w-3.5 text-[#fba922]",
                            ),
                            rx.icon(
                                "plus", class_name="h-3.5 w-3.5 text-[#fba922]"
                            ),
                        ),
                        rx.cond(
                            CommunityState.composer_open,
                            ui("Hide"),
                            ui("New topic"),
                        ),
                        type="button",
                        on_click=CommunityState.toggle_composer,
                        disabled=~AuthState.is_signed_in,
                        aria_expanded=CommunityState.composer_open,
                        class_name="gah-orange-control w-fit max-w-full flex items-center gap-1.5 rounded-full border border-[#fba922] bg-white px-3 py-1.5 text-xs font-bold text-black transition-colors hover:bg-[#fff7e8] disabled:opacity-60",
                    ),
                    rx.el.button(
                        rx.icon(
                            "megaphone", class_name="h-3.5 w-3.5 text-[#fba922]"
                        ),
                        rx.el.span(
                            ui("New topic"),
                            class_name="min-w-0 text-black [overflow-wrap:anywhere]",
                        ),
                        rx.el.span(
                            ui("Monthly limit"),
                            rx.icon(
                                "lock", class_name="h-3 w-3 shrink-0 text-black"
                            ),
                            class_name="w-fit flex items-center gap-1 rounded-full bg-[#fba922] px-2 py-0.5 text-[10px] font-bold text-black",
                        ),
                        type="button",
                        title=ui(
                            "Free members can start 1 topic per UTC calendar month."
                        ),
                        aria_label=ui("Go premium to start more topics"),
                        on_click=CommunityState.toggle_composer,
                        class_name="gah-primary-outline w-fit max-w-full flex flex-wrap justify-center items-center gap-1.5 rounded-full border border-[#fba922] bg-white px-3 py-1.5 text-xs font-bold text-black transition-colors hover:bg-[#fff7e8]",
                    ),
                ),
                rx.cond(
                    AuthState.is_signed_in
                    & CommunityState.composer_open
                    & ~CommunityState.forum_premium
                    & CommunityState.topic_allowance_available,
                    rx.el.p(
                        CommunityState.forum_display.get("topic_allowance", ""),
                        class_name="min-w-0 text-center text-sm font-medium text-[#404040]",
                    ),
                    rx.fragment(),
                ),
                class_name="flex w-full flex-col items-center justify-center gap-2 text-center",
            ),
            rx.cond(
                AuthState.is_signed_in
                & CommunityState.composer_open
                & CommunityState.topic_allowance_available,
                rx.el.div(topic_composer(), class_name="mt-4 w-full"),
                rx.fragment(),
            ),
            class_name="mt-2 w-full bg-transparent px-5 pb-3 sm:px-6",
        ),
        rx.cond(
            CommunityState.has_topic_open,
            topic_detail(),
            rx.fragment(),
        ),
        topic_feed(),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        on_mount=[
            CommunityState.load_topics,
            MembershipState.load_membership,
        ],
        class_name="flex flex-col gap-2 w-full",
    )


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------


def community_panel() -> rx.Component:
    return rx.el.div(
        transient_surface_listeners(),
        community_header(),
        rx.match(
            CommunityState.section,
            ("events", events_section()),
            ("reviews", community_reviews_section()),
            ("community", community_section()),
            community_section(),
        ),
        class_name="flex flex-col gap-3 w-full",
    )
