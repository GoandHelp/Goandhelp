import reflex as rx

from app.components.report_dialog import report_button

COMPOSER_CLASS = "gah-chat-composer relative shrink-0 w-full min-w-0 rounded-xl bg-white shadow-[0_0_10px_rgba(17,24,39,0.12)]"
MESSAGE_INPUT_CLASS = "block w-full min-w-0 min-h-24 max-h-40 [field-sizing:content] resize-none rounded-xl border-0 bg-white px-3 pt-3 pb-16 text-sm leading-relaxed text-black placeholder:text-[#4b5563] outline-hidden"
SEND_CLASS = "absolute bottom-2 right-2 shrink-0 rounded-xl border border-gray-200 bg-[#fba922] px-3 py-2.5 text-sm font-semibold text-black hover:bg-[#e08b12] disabled:opacity-60 focus-visible:ring-2 focus-visible:ring-[#e08b12]"
HISTORY_CLASS = "gah-screen-scroll w-full min-w-0 bg-white"


def _normalize_message(
    msg: dict[str, str | int | bool | list[str]]
    | rx.Var[dict[str, str | int | bool | list[str]]],
) -> rx.Var[dict[str, str | int | bool | list[str]]]:
    if isinstance(msg, dict):
        return rx.Var.create({**{"photos": []}, **msg})
    return msg


def correspondence_bubble(
    msg: dict[str, str | int | bool | list[str]]
    | rx.Var[dict[str, str | int | bool | list[str]]],
    target: str = "",
    delete_event: rx.event.EventType = rx.noop,
) -> rx.Component:
    return _correspondence_bubble(_normalize_message(msg), target, delete_event)


def _correspondence_bubble(
    msg: rx.Var[dict[str, str | int | bool | list[str]]],
    target: str,
    delete_event: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.cond(
                msg["body"].to(str) != "",
                rx.el.p(
                    msg["body"].to(str),
                    dir="auto",
                    custom_attrs={"translate": "yes"},
                    class_name="w-full min-w-0 whitespace-pre-wrap break-words [overflow-wrap:anywhere] text-sm leading-relaxed text-[#111827]",
                ),
                rx.fragment(),
            ),
            rx.el.div(
                rx.foreach(
                    msg["photos"].to(list[str]),
                    lambda photo, index: rx.el.a(
                        rx.el.img(
                            src=rx.get_upload_url(photo),
                            alt=f"Message photo {index + 1}",
                            loading="lazy",
                            class_name="h-auto max-h-48 w-full rounded-xl bg-white object-contain sm:max-h-64",
                        ),
                        href=rx.get_upload_url(photo),
                        target="_blank",
                        rel="noopener noreferrer",
                        aria_label=f"Open message photo {index + 1} at full size in a new tab",
                        class_name="block w-full min-w-0 rounded-xl text-[#111827] focus-visible:ring-2 focus-visible:ring-[#fba922]",
                    ),
                ),
                class_name="flex w-full min-w-0 max-w-sm flex-col gap-2",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("trash-2", class_name="size-3"),
                    type="button",
                    aria_label="Delete message",
                    on_click=delete_event,
                    class_name="flex size-11 shrink-0 items-center justify-center rounded-full bg-white text-[#b86e08] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                rx.cond(
                    msg["mine"].to(bool) | (target == ""),
                    rx.fragment(),
                    report_button(
                        target,
                        msg["id"].to(int),
                        msg["body"].to(str),
                        "Report message",
                    ),
                ),
                class_name="clear-both mt-1 flex w-full min-w-0 flex-wrap items-center justify-end gap-1 [&_button]:text-xs",
            ),
            class_name=rx.cond(
                msg["mine"].to(bool),
                "w-fit max-w-[85%] min-w-0 break-words [overflow-wrap:anywhere] rounded-2xl rounded-br-sm bg-[#fff0d6] px-3 py-2 text-left text-black shadow-[0_2px_4px_rgba(17,24,39,0.10)]",
                "w-fit max-w-[85%] min-w-0 break-words [overflow-wrap:anywhere] rounded-2xl rounded-bl-sm bg-[#eaf2ff] px-3 py-2 text-left text-black shadow-[0_2px_4px_rgba(17,24,39,0.10)]",
            ),
        ),
        rx.el.span(
            msg["sent_at"].to(str),
            class_name=rx.cond(
                msg["mine"].to(bool),
                "gah-message-time mt-1 max-w-full whitespace-normal break-words text-right text-xs text-[#4b5563]",
                "gah-message-time mt-1 max-w-full text-left text-xs text-[#4b5563]",
            ),
        ),
        class_name=rx.cond(
            msg["mine"].to(bool),
            "flex flex-col items-end w-full min-w-0 bg-white",
            "flex flex-col items-start w-full bg-white",
        ),
    )
