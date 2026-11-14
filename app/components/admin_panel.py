import reflex as rx
from app.avatars import member_avatar
from app.interface_i18n import ui

from app.models import CATEGORY_LABELS
from app.states.admin_state import AdminState

TH = "px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[#4b5563] border-b border-[#f7d9a0] whitespace-nowrap"
TD = "px-4 py-3 text-sm font-medium text-[#404040] align-middle whitespace-nowrap"
ROW = "border-b border-[#f7d9a0] transition-colors hover:bg-[#fff7e8]/50 even:bg-white/50"

SUMMARY_CARDS: list[tuple[str, str, str]] = [
    ("subscribers", "Subscribers", "users-round"),
    ("active_week", "Active this week", "compass"),
    ("posts", "Help posts", "notebook-pen"),
    ("posts_open", "Open posts", "map-pin"),
    ("posts_matched", "Matched posts", "hand-helping"),
    ("posts_completed", "Completed posts", "circle-check-big"),
    ("applications", "Applications", "send"),
    ("accepted", "Accepted jobs", "handshake"),
    ("threads", "Threads", "mails"),
    ("messages", "Messages", "message-square"),
    ("completed_tasks", "Completed tasks", "gift"),
    ("reviews", "Reviews", "star"),
    ("open_reports", "Open reports", "shield-alert"),
    ("flagged_members", "Flagged members", "triangle-alert"),
]


def th(label: str, icon: str) -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#e08b12]"),
            rx.el.span(label),
            class_name="flex items-center gap-1.5",
        ),
        class_name=TH,
    )


def summary_card(item: tuple[str, str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item[2], class_name="h-4 w-4 text-[#e08b12]"),
            class_name="flex items-center justify-center size-9 rounded-xl bg-[#fff7e8] shrink-0",
        ),
        rx.el.p(
            AdminState.summary[item[0]],
            class_name="mt-3 text-2xl font-bold text-[#111827]",
        ),
        rx.el.p(
            item[1],
            class_name="text-[11px] font-semibold uppercase tracking-wide text-[#4b5563]",
        ),
        class_name="w-full rounded-2xl border border-[#f7d9a0] bg-white p-4",
    )


def section_button(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.icon(item["icon"], class_name="h-4 w-4"),
        item["label"],
        type="button",
        on_click=lambda: AdminState.set_section(item["value"]),
        class_name=rx.cond(
            AdminState.section == item["value"],
            "flex items-center gap-2 rounded-xl bg-[#fff7e8] px-4 py-2 text-sm font-semibold text-[#111827] border border-[#e08b12] whitespace-nowrap",
            "flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-[#4b5563] border border-transparent transition-colors hover:text-[#111827] whitespace-nowrap",
        ),
    )


def table_shell(header: rx.Component, body: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.table(
                rx.el.thead(header),
                rx.el.tbody(body, class_name="bg-white"),
                class_name="table-auto min-w-full",
            ),
            class_name="overflow-x-auto",
        ),
        class_name="w-full overflow-hidden rounded-2xl border border-[#f7d9a0] bg-white",
    )


def pill(value: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        value,
        class_name=rx.cond(
            value == "completed",
            "w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827] capitalize",
            rx.cond(
                value == "open",
                "w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827] capitalize",
                "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#4b5563] capitalize",
            ),
        ),
    )


def bool_pill(flag: rx.Var[bool], label: str) -> rx.Component:
    return rx.el.span(
        rx.cond(
            flag,
            rx.icon("check", class_name="h-3 w-3"),
            rx.icon("clock", class_name="h-3 w-3"),
        ),
        label,
        class_name=rx.cond(
            flag,
            "w-fit flex items-center gap-1 rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827]",
            "w-fit flex items-center gap-1 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#4b5563]",
        ),
    )


