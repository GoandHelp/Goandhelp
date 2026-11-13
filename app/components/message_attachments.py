import reflex as rx

from app.states.message_attachment_state import MessageAttachmentState


def pending_photo(path: rx.Var[str], index: rx.Var[int]) -> rx.Component:
    return rx.el.div(
        rx.el.img(
            src=rx.get_upload_url(path),
            alt=f"Pending message photo {index + 1}",
            class_name="size-16 rounded-xl bg-[#fff7e8] object-cover",
        ),
        rx.el.button(
            rx.icon("x", class_name="size-4"),
            type="button",
            aria_label=f"Remove pending photo {index + 1}",
            on_click=MessageAttachmentState.remove_photo(path),
            disabled=MessageAttachmentState.busy,
            class_name="absolute -right-1 -top-1 flex size-8 items-center justify-center rounded-full bg-white text-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        key=path,
        class_name="relative shrink-0",
    )


def message_attachments() -> rx.Component:
    return rx.el.div(
        rx.cond(
            MessageAttachmentState.pending.length() > 0,
            rx.el.div(
                rx.foreach(MessageAttachmentState.pending, pending_photo),
                aria_label="Pending photo attachments",
                class_name="flex max-h-24 w-full min-w-0 gap-3 overflow-x-auto px-1 pt-2 pb-1",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.upload.root(
                rx.el.span(
                    rx.icon("paperclip", class_name="size-4"),
                    rx.cond(
                        MessageAttachmentState.busy,
                        "Attaching…",
                        "Attach photos",
                    ),
                    class_name="flex items-center gap-1.5 text-sm font-semibold text-[#e08b12]",
                ),
                id="inbox_message_photos",
                accept={
                    "image/jpeg": [".jpg", ".jpeg"],
                    "image/png": [".png"],
                    "image/webp": [".webp"],
                },
                multiple=True,
                max_files=5,
                max_size=3_000_000,
                disabled=MessageAttachmentState.busy
                | (MessageAttachmentState.pending.length() >= 5),
                on_drop=MessageAttachmentState.upload_photos(
                    rx.upload_files(upload_id="inbox_message_photos")
                ),
                aria_label="Attach photos: JPEG, PNG or WebP, up to five, 3 MB each",
                class_name="w-fit cursor-pointer rounded-xl bg-white px-2 py-2 text-[#e08b12] focus-within:ring-2 focus-within:ring-[#fba922]",
            ),
            rx.el.span(
                f"{MessageAttachmentState.pending.length()}/5",
                aria_live="polite",
                class_name="text-xs text-[#4b5563]",
            ),
            class_name="flex w-full items-center gap-1 pr-24",
        ),
        rx.cond(
            MessageAttachmentState.error,
            rx.el.p(
                MessageAttachmentState.error,
                role="alert",
                class_name="px-2 pb-2 text-sm text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        class_name="w-full min-w-0 bg-white px-2 pb-2 text-[#111827]",
    )
