import reflex as rx

import json
import logging

LANGUAGE_CHOICES: list[dict[str, str]] = [
    {"code": "", "flag": "🌐", "name": "Any language"},
    {"code": "en", "flag": "🇬🇧", "name": "English"},
    {"code": "es", "flag": "🇪🇸", "name": "Spanish"},
    {"code": "fr", "flag": "🇫🇷", "name": "French"},
    {"code": "de", "flag": "🇩🇪", "name": "German"},
    {"code": "pt", "flag": "🇵🇹", "name": "Portuguese"},
    {"code": "it", "flag": "🇮🇹", "name": "Italian"},
    {"code": "nl", "flag": "🇳🇱", "name": "Dutch"},
    {"code": "pl", "flag": "🇵🇱", "name": "Polish"},
    {"code": "uk", "flag": "🇺🇦", "name": "Ukrainian"},
    {"code": "ru", "flag": "🇷🇺", "name": "Russian"},
    {"code": "ar", "flag": "🇸🇦", "name": "Arabic"},
    {"code": "hi", "flag": "🇮🇳", "name": "Hindi"},
    {"code": "zh", "flag": "🇨🇳", "name": "Chinese"},
    {"code": "ja", "flag": "🇯🇵", "name": "Japanese"},
    {"code": "ko", "flag": "🇰🇷", "name": "Korean"},
    {"code": "bn", "flag": "🇧🇩", "name": "Bengali"},
    {"code": "ur", "flag": "🇵🇰", "name": "Urdu"},
    {"code": "id", "flag": "🇮🇩", "name": "Indonesian"},
    {"code": "tr", "flag": "🇹🇷", "name": "Turkish"},
    {"code": "vi", "flag": "🇻🇳", "name": "Vietnamese"},
    {"code": "ta", "flag": "🌐", "name": "Tamil"},
    {"code": "te", "flag": "🇮🇳", "name": "Telugu"},
    {"code": "mr", "flag": "🇮🇳", "name": "Marathi"},
    {"code": "pa", "flag": "🌐", "name": "Punjabi"},
    {"code": "fa", "flag": "🌐", "name": "Persian"},
    {"code": "sw", "flag": "🌐", "name": "Swahili"},
    {"code": "jv", "flag": "🇮🇩", "name": "Javanese"},
    {"code": "gu", "flag": "🇮🇳", "name": "Gujarati"},
    {"code": "ha", "flag": "🌐", "name": "Hausa"},
    {"code": "kn", "flag": "🇮🇳", "name": "Kannada"},
    {"code": "th", "flag": "🇹🇭", "name": "Thai"},
    {"code": "my", "flag": "🇲🇲", "name": "Burmese"},
    {"code": "ml", "flag": "🇮🇳", "name": "Malayalam"},
    {"code": "or", "flag": "🇮🇳", "name": "Odia"},
    {"code": "am", "flag": "🇪🇹", "name": "Amharic"},
    {"code": "yo", "flag": "🌐", "name": "Yoruba"},
    {"code": "ig", "flag": "🇳🇬", "name": "Igbo"},
    {"code": "uz", "flag": "🇺🇿", "name": "Uzbek"},
    {"code": "sd", "flag": "🌐", "name": "Sindhi"},
    {"code": "ps", "flag": "🌐", "name": "Pashto"},
    {"code": "ms", "flag": "🌐", "name": "Malay"},
    {"code": "tl", "flag": "🇵🇭", "name": "Tagalog"},
    {"code": "su", "flag": "🇮🇩", "name": "Sundanese"},
    {"code": "ro", "flag": "🇷🇴", "name": "Romanian"},
    {"code": "ne", "flag": "🇳🇵", "name": "Nepali"},
    {"code": "si", "flag": "🇱🇰", "name": "Sinhala"},
    {"code": "as", "flag": "🇮🇳", "name": "Assamese"},
    {"code": "km", "flag": "🇰🇭", "name": "Khmer"},
    {"code": "so", "flag": "🌐", "name": "Somali"},
    {"code": "om", "flag": "🌐", "name": "Oromo"},
    {"code": "ff", "flag": "🌐", "name": "Fula"},
    {"code": "ku", "flag": "🌐", "name": "Kurdish"},
    {"code": "az", "flag": "🇦🇿", "name": "Azerbaijani"},
    {"code": "hu", "flag": "🇭🇺", "name": "Hungarian"},
    {"code": "el", "flag": "🇬🇷", "name": "Greek"},
    {"code": "cs", "flag": "🇨🇿", "name": "Czech"},
    {"code": "sv", "flag": "🇸🇪", "name": "Swedish"},
    {"code": "he", "flag": "🇮🇱", "name": "Hebrew"},
    {"code": "be", "flag": "🇧🇾", "name": "Belarusian"},
    {"code": "bg", "flag": "🇧🇬", "name": "Bulgarian"},
    {"code": "sr", "flag": "🇷🇸", "name": "Serbian"},
    {"code": "hr", "flag": "🇭🇷", "name": "Croatian"},
    {"code": "sk", "flag": "🇸🇰", "name": "Slovak"},
    {"code": "fi", "flag": "🇫🇮", "name": "Finnish"},
    {"code": "da", "flag": "🇩🇰", "name": "Danish"},
    {"code": "no", "flag": "🇳🇴", "name": "Norwegian"},
    {"code": "lt", "flag": "🇱🇹", "name": "Lithuanian"},
    {"code": "sq", "flag": "🇦🇱", "name": "Albanian"},
    {"code": "hy", "flag": "🇦🇲", "name": "Armenian"},
    {"code": "ka", "flag": "🇬🇪", "name": "Georgian"},
    {"code": "kk", "flag": "🇰🇿", "name": "Kazakh"},
    {"code": "ky", "flag": "🇰🇬", "name": "Kyrgyz"},
    {"code": "tg", "flag": "🇹🇯", "name": "Tajik"},
    {"code": "tk", "flag": "🇹🇲", "name": "Turkmen"},
    {"code": "mn", "flag": "🇲🇳", "name": "Mongolian"},
    {"code": "lo", "flag": "🇱🇦", "name": "Lao"},
    {"code": "zu", "flag": "🇿🇦", "name": "Zulu"},
    {"code": "xh", "flag": "🇿🇦", "name": "Xhosa"},
    {"code": "af", "flag": "🌐", "name": "Afrikaans"},
    {"code": "mg", "flag": "🇲🇬", "name": "Malagasy"},
    {"code": "rw", "flag": "🇷🇼", "name": "Kinyarwanda"},
    {"code": "rn", "flag": "🇧🇮", "name": "Kirundi"},
    {"code": "sn", "flag": "🇿🇼", "name": "Shona"},
    {"code": "ny", "flag": "🌐", "name": "Chichewa"},
    {"code": "ln", "flag": "🌐", "name": "Lingala"},
    {"code": "ak", "flag": "🇬🇭", "name": "Akan"},
    {"code": "wo", "flag": "🇸🇳", "name": "Wolof"},
    {"code": "ti", "flag": "🌐", "name": "Tigrinya"},
    {"code": "ht", "flag": "🇭🇹", "name": "Haitian Creole"},
    {"code": "qu", "flag": "🌐", "name": "Quechua"},
    {"code": "gn", "flag": "🇵🇾", "name": "Guarani"},
    {"code": "ca", "flag": "🌐", "name": "Catalan"},
    {"code": "yue", "flag": "🌐", "name": "Cantonese"},
    {"code": "wuu", "flag": "🇨🇳", "name": "Wu Chinese"},
    {"code": "nan", "flag": "🌐", "name": "Min Nan Chinese"},
    {"code": "bho", "flag": "🇮🇳", "name": "Bhojpuri"},
    {"code": "mai", "flag": "🌐", "name": "Maithili"},
    {"code": "ceb", "flag": "🇵🇭", "name": "Cebuano"},
    {"code": "fil", "flag": "🇵🇭", "name": "Filipino"},
    {"code": "sat", "flag": "🇮🇳", "name": "Santali"},
]
LANGUAGE_CODES = frozenset(
    row["code"] for row in LANGUAGE_CHOICES if row["code"]
)
PREFIX = "[[GAH:HELP-LANGUAGES:v1]]"
PERIOD_PREFIX = "[[GAH:HELP-DURATION:v1]]"


