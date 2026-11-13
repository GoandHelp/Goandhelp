"""Thirteen-screen required onboarding and the eight-step guided tour overlay."""

import reflex as rx

from app.interface_i18n import ui
from app.components.language_control import language_control
from app.states.auth_state import AuthState
from app.components.openfreemap import OPENFREEMAP_LIBERTY, open_free_map
from app.components.tour_pointer import tour_pointer
from app.components.request_draft import compact_request_fields
from app.skill_categories import CATEGORY_CHOICES, CATEGORY_GRADIENT
from app.models import LOCATION_MODE_HIDDEN
from app.states.onboarding_state import (
    COUNTRY_OPTIONS,
    CUSTOM_SKILL_LIMIT,
    CUSTOM_LANGUAGE_LIMIT,
    LANGUAGE_PRESETS,
    PERMISSION_ANSWERS,
    PERMISSION_TOPICS,
    SAFETY_COMMITMENTS,
    OnboardingState,
)

COPY_PANEL = "w-fit max-w-md mx-auto rounded-2xl bg-white/80 px-5 py-3 text-center text-base font-medium leading-relaxed text-[#404040]"

BACKGROUND_CLASSES = {
    1: "pointer-events-none absolute inset-0 bg-white bg-[url('/background_portrait_mobile.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    2: "pointer-events-none absolute inset-0 bg-white bg-[url('/dog_walking_porch.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    3: "pointer-events-none absolute inset-0 bg-white bg-[url('/text_asset_named.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    4: "pointer-events-none absolute inset-0 bg-white bg-[url('/background_sewing_portrait.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    5: "pointer-events-none absolute inset-0 bg-white bg-[url('/woman_soft_people.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    6: "pointer-events-none absolute inset-0 bg-white bg-[url('/travel_screen_six.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    7: "pointer-events-none absolute inset-0 bg-white bg-[url('/community_together_vertical.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    8: "pointer-events-none absolute inset-0 bg-white bg-[url('/screen_eight_skills.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    9: "pointer-events-none absolute inset-0 bg-white bg-[url('/9_language_vertical.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    10: "pointer-events-none absolute inset-0 bg-white bg-[url('/map_white_hand.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    11: "pointer-events-none absolute inset-0 bg-white bg-[url('/portrait_mobile_onboarding.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    12: "pointer-events-none absolute inset-0 bg-white bg-[url('/vertical_mobile_onboarding.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
    13: "pointer-events-none absolute inset-0 bg-white bg-[url('/9_language_vertical.png')] bg-cover bg-center saturate-[0.9] contrast-[0.97] sepia-[0.08]",
}
BACKGROUND_URLS = {
    step: classes.split("url('")[1].split("')")[0]
    for step, classes in BACKGROUND_CLASSES.items()
}

CHIP_ON = (
    "flex w-fit items-center gap-1.5 rounded-full border-2 border-[#e08b12] "
    "bg-white px-3.5 py-2 text-[13px] font-bold text-[#404040] "
    "transition-colors focus:outline-hidden focus-visible:ring-2 "
    "focus-visible:ring-[#e08b12]"
)
CHIP_OFF = (
    "flex w-fit items-center gap-1.5 rounded-full border border-[#f6c66f] "
    "bg-white px-3.5 py-2 text-[13px] font-semibold text-[#404040] "
    "transition-colors hover:border-[#e08b12] hover:text-[#b86e08] "
    "focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]"
)
TILE_ON = (
    "flex w-full items-start gap-3 rounded-2xl border-2 border-[#e08b12] "
    "bg-[#fff7e8] p-3.5 text-left transition-colors focus:outline-hidden "
    "focus-visible:ring-2 focus-visible:ring-[#e08b12]"
)
TILE_OFF = (
    "flex w-full items-start gap-3 rounded-2xl border border-[#f6c66f] "
    "bg-white p-3.5 text-left transition-colors hover:border-[#e08b12] "
    "focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]"
)


def slide_background() -> rx.Component:
    return rx.el.div(
        rx.cond(
            OnboardingState.current_step <= 13,
            rx.el.div(class_name="absolute inset-0 bg-white/45"),
            rx.fragment(),
        ),
        aria_hidden="true",
        class_name=rx.match(
            OnboardingState.current_step,
            (1, BACKGROUND_CLASSES[1]),
            (2, BACKGROUND_CLASSES[2]),
            (3, BACKGROUND_CLASSES[3]),
            (4, BACKGROUND_CLASSES[4]),
            (5, BACKGROUND_CLASSES[5]),
            (6, BACKGROUND_CLASSES[6]),
            (7, BACKGROUND_CLASSES[7]),
            (8, BACKGROUND_CLASSES[8]),
            (9, BACKGROUND_CLASSES[9]),
            (10, BACKGROUND_CLASSES[10]),
            (11, BACKGROUND_CLASSES[11]),
            (12, BACKGROUND_CLASSES[12]),
            (13, BACKGROUND_CLASSES[13]),
            "pointer-events-none absolute inset-0 bg-white",
        ),
    )


def progress_bar() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            OnboardingState.step_label,
            aria_live="polite",
            class_name="text-center text-sm font-semibold text-[#404040]",
        ),
        rx.el.div(
            rx.el.div(
                style={"width": OnboardingState.progress_width},
                class_name="h-full rounded-full bg-[#e08b12] transition-all motion-reduce:transition-none",
            ),
            role="progressbar",
            aria_label=ui("Step"),
            aria_valuemin=1,
            aria_valuemax=13,
            aria_valuenow=OnboardingState.current_step,
            aria_valuetext=OnboardingState.step_label,
            class_name="mt-3 h-0.5 w-40 overflow-hidden rounded-full bg-[#fba922]/20",
        ),
        class_name="relative flex shrink-0 flex-col items-center px-4 pt-7 pb-4 sm:pt-10",
    )


def copy_panel(text: str) -> rx.Component:
    return rx.el.p(ui(text), class_name=COPY_PANEL)


def story_screen() -> rx.Component:
    return rx.el.div(
        rx.match(
            OnboardingState.current_step,
            (
                2,
                rx.fragment(
                    copy_panel(
                        "Go and Help is a community of good people giving and receiving help across a many fields of knowledge"
                    ),
                    rx.el.div(
                        rx.el.p(ui("A helper: Someone who gives help")),
                        rx.el.p(ui("A helpee: someone who receives help")),
                        class_name="mx-auto flex w-fit max-w-md flex-col gap-3 rounded-2xl bg-white/80 px-5 py-3 text-center text-base font-medium leading-relaxed text-[#404040]",
                    ),
                ),
            ),
            (
                3,
                rx.fragment(
                    copy_panel("Help people with simple or technical tasks"),
                    copy_panel("locally or globally"),
                    rx.el.div(
                        copy_panel("All give good Karma..."),
                        class_name="pt-16 sm:pt-24",
                    ),
                ),
            ),
            (
                4,
                rx.fragment(
                    copy_panel(
                        "Whatever tasks in life have not yet accomplished, there may be a helper out there who is happy to help"
                    ),
                ),
            ),
            (
                5,
                rx.fragment(
                    copy_panel(
                        "Whether a second hand bicycle, vintage music records, lunch, cake or cash."
                    ),
                    rx.el.div(
                        copy_panel(
                            "Select what you can offer to thank a helper"
                        ),
                        class_name="pt-20 sm:pt-32",
                    ),
                ),
            ),
            (
                6,
                rx.fragment(
                    copy_panel(
                        "Can you give first aid, play a gig or fix a leaky bamboo roof?"
                    ),
                    copy_panel(
                        "From Bangkok to Berlin use Go and Help while travelling. Swap your knowledge and skills for food and accommodation."
                    ),
                ),
            ),
            (
                7,
                rx.fragment(
                    copy_panel(
                        "Many hands make light work, so joining an event allows many people to come together and help your community."
                    ),
                    rx.el.div(
                        rx.el.p(
                            ui("Events"),
                            class_name="text-center text-base font-bold text-[#404040]",
                        ),
                        rx.el.ul(
                            rx.el.li(ui("Festivals")),
                            rx.el.li(ui("Community projects")),
                            rx.el.li(ui("Disaster relief")),
                            class_name="mx-auto w-fit list-disc text-left text-sm leading-8 text-[#404040]",
                        ),
                        class_name="mx-auto w-fit rounded-2xl bg-white/80 px-8 py-4",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        class_name="flex w-full flex-col items-center gap-5 sm:gap-7",
    )


def category_card(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon(item["icon"], class_name="h-4 w-4 text-white"),
            style={
                "--category-fill": item["color"],
                "background": CATEGORY_GRADIENT,
            },
            class_name="flex size-9 shrink-0 items-center justify-center rounded-full",
        ),
        rx.el.span(
            item["label"],
            class_name="block min-w-0 flex-1 text-center text-[13px] font-bold text-[#171717]",
        ),
        rx.cond(
            OnboardingState.categories.contains(item["value"]),
            rx.icon("check", class_name="h-4 w-4 shrink-0 text-[#e08b12]"),
            rx.fragment(),
        ),
        type="button",
        aria_pressed=rx.cond(
            OnboardingState.categories.contains(item["value"]),
            "true",
            "false",
        ),
        on_click=lambda: OnboardingState.toggle_category(item["value"]),
        class_name=rx.cond(
            OnboardingState.categories.contains(item["value"]),
            "flex w-full items-center gap-2.5 rounded-2xl border-2 border-[#e08b12] bg-white/80 px-6 py-2.5 transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            "flex w-full items-center gap-2.5 rounded-2xl border border-[#f6c66f] bg-white/80 px-6 py-2.5 transition-colors hover:border-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
    )


def language_chip(label: str) -> rx.Component:
    return rx.el.button(
        rx.cond(
            OnboardingState.languages.contains(label),
            rx.icon("check", class_name="h-3.5 w-3.5"),
            rx.icon("plus", class_name="h-3.5 w-3.5"),
        ),
        label,
        type="button",
        aria_pressed=rx.cond(
            OnboardingState.languages.contains(label), "true", "false"
        ),
        on_click=lambda: OnboardingState.toggle_language(label),
        class_name=rx.cond(
            OnboardingState.languages.contains(label),
            "flex min-h-11 items-center gap-2 rounded-md bg-transparent px-3 py-2 text-sm font-bold text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            "flex min-h-11 items-center gap-2 rounded-md bg-transparent px-3 py-2 text-sm font-medium text-black hover:text-[#b86e08] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
    )


def country_option(name: str) -> rx.Component:
    return rx.el.option(name, value=name, class_name="bg-white text-[#171717]")


def country_screen() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            ui("Choose your nationality:"),
            html_for="onboarding-country",
            class_name="mb-1 block text-[13px] font-semibold text-[#171717]",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option(
                    ui("Choose your country"),
                    value="",
                    disabled=True,
                    class_name="bg-white text-[#525252]",
                ),
                rx.foreach(COUNTRY_OPTIONS, country_option),
                id="onboarding-country",
                value=OnboardingState.home_country,
                on_change=OnboardingState.choose_country,
                class_name="w-full appearance-none cursor-pointer rounded-xl border border-[#f6c66f] bg-white px-4 py-3 pr-10 text-sm font-semibold text-[#171717] focus:border-[#e08b12] focus:ring-2 focus:ring-[#e08b12]/25 outline-hidden",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#404040]",
            ),
            class_name="relative w-full",
        ),
        class_name="mx-auto w-full max-w-xs rounded-2xl bg-white/80 p-3 text-center",
    )


def setup_panel(text: str) -> rx.Component:
    return rx.el.p(
        ui(text),
        class_name="mx-auto w-fit max-w-md rounded-2xl bg-white/80 px-5 py-3 text-center text-sm font-medium leading-relaxed text-[#404040]",
    )


def location_choice(label: str, value: str) -> rx.Component:
    return rx.el.button(
        ui(label),
        type="button",
        aria_pressed=rx.cond(
            OnboardingState.location_pref == value, "true", "false"
        ),
        on_click=lambda: OnboardingState.choose_location(value),
        class_name=rx.cond(
            OnboardingState.location_pref == value,
            "gah-segment-control rounded-full ring-2 ring-[#e08b12] bg-[#fff7e8] px-5 py-2 text-sm font-bold text-[#292929] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
            "gah-segment-control rounded-full bg-white px-5 py-2 text-sm font-semibold text-[#404040] hover:bg-[#fff7e8] focus-visible:outline-2 focus-visible:outline-[#e08b12]",
        ),
    )


def location_screen() -> rx.Component:
    return rx.el.div(
        setup_panel(
            "When you request help, your location is shown approximately between 500m and 1km away from you."
        ),
        setup_panel(
            "Only a confirmed helper is shown your accurate job location"
        ),
        rx.el.div(
            open_free_map(
                markers=OnboardingState.location_markers,
                center=OnboardingState.map_center,
                zoom=OnboardingState.map_zoom,
                style_url=OPENFREEMAP_LIBERTY,
                camera_updates=False,
                on_map_click=OnboardingState.set_location_point,
                on_marker_drag=OnboardingState.set_location_point,
                show_navigation_control=True,
                navigation_position="bottom-left",
                attribution_visible=True,
                class_name="h-64 w-full sm:h-72",
            ),
            aria_label=ui("Your location"),
            class_name="h-64 w-full shrink-0 overflow-hidden rounded-2xl border border-[#e08b12] sm:h-72",
        ),
        rx.el.div(
            location_choice("Approx", "approximate"),
            location_choice("Off", LOCATION_MODE_HIDDEN),
            role="group",
            aria_label=ui("Your location"),
            class_name="mx-auto flex w-fit items-center gap-1 rounded-full border border-[#e08b12] bg-white p-1",
        ),
        setup_panel(
            "As a helper, setting your location to 'Approximate' allows a helpee to send you direct help requests. Showing your location is not necessary for helping others."
        ),
        class_name="flex w-full flex-col items-center gap-4",
    )


def commitment_row(item: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            rx.icon(item["icon"], class_name="h-7 w-7"),
            class_name="flex size-12 shrink-0 items-center justify-center rounded-xl bg-white text-[#e08b12]",
        ),
        rx.el.div(
            rx.el.p(
                ui(item["title"]),
                class_name="text-sm font-bold text-[#171717]",
            ),
            rx.el.p(
                ui(item["body"]),
                class_name="mt-0.5 text-sm font-medium leading-relaxed text-[#404040]",
            ),
            class_name="min-w-0 flex-1",
        ),
        class_name="mx-auto flex w-full max-w-md items-start gap-4 rounded-2xl bg-white/80 p-3 text-left",
    )


def acknowledge_switch(
    checked: rx.Var[bool], label: str, on_click: rx.event.EventType
) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.cond(
                checked,
                rx.icon("check", class_name="h-3.5 w-3.5 text-white"),
                rx.fragment(),
            ),
            class_name=rx.cond(
                checked,
                "flex size-5 shrink-0 items-center justify-center rounded-md bg-[#e08b12]",
                "flex size-5 shrink-0 items-center justify-center rounded-md border border-[#c6d2e8] bg-white",
            ),
        ),
        rx.el.span(
            ui(label),
            class_name="text-left text-[13px] font-bold text-[#171717]",
        ),
        type="button",
        role="checkbox",
        aria_checked=rx.cond(checked, "true", "false"),
        on_click=on_click,
        class_name="mx-auto mt-6 flex w-fit items-center justify-center gap-3 rounded-2xl bg-white/80 p-3.5 transition-colors hover:border-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


PERMISSION_VARS = {
    "notifications": OnboardingState.perm_notifications,
    "camera": OnboardingState.perm_camera,
}


def permission_answer(topic: str, item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        ui(item["label"]),
        type="button",
        aria_pressed=rx.cond(
            PERMISSION_VARS[topic] == item["value"], "true", "false"
        ),
        on_click=lambda: OnboardingState.choose_permission(
            topic, item["value"]
        ),
        class_name=rx.cond(
            PERMISSION_VARS[topic] == item["value"], CHIP_ON, CHIP_OFF
        ),
    )


def permission_block(item: dict[str, str], topic: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                rx.icon(item["icon"], class_name="h-4 w-4"),
                class_name="flex size-12 shrink-0 items-center justify-center rounded-xl bg-white text-[#e08b12]",
            ),
            rx.el.div(
                rx.el.p(
                    ui(item["title"]),
                    class_name="text-[13px] font-bold text-[#171717]",
                ),
                rx.el.p(
                    ui(item["body"]),
                    class_name="mt-0.5 text-xs font-medium leading-relaxed text-[#404040]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.foreach(
                PERMISSION_ANSWERS,
                lambda answer: permission_answer(topic, answer),
            ),
            role="group",
            aria_label=ui(item["title"]),
            class_name="mt-4 flex flex-wrap items-center justify-center gap-2",
        ),
        class_name="mx-auto w-full max-w-md rounded-2xl bg-white/80 p-3 text-left",
    )


def permissions_screen() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            ui(
                "Nothing is requested yet. Your device only asks when you first use a feature."
            ),
            class_name="mx-auto w-full max-w-md rounded-2xl bg-white/80 px-3.5 py-2.5 text-xs font-semibold text-[#404040]",
        ),
        permission_block(PERMISSION_TOPICS[0], "notifications"),
        rx.el.h2(
            ui("Camera and photos permissions."),
            class_name="mt-5 text-center text-xl font-semibold text-[#292929]",
        ),
        permission_block(PERMISSION_TOPICS[1], "camera"),
        class_name="flex w-full flex-col gap-2.5",
    )


def first_request_screen() -> rx.Component:
    return rx.fragment(
        rx.el.div(
            compact_request_fields(
                OnboardingState, "onboarding-first-request", show_date=False
            ),
            rx.cond(
                OnboardingState.error,
                rx.el.p(
                    ui(OnboardingState.error),
                    role="alert",
                    id="first-request-error",
                    class_name="w-full bg-transparent text-sm font-semibold text-[#e08b12]",
                ),
                rx.fragment(),
            ),
            on_mount=OnboardingState.prepare_first_request,
            class_name="flex w-full flex-col gap-3 bg-transparent text-[#292929]",
        ),
    )


def language_scroll(up: bool) -> rx.Component:
    return rx.el.button(
        rx.icon(
            "triangle",
            class_name=rx.cond(
                up,
                "size-6 fill-[#fff7e8] text-[#e08b12]",
                "size-6 rotate-180 fill-[#fff7e8] text-[#e08b12]",
            ),
        ),
        type="button",
        aria_label=rx.cond(
            up, ui("Scroll languages up"), ui("Scroll languages down")
        ),
        aria_controls="onboarding-languages",
        on_click=rx.call_script(
            rx.cond(
                up,
                "document.getElementById('onboarding-languages')?.scrollBy({top:-220,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})",
                "document.getElementById('onboarding-languages')?.scrollBy({top:220,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})",
            )
        ),
        class_name="mx-auto flex size-11 items-center justify-center rounded-xl bg-[#fff7e8] text-[#e08b12] hover:bg-[#ffedcc] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def custom_answer(
    label: str,
    value: rx.Var[str],
    setter: rx.event.EventType,
    limit: int,
    hint: str = "",
    skill_details: bool = False,
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            rx.el.span(
                ui(label), class_name="text-sm font-semibold text-[#404040]"
            ),
            rx.cond(
                hint != "",
                rx.el.span(
                    ui(hint),
                    class_name="ml-auto text-right text-xs font-normal text-[#525252]",
                ),
                rx.fragment(),
            ),
            class_name="flex w-full items-center justify-between gap-2",
        ),
        rx.el.input(
            default_value=value,
            on_change=setter.debounce(300),
            placeholder=ui(label),
            max_length=limit,
            class_name="w-full rounded-xl border border-[#e08b12] bg-white px-3 py-2 text-sm text-[#292929] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        class_name=rx.cond(
            skill_details,
            "mx-auto mt-4 flex w-full max-w-sm flex-col gap-2 rounded-2xl bg-white/80 p-3 text-center",
            "mx-auto mt-4 flex w-full max-w-xs flex-col gap-2 rounded-2xl bg-white/80 p-3 text-center",
        ),
    )


def screen_body() -> rx.Component:
    return rx.match(
        OnboardingState.current_step,
        (
            1,
            rx.el.div(
                rx.el.p(
                    ui("Community in your hands"),
                    class_name="mb-3 text-center text-lg font-medium text-[#404040]",
                ),
                country_screen(),
                rx.el.div(
                    rx.el.label(
                        ui("Choose your username:"),
                        html_for="onboarding-username",
                        class_name="mt-4 block text-[13px] font-semibold text-[#111827]",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "@",
                            aria_hidden="true",
                            class_name="text-sm text-[#e08b12]",
                        ),
                        rx.el.input(
                            id="onboarding-username",
                            placeholder=ui("Choose your username:"),
                            default_value=OnboardingState.username,
                            on_change=OnboardingState.set_username.debounce(
                                400
                            ),
                            min_length=3,
                            max_length=30,
                            required=True,
                            auto_complete="username",
                            aria_describedby="username-feedback",
                            class_name="min-w-0 flex-1 border-0! bg-white py-3 text-sm text-[#111827] outline-none! ring-0! shadow-none! focus:border-0! focus:outline-none! focus:ring-0! focus:shadow-none!",
                        ),
                        class_name="mt-1 flex items-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-3 focus-within:border-[#e08b12]",
                    ),
                    rx.el.p(
                        ui(
                            "3–30 lowercase letters, numbers, periods or underscores"
                        ),
                        class_name="mt-1 text-xs text-[#4b5563]",
                    ),
                    rx.el.p(
                        ui(OnboardingState.username_feedback),
                        id="username-feedback",
                        role="status",
                        class_name="mt-1 text-xs text-[#e08b12]",
                    ),
                    class_name="w-full rounded-2xl bg-white/80 p-4 text-center",
                ),
                class_name="mx-auto flex w-full max-w-xs flex-col gap-3 text-center",
            ),
        ),
        (2, story_screen()),
        (3, story_screen()),
        (4, story_screen()),
        (5, story_screen()),
        (6, story_screen()),
        (7, story_screen()),
        (
            8,
            rx.el.div(
                rx.el.div(
                    rx.foreach(CATEGORY_CHOICES, category_card),
                    role="group",
                    aria_label=ui("How can you help?"),
                    class_name="mx-auto flex w-full max-w-sm flex-col gap-2",
                ),
                rx.cond(
                    OnboardingState.categories.length() > 0,
                    custom_answer(
                        "Any more details?",
                        OnboardingState.custom_skill,
                        OnboardingState.set_custom_skill,
                        CUSTOM_SKILL_LIMIT,
                        hint="Optional",
                        skill_details=True,
                    ),
                    rx.fragment(),
                ),
                rx.el.p(
                    ui("You can change these later in your profile."),
                    class_name="mt-4 text-sm text-[#404040]",
                ),
                class_name="w-full",
            ),
        ),
        (
            9,
            rx.el.div(
                language_scroll(True),
                rx.el.div(
                    rx.foreach(LANGUAGE_PRESETS, language_chip),
                    role="group",
                    aria_label=ui("Languages"),
                    tab_index=0,
                    id="onboarding-languages",
                    class_name="gah-screen-scroll mx-auto flex h-64 w-full max-w-md shrink-0 flex-wrap content-start items-center gap-2 overflow-y-auto overscroll-contain bg-transparent p-2 focus-visible:outline-2 focus-visible:outline-[#e08b12] sm:h-72",
                ),
                language_scroll(False),
                custom_answer(
                    "Any other languages:",
                    OnboardingState.custom_language,
                    OnboardingState.set_custom_language,
                    CUSTOM_LANGUAGE_LIMIT,
                ),
                class_name="w-full",
            ),
        ),
        (10, location_screen()),
        (
            11,
            rx.el.div(
                rx.el.div(
                    rx.foreach(SAFETY_COMMITMENTS, commitment_row),
                    class_name="flex w-full flex-col gap-8",
                ),
                rx.el.p(
                    ui(
                        "Disregard to these rules will result in a blocked account"
                    ),
                    class_name="mx-auto mt-5 w-fit max-w-md rounded-2xl bg-white/80 px-5 py-3 text-center text-[13px] font-bold text-[#e08b12]",
                ),
                acknowledge_switch(
                    OnboardingState.safety_ack,
                    "I agree to these community rules",
                    OnboardingState.toggle_safety,
                ),
                class_name="w-full",
            ),
        ),
        (12, permissions_screen()),
        (
            13,
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        ui("Post your first help request here"),
                        class_name="text-center text-base font-bold text-[#404040]",
                    ),
                    rx.el.button(
                        ui("Skip for now"),
                        type="button",
                        disabled=OnboardingState.saving,
                        on_click=OnboardingState.complete_onboarding,
                        class_name="ml-auto min-h-11 shrink-0 rounded-full bg-white/80 px-3 py-2 text-sm font-semibold text-[#e08b12] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12] disabled:opacity-50",
                    ),
                    class_name="flex w-full items-center justify-between gap-2 text-left",
                ),
                first_request_screen(),
                class_name="flex w-full flex-col gap-4 rounded-2xl bg-white/80 p-3",
            ),
        ),
        rx.fragment(),
    )


