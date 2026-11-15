"""Non-contact messaging surfaces: inline compose plus the Inbox thread."""

import reflex as rx
from app.avatars import animal_avatar
from app.interface_i18n import ui
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
    INPUT_CLASS,
    avatar_with_tick,
    error_banner,
    field_label,
    success_banner,
)
from app.components.chat_safety import chat_safety
from app.models import REPORT_TARGET_NONCONTACT_MESSAGE
from app.states.noncontact_state import (
    NonContactMessagingState,
    NonContactMessageItem,
)
from app.states.message_deletion_state import MessageDeletionState


def _avatar(path: rx.Var[str], seed: rx.Var[str]) -> rx.Var[str]:
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


def compose_form(
    person_id: rx.Var[int], person_name: rx.Var[str]
) -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label(
                "Write a message",
                "they can reply without becoming a contact",
            ),
            rx.el.textarea(
                name="body",
                rows="3",
                required=True,
                max_length=2000,
                placeholder="Hello! I'm passing through your city next week — could you point me to a good bike repair spot?",
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    NonContactMessagingState.is_sending,
                    rx.el.span(
                        rx.spinner(class_name="h-4 w-4"),
                        ui("Sending…"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                    rx.el.span(
                        rx.icon("send", class_name="h-4 w-4"),
                        "Send message",
                        class_name="flex items-center justify-center gap-2",
                    ),
                ),
                type="submit",
                disabled=NonContactMessagingState.is_sending,
                class_name="w-full sm:w-fit rounded-full bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
            ),
            rx.el.button(
                ui("Cancel"),
                type="button",
                on_click=NonContactMessagingState.close_compose,
                class_name="w-full sm:w-fit rounded-full border border-[#d4d4d4] bg-white px-4 py-2.5 text-sm font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
            ),
            class_name="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full",
        ),
        error_banner(NonContactMessagingState.error),
        on_submit=NonContactMessagingState.send_first_message,
        reset_on_submit=True,
        class_name="mt-3 flex flex-col gap-3 w-full rounded-2xl border border-dashed border-[#fff7e8] bg-[#fff7e8]/40 p-4",
    )


def message_control(
    person_id: rx.Var[int], person_name: rx.Var[str]
) -> rx.Component:
    """A `Message` button that reveals a short inline note form."""
    return rx.el.div(
        rx.el.button(
            rx.icon("mail", class_name="h-3.5 w-3.5"),
            rx.cond(
                NonContactMessagingState.compose_target_id == person_id,
                "Close message",
                "Message",
            ),
            type="button",
            aria_label=f"Message {person_name}",
            on_click=lambda: NonContactMessagingState.open_compose(
                person_id, person_name
            ),
            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3.5 py-2 text-xs font-bold text-[#e08b12] transition-colors hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fff7e8]",
        ),
        rx.cond(
            NonContactMessagingState.compose_target_id == person_id,
            compose_form(person_id, person_name),
            rx.fragment(),
        ),
        class_name="w-full",
    )


# ---------------------------------------------------------------------------
# Inbox › Contacts: non-contact conversation list and thread
# ---------------------------------------------------------------------------


def message_bubble(msg: NonContactMessageItem) -> rx.Component:
    return correspondence_bubble(
        msg,
        REPORT_TARGET_NONCONTACT_MESSAGE,
        MessageDeletionState.delete_message("noncontact", msg["id"], False),
    )


def thread_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar_with_tick(
                _avatar(
                    NonContactMessagingState.selected["other_avatar"],
                    NonContactMessagingState.selected["other_avatar_seed"],
                ),
                NonContactMessagingState.selected["other_verified"],
                "size-12 rounded-full border-2 border-white bg-[#fff7e8] object-cover",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        NonContactMessagingState.selected["other_name"],
                        class_name="text-base font-bold text-[#111827] leading-tight truncate",
                    ),
                    rx.el.span(
                        ui("Not a contact"),
                        title=ui("Not a contact"),
                        aria_label=ui("Not a contact"),
                        class_name="w-fit shrink-0 rounded-full border border-[#fff7e8] bg-[#fff7e8] px-2 py-0.5 text-[10px] font-bold text-[#e08b12]",
                    ),
                    class_name="flex min-w-0 flex-wrap items-center gap-2",
                ),
                rx.el.p(
                    "Replies are welcome either way",
                    class_name="mt-0.5 text-xs font-medium text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-center gap-3 min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-3.5 w-3.5"),
            type="button",
            aria_label=ui("Close conversation"),
            on_click=NonContactMessagingState.clear_selection,
            class_name="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-black hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        class_name="flex flex-wrap items-center justify-between gap-3 w-full",
    )


def thread_history() -> rx.Component:
    return rx.el.div(
        rx.cond(
            NonContactMessagingState.is_loading_messages,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-16 w-2/3 rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-16 w-2/3 self-end rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="flex flex-col gap-3 w-full",
            ),
            rx.cond(
                NonContactMessagingState.messages.length() > 0,
                rx.el.div(
                    rx.foreach(
                        NonContactMessagingState.messages, message_bubble
                    ),
                    class_name="flex flex-col gap-1 w-full min-w-0",
                ),
                rx.el.p(
                    "No messages in this conversation yet.",
                    class_name="text-sm font-medium text-[#4b5563] text-center py-8",
                ),
            ),
        ),
        class_name=HISTORY_CLASS,
    )


def reply_composer() -> rx.Component:
    return rx.el.form(
        rx.el.textarea(
            name="body",
            rows="1",
            required=MessageAttachmentState.pending.length() == 0,
            max_length=2000,
            aria_label="Reply — you don't need to be contacts",
            placeholder=ui("Write your reply…"),
            class_name=MESSAGE_INPUT_CLASS,
        ),
        rx.el.button(
            rx.cond(
                NonContactMessagingState.is_sending,
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
            disabled=NonContactMessagingState.is_sending
            | MessageAttachmentState.busy,
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
        on_submit=NonContactMessagingState.send_reply,
        reset_on_submit=False,
        class_name=COMPOSER_CLASS,
    )


def noncontact_conversation_view(
    embedded: bool = False, dedicated: bool = False
) -> rx.Component:
    """The selected non-contact thread, shown in the Inbox reading pane."""
    return rx.el.div(
        rx.cond(
            embedded,
            rx.el.p(
                "Not a contact · Replies are welcome either way",
                class_name="text-xs text-[#e08b12]",
            ),
            thread_header(),
        ),
        error_banner(NonContactMessagingState.error),
        success_banner(NonContactMessagingState.success),
        thread_history(),
        rx.cond(dedicated, rx.fragment(), reply_composer()),
        chat_safety(
            NonContactMessagingState.selected["other_id"],
            NonContactMessagingState.selected["other_name"],
        ),
        class_name=rx.cond(
            embedded,
            "flex flex-col gap-4 w-full min-w-0 bg-white",
            "flex flex-col gap-4 w-full min-w-0 rounded-2xl border border-[#fba922] bg-white p-4",
        ),
    )
