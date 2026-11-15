"""The compact cobalt/cream bookmark corner tab used on request cards.

It is always rendered as a SIBLING of the card's own button — never inside it —
so a tap saves the request without opening it, and no invalid nested button is
produced.
"""

import reflex as rx

from app.states.bookmark_state import BookmarkState
from app.interface_i18n import ui_template

TAB_BASE = (
    "flex size-7 items-center justify-center rounded-lg rounded-tr-2xl "
    "border transition-colors duration-150 focus:outline-hidden "
    "focus-visible:ring-2 focus-visible:ring-[#e08b12]"
)
TAB_SAVED = (
    f"{TAB_BASE} border-[#fba922] bg-[#fba922] text-black hover:bg-[#e08b12]"
)
TAB_IDLE = (
    f"{TAB_BASE} border-[#d4d4d4] bg-[#ffffff] text-[#e08b12] "
    "hover:border-[#e08b12] hover:bg-[#fff7e8]"
)


def bookmark_tab(
    post_id: rx.Var[int],
    title: rx.Var[str],
    position: str = "absolute right-2 top-2 z-20",
) -> rx.Component:
    """A small accessible save tab for one help request."""
    saved = BookmarkState.bookmarked_ids.contains(post_id)
    return rx.el.button(
        rx.icon(
            "bookmark",
            class_name=rx.cond(
                saved,
                "h-3.5 w-3.5 fill-current",
                "h-3.5 w-3.5",
            ),
        ),
        type="button",
        title=rx.cond(
            saved,
            ui_template(
                "Remove {title} from your saved help requests", "title", title
            ),
            ui_template("Save {title} to your help requests", "title", title),
        ),
        aria_label=rx.cond(
            saved,
            ui_template(
                "Remove {title} from your saved help requests", "title", title
            ),
            ui_template("Save {title} to your help requests", "title", title),
        ),
        aria_pressed=rx.cond(saved, "true", "false"),
        on_click=lambda: BookmarkState.toggle_bookmark(post_id),
        class_name=rx.cond(
            saved,
            f"{position} {TAB_SAVED}",
            f"{position} {TAB_IDLE}",
        ),
    )
