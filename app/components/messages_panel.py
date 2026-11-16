import reflex as rx

from app.interface_i18n import ui, ui_template, ui_template_multi
from app.components.job_feedback import job_feedback
from app.avatars import animal_avatar, member_avatar

from app.states.message_deletion_state import MessageDeletionState
from app.states.message_attachment_state import MessageAttachmentState
from app.components.message_attachments import message_attachments

from app.components.language_control import browser_translatable_text
from app.components.request_heading import request_heading
from app.components.disclosure import disclosure_arrow
from app.components.chat_safety import chat_safety
from app.components.chat_controls import (
    COMPOSER_CLASS,
    MESSAGE_INPUT_CLASS,
    SEND_CLASS,
    HISTORY_CLASS,
    correspondence_bubble,
)

from app.components.feedback import (
    INPUT_CLASS,
    SELECT_CLASS,
    avatar_with_tick,
    error_banner,
    field_label,
    select_wrapper,
    success_banner,
    verified_chip,
)
from app.components.contacts_panel import (
    conversation_panel as contact_conversation_panel,
    composer as contact_composer,
)
from app.components.help_hub_panel import (
    help_offer_card,
    section_skeleton,
)
from app.components.unified_inbox import (
    inbox_toolbar,
    unified_conversation_list,
    inbox_contacts_view,
    inbox_subview_header,
    envelope_star,
    contact_identity,
    back_to_inbox,
    remove_from_inbox,
)
from app.components.noncontact_panel import reply_composer
from app.states.unified_inbox_state import UnifiedInboxState
from app.states.noncontact_state import NonContactMessagingState
from app.states.contacts_state import ContactsState, ContactItem
from app.states.help_hub_state import HelpHubState
from app.states.messaging_state import (
    MessagingState,
    ReviewItem,
    ThreadItem,
    MessageItem,
)

STORY_UPLOAD_ID = "completion_story_photos"

SHARE_MARK_BASE = (
    "w-fit flex items-center gap-1.5 rounded-full px-3 py-2 text-xs "
    "font-bold transition-transform hover:scale-[1.03] "
    "focus:outline-hidden focus:ring-2 focus:ring-[#fff7e8]"
)


def contact_option(contact: ContactItem) -> rx.Component:
    return rx.el.button(
        contact_identity(contact),
        type="button",
        on_click=ContactsState.set_compose_target(
            contact["link_id"].to_string()
        ),
        aria_label=ui_template_multi(
            "Write to {name} {handle}",
            {
                "name": contact["other_name"],
                "handle": contact["other_handle"],
            },
        ),
        class_name="gah-conversation-toggle flex w-full items-center gap-3 bg-white px-3 py-3 text-black hover:bg-[#fff7e8]",
    )


def compose_area() -> rx.Component:
    """Write to a confirmed contact straight from the correspondence desk."""
    return rx.el.div(
        inbox_subview_header("Write a message", envelope_star()),
        rx.el.div(
            rx.el.label(
                ui("To:"),
                html_for="inbox-to",
                class_name="text-sm font-semibold text-black",
            ),
            rx.el.input(
                id="inbox-to",
                default_value=ContactsState.compose_search,
                on_change=ContactsState.set_compose_search.debounce(300),
                disabled=ContactsState.is_sending,
                placeholder=ui("Find a contact by name or @username"),
                auto_complete="off",
                class_name=INPUT_CLASS,
            ),
            rx.cond(
                ContactsState.is_loading,
                rx.el.p(
                    ui("Loading contacts…"),
                    role="status",
                    class_name="py-3 text-sm text-gray-600",
                ),
                rx.cond(
                    ContactsState.compose_ready,
                    rx.el.p(
                        ui(
                            "Recipient selected · edit To to choose someone else"
                        ),
                        role="status",
                        class_name="text-xs text-[#e08b12]",
                    ),
                    rx.cond(
                        ContactsState.compose_options.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                ContactsState.compose_options, contact_option
                            ),
                            aria_label=ui("Matching accepted contacts"),
                            class_name="gah-edge-stack flex max-h-64 w-full flex-col gap-0 overflow-y-auto rounded-2xl bg-white",
                        ),
                        rx.el.p(
                            ui(
                                "No matching contacts. Try another name or username."
                            ),
                            role="status",
                            class_name="py-3 text-sm text-gray-600",
                        ),
                    ),
                ),
            ),
            class_name="flex w-full flex-col gap-2",
        ),
        rx.fragment(
            rx.cond(
                ContactsState.has_message_contacts,
                rx.el.form(
                    rx.el.label(
                        ui("Subject"),
                        html_for="inbox-subject",
                        class_name="text-sm font-semibold text-black",
                    ),
                    rx.el.input(
                        id="inbox-subject",
                        name="subject",
                        required=True,
                        max_length=120,
                        placeholder=ui("What is your message about?"),
                        class_name=INPUT_CLASS,
                    ),
                    rx.el.div(
                        rx.el.label(
                            ui("Message"),
                            html_for="inbox-compose-message",
                            class_name="text-sm font-semibold text-black",
                        ),
                        rx.el.textarea(
                            name="body",
                            id="inbox-compose-message",
                            rows="7",
                            required=True,
                            max_length=2000,
                            placeholder=ui("Write a message"),
                            class_name=INPUT_CLASS
                            + " resize-y leading-relaxed",
                        ),
                        class_name="w-full",
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
                        disabled=ContactsState.is_sending
                        | ~ContactsState.compose_ready,
                        class_name="w-fit self-end rounded-xl bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
                    ),
                    on_submit=ContactsState.compose_and_send,
                    key=ContactsState.compose_generation,
                    reset_on_submit=False,
                    class_name="gah-compose-body flex flex-col gap-3 w-full rounded-2xl bg-white p-4 shadow-[0_0_10px_rgba(17,24,39,0.12)]",
                ),
                rx.el.div(
                    rx.icon(
                        "users-round", class_name="h-5 w-5 text-[#fba922] mb-2"
                    ),
                    rx.el.p(
                        ui("No confirmed contacts yet"),
                        class_name="text-sm font-bold text-[#111827]",
                    ),
                    rx.el.p(
                        ui("Confirm a contact in Community, then message them"),
                        class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                    ),
                    class_name="gah-compose-body w-full flex flex-col items-center justify-center text-center rounded-2xl bg-white px-5 py-8 shadow-[0_0_10px_rgba(17,24,39,0.12)]",
                ),
            ),
            rx.cond(
                ContactsState.error,
                rx.el.p(
                    ContactsState.error,
                    role="alert",
                    class_name="mt-3 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-semibold text-[#e08b12]",
                ),
                rx.fragment(),
            ),
        ),
        class_name="flex flex-col gap-3 w-full mb-4",
    )


