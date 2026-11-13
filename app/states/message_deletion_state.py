import reflex as rx

import logging
from sqlalchemy import text
from app.message_photos import decode_message, message_preview

from app.states.auth_state import AuthState


class MessageDeletionState(rx.State):
    error: str = ""
    success: str = ""

    @rx.event
    async def delete_message(
        self, kind: str, message_id: int, merged: bool = False
    ):
        from app.states.contacts_state import ContactsState
        from app.states.messaging_state import MessagingState
        from app.states.noncontact_state import NonContactMessagingState
        from app.states.unified_inbox_state import UnifiedInboxState

        self.error = ""
        self.success = ""
        sid = (await self.get_state(AuthState)).subscriber_id
        contacts = await self.get_state(ContactsState)
        jobs = await self.get_state(MessagingState)
        direct = await self.get_state(NonContactMessagingState)
        sources = {
            "contact": (
                "skillkind_contact_message",
                "skillkind_contact_link",
                "contact_link_id",
                "requester_id",
                "recipient_id",
                "sent_at",
                contacts.selected_contact["link_id"],
            ),
            "noncontact": (
                "skillkind_noncontact_message",
                "skillkind_noncontact_conversation",
                "conversation_id",
                "initiator_id",
                "recipient_id",
                "created_at",
                direct.selected["conv_id"],
            ),
            "job": (
                "skillkind_message",
                "skillkind_message_thread",
                "thread_id",
                "poster_id",
                "helper_id",
                "sent_at",
                jobs.selected_thread["id"],
            ),
        }
        if kind not in sources or message_id <= 0 or not sid.isdigit():
            self.error = "That message is not available."
            return
        table, parent, foreign_key, first, second, stamp, selected = sources[
            kind
        ]
        scope = "p.id = :selected"
        if merged:
            scope = f"""EXISTS (
                SELECT 1 FROM skillkind_contact_link cl
                WHERE cl.id = :link_id AND cl.status = 'accepted'
                  AND :sid IN (cl.requester_id, cl.recipient_id)
                  AND ((p.{first} = cl.requester_id AND p.{second} = cl.recipient_id)
                    OR (p.{first} = cl.recipient_id AND p.{second} = cl.requester_id))
            )"""
            if kind == "contact":
                scope = f"{scope} AND p.id = :link_id"
        try:
            async with rx.asession() as session:
                deleted = (
                    await session.execute(
                        text(f"""
                    DELETE FROM {table} m USING {parent} p
                    WHERE m.id = :message_id AND m.{foreign_key} = p.id
                      AND :sid IN (p.{first}, p.{second}) AND {scope}
                      AND NOT EXISTS (
                        SELECT 1 FROM skillkind_member_block mb
                        WHERE (mb.blocker_id = p.{first} AND mb.blocked_id = p.{second})
                           OR (mb.blocker_id = p.{second} AND mb.blocked_id = p.{first})
                      )
                    RETURNING m.{foreign_key}, m.body
                """),
                        {
                            "message_id": message_id,
                            "sid": int(sid),
                            "selected": selected,
                            "link_id": contacts.selected_contact["link_id"],
                        },
                    )
                ).first()
                if deleted is not None:
                    preview_fields = ""
                    preview = ""
                    if kind != "job":
                        last = (
                            await session.execute(
                                text(
                                    f"SELECT body FROM {table} WHERE {foreign_key} = :parent_id ORDER BY {stamp} DESC, id DESC LIMIT 1"
                                ),
                                {"parent_id": int(deleted[0])},
                            )
                        ).first()
                        preview = message_preview(last[0] if last else "")[:255]
                        preview_fields = f""", message_count = (SELECT COUNT(*) FROM {table} WHERE {foreign_key} = :parent_id),
                            last_message_preview = :preview"""
                    await session.execute(
                        text(f"""
                        UPDATE {parent} SET last_message_at =
                            (SELECT MAX({stamp}) FROM {table} WHERE {foreign_key} = :parent_id)
                            {preview_fields}
                        WHERE id = :parent_id
                    """),
                        {"parent_id": int(deleted[0]), "preview": preview},
                    )
                await session.commit()
            self.success = "Message deleted." if deleted is not None else ""
            self.error = (
                ""
                if deleted is not None
                else "That message is no longer available."
            )
            if deleted is not None:
                for photo in decode_message(deleted[1])["photos"]:
                    try:
                        (rx.get_upload_dir() / photo).unlink(missing_ok=True)
                    except Exception as e:
                        logging.exception(f"Error: {e}")
                        self.error = "Message deleted, but photo cleanup failed. Please contact support."
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "We couldn't delete that message. Please try again."
            return
        if merged or kind == "contact":
            yield ContactsState.load_contact_messages
        elif kind == "noncontact":
            yield NonContactMessagingState.load_messages
        else:
            yield MessagingState.load_conversation
        yield UnifiedInboxState.load_index
