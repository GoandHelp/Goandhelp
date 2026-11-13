import reflex as rx
from app.avatars import animal_avatar

from app.interface_i18n import ui
from app.components.notification_badge import activity_dot
from app.states.auth_state import AuthState
from app.states.notification_state import NotificationState
from app.states.profile_state import ProfileState


from app.components.header import BRAND_LOGO_SRC, BRAND_LOGO_ALT

LOGO_SRC = BRAND_LOGO_SRC

# Compact icon-only dock: no labels, just the icon slot centred in the column.
ITEM_BASE = (
    "gah-dock-control gah-nav-item flex w-full min-w-0 mx-auto flex-col "
    "items-center justify-center gap-0 rounded-xl px-0.5 "
    "h-[3.25rem] select-none transition-colors focus:outline-hidden "
    "border-0 shadow-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#fba922]"
)
ITEM_ACTIVE = f"{ITEM_BASE} bg-transparent text-[#fba922]"
ITEM_IDLE = f"{ITEM_BASE} bg-transparent text-[#404040] hover:text-[#404040]"


def is_active(value: str) -> rx.Var[bool]:
    return AuthState.is_signed_in & (ProfileState.active_tab == value)


def nav_button(
    value: str,
    label: str,
    icon: str,
    reason: str,
    unread: rx.Var[int] | int = 0,
    tour_target: str = "",
) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon(
                icon,
                stroke_width=1.75,
                class_name="h-[33px] w-[33px] shrink-0",
            ),
            activity_dot(unread),
            class_name="relative flex h-[33px] w-[33px] items-center justify-center",
        ),
        type="button",
        title=ui(label),
        aria_label=ui(label),
        aria_current=rx.cond(is_active(value), "page", "false"),
        on_click=ProfileState.navigate_from_bottom_nav(value, reason),
        custom_attrs={"data-tour-target": f"{tour_target}{value}"},
        class_name=rx.cond(is_active(value), ITEM_ACTIVE, ITEM_IDLE),
    )


def profile_button() -> rx.Component:
    return rx.el.button(
        rx.el.span(
            activity_dot(NotificationState.reviews_unread),
            rx.cond(
                AuthState.is_signed_in,
                rx.image(
                    src=rx.cond(
                        ProfileState.avatar_path,
                        rx.get_upload_url(ProfileState.avatar_path),
                        animal_avatar(ProfileState.avatar_seed),
                    ),
                    alt="Your profile photo",
                    class_name=rx.cond(
                        ProfileState.active_tab == "profile",
                        "size-[36px] min-w-[36px] min-h-[36px] aspect-square rounded-full bg-white border-0 outline outline-1 outline-offset-2 outline-[#fba922] object-cover shrink-0",
                        "size-[36px] min-w-[36px] min-h-[36px] aspect-square rounded-full bg-white border-0 object-cover shrink-0",
                    ),
                ),
                rx.icon(
                    "circle-user-round",
                    stroke_width=1.75,
                    class_name="h-[36px] w-[36px] shrink-0",
                ),
            ),
            class_name="gah-profile-avatar-slot relative flex size-[36px] min-w-[36px] min-h-[36px] aspect-square shrink-0 rounded-full overflow-visible items-center justify-center",
        ),
        type="button",
        title=ui("Profile"),
        aria_label=ui("Profile"),
        aria_current=rx.cond(is_active("profile"), "page", "false"),
        on_click=ProfileState.navigate_from_bottom_nav("profile", ""),
        custom_attrs={"data-tour-target": "profile"},
        class_name=rx.cond(is_active("profile"), ITEM_ACTIVE, ITEM_IDLE),
    )


def logo_button() -> rx.Component:
    """Raised circular centrepiece that always returns to the map.

    The reserved icon slot stays aligned with the other dock icons while the
    logo itself is drawn raised above the dock.
    """
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                rx.image(
                    src=LOGO_SRC,
                    alt=BRAND_LOGO_ALT,
                    class_name="size-[59px] rounded-full border-[3px] border-white object-contain",
                ),
                type="button",
                title=ui("Map"),
                aria_label=ui("Map"),
                on_click=ProfileState.return_to_map,
                class_name="gah-dock-control absolute bottom-[-3px] left-1/2 -translate-x-1/2 z-10 flex size-[59px] items-center justify-center bg-transparent transition-transform hover:scale-105 focus:outline-hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#fba922]",
            ),
            style={"overflow": "visible"},
            class_name="relative h-[33px] w-[33px] shrink-0",
        ),
        style={"overflow": "visible"},
        class_name="flex w-full min-w-0 mx-auto h-[3.25rem] flex-col items-center justify-center gap-0 px-0.5 text-[#e08b12]",
    )


def bottom_nav() -> rx.Component:
    """Five equal columns, so the logo/Map control is the true visual centre."""
    return rx.el.nav(
        rx.el.div(
            profile_button(),
            nav_button(
                "help",
                "Requests",
                "heart-handshake",
                "",
                NotificationState.help_unread,
            ),
            logo_button(),
            nav_button(
                "community",
                "Community",
                "users-round",
                "",
                NotificationState.community_unread,
            ),
            nav_button(
                "inbox",
                "Inbox",
                "mail",
                "",
                NotificationState.inbox_unread,
            ),
            class_name="grid w-full max-w-full min-[751px]:max-w-[620px] mx-auto grid-cols-5 items-center gap-0 px-1",
            style={"overflow": "visible"},
        ),
        on_mount=NotificationState.load_notifications,
        aria_label="Go and Help main navigation",
        class_name="gah-bottom-dock fixed bottom-0 left-0 right-0 z-50 w-full border-0 bg-white pt-1 pb-[calc(0.375rem+env(safe-area-inset-bottom))]",
    )
