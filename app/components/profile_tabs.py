import reflex as rx
from app.avatars import animal_avatar
from reflex.style import set_color_mode
from app.interface_i18n import ui, ui_template
from app.components.profile_form_feedback import (
    localized_profile_form_message,
    localized_profile_skills_summary,
)

from app.components.disclosure import disclosure_arrow

from app.components.feedback import (
    INPUT_CLASS,
    error_banner,
    field_label,
    avatar_with_tick,
    success_banner,
    verified_badge,
    verified_tick,
)
from app.components.admin_panel import admin_panel
from app.components.community_panel import community_panel
from app.components.contacts_panel import contacts_panel
from app.components.find_people_panel import find_people_panel
from app.components.header import contextual_header
from app.components.policy_screens import policy_links_row
from app.components.profile_metrics import metrics_section
from app.components.help_hub_panel import help_hub_panel
from app.components.help_post_panel import help_post_panel
from app.components.messages_panel import messages_panel
from app.components.membership_info import membership_information_section
from app.components.paywall import membership_notices_panel
from app.models import CATEGORY_LABELS, SETTINGS_LANGUAGE_OPTIONS
from app.states.auth_state import AuthState
from app.states.block_state import BlockedMember, BlockState
from app.states.notification_state import NotificationState
from app.components.onboarding import restart_tour_control
from app.states.profile_state import ProfileState

AVATAR_UPLOAD_ID = "profile_avatar_upload"


def avatar_src(path: rx.Var[str], seed: rx.Var[str] | str) -> rx.Var[str] | str:
    return rx.cond(
        path,
        rx.get_upload_url(path),
        animal_avatar(seed),
    )


STAT_CARDS: list[tuple[str, str, str]] = [
    ("posts_created", "Help posts written", "notebook-pen"),
    ("posts_open", "Still open", "map-pin"),
    ("applications_sent", "Offers you sent", "hand-helping"),
    ("applications_accepted", "Offers accepted", "circle-check-big"),
    ("tasks_helped", "Times you helped", "users-round"),
    ("tasks_received", "Times you were helped", "gift"),
    ("messages_sent", "Messages sent", "send"),
    ("reviews_received", "Reviews received", "star"),
]


def phone_privacy_notice() -> rx.Component:
    """Phone numbers are private for everyone — there is nothing to switch."""
    return rx.el.div(
        rx.el.span(
            rx.icon("lock", class_name="h-3.5 w-3.5"),
            class_name="flex size-6 shrink-0 items-center justify-center rounded-lg bg-[#fff7e8] text-[#e08b12]",
        ),
        rx.el.p(
            ui("Your number is not shared with other users"),
            class_name="min-w-0 flex-1 text-sm font-normal leading-snug text-[#111827]",
        ),
        role="note",
        class_name="flex w-full items-center gap-2 rounded-2xl bg-[#fff7e8] px-3 py-2",
    )


def save_changes_button() -> rx.Component:
    """The helping-green Save changes action, with no surrounding container."""
    return rx.el.button(
        rx.cond(
            ProfileState.is_saving,
            rx.el.span(
                rx.spinner(class_name="h-4 w-4"),
                ui("Saving…"),
                class_name="flex items-center justify-center gap-2",
            ),
            rx.el.span(
                rx.icon("check", class_name="h-4 w-4"),
                ui("Save changes"),
                class_name="flex items-center justify-center gap-2",
            ),
        ),
        type="submit",
        disabled=ProfileState.is_saving,
        class_name="gah-profile-save gah-orange-control gah-primary-outline border border-[#fba922] border-solid w-full sm:w-fit shrink-0 rounded-xl px-6 py-3 text-sm font-bold transition-colors disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#111827]",
    )


