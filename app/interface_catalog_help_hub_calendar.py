from app.models import LANGUAGE_OPTIONS

HELP_HUB_CALENDAR_KEYS: tuple[str, ...] = (
    "Choose a date",
    "Remove this day",
    "Close calendar",
    "Add date",
    "Specific days",
    "Flexible days",
    "Custom weekdays",
    "Specific time",
    "Flexible times",
)

_CALENDAR_ROWS: dict[str, str] = {
    "am": "ቀን ይምረጡ|ይህን ቀን ያስወግዱ|ቀን መቁጠሪያውን ዝጋ|ቀን ጨምር|የተወሰኑ ቀናት|ተለዋዋጭ ቀናት|ብጁ የሳምንት ቀናት|የተወሰነ ሰዓት|ተለዋዋጭ ሰዓቶች",
    "ar": "اختر تاريخًا|أزل هذا اليوم|إغلاق التقويم|إضافة تاريخ|أيام محددة|أيام مرنة|أيام أسبوع مخصصة|وقت محدد|أوقات مرنة",
    "bn": "একটি তারিখ বেছে নিন|এই দিনটি সরান|ক্যালেন্ডার বন্ধ করুন|তারিখ যোগ করুন|নির্দিষ্ট দিন|নমনীয় দিন|নিজস্ব সপ্তাহের দিন|নির্দিষ্ট সময়|নমনীয় সময়",
    "my": "ရက်စွဲရွေးပါ|ဤနေ့ကို ဖယ်ရှားရန်|ပြက္ခဒိန်ပိတ်ရန်|ရက်စွဲထည့်ရန်|သတ်မှတ်ရက်များ|ပြောင်းလွယ်သောရက်များ|စိတ်ကြိုက်ရက်သတ္တပတ်နေ့များ|သတ်မှတ်ချိန်|ပြောင်းလွယ်သောအချိန်များ",
    "zh": "选择日期|移除此日期|关闭日历|添加日期|指定日期|灵活日期|自选星期|指定时间|灵活时间",
    "cs": "Vyberte datum|Odebrat tento den|Zavřít kalendář|Přidat datum|Konkrétní dny|Flexibilní dny|Vlastní dny v týdnu|Konkrétní čas|Flexibilní časy",
    "da": "Vælg en dato|Fjern denne dag|Luk kalender|Tilføj dato|Bestemte dage|Fleksible dage|Tilpassede ugedage|Bestemt tidspunkt|Fleksible tidspunkter",
    "nl": "Kies een datum|Deze dag verwijderen|Kalender sluiten|Datum toevoegen|Specifieke dagen|Flexibele dagen|Aangepaste weekdagen|Specifieke tijd|Flexibele tijden",
    "fi": "Valitse päivämäärä|Poista tämä päivä|Sulje kalenteri|Lisää päivämäärä|Tietyt päivät|Joustavat päivät|Omat viikonpäivät|Tietty aika|Joustavat ajat",
    "fr": "Choisir une date|Supprimer ce jour|Fermer le calendrier|Ajouter une date|Jours précis|Jours flexibles|Jours personnalisés|Heure précise|Horaires flexibles",
    "de": "Datum auswählen|Diesen Tag entfernen|Kalender schließen|Datum hinzufügen|Bestimmte Tage|Flexible Tage|Eigene Wochentage|Bestimmte Uhrzeit|Flexible Zeiten",
    "el": "Επιλέξτε ημερομηνία|Αφαίρεση αυτής της ημέρας|Κλείσιμο ημερολογίου|Προσθήκη ημερομηνίας|Συγκεκριμένες ημέρες|Ευέλικτες ημέρες|Προσαρμοσμένες ημέρες εβδομάδας|Συγκεκριμένη ώρα|Ευέλικτες ώρες",
    "gu": "તારીખ પસંદ કરો|આ દિવસ દૂર કરો|કૅલેન્ડર બંધ કરો|તારીખ ઉમેરો|ચોક્કસ દિવસો|લવચીક દિવસો|પસંદ કરેલા અઠવાડિયાના દિવસો|ચોક્કસ સમય|લવચીક સમય",
    "he": "בחירת תאריך|הסרת היום הזה|סגירת לוח השנה|הוספת תאריך|ימים מסוימים|ימים גמישים|ימי שבוע מותאמים אישית|שעה מסוימת|שעות גמישות",
    "hi": "तारीख चुनें|यह दिन हटाएँ|कैलेंडर बंद करें|तारीख जोड़ें|निश्चित दिन|लचीले दिन|चुने हुए सप्ताह के दिन|निश्चित समय|लचीले समय",
    "hu": "Válassz dátumot|Nap eltávolítása|Naptár bezárása|Dátum hozzáadása|Meghatározott napok|Rugalmas napok|Egyéni hétköznapok|Meghatározott időpont|Rugalmas időpontok",
    "id": "Pilih tanggal|Hapus hari ini|Tutup kalender|Tambahkan tanggal|Hari tertentu|Hari fleksibel|Hari kerja khusus|Waktu tertentu|Waktu fleksibel",
    "it": "Scegli una data|Rimuovi questo giorno|Chiudi calendario|Aggiungi data|Giorni specifici|Giorni flessibili|Giorni personalizzati|Orario specifico|Orari flessibili",
    "ja": "日付を選択|この日を削除|カレンダーを閉じる|日付を追加|特定の日|柔軟な日程|曜日を指定|特定の時間|柔軟な時間",
    "kn": "ದಿನಾಂಕ ಆಯ್ಕೆಮಾಡಿ|ಈ ದಿನವನ್ನು ತೆಗೆದುಹಾಕಿ|ಕ್ಯಾಲೆಂಡರ್ ಮುಚ್ಚಿ|ದಿನಾಂಕ ಸೇರಿಸಿ|ನಿರ್ದಿಷ್ಟ ದಿನಗಳು|ಹೊಂದಿಕೊಳ್ಳುವ ದಿನಗಳು|ಕಸ್ಟಮ್ ವಾರದ ದಿನಗಳು|ನಿರ್ದಿಷ್ಟ ಸಮಯ|ಹೊಂದಿಕೊಳ್ಳುವ ಸಮಯಗಳು",
    "ko": "날짜 선택|이 날짜 삭제|달력 닫기|날짜 추가|특정 날짜|유연한 날짜|요일 직접 선택|특정 시간|유연한 시간",
    "ml": "തീയതി തിരഞ്ഞെടുക്കുക|ഈ ദിവസം നീക്കുക|കലണ്ടർ അടയ്ക്കുക|തീയതി ചേർക്കുക|നിശ്ചിത ദിവസങ്ങൾ|സൗകര്യപ്രദമായ ദിവസങ്ങൾ|ഇഷ്ടാനുസൃത ആഴ്ചാദിനങ്ങൾ|നിശ്ചിത സമയം|സൗകര്യപ്രദമായ സമയങ്ങൾ",
    "mr": "तारीख निवडा|हा दिवस काढा|कॅलेंडर बंद करा|तारीख जोडा|ठरावीक दिवस|लवचिक दिवस|निवडक आठवड्याचे दिवस|ठरावीक वेळ|लवचिक वेळा",
    "ne": "मिति छान्नुहोस्|यो दिन हटाउनुहोस्|पात्रो बन्द गर्नुहोस्|मिति थप्नुहोस्|निश्चित दिनहरू|लचिला दिनहरू|आफूले छानेका बारहरू|निश्चित समय|लचिला समयहरू",
    "fa": "انتخاب تاریخ|حذف این روز|بستن تقویم|افزودن تاریخ|روزهای مشخص|روزهای انعطاف‌پذیر|روزهای دلخواه هفته|زمان مشخص|زمان‌های انعطاف‌پذیر",
    "pl": "Wybierz datę|Usuń ten dzień|Zamknij kalendarz|Dodaj datę|Konkretne dni|Elastyczne dni|Własne dni tygodnia|Konkretna godzina|Elastyczne godziny",
    "pt": "Escolha uma data|Remover este dia|Fechar calendário|Adicionar data|Dias específicos|Dias flexíveis|Dias da semana personalizados|Hora específica|Horas flexíveis",
    "ro": "Alege o dată|Elimină această zi|Închide calendarul|Adaugă data|Zile specifice|Zile flexibile|Zile personalizate ale săptămânii|Oră specifică|Ore flexibile",
    "es": "Elige una fecha|Eliminar este día|Cerrar calendario|Añadir fecha|Días concretos|Días flexibles|Días de la semana personalizados|Hora concreta|Horas flexibles",
    "sw": "Chagua tarehe|Ondoa siku hii|Funga kalenda|Ongeza tarehe|Siku maalum|Siku zinazobadilika|Siku maalum za wiki|Muda maalum|Nyakati zinazobadilika",
    "sv": "Välj ett datum|Ta bort den här dagen|Stäng kalendern|Lägg till datum|Specifika dagar|Flexibla dagar|Anpassade veckodagar|Specifik tid|Flexibla tider",
    "ta": "தேதியைத் தேர்ந்தெடுக்கவும்|இந்த நாளை அகற்றவும்|நாட்காட்டியை மூடவும்|தேதியைச் சேர்க்கவும்|குறிப்பிட்ட நாட்கள்|நெகிழ்வான நாட்கள்|விருப்ப வார நாட்கள்|குறிப்பிட்ட நேரம்|நெகிழ்வான நேரங்கள்",
    "te": "తేదీని ఎంచుకోండి|ఈ రోజును తీసివేయండి|క్యాలెండర్‌ను మూసివేయండి|తేదీని జోడించండి|నిర్దిష్ట రోజులు|సౌకర్యవంతమైన రోజులు|ఎంచుకున్న వారంలోని రోజులు|నిర్దిష్ట సమయం|సౌకర్యవంతమైన సమయాలు",
    "th": "เลือกวันที่|นำวันนี้ออก|ปิดปฏิทิน|เพิ่มวันที่|วันที่กำหนด|วันที่ยืดหยุ่น|กำหนดวันในสัปดาห์เอง|เวลาที่กำหนด|เวลาที่ยืดหยุ่น",
    "tr": "Tarih seçin|Bu günü kaldır|Takvimi kapat|Tarih ekle|Belirli günler|Esnek günler|Özel hafta içi günleri|Belirli saat|Esnek saatler",
    "vi": "Chọn ngày|Xóa ngày này|Đóng lịch|Thêm ngày|Ngày cụ thể|Ngày linh hoạt|Ngày trong tuần tùy chọn|Giờ cụ thể|Giờ linh hoạt",
}

_EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
if set(_CALENDAR_ROWS) != _EXPECTED_LOCALES:
    raise ValueError(
        "Help-hub calendar catalogs must cover every non-English locale"
    )
if len(HELP_HUB_CALENDAR_KEYS) != 9 or len(set(HELP_HUB_CALENDAR_KEYS)) != 9:
    raise ValueError("Help-hub calendar sources must be exactly 9 unique keys")

HELP_HUB_CALENDAR_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(HELP_HUB_CALENDAR_KEYS, row.split("|"), strict=True))
    for locale, row in _CALENDAR_ROWS.items()
}

for _locale, _entries in HELP_HUB_CALENDAR_CATALOGS.items():
    for _source, _translation in _entries.items():
        if not _translation.strip() or _translation == _source:
            raise ValueError(
                f"Missing help-hub calendar translation: {_locale}: {_source}"
            )