def onboarding_actions() -> rx.Component:
    return rx.el.div(
        rx.cond(
            OnboardingState.is_first_step,
            rx.fragment(),
            rx.el.button(
                rx.icon("arrow-left", class_name="h-4 w-4"),
                ui("Back"),
                type="button",
                disabled=OnboardingState.saving,
                on_click=OnboardingState.go_back,
                class_name="gah-segment-control flex items-center gap-2 rounded-full border-0 bg-white/80 px-4 py-2.5 text-[13px] font-bold text-[#404040] transition-colors hover:border-[#e08b12] hover:text-[#b86e08] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12] disabled:opacity-60",
            ),
        ),
        rx.el.button(
            rx.cond(
                OnboardingState.saving,
                rx.el.span(
                    rx.spinner(class_name="h-3.5 w-3.5"),
                    ui("Saving…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                rx.el.span(
                    ui(OnboardingState.continue_label),
                    rx.icon("arrow-right", class_name="h-4 w-4"),
                    class_name="flex items-center justify-center gap-2",
                ),
            ),
            type="button",
            disabled=~OnboardingState.can_continue | OnboardingState.saving,
            on_click=OnboardingState.go_next,
            class_name="gah-segment-control flex items-center gap-2 rounded-full border-0 bg-[#e08b12] px-5 py-2.5 text-[13px] font-bold text-[#171717] transition-colors hover:bg-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12] disabled:cursor-not-allowed disabled:opacity-50",
        ),
        class_name="mt-10 flex w-full items-center justify-center gap-4 pb-6",
    )


def interface_language_screen() -> rx.Component:
    return rx.el.section(
        rx.icon("globe", class_name="mx-auto size-12 text-[#e08b12]"),
        rx.el.h1(
            ui("Choose your language"),
            id="onboarding-language-title",
            tab_index=-1,
            class_name="text-center text-3xl font-semibold text-[#e08b12] sm:text-5xl",
        ),
        rx.el.p(
            ui(
                "Interface language is separate from the languages you speak. You can change it later in Settings."
            ),
            class_name="text-center text-base leading-relaxed text-[#404040]",
        ),
        language_control("onboarding-interface-language"),
        rx.el.p(
            ui(
                "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language."
            ),
            class_name="text-center text-sm leading-relaxed text-[#4b5563]",
        ),
        rx.el.p(
            ui(OnboardingState.error),
            role="alert",
            class_name="text-sm text-[#b86e08]",
        ),
        rx.el.p(
            AuthState.language_error,
            role="alert",
            class_name="text-sm text-[#b86e08]",
        ),
        rx.el.button(
            ui("Continue"),
            rx.icon("arrow-right", class_name="size-4"),
            type="button",
            on_click=OnboardingState.confirm_interface_language,
            disabled=OnboardingState.saving | AuthState.language_saving,
            class_name="flex min-h-11 items-center gap-2 rounded-full bg-[#e08b12] px-6 py-3 text-sm font-bold text-[#171717] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b86e08] disabled:opacity-50",
        ),
        aria_labelledby="onboarding-language-title",
        on_mount=rx.call_script(
            "requestAnimationFrame(() => document.getElementById('onboarding-language-title')?.focus())"
        ),
        class_name="m-auto flex w-full max-w-xl flex-col items-center gap-6 rounded-2xl bg-white/90 px-6 py-8 sm:px-10 sm:py-12",
    )


def onboarding_flow() -> rx.Component:
    """Replaces the signed-in surface until all 13 screens are complete."""
    return rx.el.section(
        rx.el.link(
            rel="preload",
            href=rx.Var.create(BACKGROUND_URLS)[OnboardingState.current_step],
            as_="image",
            type="image/png",
        ),
        rx.cond(
            OnboardingState.current_step < 13,
            rx.el.link(
                rel="prefetch",
                href=rx.Var.create(BACKGROUND_URLS).get(
                    OnboardingState.current_step + 1, ""
                ),
                as_="image",
                type="image/webp",
            ),
            rx.fragment(),
        ),
        slide_background(),
        rx.el.div(
            rx.cond(
                OnboardingState.needs_language_choice,
                rx.fragment(),
                progress_bar(),
            ),
            rx.cond(
                OnboardingState.needs_language_choice,
                rx.el.div(
                    interface_language_screen(),
                    class_name="flex min-h-full w-full items-center justify-center p-5",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.cond(
                            OnboardingState.screen["title"] != "",
                            rx.el.h1(
                                ui(OnboardingState.screen["title"]),
                                class_name=rx.cond(
                                    OnboardingState.current_step == 1,
                                    "mb-3 text-center text-3xl font-semibold leading-tight tracking-tight text-[#e08b12] sm:mb-4 sm:text-5xl",
                                    "mb-8 text-center text-3xl font-semibold leading-tight tracking-tight text-[#e08b12] sm:mb-10 sm:text-5xl",
                                ),
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            OnboardingState.screen["body"] != "",
                            rx.el.div(
                                rx.cond(
                                    (OnboardingState.current_step >= 8)
                                    & (OnboardingState.current_step <= 12),
                                    setup_panel(OnboardingState.screen["body"]),
                                    copy_panel(OnboardingState.screen["body"]),
                                ),
                                class_name="mb-5",
                            ),
                            rx.fragment(),
                        ),
                        screen_body(),
                        rx.cond(
                            (OnboardingState.error != "")
                            & (OnboardingState.current_step != 13),
                            rx.el.p(
                                ui(OnboardingState.error),
                                role="alert",
                                class_name="mt-3 w-full rounded-xl bg-white/80 px-3 py-2 text-center text-sm font-semibold text-[#e08b12]",
                            ),
                            rx.fragment(),
                        ),
                        onboarding_actions(),
                        class_name="mx-auto flex w-full max-w-xl flex-col items-center text-center",
                    ),
                    key=OnboardingState.current_step,
                    class_name="flex w-full flex-1 items-center justify-center px-5 py-8 sm:px-8 sm:py-12",
                ),
            ),
            class_name="gah-screen-scroll relative z-10 flex min-h-0 w-full flex-1 flex-col overflow-y-auto",
        ),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        aria_label=ui("Welcome to Go and Help"),
        class_name="gah-onboarding relative isolate flex min-h-0 w-full flex-1 flex-col overflow-hidden bg-white font-['Inter'] text-[#292929]",
    )


def fireworks_burst(position: str) -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [
                "rotate-0",
                "rotate-45",
                "rotate-90",
                "rotate-135",
                "rotate-180",
                "rotate-225",
                "rotate-270",
                "rotate-315",
            ],
            lambda rotation: rx.el.div(
                rx.el.span(
                    class_name="gah-firework-spark absolute -top-12 left-0 h-4 w-1 rounded-full bg-[#fba922] motion-reduce:opacity-80"
                ),
                rx.el.span(
                    class_name="gah-firework-glint absolute -top-20 left-0 size-1 rounded-full bg-white motion-reduce:opacity-100"
                ),
                class_name=rotation,
            ),
        ),
        aria_hidden="true",
        class_name=position,
    )


