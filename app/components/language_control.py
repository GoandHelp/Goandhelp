import reflex as rx

from app.interface_i18n import ui
from app.models import LANGUAGE_OPTIONS
from app.states.auth_state import AuthState


def browser_translatable_text(
    text: str | rx.Var[str],
    class_name: str = "text-sm font-medium leading-relaxed text-[#4b5563]",
    original_class_name: str = "mt-1 whitespace-pre-wrap [overflow-wrap:anywhere] text-xs font-normal leading-relaxed text-[#4b5563]",
) -> rx.Component:
    """Display member text unchanged, with an untouched original disclosure."""
    return rx.el.div(
        rx.el.p(
            text,
            custom_attrs={"translate": "no"},
            dir="auto",
            class_name=class_name,
        ),
        rx.cond(
            text != "",
            rx.el.details(
                rx.el.summary(
                    ui("Show original language"),
                    class_name="w-fit cursor-pointer rounded-sm text-[11px] font-normal not-italic leading-relaxed text-[#4b5563] hover:text-[#e08b12] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
                ),
                rx.el.p(
                    text,
                    custom_attrs={"translate": "no"},
                    dir="auto",
                    class_name=original_class_name,
                ),
                on_click=rx.stop_propagation,
                class_name="mt-1 min-w-0 text-left",
            ),
            rx.fragment(),
        ),
        class_name="min-w-0 max-w-full [&>p]:whitespace-pre-wrap [&>p]:[overflow-wrap:anywhere]",
    )


def original_language_disclosure(text: str | rx.Var[str]) -> rx.Component:
    return rx.cond(
        text != "",
        rx.el.details(
            rx.el.summary(
                ui("Show original language"),
                class_name="cursor-pointer text-sm font-normal text-[#4b5563] hover:text-[#e08b12]",
            ),
            rx.el.p(
                text,
                custom_attrs={"translate": "no"},
                dir="auto",
                class_name="mt-2 whitespace-pre-wrap text-base font-normal text-[#404040]",
            ),
            class_name="w-full rounded-xl bg-white p-3",
        ),
        rx.fragment(),
    )


def language_option(item: tuple[str, str]) -> rx.Component:
    return rx.el.option(item[1], value=item[0])


def language_control(control_id: str = "interface-language") -> rx.Component:
    """Globe + language picker for the top-right of the header."""
    return rx.el.div(
        rx.el.label(
            ui("App Language"), html_for=control_id, class_name="sr-only"
        ),
        rx.icon(
            "globe",
            class_name="h-4 w-4 text-[#fba922] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none",
        ),
        rx.el.select(
            rx.foreach(LANGUAGE_OPTIONS, language_option),
            id=control_id,
            value=AuthState.preferred_language,
            disabled=AuthState.language_saving,
            aria_label=ui("App Language"),
            on_change=AuthState.update_language,
            class_name="appearance-none cursor-pointer rounded-lg border border-[#d4d4d4] bg-white py-2 pl-9 pr-8 text-xs font-semibold text-[#404040] transition-colors hover:border-[#e08b12] outline-hidden",
        ),
        rx.icon(
            "chevron-down",
            class_name="h-3.5 w-3.5 text-[#404040] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
        ),
        title=ui("App Language"),
        class_name="relative w-fit shrink-0",
    )
