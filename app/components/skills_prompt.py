import reflex as rx

from app.interface_i18n import ui
from app.states.profile_state import ProfileState


def skills_prompt() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 z-[100] bg-black/50",
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    ui(
                        "Please fill out your Skills and Knowledge in order to be seen on the map"
                    ),
                    class_name="text-lg font-bold leading-relaxed text-[#111827]",
                ),
                rx.radix.primitives.dialog.description(
                    ui(
                        "Choose a category or add your skills so people know how you can help."
                    ),
                    class_name="mt-2 text-sm text-[#4b5563]",
                ),
                rx.el.button(
                    ui("Let people know how I can help"),
                    type="button",
                    on_click=ProfileState.open_required_skills,
                    class_name="mt-5 w-full rounded-xl bg-[#fba922] px-4 py-3 text-sm font-bold text-black hover:bg-[#e08b12] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
                ),
                rx.el.button(
                    ui("Cancel"),
                    type="button",
                    on_click=ProfileState.close_missing_skills,
                    class_name="mt-2 w-full rounded-xl bg-white px-4 py-2 text-sm font-medium text-[#4b5563] hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-[#e08b12]",
                ),
                class_name="fixed left-1/2 top-1/2 z-[101] w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-[#f7d9a0] bg-white p-6 font-['Inter']",
            ),
        ),
        open=ProfileState.missing_skills_open,
        on_open_change=lambda opened: ProfileState.close_missing_skills(),
    )
