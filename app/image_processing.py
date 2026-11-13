"""Server-side profile photo normalisation.

Uploaded avatars are auto-oriented from EXIF, centre-cropped to a square,
resized down and re-encoded to WebP until the result is comfortably under 1 MB.
"""

import reflex as rx
import logging
import warnings
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageOps

AVATAR_MAX_BYTES = 1_000_000
AVATAR_SIZES: tuple[int, ...] = (640, 512, 384, 256, 192)
AVATAR_QUALITIES: tuple[int, ...] = (88, 80, 72, 62, 50, 40)
AVATAR_SUFFIX = ".webp"
ALLOWED_IMAGE_SUFFIXES: set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# Help-post photos keep their aspect ratio; only the long edge is bounded.
PHOTO_MAX_BYTES = 1_000_000
PHOTO_MAX_EDGES: tuple[int, ...] = (2048, 1600, 1280, 1024, 800, 640)
PHOTO_QUALITIES: tuple[int, ...] = (86, 78, 70, 60, 50, 40, 30)
PHOTO_SUFFIX = ".webp"


SOURCE_MAX_BYTES = 3_000_000
MAX_IMAGE_PIXELS = 20_000_000
_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
_MIMES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


async def read_image_upload(upload: rx.UploadFile) -> bytes:
    if (getattr(upload, "size", 0) or 0) > SOURCE_MAX_BYTES:
        raise ValueError("Source photo exceeds 3 MB")
    data = await upload.read(SOURCE_MAX_BYTES + 1)
    if len(data) > SOURCE_MAX_BYTES:
        raise ValueError("Source photo exceeds 3 MB")
    return data


def _validated_image(
    data: bytes, filename: str, content_type: str
) -> "Image.Image":
    if not data or len(data) > SOURCE_MAX_BYTES:
        raise ValueError("Source photo must be at most 3 MB")
    expected = _FORMATS.get(Path(filename).suffix.lower()) if filename else None
    if filename and expected is None:
        raise ValueError("Only JPEG, PNG and WebP are allowed")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(BytesIO(data)) as opened:
            detected = opened.format
            if detected not in _MIMES or (expected and detected != expected):
                raise ValueError("Image format does not match its extension")
            if content_type and content_type.lower() != _MIMES[detected]:
                raise ValueError("Image MIME does not match its contents")
            if opened.width * opened.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large")
            if (
                getattr(opened, "is_animated", False)
                or getattr(opened, "n_frames", 1) != 1
            ):
                raise ValueError("Animated images are not allowed")
            opened.verify()
        with Image.open(BytesIO(data)) as opened:
            opened.load()
            base = _flatten(opened)
            base.info.clear()
            return base


def _flatten(image) -> "Image.Image":
    oriented = ImageOps.exif_transpose(image)
    if oriented.mode in ("RGBA", "LA", "P"):
        oriented = oriented.convert("RGBA")
        flattened = Image.new("RGB", oriented.size, (255, 250, 240))
        flattened.paste(oriented, mask=oriented.split()[-1])
        return flattened
    return oriented.convert("RGB")


def process_help_photo_bytes(
    data: bytes, filename: str = "", content_type: str = ""
) -> bytes | None:
    """Auto-orient, downscale (aspect preserved) and re-encode to WebP <= 1 MB.

    Returns None when the bytes are unreadable/not an image, or when no
    acceptable size/quality combination could be produced.
    """
    try:
        base = _validated_image(data, filename, content_type)
        for max_edge in PHOTO_MAX_EDGES:
            resized = base.copy()
            resized.thumbnail((max_edge, max_edge), resample=Image.LANCZOS)
            for quality in PHOTO_QUALITIES:
                buffer = BytesIO()
                resized.save(buffer, format="WEBP", quality=quality, method=5)
                payload = buffer.getvalue()
                if len(payload) < PHOTO_MAX_BYTES:
                    return payload
    except Exception as e:
        logging.exception(f"Error: {e}")
        return None
    return None


def process_avatar_bytes(
    data: bytes, filename: str = "", content_type: str = ""
) -> bytes | None:
    """Return web-friendly square WebP bytes under 1 MB, or None on failure."""
    try:
        with _validated_image(data, filename, content_type) as base:
            for size in AVATAR_SIZES:
                square = ImageOps.fit(
                    base,
                    (size, size),
                    method=Image.LANCZOS,
                    centering=(0.5, 0.5),
                )
                for quality in AVATAR_QUALITIES:
                    buffer = BytesIO()
                    square.save(
                        buffer, format="WEBP", quality=quality, method=5
                    )
                    payload = buffer.getvalue()
                    if len(payload) < AVATAR_MAX_BYTES:
                        return payload
    except Exception as e:
        logging.exception(f"Error: {e}")
        return None
    return None
