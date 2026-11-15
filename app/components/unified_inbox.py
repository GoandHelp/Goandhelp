"""The unified Inbox conversation feed: one search, one list, three types."""

import reflex as rx
from app.avatars import animal_avatar

from app.interface_i18n import ui, ui_template
from app.components.feedback import avatar_with_tick
from app.states.contacts_state import ContactsState, ContactItem
from app.components.contacts_panel import avatar_src
from app.components.feedback import error_banner
from app.components.notification_badge import corner_activity_dot
from app.states.unified_inbox_state import UnifiedInboxState, UnifiedItem

TYPE_BADGE_BASE = (
    "w-fit shrink-0 flex items-center gap-1.5 rounded-full border-2 "
    "px-2.5 py-0.5 text-[11px] font-bold"
)

# The three bounded type colours are the primary scanning cue.
CONTACT_BADGE = (
    f"{TYPE_BADGE_BASE} border-[#fba922] bg-[#fff7e8] text-[#111827]"
)
HELPER_BADGE = (
    "shrink-0 inline-flex items-center gap-1.5 text-xs font-bold text-black"
)
HELPEE_BADGE = (
    "w-fit shrink-0 flex items-center gap-1.5 rounded-full border "
    "px-2.5 py-0.5 text-[11px] font-bold border-[#e08b12] bg-white text-[#e08b12]"
)

CARD_BASE = (
    "relative flex flex-col w-full rounded-2xl border-l-4 px-4 py-3 text-left "
    "transition-colors outline-hidden focus:outline-hidden "
    "focus-visible:ring-2 focus-visible:ring-[#e08b12]/50"
)

FILTER_BASE = (
    "gah-orange-control w-fit shrink-0 whitespace-nowrap flex items-center gap-1.5 rounded-full border px-3 py-1.5 "
    "text-xs font-bold transition-colors outline-hidden "
    "focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
)


def _avatar(path: rx.Var[str], seed: rx.Var[str]) -> rx.Var[str]:
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


def type_badge(item: UnifiedItem) -> rx.Component:
    """The conversation type, always visible before expansion."""
    return rx.el.span(
        rx.match(
            item["conv_type"],
            ("helper", rx.icon("hand", class_name="gah-helper-hand size-6")),
            ("helpee", rx.icon("hand-helping", class_name="size-6")),
            rx.icon("users-round", class_name="size-6"),
        ),
        title=ui(item["type_label"]),
        aria_label=ui(item["type_label"]),
        class_name="shrink-0 text-[#e08b12]",
    )


def remove_from_inbox(key: str | rx.Var[str]) -> rx.Component:
    return rx.el.button(
        rx.icon("trash-2", class_name="size-4 shrink-0 text-[#e08b12]"),
        rx.el.span(
            ui("Remove from Inbox"), class_name="text-center leading-tight"
        ),
        type="button",
        aria_label=ui("Remove from Inbox"),
        title=ui(
            "Remove only from your Inbox. Messages stay safe and new messages bring it back."
        ),
        on_click=UnifiedInboxState.dismiss_thread(key),
        class_name="gah-conversation-toggle flex min-h-11 w-fit shrink-0 flex-col items-center justify-center gap-1 rounded-xl border-0 bg-transparent px-2 py-2 text-xs font-medium text-[#e08b12] shadow-none hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#fba922] sm:flex-row sm:gap-1.5",
    )


