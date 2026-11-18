from app.models import LANGUAGE_OPTIONS

HELP_HUB_FIELD_KEYS: tuple[str, ...] = (
    "Date",
    "required when no map pin",
)

_FIELD_ROWS: dict[str, str] = {
    "am": "ቀን|ፒን በሌለበት ጊዜ ያስፈልጋል",
    "ar": "التاريخ|مطلوب عند عدم وجود دبوس على الخريطة",
    "bn": "তারিখ|মানচিত্রে পিন না থাকলে আবশ্যক",
    "my": "ရက်စွဲ|မြေပုံပင်မရှိပါက လိုအပ်သည်",
    "zh": "日期|未放置地图图钉时必填",
    "cs": "Datum|Povinné, pokud není umístěn bod na mapě",
    "da": "Dato|Påkrævet, hvis der ikke er en markør på kortet",
    "nl": "Datum|Verplicht als er geen speld op de kaart staat",
    "fi": "Päivämäärä|Pakollinen, jos karttamerkkiä ei ole",
    "fr": "Date prévue|Obligatoire si aucun repère n’est placé sur la carte",
    "de": "Datum|Erforderlich, wenn keine Markierung auf der Karte gesetzt ist",
    "el": "Ημερομηνία|Απαιτείται όταν δεν υπάρχει καρφίτσα στον χάρτη",
    "gu": "તારીખ|નકશા પર પિન ન હોય ત્યારે જરૂરી",
    "he": "תאריך|חובה אם לא הוצבה סיכה במפה",
    "hi": "तारीख|मानचित्र पर पिन न होने पर आवश्यक",
    "hu": "Dátum|Kötelező, ha nincs térképes jelölő",
    "id": "Tanggal|Wajib jika tidak ada pin pada peta",
    "it": "Data|Obbligatorio se non è presente un segnaposto sulla mappa",
    "ja": "日付|地図にピンがない場合は必須",
    "kn": "ದಿನಾಂಕ|ನಕ್ಷೆಯಲ್ಲಿ ಪಿನ್ ಇಲ್ಲದಿದ್ದರೆ ಅಗತ್ಯ",
    "ko": "날짜|지도 핀이 없으면 필수",
    "ml": "തീയതി|മാപ്പിൽ പിൻ ഇല്ലെങ്കിൽ നിർബന്ധമാണ്",
    "mr": "तारीख|नकाशावर पिन नसल्यास आवश्यक",
    "ne": "मिति|नक्सामा पिन नभएमा आवश्यक",
    "fa": "تاریخ|در صورت نبودن نشانگر روی نقشه الزامی است",
    "pl": "Data|Wymagane, jeśli na mapie nie ma pinezki",
    "pt": "Data|Obrigatório se não houver um marcador no mapa",
    "ro": "Dată|Obligatoriu dacă nu există un marcator pe hartă",
    "es": "Fecha|Obligatorio si no hay un marcador en el mapa",
    "sw": "Tarehe|Inahitajika ikiwa hakuna pini kwenye ramani",
    "sv": "Datum|Krävs om det inte finns någon kartmarkör",
    "ta": "தேதி|வரைபடத்தில் குறியீடு இல்லாவிட்டால் கட்டாயம்",
    "te": "తేదీ|మ్యాప్‌లో పిన్ లేకపోతే తప్పనిసరి",
    "th": "วันที่|จำเป็นเมื่อไม่มีหมุดบนแผนที่",
    "tr": "Tarih|Haritada bir işaret yoksa gereklidir",
    "vi": "Ngày|Bắt buộc nếu không có ghim trên bản đồ",
}

_EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
if set(_FIELD_ROWS) != _EXPECTED_LOCALES:
    raise ValueError(
        "Help-hub field catalogs must cover every non-English locale"
    )
if len(HELP_HUB_FIELD_KEYS) != 2 or len(set(HELP_HUB_FIELD_KEYS)) != 2:
    raise ValueError("Help-hub field sources must be exactly 2 unique keys")

HELP_HUB_FIELD_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(HELP_HUB_FIELD_KEYS, row.split("|"), strict=True))
    for locale, row in _FIELD_ROWS.items()
}

for _locale, _entries in HELP_HUB_FIELD_CATALOGS.items():
    for _source, _translation in _entries.items():
        if not _translation.strip() or _translation == _source:
            raise ValueError(
                f"Missing help-hub field translation: {_locale}: {_source}"
            )