def first_request_celebration() -> rx.Component:
    return rx.el.div(
        rx.el.style("""
            @keyframes gah-gentle-spark {
                0%, 100% { transform: scale(.9); opacity: .45; }
                50% { transform: scale(1.12); opacity: 1; }
            }
            @media (prefers-reduced-motion: no-preference) {
                .gah-firework-spark { animation: gah-gentle-spark 2.4s ease-in-out infinite; }
                .gah-firework-glint { animation: gah-gentle-spark 2.8s ease-in-out infinite; }
            }
        """),
        rx.cond(
            OnboardingState.celebration_visible,
            rx.el.div(
                rx.el.div(
                    fireworks_burst("absolute left-[20%] top-[25%]"),
                    fireworks_burst("absolute right-[20%] top-[35%]"),
                    fireworks_burst("absolute left-[35%] bottom-[25%]"),
                    aria_hidden="true",
                    class_name="absolute inset-0 overflow-hidden",
                ),
                rx.el.p(
                    ui(
                        "Congratulations, your first help request is ready for the world"
                    ),
                    class_name="relative -translate-y-24 max-w-xl px-6 text-center text-xl font-bold leading-relaxed text-white [text-shadow:0_1px_5px_#70430b] sm:text-3xl",
                ),
                class_name=rx.cond(
                    OnboardingState.celebration_fading,
                    "absolute inset-0 flex items-center justify-center opacity-0 transition-opacity duration-600 motion-reduce:transition-none",
                    "absolute inset-0 flex items-center justify-center opacity-100 transition-opacity duration-600 motion-reduce:transition-none",
                ),
            ),
            rx.fragment(),
        ),
        lang=AuthState.preferred_language,
        dir=AuthState.interface_direction,
        aria_live="polite",
        aria_atomic="true",
        class_name="pointer-events-none fixed inset-0 z-[60] flex items-center justify-center p-5",
    )


