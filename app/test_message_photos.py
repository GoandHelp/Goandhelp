import reflex as rx

import inspect
import json
import unittest
from io import BytesIO
from uuid import uuid4
from faker import Faker
from PIL import Image
from sqlalchemy import insert, text
from starlette.datastructures import UploadFile, Headers

from app.message_photos import (
    PREFIX,
    decode_message,
    encode_message,
    message_preview,
    last_message_photo,
)
from app.image_processing import read_image_upload, process_help_photo_bytes
from app.components import messages_panel, contacts_panel, noncontact_panel
from app.components.chat_controls import correspondence_bubble
from app.models import (
    Subscriber,
    HelpPost,
    ContactLink,
    MessageThread,
    NonContactConversation,
    Message,
    ContactMessage,
    NonContactMessage,
)
from app.states.message_attachment_state import MessageAttachmentState
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState
from app.states.unified_inbox_state import UnifiedInboxState
from app.states.contacts_state import ContactsState, EMPTY_CONTACT
from app.states.messaging_state import MessagingState, EMPTY_THREAD
from app.states.noncontact_state import (
    NonContactMessagingState,
    EMPTY_CONVERSATION,
)
from app.states.message_deletion_state import MessageDeletionState


def image_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 24), "orange").save(buffer, format="PNG")
    return buffer.getvalue()


class CodecTests(unittest.TestCase):
    def test_plain_roundtrip_is_exact(self):
        for raw in (
            "",
            "  hello\n世界  ",
            '{"text":"legacy"}',
            "Subject: Test\n\nCaption",
        ):
            self.assertEqual(encode_message(raw, []), raw)
            self.assertEqual(decode_message(raw), {"body": raw, "photos": []})
            self.assertEqual(message_preview(raw), raw)

    def test_photo_caption_and_count(self):
        names = [f"message_{uuid4().hex}.webp" for _ in range(5)]
        for count in range(1, 6):
            for caption in ("", "Hello 世界"):
                body = encode_message(caption, names[:count])
                self.assertEqual(
                    decode_message(body),
                    {"body": caption, "photos": names[:count]},
                )
                indicator = "Photo" if count == 1 else f"{count} photos"
                self.assertEqual(
                    message_preview(body),
                    f"{caption} · {indicator}" if caption else indicator,
                )
                self.assertEqual(last_message_photo(body), names[count - 1])

    def test_strict_malformed_fallback(self):
        name = f"message_{uuid4().hex}.webp"
        payloads = [
            "{",
            "[]",
            '{"text":"x","photos":[],"extra":true}',
            '{"text":"x","text":"y","photos":["' + name + '"]}',
        ]
        for photos in (
            [],
            [name] * 6,
            [name, name],
            ["../escape.webp"],
            ["/tmp/image.webp"],
            ["https://example.com/a.webp"],
            [{}],
            [name.upper()],
            [f"{name}\n"],
        ):
            payloads.append(json.dumps({"text": "caption", "photos": photos}))
        payloads.append(json.dumps({"text": 4, "photos": [name]}))
        for payload in payloads:
            raw = f"{PREFIX}{payload}"
            self.assertEqual(
                decode_message(raw),
                {"body": "Message unavailable", "photos": []},
            )
            self.assertEqual(last_message_photo(raw), "")
            self.assertEqual(message_preview(raw), "Message unavailable")
        self.assertEqual(
            decode_message("GOANDHELP:MESSAGE-PHOTOS:v2{}")["photos"], []
        )

    def test_validation_and_rendering(self):
        data = image_bytes()
        result = process_help_photo_bytes(data, "photo.png", "image/png")
        self.assertIsNotNone(result)
        self.assertIsNone(
            process_help_photo_bytes(b"x" * 3_000_001, "large.png", "image/png")
        )
        animated = BytesIO()
        Image.new("RGB", (8, 8), "red").save(
            animated,
            format="PNG",
            save_all=True,
            append_images=[Image.new("RGB", (8, 8), "blue")],
            duration=100,
            loop=0,
        )
        self.assertIsNone(
            process_help_photo_bytes(
                animated.getvalue(), "animated.png", "image/png"
            )
        )
        with Image.open(BytesIO(result)) as normalized:
            self.assertEqual(normalized.format, "WEBP")
            self.assertNotIn("exif", normalized.info)
        for filename, mime, payload in (
            ("a.jpg", "image/jpeg", data),
            ("a.png", "image/jpeg", data),
            ("a.svg", "image/svg+xml", data),
            ("a.png", "image/png", b"not an image"),
        ):
            self.assertIsNone(process_help_photo_bytes(payload, filename, mime))
        message = rx.Var.create(
            {
                "id": 1,
                "mine": True,
                "sent_at": "Now",
                **decode_message(
                    encode_message("Caption", [f"message_{uuid4().hex}.webp"])
                ),
            }
        )
        self.assertTrue(correspondence_bubble(message).render())
        for component in (
            messages_panel.composer,
            contacts_panel.composer,
            noncontact_panel.reply_composer,
        ):
            self.assertTrue(component().render())
            self.assertIn("message_attachments()", inspect.getsource(component))
        for model in (Message, ContactMessage, NonContactMessage):
            self.assertNotIn("photo_paths", model.__table__.columns)