def review_target_identity() -> rx.Component:
    return rx.el.div(
        avatar_with_tick(
            rx.cond(
                MessagingState.selected_thread["other_avatar"],
                rx.get_upload_url(
                    MessagingState.selected_thread["other_avatar"]
                ),
                animal_avatar(
                    MessagingState.selected_thread["other_avatar_seed"]
                ),
            ),
            MessagingState.selected_thread["other_verified"],
            "size-12 shrink-0 rounded-full bg-[#fff7e8] object-cover",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    MessagingState.selected_thread["other_name"],
                    class_name="text-sm font-bold text-black",
                ),
                rx.el.div(
                    rx.foreach(
                        MessagingState.rating_values,
                        lambda value: rx.icon(
                            "star",
                            class_name=rx.cond(
                                (
                                    MessagingState.selected_thread[
                                        "other_rating_count"
                                    ]
                                    > 0
                                )
                                & (
                                    value
                                    <= MessagingState.selected_thread[
                                        "other_rating"
                                    ]
                                ),
                                "size-4 stroke-[#fba922] fill-[#fba922]",
                                "size-4 stroke-[#fba922] fill-none",
                            ),
                        ),
                    ),
                    role="img",
                    aria_label=rx.cond(
                        MessagingState.selected_thread["other_rating_count"]
                        > 0,
                        ui_template_multi(
                            "{score} out of 5 · {count} reviews",
                            {
                                "score": f"{MessagingState.selected_thread['other_rating']:.1f}",
                                "count": MessagingState.selected_thread[
                                    "other_rating_count"
                                ].to_string(),
                            },
                        ),
                        ui("Unrated · 0 reviews"),
                    ),
                    class_name="flex shrink-0 items-center gap-0.5",
                ),
                class_name="flex flex-wrap items-center gap-x-2 gap-y-1",
            ),
            rx.el.p(
                MessagingState.selected_thread["other_handle"],
                class_name="text-xs text-[#e08b12]",
            ),
            rx.el.p(
                MessagingState.selected_thread["post_title"],
                class_name="mt-2 text-sm font-semibold text-black break-words",
            ),
            class_name="flex-1 min-w-0",
        ),
        rx.el.button(
            disclosure_arrow(True, "x"),
            type="button",
            aria_label=ui("Close review form"),
            aria_expanded=True,
            aria_controls=f"pending-review-{MessagingState.selected_thread['task_id']}",
            disabled=MessagingState.is_reviewing,
            on_click=MessagingState.close_review_target,
            class_name="flex size-11 shrink-0 items-center justify-center rounded-full bg-white text-black hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        class_name="flex items-start gap-3 w-full",
    )


def message_bubble(msg: MessageItem) -> rx.Component:
    return correspondence_bubble(
        msg, "", MessageDeletionState.delete_message("job", msg["id"], False)
    )


