"""Help-search category vocabulary used by the member Help Filters sheet.

The stored `skillkind_help_post.category` / `category_tags` and
`skillkind_profile.preferred_categories` values are left exactly as they are: no
schema or data migration is needed. Each filter choice simply expands to every
stored token it should match, so legacy rows keep appearing under the correct
modern label.
"""

import reflex as rx

from typing import TypedDict

from app.models import CATEGORY_ICONS, CATEGORY_LABELS, TASK_CATEGORIES
from app.skill_categories import category_color, category_ink


class FilterCategory(TypedDict):
    value: str
    label: str
    icon: str
    color: str
    ink: str


# Events is a discovery filter only; the remaining options stay the canonical
# task taxonomy, alphabetized with Other last.
FILTER_CATEGORIES: list[FilterCategory] = [
    {
        "value": "events",
        "label": "Events",
        "icon": "calendar-days",
        "color": "#c2410c",
        "ink": "#ffffff",
    },
    *[
        {
            "value": value,
            "label": CATEGORY_LABELS[value],
            "icon": CATEGORY_ICONS[value],
            "color": category_color(value),
            "ink": category_ink(value),
        }
        for value in sorted(
            TASK_CATEGORIES,
            key=lambda value: (
                value == "other",
                CATEGORY_LABELS[value].casefold(),
            ),
        )
    ],
]

FILTER_CATEGORY_LABELS: dict[str, str] = {
    item["value"]: item["label"] for item in FILTER_CATEGORIES
}

FILTER_CATEGORY_VALUES: list[str] = [
    item["value"] for item in FILTER_CATEGORIES
]

# Filter choice -> every stored category token that should match it. Legacy
# tokens (artist, builder, craftworker, health_worker, labourer,
# nanny, babysitter, teacher, services, coach, fitness) are preserved here so
# old records still filter sensibly.
_EXTRA_TOKENS: dict[str, list[str]] = {
    "translator": ["translation"],
    "first_aid": ["first-aid", "first aid"],
    "arts": ["artist"],
    "carer": ["babysitter", "nanny"],
    "construction": ["builder"],
    "craftwork": ["craftworker"],
    "healthcare": ["health_worker"],
    "labour": ["labourer"],
    "sports": ["coach", "fitness"],
    "teaching": ["teacher"],
    "other": ["services"],
}

CATEGORY_ALIASES: dict[str, list[str]] = {
    value: [value, *_EXTRA_TOKENS.get(value, [])] for value in TASK_CATEGORIES
}


def expand_category_tokens(values: list[str]) -> list[str]:
    """Every stored category token covered by the chosen filter values."""
    tokens: list[str] = []
    for value in values:
        for token in CATEGORY_ALIASES.get(value, []):
            if token not in tokens:
                tokens.append(token)
    return tokens


def category_label(value: str) -> str:
    return FILTER_CATEGORY_LABELS.get(
        value, value.replace("_", " ").title() or "Other"
    )
