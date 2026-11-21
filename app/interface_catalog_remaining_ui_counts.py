import reflex as rx

from app.models import LANGUAGE_OPTIONS

REMAINING_COUNT_KEYS: tuple[str, ...] = ("{count} review", "{count} reviews")
REMAINING_COUNT_ROWS: dict[str, str] = {
    "am": "{count} ግምገማ|{count} ግምገማዎች",
    "ar": "تقييم واحد ({count})|عدد التقييمات: {count}",
    "bn": "{count}টি পর্যালোচনা|{count}টি পর্যালোচনা",
    "my": "သုံးသပ်ချက် {count} ခု|သုံးသပ်ချက် {count} ခု",
    "zh": "{count} 条评价|{count} 条评价",
    "cs": "{count} hodnocení|Počet hodnocení: {count}",
    "da": "{count} anmeldelse|{count} anmeldelser",
    "nl": "{count} beoordeling|{count} beoordelingen",
    "fi": "{count} arvostelu|{count} arvostelua",
    "fr": "{count} avis|{count} avis",
    "de": "{count} Bewertung|{count} Bewertungen",
    "el": "{count} αξιολόγηση|{count} αξιολογήσεις",
    "gu": "{count} સમીક્ષા|{count} સમીક્ષાઓ",
    "he": "ביקורת אחת ({count})|מספר הביקורות: {count}",
    "hi": "{count} समीक्षा|{count} समीक्षाएँ",
    "hu": "{count} értékelés|{count} értékelés",
    "id": "{count} ulasan|{count} ulasan",
    "it": "{count} recensione|{count} recensioni",
    "ja": "レビュー{count}件|レビュー{count}件",
    "kn": "{count} ವಿಮರ್ಶೆ|{count} ವಿಮರ್ಶೆಗಳು",
    "ko": "리뷰 {count}개|리뷰 {count}개",
    "ml": "{count} അവലോകനം|{count} അവലോകനങ്ങൾ",
    "mr": "{count} पुनरावलोकन|{count} पुनरावलोकने",
    "ne": "{count} समीक्षा|{count} समीक्षाहरू",
    "fa": "{count} نظر|{count} نظر",
    "pl": "{count} opinia|Liczba opinii: {count}",
    "pt": "{count} avaliação|{count} avaliações",
    "ro": "{count} recenzie|Număr de recenzii: {count}",
    "es": "{count} reseña|{count} reseñas",
    "sw": "Tathmini {count}|Tathmini {count}",
    "sv": "{count} omdöme|{count} omdömen",
    "ta": "{count} மதிப்புரை|{count} மதிப்புரைகள்",
    "te": "{count} సమీక్ష|{count} సమీక్షలు",
    "th": "{count} รีวิว|{count} รีวิว",
    "tr": "{count} değerlendirme|{count} değerlendirme",
    "vi": "{count} đánh giá|{count} đánh giá",
}
if set(REMAINING_COUNT_ROWS) != {
    code for code, _ in LANGUAGE_OPTIONS if code != "en"
}:
    raise ValueError("Remaining count locale coverage is incomplete")
REMAINING_COUNT_CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(REMAINING_COUNT_KEYS, row.split("|"), strict=True))
    for code, row in REMAINING_COUNT_ROWS.items()
}
for _code, _entries in REMAINING_COUNT_CATALOGS.items():
    for _source, _value in _entries.items():
        if (
            not _value.strip()
            or _value == _source
            or _value.count("{count}") != 1
        ):
            raise ValueError(
                f"Invalid remaining count phrase: {_code}: {_source}"
            )
