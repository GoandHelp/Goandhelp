import reflex as rx
from app.components.header import BRAND_LOGO_SRC, BRAND_LOGO_ALT
from app.components.request_draft import compact_request_fields

from app.components.language_control import browser_translatable_text
from app.interface_i18n import ui, ui_template, ui_template_multi
from app.components.disclosure import disclosure_arrow

from app.components.notification_badge import corner_activity_dot
from app.states.notification_state import NotificationState

from app.components.feedback import (
    INPUT_CLASS,
    SELECT_CLASS,
    error_banner,
    field_label,
    select_wrapper,
    success_banner,
)
from app.states.auth_state import AuthState
from app.states.help_hub_state import HelpHubState
from app.states.help_post_state import HelpPostState
from app.states.membership_state import MembershipState
from app.skill_categories import CATEGORY_GRADIENT


PHOTO_UPLOAD_ID = "help_post_photos"
PHOTO_ACCEPT = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
}


def category_icon(category: rx.Var[str], class_name: str) -> rx.Component:
    """Glyph for any category token — current keys plus legacy aliases."""
    return rx.match(
        category,
        ("translator", rx.icon("languages", class_name=class_name)),
        ("first_aid", rx.icon("briefcase-medical", class_name=class_name)),
        ("arts", rx.icon("palette", class_name=class_name)),
        ("artist", rx.icon("palette", class_name=class_name)),
        ("agriculture", rx.icon("sprout", class_name=class_name)),
        ("carer", rx.icon("hand-heart", class_name=class_name)),
        ("babysitter", rx.icon("hand-heart", class_name=class_name)),
        ("nanny", rx.icon("hand-heart", class_name=class_name)),
        ("construction", rx.icon("hard-hat", class_name=class_name)),
        ("builder", rx.icon("hard-hat", class_name=class_name)),
        ("cook", rx.icon("cooking-pot", class_name=class_name)),
        ("cleaner", rx.icon("brush", class_name=class_name)),
        ("craftwork", rx.icon("hammer", class_name=class_name)),
        ("craftworker", rx.icon("hammer", class_name=class_name)),
        ("healthcare", rx.icon("heart-pulse", class_name=class_name)),
        ("health_worker", rx.icon("heart-pulse", class_name=class_name)),
        ("labour", rx.icon("package", class_name=class_name)),
        ("labourer", rx.icon("package", class_name=class_name)),
        ("legal", rx.icon("scale", class_name=class_name)),
        ("media", rx.icon("camera", class_name=class_name)),
        ("sales", rx.icon("shopping-bag", class_name=class_name)),
        ("spirituality", rx.icon("sparkles", class_name=class_name)),
        ("sports", rx.icon("dumbbell", class_name=class_name)),
        ("coach", rx.icon("dumbbell", class_name=class_name)),
        ("fitness", rx.icon("dumbbell", class_name=class_name)),
        ("teaching", rx.icon("graduation-cap", class_name=class_name)),
        ("teacher", rx.icon("graduation-cap", class_name=class_name)),
        ("technician", rx.icon("cpu", class_name=class_name)),
        ("tourism", rx.icon("map", class_name=class_name)),
        ("workshop", rx.icon("wrench", class_name=class_name)),
        ("mechanic", rx.icon("car", class_name=class_name)),
        ("music", rx.icon("music", class_name=class_name)),
        rx.icon("hand-helping", class_name=class_name),
    )


def category_card(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            category_icon(item["value"], "size-4 text-white"),
            aria_hidden="true",
            style={
                "--category-fill": item["color"],
                "background": CATEGORY_GRADIENT,
            },
            class_name="flex size-7 shrink-0 items-center justify-center rounded-full",
        ),
        rx.el.span(ui(item["label"]), class_name="flex-1 text-left"),
        rx.el.span(
            rx.cond(
                HelpPostState.selected_categories.contains(item["value"]),
                rx.icon("check", class_name="h-3.5 w-3.5"),
                rx.fragment(),
            ),
            class_name=rx.cond(
                HelpPostState.selected_categories.contains(item["value"]),
                "flex size-5 items-center justify-center rounded border border-[#fba922] bg-[#fba922] text-black",
                "flex size-5 items-center justify-center rounded border border-[#d4d4d4] bg-white text-black",
            ),
        ),
        type="button",
        role="checkbox",
        aria_checked=HelpPostState.selected_categories.contains(item["value"]),
        on_click=lambda: HelpPostState.set_category(item["value"]),
        class_name="flex w-full items-center gap-3 rounded-lg bg-white px-3 py-2 text-sm text-[#111827] hover:bg-[#fff7e8] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def option_item(item: dict[str, str]) -> rx.Component:
    return rx.el.option(ui(item["label"]), value=item["value"])


def urgency_label(value: rx.Var[str]) -> rx.Var[str]:
    return rx.match(
        value,
        ("flexible", ui("Flexible")),
        ("soon", ui("Soon")),
        ("urgent", ui("Urgent")),
        ui(value),
    )


def photo_thumbnail(photo_path: rx.Var[str]) -> rx.Component:
    return rx.image(
        src=rx.get_upload_url(photo_path),
        alt=ui("Attached job photo"),
        class_name="h-20 w-full rounded-xl border border-[#e5e5e5] object-cover bg-[#fff7e8]",
    )


def square_photo_thumbnail(photo_path: rx.Var[str]) -> rx.Component:
    """Recent-request thumbnail: a true square crop at every breakpoint."""
    return rx.image(
        src=rx.get_upload_url(photo_path),
        alt=ui("Attached job photo"),
        class_name="aspect-square w-full rounded-xl border border-[#e5e5e5] object-cover bg-[#fff7e8]",
    )


