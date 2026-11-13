import reflex as rx

MAP_COPY_KEYS = (
    "People, jobs, places...|Open Search filters|Close Search filters|Notifications — unread activity|Clear every filter|Save these search filters as an alert"
).split("|")
MAP_COPY_ROWS: dict[str, str] = {
    "am": "ሰዎች፣ ስራዎች፣ ቦታዎች...|የፍለጋ ማጣሪያዎችን ክፈት|የፍለጋ ማጣሪያዎችን ዝጋ|ማሳወቂያዎች — ያልተነበበ እንቅስቃሴ|ሁሉንም ማጣሪያዎች አጽዳ|እነዚህን የፍለጋ ማጣሪያዎች እንደ ማሳወቂያ አስቀምጥ",
    "ar": "أشخاص، مهام، أماكن...|فتح مرشحات البحث|إغلاق مرشحات البحث|إشعارات — نشاط غير مقروء|مسح جميع المرشحات|حفظ مرشحات البحث هذه كتنبيه",
    "bn": "মানুষ, কাজ, স্থান...|অনুসন্ধান ফিল্টার খুলুন|অনুসন্ধান ফিল্টার বন্ধ করুন|বিজ্ঞপ্তি — অপঠিত কার্যকলাপ|সব ফিল্টার মুছুন|এই অনুসন্ধান ফিল্টার বিজ্ঞপ্তি হিসেবে সংরক্ষণ করুন",
    "my": "လူများ၊ အလုပ်များ၊ နေရာများ...|ရှာဖွေမှုစစ်ထုတ်မှုများဖွင့်ရန်|ရှာဖွေမှုစစ်ထုတ်မှုများပိတ်ရန်|အသိပေးချက်များ — မဖတ်ရသေးသောလှုပ်ရှားမှု|စစ်ထုတ်မှုအားလုံးရှင်းရန်|ဤရှာဖွေမှုစစ်ထုတ်မှုများကို သတိပေးချက်အဖြစ်သိမ်းရန်",
    "zh": "人员、任务、地点...|打开搜索筛选|关闭搜索筛选|通知 — 未读动态|清除所有筛选|将这些搜索筛选保存为提醒",
    "cs": "Lidé, úkoly, místa...|Otevřít filtry vyhledávání|Zavřít filtry vyhledávání|Oznámení — nepřečtená aktivita|Vymazat všechny filtry|Uložit tyto filtry hledání jako upozornění",
    "da": "Personer, opgaver, steder...|Åbn søgefiltre|Luk søgefiltre|Notifikationer — ulæst aktivitet|Ryd alle filtre|Gem disse søgefiltre som en påmindelse",
    "nl": "Personen, taken, plaatsen...|Zoekfilters openen|Zoekfilters sluiten|Meldingen — ongelezen activiteit|Alle filters wissen|Deze zoekfilters als melding opslaan",
    "fi": "Ihmiset, tehtävät, paikat...|Avaa hakusuodattimet|Sulje hakusuodattimet|Ilmoitukset — lukematonta toimintaa|Tyhjennä kaikki suodattimet|Tallenna nämä hakusuodattimet hälytykseksi",
    "fr": "Personnes, tâches, lieux...|Ouvrir les filtres de recherche|Fermer les filtres de recherche|Notifications — activité non lue|Effacer tous les filtres|Enregistrer ces filtres de recherche comme alerte",
    "de": "Personen, Aufgaben, Orte...|Suchfilter öffnen|Suchfilter schließen|Benachrichtigungen — ungelesene Aktivitäten|Alle Filter zurücksetzen|Diese Suchfilter als Benachrichtigung speichern",
    "el": "Άτομα, εργασίες, μέρη...|Άνοιγμα φίλτρων αναζήτησης|Κλείσιμο φίλτρων αναζήτησης|Ειδοποιήσεις — μη αναγνωσμένη δραστηριότητα|Εκκαθάριση όλων των φίλτρων|Αποθήκευση αυτών των φίλτρων αναζήτησης ως ειδοποίηση",
    "gu": "લોકો, કામ, સ્થળો...|શોધ ફિલ્ટર ખોલો|શોધ ફિલ્ટર બંધ કરો|સૂચનાઓ — ન વાંચેલી પ્રવૃત્તિ|બધા ફિલ્ટર સાફ કરો|આ શોધ ફિલ્ટરને સૂચના તરીકે સાચવો",
    "ha": "Mutane, ayyuka, wurare...|Buɗe matatun bincike|Rufe matatun bincike|Sanarwa — ayyukan da ba a karanta ba|Goge duk matatu|Ajiye waɗannan matatun bincike a matsayin sanarwa",
    "he": "אנשים, משימות, מקומות...|פתיחת מסנני חיפוש|סגירת מסנני חיפוש|התראות — פעילות שלא נקראה|ניקוי כל המסננים|שמירת מסנני החיפוש האלה כהתראה",
    "hi": "लोग, काम, जगहें...|खोज फ़िल्टर खोलें|खोज फ़िल्टर बंद करें|सूचनाएँ — अपठित गतिविधि|सभी फ़िल्टर साफ़ करें|इन खोज फ़िल्टरों को सूचना के रूप में सहेजें",
    "hu": "Emberek, feladatok, helyek...|Keresési szűrők megnyitása|Keresési szűrők bezárása|Értesítések — olvasatlan tevékenység|Összes szűrő törlése|Ezeknek a keresési szűrőknek a mentése értesítésként",
    "id": "Orang, tugas, tempat...|Buka filter pencarian|Tutup filter pencarian|Notifikasi — aktivitas belum dibaca|Hapus semua filter|Simpan filter pencarian ini sebagai notifikasi",
    "it": "Persone, attività, luoghi...|Apri i filtri di ricerca|Chiudi i filtri di ricerca|Notifiche — attività non letta|Cancella tutti i filtri|Salva questi filtri di ricerca come avviso",
    "ja": "人、作業、場所...|検索フィルターを開く|検索フィルターを閉じる|通知 — 未読の活動|すべてのフィルターをクリア|この検索フィルターを通知として保存",
    "kn": "ಜನರು, ಕೆಲಸಗಳು, ಸ್ಥಳಗಳು...|ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ತೆರೆಯಿರಿ|ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಮುಚ್ಚಿ|ಅಧಿಸೂಚನೆಗಳು — ಓದದ ಚಟುವಟಿಕೆ|ಎಲ್ಲಾ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ತೆರವುಗೊಳಿಸಿ|ಈ ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಎಚ್ಚರಿಕೆಯಾಗಿ ಉಳಿಸಿ",
    "ko": "사람, 작업, 장소...|검색 필터 열기|검색 필터 닫기|알림 — 읽지 않은 활동|모든 필터 지우기|이 검색 필터를 알림으로 저장",
    "ml": "ആളുകൾ, ജോലികൾ, സ്ഥലങ്ങൾ...|തിരയൽ ഫിൽട്ടറുകൾ തുറക്കുക|തിരയൽ ഫിൽട്ടറുകൾ അടയ്ക്കുക|അറിയിപ്പുകൾ — വായിക്കാത്ത പ്രവർത്തനം|എല്ലാ ഫിൽട്ടറുകളും മായ്ക്കുക|ഈ തിരയൽ ഫിൽട്ടറുകൾ അറിയിപ്പായി സംരക്ഷിക്കുക",
    "mr": "लोक, कामे, ठिकाणे...|शोध फिल्टर उघडा|शोध फिल्टर बंद करा|सूचना — न वाचलेले क्रियाकलाप|सर्व फिल्टर साफ करा|हे शोध फिल्टर सूचना म्हणून जतन करा",
    "ne": "मानिस, काम, ठाउँ...|खोज फिल्टरहरू खोल्नुहोस्|खोज फिल्टरहरू बन्द गर्नुहोस्|सूचनाहरू — नपढिएको गतिविधि|सबै फिल्टरहरू मेटाउनुहोस्|यी खोज फिल्टरहरूलाई सूचनाको रूपमा सुरक्षित गर्नुहोस्",
    "fa": "افراد، کارها، مکان‌ها...|باز کردن فیلترهای جستجو|بستن فیلترهای جستجو|اعلان‌ها — فعالیت خوانده‌نشده|پاک کردن همه فیلترها|ذخیره این فیلترهای جستجو به‌عنوان هشدار",
    "pl": "Osoby, zadania, miejsca...|Otwórz filtry wyszukiwania|Zamknij filtry wyszukiwania|Powiadomienia — nieprzeczytana aktywność|Wyczyść wszystkie filtry|Zapisz te filtry wyszukiwania jako powiadomienie",
    "pt": "Pessoas, tarefas, locais...|Abrir filtros de pesquisa|Fechar filtros de pesquisa|Notificações — atividade por ler|Limpar todos os filtros|Guardar estes filtros de pesquisa como alerta",
    "ro": "Persoane, sarcini, locuri...|Deschide filtrele de căutare|Închide filtrele de căutare|Notificări — activitate necitită|Șterge toate filtrele|Salvează aceste filtre de căutare ca alertă",
    "es": "Personas, tareas, lugares...|Abrir filtros de búsqueda|Cerrar filtros de búsqueda|Notificaciones — actividad sin leer|Borrar todos los filtros|Guardar estos filtros de búsqueda como alerta",
    "sw": "Watu, kazi, maeneo...|Fungua vichujio vya utafutaji|Funga vichujio vya utafutaji|Arifa — shughuli ambazo hazijasomwa|Futa vichujio vyote|Hifadhi vichujio hivi vya utafutaji kama arifa",
    "sv": "Personer, uppgifter, platser...|Öppna sökfilter|Stäng sökfilter|Aviseringar — oläst aktivitet|Rensa alla filter|Spara dessa sökfilter som en avisering",
    "ta": "நபர்கள், வேலைகள், இடங்கள்...|தேடல் வடிகட்டிகளைத் திற|தேடல் வடிகட்டிகளை மூடு|அறிவிப்புகள் — படிக்காத செயல்பாடு|எல்லா வடிகட்டிகளையும் அழி|இந்தத் தேடல் வடிகட்டிகளை அறிவிப்பாகச் சேமி",
    "te": "వ్యక్తులు, పనులు, స్థలాలు...|శోధన ఫిల్టర్‌లను తెరవండి|శోధన ఫిల్టర్‌లను మూసివేయండి|నోటిఫికేషన్‌లు — చదవని కార్యకలాపం|అన్ని ఫిల్టర్‌లను తొలగించండి|ఈ శోధన ఫిల్టర్‌లను హెచ్చరికగా సేవ్ చేయండి",
    "th": "ผู้คน งาน สถานที่...|เปิดตัวกรองการค้นหา|ปิดตัวกรองการค้นหา|การแจ้งเตือน — กิจกรรมที่ยังไม่ได้อ่าน|ล้างตัวกรองทั้งหมด|บันทึกตัวกรองการค้นหาเหล่านี้เป็นการแจ้งเตือน",
    "tr": "Kişiler, işler, yerler...|Arama filtrelerini aç|Arama filtrelerini kapat|Bildirimler — okunmamış etkinlik|Tüm filtreleri temizle|Bu arama filtrelerini uyarı olarak kaydet",
    "vi": "Người, công việc, địa điểm...|Mở bộ lọc tìm kiếm|Đóng bộ lọc tìm kiếm|Thông báo — hoạt động chưa đọc|Xóa tất cả bộ lọc|Lưu bộ lọc tìm kiếm này làm thông báo",
}
MAP_COPY_CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(MAP_COPY_KEYS, row.split("|"), strict=True))
    for code, row in MAP_COPY_ROWS.items()
}
