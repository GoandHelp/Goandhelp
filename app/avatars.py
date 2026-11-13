import reflex as rx

ANIMAL_AVATARS: tuple[str, ...] = (
    "/face_apricot_1.png",
    "/face_sage_1.png",
    "/face_1_single.png",
    "/face_cream_1.png",
)


def animal_avatar(seed: str | rx.Var[str]) -> str | rx.Var[str]:
    """Stable local fox, owl, cat or dog; never include a seed in a URL."""
    if isinstance(seed, rx.Var):
        return rx.Var(
            _js_expr=f"{list(ANIMAL_AVATARS)!r}[Array.from(String({str(seed)} ?? '').includes('@') ? 'member' : String({str(seed)} ?? '')).reduce((n, c) => (n + c.codePointAt(0)) % 4, 0)]",
            _var_type=str,
            _var_data=seed._get_all_var_data(),
        ).to(str)
    safe_seed = "member" if "@" in seed else seed
    return ANIMAL_AVATARS[sum(ord(char) for char in safe_seed) % 4]


def member_avatar(
    path: str | rx.Var[str], seed: str | rx.Var[str]
) -> str | rx.Var[str]:
    if isinstance(path, rx.Var):
        return rx.cond(path, rx.get_upload_url(path), animal_avatar(seed))
    if path:
        return f"/_upload/{path}"
    return animal_avatar(seed)
