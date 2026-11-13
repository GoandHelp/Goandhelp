import reflex as rx
from app.avatars import member_avatar

from app.interface_i18n import ui
from app.components.feedback import verified_badge
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState


SIGNED_IN_NAV: list[dict[str, str]] = [
    {"value": "post", "label": "Ask for help", "icon": "hand-helping"},
    {"value": "people", "label": "Find people", "icon": "user-round"},
    {"value": "contacts", "label": "Contacts", "icon": "users-round"},
    {"value": "details", "label": "Profile details", "icon": "notebook-pen"},
    {"value": "area", "label": "Local area", "icon": "map-pin"},
    {"value": "activity", "label": "Activity", "icon": "chart-line"},
    {"value": "admin", "label": "Backend", "icon": "monitor"},
]


def signed_in_nav_item(item: dict[str, str]) -> rx.Component:
    return rx.menu.item(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-4 w-4 shrink-0"),
            rx.el.span(
                ui(item["label"]), class_name="min-w-0 flex-1 text-left"
            ),
            rx.cond(
                ProfileState.active_tab == item["value"],
                rx.el.span(
                    rx.icon("check", class_name="h-3.5 w-3.5"),
                    class_name="flex items-center justify-center size-5 rounded-full bg-[#fff7e8] text-[#e08b12]",
                ),
                rx.el.span(class_name="size-5"),
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        on_click=lambda: ProfileState.set_active_tab(item["value"]),
        class_name=rx.cond(
            ProfileState.active_tab == item["value"],
            "w-full rounded-xl bg-[#fff7e8] px-3 py-2.5 text-sm font-semibold text-[#111827]",
            "w-full rounded-xl px-3 py-2.5 text-sm font-semibold text-[#4b5563] transition-colors hover:bg-[#fff7e8] hover:text-[#e08b12]",
        ),
    )


def signed_in_nav_menu() -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.el.button(
                rx.icon("menu", class_name="h-4 w-4 stroke-[#111827]"),
                type="button",
                title="Open section menu",
                aria_label="Open section menu",
                class_name="flex size-10 shrink-0 items-center justify-center rounded-full border border-[#d4d4d4] bg-[#fff7e8] text-[#111827] transition-colors hover:bg-[#fff7e8]",
            )
        ),
        rx.menu.content(
            rx.el.div(
                rx.el.p(
                    "Go and Help sections",
                    class_name="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#4b5563]",
                ),
                rx.foreach(SIGNED_IN_NAV, signed_in_nav_item),
                class_name="flex flex-col gap-1",
            ),
            side="bottom",
            align="end",
            side_offset=0,
            class_name="z-50 min-w-64 rounded-2xl border border-[#f6c66f] bg-[#ffffff] p-2",
        ),
    )


# One shared brand geometry for every surface: 44px on mobile, 48px from sm.
BRAND_LOGO_SRC = "/GO%20AND%20HELP%20LOGO.png"
BRAND_LOGO_ALT = (
    "Go and Help logo: a circular multicolour community helping-hands emblem"
)
BRAND_MARK_CLASS = "size-11 sm:size-12 shrink-0 rounded-full object-contain"
# Interior gradient; solid orange over the immersive map.
BRAND_TEXT_CLASS = "text-lg font-bold tracking-tight bg-linear-to-r from-[#23de49] to-[#fba922] bg-clip-text text-transparent leading-tight text-left"
MAP_BRAND_TEXT_CLASS = (
    "text-lg font-bold tracking-tight text-[#fba922] leading-tight text-left"
)
# Top-left anchor for map overlays, matched to the header's px-4 sm:px-6 pad.
BRAND_MAP_POSITION = "absolute left-4 top-3 z-40 sm:left-6"
# Black page titles in the top right of every non-map page. The small
# top margin drops the label a few pixels so its baseline reads level with the
# "Community in your hands" slogan under the word-mark.
PAGE_TITLE_CLASS = (
    "shrink-0 text-right text-lg font-semibold tracking-tight "
    "text-[#111827] leading-tight"
)
PAGE_TITLE_ICON_CLASS = "h-5 w-5 shrink-0 text-[#111827]"


