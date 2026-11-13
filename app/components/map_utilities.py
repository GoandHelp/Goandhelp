import reflex as rx
from app.avatars import animal_avatar

from app.interface_i18n import ui
from app.components.profile_tabs import settings_content
from app.states.profile_state import ProfileState
from app.states.notification_state import NotificationItem, NotificationState


SHEET_CLASS = "pointer-events-auto fixed top-0 right-0 z-40 flex w-full max-w-[22rem] sm:max-w-[26rem] max-h-[calc(100dvh-3.875rem-1px-env(safe-area-inset-bottom))] flex-col overflow-hidden rounded-tl-none rounded-tr-none rounded-br-none rounded-bl-2xl border-l border-t border-[#f7d9a0] bg-white/60 text-[#111827] backdrop-blur-md"


def sheet_header(title: str, close: rx.event.EventType) -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            rx.cond(
                title == "Notifications",
                rx.icon("bell", class_name="size-5 shrink-0 text-[#fba922]"),
                rx.fragment(),
            ),
            ui(title),
            class_name="flex items-center gap-2 text-lg font-bold text-[#111827]",
        ),
        rx.el.button(
            rx.icon("x", class_name="size-4"),
            type="button",
            aria_label=f"{ui('Close')} — {ui(title)}",
            on_click=close,
            class_name="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#e08b12] text-white hover:bg-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        class_name="relative z-10 flex shrink-0 items-center justify-between gap-3 bg-transparent px-3.5 py-3.5",
    )


