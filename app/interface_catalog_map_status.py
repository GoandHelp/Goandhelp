from app.models import LANGUAGE_OPTIONS

MAP_STATUS_KEYS: tuple[str, ...] = ("Updating map…", "Updating map")
MAP_STATUS_ROWS: dict[str, str] = {
    "am": "ካርታውን በማዘመን ላይ…|ካርታውን በማዘመን ላይ",
    "ar": "جارٍ تحديث الخريطة…|جارٍ تحديث الخريطة",
    "bn": "মানচিত্র হালনাগাদ হচ্ছে…|মানচিত্র হালনাগাদ হচ্ছে",
    "my": "မြေပုံကို အပ်ဒိတ်လုပ်နေသည်…|မြေပုံကို အပ်ဒိတ်လုပ်နေသည်",
    "zh": "正在更新地图…|正在更新地图",
    "cs": "Aktualizace mapy…|Aktualizuji mapu",
    "da": "Opdaterer kort…|Opdaterer kort",
    "nl": "Kaart wordt bijgewerkt…|Kaart wordt bijgewerkt",
    "fi": "Karttaa päivitetään…|Karttaa päivitetään",
    "fr": "Mise à jour de la carte…|Mise à jour de la carte",
    "de": "Karte wird aktualisiert…|Karte wird aktualisiert",
    "el": "Ενημέρωση χάρτη…|Ενημέρωση χάρτη",
    "gu": "નકશો અપડેટ થઈ રહ્યો છે…|નકશો અપડેટ થઈ રહ્યો છે",
    "he": "המפה מתעדכנת…|המפה מתעדכנת",
    "hi": "मानचित्र अपडेट हो रहा है…|मानचित्र अपडेट हो रहा है",
    "hu": "Térkép frissítése…|Térkép frissítése",
    "id": "Memperbarui peta…|Memperbarui peta",
    "it": "Aggiornamento della mappa…|Aggiornamento della mappa",
    "ja": "地図を更新しています…|地図を更新しています",
    "kn": "ನಕ್ಷೆಯನ್ನು ನವೀಕರಿಸಲಾಗುತ್ತಿದೆ…|ನಕ್ಷೆಯನ್ನು ನವೀಕರಿಸಲಾಗುತ್ತಿದೆ",
    "ko": "지도 업데이트 중…|지도 업데이트 중",
    "ml": "മാപ്പ് പുതുക്കുന്നു…|മാപ്പ് പുതുക്കുന്നു",
    "mr": "नकाशा अद्ययावत होत आहे…|नकाशा अद्ययावत होत आहे",
    "ne": "नक्सा अद्यावधिक हुँदैछ…|नक्सा अद्यावधिक हुँदैछ",
    "fa": "نقشه در حال به‌روزرسانی است…|نقشه در حال به‌روزرسانی است",
    "pl": "Aktualizowanie mapy…|Aktualizowanie mapy",
    "pt": "A atualizar o mapa…|A atualizar o mapa",
    "ro": "Se actualizează harta…|Se actualizează harta",
    "es": "Actualizando el mapa…|Actualizando el mapa",
    "sw": "Inasasisha ramani…|Inasasisha ramani",
    "sv": "Uppdaterar kartan…|Uppdaterar kartan",
    "ta": "வரைபடம் புதுப்பிக்கப்படுகிறது…|வரைபடம் புதுப்பிக்கப்படுகிறது",
    "te": "మ్యాప్‌ను అప్‌డేట్ చేస్తోంది…|మ్యాప్‌ను అప్‌డేట్ చేస్తోంది",
    "th": "กำลังอัปเดตแผนที่…|กำลังอัปเดตแผนที่",
    "tr": "Harita güncelleniyor…|Harita güncelleniyor",
    "vi": "Đang cập nhật bản đồ…|Đang cập nhật bản đồ",
}
_EXPECTED_LOCALES = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if set(MAP_STATUS_ROWS) != _EXPECTED_LOCALES:
    raise ValueError("Map status catalog locale coverage is incomplete")
if any(
    len(row.split("|")) != len(MAP_STATUS_KEYS)
    for row in MAP_STATUS_ROWS.values()
):
    raise ValueError("Map status catalog row length is invalid")
MAP_STATUS_CATALOGS: dict[str, dict[str, str]] = {
    language: dict(zip(MAP_STATUS_KEYS, row.split("|"), strict=True))
    for language, row in MAP_STATUS_ROWS.items()
}