def _validate_period(count: int, unit: str) -> tuple[int, str]:
    if type(count) is not int or not 1 <= count <= 7:
        raise ValueError("Choose a duration period from 1 to 7.")
    if not isinstance(unit, str) or unit not in ("day", "week", "month"):
        raise ValueError("Choose day, week or month.")
    return count, unit


def encode_knowledge_with_period(
    text: str, codes: list[str], count: int, unit: str
) -> str:
    count, unit = _validate_period(count, unit)
    encoded = encode_knowledge(text, codes)
    # Always delimit ordinary text, including literal reserved prefixes.
    if not encoded.startswith(PREFIX):
        encoded = f"{PREFIX}[]\n{encoded}"
    metadata = json.dumps({"count": count, "unit": unit}, separators=(",", ":"))
    return f"{PERIOD_PREFIX}{metadata}\n{encoded}"


def _decode_period_header(value: str | None) -> tuple[str, tuple[int, str]]:
    text = value or ""
    if not text.startswith(PERIOD_PREFIX):
        return text, (1, "day")
    header, separator, ordinary = text.partition("\n")
    try:
        metadata = json.loads(header[len(PERIOD_PREFIX) :])
        if not separator or not isinstance(metadata, dict):
            raise ValueError("Invalid duration metadata")
        period = _validate_period(metadata.get("count"), metadata.get("unit"))
        return ordinary, period
    except (ValueError, TypeError):
        logging.warning("Ignoring malformed help-duration metadata.")
        return ordinary, (1, "day")


def decode_duration_period(value: str | None) -> tuple[int, str]:
    return _decode_period_header(value)[1]


def encode_knowledge(text: str, codes: list[str]) -> str:
    if any(
        not isinstance(code, str) or code not in LANGUAGE_CODES
        for code in codes
    ):
        raise ValueError("Choose languages from the supplied list.")
    normalized = sorted(set(codes))
    if not normalized and not text.startswith(PREFIX):
        return text
    return f"{PREFIX}{json.dumps(normalized, separators=(',', ':'))}\n{text}"


def decode_knowledge(value: str | None) -> tuple[str, list[str]]:
    text, _period = _decode_period_header(value)
    if not text.startswith(PREFIX):
        return text, []
    header, separator, ordinary = text.partition("\n")
    try:
        codes = json.loads(header[len(PREFIX) :])
        if not isinstance(codes, list) or any(
            not isinstance(code, str) or code not in LANGUAGE_CODES
            for code in codes
        ):
            raise ValueError("Invalid language metadata")
        if not separator:
            raise ValueError("Missing language metadata terminator")
        return ordinary, sorted(set(codes))
    except (ValueError, TypeError):
        logging.warning("Ignoring malformed help-language metadata.")
        return ordinary, []