def message_history() -> rx.Component:
    return rx.el.div(
        rx.cond(
            MessagingState.is_loading_thread,
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
                MessagingState.messages.length() > 0,
                rx.el.div(
                    rx.foreach(MessagingState.messages, message_bubble),
                    class_name="flex flex-col gap-1 w-full min-w-0",
                ),
                rx.el.div(
                    rx.icon("send", class_name="h-6 w-6 text-[#fba922] mb-2"),
                    rx.el.p(
                        ui("No messages in this thread yet."),
                        class_name="text-sm font-semibold text-[#404040]",
                    ),
                    rx.el.p(
                        ui("Say hello and agree where to meet."),
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
            key=MessagingState.composer_generation,
            default_value="",
            rows="1",
            aria_label=ui("Reply to this conversation"),
            placeholder=ui("Write a message"),
            class_name=MESSAGE_INPUT_CLASS,
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    MessagingState.is_sending,
                    rx.el.span(
                        rx.spinner(class_name="h-4 w-4"),
                        ui("Sending…"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                    rx.el.span(
                        ui("Send"),
                        rx.icon("send", class_name="h-4 w-4"),
                        class_name="flex items-center justify-center gap-2",
                    ),
                ),
                type="submit",
                disabled=MessagingState.is_sending
                | MessageAttachmentState.busy,
                class_name=SEND_CLASS,
            ),
            class_name="shrink-0 self-end",
        ),
        rx.el.input(
            type="hidden",
            name="conversation_key",
            default_value=UnifiedInboxState.selected_key,
            key=UnifiedInboxState.selected_key,
        ),
        message_attachments(),
        key=MessageAttachmentState.generation,
        on_submit=MessagingState.send_message,
        reset_on_submit=False,
        class_name=COMPOSER_CLASS,
    )


def completion_form() -> rx.Component:
    return rx.el.button(
        rx.cond(
            MessagingState.is_completing,
            ui("Confirming…"),
            ui("Confirm job is done"),
        ),
        rx.cond(
            MessagingState.is_completing,
            rx.icon("loader-circle", class_name="size-4 animate-spin"),
            rx.icon("check", class_name="size-4"),
        ),
        type="button",
        disabled=MessagingState.is_completing,
        on_click=MessagingState.confirm_job_done,
        class_name="flex w-fit items-center justify-center gap-1.5 rounded-full border border-[#fba922] bg-white px-3 py-1.5 text-xs font-semibold text-black hover:bg-[#fff7e8] disabled:opacity-60",
    )


def completion_card() -> rx.Component:
    return rx.cond(
        MessagingState.selected_thread["i_confirmed"],
        rx.cond(
            MessagingState.can_review,
            rx.el.button(
                ui("Review"),
                rx.icon("star", class_name="size-4"),
                type="button",
                on_click=MessagingState.open_review_target,
                class_name="flex w-fit items-center justify-center gap-1.5 rounded-full border border-[#fba922] bg-white px-3 py-1.5 text-xs font-semibold text-[#fba922] hover:bg-[#fff7e8]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MessagingState.selected_thread["can_complete"],
            completion_form(),
            rx.fragment(),
        ),
    )


def category_star(
    field: rx.Var[str],
    score: rx.Var[int],
    value: rx.Var[int],
    label: rx.Var[str],
) -> rx.Component:
    return rx.el.button(
        rx.icon(
            "star",
            class_name=rx.cond(
                value <= score,
                "h-4 w-4 text-[#e08b12]",
                "h-4 w-4 text-[#d4d4d4]",
            ),
        ),
        type="button",
        aria_label=ui_template_multi(
            "{category}: {score} out of 5 stars",
            {"category": ui(label), "score": value.to_string()},
        ),
        aria_pressed=value == score,
        on_click=lambda: MessagingState.set_review_score(field, value),
        class_name=rx.cond(
            value <= score,
            "flex items-center justify-center size-8 rounded-lg border border-[#fff7e8] bg-[#fff7e8] transition-colors",
            "flex items-center justify-center size-8 rounded-lg border border-[#e5e5e5] bg-white transition-colors hover:border-[#e08b12]",
        ),
    )


def review_category_row(item: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                ui(item["label"]),
                class_name="text-sm font-bold text-[#111827]",
            ),
            rx.el.span(
                rx.cond(
                    item["score"].to(int) > 0,
                    ui_template(
                        "{score} out of 5",
                        "score",
                        f"{item['score'].to(float):.1f}",
                    ),
                    ui("Not scored yet"),
                ),
                class_name=rx.cond(
                    item["score"].to(int) > 0,
                    "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#e08b12]",
                    "w-fit rounded-full border border-dashed border-[#d4d4d4] px-2.5 py-0.5 text-[11px] font-semibold text-[#4b5563]",
                ),
            ),
            class_name="flex flex-wrap items-center justify-between gap-2 min-w-0 max-w-full",
        ),
        rx.el.div(
            rx.foreach(
                MessagingState.rating_values,
                lambda value: category_star(
                    item["field"], item["score"].to(int), value, item["label"]
                ),
            ),
            rx.el.button(
                ui("Clear"),
                type="button",
                aria_label=ui_template_multi(
                    "Clear {category} to zero, not scored",
                    {"category": ui(item["label"])},
                ),
                on_click=lambda: MessagingState.set_review_score(
                    item["field"], 0
                ),
                class_name="text-xs text-[#e08b12] hover:underline focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-2",
        ),
        class_name="w-full min-w-0 max-w-full rounded-xl border border-[#d4d4d4] bg-white px-3 py-3",
    )


def category_score_chip(item: dict[str, str]) -> rx.Component:
    return rx.el.span(
        rx.el.span(
            ui(item["label"]),
            class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
        ),
        rx.el.span(
            ui_template(
                "{score} out of 5",
                "score",
                f"{item['score'].to(float):.1f}",
            ),
            class_name="text-[11px] font-bold text-[#e08b12]",
        ),
        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1",
    )


def star_row(rating: rx.Var[int]) -> rx.Component:
    return rx.el.div(
        rx.foreach(
            MessagingState.rating_values,
            lambda v: rx.icon(
                "star",
                class_name=rx.cond(
                    v <= rating,
                    "h-3.5 w-3.5 text-[#e08b12]",
                    "h-3.5 w-3.5 text-[#d4d4d4]",
                ),
            ),
        ),
        class_name="flex items-center gap-0.5",
    )


def review_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.h4(
                rx.cond(
                    MessagingState.review_ready,
                    ui_template(
                        "Overall {score} out of 5",
                        "score",
                        f"{(MessagingState.review_scores['category_one'] + MessagingState.review_scores['category_two'] + MessagingState.review_scores['category_three'] + MessagingState.review_scores['category_four']) / 4:.1f}",
                    ),
                    ui("Score all four categories"),
                ),
                class_name="rounded-xl bg-[#fff7e8] border border-[#fba922] px-3 py-2 text-sm font-bold text-[#b86e08]",
            ),
            rx.el.span(
                rx.icon("clipboard-check", class_name="h-3 w-3"),
                MessagingState.review_average_label,
                class_name="w-fit shrink-0 flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold text-[#e08b12]",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(MessagingState.review_fields, review_category_row),
            class_name="grid grid-cols-[repeat(auto-fit,minmax(min(100%,260px),1fr))] gap-3 w-full min-w-0",
        ),
        rx.el.div(
            field_label("A short note", "optional · up to 500 words"),
            rx.el.textarea(
                name="comment",
                rows="3",
                placeholder=ui(
                    "I.e. Turned up early, carried more than their share and told great stories."
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="w-full",
        ),
        rx.el.button(
            rx.cond(
                MessagingState.is_reviewing,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Saving review…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("star", class_name="h-4 w-4"),
                    ui("Save review"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=MessagingState.is_reviewing | ~MessagingState.review_ready,
            class_name="gah-orange-control w-full sm:w-fit rounded-xl border border-[#b86e08] bg-[#fff7e8] px-6 py-3 text-sm font-bold text-[#b86e08] transition-colors hover:bg-[#ffedcc] disabled:opacity-60",
        ),
        on_submit=MessagingState.submit_review,
        reset_on_submit=False,
        key=MessagingState.selected_thread["task_id"],
        class_name="flex flex-col gap-4 w-full bg-white",
    )


def review_response(review: ReviewItem) -> rx.Component:
    return rx.el.div(
        rx.cond(
            review["response"],
            rx.el.div(
                rx.el.p(
                    ui("Recipient’s response"),
                    class_name="text-xs font-bold text-[#e08b12]",
                ),
                browser_translatable_text(
                    review["response"],
                    class_name="mt-1 text-sm leading-relaxed text-[#4b5563]",
                ),
                class_name="mt-3 border-l-2 border-[#fff7e8] pl-3",
            ),
            rx.cond(
                review["can_respond"],
                rx.el.form(
                    rx.el.label(
                        ui("Your one-time response · up to 500 words"),
                        html_for=f"review-response-{review['id']}",
                        class_name="text-xs font-semibold text-[#4b5563]",
                    ),
                    rx.el.textarea(
                        name="response",
                        id=f"review-response-{review['id']}",
                        rows="2",
                        required=True,
                        placeholder=ui(
                            "Add a thoughtful response. It cannot be edited after posting."
                        ),
                        class_name="w-full rounded-xl border border-[#fff7e8] bg-white p-3 text-sm text-[#111827] focus:outline-hidden focus:ring-2 focus:ring-[#e08b12]",
                    ),
                    rx.el.button(
                        rx.cond(
                            MessagingState.responding_id == review["id"],
                            ui("Posting…"),
                            ui("Post response"),
                        ),
                        type="submit",
                        disabled=MessagingState.responding_id != 0,
                        class_name="w-fit rounded-xl bg-[#e08b12] px-4 py-2 text-xs font-bold text-white hover:bg-[#b86e08] disabled:opacity-60",
                    ),
                    on_submit=lambda data: (
                        MessagingState.submit_review_response(
                            review["id"], data
                        )
                    ),
                    reset_on_submit=False,
                    class_name="mt-3 flex flex-col gap-2",
                ),
                rx.fragment(),
            ),
        ),
        rx.cond(
            (MessagingState.response_error_id == review["id"])
            & (MessagingState.response_error != ""),
            rx.el.p(
                job_feedback(MessagingState.response_error),
                role="alert",
                class_name="mt-2 text-xs text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def review_card(review: ReviewItem) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=member_avatar(
                    review["reviewer_avatar"], review["reviewer_avatar_seed"]
                ),
                class_name="size-9 rounded-full bg-[#fff7e8] shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    ui_template_multi(
                        "{reviewer} → {reviewee}",
                        {
                            "reviewer": review["reviewer_name"],
                            "reviewee": review["reviewee_name"],
                        },
                    ),
                    class_name="text-sm font-semibold text-[#111827]",
                ),
                rx.el.p(
                    ui_template_multi(
                        "{direction} · {date}",
                        {
                            "direction": ui(review["direction_label"]),
                            "date": review["created"],
                        },
                    ),
                    class_name="text-[11px] font-medium text-[#4b5563] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                star_row(review["rating"].to(int)),
                rx.el.span(
                    ui_template(
                        "{score} out of 5",
                        "score",
                        f"{review['rating']:.1f}",
                    ),
                    class_name="text-[11px] font-bold text-[#e08b12]",
                ),
                class_name="flex flex-col items-end gap-1 shrink-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(review["categories"], category_score_chip),
            class_name="flex flex-wrap items-center gap-1.5 mt-2",
        ),
        rx.cond(
            review["comment"],
            browser_translatable_text(
                review["comment"],
                class_name="mt-2 text-sm font-medium text-[#4b5563] leading-relaxed",
            ),
            rx.fragment(),
        ),
        rx.cond(
            review["kindness_flag"],
            rx.el.span(
                rx.icon("sparkles", class_name="h-3 w-3"),
                ui("Kindness badge"),
                class_name="mt-2 w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827]",
            ),
            rx.fragment(),
        ),
        review_response(review),
        class_name="w-full rounded-2xl border border-[#e5e5e5] bg-white p-4",
    )


def pending_review_card(target: ThreadItem) -> rx.Component:
    return rx.el.section(
        rx.cond(
            MessagingState.review_target_open
            & (MessagingState.selected_thread["task_id"] == target["task_id"]),
            rx.el.div(
                review_target_identity(),
                rx.el.p(
                    rx.cond(
                        target["my_role"] == "poster",
                        ui_template_multi(
                            "{name} helped you with {title}.",
                            {
                                "name": target["other_name"],
                                "title": target["post_title"],
                            },
                        ),
                        ui_template_multi(
                            "{name} received your help with {title}.",
                            {
                                "name": target["other_name"],
                                "title": target["post_title"],
                            },
                        ),
                    ),
                    class_name="text-xs text-[#4b5563]",
                ),
                review_form(),
                error_banner(job_feedback(MessagingState.error)),
                rx.foreach(MessagingState.reviews, review_card),
                id=f"pending-review-{target['task_id']}",
                class_name="flex flex-col gap-4 w-full",
            ),
            rx.el.button(
                avatar_with_tick(
                    rx.cond(
                        target["other_avatar"],
                        rx.get_upload_url(target["other_avatar"]),
                        animal_avatar(target["other_avatar_seed"]),
                    ),
                    target["other_verified"],
                    "size-10 rounded-full bg-[#fff7e8] shrink-0",
                ),
                rx.el.span(
                    rx.el.span(
                        target["other_name"],
                        class_name="block text-sm font-bold text-black",
                    ),
                    rx.el.span(
                        rx.cond(
                            target["other_rating_count"] > 0,
                            ui_template_multi(
                                "{score} out of 5 · {count} reviews",
                                {
                                    "score": f"{target['other_rating']:.1f}",
                                    "count": target[
                                        "other_rating_count"
                                    ].to_string(),
                                },
                            ),
                            ui("Unrated · 0 reviews"),
                        ),
                        class_name="block mt-1 text-xs font-semibold text-[#e08b12]",
                    ),
                    rx.el.span(
                        target["post_title"],
                        class_name="block mt-1 text-xs text-[#4b5563] break-words",
                    ),
                    rx.el.span(
                        rx.cond(
                            target["my_role"] == "poster",
                            ui("Helped you"),
                            ui("Received your help"),
                        ),
                        class_name="block mt-1 text-xs text-[#4b5563]",
                    ),
                    class_name="min-w-0 flex-1 text-left",
                ),
                disclosure_arrow(),
                type="button",
                aria_expanded=False,
                aria_controls=f"pending-review-{target['task_id']}",
                disabled=MessagingState.is_reviewing,
                on_click=lambda: MessagingState.select_review_target(
                    target["task_id"]
                ),
                class_name="gah-review-toggle flex w-full items-center gap-3 bg-white focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
        ),
        rx.cond(
            MessagingState.review_target_open
            & (MessagingState.selected_thread["task_id"] == target["task_id"]),
            rx.el.button(
                rx.icon("trash-2", class_name="size-3.5"),
                ui("Delete review"),
                type="button",
                title=ui("Dismiss this unfilled review for this session only"),
                disabled=MessagingState.is_reviewing,
                on_click=lambda: MessagingState.dismiss_review_target(
                    target["task_id"]
                ),
                class_name="mt-4 flex w-fit items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs text-[#4b5563] hover:border-[#fba922] disabled:opacity-60",
            ),
            rx.fragment(),
        ),
        key=target["task_id"],
        class_name="w-full rounded-none border-0 bg-white p-3 sm:p-4",
    )


def review_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.foreach(MessagingState.review_targets, pending_review_card),
            class_name="gah-edge-stack flex flex-col gap-0 w-full",
        ),
        success_banner(job_feedback(MessagingState.success)),
        class_name="flex flex-col gap-4 w-full",
    )


def story_photo(photo: dict[str, str]) -> rx.Component:
    return rx.el.figure(
        rx.image(
            src=rx.get_upload_url(photo["url_name"]),
            alt=ui("A photo of the finished work"),
            class_name="h-28 w-40 rounded-xl object-cover bg-[#fff7e8]",
        ),
        rx.el.figcaption(
            rx.el.span(
                photo["uploader_name"],
                class_name="text-[10px] font-bold text-[#111827] truncate",
            ),
            rx.el.span(
                photo["created"],
                class_name="text-[10px] font-medium text-[#4b5563]",
            ),
            class_name="mt-1 flex flex-col",
        ),
        rx.cond(
            photo["mine"],
            rx.el.button(
                rx.icon("trash-2", class_name="h-3 w-3"),
                type="button",
                title=ui("Remove your photo"),
                aria_label=ui("Remove your photo"),
                on_click=lambda: MessagingState.remove_completion_photo(
                    photo["id"]
                ),
                class_name="absolute right-1.5 top-1.5 flex size-6 items-center justify-center rounded-full bg-white/90 text-[#4b5563] transition-colors hover:text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="relative w-fit shrink-0 rounded-2xl border border-[#fff7e8] bg-white p-1.5",
    )


def photo_strip() -> rx.Component:
    return rx.cond(
        MessagingState.completion_photos.length() > 0,
        rx.el.div(
            rx.foreach(MessagingState.completion_photos, story_photo),
            class_name="flex w-full items-start gap-2 overflow-x-auto pb-1",
        ),
        rx.el.div(
            rx.icon("images", class_name="h-5 w-5 text-[#e08b12] mb-1.5"),
            rx.el.p(
                ui("No photos on this postcard yet."),
                class_name="text-xs font-bold text-[#111827]",
            ),
            rx.el.p(
                ui(
                    "Either of you can add up to five pictures of the finished work."
                ),
                class_name="mt-0.5 text-xs font-medium text-[#4b5563]",
            ),
            class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#fff7e8] bg-white px-4 py-6",
        ),
    )


def photo_uploader() -> rx.Component:
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                rx.cond(
                    MessagingState.photo_busy,
                    rx.spinner(class_name="h-4 w-4 text-[#e08b12]"),
                    rx.icon("camera", class_name="h-4 w-4 text-[#e08b12]"),
                ),
                rx.el.span(
                    rx.cond(
                        MessagingState.photo_busy,
                        ui("Adding photos…"),
                        ui("Add completed-work photos"),
                    ),
                    class_name="text-xs font-bold text-[#111827]",
                ),
                rx.el.span(
                    rx.match(
                        MessagingState.photo_slots_left,
                        (0, ui("All 5 photo slots used")),
                        (1, ui("1 photo slot left")),
                        ui_template(
                            "{count} photo slots left",
                            "count",
                            MessagingState.photo_slots_left.to_string(),
                        ),
                    ),
                    class_name="text-[10px] font-semibold uppercase tracking-wide text-[#4b5563]",
                ),
                class_name="flex flex-col items-center justify-center gap-1 text-center",
            ),
            id=STORY_UPLOAD_ID,
            multiple=True,
            max_files=5,
            disabled=MessagingState.photo_busy
            | (MessagingState.photo_slots_left == 0),
            accept={
                "image/png": [".png"],
                "image/jpeg": [".jpg", ".jpeg"],
                "image/webp": [".webp"],
            },
            on_drop=MessagingState.handle_completion_photos(
                rx.upload_files(upload_id=STORY_UPLOAD_ID)
            ),
            class_name="w-full cursor-pointer rounded-2xl border-2 border-dashed border-[#fff7e8] bg-[#fff7e8] px-4 py-5 transition-colors hover:border-[#e08b12]",
        ),
        rx.el.p(
            ui(
                "JPEG/JPG, PNG or WebP only. Maximum 3 MB per source; stored as static WebP under 1 MB. No video or animated images. Completion photos are separate from original request photos."
            ),
            class_name="mt-2 text-[11px] font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.cond(
            MessagingState.photo_error,
            rx.el.p(
                job_feedback(MessagingState.photo_error),
                role="alert",
                class_name="mt-2 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MessagingState.photo_success,
            rx.el.p(
                job_feedback(MessagingState.photo_success),
                class_name="mt-2 rounded-xl bg-[#fba922] px-3 py-2 text-xs font-bold text-[#111827]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def share_link_button(
    key: str, label: str, icon: str, tone: str
) -> rx.Component:
    """A standard public share URL — the network opens with your caption ready."""
    return rx.el.a(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        label,
        href=MessagingState.share_links[key],
        target="_blank",
        rel="noopener noreferrer",
        title=ui_template(
            "Open {service} with your caption ready — you still press post",
            "service",
            label,
        ),
        class_name=f"{SHARE_MARK_BASE} {tone}",
    )


def device_share_button(label: str, icon: str, tone: str) -> rx.Component:
    """Instagram / TikTok have no public prefilled web post endpoint."""
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        label,
        type="button",
        on_click=lambda: MessagingState.share_via_device(label),
        title=ui_template(
            "{service} has no public web posting link, so we open your device share sheet or copy the caption for you",
            "service",
            label,
        ),
        class_name=f"{SHARE_MARK_BASE} {tone}",
    )


def share_marks() -> rx.Component:
    return rx.el.div(
        share_link_button(
            "telegram", "Telegram", "send", "bg-[#fff7e8] text-[#e08b12]"
        ),
        share_link_button(
            "whatsapp",
            "WhatsApp",
            "message-circle",
            "bg-[#fba922] text-[#111827]",
        ),
        share_link_button(
            "facebook", "Facebook", "thumbs-up", "bg-[#fff7e8] text-[#e08b12]"
        ),
        share_link_button("x", "X", "x", "bg-[#e5e5e5] text-[#111827]"),
        share_link_button(
            "pinterest", "Pinterest", "pin", "bg-[#fff7e8] text-[#e08b12]"
        ),
        share_link_button(
            "email", ui("Email"), "mail", "bg-[#fff7e8] text-[#b86e08]"
        ),
        device_share_button(
            "Instagram", "inbox", "bg-[#fff7e8] text-[#b86e08]"
        ),
        device_share_button("TikTok", "music", "bg-[#fff7e8] text-[#e08b12]"),
        class_name="flex flex-wrap items-center gap-2 w-full",
    )


def success_story_card() -> rx.Component:
    """A celebratory shared postcard — only for a perfect reciprocal pair."""
    return rx.cond(
        MessagingState.can_share_success,
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("party-popper", class_name="h-3.5 w-3.5"),
                    ui("Five stars both ways"),
                    class_name="w-fit flex items-center gap-2 rounded-full bg-[#fba922] px-3 py-1 text-xs font-bold text-[#111827]",
                ),
                rx.el.h3(
                    ui("Share the success"),
                    class_name="mt-2 text-xl font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    ui(
                        "You both gave each other a perfect score. Add a few pictures of the finished work and send the postcard wherever you like — nothing is ever posted for you."
                    ),
                    class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                photo_strip(),
                photo_uploader(),
                class_name="flex flex-col gap-3 w-full mt-4",
            ),
            rx.el.div(
                field_label("Your caption", "edit it before you share"),
                rx.el.textarea(
                    rows="3",
                    default_value=MessagingState.share_text,
                    placeholder=ui("Say what you managed together."),
                    on_change=MessagingState.set_share_caption.debounce(400),
                    class_name=INPUT_CLASS + " resize-y leading-relaxed",
                ),
                rx.el.p(
                    ui(
                        "Only the caption travels with the link. Go and Help does not keep a copy of anything you post elsewhere."
                    ),
                    class_name="mt-1.5 text-[11px] font-medium text-[#4b5563]",
                ),
                class_name="w-full mt-4",
            ),
            rx.el.div(
                rx.el.p(
                    ui("Send it to"),
                    class_name="text-[11px] font-bold uppercase tracking-[0.12em] text-[#4b5563] mb-2",
                ),
                share_marks(),
                rx.el.div(
                    rx.el.button(
                        rx.icon("copy", class_name="h-3.5 w-3.5"),
                        ui("Copy caption and link"),
                        type="button",
                        on_click=MessagingState.copy_share_caption,
                        class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3 py-2 text-xs font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                    ),
                    class_name="mt-2",
                ),
                rx.el.p(
                    ui(
                        "Instagram and TikTok have no public link that fills a post in advance, so we open your device share sheet — or copy the caption if your browser can't share."
                    ),
                    class_name="mt-2 text-[11px] font-medium leading-relaxed text-[#4b5563]",
                ),
                rx.cond(
                    MessagingState.share_note,
                    rx.el.p(
                        job_feedback(MessagingState.share_note),
                        role="status",
                        class_name="mt-2 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                class_name="w-full mt-4 rounded-2xl border border-[#e5e5e5] bg-white p-4",
            ),
            class_name="gah-main-card w-full rounded-2xl bg-[#ffffff] p-5 sm:p-6",
        ),
        rx.fragment(),
    )


def report_category_option(item: dict[str, str]) -> rx.Component:
    return rx.el.option(ui(item["label"]), value=item["value"])


def safety_report_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label("What happened?", "required"),
            select_wrapper(
                rx.el.select(
                    rx.el.option(
                        ui("Choose the closest description"),
                        value="",
                        disabled=True,
                    ),
                    rx.foreach(
                        MessagingState.report_categories,
                        report_category_option,
                    ),
                    value=MessagingState.report_category,
                    on_change=MessagingState.set_report_category,
                    class_name=SELECT_CLASS,
                )
            ),
            class_name="w-full",
        ),
        rx.el.div(
            field_label(
                "Tell us what happened", "required · up to 2000 characters"
            ),
            rx.el.textarea(
                name="details",
                rows="4",
                max_length=2000,
                required=True,
                placeholder=ui(
                    "Where and when it happened, what was said or done, and anything you'd like us to check."
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="w-full",
        ),
        rx.cond(
            MessagingState.report_ready,
            rx.fragment(),
            rx.el.p(
                ui("Please choose what happened before sending."),
                class_name="text-xs font-semibold text-[#b86e08]",
            ),
        ),
        rx.el.button(
            rx.cond(
                MessagingState.is_reporting,
                rx.el.span(
                    rx.spinner(class_name="h-4 w-4"),
                    ui("Sending privately…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    rx.icon("shield", class_name="h-4 w-4"),
                    ui("Send this report privately"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="submit",
            disabled=MessagingState.is_reporting | ~MessagingState.report_ready,
            class_name="w-full sm:w-fit rounded-xl bg-[#4b5563] px-6 py-3 text-sm font-bold text-white transition-colors hover:bg-[#111827] disabled:opacity-60",
        ),
        on_submit=MessagingState.submit_safety_report,
        reset_on_submit=True,
        class_name="flex flex-col gap-4 w-full mt-4",
    )


def safety_report_card() -> rx.Component:
    """Calm, serious and private. Independent of any star score."""
    return rx.cond(
        MessagingState.selected_thread["is_completed"],
        rx.el.div(
            rx.el.button(
                rx.el.div(
                    rx.icon(
                        "shield", class_name="h-4 w-4 text-[#4b5563] shrink-0"
                    ),
                    rx.el.div(
                        rx.el.p(
                            ui("Report a bad experience"),
                            class_name="text-sm font-bold text-[#111827] text-left",
                        ),
                        rx.el.p(
                            ui(
                                "Private, read only by our review team. Your star score makes no difference to this."
                            ),
                            class_name="mt-0.5 text-xs font-medium text-[#4b5563] text-left leading-relaxed",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name=rx.cond(
                            MessagingState.report_open,
                            "h-4 w-4 text-[#4b5563] rotate-180 transition-transform shrink-0",
                            "h-4 w-4 text-[#4b5563] transition-transform shrink-0",
                        ),
                    ),
                    class_name="flex items-start gap-3 w-full",
                ),
                type="button",
                aria_expanded=MessagingState.report_open,
                on_click=MessagingState.toggle_report_form,
                class_name="w-full rounded-2xl px-1 py-1 text-left focus:outline-hidden focus:ring-2 focus:ring-[#fff7e8]",
            ),
            rx.cond(
                MessagingState.selected_thread["my_report_done"],
                rx.el.p(
                    ui(
                        "You've already told us about this job. Our team is looking at it privately — nothing is published."
                    ),
                    class_name="mt-3 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-semibold text-[#e08b12]",
                ),
                rx.cond(
                    MessagingState.report_open,
                    rx.el.div(
                        rx.el.p(
                            ui(
                                "Nothing you write here is shown to the other person or published anywhere. We never accuse anyone in public, and an account is never suspended automatically because of a report."
                            ),
                            class_name="rounded-xl border border-[#e5e5e5] bg-white px-3 py-2 text-xs font-medium leading-relaxed text-[#4b5563]",
                        ),
                        safety_report_form(),
                        class_name="w-full mt-3",
                    ),
                    rx.fragment(),
                ),
            ),
            rx.cond(
                MessagingState.report_error,
                rx.el.p(
                    job_feedback(MessagingState.report_error),
                    role="alert",
                    class_name="mt-3 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#e08b12]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                MessagingState.report_success,
                rx.el.p(
                    job_feedback(MessagingState.report_success),
                    class_name="mt-3 rounded-xl bg-[#fba922] px-3 py-2 text-xs font-bold text-[#111827]",
                ),
                rx.fragment(),
            ),
            class_name="w-full rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-4",
        ),
        rx.fragment(),
    )


def job_chat_actions() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            chat_safety(
                MessagingState.selected_thread["other_id"],
                MessagingState.selected_thread["other_name"],
            ),
            completion_card(),
            class_name="flex flex-wrap items-center justify-center gap-2 w-full",
        ),
        error_banner(ContactsState.error),
        success_banner(ContactsState.success, white_text=True),
        class_name="flex flex-col gap-2 w-full",
    )


def job_conversation_panel(dedicated: bool = False) -> rx.Component:
    """The job discussion desk: history, completion, reviews, share, report."""
    return rx.el.div(
        rx.cond(
            MessagingState.has_selection,
            rx.el.div(
                rx.el.p(
                    rx.match(
                        MessagingState.selected_thread["is_completed"],
                        (
                            True,
                            ui_template(
                                "You have confirmed. {name} has confirmed.",
                                "name",
                                MessagingState.selected_thread["other_name"],
                            ),
                        ),
                        rx.cond(
                            MessagingState.awaiting_other_confirm,
                            ui_template(
                                "You have confirmed. Awaiting confirmation from {name}.",
                                "name",
                                MessagingState.selected_thread["other_name"],
                            ),
                            rx.cond(
                                MessagingState.selected_thread["can_complete"],
                                ui("Help confirmed · agree the details below"),
                                ui("Help not yet confirmed"),
                            ),
                        ),
                    ),
                    role="status",
                    class_name="w-full text-center text-sm font-medium leading-relaxed text-[#4b5563]",
                ),
                message_history(),
                rx.cond(dedicated, rx.fragment(), composer()),
                rx.cond(
                    MessagingState.review_target_open,
                    rx.el.div(
                        review_target_identity(),
                        review_form(),
                        rx.foreach(MessagingState.reviews, review_card),
                        class_name="flex w-full flex-col gap-4 bg-white",
                    ),
                    rx.fragment(),
                ),
                success_story_card(),
                safety_report_card(),
                job_chat_actions(),
                class_name="flex flex-col gap-4 w-full",
            ),
            rx.el.div(
                rx.icon("mails", class_name="h-6 w-6 text-[#fba922] mb-2"),
                rx.el.p(
                    ui("Pick a job conversation"),
                    class_name="text-sm font-semibold text-[#404040]",
                ),
                rx.el.p(
                    ui(
                        "Message history, completion controls and reviews open here."
                    ),
                    class_name="text-sm font-medium text-[#4b5563] mt-1",
                ),
                class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-[#fafafa] px-6 py-16",
            ),
        ),
        class_name="w-full min-w-0 bg-white",
    )


def inbox_header() -> rx.Component:
    """One calm correspondence desk: unread badge, search and type filters."""
    return rx.el.div(
        inbox_toolbar(),
        class_name="flex flex-col gap-3 w-full",
    )


def compact_heading(
    title: str, count: rx.Var[int] | rx.Var[str]
) -> rx.Component:
    return request_heading(title, count.to(int))


def hub_empty(title: str, body: str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-5 w-5 text-[#fba922] mb-1.5"),
        rx.el.p(ui(title), class_name="text-sm font-bold text-[#111827]"),
        rx.el.p(
            ui(body),
            class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#4b5563]",
        ),
        class_name="w-full flex flex-col items-center justify-center text-center rounded-2xl bg-white px-5 py-6",
    )


def inbox_disclosure(
    title: str,
    count: rx.Var[int],
    opened: rx.Var[bool],
    toggle: rx.event.EventType,
    target: str,
) -> rx.Component:
    return rx.el.h3(
        rx.el.button(
            rx.el.span(
                rx.el.span(count, class_name="text-[#e08b12]"),
                " ",
                rx.match(
                    title,
                    (
                        "Offers to help you",
                        rx.cond(
                            count == 1,
                            ui("Offer to help you"),
                            ui("Offers to help you"),
                        ),
                    ),
                    (
                        "Requests for your help",
                        rx.cond(
                            count == 1,
                            ui("Request for your help"),
                            ui("Requests for your help"),
                        ),
                    ),
                    (
                        "Messages from contacts",
                        rx.cond(
                            count == 1,
                            ui("Message from contacts"),
                            ui("Messages from contacts"),
                        ),
                    ),
                    ui(title),
                ),
                class_name="w-full min-w-0 text-center",
            ),
            rx.el.span(
                disclosure_arrow(opened),
                class_name="absolute right-0 top-1/2 -translate-y-1/2",
            ),
            type="button",
            aria_expanded=opened,
            aria_controls=target,
            on_click=toggle,
            class_name="gah-conversation-toggle relative flex w-full items-center gap-3 bg-transparent px-10 py-3 text-center text-xl sm:text-2xl font-bold tracking-tight leading-tight text-[#111827] focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        class_name="w-full",
    )


def offer_disclosure(offer: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.button(
            avatar_with_tick(
                rx.cond(
                    offer["helper_avatar"],
                    rx.get_upload_url(offer["helper_avatar"]),
                    animal_avatar(offer["helper_avatar_seed"]),
                ),
                offer["helper_verified"],
                "size-11 shrink-0 rounded-full bg-[#fff7e8] object-cover",
                ui("Helper photo"),
            ),
            rx.el.span(
                rx.el.span(
                    offer["helper_name"],
                    class_name="block text-sm font-bold text-black",
                ),
                rx.el.span(
                    ui_template("Offered {date}", "date", offer["applied"]),
                    class_name="mt-1 block text-xs text-[#4b5563]",
                ),
                rx.el.span(
                    ui_template(
                        "Helper offering you help for: {title}",
                        "title",
                        offer["title"],
                    ),
                    class_name="mt-2 block text-sm text-black",
                ),
                class_name="min-w-0 flex-1 break-words",
            ),
            disclosure_arrow(
                UnifiedInboxState.open_offer_ids.contains(offer["id"])
            ),
            type="button",
            aria_expanded=UnifiedInboxState.open_offer_ids.contains(
                offer["id"]
            ),
            aria_controls=f"offer-body-{offer['id']}",
            on_click=UnifiedInboxState.toggle_offer(offer["id"]),
            class_name="gah-conversation-toggle flex w-full items-center gap-3 bg-white p-4 text-left focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        rx.cond(
            UnifiedInboxState.open_offer_ids.contains(offer["id"]),
            rx.el.div(
                help_offer_card(offer, True, True),
                id=f"offer-body-{offer['id']}",
                class_name="w-full pl-3 sm:pl-6",
            ),
            rx.fragment(),
        ),
        class_name="w-full min-w-0 bg-white",
    )


def offers_block() -> rx.Component:
    """Incoming Help offers awaiting Confirm or Deny — moved off Help."""
    return rx.el.section(
        inbox_disclosure(
            "Offers to help you",
            HelpHubState.help_offers.length(),
            UnifiedInboxState.offers_open,
            UnifiedInboxState.toggle_offers,
            "inbox-offers",
        ),
        rx.cond(
            UnifiedInboxState.offers_open,
            rx.el.div(
                rx.cond(
                    HelpHubState.is_loading,
                    section_skeleton(),
                    rx.cond(
                        HelpHubState.help_offers.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                HelpHubState.help_offers,
                                offer_disclosure,
                            ),
                            class_name="gah-edge-stack flex flex-col gap-0 w-full",
                        ),
                        hub_empty(
                            "No offers from helpers",
                            "New offers on your requests land here with Confirm and Deny.",
                            "inbox",
                        ),
                    ),
                ),
                id="inbox-offers",
                class_name="w-full min-w-0 rounded-2xl bg-white shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def helpee_request_card(request: dict[str, str]) -> rx.Component:
    """One genuine pending direct request from a post owner to me."""
    return rx.el.article(
        rx.el.div(
            avatar_with_tick(
                member_avatar(
                    request["other_avatar"], request["other_avatar_seed"]
                ),
                request["other_verified"],
                "size-11 rounded-full bg-[#fff7e8] shrink-0",
                ui("Helpee photo"),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        request["other_name"],
                        class_name="text-sm font-bold text-[#111827] leading-tight",
                    ),
                    verified_chip(request["other_verified"]),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.p(
                    request["post_title"],
                    class_name="mt-0.5 text-xs font-semibold text-[#e08b12]",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                request["last_at"],
                class_name="shrink-0 text-[11px] font-medium text-[#4b5563]",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.cond(
            request["last_snippet"],
            rx.el.p(
                request["last_snippet"],
                class_name="mt-2 text-xs font-medium leading-relaxed text-[#4b5563] line-clamp-3",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("check", class_name="h-3.5 w-3.5"),
                ui("Accept"),
                type="button",
                aria_label=ui_template(
                    "Accept the request to help with {title}",
                    "title",
                    request["post_title"],
                ),
                disabled=MessagingState.deciding_request_id
                == request["application_id"],
                on_click=lambda: MessagingState.accept_direct_request(
                    request["application_id"]
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-4 py-2 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                ui("Decline"),
                type="button",
                aria_label=ui_template(
                    "Decline the request to help with {title}",
                    "title",
                    request["post_title"],
                ),
                disabled=MessagingState.deciding_request_id
                == request["application_id"],
                on_click=lambda: MessagingState.decline_direct_request(
                    request["application_id"]
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f6c66f] bg-white px-4 py-2 text-xs font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("message-square", class_name="h-3.5 w-3.5"),
                ui("Open conversation"),
                type="button",
                on_click=lambda: UnifiedInboxState.open_item(
                    "job", request["id"]
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-4 py-2 text-xs font-semibold text-[#e08b12] transition-colors hover:bg-[#fff7e8]",
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        class_name="w-full min-w-0 bg-white p-4",
    )


def helpee_requests_block() -> rx.Component:
    """Pending direct requests a helpee sent straight to me."""
    return rx.el.section(
        inbox_disclosure(
            "Requests for your help",
            MessagingState.direct_request_count,
            UnifiedInboxState.requests_open,
            UnifiedInboxState.toggle_requests,
            "inbox-requests",
        ),
        rx.cond(
            UnifiedInboxState.requests_open,
            rx.el.div(
                rx.cond(
                    MessagingState.is_loading,
                    section_skeleton(),
                    rx.cond(
                        MessagingState.direct_request_count > 0,
                        rx.el.div(
                            rx.foreach(
                                MessagingState.direct_help_requests,
                                helpee_request_card,
                            ),
                            class_name="gah-edge-stack flex flex-col gap-0 w-full",
                        ),
                        hub_empty(
                            "No direct requests waiting",
                            "When someone asks you personally to help with their job, "
                            "it appears here with Accept and Decline.",
                            "hand-helping",
                        ),
                    ),
                ),
                id="inbox-requests",
                class_name="w-full min-w-0 rounded-2xl bg-white shadow-[0_2px_12px_rgba(17,24,39,0.10)]",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def reading_pane(dedicated: bool = False) -> rx.Component:
    """Show the selected job desk or the contact conversation pane."""
    return rx.cond(
        MessagingState.has_selection,
        job_conversation_panel(dedicated),
        contact_conversation_panel(True, dedicated),
    )


def inbox_thread_view() -> rx.Component:
    return rx.el.section(
        rx.el.header(
            back_to_inbox(),
            rx.match(
                UnifiedInboxState.selected_key.split(":")[0],
                (
                    "job",
                    avatar_with_tick(
                        rx.cond(
                            MessagingState.selected_thread["other_avatar"],
                            rx.get_upload_url(
                                MessagingState.selected_thread["other_avatar"]
                            ),
                            animal_avatar(
                                MessagingState.selected_thread[
                                    "other_avatar_seed"
                                ]
                            ),
                        ),
                        MessagingState.selected_thread["other_verified"],
                        "size-12 shrink-0 rounded-full bg-[#fff7e8] object-cover",
                        ui("Member profile photo"),
                        MessagingState.selected_thread["other_id"],
                    ),
                ),
                (
                    "contact",
                    avatar_with_tick(
                        rx.cond(
                            ContactsState.selected_contact["other_avatar"],
                            rx.get_upload_url(
                                ContactsState.selected_contact["other_avatar"]
                            ),
                            animal_avatar(
                                ContactsState.selected_contact[
                                    "other_avatar_seed"
                                ]
                            ),
                        ),
                        ContactsState.selected_contact["other_verified"],
                        "size-12 shrink-0 rounded-full bg-[#fff7e8] object-cover",
                        ui("Member profile photo"),
                        ContactsState.selected_contact["other_id"],
                    ),
                ),
                avatar_with_tick(
                    rx.cond(
                        NonContactMessagingState.selected["other_avatar"],
                        rx.get_upload_url(
                            NonContactMessagingState.selected["other_avatar"]
                        ),
                        animal_avatar(
                            NonContactMessagingState.selected[
                                "other_avatar_seed"
                            ]
                        ),
                    ),
                    NonContactMessagingState.selected["other_verified"],
                    "size-12 shrink-0 rounded-full bg-[#fff7e8] object-cover",
                    ui("Member profile photo"),
                    NonContactMessagingState.selected["other_id"],
                ),
            ),
            rx.el.h2(
                rx.match(
                    UnifiedInboxState.selected_key.split(":")[0],
                    ("job", MessagingState.selected_thread["other_name"]),
                    ("contact", ContactsState.selected_contact["other_name"]),
                    NonContactMessagingState.selected["other_name"],
                ),
                class_name="min-w-0 flex-1 truncate text-lg font-semibold text-[#111827]",
            ),
            remove_from_inbox(UnifiedInboxState.selected_key),
            class_name="flex shrink-0 w-full items-center gap-2 bg-white py-3 sm:gap-3",
        ),
        error_banner(UnifiedInboxState.error),
        rx.el.div(
            reading_pane(True),
            error_banner(job_feedback(MessagingState.error)),
            success_banner(job_feedback(MessagingState.success)),
            error_banner(ContactsState.error),
            success_banner(ContactsState.success),
            error_banner(MessageDeletionState.error),
            success_banner(MessageDeletionState.success),
            id="gah-thread-history",
            role="region",
            aria_label=ui("Conversation history and actions"),
            tab_index=0,
            class_name="gah-screen-scroll flex-1 min-h-0 w-full min-w-0 overflow-y-auto overscroll-contain pb-4 bg-white",
        ),
        rx.el.div(
            rx.match(
                UnifiedInboxState.selected_key.split(":")[0],
                (
                    "job",
                    rx.cond(
                        MessagingState.has_selection, composer(), rx.fragment()
                    ),
                ),
                (
                    "contact",
                    rx.cond(
                        ContactsState.can_message_selected,
                        contact_composer(),
                        rx.fragment(),
                    ),
                ),
                rx.cond(
                    NonContactMessagingState.has_selection,
                    reply_composer(),
                    rx.fragment(),
                ),
            ),
            class_name="shrink-0 w-full min-w-0 bg-white pt-2 pb-3",
        ),
        id="gah-inbox-thread",
        aria_label=ui("Inbox conversation"),
        on_mount=rx.call_script("""
            window.gahThreadCleanup?.();
            const frame = document.getElementById('gah-inbox-thread');
            const viewport = window.visualViewport;
            const sync = () => {
                if (!frame) return;
                const dock = document.querySelector('.gah-bottom-dock');
                const height = viewport?.height ?? window.innerHeight;
                frame.style.top = `${viewport?.offsetTop ?? 0}px`;
                frame.style.height = `${Math.max(0, height - (dock?.getBoundingClientRect().height ?? 64) - 12)}px`;
            };
            sync();
            viewport?.addEventListener('resize', sync);
            viewport?.addEventListener('scroll', sync);
            window.addEventListener('resize', sync);
            window.gahThreadCleanup = () => {
                viewport?.removeEventListener('resize', sync);
                viewport?.removeEventListener('scroll', sync);
                window.removeEventListener('resize', sync);
            };
        """),
        on_unmount=[
            rx.call_script(
                "window.gahThreadCleanup?.(); delete window.gahThreadCleanup;"
            ),
            MessageAttachmentState.clear_pending,
        ],
        class_name="fixed top-0 left-0 right-0 z-40 flex h-[calc(100dvh-5rem-env(safe-area-inset-bottom))] w-full min-w-0 flex-col overflow-hidden bg-white px-4 sm:px-6 text-[#111827]",
    )


def conversation_column() -> rx.Component:
    return rx.el.div(
        unified_conversation_list(reading_pane()),
        class_name="flex flex-col gap-4 w-full min-w-0 bg-transparent",
    )


def messages_block() -> rx.Component:
    return rx.el.section(
        conversation_column(),
        id="inbox-messages",
        class_name="flex w-full flex-col gap-3",
    )


def messages_panel() -> rx.Component:
    return rx.el.div(
        rx.match(
            UnifiedInboxState.view,
            ("compose", compose_area()),
            ("contacts", inbox_contacts_view()),
            ("thread", inbox_thread_view()),
            rx.fragment(
                inbox_header(),
                messages_block(),
            ),
        ),
        error_banner(job_feedback(MessagingState.error)),
        success_banner(job_feedback(MessagingState.success)),
        error_banner(MessageDeletionState.error),
        success_banner(MessageDeletionState.success),
        on_mount=[
            UnifiedInboxState.reset_disclosures,
            MessagingState.load_threads,
            ContactsState.load_contacts,
            NonContactMessagingState.load_conversations,
            HelpHubState.load_help_hub,
        ],
        class_name="flex flex-col gap-2 w-full",
    )
