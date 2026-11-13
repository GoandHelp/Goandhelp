"""Shared skills-and-knowledge category vocabulary.

One source of truth for:

* the accessible circular map-glyph colour of every current TASK_CATEGORIES key
  (glyph ink is chosen for legibility against each fill);
* normalising / de-duplicating the multi-select values stored in
  `Profile.preferred_categories` and `HelpPost.category_tags`;
* reading a help post's categories back out, falling back to the legacy single
  `HelpPost.category` column for rows written before `category_tags` existed;
* the per-tier help-request category allowance (1 free, 3 premium).

No schema changes and no data migration: legacy stored tokens are resolved to
their current key on read through `LEGACY_CATEGORY_ALIASES`.
"""

import reflex as rx

from app.models import (
    CATEGORY_ICONS,
    CATEGORY_LABELS,
    CATEGORY_OTHER,
    LEGACY_CATEGORY_ALIASES,
    TASK_CATEGORIES,
)

# A free member may tag a help request with exactly one category; a premium
# member with up to three. MAX_REQUEST_CATEGORIES is the absolute storage ceiling
# so normalisation never silently truncates a premium selection.
FREE_REQUEST_CATEGORIES = 1
PREMIUM_REQUEST_CATEGORIES = 3
MAX_REQUEST_CATEGORIES = PREMIUM_REQUEST_CATEGORIES

# Exact paywall copy shown when a free member reaches for a second category.
CATEGORY_UPGRADE_REASON = "Select multiple categories and increase your exposure by becoming a Premium Member"


def request_category_limit(is_premium: bool) -> int:
    """How many categories one help request may carry: 1 free, 3 premium."""
    return PREMIUM_REQUEST_CATEGORIES if is_premium else FREE_REQUEST_CATEGORIES


def category_limit_message(limit: int) -> str:
    return (
        f"A help request can have up to {limit} categories. Remove one first."
    )


# Category identity only: global controls retain the orange theme.
CATEGORY_COLORS: dict[str, str] = {
    "translator": "#7c3aed",
    "first_aid": "#dc2626",
    "arts": "#166534",
    "agriculture": "#668944",
    "carer": "#0e8176",
    "construction": "#c2410c",
    "cook": "#a87c00",
    "cleaner": "#2563eb",
    "craftwork": "#a16207",
    "healthcare": "#0891b2",
    "labour": "#be123c",
    "legal": "#312e81",
    "mechanic": "#334155",
    "media": "#d946ef",
    "music": "#0f766e",
    "sales": "#be3455",
    "spirituality": "#7960b5",
    "sports": "#4d7c0f",
    "teaching": "#a44f2c",
    "technician": "#075985",
    "tourism": "#11778b",
    "workshop": "#854d6b",
    CATEGORY_OTHER: "#64748b",
}

CATEGORY_GRADIENT = (
    "linear-gradient(180deg, "
    "color-mix(in srgb, var(--category-fill) 92%, white) 0%, "
    "var(--category-fill) 52%, "
    "color-mix(in srgb, var(--category-fill) 88%, black) 100%)"
)

# Short, plain-English guidance shown on each Ask for Help category card.
CATEGORY_BLURBS: dict[str, str] = {
    "translator": "Help with conversations, documents and understanding another language.",
    "first_aid": "Basic first-aid knowledge and support. For emergencies, call local emergency services.",
    "arts": "Drawing, painting, visual arts, performance and creative projects.",
    "agriculture": "Farms, gardens, harvests, animals and land work.",
    "carer": "Childcare, companionship and everyday support for someone.",
    "construction": "Building, painting, tiling and site help on the job.",
    "cook": "Cooking, baking, prep and serving food together.",
    "cleaner": "Cleaning, tidying, laundry and getting a place spotless.",
    "craftwork": "Repairs, woodwork, sewing, fixing and making by hand.",
    "healthcare": "Clinic visits, pharmacy runs, care and company.",
    "labour": "Lifting, moving, loading, clearing and general graft.",
    "legal": "Paperwork, forms, contracts and understanding the rules.",
    "mechanic": "Vehicle and bicycle maintenance, diagnostics and mechanical repairs.",
    "music": "Singing, instruments, practice, composing and making music together.",
    "media": "Photos, video, writing, social posts and translation.",
    "sales": "Markets, stalls, shops, customers and selling a thing.",
    "spirituality": "Ceremony, meditation, reflection and quiet company.",
    "sports": "Training, coaching, fitness, games and being active.",
    "teaching": "Language practice, tutoring, showing someone a craft.",
    "technician": "Computers, phones, wiring, networks and electronics.",
    "tourism": "Guiding, hosting, tours and showing people around.",
    "workshop": "Workshop tools, equipment and practical making projects.",
    CATEGORY_OTHER: "A practical request that does not fit another category.",
}


