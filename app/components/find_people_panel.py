import reflex as rx
from app.avatars import member_avatar
from app.interface_i18n import ui, ui_template, ui_template_multi

from app.components.feedback import (  # noqa: I001
    avatar_with_tick,
    INPUT_CLASS,
    error_banner,
    field_label,
    success_banner,
)
from app.components.noncontact_panel import message_control
from app.components.report_dialog import report_button
from app.models import REPORT_TARGET_PROFILE
from app.states.contacts_state import ContactsState
from app.states.find_people_state import FindPeopleState


def tag_pill(label: rx.Var[str], icon: str, class_name: str) -> rx.Component:
    return rx.el.span(
        rx.icon(icon, class_name="h-3 w-3"),
        label,
        class_name=class_name,
    )


def language_chip(item: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        rx.icon("languages", class_name="h-3 w-3"),
        item.strip(),
        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
    )


def skill_chip(item: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        rx.icon("wrench", class_name="h-3 w-3"),
        item.strip(),
        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
    )


def search_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("search", class_name="h-4 w-4 text-[#e08b12]"),
                rx.el.h3(
                    ui("Find fellow travellers"),
                    class_name="text-sm font-bold text-[#111827]",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.span(
                rx.cond(
                    ContactsState.has_searched,
                    ui_template(
                        "{count} on the board",
                        "count",
                        ContactsState.search_results.length().to_string(),
                    ),
                    ui("Search by name or city"),
                ),
                class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-[#e08b12]",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                field_label("Name", "who are you looking for?"),
                rx.el.div(
                    rx.icon(
                        "user-round-search",
                        class_name="h-4 w-4 text-[#4b5563] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none",
                    ),
                    rx.el.input(
                        default_value=ContactsState.search_query,
                        placeholder="Maya",
                        on_change=ContactsState.set_search_query.debounce(500),
                        class_name=INPUT_CLASS + " pl-10",
                    ),
                    class_name="relative w-full",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                field_label("City", "where in the world?"),
                rx.el.div(
                    rx.icon(
                        "map-pin",
                        class_name="h-4 w-4 text-[#4b5563] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none",
                    ),
                    rx.el.input(
                        default_value=ContactsState.search_city,
                        placeholder="Porto",
                        on_change=ContactsState.set_search_city.debounce(500),
                        class_name=INPUT_CLASS + " pl-10",
                    ),
                    class_name="relative w-full",
                ),
                class_name="w-full",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
        ),
        rx.el.div(
            rx.el.p(
                ui(
                    "Neighbours are listed with the most kindness points first."
                ),
                class_name="text-xs font-medium text-[#4b5563]",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    ui("Clear search"),
                    type="button",
                    on_click=[
                        ContactsState.clear_search,
                        FindPeopleState.collapse,
                    ],
                    class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3 py-1.5 text-xs font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                    ui("Refresh board"),
                    type="button",
                    on_click=[
                        ContactsState.search_people,
                        ContactsState.load_contacts,
                    ],
                    class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f6c66f] bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#e08b12] transition-colors hover:bg-[#fff7e8]",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3",
        ),
        class_name="flex flex-col gap-4 w-full rounded-[2rem] border border-[#e5e5e5] bg-[#ffffff] p-5 sm:p-6",
    )


def localized_person_status(status: rx.Var[str]) -> rx.Var[str]:
    return rx.match(
        status,
        (
            "Request sent — waiting for a reply",
            ui("Request sent — waiting for a reply"),
        ),
        (
            "They'd like to connect with you",
            ui("They'd like to connect with you"),
        ),
        ("Already in your contacts", ui("Already in your contacts")),
        (
            "Request was declined — you can ask again",
            ui("Request was declined — you can ask again"),
        ),
        ("You were contacts before", ui("You were contacts before")),
        ("Not connected yet", ui("Not connected yet")),
        status,
    ).to(str)


def status_note(person: dict[str, str]) -> rx.Component:
    return rx.el.span(
        rx.icon("info", class_name="h-3 w-3"),
        localized_person_status(person["status_label"]),
        class_name=rx.cond(
            person["is_contact"],
            "w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-2.5 py-1 text-[11px] font-semibold text-[#111827]",
            "w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#4b5563]",
        ),
    )


def detail_row(icon: str, label: str, value: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex items-center justify-center size-8 rounded-lg bg-[#fff7e8] shrink-0",
        ),
        rx.el.div(
            rx.el.p(
                ui(label),
                class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
            ),
            rx.el.p(
                value,
                class_name="text-sm font-semibold text-[#111827] mt-0.5 leading-snug",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 min-w-0",
    )


def request_form(person: dict[str, str]) -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label(
                "Say hello", "optional — a line about why you're reaching out"
            ),
            rx.el.textarea(
                name="note",
                rows="3",
                placeholder=ui(
                    "Hi! I'm in town for a fortnight and would love to swap language practice for a bike repair lesson."
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="w-full",
        ),
        rx.el.button(
            rx.cond(
                ContactsState.is_requesting,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Sending request…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("user-round-plus", class_name="h-4 w-4"),
                    ui_template(
                        "Send contact request to {name}", "name", person["name"]
                    ),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=ContactsState.is_requesting,
            class_name="w-full sm:w-fit rounded-xl bg-[#e08b12] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
        ),
        on_submit=FindPeopleState.submit_request,
        reset_on_submit=True,
        class_name="flex flex-col gap-3 w-full rounded-2xl border border-dashed border-[#f6c66f] bg-[#fff7e8]/50 p-4",
    )


def person_details(person: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            detail_row(
                "map-pin",
                "Based in",
                rx.cond(
                    person["city"], person["city"], ui("City not shared yet")
                ),
            ),
            detail_row(
                "languages",
                "Languages",
                rx.cond(
                    person["languages"], person["languages"], ui("Not listed")
                ),
            ),
            detail_row(
                "wrench",
                "Skills",
                rx.cond(person["skills"], person["skills"], ui("Not listed")),
            ),
            detail_row(
                "clock",
                "Availability",
                rx.cond(
                    person["availability"],
                    person["availability"],
                    ui("Ask them directly"),
                ),
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-4",
        ),
        rx.cond(
            person["can_request"],
            request_form(person),
            rx.el.p(
                localized_person_status(person["status_label"]),
                class_name="text-sm font-medium text-[#4b5563]",
            ),
        ),
        rx.el.div(
            report_button(
                REPORT_TARGET_PROFILE,
                person["id"],
                person["name"],
                ui("Report profile"),
            ),
            class_name="w-full",
        ),
        class_name="flex flex-col gap-3 w-full mt-4",
    )


def person_card(person: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            avatar_with_tick(
                member_avatar(person["avatar_path"], person["avatar_seed"]),
                person["verified"],
                "size-14 rounded-full border-2 border-white bg-[#fff7e8] shrink-0",
                accessible_label=ui_template(
                    "Open the profile of {name}", "name", person["name"]
                ),
            ),
            rx.el.div(
                rx.el.p(
                    person["name"],
                    class_name="text-base font-bold text-[#111827] leading-tight",
                ),
                rx.cond(
                    person["headline"],
                    rx.el.p(
                        person["headline"],
                        class_name="text-sm font-medium text-[#4b5563] mt-1 leading-relaxed line-clamp-2",
                    ),
                    rx.el.p(
                        ui("A Go and Help neighbour with a story to swap."),
                        class_name="text-sm font-medium text-[#4b5563] mt-1 italic",
                    ),
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            rx.cond(
                person["city"],
                tag_pill(
                    person["city"],
                    "map-pin",
                    "w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                person["languages"],
                rx.foreach(person["languages"].split(","), language_chip),
                rx.fragment(),
            ),
            rx.cond(
                person["skills"],
                rx.foreach(person["skills"].split(","), skill_chip),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                rx.icon("sparkles", class_name="h-3 w-3"),
                ui_template(
                    rx.cond(
                        person["kindness"].to(int) == 1,
                        ui("{count} kindness point"),
                        ui("{count} kindness points"),
                    ),
                    "count",
                    person["kindness"].to(int).to_string(),
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
            ),
            rx.cond(
                person["reviews"] > 0,
                rx.el.span(
                    rx.icon("star", class_name="h-3 w-3"),
                    ui_template_multi(
                        rx.cond(
                            person["reviews"].to(int) == 1,
                            ui("{rating} · {count} review"),
                            ui("{rating} · {count} reviews"),
                        ),
                        {
                            "rating": f"{person['rating'].to(float):.1f}",
                            "count": person["reviews"].to(int).to_string(),
                        },
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
                ),
                rx.el.span(
                    rx.icon("heart-handshake", class_name="h-3 w-3"),
                    ui("New to Go and Help"),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
                ),
            ),
            rx.cond(
                person["joined"],
                rx.el.span(
                    rx.icon("calendar", class_name="h-3 w-3"),
                    ui_template("Joined {date}", "date", person["joined"]),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#4b5563]",
                ),
                rx.fragment(),
            ),
            status_note(person),
            class_name="flex flex-wrap items-center gap-1.5 mt-2",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    FindPeopleState.expanded_id == person["id"],
                    rx.icon("chevron-up", class_name="h-3.5 w-3.5"),
                    rx.icon("chevron-down", class_name="h-3.5 w-3.5"),
                ),
                rx.cond(
                    FindPeopleState.expanded_id == person["id"],
                    ui("Hide profile"),
                    ui("View profile details"),
                ),
                type="button",
                on_click=lambda: FindPeopleState.toggle_expanded(person["id"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f6c66f] bg-[#fff7e8] px-3.5 py-2 text-xs font-semibold text-[#e08b12] transition-colors hover:bg-[#fff7e8]",
            ),
            rx.cond(
                person["can_request"],
                rx.el.button(
                    rx.icon("user-round-plus", class_name="h-3.5 w-3.5"),
                    ui("Send contact request"),
                    type="button",
                    disabled=ContactsState.is_requesting,
                    on_click=lambda: FindPeopleState.quick_request(
                        person["id"]
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#e08b12] px-3.5 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
                ),
                rx.fragment(),
            ),
            rx.cond(
                person["can_respond"],
                rx.el.button(
                    rx.icon("check", class_name="h-3.5 w-3.5"),
                    ui("Accept their request"),
                    type="button",
                    disabled=ContactsState.is_responding,
                    on_click=lambda: ContactsState.accept_request(
                        person["link_id"]
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3.5 py-2 text-xs font-semibold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                ),
                rx.fragment(),
            ),
            rx.cond(
                person["is_contact"],
                rx.el.span(
                    rx.icon("circle-check-big", class_name="h-3.5 w-3.5"),
                    ui("Already contacts"),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3.5 py-2 text-xs font-semibold text-[#111827]",
                ),
                rx.fragment(),
            ),
            report_button(
                REPORT_TARGET_PROFILE,
                person["id"],
                person["name"],
                ui("Report"),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        rx.el.div(
            message_control(person["id"], person["name"]),
            class_name="mt-3 w-full",
        ),
        rx.cond(
            FindPeopleState.expanded_id == person["id"],
            person_details(person),
            rx.fragment(),
        ),
        class_name="w-full rounded-3xl border border-[#e5e5e5] bg-white p-5",
    )


def results_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-40 w-full rounded-3xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-40 w-full rounded-3xl bg-[#e5e5e5]"
        ),
        class_name="grid grid-cols-1 xl:grid-cols-2 gap-4 w-full",
    )


def start_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("compass", class_name="h-6 w-6 text-[#e08b12]"),
            class_name="flex items-center justify-center size-12 rounded-2xl bg-[#fff7e8] mb-3",
        ),
        rx.el.p(
            ui("Pin a name or a city to the noticeboard"),
            class_name="text-sm font-bold text-[#111827]",
        ),
        rx.el.p(
            ui(
                "Type someone's name, or the city you're heading to, and the travellers who can help will appear here."
            ),
            class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        class_name="flex flex-col items-center justify-center text-center w-full rounded-[2rem] border border-dashed border-[#f6c66f] bg-[#fff7e8]/40 px-6 py-12",
    )


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("user-round-search", class_name="h-6 w-6 text-[#e08b12]"),
            class_name="flex items-center justify-center size-12 rounded-2xl bg-[#fff7e8] mb-3",
        ),
        rx.el.p(
            ui("Nobody on the board matches that yet"),
            class_name="text-sm font-bold text-[#111827]",
        ),
        rx.el.p(
            ui(
                "Try a shorter name, or search by city only — new neighbours join every day."
            ),
            class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        class_name="flex flex-col items-center justify-center text-center w-full rounded-[2rem] border border-dashed border-[#d4d4d4] bg-[#ffffff] px-6 py-12",
    )


def results_section() -> rx.Component:
    return rx.cond(
        ContactsState.is_searching,
        results_skeleton(),
        rx.cond(
            ContactsState.has_searched,
            rx.cond(
                ContactsState.search_results.length() > 0,
                rx.el.div(
                    rx.foreach(
                        ContactsState.search_results,
                        person_card,
                    ),
                    class_name="grid grid-cols-1 xl:grid-cols-2 gap-4 w-full items-start",
                ),
                empty_state(),
            ),
            start_state(),
        ),
    )


def find_people_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("search", class_name="h-3.5 w-3.5"),
                    ui("Find people"),
                    class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12]",
                ),
                rx.el.h2(
                    ui("The traveller noticeboard."),
                    class_name="mt-3 text-2xl font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    ui(
                        "Search neighbours by name or city, read what they can offer, and send a contact request to start swapping help."
                    ),
                    class_name="mt-1 text-sm font-medium text-[#4b5563] leading-relaxed",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("users-round", class_name="h-3.5 w-3.5"),
                    rx.cond(
                        ContactsState.contacts.length() == 0,
                        ui("No contacts yet"),
                        rx.cond(
                            ContactsState.contacts.length() == 1,
                            ui_template(
                                "{count} contact",
                                "count",
                                ContactsState.contacts.length().to_string(),
                            ),
                            ui_template(
                                "{count} contacts",
                                "count",
                                ContactsState.contacts.length().to_string(),
                            ),
                        ),
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1.5 text-xs font-semibold text-[#111827]",
                ),
                rx.cond(
                    ContactsState.incoming_count > 0,
                    rx.el.span(
                        rx.icon("mail", class_name="h-3.5 w-3.5"),
                        ui_template(
                            "{count} waiting on you",
                            "count",
                            ContactsState.incoming_count.to_string(),
                        ),
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    ContactsState.outgoing_count > 0,
                    rx.el.span(
                        rx.icon("send", class_name="h-3.5 w-3.5"),
                        ui_template(
                            "{count} sent",
                            "count",
                            ContactsState.outgoing_count.to_string(),
                        ),
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="w-full flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-3xl border border-[#e5e5e5] bg-white p-6",
        ),
        error_banner(ContactsState.error),
        success_banner(ContactsState.success),
        search_panel(),
        results_section(),
        on_mount=ContactsState.load_contacts,
        class_name="flex flex-col gap-5 w-full",
    )