def tour_prompt() -> rx.Component:
    return rx.cond(
        OnboardingState.tour_prompt_visible
        & ~OnboardingState.celebration_visible,
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    type="button",
                    title=ui("Close"),
                    aria_label=ui("Close"),
                    on_click=OnboardingState.dismiss_tour_prompt,
                    class_name="absolute right-3 top-3 flex size-9 items-center justify-center rounded-full border border-[#f6c66f] bg-white text-[#b86e08] hover:bg-[#fff7e8] focus-visible:outline-2 focus-visible:outline-[#b86e08]",
                ),
                rx.icon("compass", class_name="mx-auto h-6 w-6 text-[#b86e08]"),
                rx.el.h2(
                    ui("Learn how to navigate the app"),
                    id="gah-tour-prompt-title",
                    class_name="mt-3 text-center text-lg font-bold text-[#171717]",
                ),
                rx.el.p(
                    ui(
                        "Take a quick tour of the main controls, or explore on your own."
                    ),
                    id="gah-tour-prompt-description",
                    class_name="mt-2 text-center text-sm font-medium leading-relaxed text-[#404040]",
                ),
                rx.el.button(
                    ui("Start tour"),
                    type="button",
                    id="gah-tour-prompt-start",
                    on_click=OnboardingState.start_tour,
                    class_name="mt-5 min-h-11 w-full rounded-full bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#b86e08] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b86e08]",
                ),
                role="dialog",
                aria_labelledby="gah-tour-prompt-title",
                aria_describedby="gah-tour-prompt-description",
                on_mount=rx.call_script(
                    "requestAnimationFrame(() => document.getElementById('gah-tour-prompt-start')?.focus())"
                ),
                class_name="pointer-events-auto relative w-full max-w-sm rounded-2xl border border-[#f6c66f] bg-[#fff7e8] px-6 pb-6 pt-8 font-['Inter']",
            ),
            class_name="pointer-events-none fixed inset-0 z-[70] flex items-center justify-center p-5",
        ),
        rx.fragment(),
    )


