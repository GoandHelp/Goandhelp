"""Received reviews, presented in Community › Reviews.

The cards are exactly the ones that used to live on the Profile screen; the
data still comes from `ProfileState.received_reviews`, which is loaded by the
existing profile loader.
"""

import reflex as rx

from app.interface_i18n import ui
from app.avatars import animal_avatar

from app.components.language_control import browser_translatable_text

from app.components.feedback import avatar_with_tick
from app.components.notification_badge import corner_activity_dot
from app.components.messages_panel import review_section
from app.components.disclosure import disclosure_arrow
from app.states.notification_state import NotificationState
from app.states.messaging_state import MessagingState
from app.states.profile_state import ProfileState, ReceivedReview


def review_rating_star(state: rx.Var[str]) -> rx.Component:
    return rx.match(
        state,
        (
            "full",
            rx.icon(
                "star", class_name="size-6 stroke-[#fba922] fill-[#fba922]"
            ),
        ),
        (
            "half",
            rx.icon(
                "star-half",
                class_name="size-6 stroke-[#fba922] fill-[#fba922]",
            ),
        ),
        rx.icon("star", class_name="size-6 stroke-[#fba922]"),
    )


def your_reviews_header() -> rx.Component:
    return rx.el.div(
        corner_activity_dot(
            NotificationState.reviews_unread > 0,
            "New activity in Reviews",
        ),
        rx.el.div(
            rx.foreach(ProfileState.combined_star_states, review_rating_star),
            role="img",
            title=ProfileState.combined_rating_label,
            aria_label=ProfileState.combined_rating_label,
            class_name="flex items-center justify-center gap-1",
        ),
        rx.el.h3(
            rx.el.span(
                ProfileState.received_reviews.length(),
                class_name="text-[#e08b12]",
            ),
            " ",
            rx.cond(
                ProfileState.received_reviews.length() == 1,
                ui("Review received"),
                ui("Reviews received"),
            ),
            class_name="w-full px-10 text-center text-xl sm:text-2xl font-bold tracking-tight text-black leading-tight",
        ),
        rx.el.p(
            f"{ProfileState.combined_rating_avg:.1f} out of 5",
            class_name="text-sm font-semibold text-[#4b5563]",
        ),
        class_name="relative flex w-full flex-col items-center gap-1.5",
    )


def received_rating_stars(
    score: rx.Var[int], overall: bool = False
) -> rx.Component:
    return rx.el.div(
        rx.foreach(
            rx.Var.range(1, 6),
            lambda step: rx.icon(
                "star",
                class_name=rx.cond(
                    overall,
                    rx.cond(
                        step <= score,
                        "size-6 stroke-[#fba922] fill-[#fba922]",
                        "size-6 stroke-[#fba922] fill-none",
                    ),
                    rx.cond(
                        step <= score,
                        "size-4 stroke-[#fba922] fill-[#fba922]",
                        "size-4 stroke-[#fba922] fill-none",
                    ),
                ),
            ),
        ),
        role="img",
        aria_label=f"{score} out of 5 stars",
        class_name="flex shrink-0 items-center gap-0.5",
    )


def review_category_row(item: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.span(item["label"], class_name="text-sm font-medium text-black"),
        rx.el.div(
            received_rating_stars(item["score"].to(int)),
            rx.el.span(
                f"{item['score']}/5",
                class_name="text-sm font-semibold text-[#e08b12]",
            ),
            class_name="flex shrink-0 items-center gap-2",
        ),
        class_name="flex w-full items-center justify-between gap-3 py-2",
    )


