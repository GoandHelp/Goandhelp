import reflex as rx

from app.interface_i18n import ui
from app.components.block_dialog import block_member_button
from app.components.report_dialog import report_button
from app.models import REPORT_TARGET_PROFILE
from app.states.contacts_state import ContactsState
from app.components.feedback import error_banner, success_banner


def chat_safety(member_id: rx.Var[int], name: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                rx.cond(
                    ContactsState.accepted_member_ids.contains(member_id),
                    ui("Already a contact"),
                    rx.cond(
                        ContactsState.pending_member_ids.contains(member_id),
                        ui("Contact request pending"),
                        ui("Add contact"),
                    ),
                ),
                type="button",
                disabled=ContactsState.is_requesting
                | ContactsState.accepted_member_ids.contains(member_id)
                | ContactsState.pending_member_ids.contains(member_id),
                on_click=ContactsState.send_request(member_id, ""),
                class_name="w-fit rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#e08b12] hover:bg-[#fff7e8] disabled:text-gray-500",
            ),
            report_button(REPORT_TARGET_PROFILE, member_id, name),
            block_member_button(member_id, name),
            class_name="flex max-w-full flex-wrap items-center justify-center gap-1.5",
        ),
        error_banner(ContactsState.error),
        success_banner(ContactsState.success),
        class_name="flex w-full flex-col gap-2",
    )