# ------------------------------------------------------------------ the tour
TOUR_WRAPPER_CLASS = "gah-tour-wrapper pointer-events-none fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[70] w-[calc(100%-1rem-env(safe-area-inset-left)-env(safe-area-inset-right))] max-w-[424px] rounded-[2.85rem] p-[20px] backdrop-blur-[20px]"
TOUR_CARD_CLASS = "pointer-events-auto relative w-full max-h-[max(8rem,calc(100dvh-10rem-40px-2*env(safe-area-inset-bottom)-2*env(safe-area-inset-top)))] overflow-y-auto overscroll-contain rounded-[1.6rem] border-2 border-[#e08b12] bg-[#fff7e8] px-4 pb-4 pt-3 text-[#404040]"


def tour_controls() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("arrow-left", class_name="h-4 w-4"),
            ui("Back"),
            type="button",
            disabled=OnboardingState.tour_is_first,
            on_click=OnboardingState.tour_back,
            class_name="justify-self-start flex items-center gap-1.5 rounded-full border border-[#f6c66f] bg-white px-2 sm:px-3.5 py-2 text-xs font-bold text-[#404040] transition-colors hover:border-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12] disabled:opacity-40",
        ),
        rx.el.span(
            OnboardingState.tour_step_label,
            aria_live="polite",
            class_name="text-center text-xs font-semibold text-[#404040]",
        ),
        rx.el.button(
            rx.cond(OnboardingState.tour_is_last, ui("Finish"), ui("Next")),
            rx.cond(
                OnboardingState.tour_is_last,
                rx.icon("check", class_name="h-4 w-4"),
                rx.icon("arrow-right", class_name="h-4 w-4"),
            ),
            type="button",
            on_click=rx.cond(
                OnboardingState.tour_is_last,
                OnboardingState.tour_finish,
                OnboardingState.tour_next,
            ),
            class_name="justify-self-end flex items-center gap-1.5 rounded-full bg-[#e08b12] px-2 sm:px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-[#b86e08] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        class_name="mt-3 grid w-full grid-cols-[1fr_auto_1fr] items-center gap-2",
    )