def subscriber_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.image(
                    src=member_avatar(
                        row["avatar_path"], f"member-{row['id']}"
                    ),
                    class_name="size-8 rounded-full bg-[#fff7e8] shrink-0",
                ),
                rx.el.div(
                    rx.el.p(
                        row["name"],
                        class_name="text-sm font-semibold text-[#111827]",
                    ),
                    rx.el.p(
                        row["email"],
                        class_name="text-[11px] font-medium text-[#4b5563]",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-3",
            ),
            class_name=TD,
        ),
        rx.el.td(pill(row["mode"]), class_name=TD),
        rx.el.td(row["joined"], class_name=TD),
        rx.el.td(row["last_seen"], class_name=TD),
        rx.el.td(row["posts"], class_name=TD),
        rx.el.td(row["applications"], class_name=TD),
        rx.el.td(row["reviews"], class_name=TD),
        rx.el.td(row["kindness"], class_name=TD),
        class_name=ROW,
    )


def subscribers_table() -> rx.Component:
    return table_shell(
        rx.el.tr(
            th("Subscriber", "users-round"),
            th("Mode", "compass"),
            th("Joined", "calendar"),
            th("Last seen", "clock"),
            th("Posts", "notebook-pen"),
            th("Offers", "hand-helping"),
            th("Reviews", "star"),
            th("Kindness", "sparkles"),
            class_name="bg-white",
        ),
        rx.foreach(AdminState.subscribers, subscriber_row),
    )


def post_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["title"],
                class_name="text-sm font-semibold text-[#111827] max-w-[18rem] truncate",
            ),
            class_name=TD,
        ),
        rx.el.td(row["author"], class_name=TD),
        rx.el.td(
            rx.el.span(
                CATEGORY_LABELS.get(row["category"], row["category"]),
                class_name="w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827]",
            ),
            class_name=TD,
        ),
        rx.el.td(
            rx.el.span(
                row["reward"],
                class_name="w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-semibold text-[#111827] capitalize",
            ),
            class_name=TD,
        ),
        rx.el.td(row["city"], class_name=TD),
        rx.el.td(pill(row["status"]), class_name=TD),
        rx.el.td(
            rx.el.span(row["urgency"], class_name="capitalize"), class_name=TD
        ),
        rx.el.td(row["applicants"], class_name=TD),
        rx.el.td(row["created"], class_name=TD),
        class_name=ROW,
    )


def posts_table() -> rx.Component:
    return table_shell(
        rx.el.tr(
            th("Title", "notebook-pen"),
            th("Author", "users-round"),
            th("Category", "compass"),
            th("Reward", "gift"),
            th("City", "map-pin"),
            th("Status", "activity"),
            th("Urgency", "clock"),
            th("Applicants", "hand-helping"),
            th("Created", "calendar"),
            class_name="bg-white",
        ),
        rx.foreach(AdminState.posts, post_row),
    )


def accepted_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["title"],
                class_name="text-sm font-semibold text-[#111827] max-w-[18rem] truncate",
            ),
            class_name=TD,
        ),
        rx.el.td(row["poster"], class_name=TD),
        rx.el.td(row["helper"], class_name=TD),
        rx.el.td(pill(row["post_status"]), class_name=TD),
        rx.el.td(row["accepted_at"], class_name=TD),
        class_name=ROW,
    )


def accepted_table() -> rx.Component:
    return table_shell(
        rx.el.tr(
            th("Job", "hand-helping"),
            th("Poster", "notebook-pen"),
            th("Helper", "users-round"),
            th("Post status", "activity"),
            th("Accepted", "calendar"),
            class_name="bg-white",
        ),
        rx.foreach(AdminState.accepted_jobs, accepted_row),
    )