class DatabasePhotoTests(unittest.IsolatedAsyncioTestCase):
    """Real managed database and upload directory; fixtures deleted after each test."""

    async def asyncSetUp(self):
        fake = Faker()
        self.members: list[int] = []
        self.files: list[str] = []
        async with rx.asession() as session:
            for _ in range(2):
                member = (
                    await session.execute(
                        insert(Subscriber.__table__)
                        .values(
                            email=f"photo-test-{uuid4().hex}@example.invalid",
                            display_name=fake.name(),
                            is_active=True,
                            is_verified=True,
                        )
                        .returning(Subscriber.id)
                    )
                ).scalar_one()
                self.members.append(member)
            self.post = (
                await session.execute(
                    insert(HelpPost.__table__)
                    .values(
                        author_id=self.members[0],
                        title="Photo regression fixture",
                    )
                    .returning(HelpPost.id)
                )
            ).scalar_one()
            self.contact = (
                await session.execute(
                    insert(ContactLink.__table__)
                    .values(
                        requester_id=self.members[0],
                        recipient_id=self.members[1],
                        status="accepted",
                    )
                    .returning(ContactLink.id)
                )
            ).scalar_one()
            self.job = (
                await session.execute(
                    insert(MessageThread.__table__)
                    .values(
                        post_id=self.post,
                        poster_id=self.members[0],
                        helper_id=self.members[1],
                        subject="Photo regression fixture",
                    )
                    .returning(MessageThread.id)
                )
            ).scalar_one()
            self.direct = (
                await session.execute(
                    insert(NonContactConversation.__table__)
                    .values(
                        initiator_id=self.members[0],
                        recipient_id=self.members[1],
                    )
                    .returning(NonContactConversation.id)
                )
            ).scalar_one()
            await session.commit()
        self.state = MessageAttachmentState(_reflex_internal_init=True)
        auth = await self.state.get_state(AuthState)
        auth.subscriber_id = str(self.members[0])
        auth.email = "photo-tests@example.invalid"
        (await self.state.get_state(ProfileState)).active_tab = "inbox"

    async def asyncTearDown(self):
        for filename in self.files:
            (rx.get_upload_dir() / filename).unlink(missing_ok=True)
        async with rx.asession() as session:
            await session.execute(
                text(
                    "DELETE FROM skillkind_member_notification WHERE actor_id = ANY(:ids) OR recipient_id = ANY(:ids)"
                ),
                {"ids": self.members},
            )
            await session.execute(
                text("DELETE FROM skillkind_help_post WHERE id = :id"),
                {"id": self.post},
            )
            await session.execute(
                text("DELETE FROM skillkind_subscriber WHERE id = ANY(:ids)"),
                {"ids": self.members},
            )
            await session.commit()

    async def select(self, kind: str, ref: int):
        inbox = await self.state.get_state(UnifiedInboxState)
        await inbox._clear_selections()
        inbox.view = "thread"
        inbox.selected_key = f"{kind}:{ref}"
        (await self.state.get_state(ContactsState)).selected_contact = (
            {
                **EMPTY_CONTACT,
                "link_id": self.contact,
                "other_id": self.members[1],
                "status": "accepted",
            }
            if kind == "contact"
            else dict(EMPTY_CONTACT)
        )
        (await self.state.get_state(MessagingState)).selected_thread = (
            {
                **EMPTY_THREAD,
                "id": self.job,
                "other_id": self.members[1],
                "post_id": self.post,
            }
            if kind == "job"
            else dict(EMPTY_THREAD)
        )
        (await self.state.get_state(NonContactMessagingState)).selected = (
            {
                **EMPTY_CONVERSATION,
                "conv_id": self.direct,
                "other_id": self.members[1],
            }
            if kind == "noncontact"
            else dict(EMPTY_CONVERSATION)
        )

    async def upload(self):
        upload = UploadFile(
            BytesIO(image_bytes()),
            filename="fixture.png",
            headers=Headers({"content-type": "image/png"}),
        )
        upload.name = "fixture.png"
        await MessageAttachmentState.upload_photos.fn(self.state, [upload])
        self.assertEqual(self.state.error, "")
        filename = self.state.pending[-1]
        self.files.append(filename)
        self.assertTrue((rx.get_upload_dir() / filename).is_file())
        return filename

    async def test_actual_three_kind_send_read_delete(self):
        for kind, ref in (
            ("contact", self.contact),
            ("job", self.job),
            ("noncontact", self.direct),
        ):
            await self.select(kind, ref)
            filename = await self.upload()
            self.assertTrue(await self.state._persist(kind, ref, "Caption"))
            self.assertEqual(self.state.pending, [])
            table, parent, foreign, _, _, notification = self.state._source(
                kind
            )
            async with rx.asession() as session:
                row = (
                    await session.execute(
                        text(
                            f"SELECT id, body FROM {table} WHERE {foreign} = :ref ORDER BY id DESC LIMIT 1"
                        ),
                        {"ref": ref},
                    )
                ).one()
                notice = (
                    await session.execute(
                        text(
                            f"SELECT body FROM skillkind_member_notification WHERE {notification} = :ref AND actor_id = :sid ORDER BY id DESC LIMIT 1"
                        ),
                        {
                            "ref": self.post if kind == "job" else ref,
                            "sid": self.members[0],
                        },
                    )
                ).scalar_one()
                self.assertEqual(
                    decode_message(row[1]),
                    {"body": "Caption", "photos": [filename]},
                )
                self.assertEqual(notice, "Caption · Photo")
                if kind != "job":
                    preview = (
                        await session.execute(
                            text(
                                f"SELECT last_message_preview FROM {parent} WHERE id = :ref"
                            ),
                            {"ref": ref},
                        )
                    ).scalar_one()
                    self.assertEqual(preview, "Caption · Photo")
            deletion = await self.state.get_state(MessageDeletionState)
            async for _ in MessageDeletionState.delete_message.fn(
                deletion, kind, row[0], False
            ):
                pass
            self.assertEqual(deletion.error, "")
            self.assertFalse((rx.get_upload_dir() / filename).exists())

    async def test_merged_mapping_and_photo_only_messages(self):
        stored: list[str] = []
        for kind, ref in (
            ("contact", self.contact),
            ("job", self.job),
            ("noncontact", self.direct),
        ):
            await self.select(kind, ref)
            filename = await self.upload()
            stored.append(filename)
            self.assertTrue(await self.state._persist(kind, ref, ""))
        await self.select("contact", self.contact)
        contacts = await self.state.get_state(ContactsState)
        async for _ in ContactsState.load_contact_messages.fn(contacts):
            pass
        self.assertEqual(
            {m["source_kind"] for m in contacts.contact_messages},
            {"contact", "noncontact"},
        )
        self.assertTrue(
            all(
                m["body"] == "" and len(m["photos"]) == 1
                for m in contacts.contact_messages
            )
        )
        async with rx.asession() as session:
            await session.execute(
                text(
                    "INSERT INTO skillkind_message (thread_id, sender_id, body) VALUES (:ref, :sid, :body)"
                ),
                {
                    "ref": self.job,
                    "sid": self.members[1],
                    "body": encode_message("Reply", [stored[1]]),
                },
            )
            await session.commit()
        async for _ in ContactsState.load_contact_messages.fn(contacts):
            pass
        self.assertEqual(
            {m["source_kind"] for m in contacts.contact_messages},
            {"contact", "job", "noncontact"},
        )
        job_message = next(
            m for m in contacts.contact_messages if m["source_kind"] == "job"
        )
        self.assertEqual(
            (job_message["body"], job_message["photos"]), ("Reply", [stored[1]])
        )
        await self.select("job", self.job)
        jobs = await self.state.get_state(MessagingState)
        self.assertEqual(
            await jobs._load_conversation_data(
                str(self.members[0]), jobs.selected_thread
            ),
            "ok",
        )
        self.assertEqual(jobs.messages[0]["photos"], [stored[1]])
        await self.select("noncontact", self.direct)
        direct = await self.state.get_state(NonContactMessagingState)
        async for _ in NonContactMessagingState.load_messages.fn(direct):
            pass
        self.assertEqual(direct.messages[0]["photos"], [stored[2]])

    async def test_navigation_remove_failure_and_source_limit(self):
        await self.select("contact", self.contact)
        filename = await self.upload()
        await MessageAttachmentState.remove_photo.fn(self.state, filename)
        self.assertFalse((rx.get_upload_dir() / filename).exists())
        filename = await self.upload()
        with self.assertRaises(ValueError):
            await self.state._persist("job", self.job, "Wrong target")
        self.assertEqual(self.state.pending, [filename])
        inbox = await self.state.get_state(UnifiedInboxState)
        await UnifiedInboxState.back_to_inbox.fn(inbox)
        self.assertEqual(self.state.pending, [])
        self.assertFalse((rx.get_upload_dir() / filename).exists())
        upload = UploadFile(BytesIO(b"x" * 3_000_001), filename="too-big.png")
        with self.assertRaises(ValueError):
            await read_image_upload(upload)


if __name__ == "__main__":
    unittest.main()