def received_review_card(review: ReceivedReview) -> rx.Component:
    return rx.el.article(
        rx.el.button(
            avatar_with_tick(
                rx.cond(
                    review["reviewer_avatar"],
                    rx.get_upload_url(review["reviewer_avatar"]),
                    animal_avatar(review["reviewer_seed"]),
                ),
                review["reviewer_verified"],
                "size-10 rounded-full bg-[#fff7e8] shrink-0",
                "Reviewer avatar",
            ),
            rx.el.div(
                rx.el.p(
                    review["reviewer_name"],
                    class_name="text-sm font-semibold text-black leading-tight",
                ),
                rx.el.p(
                    review["job_title"],
                    class_name="text-sm font-medium text-[#4b5563] mt-0.5 break-words",
                ),
                rx.el.div(
                    received_rating_stars(review["rating"], True),
                    class_name="mt-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            disclosure_arrow(
                ProfileState.open_received_review_ids.contains(review["id"])
            ),
            type="button",
            aria_label=f"Review from {review['reviewer_name']} for {review['job_title']}",
            aria_expanded=ProfileState.open_received_review_ids.contains(
                review["id"]
            ),
            aria_controls=f"received-review-{review['id']}",
            on_click=lambda: ProfileState.toggle_received_review(review["id"]),
            class_name="gah-review-toggle flex items-start gap-3 w-full text-left rounded-xl bg-white p-1 focus-visible:ring-2 focus-visible:ring-[#e08b12]",
        ),
        rx.cond(
            ProfileState.open_received_review_ids.contains(review["id"]),
            rx.el.div(
                rx.el.div(
                    rx.foreach(review["categories"], review_category_row),
                    class_name="flex w-full flex-col divide-y divide-gray-100 mt-3",
                ),
                rx.el.div(
                    rx.el.span(
                        rx.icon("calendar", class_name="h-3 w-3"),
                        review["created"],
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-1 text-[11px] font-semibold text-[#4b5563]",
                    ),
                    rx.cond(
                        review["kindness_flag"],
                        rx.el.span(
                            rx.icon("sparkles", class_name="h-3 w-3"),
                            ui("Kindness badge"),
                            class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-2.5 py-1 text-[11px] font-semibold text-black",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-3",
                ),
                rx.cond(
                    review["comment"],
                    browser_translatable_text(
                        review["comment"],
                        class_name="mt-3 text-sm font-medium italic leading-relaxed text-[#4b5563]",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    review["response"],
                    rx.el.div(
                        rx.el.p(
                            ui("Recipient’s response"),
                            class_name="text-xs font-bold text-[#e08b12]",
                        ),
                        browser_translatable_text(
                            review["response"],
                            class_name="mt-1 text-sm leading-relaxed text-[#4b5563]",
                        ),
                        class_name="mt-3 border-l-2 border-[#fff7e8] pl-3",
                    ),
                    rx.fragment(),
                ),
                id=f"received-review-{review['id']}",
                class_name="w-full border-t border-[#f7d9a0] pt-3",
            ),
            rx.fragment(),
        ),
        key=review["id"],
        class_name="w-full rounded-none border-0 bg-white p-4",
    )


def received_reviews_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h3(
                ui("My reviews"),
                class_name="w-full px-10 text-center text-xl sm:text-2xl font-bold tracking-tight text-black leading-tight",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                type="button",
                title="Reload pending and received reviews",
                aria_label="Reload pending and received reviews",
                on_click=[
                    MessagingState.load_threads,
                    ProfileState.load_profile,
                ],
                class_name="absolute right-0 top-1/2 -translate-y-1/2 size-8 flex items-center justify-center rounded-full border border-[#d4d4d4] bg-white text-[#e08b12] transition-colors hover:border-[#fba922] focus-visible:ring-2 focus-visible:ring-[#fba922]",
            ),
            class_name="relative flex w-full min-h-8 items-center",
        ),
        rx.cond(
            ProfileState.is_loading & ~ProfileState.loaded,
            rx.el.div(
                rx.el.div(
                    class_name="h-20 w-full animate-pulse rounded-xl bg-[#fff7e8]"
                ),
                rx.el.div(
                    class_name="h-20 w-full animate-pulse rounded-xl bg-[#fff7e8]"
                ),
                role="status",
                aria_label=ui("Loading reviews"),
                class_name="mt-4 flex w-full flex-col gap-2",
            ),
            rx.cond(
                ProfileState.received_reviews.length() > 0,
                rx.el.div(
                    rx.foreach(
                        ProfileState.received_reviews, received_review_card
                    ),
                    class_name="gah-edge-stack flex flex-col gap-0 w-full mt-4",
                ),
                rx.el.div(
                    rx.icon(
                        "heart-handshake",
                        class_name="h-6 w-6 text-[#fba922] mb-2",
                    ),
                    rx.el.p(
                        ui("Your first review is still waiting"),
                        class_name="text-sm font-semibold text-black",
                    ),
                    rx.el.p(
                        ui(
                            "Keep showing up with a helping hand — reviews will appear here after a completed job."
                        ),
                        class_name="mt-1 max-w-xl text-sm font-medium leading-relaxed text-[#4b5563]",
                    ),
                    class_name="gah-edge-stack mt-4 flex flex-col gap-0 w-full items-center justify-center text-center bg-white px-6 py-8",
                ),
            ),
        ),
        class_name="w-full bg-transparent",
    )


def community_reviews_section() -> rx.Component:
    return rx.el.div(
        your_reviews_header(),
        rx.el.section(
            rx.el.h3(
                ui("To review"),
                class_name="text-center text-xl sm:text-2xl font-bold text-black",
            ),
            review_section(),
            rx.cond(
                MessagingState.is_loading
                & (MessagingState.review_targets.length() == 0),
                rx.el.div(
                    class_name="h-20 w-full animate-pulse rounded-xl bg-[#fff7e8]"
                ),
                rx.cond(
                    MessagingState.review_targets.length() > 0,
                    rx.fragment(),
                    rx.el.div(
                        rx.el.p(
                            ui("No reviews waiting to be written."),
                            class_name="text-sm font-medium text-[#4b5563]",
                        ),
                        class_name="gah-edge-stack mt-4 flex w-full items-center justify-center rounded-2xl bg-white px-6 py-8 text-center shadow-sm",
                    ),
                ),
            ),
            class_name="flex w-full flex-col gap-3",
        ),
        received_reviews_section(),
        on_mount=MessagingState.load_review_targets,
        class_name="pt-3 flex flex-col gap-4 w-full bg-[#ffffff] text-black",
    )