def message_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(f"#{row['thread_id']}", class_name=TD),
        rx.el.td(
            rx.el.p(
                row["title"],
                class_name="text-sm font-semibold text-[#111827] max-w-[14rem] truncate",
            ),
            class_name=TD,
        ),
        rx.el.td(row["sender"], class_name=TD),
        rx.el.td(
            rx.el.p(
                row["snippet"],
                class_name="text-sm font-medium text-[#4b5563] max-w-[22rem] truncate whitespace-normal line-clamp-2",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(row["sent_at"], class_name=TD),
        rx.el.td(bool_pill(row["read"].to(bool), "read"), class_name=TD),
        class_name=ROW,
    )


def messages_table() -> rx.Component:
    return table_shell(
        rx.el.tr(
            th("Thread", "mails"),
            th("Job", "notebook-pen"),
            th("Sender", "users-round"),
            th("Message", "message-square"),
            th("Sent", "clock"),
            th("Status", "eye"),
            class_name="bg-white",
        ),
        rx.foreach(AdminState.recent_messages, message_row),
    )


def task_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["title"],
                class_name="text-sm font-semibold text-[#111827] max-w-[18rem] truncate",
            ),
            class_name=TD,
        ),
        rx.el.td(row["poster"], class_name=TD),
        rx.el.td(row["helper"], class_name=TD),
        rx.el.td(f"{row['minutes']} min", class_name=TD),
        rx.el.td(row["reward_given"], class_name=TD),
        rx.el.td(
            rx.el.div(
                bool_pill(row["poster_confirmed"].to(bool), "poster"),
                bool_pill(row["helper_confirmed"].to(bool), "helper"),
                class_name="flex items-center gap-1.5",
            ),
            class_name=TD,
        ),
        rx.el.td(row["completed_at"], class_name=TD),
        class_name=ROW,
    )


def tasks_table() -> rx.Component:
    return table_shell(
        rx.el.tr(
            th("Job", "circle-check-big"),
            th("Poster", "notebook-pen"),
            th("Helper", "hand-helping"),
            th("Duration", "hourglass"),
            th("Reward given", "gift"),
            th("Confirmations", "check"),
            th("Completed", "calendar"),
            class_name="bg-white",
        ),
        rx.foreach(AdminState.completed_tasks, task_row),
    )


def review_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(row["reviewer"], class_name=TD),
        rx.el.td(row["reviewee"], class_name=TD),
        rx.el.td(
            rx.el.span(
                row["direction_label"],
                class_name="w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#4b5563]",
            ),
            class_name=TD,
        ),
        rx.el.td(
            rx.el.span(
                rx.icon("star", class_name="h-3 w-3"),
                f"{row['rating']}/5",
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-semibold text-[#e08b12]",
            ),
            class_name=TD,
        ),
        rx.el.td(
            rx.el.p(
                row["comment"],
                class_name="text-sm font-medium text-[#4b5563] max-w-[22rem] whitespace-normal line-clamp-2",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            bool_pill(row["kindness_flag"].to(bool), "badge"), class_name=TD
        ),
        rx.el.td(row["created"], class_name=TD),
        class_name=ROW,
    )


def reviews_table() -> rx.Component:
    return table_shell(
        rx.el.tr(
            th("Reviewer", "users-round"),
            th("Reviewee", "user-round-plus"),
            th("Direction", "compass"),
            th("Rating", "star"),
            th("Comment", "message-square"),
            th("Kindness", "sparkles"),
            th("Created", "calendar"),
            class_name="bg-white",
        ),
        rx.foreach(AdminState.reviews, review_row),
    )


def status_pill(row: dict[str, str]) -> rx.Component:
    return rx.el.span(
        row["status_label"],
        class_name=rx.cond(
            row["status"] == "open",
            "w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-bold text-[#111827]",
            rx.cond(
                row["status"] == "reviewing",
                "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                rx.cond(
                    row["status"] == "resolved",
                    "w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-bold text-[#111827]",
                    "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#4b5563]",
                ),
            ),
        ),
    )


