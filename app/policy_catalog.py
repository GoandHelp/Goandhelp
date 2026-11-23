"""Policy source inventory and validated offline catalogs.

Only authored document fields and reader chrome are eligible for this catalog.
The inventory is complete; translation coverage is intentionally reported
separately and must not be inferred from the number of registered locales.
"""

from collections import Counter
from string import Formatter

from app.policies import POLICY_DOCUMENTS
from app.policy_catalog_agreement_french import AGREEMENT_FRENCH_ROWS
from app.policy_catalog_agreement_german import AGREEMENT_GERMAN_ROWS
from app.policy_catalog_agreement_russian_urdu import (
    AGREEMENT_RUSSIAN_URDU_ROWS,
)
from app.policy_catalog_chrome import POLICY_CHROME_KEYS, POLICY_CHROME_ROWS
from app.policy_catalog_credits_asian import CREDITS_ASIAN_ROWS
from app.policy_catalog_credits_european import CREDITS_EUROPEAN_ROWS
from app.policy_catalog_credits_global import CREDITS_GLOBAL_ROWS
from app.policy_catalog_privacy import PRIVACY_ROWS
from app.policy_catalog_howto_french import HOWTO_FRENCH_ROWS
from app.policy_catalog_howto_german import HOWTO_GERMAN_ROWS
from app.policy_catalog_privacy_german import PRIVACY_GERMAN_ROWS
from app.policy_catalog_howto_russian_urdu import HOWTO_RUSSIAN_URDU_ROWS
from app.policy_catalog_howto_spanish import HOWTO_SPANISH_ROWS
from app.policy_catalog_privacy_spanish import PRIVACY_SPANISH_ROWS
from app.policy_catalog_agreement_spanish import AGREEMENT_SPANISH_ROWS

POLICY_DOCUMENT_KEYS: tuple[str, ...] = (
    "howto",
    "privacy",
    "agreement",
    "credits",
)
POLICY_LOCALES: frozenset[str] = frozenset(
    {
        "am",
        "ar",
        "bn",
        "my",
        "zh",
        "cs",
        "da",
        "nl",
        "fi",
        "fr",
        "de",
        "el",
        "gu",
        "he",
        "hi",
        "hu",
        "id",
        "it",
        "ja",
        "kn",
        "ko",
        "ml",
        "mr",
        "ne",
        "fa",
        "pl",
        "pt",
        "ro",
        "es",
        "sw",
        "sv",
        "ta",
        "te",
        "th",
        "tr",
        "vi",
        "ru",
        "ur",
    }
)


def document_sources(key: str) -> tuple[str, ...]:
    document = POLICY_DOCUMENTS[key]
    texts = [
        document[field] for field in ("title", "subtitle", "updated", "notice")
    ]
    for section in document["sections"]:
        texts.append(section["heading"])
        texts.extend(section["paragraphs"])
    return tuple(texts)


DOCUMENT_SOURCE_KEYS: dict[str, tuple[str, ...]] = {
    key: document_sources(key) for key in POLICY_DOCUMENT_KEYS
}
SOURCE_KEYS: tuple[str, ...] = tuple(
    dict.fromkeys(
        text
        for key in POLICY_DOCUMENT_KEYS
        for text in DOCUMENT_SOURCE_KEYS[key]
    )
)
SOURCE_COINCIDENCES: frozenset[tuple[str, str]] = frozenset({("nl", "Credits")})
CREDITS_ROWS: dict[str, tuple[str, ...]] = {}
for _part in (CREDITS_EUROPEAN_ROWS, CREDITS_ASIAN_ROWS, CREDITS_GLOBAL_ROWS):
    if set(CREDITS_ROWS) & set(_part):
        raise ValueError("Credits locale groups overlap")
    CREDITS_ROWS.update(_part)
if set(CREDITS_ROWS) != POLICY_LOCALES:
    raise ValueError("Credits must cover every non-English Settings locale")
if len(SOURCE_KEYS) != 182:
    raise ValueError("The canonical policy source inventory changed")


def placeholders(text: str) -> Counter[str]:
    return Counter(name for _, name, _, _ in Formatter().parse(text) if name)


def validate_rows(
    keys: tuple[str, ...], rows: dict[str, tuple[str, ...]]
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for locale, row in rows.items():
        if locale not in POLICY_LOCALES or len(row) != len(keys):
            raise ValueError(f"Invalid policy row length or locale: {locale}")
        entries: dict[str, str] = {}
        for source, value in zip(keys, row, strict=True):
            if not value.strip() or placeholders(source) != placeholders(value):
                raise ValueError(
                    f"Empty policy translation or invalid slots: {locale}"
                )
            if source == value and (locale, source) not in SOURCE_COINCIDENCES:
                raise ValueError(
                    f"English policy fallback is not a translation: {locale}"
                )
            for name in (
                "Go and Help",
                "OpenFreeMap",
                "OpenStreetMap",
                "MapLibre",
                "Planetiler",
                "OpenMapTiles",
                "Open Database License",
                "ODbL",
                "©",
            ):
                if name in source and name not in value:
                    raise ValueError(
                        f"Policy attribution missing {name}: {locale}"
                    )
            entries[source] = value
        result[locale] = entries
    return result


POLICY_CATALOGS: dict[str, dict[str, str]] = validate_rows(
    DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS
)
for _keys, _rows in (
    (DOCUMENT_SOURCE_KEYS["privacy"], PRIVACY_ROWS),
    (DOCUMENT_SOURCE_KEYS["agreement"], AGREEMENT_GERMAN_ROWS),
    (DOCUMENT_SOURCE_KEYS["agreement"], AGREEMENT_FRENCH_ROWS),
    (DOCUMENT_SOURCE_KEYS["howto"], HOWTO_FRENCH_ROWS),
    (DOCUMENT_SOURCE_KEYS["howto"], HOWTO_GERMAN_ROWS),
    (DOCUMENT_SOURCE_KEYS["privacy"], PRIVACY_GERMAN_ROWS),
    (DOCUMENT_SOURCE_KEYS["howto"], HOWTO_RUSSIAN_URDU_ROWS),
    (DOCUMENT_SOURCE_KEYS["agreement"], AGREEMENT_RUSSIAN_URDU_ROWS),
    (DOCUMENT_SOURCE_KEYS["howto"], HOWTO_SPANISH_ROWS),
    (DOCUMENT_SOURCE_KEYS["privacy"], PRIVACY_SPANISH_ROWS),
    (DOCUMENT_SOURCE_KEYS["agreement"], AGREEMENT_SPANISH_ROWS),
    (POLICY_CHROME_KEYS, POLICY_CHROME_ROWS),
):
    for _locale, _entries in validate_rows(_keys, _rows).items():
        for _source, _value in _entries.items():
            POLICY_CATALOGS[_locale].setdefault(_source, _value)

POLICY_TRANSLATED_KEYS: tuple[str, ...] = tuple(
    dict.fromkeys(
        source for entries in POLICY_CATALOGS.values() for source in entries
    )
)


def missing_policy_sources(
    entries: dict[str, str], locale: str
) -> tuple[str, ...]:
    """Audit actual effective entries; neither missing nor English counts as covered."""
    return tuple(
        source
        for source in SOURCE_KEYS
        if not entries.get(source, "").strip()
        or (
            entries[source] == source
            and (locale, source) not in SOURCE_COINCIDENCES
        )
    )
