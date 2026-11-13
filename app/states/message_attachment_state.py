import reflex as rx

import asyncio
import logging
from uuid import uuid4
from sqlalchemy import text

from app.image_processing import read_image_upload, process_help_photo_bytes
from app.message_photos import encode_message, message_preview, safe_photo_name


class MessageAttachmentState(rx.State):
    pending: list[str] = []
    scope: str = ""
    account: str = ""
    busy: bool = False
    error: str = ""
    generation: int = 0

    async def _target(self) -> tuple[str, str]:
        from app.states.auth_state import AuthState
        from app.states.unified_inbox_state import UnifiedInboxState
        from app.states.profile_state import ProfileState
        from app.states.contacts_state import ContactsState
        from app.states.messaging_state import MessagingState
        from app.states.noncontact_state import NonContactMessagingState

        auth = await self.get_state(AuthState)
        inbox = await self.get_state(UnifiedInboxState)
        profile = await self.get_state(ProfileState)
        if (
            not auth.is_signed_in
            or not auth.subscriber_id.isdigit()
            or profile.active_tab != "inbox"
            or inbox.view != "thread"
        ):
            return "", ""
        contacts = await self.get_state(ContactsState)
        jobs = await self.get_state(MessagingState)
        direct = await self.get_state(NonContactMessagingState)
        targets = {
            f"contact:{contacts.selected_contact['link_id']}",
            f"job:{jobs.selected_thread['id']}",
            f"noncontact:{direct.selected['conv_id']}",
        }
        if inbox.selected_key not in targets:
            return "", ""
        return auth.subscriber_id, inbox.selected_key

    async def _unlink(self, path: str):
        if safe_photo_name(path):
            try:
                await asyncio.to_thread(
                    (rx.get_upload_dir() / path).unlink, missing_ok=True
                )
            except Exception as e:
                logging.exception(f"Error: {e}")
                raise

    async def _discard(self):
        for path in list(self.pending):
            await self._unlink(path)
            self.pending.remove(path)
        self.scope = ""
        self.account = ""
        self.error = ""
        self.generation += 1

    @rx.event
    async def clear_pending(self):
        try:
            await self._discard()
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Couldn't remove a staged photo. Please try again."

    @rx.event
    async def remove_photo(self, path: str):
        if path not in self.pending or self.busy:
            return
        try:
            await self._unlink(path)
            self.pending.remove(path)
            self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Couldn't remove that photo. Please try again."

    @rx.event
    async def upload_photos(self, files: list[rx.UploadFile]):
        sid, target = await self._target()
        if not target:
            self.error = (
                "Open a signed-in conversation before attaching photos."
            )
            return
        if self.scope != target or self.account != sid:
            await self._discard()
        self.scope, self.account = target, sid
        if not files or len(self.pending) + len(files) > 5:
            self.error = "Attach at most five photos per message."
            return
        self.busy = True
        self.error = ""
        staged: list[str] = []
        try:
            kind, ref = target.split(":")
            await self._authorize(kind, int(ref), int(sid))
            for file in files:
                mime = str(file.content_type or "").lower()
                if mime not in {"image/jpeg", "image/png", "image/webp"}:
                    raise ValueError("Choose JPEG, PNG or WebP photos only.")
                data = await read_image_upload(file)
                payload = await asyncio.to_thread(
                    process_help_photo_bytes, data, str(file.name or ""), mime
                )
                if payload is None:
                    raise ValueError(
                        "That photo is invalid. Use a static JPEG, PNG or WebP up to 3 MB."
                    )
                name = f"message_{uuid4().hex}.webp"
                directory = rx.get_upload_dir()
                directory.mkdir(parents=True, exist_ok=True)
                staged.append(name)
                await asyncio.to_thread((directory / name).write_bytes, payload)
            if await self._target() != (sid, target):
                raise ValueError(
                    "Conversation changed. Attach the photos again."
                )
            self.pending.extend(staged)
            staged = []
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "Couldn't attach photos. Please try again."
            )
        finally:
            for name in staged:
                await self._unlink(name)
            self.busy = False
        return rx.clear_selected_files("inbox_message_photos")

    def _source(self, kind: str) -> tuple[str, str, str, str, str, str]:
        sources = {
            "job": (
                "skillkind_message",
                "skillkind_message_thread",
                "thread_id",
                "poster_id",
                "helper_id",
                "help_post_id",
            ),
            "contact": (
                "skillkind_contact_message",
                "skillkind_contact_link",
                "contact_link_id",
                "requester_id",
                "recipient_id",
                "contact_link_id",
            ),
            "noncontact": (
                "skillkind_noncontact_message",
                "skillkind_noncontact_conversation",
                "conversation_id",
                "initiator_id",
                "recipient_id",
                "noncontact_conversation_id",
            ),
        }
        if kind not in sources:
            raise ValueError("Invalid conversation")
        return sources[kind]

    async def _authorize(self, kind: str, ref: int, sid: int):
        _, parent, _, first, second, _ = self._source(kind)
        accepted = "AND p.status = 'accepted'" if kind == "contact" else ""
        async with rx.asession() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT p.id FROM {parent} p
                JOIN skillkind_subscriber s ON s.id = :sid AND s.is_active
                WHERE p.id = :ref AND :sid IN (p.{first}, p.{second}) {accepted}
                  AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
                    WHERE (b.blocker_id = p.{first} AND b.blocked_id = p.{second})
                       OR (b.blocker_id = p.{second} AND b.blocked_id = p.{first}))
            """),
                    {"ref": ref, "sid": sid},
                )
            ).first()
        if row is None:
            raise ValueError("That conversation isn't available to you.")

    async def _persist(
        self,
        kind: str,
        ref: int,
        caption: str,
        allow_compose: bool = False,
        expected_key: str = "",
    ) -> bool:
        from app.states.auth_state import AuthState

        auth = await self.get_state(AuthState)
        sid = auth.subscriber_id
        target = f"{kind}:{ref}"
        if not auth.is_signed_in or not sid.isdigit():
            raise ValueError("Your session expired — please sign in again.")
        if expected_key and expected_key != target:
            raise ValueError(
                "Conversation changed. Open the conversation and send again."
            )
        current = await self._target()
        if (
            self.pending
            and (self.scope != target or self.account != sid)
            and not allow_compose
        ):
            raise ValueError(
                "These photos belong to another conversation. Attach them again."
            )
        if not allow_compose and current != (sid, target):
            raise ValueError(
                "Conversation changed. Open the conversation and send again."
            )
        photos = (
            list(self.pending)
            if not allow_compose
            and self.scope == target
            and self.account == sid
            else []
        )
        if self.busy:
            raise ValueError("Wait for your photos to finish uploading.")
        if not caption and not photos:
            raise ValueError("Write a few words before sending.")
        if len(caption) > 2000:
            raise ValueError("Keep messages under 2000 characters.")
        for photo in photos:
            if (
                not safe_photo_name(photo)
                or not (rx.get_upload_dir() / photo).is_file()
            ):
                raise ValueError(
                    "A staged photo is missing. Remove it and attach again."
                )
        body = encode_message(caption, photos)
        preview = message_preview(body)[:255]
        table, parent, foreign, first, second, notification = self._source(kind)
        accepted = "AND p.status = 'accepted'" if kind == "contact" else ""
        async with rx.asession() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT p.{first}, p.{second}, {("p.post_id" if kind == "job" else "p.id")}
                FROM {parent} p JOIN skillkind_subscriber s ON s.id = :sid AND s.is_active
                WHERE p.id = :ref AND :sid IN (p.{first}, p.{second}) {accepted}
                  AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
                    WHERE (b.blocker_id = p.{first} AND b.blocked_id = p.{second})
                       OR (b.blocker_id = p.{second} AND b.blocked_id = p.{first}))
                FOR UPDATE OF p
            """),
                    {"ref": ref, "sid": int(sid)},
                )
            ).first()
            if row is None:
                raise ValueError("That conversation isn't available to you.")
            if not allow_compose and await self._target() != (sid, target):
                raise ValueError(
                    "Conversation changed. Send again from the correct thread."
                )
            other = int(row[1]) if int(row[0]) == int(sid) else int(row[0])
            recipient_column = "" if kind == "job" else ", recipient_id"
            recipient_value = "" if kind == "job" else ", :other"
            inserted = await session.execute(
                text(f"""
                INSERT INTO {table} ({foreign}, sender_id, body{recipient_column})
                SELECT p.id, :sid, :body{recipient_value} FROM {parent} p
                WHERE p.id = :ref AND :sid IN (p.{first}, p.{second}) {accepted}
                  AND NOT EXISTS (SELECT 1 FROM skillkind_member_block b
                    WHERE (b.blocker_id = p.{first} AND b.blocked_id = p.{second})
                       OR (b.blocker_id = p.{second} AND b.blocked_id = p.{first}))
                RETURNING id
            """),
                {"ref": ref, "sid": int(sid), "other": other, "body": body},
            )
            if inserted.first() is None:
                raise ValueError("That conversation isn't available to you.")
            updates = (
                "is_archived = FALSE"
                if kind == "job"
                else "message_count = COALESCE(message_count, 0) + 1, last_message_preview = :preview, last_message_sender_id = :sid, updated_at = now()"
            )
            if kind == "noncontact":
                updates = f"{updates}, status = CASE WHEN initiator_id = :sid THEN status ELSE 'replied' END"
            await session.execute(
                text(
                    f"UPDATE {parent} SET last_message_at = now(), {updates} WHERE id = :ref"
                ),
                {"ref": ref, "sid": int(sid), "preview": preview},
            )
            await session.execute(
                text(f"""
                INSERT INTO skillkind_member_notification
                    (recipient_id, actor_id, kind, title, body, {notification}, target_route)
                VALUES (:other, :sid, 'inbox_message', 'New message in your Inbox', :preview, :source, 'inbox')
            """),
                {
                    "other": other,
                    "sid": int(sid),
                    "preview": preview,
                    "source": int(row[2]),
                },
            )
            await session.commit()
        self.pending = [p for p in self.pending if p not in photos]
        self.generation += 1
        self.error = ""
        return True
