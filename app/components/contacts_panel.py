import reflex as rx
from app.avatars import animal_avatar
from app.interface_i18n import ui, ui_template
from app.states.message_attachment_state import MessageAttachmentState
from app.states.unified_inbox_state import UnifiedInboxState
from app.components.message_attachments import message_attachments

from app.components.chat_controls import (
    COMPOSER_CLASS,
    MESSAGE_INPUT_CLASS,
    SEND_CLASS,
    HISTORY_CLASS,
    correspondence_bubble,
)

from app.components.feedback import (
    avatar_with_tick,
    error_banner,
    success_banner,
)
from app.components.noncontact_panel import noncontact_conversation_view
from app.components.notification_badge import activity_dot
from app.components.block_dialog import block_member_button
from app.components.chat_safety import chat_safety
from app.models import (
    REPORT_TARGET_CONTACT_MESSAGE,
    REPORT_TARGET_NONCONTACT_MESSAGE,
)
from app.states.message_deletion_state import MessageDeletionState
from app.states.community_state import CommunityState
from app.states.contacts_state import (
    ContactItem,
    ContactsState,
    ContactMessageItem,
)
from app.states.noncontact_state import NonContactMessagingState


def avatar_src(path: rx.Var[str], seed: rx.Var[str]) -> rx.Var[str]:
    """Real profile photo when there is one, otherwise a warm fallback."""
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


def contacts_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                ui_template(
                    "{count} Contacts",
                    "count",
                    ContactsState.contacts.length().to_string(),
                ),
                class_name="text-2xl font-bold tracking-tight text-[#111827]",
            ),
            rx.el.p(
                ui("Connections to a world of kind people"),
                class_name="mt-1 text-sm font-medium text-[#4b5563] leading-relaxed",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("search", class_name="h-3.5 w-3.5"),
            ui("Find people"),
            type="button",
            on_click=lambda: CommunityState.set_section("search"),
            class_name="w-fit shrink-0 flex items-center gap-2 rounded-full bg-[#fff7e8] px-4 py-2 text-xs font-semibold text-[#e08b12] transition-colors hover:bg-[#f7d9a0] focus:outline-hidden focus:ring-2 focus:ring-[#e08b12]",
        ),
        class_name="w-full flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-3xl bg-white p-6",
    )


def city_chip(city: rx.Var[str]) -> rx.Component:
    return rx.cond(
        city,
        rx.el.span(
            rx.icon("map-pin", class_name="h-3 w-3"),
            city,
            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
        ),
        rx.fragment(),
    )


def intro_note(note: rx.Var[str]) -> rx.Component:
    return rx.cond(
        note,
        rx.el.p(
            f"“{note}”",
            class_name="mt-3 rounded-2xl border border-[#e08b12] bg-[#fff7e8]/50 px-3 py-2 text-sm font-medium italic leading-relaxed text-[#4b5563]",
        ),
        rx.fragment(),
    )