def upcoming_job_card(job: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("calendar", class_name="h-5 w-5 text-[#e08b12]"),
                class_name="flex items-center justify-center size-11 rounded-xl bg-[#fff7e8] shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    job["title"],
                    class_name="text-base font-bold text-[#111827] leading-snug",
                ),
                rx.el.p(
                    f"with {job['other_name']}",
                    class_name="text-sm font-medium text-[#4b5563] mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                job["status"],
                class_name="w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08] capitalize shrink-0",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                rx.icon("users-round", class_name="h-3 w-3"),
                job["role_label"],
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08]",
            ),
            rx.el.span(
                rx.icon("compass", class_name="h-3 w-3"),
                job["category_label"],
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1 text-xs font-semibold text-[#111827]",
            ),
            rx.el.span(
                rx.icon("gift", class_name="h-3 w-3"),
                job["reward"],
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08]",
            ),
            rx.cond(
                job["reward_details"],
                rx.el.span(
                    job["reward_details"],
                    class_name="w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#4b5563]",
                ),
                rx.fragment(),
            ),
            rx.cond(
                job["has_schedule"],
                rx.el.span(
                    rx.icon("calendar-check", class_name="h-3 w-3"),
                    "In calendar export",
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08]",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "map-pin", class_name="h-4 w-4 text-[#e08b12] shrink-0"
                ),
                rx.el.div(
                    rx.el.p(
                        "Where",
                        class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
                    ),
                    rx.el.p(
                        job["location"],
                        class_name="text-sm font-semibold text-[#111827] mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-2.5 min-w-0",
            ),
            rx.el.div(
                rx.icon("clock", class_name="h-4 w-4 text-[#e08b12] shrink-0"),
                rx.el.div(
                    rx.el.p(
                        "Original request",
                        class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
                    ),
                    rx.el.p(
                        job["scheduled"],
                        class_name="text-sm font-semibold text-[#111827] mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-2.5 min-w-0",
            ),
            rx.el.div(
                rx.icon(
                    "calendar-check",
                    class_name="h-4 w-4 text-[#e08b12] shrink-0",
                ),
                rx.el.div(
                    rx.el.p(
                        "Helper availability",
                        class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
                    ),
                    rx.el.p(
                        job["proposed_available"],
                        class_name="text-sm font-semibold text-[#111827] mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-2.5 min-w-0",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 rounded-2xl border border-[#d4d4d4] bg-[#ffffff] p-4",
        ),
        rx.el.div(
            rx.icon("send", class_name="h-4 w-4 text-[#b86e08] shrink-0"),
            rx.el.p(
                job["conversation_hint"],
                class_name="text-sm font-semibold text-[#111827] leading-relaxed",
            ),
            class_name="flex items-start gap-2.5 mt-4 rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-4 py-3",
        ),
        class_name="gah-main-card w-full px-5 py-4 sm:px-6 sm:py-5",
    )


def calendar_export_button() -> rx.Component:
    """A pocket-sized travel tool: save agreed jobs as one .ics file."""
    return rx.el.button(
        rx.cond(
            ProfileState.calendar_busy,
            rx.spinner(class_name="h-3.5 w-3.5"),
            rx.icon("calendar-plus", class_name="h-3.5 w-3.5"),
        ),
        "Export calendar (.ics)",
        type="button",
        disabled=ProfileState.calendar_busy,
        title="Download your accepted jobs as a calendar file",
        aria_label="Export calendar as an ICS file",
        on_click=ProfileState.export_calendar,
        class_name="w-fit shrink-0 flex items-center gap-2 rounded-full bg-[#e08b12] px-3.5 py-2 text-xs font-bold text-white transition-colors hover:bg-[#e08b12] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]",
    )


def calendar_export_feedback() -> rx.Component:
    """Clear empty / error and success notes for the calendar export."""
    return rx.el.div(
        rx.cond(
            ProfileState.calendar_error,
            rx.el.p(
                rx.icon("triangle-alert", class_name="h-3.5 w-3.5 shrink-0"),
                ProfileState.calendar_error,
                role="alert",
                class_name="mt-3 flex w-full items-start gap-2 rounded-2xl border border-[#e08b12] bg-[#fff7e8] px-3.5 py-2.5 text-xs font-semibold leading-relaxed text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ProfileState.calendar_notice,
            rx.el.p(
                rx.icon("calendar-check", class_name="h-3.5 w-3.5 shrink-0"),
                ProfileState.calendar_notice,
                role="status",
                class_name="mt-3 flex w-full items-start gap-2 rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-3.5 py-2.5 text-xs font-semibold leading-relaxed text-[#b86e08]",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )


def upcoming_jobs_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Upcoming jobs",
                    class_name="text-xl sm:text-2xl font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    "Accepted and matched jobs stay here as shared confirmation for both sides.",
                    class_name="mt-1 text-sm font-medium text-[#4b5563] leading-relaxed",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("calendar", class_name="h-3.5 w-3.5"),
                    rx.cond(
                        ProfileState.scheduled_job_count > 0,
                        f"{ProfileState.scheduled_job_count} dated",
                        "Your calendar",
                    ),
                    class_name="w-fit shrink-0 flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08]",
                ),
                calendar_export_button(),
                class_name="flex shrink-0 flex-col items-end gap-2",
            ),
            class_name="w-full flex items-start justify-between gap-4 mt-2",
        ),
        calendar_export_feedback(),
        rx.cond(
            ProfileState.upcoming_jobs.length() > 0,
            rx.el.div(
                rx.foreach(ProfileState.upcoming_jobs, upcoming_job_card),
                class_name="flex flex-col gap-3 mt-5 w-full",
            ),
            rx.el.div(
                rx.icon("calendar", class_name="h-5 w-5 text-[#4b5563] mb-2"),
                rx.el.p(
                    "No accepted or matched jobs yet.",
                    class_name="text-sm font-semibold text-[#404040]",
                ),
                rx.el.p(
                    "When someone accepts a request, the appointment details will appear here for everyone involved.",
                    class_name="text-sm font-medium text-[#4b5563] mt-1 leading-relaxed",
                ),
                class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-white/60 px-6 py-8 mt-5",
            ),
        ),
        class_name="w-full",
    )


def rating_star(state: rx.Var[str]) -> rx.Component:
    return rx.match(
        state,
        (
            "full",
            rx.icon(
                "star",
                class_name="h-5 w-5 stroke-[#e08b12] fill-[#e08b12]",
            ),
        ),
        (
            "half",
            rx.icon(
                "star-half",
                class_name="h-5 w-5 stroke-[#e08b12] fill-[#e08b12]",
            ),
        ),
        rx.icon("star", class_name="h-5 w-5 stroke-[#d4d4d4]"),
    )


def inline_rating_stars() -> rx.Component:
    """Accessible shortcut to Community Reviews beside the display name."""
    return rx.el.button(
        rx.foreach(ProfileState.combined_star_states, rating_star),
        type="button",
        title=ProfileState.combined_rating_label,
        aria_label=f"Open Community Reviews — {ProfileState.combined_rating_label}",
        on_click=ProfileState.open_reviews,
        class_name="gah-rating-stars -my-1 flex min-h-11 shrink-0 cursor-pointer items-center gap-0.5 border-0 bg-transparent text-[#e08b12] shadow-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#fba922]",
    )


def verification_note(icon: str, title: str, body: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                title,
                class_name="text-xs font-bold text-[#111827]",
            ),
            rx.el.p(
                body,
                class_name="mt-0.5 text-xs font-medium leading-relaxed text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1",
        ),
        class_name="flex w-full items-start gap-2.5 px-1 py-1",
    )


def verification_guidance() -> rx.Component:
    """`How verification works` — honest about what the tick does and doesn't mean."""
    return rx.el.details(
        rx.el.summary(
            rx.el.div(
                rx.icon(
                    "badge-check", class_name="h-4 w-4 text-[#b86e08] shrink-0"
                ),
                rx.el.div(
                    rx.el.p(
                        rx.el.span("Get verified - ", class_name="font-bold"),
                        rx.el.span(
                            "Get more opportunities", class_name="font-normal"
                        ),
                        class_name="text-sm text-[#111827]",
                    ),
                    class_name="min-w-0 flex-1",
                ),
                disclosure_arrow(),
                class_name="flex items-center gap-3 w-full",
            ),
            class_name="cursor-pointer list-none rounded-2xl px-1 py-1 focus:outline-hidden focus:ring-2 focus:ring-[#fff7e8]",
        ),
        rx.el.div(
            verification_note(
                "mail",
                "What the verification tick means",
                "Increase your chances of people offering to help you, and "
                "people accepting your offers to help them.",
            ),
            class_name="flex flex-col gap-2 w-full mt-3",
        ),
        class_name="group/verification w-full mt-4 rounded-2xl border border-[#fba922] bg-white p-3",
    )


def identity_portrait() -> rx.Component:
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                rx.image(
                    src=avatar_src(
                        ProfileState.avatar_path, ProfileState.avatar_seed
                    ),
                    alt="Your Go and Help profile photo",
                    class_name="size-20 sm:size-24 rounded-full bg-[#fff7e8] object-cover",
                ),
                rx.el.span(
                    rx.cond(
                        ProfileState.avatar_busy,
                        rx.icon(
                            "loader-circle",
                            class_name="h-3.5 w-3.5 animate-spin text-[#fba922]",
                        ),
                        rx.icon(
                            "camera", class_name="h-3.5 w-3.5 text-[#fba922]"
                        ),
                    ),
                    class_name="absolute bottom-0 right-0 flex size-8 items-center justify-center rounded-full border-2 border-[#fba922] bg-white",
                ),
                verified_badge(AuthState.is_verified),
                class_name="relative rounded-full ring-4 ring-[#fff7e8] transition-transform hover:scale-[1.02]",
            ),
            id=AVATAR_UPLOAD_ID,
            multiple=False,
            max_files=1,
            accept={
                "image/png": [".png"],
                "image/jpeg": [".jpg", ".jpeg"],
                "image/webp": [".webp"],
            },
            on_drop=ProfileState.handle_avatar_upload(
                rx.upload_files(upload_id=AVATAR_UPLOAD_ID)
            ),
            class_name="cursor-pointer rounded-full w-fit",
        ),
        class_name="flex flex-col items-start shrink-0",
    )


def identity_passport() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            identity_portrait(),
            rx.el.div(
                rx.el.div(
                    rx.el.h1(
                        AuthState.display_name,
                        class_name="text-[calc(1.5rem-1pt)] sm:text-[calc(1.875rem-1pt)] font-bold tracking-tight text-[#111827] leading-tight",
                    ),
                    verified_tick(AuthState.is_verified),
                    inline_rating_stars(),
                    rx.cond(
                        ProfileState.nationality_flag,
                        rx.el.span(
                            ProfileState.nationality_flag,
                            title=ProfileState.nationality,
                            aria_label=ProfileState.nationality,
                            class_name="text-lg leading-none shrink-0",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.div(
                    rx.el.span(
                        ProfileState.handle_label,
                        class_name=rx.cond(
                            ProfileState.username,
                            "w-fit rounded-full border border-[#fba922] bg-white px-3 py-1 text-xs font-bold text-black",
                            "w-fit rounded-full border border-dashed border-[#d4d4d4] bg-white px-3 py-1 text-xs font-semibold text-[#4b5563]",
                        ),
                    ),
                    class_name="mt-2 flex flex-wrap items-center gap-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex w-full flex-row items-start gap-4",
        ),
        error_banner(ProfileState.avatar_error),
        rx.cond(AuthState.is_verified, rx.fragment(), verification_guidance()),
        class_name="gah-main-card w-full rounded-[2rem] bg-[#ffffff] p-5 sm:p-6",
    )


def sign_out_action() -> rx.Component:
    """Compact, centered sign out at the bottom of Profile."""
    return rx.el.div(
        rx.el.button(
            rx.icon("log-out", class_name="h-4 w-4"),
            rx.el.span(ui("Sign out"), class_name="text-sm font-bold"),
            type="button",
            title=ui("Sign out"),
            aria_label=ui("Sign out"),
            on_click=AuthState.sign_out,
            class_name="flex min-h-11 w-fit items-center justify-center gap-2 rounded-full border border-[#fba922] bg-[#fba922] px-5 py-2.5 text-black transition-colors hover:bg-[#e08b12] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#b86e08]",
        ),
        class_name="relative top-[10px] flex w-full justify-center",
    )


def disclosure_header(
    title: str,
    subtitle: rx.Var[str] | str | rx.Component,
    icon: str,
    open_var: rx.Var[bool],
    on_click: rx.event.EventType,
    panel_id: str,
) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            rx.icon(icon, class_name="h-4 w-4 text-[#fba922]"),
            class_name="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#fff7e8] text-[#fba922]",
        ),
        rx.el.span(
            rx.el.span(
                ui(title),
                class_name="block text-start text-lg font-bold tracking-tight text-[#111827]",
            ),
            rx.el.span(
                subtitle,
                class_name="mt-0.5 block text-start text-xs font-medium leading-relaxed text-[#4b5563]",
            ),
            class_name="min-w-0 flex-1",
        ),
        disclosure_arrow(open_var),
        type="button",
        aria_expanded=rx.cond(open_var, "true", "false"),
        aria_controls=panel_id,
        on_click=on_click,
        class_name="gah-profile-disclosure flex w-full items-center gap-3 bg-white px-1 py-1 text-left transition-colors hover:opacity-90 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
    )


def my_information_section() -> rx.Component:
    """Collapsed-by-default disclosure wrapping the existing details form."""
    return rx.el.section(
        disclosure_header(
            "My information",
            ui("Handle, Phone, Email, Bio, Languages, Password"),
            "notebook-pen",
            ProfileState.information_open,
            ProfileState.toggle_information,
            "gah-my-information",
        ),
        rx.cond(
            ProfileState.information_open,
            rx.el.div(
                details_tab(),
                id="gah-my-information",
                class_name="mt-4 w-full",
            ),
            rx.fragment(),
        ),
        class_name="gah-profile-row w-full bg-white px-5 py-4 sm:px-6 sm:py-5",
    )


def skills_knowledge_section() -> rx.Component:
    """`My Skills` disclosure with selectable categories and free text."""
    return rx.el.section(
        disclosure_header(
            "My Skills",
            localized_profile_skills_summary(
                ProfileState.selected_category_labels,
                ProfileState.skill_list.length(),
            ),
            "wrench",
            ProfileState.skills_open,
            ProfileState.toggle_skills,
            "gah-my-skills",
        ),
        rx.cond(
            ProfileState.skills_open,
            rx.el.form(
                rx.el.div(
                    rx.el.p(
                        ui("Select what you can help with"),
                        class_name="w-full text-center text-sm font-semibold text-[#111827]",
                    ),
                    rx.el.div(
                        rx.foreach(
                            ProfileState.category_options, category_chip
                        ),
                        class_name="mt-3 flex flex-wrap gap-2",
                    ),
                    class_name="w-full",
                ),
                rx.cond(
                    ProfileState.selected_category_labels.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            ProfileState.selected_category_labels,
                            lambda label: rx.el.span(
                                ui(label),
                                class_name="w-fit rounded-full border border-[#fba922] bg-white px-3 py-1 text-xs font-semibold text-black",
                            ),
                        ),
                        class_name="flex flex-wrap gap-2",
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    field_label(
                        "Other Skills",
                        "Anything the categories miss",
                    ),
                    rx.el.textarea(
                        name="skills",
                        default_value=ProfileState.skills,
                        key=ProfileState.skills,
                        rows="3",
                        placeholder=ui(
                            "Plumber, Electrician, Hairdresser, Dentist, Tailor..."
                        ),
                        aria_label=ui("Other Skills"),
                        class_name=INPUT_CLASS + " resize-y leading-relaxed",
                    ),
                    class_name="w-full",
                ),
                rx.el.button(
                    rx.cond(
                        ProfileState.is_saving,
                        rx.el.span(
                            rx.spinner(class_name="h-4 w-4"),
                            ui("Saving…"),
                            class_name="flex items-center justify-center gap-2",
                        ),
                        rx.el.span(
                            rx.icon("check", class_name="h-4 w-4"),
                            ui("Save skills and knowledge"),
                            class_name="flex items-center justify-center gap-2",
                        ),
                    ),
                    type="submit",
                    disabled=ProfileState.is_saving,
                    class_name="gah-profile-save gah-orange-control gah-primary-outline border border-[#fba922] border-solid w-full sm:w-fit rounded-xl px-6 py-3 text-sm font-bold transition-colors disabled:opacity-60 focus-visible:ring-2 focus-visible:ring-[#e08b12]",
                ),
                on_submit=ProfileState.save_skills,
                reset_on_submit=False,
                dir=AuthState.interface_direction,
                id="gah-my-skills",
                class_name="mt-4 flex flex-col gap-4 w-full",
            ),
            rx.fragment(),
        ),
        id="gah-skills-box",
        custom_attrs={"data-tour-target": "skills"},
        tab_index=-1,
        class_name="gah-profile-row w-full scroll-mt-5 bg-white px-5 py-4 sm:px-6 sm:py-5 focus-visible:outline-2 focus-visible:outline-[#e08b12]",
    )


def setting_choice(
    label: str,
    active: rx.Var[bool],
    on_click: rx.event.EventType,
) -> rx.Component:
    return rx.el.button(
        ui(label),
        type="button",
        role="radio",
        aria_checked=rx.cond(active, "true", "false"),
        on_click=on_click,
        class_name=rx.cond(
            active,
            "gah-setting-choice w-fit rounded-full border-2 border-[#fba922] bg-white px-3.5 py-2 text-xs font-bold text-black transition-colors",
            "w-fit rounded-full border border-[#f7d9a0] bg-white px-3.5 py-2 text-xs font-semibold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
        ),
    )


def setting_row(
    title: str, hint: str | rx.Var[str], control: rx.Component
) -> rx.Component:
    return rx.el.div(
        rx.el.p(ui(title), class_name="text-sm font-bold text-[#111827]"),
        rx.el.p(
            hint,
            class_name="mt-0.5 text-xs font-medium leading-relaxed text-[#4b5563]",
        ),
        control,
        class_name="w-full rounded-2xl border border-[#f7d9a0] bg-white p-4",
    )


def appearance_control() -> rx.Component:
    """Day / Night / System, applied through Reflex's colour-mode event."""
    return rx.el.div(
        setting_choice(
            "Day",
            ProfileState.appearance == "light",
            [ProfileState.set_appearance("light"), set_color_mode("light")],
        ),
        setting_choice(
            "Night",
            ProfileState.appearance == "dark",
            [ProfileState.set_appearance("dark"), set_color_mode("dark")],
        ),
        setting_choice(
            "System",
            ProfileState.appearance == "system",
            [
                ProfileState.set_appearance("system"),
                set_color_mode("system"),
            ],
        ),
        role="radiogroup",
        aria_label=ui("Appearance"),
        class_name="mt-3 flex flex-wrap items-center gap-2",
    )


def notification_switch(
    label: str, key: str, enabled: rx.Var[bool]
) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            ui(label),
            class_name="min-w-0 flex-1 break-words text-sm font-semibold leading-relaxed text-[#111827]",
        ),
        rx.el.button(
            rx.el.span(
                class_name=rx.cond(
                    enabled,
                    "block size-5 translate-x-5 rounded-full bg-white transition-transform",
                    "block size-5 translate-x-0 rounded-full bg-white transition-transform",
                ),
            ),
            type="button",
            role="switch",
            aria_label=ui(label),
            aria_checked=rx.cond(enabled, "true", "false"),
            disabled=ProfileState.notification_preferences_busy,
            on_click=lambda: ProfileState.toggle_notification_preference(key),
            class_name=rx.cond(
                enabled,
                "flex h-8 w-12 shrink-0 items-center rounded-full bg-[#fba922] p-1 text-[#111827] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12] disabled:opacity-60",
                "flex h-8 w-12 shrink-0 items-center rounded-full bg-[#6b7280] p-1 text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12] disabled:opacity-60",
            ),
        ),
        class_name="flex min-h-11 items-center justify-between gap-3 py-1",
    )