def guided_tour() -> rx.Component:
    """Dismissible but persistent callout layered over the real product."""
    return rx.fragment(
        tour_prompt(),
        rx.el.style("""
            @keyframes gah-tour-pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.075); }
            }
            @media (prefers-reduced-motion: no-preference) {
                .gah-app-shell:has(#gah-tour-card[data-tour-step="1"]) [data-tour-target="profile"] .gah-profile-avatar-slot,
                .gah-app-shell:has(#gah-tour-card[data-tour-step="2"]) [data-tour-target="skills"] .gah-profile-disclosure span.block:first-child,
                .gah-app-shell:has(#gah-tour-card[data-tour-step="3"]) [data-tour-target="filters-label"],
                .gah-app-shell:has(#gah-tour-card[data-tour-step="4"]) .gah-request-ask h2,
                .gah-app-shell:has(#gah-tour-card[data-tour-step="4"]) .gah-request-ask > :last-child,
                .gah-app-shell:has(#gah-tour-card[data-tour-step="6"]) [data-tour-target="community-community"] span:last-child,
                .gah-app-shell:has(#gah-tour-card[data-tour-step="7"]) [data-tour-target="community-events"] span:last-child,
                .gah-app-shell:has(#gah-tour-card[data-tour-step="8"]) [data-tour-target="community-reviews"] span:last-child {
                    animation: gah-tour-pulse 1.9s ease-in-out infinite;
                    transform-origin: center;
                }
            }
            .gah-app-shell:has(#gah-tour-card[data-tour-step="8"]) .gah-tour-wrapper {
                -webkit-backdrop-filter: none;
                backdrop-filter: none;
            }
            .gah-app-shell:has(#gah-tour-card[data-tour-step="8"]) .gah-tour-wrapper::before {
                content: "";
                position: absolute;
                inset: -24px;
                border-radius: 50%;
                pointer-events: none;
                -webkit-backdrop-filter: blur(20px);
                backdrop-filter: blur(20px);
                -webkit-mask-image: radial-gradient(ellipse closest-side, black 38%, transparent 100%);
                mask-image: radial-gradient(ellipse closest-side, black 38%, transparent 100%);
            }
        """),
        rx.cond(
            OnboardingState.tour_visible,
            rx.fragment(
                tour_pointer(),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.button(
                                rx.icon("x", class_name="h-3.5 w-3.5"),
                                type="button",
                                title=ui("Close tour"),
                                aria_label=ui("Hide the tour"),
                                on_click=OnboardingState.tour_dismiss,
                                class_name="absolute right-3 top-3 flex size-7 shrink-0 items-center justify-center rounded-full border border-[#f6c66f] bg-white text-[#e08b12] transition-colors hover:border-[#e08b12]",
                            ),
                            class_name="flex items-center gap-2",
                        ),
                        rx.el.h2(
                            ui(OnboardingState.tour_card["title"]),
                            id="gah-tour-title",
                            class_name="mt-0 min-h-7 px-7 text-center text-base font-bold tracking-tight text-[#171717]",
                        ),
                        rx.el.p(
                            ui(OnboardingState.tour_card["body"]),
                            id="gah-tour-description",
                            class_name="mt-1 text-[13px] font-medium leading-relaxed text-[#404040]",
                        ),
                        tour_controls(),
                        role="dialog",
                        aria_labelledby="gah-tour-title",
                        aria_describedby="gah-tour-description",
                        id="gah-tour-card",
                        custom_attrs={
                            "data-tour-focus": OnboardingState.tour_card[
                                "target"
                            ],
                            "data-tour-step": OnboardingState.tour_step,
                        },
                        class_name=TOUR_CARD_CLASS,
                    ),
                    lang=AuthState.preferred_language,
                    dir=AuthState.interface_direction,
                    class_name=TOUR_WRAPPER_CLASS,
                ),
            ),
            rx.fragment(),
        ),
    )


