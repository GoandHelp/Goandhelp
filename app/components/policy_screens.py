"""Full-screen handbook and policy reader, styled like a travel handbook."""

import reflex as rx

from app.components.header import BRAND_LOGO_SRC, BRAND_LOGO_ALT
from app.interface_i18n import ui, ui_template
from app.policies import POLICY_LINKS, PolicySection
from app.states.policy_state import PolicyState


def policy_paragraph(text: rx.Var[str]) -> rx.Component:
    return rx.el.p(
        text,
        class_name="text-[13px] sm:text-sm font-medium leading-relaxed text-[#4b5563]",
    )


def policy_section(section: PolicySection, index: rx.Var[int]) -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                rx.icon(section["icon"], class_name="h-4 w-4"),
                class_name="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8] text-[#fba922]",
            ),
            rx.el.div(
                rx.el.p(
                    ui_template(
                        "Section {count}", "count", (index + 1).to_string()
                    ),
                    class_name="text-[10px] font-bold uppercase tracking-[0.16em] text-[#8c91aa]",
                ),
                rx.el.h2(
                    section["heading"],
                    class_name="text-base sm:text-lg font-bold tracking-tight leading-snug text-[#111827]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.foreach(section["paragraphs"], policy_paragraph),
            class_name="mt-3 flex flex-col gap-2.5",
        ),
        class_name="w-full rounded-[1.6rem] border border-[#e08b12] bg-white px-4 py-4 sm:px-6 sm:py-5",
    )


def policy_header() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("arrow-left", class_name="h-4 w-4"),
            rx.el.span(ui("Back"), class_name="text-xs font-bold"),
            type="button",
            title=ui("Back to your profile"),
            aria_label=ui("Back to your profile"),
            on_click=PolicyState.close_policy,
            class_name="gah-inverse-text flex w-fit shrink-0 items-center gap-1.5 rounded-full bg-[#e08b12] px-3.5 py-2 text-white transition-colors hover:bg-[#b86e08] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.el.div(
            rx.image(
                src=BRAND_LOGO_SRC,
                alt=BRAND_LOGO_ALT,
                class_name="size-11 sm:size-12 shrink-0 rounded-full object-contain",
            ),
            rx.el.span(
                "Go and Help",
                class_name="text-sm font-bold tracking-tight text-[#e08b12]",
            ),
            class_name="flex items-center gap-2",
        ),
        class_name="sticky top-0 z-10 flex w-full items-center justify-between gap-3 border-b border-[#e08b12] bg-white/95 px-4 py-3 backdrop-blur-md sm:px-6",
    )


def policy_screen() -> rx.Component:
    """The reader itself: rendered only when a document is open."""
    return rx.el.div(
        policy_header(),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon(PolicyState.icon, class_name="h-5 w-5"),
                    class_name="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-[#fff7e8] text-[#fba922]",
                ),
                rx.el.div(
                    rx.el.h1(
                        PolicyState.title,
                        id="policy-title",
                        class_name="text-2xl sm:text-3xl font-bold tracking-tight leading-tight text-[#111827]",
                    ),
                    rx.el.p(
                        PolicyState.subtitle,
                        class_name="mt-1 text-[13px] sm:text-sm font-medium leading-relaxed text-[#4b5563]",
                    ),
                    rx.el.p(
                        PolicyState.updated,
                        class_name="mt-2 w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#b86e08]",
                    ),
                    class_name="min-w-0 flex-1",
                ),
                class_name="flex items-start gap-3",
            ),
            rx.el.div(
                rx.icon(
                    "shield-alert",
                    class_name="mt-0.5 h-4 w-4 shrink-0 text-[#fba922]",
                ),
                rx.el.p(
                    PolicyState.notice,
                    class_name="text-[13px] font-bold leading-relaxed text-[#b86e08]",
                ),
                role="note",
                class_name="mt-4 flex w-full items-start gap-2.5 rounded-[1.4rem] border border-[#e08b12] bg-[#fff7e8] px-4 py-3.5",
            ),
            rx.el.div(
                rx.foreach(
                    PolicyState.sections,
                    lambda section, index: policy_section(section, index),
                ),
                class_name="mt-4 flex w-full flex-col gap-3",
            ),
            rx.el.p(
                ui(
                    "This screen is part of the Go and Help app. It is written for adults everywhere and is not legal advice for any particular country."
                ),
                class_name="mt-5 text-center text-[11px] font-medium leading-relaxed text-[#68708f]",
            ),
            rx.el.button(
                rx.icon("arrow-left", class_name="h-4 w-4"),
                ui("Back to your profile"),
                type="button",
                aria_label=ui("Back to your profile"),
                on_click=PolicyState.close_policy,
                class_name="gah-inverse-text mx-auto mt-4 flex w-fit items-center gap-2 rounded-full bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="mx-auto w-full max-w-3xl px-4 pb-32 pt-5 sm:px-6",
        ),
        role="dialog",
        aria_modal="true",
        aria_labelledby="policy-title",
        class_name="gah-screen-scroll fixed inset-0 z-[70] h-[100dvh] w-full overflow-y-auto overscroll-contain bg-white",
    )


def policy_overlay() -> rx.Component:
    return rx.cond(PolicyState.is_open, policy_screen(), rx.fragment())


def policy_link_card(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon(item["icon"], class_name="h-4 w-4"),
            class_name="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8] text-[#fba922]",
        ),
        rx.el.span(
            ui(item["label"]),
            class_name="min-w-0 flex-1 break-words text-start text-[13px] font-bold leading-snug text-[#111827]",
        ),
        rx.icon("chevron-right", class_name="h-4 w-4 shrink-0 text-[#e08b12]"),
        type="button",
        aria_label=ui(item["label"]),
        on_click=lambda: PolicyState.open_policy(item["key"]),
        class_name="flex w-full items-center gap-3 rounded-2xl border border-[#e08b12] bg-white px-3.5 py-3 transition-colors hover:border-[#e08b12] hover:bg-[#fff7e8] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def policy_links_row() -> rx.Component:
    """Centred handbook links at the very bottom of the Profile screen."""
    return rx.el.section(
        rx.el.div(
            rx.icon("book-open", class_name="h-4 w-4 text-[#fba922]"),
            rx.el.h2(
                ui("More information"),
                class_name="text-lg font-bold tracking-tight text-[#111827]",
            ),
            class_name="flex items-center justify-center gap-2",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(POLICY_LINKS[:1], policy_link_card),
                class_name="w-full",
            ),
            rx.el.div(
                rx.foreach(POLICY_LINKS[1:], policy_link_card),
                class_name="mt-3 grid w-full grid-cols-1 gap-2 sm:grid-cols-2",
            ),
            class_name="mx-auto mt-3 w-full max-w-2xl",
        ),
        class_name="w-full rounded-[2rem] border border-[#f7d9a0] bg-white p-5 text-center sm:p-6",
    )
