"""Versioned message body codec; no filesystem or framework dependencies."""

import json
import re
from typing import TypedDict

import logging

PREFIX = "\u001eGOANDHELP:MESSAGE-PHOTOS:v1\n"
BASENAME = re.compile(r"message_[0-9a-f]{32}\.webp\Z")


class MessageContent(TypedDict):
    body: str
    photos: list[str]


def safe_photo_name(name: object) -> bool:
    return isinstance(name, str) and BASENAME.fullmatch(name) is not None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate message key")
        result[key] = value
    return result


def encode_message(text: str, photos: list[str]) -> str:
    if not isinstance(text, str):
        raise ValueError("Message text must be a string")
    if not photos:
        return text
    if (
        not isinstance(photos, list)
        or not 1 <= len(photos) <= 5
        or not all(safe_photo_name(p) for p in photos)
        or len(set(photos)) != len(photos)
    ):
        raise ValueError("Invalid message photos")
    return f"{PREFIX}{json.dumps({'text': text, 'photos': photos}, ensure_ascii=False, separators=(',', ':'))}"


def decode_message(raw: str | None) -> MessageContent:
    body = raw or ""
    if not body.startswith(PREFIX):
        return {"body": body, "photos": []}
    fallback: MessageContent = {"body": "Message unavailable", "photos": []}
    try:
        value = json.loads(
            body[len(PREFIX) :], object_pairs_hook=_unique_object
        )
        if (
            not isinstance(value, dict)
            or set(value) != {"text", "photos"}
            or not isinstance(value["text"], str)
        ):
            return fallback
        photos = value["photos"]
        if (
            not isinstance(photos, list)
            or not 1 <= len(photos) <= 5
            or not all(safe_photo_name(p) for p in photos)
            or len(set(photos)) != len(photos)
        ):
            return fallback
        return {"body": value["text"], "photos": photos}
    except (ValueError, TypeError, RecursionError):
        logging.exception("Unexpected error")
        return fallback


def message_preview(raw: str | None) -> str:
    content = decode_message(raw)
    count = len(content["photos"])
    if not count:
        return (
            "Message unavailable"
            if (raw or "").startswith(PREFIX)
            else content["body"]
        )
    indicator = "Photo" if count == 1 else f"{count} photos"
    caption = content["body"].strip()
    return f"{caption} · {indicator}" if caption else indicator


def last_message_photo(raw: str | None) -> str:
    photos = decode_message(raw)["photos"]
    return photos[-1] if photos else ""