def notification_settings() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            rx.icon("bell", class_name="h-4 w-4 text-[#fba922]"),
            ui("Notifications"),
            class_name="flex items-center gap-2 text-sm font-bold text-[#111827]",
        ),
        rx.el.div(
            notification_switch(
                "Requests in my field",
                "notify_requests_in_my_field",
                ProfileState.notify_requests_in_my_field,
            ),
            rx.el.label(
                ui_template(
                    "Notification radius: {radius} km",
                    "radius",
                    ProfileState.requests_in_my_field_radius_km.to_string(),
                ),
                html_for="field-request-radius",
                class_name="block text-center text-sm font-semibold text-[#111827]",
            ),
            rx.el.input(
                id="field-request-radius",
                type="range",
                min="1",
                max="1000",
                step="1",
                default_value=ProfileState.requests_in_my_field_radius_km.to_string(),
                key=ProfileState.field_radius_reset_token.to_string(),
                on_change=ProfileState.set_field_request_radius.throttle(100),
                aria_label=ui(
                    "Requests in my field notification radius in kilometres"
                ),
                aria_valuetext=ui_template(
                    "{radius} kilometres",
                    "radius",
                    ProfileState.requests_in_my_field_radius_km.to_string(),
                ),
                disabled=~ProfileState.notify_requests_in_my_field,
                class_name="mt-3 h-8 w-full cursor-pointer accent-[#fba922] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08b12] disabled:cursor-default disabled:opacity-50",
            ),
            rx.el.div(
                rx.el.span(ui_template("{radius} km", "radius", "1")),
                rx.el.span(ui_template("{radius} km", "radius", "1000")),
                class_name="flex justify-between text-xs font-medium text-[#4b5563]",
            ),
            rx.el.p(
                ui(
                    "New requests matching your saved skills and private location. Your location need not be visible on the map."
                ),
                class_name="mt-2 text-xs font-medium leading-relaxed text-[#4b5563]",
            ),
            class_name="my-2 rounded-xl border border-[#f7d9a0] bg-white p-3",
        ),
        notification_switch(
            "Help offers and requests",
            "notify_help_offers",
            ProfileState.notify_help_offers,
        ),
        notification_switch(
            "Messages", "notify_messages", ProfileState.notify_messages
        ),
        notification_switch(
            "Schedule changes",
            "notify_schedule_changes",
            ProfileState.notify_schedule_changes,
        ),
        notification_switch(
            "Community activity",
            "notify_community_activity",
            ProfileState.notify_community_activity,
        ),
        notification_switch(
            "Reminders and task updates",
            "notify_reminders",
            ProfileState.notify_reminders,
        ),
        rx.el.p(
            ui(ProfileState.notification_preferences_notice),
            role="status",
            class_name="text-xs font-medium text-[#4b5563]",
        ),
        rx.cond(
            ProfileState.notification_preferences_error != "",
            rx.el.p(
                ui(ProfileState.notification_preferences_error),
                role="alert",
                class_name="rounded-xl border border-[#e08b12] bg-[#fff7e8] px-3 py-2 text-xs font-medium text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-2xl border border-[#f7d9a0] bg-white p-4",
    )


def settings_content() -> rx.Component:
    """Shared settings controls with the existing persistence handlers."""
    return rx.el.div(
        notification_settings(),
        setting_row(
            "Appearance",
            ui("Day, Night, or follow your device setting."),
            appearance_control(),
        ),
        setting_row(
            "Date display",
            ui_template(
                "Dates are shown as {date}.",
                "date",
                ProfileState.date_format_example,
            ),
            rx.el.div(
                setting_choice(
                    "Day–Month–Year",
                    ProfileState.date_format == "dmy",
                    lambda: ProfileState.set_date_format("dmy"),
                ),
                setting_choice(
                    "Month–Day–Year",
                    ProfileState.date_format == "mdy",
                    lambda: ProfileState.set_date_format("mdy"),
                ),
                setting_choice(
                    "Year–Month–Day",
                    ProfileState.date_format == "ymd",
                    lambda: ProfileState.set_date_format("ymd"),
                ),
                role="radiogroup",
                aria_label=ui("Date display"),
                class_name="mt-3 flex flex-wrap items-center gap-2",
            ),
        ),
        setting_row(
            "Distance units",
            ui("Your preferred unit for distances."),
            rx.el.div(
                setting_choice(
                    "Kilometres",
                    ProfileState.distance_units == "km",
                    lambda: ProfileState.set_distance_units("km"),
                ),
                setting_choice(
                    "Miles",
                    ProfileState.distance_units == "mi",
                    lambda: ProfileState.set_distance_units("mi"),
                ),
                role="radiogroup",
                aria_label=ui("Distance units"),
                class_name="mt-3 flex flex-wrap items-center gap-2",
            ),
        ),
        rx.el.div(
            app_language_field(),
            class_name="w-full rounded-2xl border border-[#f7d9a0] bg-white p-4",
        ),
        restart_tour_control(),
        id="gah-settings",
        class_name="flex w-full flex-col gap-3",
    )


def blocked_member_row(member: BlockedMember) -> rx.Component:
    """One private row: who they are, when you blocked them, and Unblock."""
    return rx.el.li(
        avatar_with_tick(
            avatar_src(member["avatar"], member["avatar_seed"]),
            member["verified"],
            "size-11 rounded-full bg-[#fff7e8] object-cover",
            ui("Blocked member photo"),
        ),
        rx.el.div(
            rx.el.p(
                member["name"],
                class_name="truncate text-sm font-bold leading-tight text-[#111827]",
            ),
            rx.el.div(
                rx.cond(
                    member["handle"],
                    rx.el.span(
                        member["handle"],
                        class_name="text-[11px] font-bold text-[#b86e08]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    member["blocked_on"],
                    rx.el.span(
                        rx.icon("calendar", class_name="h-3 w-3"),
                        ui_template(
                            "Blocked {date}", "date", member["blocked_on"]
                        ),
                        class_name="w-fit flex items-center gap-1.5 text-[11px] font-medium text-[#4b5563]",
                    ),
                    rx.fragment(),
                ),
                class_name="mt-0.5 flex flex-wrap items-center gap-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.cond(
                BlockState.unblocking_id == member["id"],
                rx.el.span(
                    rx.spinner(class_name="h-3.5 w-3.5"),
                    ui("Unblocking…"),
                    class_name="flex items-center justify-center gap-1.5",
                ),
                rx.el.span(
                    rx.icon("user-check", class_name="h-3.5 w-3.5"),
                    ui("Unblock"),
                    class_name="flex items-center justify-center gap-1.5",
                ),
            ),
            type="button",
            disabled=BlockState.unblocking_id > 0,
            aria_label=ui_template("Unblock {name}", "name", member["name"]),
            on_click=lambda: BlockState.unblock_member(member["id"]),
            class_name="w-fit shrink-0 rounded-full border border-[#fba922] bg-white px-3.5 py-2 text-xs font-bold text-[#b86e08] transition-colors hover:bg-[#fff7e8] disabled:opacity-60 dark:bg-[#1f2937] dark:text-[#fbbf24]",
        ),
        class_name="gah-inset-row flex w-full items-center gap-3 bg-white p-3",
    )


def blocked_members_section() -> rx.Component:
    """Collapsed-by-default private disclosure — never a separate page."""
    return rx.el.section(
        disclosure_header(
            "Blocked members",
            BlockState.localized_blocked_count_label,
            "user-minus",
            ProfileState.blocked_open,
            ProfileState.toggle_blocked,
            "gah-blocked-members",
        ),
        rx.cond(
            ProfileState.blocked_open,
            rx.el.div(
                rx.el.p(
                    rx.icon(
                        "lock",
                        class_name="h-3 w-3 inline-block mr-1 text-[#e08b12]",
                    ),
                    ui(
                        "Blocked members are never notified. Their posts and comments are hidden from you, and contact requests and messages are prevented in both directions."
                    ),
                    class_name="text-xs font-medium leading-relaxed text-black dark:text-gray-100",
                ),
                error_banner(ui(BlockState.list_error)),
                success_banner(ui(BlockState.list_success)),
                rx.cond(
                    BlockState.is_loading,
                    rx.el.div(
                        rx.el.div(
                            class_name="animate-pulse h-16 w-full rounded-2xl bg-[#fff7e8]"
                        ),
                        rx.el.div(
                            class_name="animate-pulse h-16 w-full rounded-2xl bg-[#fff7e8]"
                        ),
                        class_name="flex w-full flex-col gap-2",
                    ),
                    rx.cond(
                        BlockState.blocked.length() > 0,
                        rx.el.ul(
                            rx.foreach(BlockState.blocked, blocked_member_row),
                            aria_label=ui("Members you have blocked"),
                            class_name="flex w-full flex-col gap-2",
                        ),
                        rx.el.p(
                            ui(
                                "You haven't blocked anyone. If you ever need "
                                "to, use the Block action on a member's post, "
                                "comment or conversation."
                            ),
                            class_name="rounded-2xl border border-dashed border-[#c6d2e8] bg-white px-4 py-6 text-center text-sm font-medium text-[#4b5563] dark:border-gray-600 dark:bg-[#1f2937] dark:text-gray-200",
                        ),
                    ),
                ),
                id="gah-blocked-members",
                on_mount=BlockState.load_blocked_members,
                class_name="mt-4 flex w-full flex-col gap-3",
            ),
            rx.fragment(),
        ),
        class_name="gah-profile-row w-full bg-white px-5 py-4 sm:px-6 sm:py-5",
    )


def pending_application_card(app: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            avatar_with_tick(
                avatar_src(app["helper_avatar"], app["helper_avatar_seed"]),
                app["helper_verified"],
                "size-14 rounded-full bg-[#fff7e8] object-cover shrink-0 ring-2 ring-[#fff7e8]",
                "Helper photo",
            ),
            rx.el.div(
                rx.el.p(
                    app["helper_name"],
                    class_name="text-base font-bold text-[#111827] leading-tight",
                ),
                rx.el.div(
                    rx.cond(
                        app["helper_handle"],
                        rx.el.span(
                            app["helper_handle"],
                            class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#b86e08]",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        app["helper_nationality"],
                        rx.el.span(
                            app["helper_flag"],
                            app["helper_nationality"],
                            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#b86e08]",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        rx.icon("hand-helping", class_name="h-3 w-3"),
                        f"{app['helper_score']}/100 give score",
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#e08b12]",
                    ),
                    rx.el.span(
                        rx.icon("gift", class_name="h-3 w-3"),
                        f"{app['helper_helped']} helped",
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#b86e08]",
                    ),
                    class_name="mt-1.5 flex flex-wrap items-center gap-1.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("hourglass", class_name="h-3 w-3"),
                "Waiting on you",
                class_name="w-fit shrink-0 flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1 text-[11px] font-bold text-[#b86e08]",
            ),
            class_name="flex w-full items-start gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "notebook-pen", class_name="h-4 w-4 text-[#e08b12] shrink-0"
                ),
                rx.el.div(
                    rx.el.p(
                        app["post_title"],
                        class_name="text-sm font-bold text-[#111827]",
                    ),
                    rx.el.div(
                        rx.el.span(
                            app["category_label"],
                            class_name="w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827]",
                        ),
                        rx.el.span(
                            app["reward"],
                            class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#b86e08]",
                        ),
                        rx.cond(
                            app["reward_details"],
                            rx.el.span(
                                app["reward_details"],
                                class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#4b5563]",
                            ),
                            rx.fragment(),
                        ),
                        class_name="mt-1.5 flex flex-wrap items-center gap-1.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-2.5 min-w-0",
            ),
            rx.el.div(
                detail_line("map-pin", "Where", app["location"]),
                detail_line("clock", "You asked for", app["scheduled"]),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
            ),
            class_name="mt-4 rounded-2xl border border-[#d4d4d4] bg-[#ffffff] p-4",
        ),
        rx.cond(
            app["pitch"],
            rx.el.div(
                rx.icon(
                    "message-circle",
                    class_name="h-4 w-4 text-[#b86e08] shrink-0",
                ),
                rx.el.p(
                    f"“{app['pitch']}”",
                    class_name="text-sm font-medium italic leading-relaxed text-[#111827]",
                ),
                class_name="mt-3 flex items-start gap-2.5 rounded-2xl border border-[#fff7e8] bg-[#fff7e8] px-4 py-3",
            ),
            rx.el.p(
                "This helper didn't add a message.",
                class_name="mt-3 text-sm font-medium italic text-[#4b5563]",
            ),
        ),
        rx.el.div(
            field_label("Response message", "optional — sent to their inbox"),
            rx.el.textarea(
                rows="2",
                placeholder="See you at the market gate at 9am — thank you!",
                on_change=lambda value: ProfileState.set_response_draft(
                    app["key"], value
                ),
                class_name=INPUT_CLASS + " resize-y leading-relaxed",
            ),
            class_name="mt-4 w-full",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("circle-check-big", class_name="h-4 w-4"),
                "Confirm helper",
                type="button",
                disabled=ProfileState.deciding_id == app["id"],
                on_click=lambda: ProfileState.confirm_application(app["id"]),
                class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl bg-[#e08b12] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("circle-x", class_name="h-4 w-4"),
                "Deny",
                type="button",
                disabled=ProfileState.deciding_id == app["id"],
                on_click=lambda: ProfileState.deny_application(app["id"]),
                class_name="w-full sm:w-fit flex items-center justify-center gap-2 rounded-xl border border-[#d4d4d4] bg-white px-5 py-2.5 text-sm font-bold text-[#404040] transition-colors hover:bg-[#fff7e8] disabled:opacity-60",
            ),
            rx.el.span(
                f"Applied {app['applied']}",
                class_name="text-[11px] font-semibold text-[#4b5563] sm:ml-auto",
            ),
            class_name="mt-4 flex flex-col sm:flex-row sm:items-center gap-2 w-full",
        ),
        class_name="w-full rounded-3xl border border-[#fff7e8] bg-white p-5 sm:p-6",
    )


def detail_line(icon: str, label: str, value: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-4 w-4 text-[#e08b12] shrink-0"),
        rx.el.div(
            rx.el.p(
                label,
                class_name="text-[10px] font-bold uppercase tracking-wide text-[#4b5563]",
            ),
            rx.el.p(
                value,
                class_name="mt-0.5 text-sm font-semibold text-[#111827]",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 min-w-0",
    )


def pending_requests_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Participation requests",
                    class_name="text-xl sm:text-2xl font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    "Helpers waiting on your answer for the jobs you posted. Confirming fills the single helper slot.",
                    class_name="mt-1 text-sm font-medium leading-relaxed text-[#4b5563]",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("inbox", class_name="h-3.5 w-3.5"),
                f"{ProfileState.pending_count} waiting",
                class_name="w-fit shrink-0 flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-bold text-[#b86e08]",
            ),
            class_name="flex w-full items-start justify-between gap-4",
        ),
        rx.cond(
            ProfileState.pending_applications.length() > 0,
            rx.el.div(
                rx.foreach(
                    ProfileState.pending_applications,
                    lambda app: pending_application_card(app),
                ),
                class_name="flex flex-col gap-3 mt-5 w-full",
            ),
            rx.el.div(
                rx.icon(
                    "hand-helping", class_name="h-6 w-6 text-[#e08b12] mb-2"
                ),
                rx.el.p(
                    "No one is waiting on you right now.",
                    class_name="text-sm font-semibold text-[#111827]",
                ),
                rx.el.p(
                    "When a helper offers to join one of your jobs, their request lands here with Confirm and Deny.",
                    class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#4b5563]",
                ),
                class_name="mt-5 flex flex-col items-center justify-center text-center rounded-2xl border border-dashed border-[#fff7e8] bg-[#fff7e8]/50 px-6 py-8",
            ),
        ),
        class_name="w-full rounded-[2rem] border border-[#d4d4d4] bg-[#ffffff] p-5 sm:p-6",
    )


def details_tab() -> rx.Component:
    return rx.el.div(
        rx.el.form(
            rx.el.div(
                rx.el.div(
                    field_label("Public handle", "unique, lowercase"),
                    rx.el.input(
                        name="username",
                        default_value=ProfileState.username,
                        key=ProfileState.username,
                        placeholder="maya.lisbon",
                        aria_label=ui("Public handle"),
                        class_name=INPUT_CLASS,
                    ),
                    class_name="w-full",
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
            ),
            rx.el.div(
                field_label("Phone", "optional"),
                rx.el.input(
                    name="phone",
                    default_value=AuthState.phone,
                    key=AuthState.phone,
                    placeholder="+351 900 000 000",
                    aria_label=ui("Phone"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full md:w-1/2",
            ),
            phone_privacy_notice(),
            rx.el.div(
                field_label("Country", "account country"),
                rx.el.input(
                    name="home_country",
                    default_value=ProfileState.home_country,
                    key=ProfileState.home_country,
                    max_length=100,
                    placeholder=ui("Country"),
                    aria_label=ui("Country"),
                    class_name=INPUT_CLASS,
                ),
                class_name="w-full md:w-1/2",
            ),
            rx.cond(
                AuthState.is_signed_in,
                rx.el.div(
                    rx.el.label(
                        ui("Email"),
                        html_for="profile-private-email",
                        class_name="block text-sm font-semibold text-[#111827]",
                    ),
                    rx.el.input(
                        id="profile-private-email",
                        type="email",
                        default_value=AuthState.email,
                        key=AuthState.email,
                        read_only=True,
                        aria_describedby="profile-private-email-help",
                        aria_label=ui("Email"),
                        class_name=INPUT_CLASS,
                    ),
                    rx.el.p(
                        ui(
                            "Private — only visible to you. Your email cannot be edited here."
                        ),
                        id="profile-private-email-help",
                        class_name="mt-1 text-sm text-[#4b5563]",
                    ),
                    class_name="w-full md:w-1/2",
                ),
                rx.fragment(),
            ),
            rx.el.div(
                field_label("Biography", "why you help, why you need help"),
                rx.el.textarea(
                    name="bio",
                    default_value=ProfileState.bio,
                    key=ProfileState.bio,
                    rows="5",
                    placeholder=ui(
                        "I.e. I'm a Photographer travelling Asia, happy to help others in exchange for a accommodation..."
                    ),
                    aria_label=ui("Biography"),
                    class_name=INPUT_CLASS + " resize-y leading-relaxed",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.div(
                    field_label("Languages", "comma separated"),
                    rx.el.input(
                        name="languages",
                        default_value=ProfileState.languages,
                        key=ProfileState.languages,
                        placeholder=ui("English, Portuguese, Spanish"),
                        aria_label=ui("Languages"),
                        class_name=INPUT_CLASS,
                    ),
                    class_name="w-full",
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    rx.foreach(ProfileState.language_list, tag_chip),
                    class_name="flex flex-wrap gap-2",
                ),
                class_name="w-full",
            ),
            save_changes_button(),
            on_submit=ProfileState.save_details,
            reset_on_submit=False,
            dir=AuthState.interface_direction,
            class_name="flex flex-col gap-[17px] w-full",
        ),
        change_password_form(),
        class_name="flex flex-col gap-[17px] w-full",
    )


def password_field(
    label: str, name: str, autocomplete: str, minimum: int
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            ui(label), class_name="text-sm font-semibold text-[#111827]"
        ),
        rx.el.input(
            name=name,
            type="password",
            auto_complete=autocomplete,
            min_length=minimum,
            required=True,
            disabled=ProfileState.password_busy,
            class_name=INPUT_CLASS,
        ),
        class_name="flex w-full flex-col gap-2",
    )


def change_password_form() -> rx.Component:
    return rx.el.form(
        rx.el.h3(
            rx.icon("lock-keyhole", class_name="h-4 w-4 text-[#fba922]"),
            ui("Change password"),
            class_name="flex items-center gap-2 text-sm font-bold text-[#111827]",
        ),
        password_field(
            "Current password", "current_password", "current-password", 1
        ),
        rx.el.div(
            password_field("New password", "new_password", "new-password", 6),
            password_field(
                "Confirm new password", "confirm_password", "new-password", 6
            ),
            class_name="grid w-full grid-cols-1 gap-4 md:grid-cols-2",
        ),
        error_banner(ui(ProfileState.password_error)),
        success_banner(ui(ProfileState.password_success)),
        rx.el.button(
            rx.cond(
                ProfileState.password_busy,
                rx.el.span(
                    rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                    ui("Changing password…"),
                    class_name="flex items-center justify-center gap-2",
                ),
                ui("Change password"),
            ),
            type="submit",
            disabled=ProfileState.password_busy,
            aria_busy=ProfileState.password_busy,
            class_name="gah-orange-control w-full sm:w-fit rounded-xl border border-[#fba922] bg-[#fba922] px-6 py-3 text-sm font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#fba922]",
        ),
        on_submit=ProfileState.change_password,
        reset_on_submit=True,
        aria_label=ui("Change password"),
        class_name="flex w-full flex-col gap-4 border-t border-[#f7d9a0] pt-4",
    )


def app_language_option(item: tuple[str, str]) -> rx.Component:
    return rx.el.option(item[1], value=item[0])


def app_language_field() -> rx.Component:
    """Persisting app/display language picker (outside form data)."""
    return rx.el.div(
        rx.el.label(
            ui("App Language"),
            html_for="settings-interface-language",
            class_name="block text-sm font-semibold text-[#111827]",
        ),
        rx.el.div(
            rx.icon(
                "globe",
                class_name="h-4 w-4 text-[#fba922] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            rx.el.select(
                rx.foreach(SETTINGS_LANGUAGE_OPTIONS, app_language_option),
                id="settings-interface-language",
                value=AuthState.preferred_language,
                disabled=AuthState.language_saving,
                on_change=AuthState.update_language,
                class_name="w-full appearance-none cursor-pointer rounded-lg border border-[#f7d9a0] bg-white py-3 pl-10 pr-9 text-sm font-semibold text-[#111827] outline-hidden transition-colors focus:border-[#e08b12] focus:ring-2 focus:ring-[#fff7e8]",
            ),
            rx.icon(
                "chevron-down",
                class_name="h-4 w-4 text-[#4b5563] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            class_name="relative w-full",
        ),
        rx.el.p(
            ui(
                "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language."
            ),
            class_name="mt-2 text-xs leading-relaxed text-[#4b5563]",
        ),
        rx.el.p(
            AuthState.language_error,
            role="alert",
            class_name="mt-2 text-sm text-[#b86e08]",
        ),
        class_name="w-full",
    )


def tag_chip(label: str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#b86e08]",
    )


def category_chip(category: str) -> rx.Component:
    return rx.el.button(
        rx.cond(
            ProfileState.selected_categories.contains(category),
            rx.icon("check", class_name="h-3.5 w-3.5"),
            rx.icon("plus", class_name="h-3.5 w-3.5"),
        ),
        ui(CATEGORY_LABELS.get(category, category.replace("_", " ").title())),
        type="button",
        on_click=lambda: ProfileState.toggle_category(category),
        class_name=rx.cond(
            ProfileState.selected_categories.contains(category),
            "w-fit flex items-center gap-1.5 rounded-full border border-[#e08b12] bg-[#fba922] px-3 py-1.5 text-xs font-semibold text-[#111827] capitalize transition-colors",
            "w-fit flex items-center gap-1.5 rounded-full border border-[#d4d4d4] bg-white px-3 py-1.5 text-xs font-semibold text-[#4b5563] capitalize transition-colors hover:border-[#e08b12] hover:text-[#b86e08]",
        ),
    )


def stat_card(item: tuple[str, str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item[2], class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex items-center justify-center size-9 rounded-xl bg-[#fff7e8] shrink-0",
        ),
        rx.el.p(
            ProfileState.stats[item[0]],
            class_name="mt-3 text-3xl font-bold text-[#111827]",
        ),
        rx.el.p(
            item[1],
            class_name="text-xs font-semibold uppercase tracking-wide text-[#4b5563]",
        ),
        class_name="w-full rounded-2xl border border-[#e5e5e5] bg-white p-5",
    )


def rating_card(
    title: str, avg: rx.Var[float], count: rx.Var[int], icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[#111827]"),
            rx.el.h3(title, class_name="text-sm font-semibold text-[#111827]"),
            class_name="flex items-center gap-2",
        ),
        rx.cond(
            count > 0,
            rx.el.div(
                rx.el.p(
                    f"{avg:.1f}",
                    class_name="text-3xl font-bold text-[#111827]",
                ),
                rx.el.span(
                    rx.icon("star", class_name="h-3.5 w-3.5"),
                    f"{count} reviews",
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1 text-xs font-semibold text-[#111827]",
                ),
                class_name="mt-3 flex items-center gap-3",
            ),
            rx.el.p(
                "No reviews yet — your first completed task starts the story.",
                class_name="mt-3 text-sm font-medium text-[#4b5563]",
            ),
        ),
        class_name="w-full rounded-2xl border border-[#e5e5e5] bg-white p-5",
    )


def journal_row(entry: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("notebook-pen", class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex items-center justify-center size-9 rounded-xl bg-[#fff7e8] shrink-0",
        ),
        rx.el.div(
            rx.el.p(
                entry["title"],
                class_name="text-sm font-semibold text-[#111827]",
            ),
            rx.el.p(
                f"{entry['category']} · {entry['created']}",
                class_name="text-xs font-medium text-[#4b5563] mt-0.5 capitalize",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.span(
            entry["status"],
            class_name="w-fit rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-semibold text-[#404040] capitalize shrink-0",
        ),
        class_name="flex items-center gap-4 w-full rounded-2xl border border-[#e5e5e5] bg-white p-4",
    )


def activity_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Your kindness ledger",
                    class_name="text-lg font-semibold text-[#111827]",
                ),
                rx.el.p(
                    "Everything you've posted, offered and completed on Go and Help.",
                    class_name="text-sm font-medium text-[#4b5563] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                rx.icon("sparkles", class_name="h-3.5 w-3.5"),
                f"{ProfileState.kindness_points} kindness points",
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#b86e08]",
            ),
            class_name="w-full flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3",
        ),
        rx.el.div(
            rx.foreach(STAT_CARDS, stat_card),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full",
        ),
        rx.el.div(
            rating_card(
                "Rating as a helper",
                ProfileState.helper_rating_avg,
                ProfileState.helper_rating_count,
                "hand-helping",
            ),
            rating_card(
                "Rating as a traveller",
                ProfileState.traveller_rating_avg,
                ProfileState.traveller_rating_count,
                "map-pin",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
        ),
        rx.el.div(
            rx.el.h3(
                "Recent journal entries",
                class_name="text-sm font-semibold text-[#111827] mb-3",
            ),
            rx.cond(
                ProfileState.entries.length() > 0,
                rx.el.div(
                    rx.foreach(ProfileState.entries, journal_row),
                    class_name="flex flex-col gap-3 w-full",
                ),
                rx.el.div(
                    rx.icon(
                        "compass", class_name="h-6 w-6 text-[#4b5563] mb-2"
                    ),
                    rx.el.p(
                        "Your journal is still blank.",
                        class_name="text-sm font-semibold text-[#404040]",
                    ),
                    rx.el.p(
                        "Once help posts start flowing, they'll be listed here.",
                        class_name="text-sm font-medium text-[#4b5563] mt-1",
                    ),
                    class_name="flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#d4d4d4] bg-white/60 px-6 py-10",
                ),
            ),
            class_name="w-full",
        ),
        class_name="flex flex-col gap-[17px] w-full",
    )


def loading_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-28 w-full rounded-3xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-14 w-full rounded-2xl bg-[#e5e5e5]"
        ),
        rx.el.div(
            class_name="animate-pulse h-80 w-full rounded-3xl bg-[#e5e5e5]"
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def profile_screen() -> rx.Component:
    return rx.el.div(
        identity_passport(),
        error_banner(localized_profile_form_message(ProfileState.error)),
        success_banner(
            localized_profile_form_message(ProfileState.success), centered=True
        ),
        rx.el.div(
            my_information_section(),
            skills_knowledge_section(),
            metrics_section(),
            blocked_members_section(),
            class_name="gah-edge-stack flex w-full flex-col gap-0 bg-white",
        ),
        membership_information_section(),
        membership_notices_panel(),
        policy_links_row(),
        sign_out_action(),
        class_name="gah-profile-screen flex flex-col gap-[17px] w-full",
    )


def community_screen() -> rx.Component:
    return community_panel()


def inbox_screen() -> rx.Component:
    return messages_panel()


def screen_content() -> rx.Component:
    """The complete existing screen for whichever section is active."""
    return rx.match(
        ProfileState.active_tab,
        ("profile", profile_screen()),
        ("help", help_hub_panel()),
        ("upcoming", help_hub_panel()),
        ("get_help", help_hub_panel()),
        ("community", community_screen()),
        ("inbox", inbox_screen()),
        ("details", details_tab()),
        ("post", help_post_panel()),
        ("people", find_people_panel()),
        ("contacts", contacts_panel()),
        ("messages", messages_panel()),
        ("area", profile_screen()),
        ("activity", activity_tab()),
        ("admin", admin_panel()),
        profile_screen(),
    )


def profile_tabs() -> rx.Component:
    """Full page-like member screen that replaces the map content area.

    The dock stays fixed on top of this scroll container; the centre Map dock
    item is the only route back, so there is no close control here.
    """
    return rx.el.section(
        contextual_header(),
        rx.el.div(
            rx.cond(
                ProfileState.is_loading & ~ProfileState.loaded,
                loading_skeleton(),
                screen_content(),
            ),
            class_name=rx.cond(
                ProfileState.active_tab == "community",
                "min-h-0 flex-1 overflow-y-auto overscroll-contain w-full max-w-[100rem] mx-auto px-4 sm:px-6 pt-5 pb-[calc(6.5rem+env(safe-area-inset-bottom))]",
                "w-full max-w-[100rem] mx-auto px-4 sm:px-6 pt-5 pb-[calc(6.5rem+env(safe-area-inset-bottom))]",
            ),
        ),
        on_mount=NotificationState.load_notifications,
        aria_label=ProfileState.active_tab_label,
        class_name=rx.cond(
            ProfileState.active_tab == "community",
            "gah-member-section flex flex-col min-h-0 w-full flex-1 overflow-hidden",
            "gah-member-section min-h-0 w-full flex-1 overflow-y-auto overscroll-contain",
        ),
    )