def restart_tour_control() -> rx.Component:
    """Optional `Restart tour` action, shown in Profile settings."""
    return rx.cond(
        OnboardingState.tour_can_restart,
        rx.el.div(
            rx.el.p(
                ui("Guided tour"),
                class_name="text-sm font-bold text-[#171717]",
            ),
            rx.el.p(
                ui("Restart tour"),
                ": ",
                ui("Profile"),
                ", ",
                ui("Search filters"),
                ", ",
                ui("Requests"),
                ", ",
                ui("Inbox"),
                ", ",
                ui("Forum"),
                ", ",
                ui("Events"),
                ", ",
                ui("Reviews"),
                class_name="mt-0.5 text-xs font-medium leading-relaxed text-[#404040]",
            ),
            rx.el.button(
                rx.icon("play", class_name="h-4 w-4"),
                ui("Restart tour"),
                type="button",
                on_click=OnboardingState.restart_tour,
                class_name="mt-3 flex w-fit items-center gap-2 rounded-full border border-[#e08b12] bg-[#fff7e8] px-3.5 py-2 text-xs font-bold text-[#404040] transition-colors hover:bg-[#d0e2ff] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
            ),
            class_name="w-full rounded-2xl border border-[#f7d9a0] bg-white p-4",
        ),
        rx.fragment(),
    )