def moderation_pill(row: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            row["moderation_label"],
            class_name=rx.cond(
                row["moderation_status"] == "banned",
                "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                rx.cond(
                    row["moderation_status"] == "warned",
                    "w-fit rounded-full bg-[#fba922] px-2.5 py-0.5 text-[11px] font-bold text-[#111827]",
                    "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#4b5563]",
                ),
            ),
        ),
        rx.el.span(
            f"{row['warning_count']} warning(s)",
            class_name="text-[10px] font-semibold uppercase tracking-wide text-[#4b5563]",
        ),
        rx.cond(
            row["account_active"].to(bool),
            rx.fragment(),
            rx.el.span(
                rx.icon("lock", class_name="h-3 w-3"),
                "Deactivated",
                class_name="w-fit flex items-center gap-1 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[10px] font-bold text-[#e08b12]",
            ),
        ),
        class_name="flex flex-col items-start gap-1",
    )


def safety_actions(row: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                rx.icon("triangle-alert", class_name="h-3 w-3"),
                "Warn",
                type="button",
                disabled=AdminState.is_moderating,
                on_click=lambda: AdminState.warn_member(row["id"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1.5 text-[11px] font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("check", class_name="h-3 w-3"),
                "Resolve",
                type="button",
                disabled=AdminState.is_moderating,
                on_click=lambda: AdminState.resolve_report(row["id"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fba922] px-3 py-1.5 text-[11px] font-bold text-[#111827] transition-colors hover:bg-[#e08b12] disabled:opacity-60",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3 w-3"),
                "Dismiss",
                type="button",
                disabled=AdminState.is_moderating,
                on_click=lambda: AdminState.dismiss_report(row["id"]),
                class_name="w-fit flex items-center gap-1.5 rounded-full border border-[#f7d9a0] bg-white px-3 py-1.5 text-[11px] font-bold text-[#4b5563] transition-colors hover:border-[#e08b12] hover:text-[#e08b12] disabled:opacity-60",
            ),
            class_name="flex flex-wrap items-center gap-1.5",
        ),
        rx.cond(
            AdminState.ban_confirm_id == row["id"],
            rx.el.div(
                rx.el.p(
                    "Ban this member? The account is deactivated immediately.",
                    class_name="text-[11px] font-semibold text-[#e08b12] whitespace-normal",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("ban", class_name="h-3 w-3"),
                        "Confirm ban",
                        type="button",
                        disabled=AdminState.is_moderating,
                        on_click=lambda: AdminState.ban_member(row["id"]),
                        class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#e08b12] px-3 py-1.5 text-[11px] font-bold text-white transition-colors hover:bg-[#b86e08] disabled:opacity-60",
                    ),
                    rx.el.button(
                        "Cancel",
                        type="button",
                        on_click=AdminState.cancel_ban,
                        class_name="w-fit rounded-full border border-[#f7d9a0] bg-white px-3 py-1.5 text-[11px] font-bold text-[#4b5563] transition-colors hover:border-[#404040]",
                    ),
                    class_name="flex items-center gap-1.5 mt-1.5",
                ),
                class_name="mt-2 rounded-xl border border-[#f7d9a0] bg-[#fff7e8] px-3 py-2 max-w-[16rem]",
            ),
            rx.el.button(
                rx.icon("ban", class_name="h-3 w-3"),
                "Ban…",
                type="button",
                on_click=lambda: AdminState.request_ban(row["id"]),
                class_name="mt-1.5 w-fit flex items-center gap-1.5 rounded-full border border-[#f7d9a0] bg-white px-3 py-1.5 text-[11px] font-bold text-[#e08b12] transition-colors hover:bg-[#fff7e8]",
            ),
        ),
        class_name="flex flex-col items-start",
    )


def safety_row(row: dict[str, str]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    row["category_label"],
                    class_name=rx.cond(
                        row["is_severe"].to(bool),
                        "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                        "w-fit rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                    ),
                ),
                rx.el.p(
                    row["job_title"],
                    class_name="mt-1 text-[11px] font-medium text-[#4b5563] max-w-[12rem] truncate",
                ),
                rx.el.p(
                    row["created"],
                    class_name="text-[11px] font-medium text-[#4b5563]",
                ),
                class_name="flex flex-col items-start",
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.el.p(
                row["details"],
                class_name="text-sm font-medium text-[#404040] max-w-[24rem] whitespace-normal leading-relaxed",
            ),
            rx.cond(
                row["admin_note"],
                rx.el.p(
                    f"Admin note: {row['admin_note']}",
                    class_name="mt-1.5 text-[11px] font-semibold text-[#e08b12] max-w-[24rem] whitespace-normal",
                ),
                rx.fragment(),
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.p(
                    row["reporter"],
                    class_name="text-sm font-semibold text-[#111827]",
                ),
                rx.el.p(
                    row["reporter_email"],
                    class_name="text-[11px] font-medium text-[#4b5563]",
                ),
                class_name="min-w-0",
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.p(
                    row["reported"],
                    class_name="text-sm font-semibold text-[#111827]",
                ),
                rx.el.p(
                    row["reported_email"],
                    class_name="text-[11px] font-medium text-[#4b5563]",
                ),
                class_name="min-w-0",
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.el.span(
                rx.icon("star", class_name="h-3 w-3"),
                f"{row['one_star_count']}",
                title="One-star reviews received",
                class_name=rx.cond(
                    row["one_star_count"].to(int) > 2,
                    "w-fit flex items-center gap-1 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#e08b12]",
                    "w-fit flex items-center gap-1 rounded-full bg-[#fff7e8] px-2.5 py-0.5 text-[11px] font-bold text-[#4b5563]",
                ),
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(moderation_pill(row), class_name="px-4 py-3 align-top"),
        rx.el.td(status_pill(row), class_name="px-4 py-3 align-top"),
        rx.el.td(safety_actions(row), class_name="px-4 py-3 align-top"),
        class_name=ROW,
    )


def content_report_row(row: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.h4(
            f"{row['target_type']} #{row['target_id']} · {row['status']}",
            class_name="text-sm font-bold text-black",
        ),
        rx.el.p(
            row["excerpt"],
            class_name="mt-2 whitespace-pre-wrap break-words text-sm text-[#404040]",
        ),
        rx.el.p(
            f"Category: {row['category']}",
            class_name="mt-2 text-xs font-bold text-[#e08b12]",
        ),
        rx.el.p(
            row["details"],
            class_name="mt-1 whitespace-pre-wrap break-words text-sm text-black",
        ),
        rx.el.p(
            f"Reporter: {row['reporter']} · Reported member: {row['reported']}",
            class_name="mt-2 text-xs text-[#404040]",
        ),
        rx.el.p(
            f"Created: {row['created']} · Reviewed: {row['reviewed']}",
            class_name="mt-1 text-xs text-[#404040]",
        ),
        rx.el.p(
            f"Admin note: {row['admin_note']} · Updated: {row['note_updated']}",
            class_name="mt-1 whitespace-pre-wrap break-words text-xs text-[#e08b12]",
        ),
        rx.el.div(
            rx.foreach(
                ["reviewing", "resolved", "dismissed", "warn"],
                lambda action: rx.el.button(
                    action.title(),
                    type="button",
                    on_click=lambda: AdminState.moderate_content(
                        row["id"].to(int), action
                    ),
                    class_name="rounded-full border border-[#e08b12] bg-white px-3 py-2 text-xs font-bold text-[#e08b12] hover:bg-[#fff7e8]",
                ),
            ),
            rx.cond(
                AdminState.content_ban_confirm_id == row["id"].to(int),
                rx.el.div(
                    rx.el.p(
                        "Ban this member? Their account will be deactivated.",
                        class_name="text-xs text-black",
                    ),
                    rx.el.button(
                        "Confirm ban",
                        type="button",
                        on_click=lambda: AdminState.moderate_content(
                            row["id"].to(int), "ban"
                        ),
                        class_name="rounded-full bg-[#e08b12] px-3 py-2 text-xs font-bold text-white",
                    ),
                    rx.el.button(
                        "Cancel",
                        type="button",
                        on_click=AdminState.cancel_content_ban,
                        class_name="rounded-full border border-[#f7d9a0] bg-white px-3 py-2 text-xs text-black",
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.button(
                    "Ban…",
                    type="button",
                    on_click=lambda: AdminState.request_content_ban(
                        row["id"].to(int)
                    ),
                    class_name="rounded-full bg-[#e08b12] px-3 py-2 text-xs font-bold text-white",
                ),
            ),
            class_name="mt-3 flex flex-wrap items-center gap-2",
        ),
        class_name="min-w-0 rounded-2xl border border-[#f7d9a0] bg-white p-4",
    )


def safety_table() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("shield-alert", class_name="h-3.5 w-3.5"),
                    "Incident ledger",
                    class_name="w-fit flex items-center gap-2 rounded-full bg-[#fff7e8] px-3 py-1 text-xs font-bold text-[#e08b12]",
                ),
                rx.el.h3(
                    "Safety review",
                    class_name="mt-2 text-lg font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    "Private reports filed by the two people on a completed job. "
                    "Nothing here is public, and no account is ever banned "
                    "automatically — every decision below is yours.",
                    class_name="mt-1 text-sm font-medium text-[#4b5563] leading-relaxed max-w-2xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.el.label(
                "Admin note (optional) — saved with the next action you take",
                html_for="admin_moderation_note",
                class_name="text-xs font-semibold text-[#404040]",
            ),
            rx.el.textarea(
                id="admin_moderation_note",
                rows="2",
                placeholder="What did you check, and why this outcome?",
                default_value=AdminState.admin_note,
                on_change=AdminState.set_admin_note.debounce(400),
                class_name="mt-1.5 w-full rounded-xl border border-[#f7d9a0] bg-[#ffffff] px-4 py-2.5 text-sm font-medium text-[#111827] placeholder:text-[#4b5563] outline-hidden transition-colors focus:border-[#e08b12] focus:ring-2 focus:ring-[#fff7e8] resize-y",
            ),
            class_name="w-full mt-4",
        ),
        rx.cond(
            AdminState.moderation_error,
            rx.el.p(
                AdminState.moderation_error,
                role="alert",
                class_name="mt-3 rounded-xl bg-[#fff7e8] px-3 py-2 text-xs font-bold text-[#e08b12]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AdminState.moderation_success,
            rx.el.p(
                AdminState.moderation_success,
                class_name="mt-3 rounded-xl bg-[#fba922] px-3 py-2 text-xs font-bold text-[#111827]",
            ),
            rx.fragment(),
        ),
        rx.el.h3(
            ui("Profile, message and community reports"),
            class_name="mt-5 text-lg font-bold text-black",
        ),
        rx.el.p(
            ui(
                "Up to 60 reports, open and reviewing first. Use the admin note above for your next decision."
            ),
            class_name="mt-1 text-xs text-[#404040]",
        ),
        rx.cond(
            AdminState.content_reports.length() > 0,
            rx.el.div(
                rx.foreach(AdminState.content_reports, content_report_row),
                class_name="mt-3 flex w-full flex-col gap-3",
            ),
            rx.el.p(
                "No content reports have been filed.",
                class_name="mt-3 text-sm text-[#404040]",
            ),
        ),
        rx.el.h3(
            ui("Completed-job safety reports"),
            class_name="mt-5 text-lg font-bold text-black",
        ),
        rx.cond(
            AdminState.safety_reports.length() > 0,
            rx.el.div(
                table_shell(
                    rx.el.tr(
                        th("Category", "shield-alert"),
                        th("What happened", "message-square"),
                        th("Reporter", "user-round"),
                        th("Reported member", "user-round-x"),
                        th("1-star", "star"),
                        th("Account", "gavel"),
                        th("Report status", "activity"),
                        th("Decision", "scale"),
                        class_name="bg-white",
                    ),
                    rx.foreach(AdminState.safety_reports, safety_row),
                ),
                class_name="w-full mt-4",
            ),
            rx.el.div(
                rx.icon(
                    "shield-check",
                    class_name="h-6 w-6 text-[#e08b12] mb-2",
                ),
                rx.el.p(
                    "No safety reports have been filed.",
                    class_name="text-sm font-bold text-[#111827]",
                ),
                rx.el.p(
                    "Reports appear here the moment someone tells us about a "
                    "bad experience on a completed job.",
                    class_name="mt-1 text-sm font-medium text-[#4b5563]",
                ),
                class_name="mt-4 flex flex-col items-center justify-center text-center w-full rounded-2xl border border-dashed border-[#f7d9a0] bg-white px-6 py-10",
            ),
        ),
        class_name="w-full rounded-3xl border border-[#f7d9a0] bg-white p-5 sm:p-6",
    )


def empty_note() -> rx.Component:
    return rx.el.p(
        ui("Rows appear here as neighbours sign up, post, chat and review."),
        class_name="text-xs font-medium text-[#4b5563] mt-3",
    )


def admin_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("shield", class_name="h-3.5 w-3.5"),
                    "Backend activity",
                    class_name="w-fit flex items-center gap-2 rounded-full bg-[#fba922] px-3 py-1 text-xs font-semibold text-[#111827]",
                ),
                rx.el.h2(
                    "Everything happening across Go and Help.",
                    class_name="mt-3 text-2xl font-bold tracking-tight text-[#111827]",
                ),
                rx.el.p(
                    "Subscribers, help posts, accepted jobs, messages, completed tasks and the "
                    "full review history — the ledger behind the journal.",
                    class_name="mt-1 text-sm font-medium text-[#4b5563] leading-relaxed",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("star", class_name="h-3.5 w-3.5"),
                    f"{AdminState.avg_rating:.1f} avg rating",
                    class_name="w-fit flex items-center gap-1.5 rounded-full bg-[#fff7e8] px-3 py-1.5 text-xs font-semibold text-[#e08b12]",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                    "Refresh",
                    type="button",
                    on_click=AdminState.load_activity,
                    class_name="w-fit flex items-center gap-2 rounded-full border border-[#f7d9a0] bg-white px-4 py-2 text-xs font-semibold text-[#404040] transition-colors hover:border-[#e08b12] hover:text-[#e08b12]",
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="w-full flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-3xl border border-[#f7d9a0] bg-white p-6",
        ),
        rx.cond(
            AdminState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-24 w-full rounded-2xl bg-[#fff7e8]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-64 w-full rounded-2xl bg-[#fff7e8]"
                ),
                class_name="flex flex-col gap-4 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    rx.foreach(SUMMARY_CARDS, summary_card),
                    class_name="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 w-full",
                ),
                rx.el.div(
                    rx.foreach(AdminState.sections, section_button),
                    class_name="flex items-center gap-2 rounded-2xl bg-[#fff7e8] p-1.5 w-full overflow-x-auto",
                ),
                rx.el.div(
                    rx.match(
                        AdminState.section,
                        ("subscribers", subscribers_table()),
                        ("posts", posts_table()),
                        ("accepted", accepted_table()),
                        ("messages", messages_table()),
                        ("tasks", tasks_table()),
                        ("reviews", reviews_table()),
                        ("safety", safety_table()),
                        subscribers_table(),
                    ),
                    rx.cond(
                        AdminState.section == "safety",
                        rx.fragment(),
                        empty_note(),
                    ),
                    class_name="w-full",
                ),
                class_name="flex flex-col gap-5 w-full",
            ),
        ),
        on_mount=AdminState.load_activity,
        class_name="flex flex-col gap-5 w-full",
    )
