import reflex as rx

from collections import Counter
from string import Formatter

from app.interface_catalog_profile_forms_a import PROFILE_FORM_ROWS_A
from app.interface_catalog_profile_forms_b import PROFILE_FORM_ROWS_B
from app.interface_catalog_profile_forms_c import PROFILE_FORM_ROWS_C
from app.interface_catalog_profile_forms_subtitle import (
    PROFILE_FORM_SUBTITLE_ROWS,
)
from app.models import LANGUAGE_OPTIONS

PROFILE_FORM_BASE_KEYS: tuple[str, ...] = (
    "Public handle",
    "unique, lowercase",
    "account country",
    "Biography",
    "why you help, why you need help",
    "I.e. I'm a Photographer travelling Asia, happy to help others in exchange for a accommodation...",
    "comma separated",
    "English, Portuguese, Spanish",
    "Handle",
    "Phone",
    "Email",
    "Bio",
    "Languages",
    "Password",
    "Select what you can help with",
    "Other Skills",
    "Anything the categories miss",
    "Plumber, Electrician, Hairdresser, Dentist, Tailor...",
    "Save skills and knowledge",
    "Choose the categories you can help with, and add anything else you know.",
    "No categories yet",
    "{count} other skills listed",
    "1 other skill listed",
    "Choose at least one category, or describe your other skills and knowledge.",
    "Skills and knowledge saved.",
    "Handles are 3–30 characters, lowercase letters, numbers, dots or underscores.",
    "That biography is a little long — trim it under 2000 characters.",
    "@{handle} is already claimed by another traveller — try a different handle.",
    "@{handle} is already claimed — pick another handle.",
    "We couldn't save your profile. Please try again.",
    "Profile details saved.",
    "Private — only visible to you. Your email cannot be edited here.",
)
PROFILE_FORM_SUBTITLE_KEY = "Handle, Phone, Email, Bio, Languages, Password"
PROFILE_FORM_KEYS: tuple[str, ...] = (
    *PROFILE_FORM_BASE_KEYS,
    PROFILE_FORM_SUBTITLE_KEY,
)

PROFILE_FORM_SOURCE_COINCIDENCES: frozenset[tuple[str, str]] = frozenset(
    {
        ("pl", "Bio"),
        ("ro", "Bio"),
        ("es", "Bio"),
        ("vi", "Email"),
    }
)

PROFILE_FORM_ROWS: dict[str, list[str]] = {
    **PROFILE_FORM_ROWS_A,
    **PROFILE_FORM_ROWS_B,
    **PROFILE_FORM_ROWS_C,
}
_EXPECTED_LOCALES = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if len(PROFILE_FORM_BASE_KEYS) != 32 or len(set(PROFILE_FORM_KEYS)) != 33:
    raise ValueError("Profile forms catalog requires 33 unique sources")
if (
    set(PROFILE_FORM_ROWS) != _EXPECTED_LOCALES
    or set(PROFILE_FORM_SUBTITLE_ROWS) != _EXPECTED_LOCALES
):
    raise ValueError(
        "Profile forms catalog must cover offered non-English locales"
    )
if sum(
    map(len, (PROFILE_FORM_ROWS_A, PROFILE_FORM_ROWS_B, PROFILE_FORM_ROWS_C))
) != len(PROFILE_FORM_ROWS):
    raise ValueError("Profile forms locale groups must not overlap")

PROFILE_FORM_CATALOGS: dict[str, dict[str, str]] = {
    locale: {
        **dict(zip(PROFILE_FORM_BASE_KEYS, values, strict=True)),
        PROFILE_FORM_SUBTITLE_KEY: PROFILE_FORM_SUBTITLE_ROWS[locale],
    }
    for locale, values in PROFILE_FORM_ROWS.items()
}
_formatter = Formatter()
for _locale, _entries in PROFILE_FORM_CATALOGS.items():
    for _source, _value in _entries.items():
        if not _value.strip() or (
            _value == _source
            and (_locale, _source) not in PROFILE_FORM_SOURCE_COINCIDENCES
        ):
            raise ValueError(
                f"Missing native profile-form phrase: {_locale}: {_source}"
            )
        if Counter(
            field for _, field, _, _ in _formatter.parse(_source) if field
        ) != Counter(
            field for _, field, _, _ in _formatter.parse(_value) if field
        ):
            raise ValueError(
                f"Profile-form placeholder mismatch: {_locale}: {_source}"
            )
