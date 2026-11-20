import reflex as rx

from urllib.parse import quote

USER_AVATAR_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
    '<rect width="64" height="64" fill="#fff7e8"/>'
    '<circle cx="32" cy="21" r="11" fill="#404040"/>'
    '<path d="M10 56 A22 22 0 0 1 54 56 Z" fill="#404040"/>'
    "</svg>"
)
USER_AVATAR = f"data:image/svg+xml,{quote(USER_AVATAR_SVG, safe='')}"
ANIMAL_AVATARS: tuple[str, ...] = (USER_AVATAR,)


def animal_avatar(seed: str | rx.Var[str]) -> str | rx.Var[str]:
    """Compatibility fallback: one standard user silhouette, independent of seed."""
    if isinstance(seed, rx.Var):
        return rx.Var.create(USER_AVATAR)
    return USER_AVATAR


def member_avatar(
    path: str | rx.Var[str], seed: str | rx.Var[str]
) -> str | rx.Var[str]:
    if isinstance(path, rx.Var):
        return rx.cond(path, rx.get_upload_url(path), animal_avatar(seed))
    if path:
        return f"/_upload/{path}"
    return animal_avatar(seed)