def pending_photo_tile(photo_path: rx.Var[str], index: int) -> rx.Component:
    return rx.el.div(
        rx.image(
            src=rx.get_upload_url(photo_path),
            alt=ui("Photo ready to post"),
            class_name="aspect-square w-full rounded-xl border border-[#d4d4d4] object-cover bg-[#fff7e8]",
        ),
        rx.el.span(
            index + 1,
            class_name="absolute left-2 top-2 flex size-5 items-center justify-center rounded-full bg-[#111827]/80 text-[10px] font-bold text-white",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-3.5 w-3.5"),
            type="button",
            title=ui("Remove this photo"),
            on_click=lambda: HelpPostState.remove_photo(photo_path),
            class_name="absolute right-2 top-2 flex size-6 items-center justify-center rounded-full bg-white/95 text-[#e08b12] border border-[#d4d4d4] transition-colors hover:bg-[#e08b12] hover:text-white",
        ),
        rx.el.span(
            ui("WebP - under 1 MB"),
            class_name="absolute inset-x-2 bottom-2 rounded-full bg-[#111827]/75 px-2 py-0.5 text-center text-[10px] font-semibold text-white",
        ),
        class_name="relative w-full",
    )


def job_info_field() -> rx.Component:
    return rx.el.div(
        field_label("Job info", "required - max 500 characters"),
        rx.el.textarea(
            name="description",
            rows="6",
            max_length=500,
            placeholder=ui(
                "I'm moving out of a fourth-floor flat and need someone strong for an hour. Lift is broken, boxes are packed and light-ish..."
            ),
            on_change=HelpPostState.set_job_info.debounce(250),
            class_name=INPUT_CLASS + " resize-y leading-relaxed",
        ),
        rx.el.div(
            rx.el.span(
                ui(
                    "Describe the job, the place and what a helper should bring."
                ),
                class_name="text-xs font-medium text-[#4b5563]",
            ),
            rx.el.span(
                ui_template(
                    "{count} characters left",
                    "count",
                    HelpPostState.job_info_remaining.to_string(),
                ),
                class_name=rx.cond(
                    HelpPostState.job_info_near_limit,
                    "text-xs font-semibold text-[#e08b12] shrink-0",
                    "text-xs font-semibold text-[#e08b12] shrink-0",
                ),
            ),
            class_name="mt-1.5 flex items-baseline justify-between gap-3 w-full",
        ),
        class_name="w-full",
    )