def page_title_icon() -> rx.Component:
    """The matching bottom-navigation glyph, immediately left of the title."""
    return rx.match(
        ProfileState.active_tab,
        (
            "profile",
            rx.icon(
                "circle-user-round",
                class_name=PAGE_TITLE_ICON_CLASS,
            ),
        ),
        (
            "help",
            rx.icon(
                "heart-handshake",
                class_name="h-5 w-5 shrink-0 -translate-y-[1px] text-[#404040]",
            ),
        ),
        (
            "upcoming",
            rx.icon(
                "heart-handshake",
                class_name="h-5 w-5 shrink-0 -translate-y-[1px] text-[#404040]",
            ),
        ),
        (
            "get_help",
            rx.icon(
                "heart-handshake",
                class_name="h-5 w-5 shrink-0 -translate-y-[1px] text-[#404040]",
            ),
        ),
        ("community", rx.icon("users-round", class_name=PAGE_TITLE_ICON_CLASS)),
        (
            "inbox",
            rx.icon(
                "mail",
                class_name="h-5 w-5 shrink-0 -translate-y-[2px] text-[#111827]",
            ),
        ),
        rx.fragment(),
    )


def page_title_block() -> rx.Component:
    """One identical, responsive title treatment for all four dock pages."""
    return rx.el.div(
        page_title_icon(),
        rx.el.p(ui(ProfileState.active_tab_label), class_name=PAGE_TITLE_CLASS),
        class_name="mr-[10px] flex shrink-0 items-center gap-2 self-center",
    )


def brand_mark(class_name: str = BRAND_MARK_CLASS) -> rx.Component:
    """The real circular company logo, shared by every member header."""
    return rx.image(
        src=BRAND_LOGO_SRC,
        alt=BRAND_LOGO_ALT,
        class_name=class_name,
    )


def account_badge() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                AuthState.display_name,
                class_name="text-right text-sm font-semibold text-[#111827] leading-tight truncate pr-2",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("hand-helping", class_name="h-3 w-3"),
                    f"given {ProfileState.stats['tasks_helped']}",
                    class_name="w-fit flex items-center gap-1 rounded-full bg-[#fff7e8] px-2 py-0.5 text-[11px] font-semibold text-[#e08b12] whitespace-nowrap",
                ),
                rx.el.span(
                    rx.icon("gift", class_name="h-3 w-3"),
                    f"received {ProfileState.stats['tasks_received']}",
                    class_name="w-fit flex items-center gap-1 rounded-full bg-[#fff7e8] px-2 py-0.5 text-[11px] font-semibold text-[#4b5563] whitespace-nowrap",
                ),
                class_name="flex flex-wrap items-center justify-end gap-1.5 mt-0.5",
            ),
            class_name="hidden min-w-0 flex-col items-end lg:flex",
        ),
        rx.el.button(
            rx.el.div(
                rx.image(
                    src=member_avatar(
                        ProfileState.avatar_path,
                        f"member-{AuthState.subscriber_id}",
                    ),
                    alt="Your profile photo",
                    class_name="size-10 rounded-full bg-[#fff7e8] shrink-0",
                ),
                verified_badge(AuthState.is_verified),
                class_name="relative w-fit shrink-0",
            ),
            type="button",
            title="Open profile details",
            aria_label="Open profile details",
            on_click=lambda: ProfileState.set_active_tab("details"),
            class_name="flex size-10 shrink-0 items-center justify-center rounded-full transition-transform hover:scale-105 focus:outline-hidden focus:ring-2 focus:ring-[#e08b12]",
        ),
        class_name="flex min-w-0 items-center gap-2 sm:gap-3",
    )


def sign_out_button() -> rx.Component:
    return rx.el.button(
        rx.icon("log-out", class_name="h-4 w-4"),
        type="button",
        title=ui("Sign out"),
        aria_label=ui("Sign out"),
        on_click=AuthState.sign_out,
        class_name="flex items-center justify-center size-10 rounded-full border border-[#fba922] bg-[#fba922] text-black transition-colors hover:bg-[#e08b12] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
    )


CONTEXTUAL_SCREENS: list[str] = [
    "profile",
    "help",
    "upcoming",
    "get_help",
    "community",
    "inbox",
]


