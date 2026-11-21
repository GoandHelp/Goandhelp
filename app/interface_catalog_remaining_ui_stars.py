import reflex as rx

from collections import Counter
from string import Formatter
from app.models import LANGUAGE_OPTIONS

REMAINING_STARS_KEYS: tuple[str, ...] = ("{score} out of 5 stars",)
REMAINING_STARS_ROWS: dict[str, str] = {
    "am": "ከ5 ኮከቦች {score}",
    "ar": "{score} من أصل 5 نجوم",
    "bn": "৫ তারার মধ্যে {score}",
    "my": "ကြယ် 5 ပွင့်အနက် {score}",
    "zh": "{score} 星（满分 5 星）",
    "cs": "{score} z 5 hvězdiček",
    "da": "{score} ud af 5 stjerner",
    "nl": "{score} van 5 sterren",
    "fi": "{score} tähteä viidestä",
    "fr": "{score} étoiles sur 5",
    "de": "{score} von 5 Sternen",
    "el": "{score} από 5 αστέρια",
    "gu": "5 તારામાંથી {score}",
    "he": "{score} מתוך 5 כוכבים",
    "hi": "5 सितारों में से {score}",
    "hu": "{score} csillag az 5-ből",
    "id": "{score} dari 5 bintang",
    "it": "{score} stelle su 5",
    "ja": "5つ星中{score}つ星",
    "kn": "5 ನಕ್ಷತ್ರಗಳಲ್ಲಿ {score}",
    "ko": "별 5개 중 {score}개",
    "ml": "5 നക്ഷത്രങ്ങളിൽ {score}",
    "mr": "5 तार्‍यांपैकी {score}",
    "ne": "5 तारामध्ये {score}",
    "fa": "{score} از 5 ستاره",
    "pl": "{score} z 5 gwiazdek",
    "pt": "{score} de 5 estrelas",
    "ro": "{score} din 5 stele",
    "es": "{score} de 5 estrellas",
    "sw": "Nyota {score} kati ya 5",
    "sv": "{score} av 5 stjärnor",
    "ta": "5 நட்சத்திரங்களில் {score}",
    "te": "5 నక్షత్రాలలో {score}",
    "th": "{score} จาก 5 ดาว",
    "tr": "5 üzerinden {score} yıldız",
    "vi": "{score} trên 5 sao",
}
if set(REMAINING_STARS_ROWS) != {
    code for code, _ in LANGUAGE_OPTIONS if code != "en"
}:
    raise ValueError("Remaining stars locale coverage is incomplete")
REMAINING_STARS_CATALOGS: dict[str, dict[str, str]] = {
    code: {REMAINING_STARS_KEYS[0]: value}
    for code, value in REMAINING_STARS_ROWS.items()
}
_formatter = Formatter()
for _code, _value in REMAINING_STARS_ROWS.items():
    if (
        not _value.strip()
        or _value == REMAINING_STARS_KEYS[0]
        or Counter(slot for _, slot, _, _ in _formatter.parse(_value) if slot)
        != Counter({"score": 1})
    ):
        raise ValueError(f"Invalid remaining stars phrase: {_code}")