def notification_row(item: NotificationItem) -> rx.Component:
    return rx.el.li(
        rx.el.button(
            rx.image(
                src=rx.cond(
                    item["actor_avatar"],
                    rx.get_upload_url(item["actor_avatar"]),
                    animal_avatar(item["actor_seed"]),
                ),
                alt=item["actor_name"],
                class_name="size-10 shrink-0 rounded-full bg-[#fff7e8] object-cover",
            ),
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="mt-1 break-words text-sm font-bold text-[#111827]",
                ),
                rx.el.p(
                    item["created"],
                    class_name="mt-2 text-[11px] text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            type="button",
            aria_label=item["title"],
            on_click=NotificationState.open_notification(item),
            disabled=NotificationState.action_id == item["id"],
            class_name="gah-conversation-toggle flex min-w-0 flex-1 items-start gap-2.5 bg-transparent text-left focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="size-4"),
            type="button",
            aria_label="Delete notification",
            on_click=NotificationState.delete_notification(item["id"]),
            disabled=NotificationState.action_id == item["id"],
            class_name="gah-conversation-toggle flex size-9 shrink-0 items-center justify-center rounded-full bg-transparent text-[#b86e08] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        key=item["id"],
        class_name=rx.cond(
            item["is_read"],
            "flex w-full items-start gap-2 bg-white p-3",
            "flex w-full items-start gap-2 bg-[#fff7e8] p-3",
        ),
    )


def field_notification_row() -> rx.Component:
    return rx.el.li(
        rx.el.button(
            rx.el.span(
                rx.icon("hand-helping", class_name="size-5"),
                class_name="flex size-10 shrink-0 items-center justify-center rounded-full bg-white text-[#e08b12]",
            ),
            rx.el.div(
                rx.el.p(
                    f"{ui('Requests in my field')} ({NotificationState.field_unread})",
                    class_name="text-sm font-bold text-[#111827]",
                ),
                rx.el.p(
                    ui("View matching requests"),
                    class_name="mt-1 text-xs font-medium text-[#b86e08]",
                ),
                rx.el.p(
                    NotificationState.field_created,
                    class_name="mt-2 text-xs text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            type="button",
            on_click=NotificationState.open_field_group,
            disabled=NotificationState.action_id != 0,
            aria_label=f"{ui('View matching requests')} ({NotificationState.field_unread})",
            class_name="gah-conversation-toggle flex min-w-0 flex-1 items-start gap-2.5 bg-transparent text-left focus-visible:ring-2 focus-visible:ring-[#fba922] disabled:opacity-60",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="size-4"),
            type="button",
            aria_label="Delete grouped requests in my field notification",
            on_click=NotificationState.delete_field_group,
            disabled=NotificationState.action_id != 0,
            class_name="gah-conversation-toggle flex size-9 shrink-0 items-center justify-center rounded-full bg-transparent text-[#b86e08] hover:bg-white focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        class_name="flex w-full items-start gap-2 border border-[#f7d9a0] bg-[#fff7e8] p-3",
    )


def notification_feed() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                ui("Recent activity"),
                class_name="text-xs font-semibold text-[#4b5563]",
            ),
            rx.el.button(
                ui("Mark all read"),
                type="button",
                on_click=NotificationState.mark_all_read,
                disabled=(NotificationState.total_unread == 0)
                | NotificationState.read_busy
                | NotificationState.is_loading,
                class_name="min-h-9 rounded-full bg-[#fba922] px-3 text-xs font-bold text-black hover:bg-[#e08b12] disabled:opacity-50",
            ),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.cond(
            NotificationState.error != "",
            rx.el.div(
                rx.el.p(
                    NotificationState.error,
                    role="alert",
                    class_name="text-xs text-[#b86e08]",
                ),
                rx.el.button(
                    ui("Try again"),
                    type="button",
                    on_click=NotificationState.load_notifications,
                    class_name="mt-2 rounded-full bg-[#e08b12] px-3 py-2 text-xs font-bold text-white",
                ),
                class_name="rounded-xl border border-[#c3d9ff] bg-[#fff7e8] p-3",
            ),
            rx.fragment(),
        ),
        rx.cond(
            NotificationState.is_loading,
            rx.el.div(
                rx.icon(
                    "loader-circle",
                    class_name="size-4 animate-spin text-[#e08b12]",
                ),
                ui("Loading notifications…"),
                role="status",
                class_name="flex items-center gap-2 py-6 text-sm text-[#4b5563]",
            ),
            rx.cond(
                NotificationState.has_notifications,
                rx.el.ul(
                    rx.cond(
                        NotificationState.field_unread > 0,
                        field_notification_row(),
                        rx.fragment(),
                    ),
                    rx.foreach(NotificationState.recent, notification_row),
                    class_name="gah-edge-stack flex w-full flex-col gap-0 overflow-hidden",
                ),
                rx.cond(
                    NotificationState.error == "",
                    rx.el.div(
                        rx.icon("bell", class_name="size-6 text-[#fba922]"),
                        rx.el.p(
                            ui("No notifications yet"),
                            class_name="text-sm font-bold text-[#111827]",
                        ),
                        rx.el.p(
                            ui(
                                "New activity matching your preferences will appear here."
                            ),
                            class_name="text-xs text-[#4b5563]",
                        ),
                        class_name="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-[#f7d9a0] bg-white px-4 py-8 text-center",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        class_name="flex flex-col gap-3",
    )


def map_utility_sheets() -> rx.Component:
    return rx.fragment(
        rx.cond(
            ProfileState.settings_open,
            rx.el.section(
                sheet_header("Settings", NotificationState.toggle_map_settings),
                rx.el.div(
                    settings_content(),
                    class_name="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3.5 pt-3 pb-6",
                ),
                role="dialog",
                aria_label=ui("Settings"),
                id="map-settings-sheet",
                class_name=SHEET_CLASS,
            ),
            rx.fragment(),
        ),
        rx.cond(
            NotificationState.panel_open,
            rx.el.section(
                sheet_header("Notifications", NotificationState.close_panel),
                rx.el.div(
                    notification_feed(),
                    class_name="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3.5 pt-3 pb-3.5",
                ),
                role="dialog",
                aria_label=ui("Notifications"),
                id="map-notifications-sheet",
                class_name=SHEET_CLASS,
            ),
            rx.fragment(),
        ),
    )