def incoming_card(contact: ContactItem) -> rx.Component:
    """An incoming contact request, with accept and decline kept intact."""
    return rx.el.article(
        rx.el.div(
            avatar_with_tick(
                avatar_src(
                    contact["other_avatar"], contact["other_avatar_seed"]
                ),
                contact["other_verified"],
                "size-12 rounded-full border-2 border-white bg-[#fff7e8] object-cover",
            ),
            rx.el.div(
                rx.el.p(
                    contact["other_name"],
                    class_name="text-sm font-bold text-[#111827] leading-tight",
                ),
                rx.cond(
                    contact["other_handle"],
                    rx.el.span(
                        contact["other_handle"],
                        class_name="mt-0.5 w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("mail", class_name="h-3 w-3"),
                ui("Wants to connect"),
                class_name="w-fit shrink-0 flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#e08b12]",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            city_chip(contact["other_city"]),
            rx.cond(
                contact["requested_at"],
                rx.el.span(
                    rx.icon("calendar", class_name="h-3 w-3"),
                    ui_template(
                        "Asked {date}", "date", contact["requested_at"]
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#4b5563]",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-3",
        ),
        intro_note(contact["intro_note"]),
        rx.el.div(
            rx.el.button(
                rx.icon("check", class_name="h-3.5 w-3.5"),
                ui("Confirm contact"),
                type="button",
                disabled=ContactsState.is_responding,
                on_click=lambda: ContactsState.accept_request(
                    contact["link_id"]
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3.5 py-2 text-xs font-semibold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                ui("Decline"),
                type="button",
                disabled=ContactsState.is_responding,
                on_click=lambda: ContactsState.decline_request(
                    contact["link_id"]
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f7d9a0] bg-white px-3.5 py-2 text-xs font-semibold text-[#4b5563] transition-colors hover:border-[#f7d9a0] hover:text-[#e08b12] disabled:opacity-60",
            ),
            block_member_button(contact["other_id"], contact["other_name"]),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        class_name="w-full rounded-2xl border border-[#f7d9a0] bg-white p-4",
    )


def list_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-20 w-full rounded-2xl bg-[#fff7e8]"
        ),
        rx.el.div(
            class_name="animate-pulse h-20 w-full rounded-2xl bg-[#fff7e8]"
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def requests_section() -> rx.Component:
    """Incoming requests only — nothing outgoing is listed separately."""
    return rx.el.section(
        rx.el.h3(
            ui("Requests"),
            class_name="text-xl sm:text-2xl font-bold tracking-tight text-[#111827]",
        ),
        rx.cond(
            ContactsState.is_loading,
            rx.el.div(list_skeleton(), class_name="mt-4 w-full"),
            rx.cond(
                ContactsState.incoming_count > 0,
                rx.el.div(
                    rx.foreach(ContactsState.incoming_requests, incoming_card),
                    class_name="mt-4 grid grid-cols-1 xl:grid-cols-2 gap-3 w-full items-start",
                ),
                rx.el.p(
                    ui("No requests waiting."),
                    class_name="mt-3 rounded-2xl border border-dashed border-[#f7d9a0] bg-white/60 px-4 py-4 text-sm font-medium text-[#4b5563]",
                ),
            ),
        ),
        class_name="w-full",
    )


def contact_row(contact: dict[str, str]) -> rx.Component:
    """One address-book line: photo, name and handle, message icon."""
    return rx.el.li(
        rx.el.div(
            avatar_with_tick(
                avatar_src(
                    contact["other_avatar"], contact["other_avatar_seed"]
                ),
                contact["other_verified"],
                "h-[70px] w-[70px] rounded-full bg-[#fff7e8] object-cover",
                "Contact profile photo",
            ),
            class_name="flex h-[70px] w-[70px] shrink-0 items-center justify-center rounded-full ring-2 ring-[#fff7e8]",
        ),
        rx.el.div(
            rx.el.p(
                contact["other_name"],
                class_name="text-base font-bold text-[#111827] leading-tight truncate",
            ),
            rx.cond(
                contact["other_handle"],
                rx.el.p(
                    contact["other_handle"],
                    class_name="mt-0.5 text-sm font-semibold text-[#e08b12] truncate",
                ),
                rx.el.p(
                    ui("no username yet"),
                    class_name="mt-0.5 text-sm font-medium text-[#4b5563] italic truncate",
                ),
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("message-square", class_name="h-5 w-5"),
            activity_dot(contact["unread_count"]),
            type="button",
            aria_label=ui_template(
                "Message {name} in the Inbox", "name", contact["other_name"]
            ),
            title=ui("Open this conversation in your Inbox"),
            on_click=lambda: ContactsState.open_contact_in_inbox(
                contact["link_id"]
            ),
            class_name="relative flex size-11 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-[#e08b12] transition-colors hover:bg-[#f7d9a0] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        class_name="flex w-full items-center gap-4 rounded-2xl border border-[#f7d9a0] bg-white px-4 py-3",
    )


def contacts_list() -> rx.Component:
    return rx.cond(
        ContactsState.is_loading,
        list_skeleton(),
        rx.cond(
            ContactsState.contacts.length() > 0,
            rx.el.ul(
                rx.foreach(ContactsState.contacts, contact_row),
                aria_label=ui("Your contacts"),
                class_name="flex flex-col gap-2 w-full",
            ),
            rx.el.p(
                ui("No contacts yet — find people and send a request."),
                class_name="rounded-2xl border border-dashed border-[#f7d9a0] bg-white/60 px-4 py-6 text-center text-sm font-medium text-[#4b5563]",
            ),
        ),
    )


def contacts_panel() -> rx.Component:
    return rx.el.div(
        requests_section(),
        contacts_header(),
        error_banner(ContactsState.error),
        success_banner(ContactsState.success),
        contacts_list(),
        on_mount=ContactsState.load_contacts,
        class_name="flex flex-col gap-5 w-full",
    )


# ---------------------------------------------------------------------------
# Inbox surface: the direct-message conversation panel.
# Used by the Inbox › Contacts folder only, never by Community › Contacts.
# ---------------------------------------------------------------------------


def message_bubble(msg: ContactMessageItem) -> rx.Component:
    return correspondence_bubble(
        msg,
        rx.match(
            msg["source_kind"],
            ("contact", REPORT_TARGET_CONTACT_MESSAGE),
            ("noncontact", REPORT_TARGET_NONCONTACT_MESSAGE),
            "",
        ),
        MessageDeletionState.delete_message(
            msg["source_kind"], msg["id"], True
        ),
    )


def conversation_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar_with_tick(
                avatar_src(
                    ContactsState.selected_contact["other_avatar"],
                    ContactsState.selected_contact["other_avatar_seed"],
                ),
                ContactsState.selected_contact["other_verified"],
                "size-12 rounded-full border-2 border-white bg-[#fff7e8] object-cover",
            ),
            rx.el.div(
                rx.el.p(
                    ContactsState.selected_contact["other_name"],
                    class_name="text-base font-bold text-[#111827] leading-tight",
                ),
                rx.el.p(
                    ui(ContactsState.selected_contact["status_label"]),
                    class_name="text-xs font-medium text-[#4b5563] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-center gap-3 min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-3.5 w-3.5"),
            type="button",
            aria_label=ui("Close conversation"),
            on_click=ContactsState.clear_selection,
            class_name="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-black hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        class_name="flex flex-wrap items-center justify-between gap-3 w-full",
    )


def message_history() -> rx.Component:
    return rx.el.div(
        rx.cond(
            ContactsState.is_loading_messages,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-16 w-2/3 rounded-2xl bg-[#fff7e8]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-16 w-2/3 self-end rounded-2xl bg-[#fff7e8]"
                ),
                class_name="flex flex-col gap-3 w-full",
            ),
            rx.cond(
                ContactsState.contact_messages.length() > 0,
                rx.el.div(
                    rx.foreach(ContactsState.contact_messages, message_bubble),
                    class_name="flex flex-col gap-1 w-full min-w-0",
                ),
                rx.el.div(
                    rx.icon(
                        "message-square",
                        class_name="h-6 w-6 text-[#fba922] mb-2",
                    ),
                    rx.el.p(
                        ui("No messages yet"),
                        class_name="text-sm font-semibold text-[#111827]",
                    ),
                    rx.el.p(
                        ui(
                            "Say hello, share where you're heading, and swap a little help."
                        ),
                        class_name="text-sm font-medium text-[#4b5563] mt-1",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full px-6 py-10",
                ),
            ),
        ),
        class_name=HISTORY_CLASS,
    )


def composer() -> rx.Component:
    return rx.el.form(
        rx.el.textarea(
            name="body",
            rows="1",
            aria_label=ui("Write a note to your confirmed contact"),
            placeholder=ui("Write a message"),
            class_name=MESSAGE_INPUT_CLASS,
        ),
        rx.el.button(
            rx.cond(
                ContactsState.is_sending,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Sending…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("send", class_name="h-4 w-4"),
                    ui("Send"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=ContactsState.is_sending | MessageAttachmentState.busy,
            class_name=SEND_CLASS,
        ),
        rx.el.input(
            type="hidden",
            name="conversation_key",
            default_value=UnifiedInboxState.selected_key,
            key=UnifiedInboxState.selected_key,
        ),
        message_attachments(),
        key=MessageAttachmentState.generation,
        on_submit=ContactsState.send_contact_message,
        reset_on_submit=False,
        class_name=COMPOSER_CLASS,
    )


def conversation_panel(
    embedded: bool = False, dedicated: bool = False
) -> rx.Component:
    return rx.el.div(
        rx.cond(
            ContactsState.has_selection,
            rx.el.div(
                rx.cond(
                    embedded,
                    rx.el.p(
                        ui(ContactsState.selected_contact["status_label"]),
                        class_name="text-xs text-[#e08b12]",
                    ),
                    conversation_header(),
                ),
                message_history(),
                rx.cond(
                    ContactsState.can_message_selected,
                    rx.cond(dedicated, rx.fragment(), composer()),
                    rx.el.p(
                        ui(
                            "You can write once this contact request is confirmed by both sides."
                        ),
                        class_name="text-sm font-medium text-[#4b5563]",
                    ),
                ),
                chat_safety(
                    ContactsState.selected_contact["other_id"],
                    ContactsState.selected_contact["other_name"],
                ),
                class_name="flex flex-col gap-4 w-full min-w-0",
            ),
            rx.cond(
                NonContactMessagingState.has_selection,
                rx.el.div(
                    noncontact_conversation_view(embedded, dedicated),
                    class_name="w-full mt-4",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "mails",
                            class_name="h-6 w-6 text-[#fba922]",
                        ),
                        class_name="flex items-center justify-center size-12 rounded-2xl bg-[#fff7e8] mb-3",
                    ),
                    rx.el.p(
                        ui("Select a conversation to read it"),
                        class_name="text-sm font-bold text-[#111827]",
                    ),
                    rx.el.p(
                        ui(
                            "Pick any conversation from the list — contacts, direct messages and job threads all open here."
                        ),
                        class_name="mt-1 max-w-md text-xs font-medium leading-relaxed text-[#4b5563]",
                    ),
                    role="status",
                    aria_label=ui("No conversation selected"),
                    class_name="mt-4 flex flex-col items-center justify-center text-center rounded-2xl border border-dashed border-[#f7d9a0] bg-white/60 px-6 py-14",
                ),
            ),
        ),
        class_name=rx.cond(
            embedded,
            "w-full min-w-0 bg-white",
            "w-full min-w-0 rounded-2xl border border-[#fba922] bg-white p-4",
        ),
    )