def photo_upload_section() -> rx.Component:
    return rx.el.div(
        field_label("Upload Photos", "optional - maximum 5"),
        rx.cond(
            (HelpPostState.pending_photo_paths.length() < 5)
            | HelpPostState.photo_busy,
            rx.upload.root(
                rx.cond(
                    HelpPostState.photo_busy,
                    rx.el.div(
                        rx.image(
                            src=BRAND_LOGO_SRC,
                            alt=BRAND_LOGO_ALT,
                            class_name="size-10 rounded-full object-cover motion-safe:animate-pulse",
                        ),
                        rx.el.p(
                            ui("Pictures are being uploaded"),
                            class_name="text-sm font-semibold text-[#111827]",
                        ),
                        role="status",
                        aria_live="polite",
                        class_name="flex min-h-28 w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[#fba922] bg-[#fff7e8] p-5",
                    ),
                    rx.el.div(
                        rx.icon("camera", class_name="h-6 w-6 text-[#e08b12]"),
                        rx.el.p(
                            ui("Drop or click to select photos"),
                            class_name="text-sm font-semibold text-[#111827]",
                        ),
                        rx.el.p(
                            ui(
                                "Static JPEG/JPG, PNG or WebP only · 3 MB maximum · no video"
                            ),
                            class_name="text-xs font-medium text-[#4b5563]",
                        ),
                        rx.el.p(
                            ui_template(
                                "{count} of 5 slots free",
                                "count",
                                HelpPostState.photo_slots_left.to_string(),
                            ),
                            class_name="text-xs font-semibold text-[#e08b12]",
                        ),
                        class_name="flex min-h-28 w-full flex-col items-center justify-center gap-1 rounded-2xl border-2 border-dashed border-[#fba922] bg-[#fff7e8] px-5 py-5 text-center transition-colors hover:border-[#e08b12] hover:bg-[#fff0d6]",
                    ),
                ),
                id=PHOTO_UPLOAD_ID,
                disabled=HelpPostState.photo_busy,
                accept=PHOTO_ACCEPT,
                multiple=True,
                max_files=5,
                on_drop=HelpPostState.handle_upload(
                    rx.upload_files(upload_id=PHOTO_UPLOAD_ID)
                ),
            ),
            rx.el.div(
                rx.icon("check", class_name="h-5 w-5 text-[#111827]"),
                rx.el.p(
                    ui("Five photos attached - remove one to swap it out"),
                    class_name="text-sm font-semibold text-[#111827]",
                ),
                class_name="flex min-h-28 w-full items-center justify-center gap-2 rounded-2xl border border-[#f6c66f] bg-[#fff7e8] px-5 py-5 text-center",
            ),
        ),
        error_banner(ui(HelpPostState.localized_feedback["photo_error"])),
        rx.cond(
            HelpPostState.photo_notice,
            rx.el.div(
                rx.icon(
                    "circle-check-big",
                    class_name="h-3.5 w-3.5 text-[#111827] shrink-0",
                ),
                rx.el.span(
                    ui(HelpPostState.localized_feedback["photo_notice"]),
                    class_name="text-xs font-semibold text-[#111827]",
                ),
                class_name="flex items-center gap-2 rounded-xl border border-[#fba922] bg-[#fba922] px-3 py-2 w-full",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpPostState.pending_photo_paths.length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.icon("image", class_name="h-3.5 w-3.5 text-[#e08b12]"),
                    rx.el.span(
                        ui_template(
                            "{count} / 5 attached",
                            "count",
                            HelpPostState.pending_photo_paths.length().to_string(),
                        ),
                        class_name="text-xs font-semibold text-[#e08b12]",
                    ),
                    rx.el.span(
                        ui("Tap the cross to remove a photo before posting."),
                        class_name="text-xs font-medium text-[#4b5563]",
                    ),
                    class_name="flex flex-wrap items-center gap-x-2 gap-y-1",
                ),
                rx.el.div(
                    rx.foreach(
                        HelpPostState.pending_photo_paths,
                        lambda path, index: pending_photo_tile(path, index),
                    ),
                    class_name="grid grid-cols-2 sm:grid-cols-5 gap-2 w-full",
                ),
                class_name="flex flex-col gap-2 rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-3",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col gap-2 w-full",
    )


def cadence_card(item: dict[str, str]) -> rx.Component:
    """Tap-first cadence choice — helping-green when chosen."""
    return rx.el.button(
        rx.el.div(
            rx.icon("repeat", class_name="h-4 w-4"),
            class_name=rx.cond(
                HelpPostState.repeat_enabled
                & (HelpPostState.repeat_cadence == item["value"]),
                "flex items-center justify-center size-9 rounded-xl bg-white text-[#111827] shrink-0",
                "flex items-center justify-center size-9 rounded-xl bg-[#eaf1ff] text-[#e08b12] shrink-0",
            ),
        ),
        rx.el.div(
            rx.el.p(
                ui(item["label"]),
                class_name=rx.cond(
                    HelpPostState.repeat_enabled
                    & (HelpPostState.repeat_cadence == item["value"]),
                    "text-sm font-bold text-[#111827] text-left",
                    "text-sm font-bold text-[#111827] text-left",
                ),
            ),
            rx.el.p(
                ui(item["blurb"]),
                class_name=rx.cond(
                    HelpPostState.repeat_enabled
                    & (HelpPostState.repeat_cadence == item["value"]),
                    "text-xs font-medium text-[#111827]/80 mt-0.5 text-left",
                    "text-xs font-medium text-[#4b5563] mt-0.5 text-left",
                ),
            ),
            class_name="min-w-0",
        ),
        type="button",
        aria_pressed=rx.cond(
            HelpPostState.repeat_enabled
            & (HelpPostState.repeat_cadence == item["value"]),
            "true",
            "false",
        ),
        on_click=lambda: HelpPostState.set_repeat_cadence(item["value"]),
        class_name=rx.cond(
            HelpPostState.repeat_enabled
            & (HelpPostState.repeat_cadence == item["value"]),
            "flex items-start gap-3 w-full rounded-2xl border-2 border-[#fba922] bg-[#fba922] p-3 transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#111827]",
            "flex items-start gap-3 w-full rounded-2xl border border-[#f6c66f] bg-white p-3 transition-colors hover:border-[#fba922] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#f6c66f]",
        ),
    )


def repeat_section() -> rx.Component:
    """Optional recurrence. One-time stays the default until tapped on."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("repeat", class_name="h-4 w-4 text-[#e08b12]"),
                rx.el.h3(
                    ui("Repeat this request"),
                    class_name="text-sm font-bold text-[#111827]",
                ),
                rx.el.span(
                    ui(HelpPostState.repeat_summary),
                    class_name=rx.cond(
                        HelpPostState.repeat_enabled,
                        "w-fit rounded-full bg-[#fba922] px-3 py-1 text-xs font-bold text-[#111827]",
                        "w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-bold text-[#e08b12]",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2 min-w-0",
            ),
            rx.el.button(
                rx.cond(
                    HelpPostState.repeat_enabled,
                    rx.icon("toggle-right", class_name="h-4 w-4"),
                    rx.icon("toggle-left", class_name="h-4 w-4"),
                ),
                rx.cond(
                    HelpPostState.repeat_enabled,
                    ui("Repeating"),
                    ui("One-time"),
                ),
                type="button",
                aria_pressed=rx.cond(
                    HelpPostState.repeat_enabled, "true", "false"
                ),
                on_click=HelpPostState.toggle_repeat,
                class_name=rx.cond(
                    HelpPostState.repeat_enabled,
                    "w-fit shrink-0 flex items-center gap-1.5 rounded-full bg-[#fba922] px-4 py-2 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12]",
                    "w-fit shrink-0 flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-4 py-2 text-xs font-bold text-[#4b5563] transition-colors hover:border-[#fba922] hover:text-[#111827]",
                ),
            ),
            class_name="flex w-full flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            ui(
                "Off by default. When on, each date is created automatically from the date and time you picked above — always within your posting allowance."
            ),
            class_name="mt-1.5 text-xs font-medium leading-relaxed text-[#4b5563]",
        ),
        rx.cond(
            HelpPostState.repeat_enabled,
            rx.el.div(
                rx.el.div(
                    rx.foreach(HelpPostState.cadence_choices, cadence_card),
                    class_name="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full",
                ),
                rx.el.div(
                    rx.cond(
                        HelpPostState.repeat_interval_applies,
                        rx.el.div(
                            field_label("How often", "optional"),
                            select_wrapper(
                                rx.el.select(
                                    rx.foreach(
                                        HelpPostState.repeat_interval_options,
                                        option_item,
                                    ),
                                    value=HelpPostState.repeat_interval.to_string(),
                                    on_change=HelpPostState.set_repeat_interval,
                                    class_name=SELECT_CLASS,
                                )
                            ),
                            class_name="w-full",
                        ),
                        rx.el.div(
                            field_label("How often", "fixed"),
                            rx.el.p(
                                ui("Every two weeks, on the same weekday."),
                                class_name="rounded-xl border border-[#f6c66f] bg-[#fff7e8]/60 px-4 py-3 text-xs font-semibold text-[#e08b12]",
                            ),
                            class_name="w-full",
                        ),
                    ),
                    rx.el.div(
                        field_label("Stop repeating on", "optional"),
                        rx.el.input(
                            name="repeat_end_date",
                            type="date",
                            min=HelpPostState.schedule_min.split("T")[0],
                            max=HelpPostState.schedule_max.split("T")[0],
                            class_name=INPUT_CLASS,
                        ),
                        class_name="w-full",
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mt-3",
                ),
                class_name="w-full mt-3",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-2xl border border-[#f6c66f] bg-[#fff7e8] p-4",
    )


def schedule_status_badge(schedule: dict[str, str]) -> rx.Component:
    return rx.el.span(
        ui(schedule["status_label"]),
        class_name=rx.cond(
            schedule["is_active"],
            "w-fit shrink-0 rounded-full bg-[#fba922] px-3 py-1 text-xs font-bold text-[#111827]",
            rx.cond(
                schedule["is_paused"],
                "w-fit shrink-0 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-bold text-[#e08b12]",
                "w-fit shrink-0 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-bold text-[#4b5563]",
            ),
        ),
    )


def schedule_card(schedule: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon("repeat", class_name="h-4 w-4 text-white"),
                class_name="flex items-center justify-center size-9 rounded-xl bg-[#e08b12] shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    schedule["title"],
                    class_name="text-sm font-bold text-[#111827] leading-tight",
                ),
                rx.el.p(
                    ui(schedule["cadence_label"]),
                    class_name="mt-0.5 text-xs font-semibold text-[#e08b12]",
                ),
                class_name="min-w-0 flex-1",
            ),
            schedule_status_badge(schedule),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                rx.icon("calendar-clock", class_name="h-3 w-3"),
                ui(schedule["next_label"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12]",
            ),
            rx.el.span(
                rx.icon("calendar-x", class_name="h-3 w-3"),
                ui(schedule["end_label"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#4b5563]",
            ),
            rx.el.span(
                rx.icon("layers", class_name="h-3 w-3"),
                ui_template(
                    "{count} created", "count", schedule["count"].to_string()
                ),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12]",
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        rx.cond(
            schedule["is_ended"],
            rx.el.p(
                ui("This repeating request has finished."),
                class_name="mt-3 text-xs font-medium text-[#4b5563]",
            ),
            rx.el.div(
                rx.cond(
                    schedule["is_active"],
                    rx.el.button(
                        rx.icon("pause", class_name="h-3.5 w-3.5"),
                        ui("Pause"),
                        type="button",
                        disabled=HelpPostState.schedule_busy_id
                        == schedule["id"],
                        on_click=lambda: HelpPostState.pause_schedule(
                            schedule["id"]
                        ),
                        class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-4 py-2 text-xs font-bold text-[#4b5563] transition-colors hover:border-[#d4d4d4] hover:text-[#e08b12] disabled:opacity-60",
                    ),
                    rx.el.button(
                        rx.icon("play", class_name="h-3.5 w-3.5"),
                        ui("Resume"),
                        type="button",
                        disabled=HelpPostState.schedule_busy_id
                        == schedule["id"],
                        on_click=lambda: HelpPostState.resume_schedule(
                            schedule["id"]
                        ),
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-4 py-2 text-xs font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
                    ),
                ),
                rx.el.button(
                    rx.icon("square", class_name="h-3.5 w-3.5"),
                    ui("End"),
                    type="button",
                    disabled=HelpPostState.schedule_busy_id == schedule["id"],
                    on_click=lambda: HelpPostState.end_schedule(schedule["id"]),
                    class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-4 py-2 text-xs font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] disabled:opacity-60",
                ),
                class_name="mt-3 flex flex-wrap items-center gap-2",
            ),
        ),
        class_name="gah-inset-row w-full bg-white p-4",
    )


def recurring_section() -> rx.Component:
    """Compact overview of every repeating request this member owns."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("repeat", class_name="h-4 w-4 text-[#e08b12]"),
                rx.el.h3(
                    ui("Recurring requests"),
                    class_name="text-sm font-bold text-[#111827]",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.span(
                HelpPostState.recurring_schedules.length(),
                class_name="w-fit shrink-0 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
            ),
            class_name="flex w-full items-center justify-between gap-3",
        ),
        rx.cond(
            ui(HelpPostState.localized_feedback["schedule_error"]),
            rx.el.p(
                HelpPostState.localized_feedback["schedule_error"],
                role="alert",
                class_name="mt-2 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ui(HelpPostState.localized_feedback["schedule_notice"]),
            rx.el.p(
                HelpPostState.localized_feedback["schedule_notice"],
                class_name="mt-2 rounded-xl bg-[#fba922] px-3 py-2 text-xs font-bold text-[#111827]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            HelpPostState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="mt-3 w-full",
            ),
            rx.cond(
                HelpPostState.has_recurring,
                rx.el.div(
                    rx.foreach(
                        HelpPostState.recurring_schedules,
                        lambda item: schedule_card(item),
                    ),
                    class_name="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-3 w-full",
                ),
                rx.el.div(
                    rx.icon(
                        "repeat", class_name="h-5 w-5 text-[#e08b12] mb-1.5"
                    ),
                    rx.el.p(
                        ui("No repeating requests yet"),
                        class_name="text-sm font-bold text-[#111827]",
                    ),
                    rx.el.p(
                        ui(
                            "Turn on “Repeat this request” in the form above and each date will be created for you."
                        ),
                        class_name="mt-1 max-w-xl text-xs font-medium leading-relaxed text-[#4b5563]",
                    ),
                    class_name="mt-3 flex flex-col items-center justify-center text-center rounded-2xl border border-dashed border-[#f6c66f] bg-white px-5 py-6",
                ),
            ),
        ),
        class_name="gah-main-card w-full bg-[#ffffff] p-4 sm:p-5",
    )


def submit_button() -> rx.Component:
    return rx.el.button(
        rx.cond(
            HelpPostState.is_saving,
            rx.el.span(
                rx.spinner(class_name="h-4 w-4"),
                ui("Posting your request…"),
                class_name="flex items-center justify-center gap-2",
            ),
            rx.el.span(
                rx.icon("send", class_name="h-4 w-4"),
                ui("Post help request"),
                class_name="flex items-center justify-center gap-2",
            ),
        ),
        type="submit",
        disabled=HelpPostState.is_saving,
        class_name="w-full sm:w-fit rounded-xl bg-[#fba922] px-6 py-3 text-sm font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#111827]",
    )


CATEGORY_LISTENERS = """
(() => {
    const boundary = document.getElementById('job-category-boundary');
    if (!boundary) return;
    boundary.gahCategoryCleanup?.();
    const close = (event) => {
        const trigger = boundary.querySelector('[aria-controls="job-category-options"]');
        if (trigger?.getAttribute('aria-expanded') !== 'true') return;
        const escape = event.type === 'keydown' && event.key === 'Escape';
        if (event.type === 'keydown' && !escape) return;
        if (!escape && boundary.contains(event.target)) return;
        boundary.querySelector('[data-category-close]')?.click();
        if (escape) { event.preventDefault(); trigger.focus(); }
    };
    document.addEventListener('click', close);
    document.addEventListener('scroll', close, true);
    document.addEventListener('keydown', close);
    boundary.gahCategoryCleanup = () => {
        document.removeEventListener('click', close);
        document.removeEventListener('scroll', close, true);
        document.removeEventListener('keydown', close);
        delete boundary.gahCategoryCleanup;
    };
    const cleanup = () => boundary.gahCategoryCleanup?.();
    document.addEventListener('gah-category-unmount', cleanup, {once: true});
})();
"""


def category_section() -> rx.Component:
    return rx.el.div(
        field_label("Job category", HelpPostState.localized_category_slot_hint),
        rx.el.button(
            rx.el.span(
                rx.cond(
                    ui(HelpPostState.category_summary_label),
                    ui(HelpPostState.category_summary_label),
                    ui("Choose job categories"),
                ),
                class_name="flex-1 text-left",
            ),
            rx.el.span(
                HelpPostState.selected_categories.length(),
                class_name="text-xs text-[#e08b12]",
            ),
            disclosure_arrow(HelpPostState.category_dropdown_open),
            type="button",
            aria_expanded=HelpPostState.category_dropdown_open,
            aria_controls="job-category-options",
            on_click=HelpPostState.toggle_category_dropdown,
            class_name="flex w-full items-center gap-3 rounded-xl border border-[#f6c66f] bg-white px-4 py-3 text-sm text-[#111827] hover:border-[#e08b12] focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.cond(
            HelpPostState.category_dropdown_open,
            rx.el.div(
                rx.foreach(HelpPostState.categories, category_card),
                role="group",
                aria_label=ui("Job categories"),
                id="job-category-options",
                class_name="mt-2 max-h-72 overflow-y-auto rounded-xl border border-[#f6c66f] bg-white p-1",
            ),
            rx.fragment(),
        ),
        rx.el.p(
            ui(HelpPostState.localized_category_count_label),
            class_name="mt-2 text-xs text-[#4b5563]",
        ),
        error_banner(ui(HelpPostState.localized_feedback["error"])),
        rx.el.button(
            ui("Close job categories"),
            type="button",
            custom_attrs={"data-category-close": "true"},
            on_click=HelpPostState.close_category_dropdown,
            class_name="sr-only focus:not-sr-only bg-white text-[#e08b12]",
        ),
        id="job-category-boundary",
        on_mount=rx.call_script(CATEGORY_LISTENERS),
        on_unmount=[
            rx.call_script(
                "document.dispatchEvent(new Event('gah-category-unmount'));"
            ),
            HelpPostState.close_category_dropdown,
        ],
        class_name="w-full",
    )


def reward_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            field_label("Reward you can offer", "required"),
            select_wrapper(
                rx.el.select(
                    rx.foreach(HelpPostState.reward_options, option_item),
                    value=HelpPostState.reward_type,
                    on_change=HelpPostState.set_reward_type,
                    class_name=SELECT_CLASS,
                )
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.cond(
                HelpPostState.reward_is_other,
                field_label("Describe your reward", "required"),
                field_label("Reward details", "optional"),
            ),
            rx.el.input(
                name="reward_details",
                placeholder=ui(
                    "Home-cooked dinner with my family in the old town"
                ),
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
    )


def details_heading() -> rx.Component:
    return rx.el.div(
        rx.icon("notebook-pen", class_name="h-4 w-4 text-[#e08b12]"),
        rx.el.h3(
            ui("Posting details"),
            class_name="text-sm font-semibold text-[#111827]",
        ),
        rx.el.span(
            ui("reward, meeting point and timing"),
            class_name="text-xs font-medium text-[#4b5563]",
        ),
        class_name="flex flex-wrap items-center gap-2 w-full border-t border-[#e5e5e5] pt-5",
    )


def post_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            field_label("Job title", "required"),
            rx.el.input(
                name="title",
                placeholder=ui("Two hands to carry boxes up three flights"),
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        category_section(),
        job_info_field(),
        photo_upload_section(),
        details_heading(),
        rx.el.div(
            field_label("Requester name", "who helpers should ask for"),
            rx.el.input(
                name="requester_name",
                default_value=AuthState.display_name,
                key=AuthState.display_name,
                placeholder=ui("Maya from Lisbon"),
                class_name=INPUT_CLASS,
            ),
            class_name="w-full",
        ),
        reward_section(),
        rx.el.div(
            rx.el.div(
                field_label("Meeting point", "required"),
                rx.el.input(
                    name="location_name",
                    placeholder=ui("Rua das Flores 22, by the blue door"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                field_label("City", "required"),
                rx.el.input(
                    name="city",
                    placeholder=ui("Porto"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                field_label("Country", "optional"),
                rx.el.input(
                    name="country",
                    placeholder=ui("Portugal"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4 w-full",
        ),
        rx.el.div(
            rx.el.div(
                field_label(
                    "Date & time needed", "required · UTC · within two years"
                ),
                rx.el.input(
                    name="scheduled_for",
                    type="datetime-local",
                    required=True,
                    min=HelpPostState.schedule_min,
                    max=HelpPostState.schedule_max,
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                field_label("How long will it take?"),
                select_wrapper(
                    rx.el.select(
                        rx.foreach(HelpPostState.duration_options, option_item),
                        name="duration_minutes",
                        default_value="60",
                        class_name=SELECT_CLASS,
                    )
                ),
                class_name="w-full",
            ),
            rx.el.div(
                field_label("Urgency"),
                select_wrapper(
                    rx.el.select(
                        rx.foreach(HelpPostState.urgency_options, option_item),
                        name="urgency",
                        default_value="flexible",
                        class_name=SELECT_CLASS,
                    )
                ),
                class_name="w-full",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4 w-full",
        ),
        rx.cond(
            MembershipState.is_premium,
            rx.el.div(
                field_label("Number of people required", "Premium · 1–500"),
                rx.el.input(
                    name="helpers_needed",
                    type="number",
                    min=1,
                    max=500,
                    step=1,
                    default_value="1",
                    required=True,
                    aria_label=ui("Number of people required"),
                    class_name=INPUT_CLASS,
                ),
                rx.el.p(
                    ui(
                        "Premium lets you confirm up to 500 helpers. Your request stays open until all places are filled."
                    ),
                    class_name="mt-1.5 text-xs font-medium text-[#4b5563]",
                ),
                class_name="w-full",
            ),
            rx.el.p(
                ui(
                    "Free requests are for one helper. Premium members can request 1–500 people."
                ),
                class_name="text-xs font-medium text-[#4b5563]",
            ),
        ),
        repeat_section(),
        submit_button(),
        on_submit=HelpPostState.create_post,
        on_mount=HelpPostState.refresh_date_bounds,
        reset_on_submit=False,
        class_name="gah-main-card flex flex-col gap-5 w-full bg-[#ffffff] p-6 sm:p-8",
    )


def count_card(label: str, value: rx.Var[int], icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex items-center justify-center size-9 rounded-xl bg-[#fff7e8] shrink-0",
        ),
        rx.el.p(value, class_name="mt-3 text-3xl font-bold text-[#111827]"),
        rx.el.p(
            ui(label),
            class_name="text-xs font-semibold uppercase tracking-wide text-[#4b5563]",
        ),
        class_name="w-full rounded-2xl border border-[#e5e5e5] bg-white p-5",
    )


def status_badge(status: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        rx.match(
            status,
            ("open", ui("Open")),
            ("matched", ui("Confirmed")),
            ("completed", ui("Completed")),
            ("cancelled", ui("Cancelled")),
            ("expired", ui("Expired")),
            ui(status),
        ),
        class_name=rx.cond(
            status == "open",
            "ml-auto w-fit rounded-full bg-[#fba922] px-3 py-1 text-xs font-semibold text-[#111827] capitalize shrink-0",
            "ml-auto w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#4b5563] capitalize shrink-0",
        ),
    )


def delete_confirm_row(post: dict[str, str]) -> rx.Component:
    """Inline confirm/keep controls for this exact journal entry."""
    return rx.el.div(
        rx.el.p(
            ui_template_multi(
                "Remove “{title}” from the board?", {"title": post["title"]}
            ),
            class_name="text-xs font-bold text-[#111827] text-center",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    HelpHubState.removal_busy,
                    rx.spinner(class_name="h-3.5 w-3.5"),
                    rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                ),
                ui("Yes, remove it"),
                type="button",
                disabled=HelpHubState.removal_busy,
                aria_label=ui("Confirm removing this help request"),
                on_click=HelpHubState.confirm_removal,
                class_name="flex w-fit items-center gap-1.5 rounded-full bg-[#e08b12] px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#f6c66f]",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                ui("Keep it"),
                type="button",
                disabled=HelpHubState.removal_busy,
                aria_label=ui("Keep this help request"),
                on_click=HelpHubState.cancel_removal,
                class_name="flex w-fit items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-4 py-2 text-xs font-bold text-[#4b5563] transition-colors hover:bg-[#fff7e8] disabled:opacity-60",
            ),
            class_name="mt-2 flex flex-wrap items-center justify-center gap-2",
        ),
        class_name="mt-4 w-full rounded-2xl border border-[#d4d4d4] bg-[#fff7e8] p-3",
    )


def owner_edit_form() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            ui("Edit help request"),
            class_name="text-center text-base font-semibold text-[#292929]",
        ),
        rx.el.p(
            ui(
                "Keep your current location, or place a replacement pin below. Editing closes as soon as any help offer arrives."
            ),
            class_name="text-sm text-[#525252]",
        ),
        compact_request_fields(HelpPostState, "edit-help-request"),
        error_banner(ui(HelpPostState.localized_feedback["edit_error"])),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    HelpPostState.edit_busy, ui("Saving…"), ui("Save changes")
                ),
                type="button",
                disabled=HelpPostState.edit_busy,
                on_click=HelpPostState.save_edit,
                class_name="rounded-full bg-[#fba922] px-4 py-2 text-sm font-bold text-[#292929] disabled:opacity-50",
            ),
            rx.el.button(
                ui("Cancel"),
                type="button",
                disabled=HelpPostState.edit_busy,
                on_click=HelpPostState.cancel_edit,
                class_name="rounded-full border border-[#f6c66f] bg-white px-4 py-2 text-sm text-[#404040]",
            ),
            class_name="flex justify-center gap-3",
        ),
        class_name="mt-4 flex w-full flex-col gap-4 border-t border-[#f6c66f] bg-white pt-4",
    )


def owner_delete_footer(post: dict[str, str]) -> rx.Component:
    """Quiet destructive action at the foot of an own, still-open request."""
    return rx.cond(
        post["status"] == "open",
        rx.cond(
            HelpHubState.removal_selected_id == post["id"],
            delete_confirm_row(post),
            rx.el.div(
                rx.cond(
                    post.get("can_edit", False).to(bool),
                    rx.el.button(
                        rx.icon("pencil", class_name="size-3.5"),
                        ui("Edit"),
                        type="button",
                        on_click=lambda: HelpPostState.begin_edit(post["id"]),
                        class_name="flex w-fit items-center gap-1.5 rounded-full border border-[#f6c66f] bg-white px-4 py-2 text-xs font-bold text-[#e08b12]",
                    ),
                    rx.fragment(),
                ),
                rx.el.button(
                    rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                    ui("Delete"),
                    type="button",
                    aria_label=ui_template_multi(
                        "Delete {title}", {"title": post["title"]}
                    ),
                    on_click=lambda: HelpHubState.select_removal(
                        post["id"], post["title"]
                    ),
                    class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-4 py-2 text-xs font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#f6c66f]",
                ),
                class_name="mt-4 flex w-full items-center justify-center border-t border-[#e5e5e5] pt-4",
            ),
        ),
        rx.fragment(),
    )


# Flat variants drop the card shell so content sits directly in its section.
CARD_SHELL = {
    False: "w-full rounded-2xl border border-[#e5e5e5] bg-white p-5",
    True: "gah-inset-row w-full py-4 first:pt-0 last:pb-0",
}
PHOTO_SHELL = {
    False: "mt-4 rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-3",
    True: "mt-4",
}
PHOTO_TILE = {False: photo_thumbnail, True: square_photo_thumbnail}
# Recent (flat) request thumbnails render at half their previous size, so the
# column count doubles at every breakpoint.
PHOTO_GRID = {
    False: "grid grid-cols-2 sm:grid-cols-5 gap-2 w-full",
    True: "grid grid-cols-4 sm:grid-cols-10 gap-1.5 w-full",
}


def photo_caption(flat: bool) -> rx.Component:
    """Recent (flat) requests show the grid only — no label, no camera icon."""
    return rx.cond(
        flat,
        rx.fragment(),
        rx.el.div(
            rx.icon("camera", class_name="h-3.5 w-3.5 text-[#e08b12]"),
            rx.el.span(
                ui("Job photos"),
                class_name="text-xs font-semibold text-[#e08b12]",
            ),
            class_name="flex items-center gap-1.5",
        ),
    )


def post_card(
    post: dict[str, str],
    deletable: bool = False,
    flat: bool = False,
    compact: bool = False,
) -> rx.Component:
    """Shared request card. Owner deletion only when explicitly enabled."""
    return rx.el.div(
        corner_activity_dot(
            NotificationState.unread_help_post_ids.contains(post["id"].to(int)),
            ui("New activity on this help request"),
        ),
        rx.cond(
            compact,
            browser_translatable_text(
                post["description"],
                class_name="text-sm font-medium text-[#4b5563] leading-relaxed",
            ),
            rx.el.div(
                rx.el.div(
                    category_icon(post["category"], "h-5 w-5 text-white"),
                    class_name="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[#e08b12]",
                ),
                rx.el.div(
                    rx.el.p(
                        post["title"],
                        class_name="text-sm font-semibold text-[#111827]",
                    ),
                    browser_translatable_text(
                        post["description"],
                        class_name="text-sm font-medium text-[#4b5563] mt-1 leading-relaxed line-clamp-2",
                    ),
                    class_name="min-w-0 flex-1",
                ),
                status_badge(post["status"]),
                class_name="flex items-start gap-4 w-full",
            ),
        ),
        rx.el.div(
            rx.el.span(
                rx.icon("compass", class_name="h-3 w-3"),
                ui(post["category_label"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#eaf1ff] px-3 py-1 text-xs font-bold text-[#b86e08]",
            ),
            rx.el.span(
                rx.icon("gift", class_name="h-3 w-3"),
                ui(post["reward_label"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12]",
            ),
            rx.el.span(
                rx.icon("map-pin", class_name="h-3 w-3"),
                post["location"],
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#4b5563]",
            ),
            rx.el.span(
                rx.icon("calendar", class_name="h-3 w-3"),
                post["scheduled"],
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#4b5563]",
            ),
            rx.el.span(
                rx.icon("clock", class_name="h-3 w-3"),
                urgency_label(post["urgency"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#4b5563] capitalize",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        rx.cond(
            post["photos"].length() > 0,
            rx.el.div(
                photo_caption(flat),
                rx.el.div(
                    rx.foreach(post["photos"], PHOTO_TILE[flat]),
                    class_name=PHOTO_GRID[flat],
                ),
                class_name=PHOTO_SHELL[flat],
            ),
            rx.fragment(),
        ),
        rx.cond(
            post["reward_details"],
            rx.el.p(
                post["reward_details"],
                class_name="text-xs font-medium text-[#4b5563] mt-3 italic",
            ),
            rx.fragment(),
        ),
        rx.cond(deletable, owner_delete_footer(post), rx.fragment()),
        rx.cond(
            deletable & (HelpPostState.edit_post_id == post["id"]),
            owner_edit_form(),
            rx.fragment(),
        ),
        rx.cond(
            deletable & (HelpPostState.edit_post_id == 0),
            error_banner(ui(HelpPostState.localized_feedback["edit_error"])),
            rx.fragment(),
        ),
        class_name=rx.cond(
            flat,
            "relative w-full bg-white py-4",
            "relative w-full rounded-2xl border border-gray-200 bg-white p-4",
        ),
    )


def recent_post_card(post: dict[str, str]) -> rx.Component:
    return rx.el.div(
        post_card(post, deletable=True),
        rx.el.p(
            rx.icon("users", class_name="h-3.5 w-3.5"),
            ui_template(
                "People required: {count}",
                "count",
                post["helpers_needed"].to_string(),
            ),
            class_name="flex items-center gap-1.5 px-5 pb-3 text-xs font-semibold text-[#e08b12]",
        ),
        class_name="w-full",
    )


def recent_posts_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    ui("Your help requests"),
                    class_name="text-lg font-semibold text-[#111827]",
                ),
                rx.el.p(
                    ui("The last six pages of your journal — freshest first."),
                    class_name="text-sm font-medium text-[#4b5563] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                ui("Refresh"),
                type="button",
                on_click=HelpPostState.load_recent,
                class_name="w-fit flex items-center gap-2 rounded-full border border-[#d4d4d4] bg-white px-4 py-2 text-xs font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
            ),
            class_name="w-full flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3",
        ),
        rx.el.div(
            count_card(
                "Requests posted", HelpPostState.counts["total"], "notebook-pen"
            ),
            count_card("Still open", HelpPostState.counts["open"], "map-pin"),
            count_card(
                "Upcoming", HelpPostState.counts["upcoming"], "calendar"
            ),
            class_name="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full",
        ),
        rx.cond(
            HelpPostState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 w-full rounded-2xl bg-[#e5e5e5]"
                ),
                class_name="flex flex-col gap-3 w-full",
            ),
            rx.cond(
                HelpPostState.recent_posts.length() > 0,
                rx.el.div(
                    rx.foreach(HelpPostState.recent_posts, recent_post_card),
                    class_name="flex flex-col gap-3 w-full",
                ),
                rx.el.div(
                    rx.icon(
                        "hand-helping",
                        class_name="h-6 w-6 text-[#4b5563] mb-2",
                    ),
                    rx.el.p(
                        ui("No help requests posted yet."),
                        class_name="text-sm font-semibold text-[#4b5563]",
                    ),
                    rx.el.p(
                        ui(
                            "Fill in the form above and your first request will appear here."
                        ),
                        class_name="text-sm font-medium text-[#4b5563] mt-1",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-white/60 px-6 py-10",
                ),
            ),
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def help_post_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("notebook-pen", class_name="h-3.5 w-3.5"),
                    ui("Ask for help"),
                    class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#e08b12]",
                ),
                rx.el.h2(
                    ui("Post what you need a hand with."),
                    class_name="mt-3 text-2xl font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    ui(
                        "Describe the task, offer something warm in return, and pick the moment you need someone there."
                    ),
                    class_name="mt-1 text-sm font-medium text-[#4b5563] leading-relaxed",
                ),
                class_name="min-w-0",
            ),
            class_name="gah-main-card w-full bg-white p-6",
        ),
        error_banner(ui(HelpPostState.localized_feedback["error"])),
        success_banner(ui(HelpPostState.localized_feedback["success"])),
        post_form(),
        recurring_section(),
        recent_posts_section(),
        on_mount=HelpPostState.load_recent,
        class_name="flex flex-col gap-5 w-full",
    )