def conversation_card(
    item: UnifiedItem, pane: rx.Component = rx.fragment()
) -> rx.Component:
    return rx.el.article(
        rx.el.button(
            corner_activity_dot(
                item["unread_count"] > 0,
                ui("Unread messages in this conversation"),
            ),
            avatar_with_tick(
                _avatar(item["other_avatar"], item["other_avatar_seed"]),
                item["other_verified"],
                "size-16 shrink-0 rounded-full bg-[#fff7e8] object-cover",
                ui("Member profile photo"),
            ),
            rx.el.div(
                rx.el.p(
                    item["other_name"],
                    rx.cond(
                        item["job_title"],
                        f" — {item['job_title']}",
                        rx.cond(
                            item["preview"].startswith("Subject: "),
                            f" — {item['preview'].split('\n')[0].split('Subject: ')[1]}",
                            "",
                        ),
                    ),
                    class_name="truncate whitespace-nowrap text-lg font-semibold text-[#111827]",
                ),
                rx.el.p(
                    rx.cond(
                        item["preview"].startswith("Subject: ")
                        & (item["preview"].split("\n\n").length() > 1),
                        item["preview"].split("\n\n")[-1].strip(),
                        rx.cond(
                            item["preview"],
                            item["preview"],
                            ui("No messages yet"),
                        ),
                    ),
                    class_name="mt-0.5 truncate whitespace-nowrap text-sm font-medium leading-relaxed text-[#111827]",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                item["last_photo"],
                rx.el.img(
                    src=rx.get_upload_url(item["last_photo"]),
                    alt=ui("Latest message photo"),
                    loading="lazy",
                    class_name="size-12 shrink-0 rounded-xl bg-[#fff7e8] object-cover",
                ),
                rx.fragment(),
            ),
            type_badge(item),
            type="button",
            aria_label=rx.match(
                item["conv_type"],
                (
                    "contact",
                    ui_template(
                        "Open the Contact conversation with {name}",
                        "name",
                        item["other_name"],
                    ),
                ),
                (
                    "helper",
                    ui_template(
                        "Open the Helper conversation with {name}",
                        "name",
                        item["other_name"],
                    ),
                ),
                (
                    "helpee",
                    ui_template(
                        "Open the Helpee conversation with {name}",
                        "name",
                        item["other_name"],
                    ),
                ),
                ui_template(
                    "Open the Contact conversation with {name}",
                    "name",
                    item["other_name"],
                ),
            ),
            aria_current=rx.cond(
                UnifiedInboxState.selected_key == item["key"], "true", "false"
            ),
            on_click=UnifiedInboxState.open_item(item["kind"], item["ref_id"]),
            class_name="gah-conversation-toggle relative flex flex-1 min-w-0 items-center gap-3 border-0 bg-transparent py-3 text-left shadow-none hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        remove_from_inbox(item["key"]),
        key=item["key"],
        class_name="flex w-full min-w-0 items-center gap-1 border-0 bg-transparent text-[#111827] shadow-none sm:gap-3",
    )


def filter_chip(option: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.cond(
            UnifiedInboxState.unread_by_type.get(option["value"], 0) > 0,
            rx.el.span(
                class_name="absolute right-2 top-2 size-2 rounded-full bg-[#e08b12]",
                aria_label=rx.match(
                    option["value"],
                    ("helper", ui("Unread Helpers messages")),
                    ("helpee", ui("Unread Helpees messages")),
                    ui("Unread Contacts messages"),
                ),
                role="img",
            ),
            rx.fragment(),
        ),
        rx.match(
            option["value"],
            (
                "helper",
                rx.icon(
                    "hand", class_name="gah-helper-hand size-6 text-[#e08b12]"
                ),
            ),
            rx.icon(option["icon"], class_name="size-6 text-[#e08b12]"),
        ),
        rx.el.span(
            ui(option["label"]), class_name="text-xs sm:text-sm text-black"
        ),
        title=ui(option["label"]),
        aria_label=ui(option["label"]),
        type="button",
        aria_pressed=rx.cond(
            UnifiedInboxState.type_filter == option["value"], "true", "false"
        ),
        on_click=lambda: UnifiedInboxState.set_type_filter(option["value"]),
        class_name=rx.cond(
            UnifiedInboxState.type_filter == option["value"],
            "gah-conversation-toggle relative flex min-w-0 flex-1 flex-col items-center gap-1 rounded-xl bg-[#fff7e8] px-0 py-3 text-black focus-visible:ring-2 focus-visible:ring-[#fba922]",
            "gah-conversation-toggle relative flex min-w-0 flex-1 flex-col items-center gap-1 rounded-xl bg-white px-0 py-3 text-black hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
    )


def inbox_toolbar() -> rx.Component:
    """Search, an accessible funnel, and New on one compact row."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#fba922]",
                ),
                rx.el.input(
                    id="gah-inbox-search",
                    placeholder=ui("Search: Contacts, Messages..."),
                    default_value=UnifiedInboxState.search,
                    aria_label=ui("Search: Contacts, Messages..."),
                    on_change=UnifiedInboxState.set_search.debounce(400),
                    class_name=(
                        "w-full rounded-2xl border border-[#f6c66f] bg-white "
                        "pl-10 pr-4 py-3 text-sm font-medium text-[#111827] "
                        "placeholder:text-[#4b5563] outline-hidden "
                        "focus:border-[#e08b12] focus:ring-2 "
                        "focus:ring-[#e08b12]/30"
                    ),
                ),
                class_name="relative min-w-0 flex-1 rounded-2xl bg-white shadow-[0_1px_6px_rgba(17,24,39,0.10)]!",
            ),
            rx.el.button(
                rx.icon("funnel", class_name="size-5"),
                type="button",
                title=ui("Filters"),
                aria_label=ui("Filters"),
                aria_expanded=UnifiedInboxState.filters_open,
                aria_controls="gah-inbox-filters",
                on_click=UnifiedInboxState.toggle_filters,
                class_name=rx.cond(
                    UnifiedInboxState.filters_open,
                    "gah-conversation-toggle flex size-12 shrink-0 items-center justify-center rounded-2xl border border-[#fba922] bg-[#fff7e8] text-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                    "gah-conversation-toggle flex size-12 shrink-0 items-center justify-center rounded-2xl border border-[#f6c66f] bg-white text-[#e08b12] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
            ),
            rx.el.button(
                rx.icon(
                    "mail-plus", class_name="size-4 shrink-0 text-[#e08b12]"
                ),
                ui("New"),
                type="button",
                aria_label=ui("New message"),
                on_click=UnifiedInboxState.open_compose(0),
                class_name="gah-conversation-toggle inline-flex min-h-12 shrink-0 items-center justify-center gap-1.5 rounded-2xl border border-[#f6c66f] bg-white px-2 sm:px-3 text-sm font-semibold text-[#111827] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="flex w-full min-w-0 items-center gap-2",
        ),
        rx.el.div(
            rx.foreach(UnifiedInboxState.type_filters, filter_chip),
            rx.el.button(
                rx.el.span(
                    rx.icon("x", class_name="size-3.5"),
                    aria_hidden=True,
                    class_name="flex size-5 shrink-0 items-center justify-center rounded-full bg-[#fff0d9] text-[#b86e08]",
                ),
                ui("clear"),
                type="button",
                aria_label=ui("Clear filters"),
                on_click=[
                    UnifiedInboxState.clear_filters,
                    rx.call_script(
                        "document.getElementById('gah-inbox-search').value = ''"
                    ),
                ],
                class_name="gah-conversation-toggle ml-auto inline-flex min-h-11 shrink-0 items-center gap-1 bg-transparent px-0.5 text-xs font-semibold text-[#e08b12] hover:underline focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            id="gah-inbox-filters",
            role="group",
            aria_label=ui("Filter conversations by type"),
            aria_hidden=~UnifiedInboxState.filters_open,
            class_name=rx.cond(
                UnifiedInboxState.filters_open,
                "mt-2 flex w-full min-w-0 items-center gap-1 sm:gap-2",
                "hidden",
            ),
        ),
        class_name="w-full bg-transparent",
    )


def envelope_star() -> rx.Component:
    return rx.el.span(
        rx.icon("mail", class_name="size-7"),
        rx.icon(
            "star",
            class_name="absolute -right-1.5 -top-1.5 size-3.5 fill-[#fba922] text-[#fba922]",
        ),
        aria_hidden=True,
        class_name="relative inline-flex shrink-0 text-[#e08b12]",
    )


def back_to_inbox() -> rx.Component:
    return rx.el.button(
        rx.icon("arrow-left", class_name="size-4"),
        ui("Back"),
        type="button",
        aria_label=ui("Back to Inbox"),
        on_click=UnifiedInboxState.back_to_inbox,
        class_name="flex min-h-10 w-fit items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-2 text-sm font-semibold text-[#b86e08] hover:bg-[#ffedcc] focus-visible:ring-2 focus-visible:ring-[#e08b12] sm:px-4",
    )


def inbox_subview_header(title: str, icon: rx.Component) -> rx.Component:
    return rx.el.div(
        back_to_inbox(),
        rx.el.h3(
            icon,
            rx.el.span(
                ui(title), class_name="min-w-0 text-center leading-tight"
            ),
            class_name="flex min-w-0 items-center justify-center gap-1.5 text-center text-base font-semibold text-[#111827] sm:gap-2 sm:text-lg",
        ),
        rx.el.span(aria_hidden=True, class_name="block"),
        class_name="grid w-full grid-cols-[minmax(0,1fr)_minmax(0,2fr)_minmax(0,1fr)] items-center gap-1 py-1 sm:gap-2",
    )


def contact_identity(contact: ContactItem) -> rx.Component:
    return rx.fragment(
        avatar_with_tick(
            avatar_src(contact["other_avatar"], contact["other_avatar_seed"]),
            contact["other_verified"],
            "size-11 shrink-0 rounded-full bg-[#fff7e8] object-cover",
        ),
        rx.el.span(
            rx.el.span(
                contact["other_name"],
                class_name="block truncate text-sm font-semibold text-black",
            ),
            rx.el.span(
                contact["other_handle"],
                class_name="block truncate text-xs text-[#e08b12]",
            ),
            class_name="min-w-0 flex-1 text-left",
        ),
        rx.el.span(
            contact["country_flag"],
            title=contact["nationality"],
            aria_label=contact["nationality"],
            class_name="shrink-0 text-xl",
        ),
    )


def address_book_row(contact: ContactItem) -> rx.Component:
    return rx.el.li(
        rx.el.button(
            contact_identity(contact),
            type="button",
            aria_label=ui_template(
                "Open {name}'s passport", "name", contact["other_name"]
            ),
            on_click=UnifiedInboxState.open_contact_passport(
                contact["link_id"]
            ),
            class_name="gah-conversation-toggle flex flex-1 min-w-0 items-center gap-3 bg-white py-3 text-black",
        ),
        rx.el.button(
            envelope_star(),
            rx.el.span(ui("New"), class_name="text-xs text-black"),
            type="button",
            aria_label=ui_template(
                "New message to {name}", "name", contact["other_name"]
            ),
            on_click=UnifiedInboxState.open_compose(contact["link_id"]),
            class_name="gah-conversation-toggle flex shrink-0 flex-col items-center gap-1 rounded-xl bg-white px-3 py-2 hover:bg-[#fff7e8]",
        ),
        key=contact["link_id"],
        class_name="flex w-full items-center gap-3 bg-white px-3",
    )


def inbox_contacts_view() -> rx.Component:
    return rx.el.section(
        inbox_subview_header(
            "My contacts",
            rx.icon(
                "users-round",
                class_name="size-5 shrink-0 text-[#e08b12] sm:size-6",
            ),
        ),
        error_banner(ContactsState.error),
        rx.cond(
            ContactsState.is_loading,
            rx.el.p(
                ui("Loading contacts…"),
                role="status",
                class_name="py-8 text-center text-gray-600",
            ),
            rx.cond(
                ContactsState.has_message_contacts,
                rx.el.ul(
                    rx.foreach(ContactsState.contacts, address_book_row),
                    class_name="gah-edge-stack flex w-full flex-col gap-0 overflow-hidden rounded-2xl bg-white",
                ),
                rx.el.p(
                    ui(
                        "No confirmed contacts yet. Connect with someone in Community to start writing."
                    ),
                    role="status",
                    class_name="py-8 text-center text-gray-600",
                ),
            ),
        ),
        class_name="flex w-full flex-col gap-3",
    )


def list_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-28 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-28 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-28 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.icon("mails", class_name="h-6 w-6 text-[#fba922] mb-2"),
        rx.el.p(
            rx.cond(
                UnifiedInboxState.has_search,
                ui("Nothing matches that search"),
                ui("No conversations yet"),
            ),
            class_name="text-sm font-bold text-[#111827]",
        ),
        rx.el.p(
            rx.cond(
                UnifiedInboxState.has_search,
                ui("Try a different name, message or request title."),
                ui(
                    "Contacts, direct messages and job conversations all land here."
                ),
            ),
            class_name="mt-1 max-w-md text-xs font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.cond(
            UnifiedInboxState.has_search,
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                ui("Clear search"),
                type="button",
                on_click=[
                    UnifiedInboxState.clear_search,
                    rx.call_script(
                        "document.getElementById('gah-inbox-search').value = ''"
                    ),
                ],
                class_name="mt-3 w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-4 py-2 text-xs font-bold text-[#e08b12] transition-colors hover:bg-[#fff7e8]",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#fba922] bg-white px-5 py-12",
    )


def unified_conversation_list(
    pane: rx.Component = rx.fragment(),
) -> rx.Component:
    return rx.el.section(
        rx.cond(
            UnifiedInboxState.error,
            rx.el.p(
                UnifiedInboxState.error,
                role="alert",
                class_name="mb-3 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            UnifiedInboxState.is_loading,
            list_skeleton(),
            rx.cond(
                UnifiedInboxState.error,
                rx.fragment(),
                rx.cond(
                    UnifiedInboxState.items.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            UnifiedInboxState.items,
                            conversation_card,
                        ),
                        class_name="flex w-full flex-col gap-3 bg-transparent",
                    ),
                    empty_state(),
                ),
            ),
        ),
        aria_label=ui("All conversations"),
        class_name="w-full min-w-0 bg-transparent",
    )