def minimal_header() -> rx.Component:
    """Shared brand-only header for My Profile, Help, Community and Inbox.

    Just the real logo, the name and the slogan — every part of it returns to
    the map. No avatar, mail icon, section menu, sign-out control or divider.
    """
    return rx.el.header(
        rx.el.div(
            rx.el.button(
                brand_mark(),
                rx.el.div(
                    rx.el.p(
                        "Go and Help",
                        class_name=BRAND_TEXT_CLASS,
                    ),
                    rx.el.p(
                        ui("Community in your hands"),
                        class_name="hidden min-[400px]:block text-xs font-medium text-[#404040] text-left",
                    ),
                    class_name="min-w-0",
                ),
                type="button",
                title="Go and Help — back to the map",
                aria_label="Go and Help — back to the map",
                on_click=ProfileState.return_to_map,
                class_name="gah-brand-home flex min-w-0 flex-1 items-center gap-3 rounded-none border-0 bg-transparent shadow-none transition-opacity hover:opacity-90 focus:outline-hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12]",
            ),
            page_title_block(),
            class_name="w-full max-w-[100rem] mx-auto px-4 sm:px-6 py-3 flex items-start justify-between gap-3 sm:gap-4",
        ),
        class_name=rx.cond(
            ProfileState.active_tab == "community",
            "gah-community-context-header w-full bg-white sticky top-0 z-40 after:content-[''] after:absolute after:inset-x-0 after:top-full after:h-3 after:pointer-events-none after:bg-white",
            "w-full bg-white/20 backdrop-blur-sm sticky top-0 z-40 after:content-[''] after:absolute after:inset-x-0 after:top-full after:h-3 after:pointer-events-none after:bg-white/20 after:backdrop-blur-sm after:[mask-image:linear-gradient(to_bottom,black,transparent)]",
        ),
    )


def contextual_header():
    """Fuller header everywhere except Help, Community and Inbox."""
    return rx.match(
        ProfileState.active_tab,
        ("profile", minimal_header()),
        ("help", minimal_header()),
        ("upcoming", minimal_header()),
        ("get_help", minimal_header()),
        ("community", minimal_header()),
        ("inbox", minimal_header()),
        header(member_context=True),
    )


def header(member_context: bool = False) -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.button(
                brand_mark(),
                rx.el.div(
                    rx.el.p(
                        rx.el.span("Goandhelp", class_name="sm:hidden"),
                        rx.el.span(
                            "Go and Help", class_name="hidden sm:inline"
                        ),
                        class_name=BRAND_TEXT_CLASS,
                    ),
                    rx.el.p(
                        ui("Community in your hands"),
                        class_name="text-xs font-medium text-[#404040] text-left",
                    ),
                    class_name="min-w-0",
                ),
                type="button",
                title="Go and Help — back to the map",
                aria_label="Go and Help — back to the map",
                on_click=ProfileState.return_to_map,
                class_name="gah-brand-home flex items-center gap-3 rounded-none border-0 bg-transparent shadow-none transition-opacity hover:opacity-90 focus:outline-hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12]",
            ),
            rx.cond(
                AuthState.is_signed_in,
                rx.el.div(
                    account_badge(),
                    rx.el.button(
                        rx.icon("mail", class_name="h-4 w-4 stroke-[#111827]"),
                        type="button",
                        title="Open messages",
                        aria_label="Open messages",
                        on_click=lambda: ProfileState.set_active_tab(
                            "messages"
                        ),
                        class_name="flex size-10 items-center justify-center rounded-full border border-[#f6c66f] bg-[#fff7e8] text-[#111827] transition-colors hover:bg-[#fff7e8]",
                    ),
                    signed_in_nav_menu(),
                    sign_out_button(),
                    class_name="flex min-w-0 items-center gap-1.5 sm:gap-2",
                ),
                rx.el.div(
                    rx.el.span(
                        rx.icon("map", class_name="h-3.5 w-3.5"),
                        "Sign up & start helping",
                        class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#e08b12]",
                    ),
                    class_name="flex items-center gap-2",
                ),
            ),
            class_name="w-full max-w-[100rem] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4",
        ),
        class_name=rx.cond(
            member_context,
            "w-full bg-white/20 backdrop-blur-sm sticky top-0 z-40 after:content-[''] after:absolute after:inset-x-0 after:top-full after:h-3 after:pointer-events-none after:bg-white/20 after:backdrop-blur-sm after:[mask-image:linear-gradient(to_bottom,black,transparent)]",
            "w-full bg-[#ffffff]/90 backdrop-blur-sm sticky top-0 z-40 after:content-[''] after:absolute after:inset-x-0 after:top-full after:h-3 after:pointer-events-none after:bg-white/90 after:backdrop-blur-sm after:[mask-image:linear-gradient(to_bottom,black,transparent)]",
        ),
    )