def canonical_category(value: str) -> str:
    """The current key for one raw stored token, or `""` when unknown."""
    key = str(value or "").strip().lower().replace(" ", "_")
    key = LEGACY_CATEGORY_ALIASES.get(key, key)
    return key if key in TASK_CATEGORIES else ""


def category_color(value: str) -> str:
    """Marker / chip fill for one category key (legacy tokens included)."""
    key = canonical_category(value) or CATEGORY_OTHER
    return CATEGORY_COLORS.get(key, CATEGORY_COLORS[CATEGORY_OTHER])


def category_ink(value: str) -> str:
    """The shared category glyph ink, including for legacy aliases."""
    return "#ffffff"


def category_icon_name(value: str) -> str:
    """Lucide icon name for one category key (legacy tokens included)."""
    key = canonical_category(value) or CATEGORY_OTHER
    return CATEGORY_ICONS.get(key, CATEGORY_ICONS[CATEGORY_OTHER])


def category_label(value: str) -> str:
    key = canonical_category(value)
    if key:
        return CATEGORY_LABELS[key]
    return str(value or "").replace("_", " ").strip().title() or "Other"


def category_blurb(value: str) -> str:
    key = canonical_category(value) or CATEGORY_OTHER
    return CATEGORY_BLURBS.get(key, CATEGORY_BLURBS[CATEGORY_OTHER])


def normalize_categories(
    values: list[str], limit: int | None = None
) -> list[str]:
    """Keep only real category keys, de-duplicated, in the order chosen."""
    cleaned: list[str] = []
    for raw in values:
        key = canonical_category(raw)
        if key and key not in cleaned:
            cleaned.append(key)
    if limit is not None:
        return cleaned[:limit]
    return cleaned


def split_categories(raw: str) -> list[str]:
    """Normalized keys held in a stored comma separated column."""
    return normalize_categories(str(raw or "").split(","))


def join_categories(values: list[str], limit: int | None = None) -> str:
    """Storage form for `preferred_categories` / `category_tags`."""
    return ",".join(normalize_categories(values, limit))


def post_categories(category_tags: str, legacy_category: str) -> list[str]:
    """Every category a help post belongs to.

    Rows written before `category_tags` existed keep an empty tag column, so
    the legacy single `category` value is used instead.
    """
    tags = split_categories(category_tags)
    if tags:
        return tags
    return normalize_categories([legacy_category]) or [CATEGORY_OTHER]


def primary_category(values: list[str]) -> str:
    """The first chosen category, used for the map glyph and legacy column."""
    cleaned = normalize_categories(values)
    return cleaned[0] if cleaned else CATEGORY_OTHER


def category_labels(values: list[str]) -> list[str]:
    return [category_label(value) for value in normalize_categories(values)]


def categories_overlap(left: list[str], right: list[str]) -> bool:
    """True when a request and a helper share at least one category."""
    return bool(
        set(normalize_categories(left)) & set(normalize_categories(right))
    )


CATEGORY_CHOICES: list[dict[str, str]] = [
    {
        "value": value,
        "label": category_label(value),
        "icon": category_icon_name(value),
        "color": category_color(value),
        "ink": category_ink(value),
        "blurb": category_blurb(value),
    }
    for value in sorted(
        TASK_CATEGORIES,
        key=lambda value: (
            value == CATEGORY_OTHER,
            CATEGORY_LABELS[value].casefold(),
        ),
    )
]
