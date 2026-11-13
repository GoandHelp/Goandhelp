import reflex as rx

import string
from collections import Counter

from app.models import CATEGORY_LABELS, LANGUAGE_OPTIONS, TASK_CATEGORIES

SEARCH_FILTER_KEYS: tuple[str, ...] = (
    "Events",
    "Translator",
    "First-aid",
    "Arts",
    "Agriculture",
    "Carer",
    "Construction",
    "Cook",
    "Cleaner",
    "Craftwork",
    "Healthcare",
    "Labour",
    "Legal",
    "Mechanic",
    "Media",
    "Music",
    "Sales",
    "Spirituality",
    "Sports",
    "Teaching",
    "Technician",
    "Tourism",
    "Workshop",
    "Other",
    "Any reward",
    "Money",
    "Lunch",
    "Dinner",
    "Accommodation",
    "Guided tours",
    "Workshops",
    "Lessons",
    "English",
    "Spanish",
    "French",
    "Portuguese",
    "German",
    "Italian",
    "Arabic",
    "Hindi",
    "Chinese",
    "Japanese",
    "Any time",
    "Online today",
    "Online this week",
    "Online this month",
)

SEARCH_FILTER_UI_KEYS: tuple[str, ...] = (
    "Go",
    "Get",
    "All categories",
    "Any",
    "Distance",
    "1 km",
    "My location",
    "Show my location",
    "Show my location: Off",
    "Show my location: Approx",
    "Nationality",
    "Filter by nationality",
    "Spoken languages",
    "choose any",
    "Combined rating",
    "Subscribe",
    "Premium",
    "Active filters",
)

SEARCH_FILTER_UI_ROWS: dict[str, str] = {
    "am": "ስጥ|ተቀበል|ሁሉም ምድቦች|ማንኛውም|ርቀት|1 ኪ.ሜ.|አካባቢዬ|አካባቢዬን አሳይ|አካባቢዬን አሳይ፦ ጠፍቷል|አካባቢዬን አሳይ፦ ግምታዊ|ዜግነት|በዜግነት አጣራ|የሚነገሩ ቋንቋዎች|ማንኛውንም ይምረጡ|የተጣመረ ደረጃ|ይመዝገቡ|ፕሪሚየም|ንቁ ማጣሪያዎች",
    "ar": "قدّم|احصل|جميع الفئات|أيّ|المسافة|1 كم|موقعي|عرض موقعي|عرض موقعي: إيقاف|عرض موقعي: تقريبي|الجنسية|تصفية حسب الجنسية|اللغات المنطوقة|اختر أيًا منها|التقييم المجمّع|اشترك|مميز|المرشحات النشطة",
    "bn": "দিতে চান|পেতে চান|সব বিভাগ|যেকোনো|দূরত্ব|১ কিমি|আমার অবস্থান|আমার অবস্থান দেখান|আমার অবস্থান দেখান: বন্ধ|আমার অবস্থান দেখান: আনুমানিক|জাতীয়তা|জাতীয়তা অনুযায়ী ফিল্টার|কথ্য ভাষা|যেকোনোটি বেছে নিন|সম্মিলিত রেটিং|সাবস্ক্রাইব|প্রিমিয়াম|সক্রিয় ফিল্টার",
    "my": "ပေးရန်|ရယူရန်|အမျိုးအစားအားလုံး|မည်သည့်|အကွာအဝေး|1 ကီလိုမီတာ|ကျွန်ုပ်၏တည်နေရာ|ကျွန်ုပ်၏တည်နေရာကိုပြရန်|ကျွန်ုပ်၏တည်နေရာကိုပြရန်: ပိတ်|ကျွန်ုပ်၏တည်နေရာကိုပြရန်: ခန့်မှန်း|နိုင်ငံသား|နိုင်ငံသားအလိုက်စစ်ရန်|ပြောဆိုသောဘာသာစကားများ|မည်သည့်အရာမဆိုရွေးပါ|ပေါင်းစပ်အဆင့်သတ်မှတ်ချက်|စာရင်းသွင်းရန်|ပရီမီယံ|အသုံးပြုနေသောစစ်ထုတ်မှုများ",
    "zh": "提供帮助|获取帮助|所有类别|不限|距离|1 公里|我的位置|显示我的位置|显示我的位置：关闭|显示我的位置：大致位置|国籍|按国籍筛选|使用的语言|任选|综合评分|订阅|高级会员|已启用的筛选",
    "cs": "Nabídnout|Získat|Všechny kategorie|Libovolná|Vzdálenost|1 km|Moje poloha|Zobrazit mou polohu|Zobrazit mou polohu: vypnuto|Zobrazit mou polohu: přibližně|Národnost|Filtrovat podle národnosti|Mluvené jazyky|Vyberte libovolné|Celkové hodnocení|Předplatit|Premium|Aktivní filtry",
    "da": "Giv|Få|Alle kategorier|Alle|Afstand|1 km|Min placering|Vis min placering|Vis min placering: fra|Vis min placering: cirka|Nationalitet|Filtrer efter nationalitet|Talte sprog|Vælg alle|Samlet bedømmelse|Abonnér|Premium|Aktive filtre",
    "nl": "Geven|Krijgen|Alle categorieën|Alle|Afstand|1 km|Mijn locatie|Mijn locatie tonen|Mijn locatie tonen: uit|Mijn locatie tonen: ongeveer|Nationaliteit|Filteren op nationaliteit|Gesproken talen|Kies een willekeurige|Gecombineerde beoordeling|Abonneren|Premium|Actieve filters",
    "fi": "Anna|Saa|Kaikki luokat|Mikä tahansa|Etäisyys|1 km|Oma sijainti|Näytä sijaintini|Näytä sijaintini: pois|Näytä sijaintini: likimääräinen|Kansalaisuus|Suodata kansalaisuuden mukaan|Puhutut kielet|Valitse mikä tahansa|Yhdistetty arvio|Tilaa|Premium|Aktiiviset suodattimet",
    "fr": "Donner|Recevoir|Toutes les catégories|Tout|Distance|1 km|Ma position|Afficher ma position|Afficher ma position : désactivée|Afficher ma position : approximative|Nationalité|Filtrer par nationalité|Langues parlées|Choisir au choix|Note combinée|S’abonner|Premium|Filtres actifs",
    "de": "Geben|Erhalten|Alle Kategorien|Beliebig|Entfernung|1 km|Mein Standort|Meinen Standort anzeigen|Meinen Standort anzeigen: aus|Meinen Standort anzeigen: ungefähr|Nationalität|Nach Nationalität filtern|Gesprochene Sprachen|Beliebig auswählen|Gesamtbewertung|Abonnieren|Premium|Aktive Filter",
    "el": "Προσφορά|Λήψη|Όλες οι κατηγορίες|Οποιαδήποτε|Απόσταση|1 χλμ.|Η τοποθεσία μου|Εμφάνιση της τοποθεσίας μου|Εμφάνιση της τοποθεσίας μου: ανενεργή|Εμφάνιση της τοποθεσίας μου: κατά προσέγγιση|Εθνικότητα|Φιλτράρισμα ανά εθνικότητα|Ομιλούμενες γλώσσες|Επιλέξτε οποιοδήποτε|Συνδυασμένη βαθμολογία|Εγγραφή|Premium|Ενεργά φίλτρα",
    "gu": "આપો|મેળવો|બધી શ્રેણીઓ|કોઈપણ|અંતર|1 કિમી|મારું સ્થાન|મારું સ્થાન બતાવો|મારું સ્થાન બતાવો: બંધ|મારું સ્થાન બતાવો: અંદાજિત|રાષ્ટ્રીયતા|રાષ્ટ્રીયતા દ્વારા ફિલ્ટર|બોલાતી ભાષાઓ|કોઈપણ પસંદ કરો|સંયુક્ત રેટિંગ|સબ્સ્ક્રાઇબ કરો|પ્રીમિયમ|સક્રિય ફિલ્ટર",
    "he": "לתת|לקבל|כל הקטגוריות|כלשהו|מרחק|1 ק״מ|המיקום שלי|הצגת המיקום שלי|הצגת המיקום שלי: כבוי|הצגת המיקום שלי: משוער|לאום|סינון לפי לאום|שפות מדוברות|בחירה כלשהי|דירוג משולב|הרשמה|Premium|מסננים פעילים",
    "hi": "देना|पाना|सभी श्रेणियाँ|कोई भी|दूरी|1 किमी|मेरी जगह|मेरी जगह दिखाएँ|मेरी जगह दिखाएँ: बंद|मेरी जगह दिखाएँ: अनुमानित|राष्ट्रीयता|राष्ट्रीयता से फ़िल्टर करें|बोली जाने वाली भाषाएँ|कोई भी चुनें|संयुक्त रेटिंग|सदस्यता लें|प्रीमियम|सक्रिय फ़िल्टर",
    "hu": "Adás|Kapás|Minden kategória|Bármelyik|Távolság|1 km|Helyzetem|Helyzetem megjelenítése|Helyzetem megjelenítése: ki|Helyzetem megjelenítése: hozzávetőleges|Állampolgárság|Szűrés állampolgárság szerint|Beszélt nyelvek|Bármelyik kiválasztása|Összesített értékelés|Feliratkozás|Prémium|Aktív szűrők",
    "id": "Memberi|Mendapatkan|Semua kategori|Apa saja|Jarak|1 km|Lokasi saya|Tampilkan lokasi saya|Tampilkan lokasi saya: nonaktif|Tampilkan lokasi saya: perkiraan|Kebangsaan|Filter berdasarkan kebangsaan|Bahasa yang dikuasai|Pilih apa saja|Penilaian gabungan|Berlangganan|Premium|Filter aktif",
    "it": "Dare|Ricevere|Tutte le categorie|Qualsiasi|Distanza|1 km|La mia posizione|Mostra la mia posizione|Mostra la mia posizione: disattivata|Mostra la mia posizione: approssimativa|Nazionalità|Filtra per nazionalità|Lingue parlate|Scegli qualsiasi|Valutazione combinata|Abbonati|Premium|Filtri attivi",
    "ja": "提供|受け取る|すべてのカテゴリー|指定なし|距離|1 km|現在地|現在地を表示|現在地を表示：オフ|現在地を表示：おおよその位置|国籍|国籍で絞り込む|話せる言語|どれでも選択|総合評価|登録|プレミアム|適用中のフィルター",
    "kn": "ನೀಡಿ|ಪಡೆಯಿರಿ|ಎಲ್ಲಾ ವರ್ಗಗಳು|ಯಾವುದಾದರೂ|ದೂರ|1 ಕಿಮೀ|ನನ್ನ ಸ್ಥಳ|ನನ್ನ ಸ್ಥಳ ತೋರಿಸಿ|ನನ್ನ ಸ್ಥಳ ತೋರಿಸಿ: ಆಫ್|ನನ್ನ ಸ್ಥಳ ತೋರಿಸಿ: ಅಂದಾಜು|ರಾಷ್ಟ್ರೀಯತೆ|ರಾಷ್ಟ್ರೀಯತೆಯಂತೆ ಫಿಲ್ಟರ್ ಮಾಡಿ|ಮಾತನಾಡುವ ಭಾಷೆಗಳು|ಯಾವುದಾದರೂ ಆಯ್ಕೆಮಾಡಿ|ಸಂಯೋಜಿತ ರೇಟಿಂಗ್|ಚಂದಾದಾರರಾಗಿ|ಪ್ರೀಮಿಯಂ|ಸಕ್ರಿಯ ಫಿಲ್ಟರ್‌ಗಳು",
    "ko": "제공|받기|모든 분류|전체|거리|1km|내 위치|내 위치 표시|내 위치 표시: 끄기|내 위치 표시: 대략적인 위치|국적|국적으로 필터|사용 언어|원하는 항목 선택|종합 평점|구독|프리미엄|활성 필터",
    "ml": "നൽകുക|നേടുക|എല്ലാ വിഭാഗങ്ങളും|ഏതെങ്കിലും|ദൂരം|1 കി.മീ.|എന്റെ സ്ഥലം|എന്റെ സ്ഥലം കാണിക്കുക|എന്റെ സ്ഥലം കാണിക്കുക: ഓഫ്|എന്റെ സ്ഥലം കാണിക്കുക: ഏകദേശം|ദേശീയത|ദേശീയത പ്രകാരം ഫിൽട്ടർ ചെയ്യുക|സംസാരിക്കുന്ന ഭാഷകൾ|ഏതെങ്കിലും തിരഞ്ഞെടുക്കുക|സംയോജിത റേറ്റിംഗ്|സബ്‌സ്‌ക്രൈബ്|പ്രീമിയം|സജീവ ഫിൽട്ടറുകൾ",
    "mr": "देणे|मिळवणे|सर्व श्रेणी|कोणतेही|अंतर|1 किमी|माझे स्थान|माझे स्थान दाखवा|माझे स्थान दाखवा: बंद|माझे स्थान दाखवा: अंदाजे|राष्ट्रीयत्व|राष्ट्रीयत्वानुसार फिल्टर|बोलल्या जाणाऱ्या भाषा|कोणतेही निवडा|एकत्रित रेटिंग|सदस्यता घ्या|प्रीमियम|सक्रिय फिल्टर",
    "ne": "दिनुहोस्|पाउनुहोस्|सबै श्रेणीहरू|जुनसुकै|दूरी|1 किमी|मेरो स्थान|मेरो स्थान देखाउनुहोस्|मेरो स्थान देखाउनुहोस्: बन्द|मेरो स्थान देखाउनुहोस्: अनुमानित|राष्ट्रियता|राष्ट्रियता अनुसार फिल्टर|बोलिने भाषाहरू|जुनसुकै छान्नुहोस्|संयुक्त मूल्याङ्कन|सदस्यता लिनुहोस्|प्रिमियम|सक्रिय फिल्टरहरू",
    "fa": "ارائه|دریافت|همه دسته‌ها|هرکدام|فاصله|۱ کیلومتر|موقعیت من|نمایش موقعیت من|نمایش موقعیت من: خاموش|نمایش موقعیت من: تقریبی|ملیت|فیلتر بر اساس ملیت|زبان‌های گفتاری|هرکدام را انتخاب کنید|امتیاز ترکیبی|اشتراک|ویژه|فیلترهای فعال",
    "pl": "Daj|Otrzymaj|Wszystkie kategorie|Dowolna|Odległość|1 km|Moja lokalizacja|Pokaż moją lokalizację|Pokaż moją lokalizację: wyłączona|Pokaż moją lokalizację: przybliżona|Narodowość|Filtruj według narodowości|Języki mówione|Wybierz dowolne|Łączna ocena|Subskrybuj|Premium|Aktywne filtry",
    "pt": "Dar|Receber|Todas as categorias|Qualquer|Distância|1 km|A minha localização|Mostrar a minha localização|Mostrar a minha localização: desativada|Mostrar a minha localização: aproximada|Nacionalidade|Filtrar por nacionalidade|Idiomas falados|Escolha qualquer|Classificação combinada|Subscrever|Premium|Filtros ativos",
    "ro": "Oferă|Primește|Toate categoriile|Oricare|Distanță|1 km|Locația mea|Arată locația mea|Arată locația mea: dezactivată|Arată locația mea: aproximativă|Naționalitate|Filtrează după naționalitate|Limbi vorbite|Alege oricare|Evaluare combinată|Abonează-te|Premium|Filtre active",
    "es": "Dar|Recibir|Todas las categorías|Cualquiera|Distancia|1 km|Mi ubicación|Mostrar mi ubicación|Mostrar mi ubicación: desactivada|Mostrar mi ubicación: aproximada|Nacionalidad|Filtrar por nacionalidad|Idiomas hablados|Elige cualquiera|Valoración combinada|Suscribirse|Premium|Filtros activos",
    "sw": "Toa|Pokea|Aina zote|Yoyote|Umbali|1 km|Mahali nilipo|Onyesha mahali nilipo|Onyesha mahali nilipo: zima|Onyesha mahali nilipo: takriban|Utaifa|Chuja kwa utaifa|Lugha zinazozungumzwa|Chagua yoyote|Ukadiriaji wa pamoja|Jiandikishe|Premium|Vichujio vinavyotumika",
    "sv": "Ge|Få|Alla kategorier|Valfri|Avstånd|1 km|Min plats|Visa min plats|Visa min plats: av|Visa min plats: ungefärlig|Nationalitet|Filtrera efter nationalitet|Talade språk|Välj valfritt|Samlat betyg|Prenumerera|Premium|Aktiva filter",
    "ta": "கொடு|பெறு|அனைத்து வகைகள்|ஏதேனும்|தூரம்|1 கிமீ|எனது இடம்|எனது இடத்தைக் காட்டு|எனது இடத்தைக் காட்டு: முடக்கு|எனது இடத்தைக் காட்டு: தோராயம்|தேசியம்|தேசியத்தின் அடிப்படையில் வடிகட்டு|பேசும் மொழிகள்|ஏதேனும் ஒன்றைத் தேர்ந்தெடு|ஒருங்கிணைந்த மதிப்பீடு|சந்தா செலுத்து|பிரீமியம்|செயலில் உள்ள வடிகட்டிகள்",
    "te": "ఇవ్వండి|పొందండి|అన్ని వర్గాలు|ఏదైనా|దూరం|1 కి.మీ.|నా స్థానం|నా స్థానాన్ని చూపండి|నా స్థానాన్ని చూపండి: ఆఫ్|నా స్థానాన్ని చూపండి: సుమారు|జాతీయత|జాతీయతతో ఫిల్టర్ చేయండి|మాట్లాడే భాషలు|ఏదైనా ఎంచుకోండి|సంయుక్త రేటింగ్|సబ్‌స్క్రైబ్ చేయండి|ప్రీమియం|క్రియాశీల ఫిల్టర్‌లు",
    "th": "ให้|รับ|ทุกหมวดหมู่|ใดก็ได้|ระยะทาง|1 กม.|ตำแหน่งของฉัน|แสดงตำแหน่งของฉัน|แสดงตำแหน่งของฉัน: ปิด|แสดงตำแหน่งของฉัน: โดยประมาณ|สัญชาติ|กรองตามสัญชาติ|ภาษาที่พูด|เลือกอะไรก็ได้|คะแนนรวม|สมัครสมาชิก|พรีเมียม|ตัวกรองที่ใช้งานอยู่",
    "tr": "Ver|Al|Tüm kategoriler|Herhangi biri|Mesafe|1 km|Konumum|Konumumu göster|Konumumu göster: kapalı|Konumumu göster: yaklaşık|Uyruk|Uyruğa göre filtrele|Konuşulan diller|Herhangi birini seç|Birleşik puan|Abone ol|Premium|Etkin filtreler",
    "vi": "Cho đi|Nhận|Tất cả danh mục|Bất kỳ|Khoảng cách|1 km|Vị trí của tôi|Hiển thị vị trí của tôi|Hiển thị vị trí của tôi: tắt|Hiển thị vị trí của tôi: gần đúng|Quốc tịch|Lọc theo quốc tịch|Ngôn ngữ sử dụng|Chọn bất kỳ|Đánh giá tổng hợp|Đăng ký|Premium|Bộ lọc đang hoạt động",
}

SEARCH_FILTER_SUMMARY_KEYS: tuple[str, ...] = (
    "Category: {value}",
    "Reward: {value}",
    "Place: {value}",
    "Nationality: {value}",
    "Speaks {value}",
    "Rating {value}%",
    "{count} categories selected",
    "{distance} km",
    "{distance}+ km",
)

if set(SEARCH_FILTER_KEYS[:1]) != {"Events"} or set(
    SEARCH_FILTER_KEYS[1:24]
) != {CATEGORY_LABELS[value] for value in TASK_CATEGORIES}:
    raise ValueError("Search filter taxonomy source inventory is invalid")

SEARCH_FILTER_ROWS: dict[str, str] = {
    "am": "ክስተቶች|ተርጓሚ|የመጀመሪያ እርዳታ|ጥበብ|ግብርና|አሳዳጊ|ግንባታ|ምግብ ማብሰል|ጽዳት|የእጅ ሥራ|ጤና እንክብካቤ|ጉልበት ሥራ|ሕጋዊ|መካኒክ|ሚዲያ|ሙዚቃ|ሽያጭ|መንፈሳዊነት|ስፖርት|ማስተማር|ቴክኒሻን|ቱሪዝም|ወርክሾፕ|ሌላ|ማንኛውም ሽልማት|ገንዘብ|ምሳ|እራት|ማረፊያ|የተመሩ ጉብኝቶች|ወርክሾፖች|ትምህርቶች|አማርኛ|እንግሊዝኛ|ስፓኒሽ|ፈረንሳይኛ|ፖርቱጋልኛ|ጀርመንኛ|ጣሊያንኛ|ዓረብኛ|ሂንዲ|ቻይንኛ|ጃፓንኛ|በማንኛውም ጊዜ|ዛሬ መስመር ላይ|በዚህ ሳምንት መስመር ላይ|በዚህ ወር መስመር ላይ",
    "ar": "الفعاليات|مترجم|إسعافات أولية|فنون|زراعة|مقدّم رعاية|إنشاءات|طاهٍ|تنظيف|أعمال يدوية|رعاية صحية|أعمال يدوية|قانوني|ميكانيكي|إعلام|موسيقى|مبيعات|روحانية|رياضة|تدريس|فني|سياحة|ورشة عمل|أخرى|أي مكافأة|مال|غداء|عشاء|إقامة|جولات إرشادية|ورش عمل|دروس|الأمهرية|الإنجليزية|الإسبانية|الفرنسية|البرتغالية|الألمانية|الإيطالية|العربية|الهندية|الصينية|اليابانية|أي وقت|متصل اليوم|متصل هذا الأسبوع|متصل هذا الشهر",
    "bn": "অনুষ্ঠান|অনুবাদক|প্রাথমিক চিকিৎসা|শিল্পকলা|কৃষি|যত্নদাতা|নির্মাণ|রাঁধুনি|পরিষ্কার|হস্তশিল্প|স্বাস্থ্যসেবা|শ্রম|আইন|মেকানিক|মিডিয়া|সঙ্গীত|বিক্রয়|আধ্যাত্মিকতা|খেলাধুলা|শিক্ষাদান|প্রযুক্তিবিদ|পর্যটন|কর্মশালা|অন্যান্য|যেকোনো পুরস্কার|অর্থ|দুপুরের খাবার|রাতের খাবার|থাকার ব্যবস্থা|গাইডসহ ভ্রমণ|কর্মশালা|পাঠ|আমহারিক|ইংরেজি|স্প্যানিশ|ফরাসি|পর্তুগিজ|জার্মান|ইতালীয়|আরবি|হিন্দি|চীনা|জাপানি|যেকোনো সময়|আজ অনলাইনে|এই সপ্তাহে অনলাইনে|এই মাসে অনলাইনে",
    "my": "ပွဲများ|ဘာသာပြန်သူ|ရှေးဦးသူနာပြု|အနုပညာ|စိုက်ပျိုးရေး|စောင့်ရှောက်သူ|ဆောက်လုပ်ရေး|ချက်ပြုတ်သူ|သန့်ရှင်းရေး|လက်မှုပညာ|ကျန်းမာရေးစောင့်ရှောက်မှု|လုပ်အား|ဥပဒေ|စက်ပြင်|မီဒီယာ|ဂီတ|အရောင်း|စိတ်ဝိညာဉ်ရေးရာ|အားကစား|သင်ကြားရေး|နည်းပညာရှင်|ခရီးသွားလုပ်ငန်း|အလုပ်ရုံ|အခြား|မည်သည့်ဆုမဆို|ငွေ|နေ့လယ်စာ|ညစာ|တည်းခိုနေရာ|လမ်းညွှန်ခရီးစဉ်|အလုပ်ရုံများ|သင်ခန်းစာများ|အမ်ဟာရစ်|အင်္ဂလိပ်|စပိန်|ပြင်သစ်|ပေါ်တူဂီ|ဂျာမန်|အီတလီ|အာရဗီ|ဟိန္ဒီ|တရုတ်|ဂျပန်|အချိန်မရွေး|ယနေ့အွန်လိုင်း|ယခုအပတ်အွန်လိုင်း|ယခုလအတွင်းအွန်လိုင်း",
    "zh": "活动|翻译|急救|艺术|农业|护理|建筑|烹饪|清洁|手工艺|医疗保健|劳务|法律|机械维修|媒体|音乐|销售|灵性|体育|教学|技术服务|旅游|工作坊|其他|任意奖励|金钱|午餐|晚餐|住宿|导览|工作坊|课程|阿姆哈拉语|英语|西班牙语|法语|葡萄牙语|德语|意大利语|阿拉伯语|印地语|中文|日语|不限时间|今天在线|本周在线|本月在线",
    "cs": "Události|Překladatel|První pomoc|Umění|Zemědělství|Pečovatel|Stavebnictví|Kuchař|Úklid|Řemeslná práce|Zdravotní péče|Práce|Právo|Mechanik|Média|Hudba|Prodej|Duchovno|Sport|Výuka|Technik|Cestovní ruch|Dílna|Ostatní|Libovolná odměna|Peníze|Oběd|Večeře|Ubytování|Komentované prohlídky|Workshopy|Lekce|Amharština|Angličtina|Španělština|Francouzština|Portugalština|Němčina|Italština|Arabština|Hindština|Čínština|Japonština|Kdykoli|Online dnes|Online tento týden|Online tento měsíc",
    "da": "Begivenheder|Oversætter|Førstehjælp|Kunst|Landbrug|Omsorgsperson|Byggeri|Kok|Rengøring|Håndværk|Sundhedspleje|Arbejde|Jura|Mekaniker|Medier|Musik|Salg|Spiritualitet|Sport|Undervisning|Tekniker|Turisme|Workshop|Andet|Enhver belønning|Penge|Frokost|Aftensmad|Overnatning|Guidede ture|Workshops|Undervisning|Amharisk|Engelsk|Spansk|Fransk|Portugisisk|Tysk|Italiensk|Arabisk|Hindi|Kinesisk|Japansk|Når som helst|Online i dag|Online denne uge|Online denne måned",
    "nl": "Evenementen|Vertaler|Eerste hulp|Kunst|Landbouw|Verzorger|Bouw|Kok|Schoonmaak|Handwerk|Gezondheidszorg|Arbeid|Juridisch|Monteur|Media|Muziek|Verkoop|Spiritualiteit|Sport|Lesgeven|Technicus|Toerisme|Workshop|Overig|Elke beloning|Geld|Lunch|Diner|Accommodatie|Rondleidingen|Workshops|Lessen|Amhaars|Engels|Spaans|Frans|Portugees|Duits|Italiaans|Arabisch|Hindi|Chinees|Japans|Altijd|Vandaag online|Deze week online|Deze maand online",
    "fi": "Tapahtumat|Kääntäjä|Ensiapu|Taide|Maatalous|Hoitaja|Rakentaminen|Kokki|Siivous|Käsityö|Terveydenhuolto|Työ|Laki|Mekaanikko|Media|Musiikki|Myynti|Hengellisyys|Urheilu|Opetus|Teknikko|Matkailu|Työpaja|Muu|Mikä tahansa palkkio|Raha|Lounas|Illallinen|Majoitus|Opastetut kierrokset|Työpajat|Oppitunnit|Amhara|Englanti|Espanja|Ranska|Portugali|Saksa|Italia|Arabia|Hindi|Kiina|Japani|Milloin tahansa|Verkossa tänään|Verkossa tällä viikolla|Verkossa tässä kuussa",
    "fr": "Événements|Traducteur|Premiers secours|Arts|Agriculture|Aidant|Construction|Cuisine|Ménage|Artisanat|Santé|Travail manuel|Juridique|Mécanique|Médias|Musique|Vente|Spiritualité|Sport|Enseignement|Technicien|Tourisme|Atelier|Autre|Toute récompense|Argent|Déjeuner|Dîner|Hébergement|Visites guidées|Ateliers|Cours|Amharique|Anglais|Espagnol|Français|Portugais|Allemand|Italien|Arabe|Hindi|Chinois|Japonais|À tout moment|En ligne aujourd’hui|En ligne cette semaine|En ligne ce mois-ci",
    "de": "Veranstaltungen|Übersetzer|Erste Hilfe|Kunst|Landwirtschaft|Betreuung|Bauwesen|Kochen|Reinigung|Handwerk|Gesundheitswesen|Arbeit|Recht|Mechanik|Medien|Musik|Verkauf|Spiritualität|Sport|Unterricht|Technik|Tourismus|Workshop|Sonstiges|Beliebige Belohnung|Geld|Mittagessen|Abendessen|Unterkunft|Geführte Touren|Workshops|Unterricht|Amharisch|Englisch|Spanisch|Französisch|Portugiesisch|Deutsch|Italienisch|Arabisch|Hindi|Chinesisch|Japanisch|Jederzeit|Heute online|Diese Woche online|Diesen Monat online",
    "el": "Εκδηλώσεις|Μεταφραστής|Πρώτες βοήθειες|Τέχνες|Γεωργία|Φροντιστής|Κατασκευές|Μάγειρας|Καθαρισμός|Χειροτεχνία|Υγειονομική περίθαλψη|Εργασία|Νομικά|Μηχανικός|Μέσα ενημέρωσης|Μουσική|Πωλήσεις|Πνευματικότητα|Αθλητισμός|Διδασκαλία|Τεχνικός|Τουρισμός|Εργαστήριο|Άλλο|Οποιαδήποτε ανταμοιβή|Χρήματα|Μεσημεριανό|Δείπνο|Διαμονή|Ξεναγήσεις|Εργαστήρια|Μαθήματα|Αμαρικά|Αγγλικά|Ισπανικά|Γαλλικά|Πορτογαλικά|Γερμανικά|Ιταλικά|Αραβικά|Χίντι|Κινεζικά|Ιαπωνικά|Οποτεδήποτε|Σε σύνδεση σήμερα|Σε σύνδεση αυτή την εβδομάδα|Σε σύνδεση αυτόν τον μήνα",
    "gu": "કાર્યક્રમો|અનુવાદક|પ્રાથમિક સારવાર|કળા|કૃષિ|સંભાળકર્તા|બાંધકામ|રસોઈયા|સફાઈ|હસ્તકલા|આરોગ્યસંભાળ|મજૂરી|કાનૂની|મિકેનિક|મીડિયા|સંગીત|વેચાણ|આધ્યાત્મિકતા|રમતગમત|શિક્ષણ|ટેકનિશિયન|પ્રવાસન|કાર્યશાળા|અન્ય|કોઈપણ પુરસ્કાર|પૈસા|બપોરનું ભોજન|રાત્રિભોજન|રહેઠાણ|માર્ગદર્શિત પ્રવાસ|કાર્યશાળાઓ|પાઠ|અમ્હારિક|અંગ્રેજી|સ્પેનિશ|ફ્રેન્ચ|પોર્ટુગીઝ|જર્મન|ઇટાલિયન|અરબી|હિન્દી|ચાઇનીઝ|જાપાનીઝ|કોઈપણ સમયે|આજે ઑનલાઇન|આ અઠવાડિયે ઑનલાઇન|આ મહિને ઑનલાઇન",
    "he": "אירועים|מתרגם|עזרה ראשונה|אמנות|חקלאות|מטפל|בנייה|בישול|ניקיון|מלאכת יד|בריאות|עבודת כפיים|משפטים|מכונאות|מדיה|מוזיקה|מכירות|רוחניות|ספורט|הוראה|טכנאי|תיירות|סדנה|אחר|כל תגמול|כסף|ארוחת צהריים|ארוחת ערב|לינה|סיורים מודרכים|סדנאות|שיעורים|אמהרית|אנגלית|ספרדית|צרפתית|פורטוגזית|גרמנית|איטלקית|ערבית|הינדית|סינית|יפנית|בכל עת|מחובר היום|מחובר השבוע|מחובר החודש",
    "hi": "कार्यक्रम|अनुवादक|प्राथमिक उपचार|कला|कृषि|देखभालकर्ता|निर्माण|रसोइया|सफ़ाई|हस्तशिल्प|स्वास्थ्य सेवा|श्रम|कानूनी|मैकेनिक|मीडिया|संगीत|बिक्री|आध्यात्मिकता|खेल|शिक्षण|तकनीशियन|पर्यटन|कार्यशाला|अन्य|कोई भी इनाम|पैसा|दोपहर का भोजन|रात का खाना|आवास|निर्देशित यात्राएँ|कार्यशालाएँ|पाठ|अम्हारिक|अंग्रेज़ी|स्पेनिश|फ़्रेंच|पुर्तगाली|जर्मन|इतालवी|अरबी|हिंदी|चीनी|जापानी|कभी भी|आज ऑनलाइन|इस सप्ताह ऑनलाइन|इस महीने ऑनलाइन",
    "hu": "Események|Fordító|Elsősegély|Művészet|Mezőgazdaság|Gondozó|Építőipar|Főzés|Takarítás|Kézművesség|Egészségügy|Munka|Jogi|Szerelő|Média|Zene|Értékesítés|Spiritualitás|Sport|Oktatás|Technikus|Turizmus|Műhely|Egyéb|Bármilyen jutalom|Pénz|Ebéd|Vacsora|Szállás|Vezetett túrák|Műhelyek|Leckék|Amhara|Angol|Spanyol|Francia|Portugál|Német|Olasz|Arab|Hindi|Kínai|Japán|Bármikor|Ma online|Ezen a héten online|Ebben a hónapban online",
    "id": "Acara|Penerjemah|Pertolongan pertama|Seni|Pertanian|Pengasuh|Konstruksi|Memasak|Kebersihan|Kerajinan|Kesehatan|Tenaga kerja|Hukum|Mekanik|Media|Musik|Penjualan|Spiritualitas|Olahraga|Mengajar|Teknisi|Pariwisata|Lokakarya|Lainnya|Hadiah apa pun|Uang|Makan siang|Makan malam|Akomodasi|Tur berpemandu|Lokakarya|Pelajaran|Amharik|Inggris|Spanyol|Prancis|Portugis|Jerman|Italia|Arab|Hindi|Tionghoa|Jepang|Kapan saja|Online hari ini|Online minggu ini|Online bulan ini",
    "it": "Eventi|Traduttore|Primo soccorso|Arti|Agricoltura|Assistente|Edilizia|Cucina|Pulizia|Artigianato|Assistenza sanitaria|Lavoro manuale|Legale|Meccanico|Media|Musica|Vendite|Spiritualità|Sport|Insegnamento|Tecnico|Turismo|Laboratorio|Altro|Qualsiasi ricompensa|Denaro|Pranzo|Cena|Alloggio|Visite guidate|Laboratori|Lezioni|Amarico|Inglese|Spagnolo|Francese|Portoghese|Tedesco|Italiano|Arabo|Hindi|Cinese|Giapponese|In qualsiasi momento|Online oggi|Online questa settimana|Online questo mese",
    "ja": "イベント|翻訳|応急手当|芸術|農業|介護|建設|料理|清掃|手工芸|医療|労働|法律|整備|メディア|音楽|販売|精神性|スポーツ|教育|技術者|観光|ワークショップ|その他|任意の謝礼|金銭|昼食|夕食|宿泊|ガイド付きツアー|ワークショップ|レッスン|アムハラ語|英語|スペイン語|フランス語|ポルトガル語|ドイツ語|イタリア語|アラビア語|ヒンディー語|中国語|日本語|いつでも|今日オンライン|今週オンライン|今月オンライン",
    "kn": "ಕಾರ್ಯಕ್ರಮಗಳು|ಅನುವಾದಕ|ಪ್ರಥಮ ಚಿಕಿತ್ಸೆ|ಕಲೆ|ಕೃಷಿ|ಪಾಲನೆ ಮಾಡುವವರು|ನಿರ್ಮಾಣ|ಅಡುಗೆ|ಸ್ವಚ್ಛತೆ|ಕರಕುಶಲ|ಆರೋಗ್ಯ ಸೇವೆ|ಕಾರ್ಮಿಕ ಕೆಲಸ|ಕಾನೂನು|ಮೆಕ್ಯಾನಿಕ್|ಮಾಧ್ಯಮ|ಸಂಗೀತ|ಮಾರಾಟ|ಆಧ್ಯಾತ್ಮಿಕತೆ|ಕ್ರೀಡೆ|ಬೋಧನೆ|ತಂತ್ರಜ್ಞ|ಪ್ರವಾಸೋದ್ಯಮ|ಕಾರ್ಯಾಗಾರ|ಇತರೆ|ಯಾವುದೇ ಬಹುಮಾನ|ಹಣ|ಮಧ್ಯಾಹ್ನದ ಊಟ|ರಾತ್ರಿ ಊಟ|ವಸತಿ|ಮಾರ್ಗದರ್ಶಿತ ಪ್ರವಾಸಗಳು|ಕಾರ್ಯಾಗಾರಗಳು|ಪಾಠಗಳು|ಅಮ್ಹಾರಿಕ್|ಇಂಗ್ಲಿಷ್|ಸ್ಪ್ಯಾನಿಷ್|ಫ್ರೆಂಚ್|ಪೋರ್ಚುಗೀಸ್|ಜರ್ಮನ್|ಇಟಾಲಿಯನ್|ಅರೇಬಿಕ್|ಹಿಂದಿ|ಚೈನೀಸ್|ಜಪಾನೀಸ್|ಯಾವಾಗ ಬೇಕಾದರೂ|ಇಂದು ಆನ್‌ಲೈನ್|ಈ ವಾರ ಆನ್‌ಲೈನ್|ಈ ತಿಂಗಳು ಆನ್‌ಲೈನ್",
    "ko": "이벤트|번역|응급처치|예술|농업|돌봄|건설|요리|청소|공예|의료|노동|법률|정비|미디어|음악|판매|영성|스포츠|교육|기술|관광|워크숍|기타|모든 보상|금전|점심|저녁|숙박|가이드 투어|워크숍|수업|암하라어|영어|스페인어|프랑스어|포르투갈어|독일어|이탈리아어|아랍어|힌디어|중국어|일본어|언제든지|오늘 온라인|이번 주 온라인|이번 달 온라인",
    "ml": "പരിപാടികൾ|വിവർത്തകൻ|പ്രഥമശുശ്രൂഷ|കലകൾ|കൃഷി|പരിചാരകൻ|നിർമ്മാണം|പാചകം|ശുചീകരണം|കരകൗശലം|ആരോഗ്യപരിചരണം|തൊഴിൽ|നിയമം|മെക്കാനിക്|മാധ്യമം|സംഗീതം|വിൽപ്പന|ആത്മീയത|കായികം|പഠിപ്പിക്കൽ|സാങ്കേതികവിദഗ്ധൻ|ടൂറിസം|ശിൽപശാല|മറ്റുള്ളവ|ഏതെങ്കിലും പ്രതിഫലം|പണം|ഉച്ചഭക്ഷണം|അത്താഴം|താമസം|വഴികാട്ടിയുള്ള യാത്രകൾ|ശിൽപശാലകൾ|പാഠങ്ങൾ|അംഹാരിക്|ഇംഗ്ലീഷ്|സ്പാനിഷ്|ഫ്രഞ്ച്|പോർച്ചുഗീസ്|ജർമ്മൻ|ഇറ്റാലിയൻ|അറബിക്|ഹിന്ദി|ചൈനീസ്|ജാപ്പനീസ്|എപ്പോൾ വേണമെങ്കിലും|ഇന്ന് ഓൺലൈൻ|ഈ ആഴ്ച ഓൺലൈൻ|ഈ മാസം ഓൺലൈൻ",
    "mr": "कार्यक्रम|अनुवादक|प्रथमोपचार|कला|शेती|काळजीवाहक|बांधकाम|स्वयंपाक|स्वच्छता|हस्तकला|आरोग्यसेवा|मजुरी|कायदा|मेकॅनिक|माध्यमे|संगीत|विक्री|अध्यात्म|खेळ|अध्यापन|तंत्रज्ञ|पर्यटन|कार्यशाळा|इतर|कोणतेही बक्षीस|पैसे|दुपारचे जेवण|रात्रीचे जेवण|निवास|मार्गदर्शित सहली|कार्यशाळा|धडे|अम्हारिक|इंग्रजी|स्पॅनिश|फ्रेंच|पोर्तुगीज|जर्मन|इटालियन|अरबी|हिंदी|चिनी|जपानी|कधीही|आज ऑनलाइन|या आठवड्यात ऑनलाइन|या महिन्यात ऑनलाइन",
    "ne": "कार्यक्रमहरू|अनुवादक|प्राथमिक उपचार|कला|कृषि|हेरचाहकर्ता|निर्माण|पकाउने|सफाइ|हस्तकला|स्वास्थ्य सेवा|श्रम|कानुनी|मेकानिक|मिडिया|सङ्गीत|बिक्री|आध्यात्मिकता|खेलकुद|शिक्षण|प्राविधिक|पर्यटन|कार्यशाला|अन्य|जुनसुकै पुरस्कार|पैसा|दिउँसोको खाना|रातिको खाना|आवास|मार्गदर्शित भ्रमण|कार्यशालाहरू|पाठहरू|अम्हारिक|अङ्ग्रेजी|स्पेनी|फ्रेन्च|पोर्तुगाली|जर्मन|इटालियन|अरबी|हिन्दी|चिनियाँ|जापानी|जुनसुकै बेला|आज अनलाइन|यस हप्ता अनलाइन|यस महिना अनलाइन",
    "fa": "رویدادها|مترجم|کمک‌های اولیه|هنر|کشاورزی|مراقب|ساخت‌وساز|آشپزی|نظافت|صنایع دستی|مراقبت سلامت|کارگری|حقوقی|مکانیک|رسانه|موسیقی|فروش|معنویت|ورزش|آموزش|تکنسین|گردشگری|کارگاه|سایر|هر پاداشی|پول|ناهار|شام|اقامت|تورهای راهنما‌دار|کارگاه‌ها|درس‌ها|امهری|انگلیسی|اسپانیایی|فرانسوی|پرتغالی|آلمانی|ایتالیایی|عربی|هندی|چینی|ژاپنی|هر زمان|امروز آنلاین|این هفته آنلاین|این ماه آنلاین",
    "pl": "Wydarzenia|Tłumacz|Pierwsza pomoc|Sztuka|Rolnictwo|Opiekun|Budownictwo|Gotowanie|Sprzątanie|Rękodzieło|Opieka zdrowotna|Praca fizyczna|Prawo|Mechanik|Media|Muzyka|Sprzedaż|Duchowość|Sport|Nauczanie|Technik|Turystyka|Warsztat|Inne|Dowolna nagroda|Pieniądze|Lunch|Kolacja|Zakwaterowanie|Wycieczki z przewodnikiem|Warsztaty|Lekcje|Amharski|Angielski|Hiszpański|Francuski|Portugalski|Niemiecki|Włoski|Arabski|Hindi|Chiński|Japoński|W dowolnym czasie|Online dzisiaj|Online w tym tygodniu|Online w tym miesiącu",
    "pt": "Eventos|Tradutor|Primeiros socorros|Artes|Agricultura|Cuidador|Construção|Cozinha|Limpeza|Artesanato|Cuidados de saúde|Trabalho manual|Jurídico|Mecânico|Media|Música|Vendas|Espiritualidade|Desporto|Ensino|Técnico|Turismo|Oficina|Outro|Qualquer recompensa|Dinheiro|Almoço|Jantar|Alojamento|Visitas guiadas|Oficinas|Aulas|Amárico|Inglês|Espanhol|Francês|Português|Alemão|Italiano|Árabe|Hindi|Chinês|Japonês|A qualquer momento|Online hoje|Online esta semana|Online este mês",
    "ro": "Evenimente|Traducător|Prim ajutor|Arte|Agricultură|Îngrijitor|Construcții|Bucătar|Curățenie|Meșteșuguri|Sănătate|Muncă|Juridic|Mecanic|Media|Muzică|Vânzări|Spiritualitate|Sport|Predare|Tehnician|Turism|Atelier|Altele|Orice recompensă|Bani|Prânz|Cină|Cazare|Tururi ghidate|Ateliere|Lecții|Amharică|Engleză|Spaniolă|Franceză|Portugheză|Germană|Italiană|Arabă|Hindi|Chineză|Japoneză|Oricând|Online astăzi|Online săptămâna aceasta|Online luna aceasta",
    "es": "Eventos|Traductor|Primeros auxilios|Artes|Agricultura|Cuidador|Construcción|Cocina|Limpieza|Artesanía|Atención sanitaria|Trabajo manual|Legal|Mecánico|Medios|Música|Ventas|Espiritualidad|Deportes|Enseñanza|Técnico|Turismo|Taller|Otro|Cualquier recompensa|Dinero|Almuerzo|Cena|Alojamiento|Visitas guiadas|Talleres|Clases|Amárico|Inglés|Español|Francés|Portugués|Alemán|Italiano|Árabe|Hindi|Chino|Japonés|En cualquier momento|En línea hoy|En línea esta semana|En línea este mes",
    "sw": "Matukio|Mtafsiri|Huduma ya kwanza|Sanaa|Kilimo|Mlezi|Ujenzi|Mpishi|Usafi|Ufundi|Huduma ya afya|Kazi|Sheria|Fundi|Vyombo vya habari|Muziki|Mauzo|Uroho|Michezo|Ufundishaji|Fundi stadi|Utalii|Warsha|Nyingine|Zawadi yoyote|Pesa|Chakula cha mchana|Chakula cha jioni|Malazi|Ziara zinazoongozwa|Warsha|Masomo|Kiamhari|Kiingereza|Kihispania|Kifaransa|Kireno|Kijerumani|Kiitaliano|Kiarabu|Kihindi|Kichina|Kijapani|Wakati wowote|Mtandaoni leo|Mtandaoni wiki hii|Mtandaoni mwezi huu",
    "sv": "Evenemang|Översättare|Första hjälpen|Konst|Jordbruk|Vårdare|Bygg|Matlagning|Städning|Hantverk|Hälsovård|Arbete|Juridik|Mekaniker|Media|Musik|Försäljning|Andlighet|Sport|Undervisning|Tekniker|Turism|Workshop|Annat|Valfri belöning|Pengar|Lunch|Middag|Boende|Guidade turer|Workshops|Lektioner|Amhariska|Engelska|Spanska|Franska|Portugisiska|Tyska|Italienska|Arabiska|Hindi|Kinesiska|Japanska|När som helst|Online idag|Online den här veckan|Online den här månaden",
    "ta": "நிகழ்வுகள்|மொழிபெயர்ப்பாளர்|முதலுதவி|கலை|விவசாயம்|பராமரிப்பாளர்|கட்டுமானம்|சமையல்|சுத்தம்|கைவினை|சுகாதாரம்|உழைப்பு|சட்டம்|இயந்திரவியல்|ஊடகம்|இசை|விற்பனை|ஆன்மீகம்|விளையாட்டு|கற்பித்தல்|தொழில்நுட்ப நிபுணர்|சுற்றுலா|பட்டறை|மற்றவை|எந்த வெகுமதியும்|பணம்|மதிய உணவு|இரவு உணவு|தங்குமிடம்|வழிகாட்டிய சுற்றுப்பயணங்கள்|பட்டறைகள்|பாடங்கள்|அம்ஹாரிக்|ஆங்கிலம்|ஸ்பானிஷ்|பிரெஞ்சு|போர்த்துகீசியம்|ஜெர்மன்|இத்தாலியன்|அரபு|இந்தி|சீனம்|ஜப்பானியம்|எப்போது வேண்டுமானாலும்|இன்று ஆன்லைனில்|இந்த வாரம் ஆன்லைனில்|இந்த மாதம் ஆன்லைனில்",
    "te": "కార్యక్రమాలు|అనువాదకుడు|ప్రథమ చికిత్స|కళలు|వ్యవసాయం|సంరక్షకుడు|నిర్మాణం|వంట|శుభ్రత|హస్తకళ|ఆరోగ్య సంరక్షణ|శ్రమ|చట్టపరమైన|మెకానిక్|మీడియా|సంగీతం|అమ్మకాలు|ఆధ్యాత్మికత|క్రీడలు|బోధన|సాంకేతిక నిపుణుడు|పర్యాటకం|వర్క్‌షాప్|ఇతరాలు|ఏదైనా బహుమతి|డబ్బు|మధ్యాహ్న భోజనం|రాత్రి భోజనం|వసతి|మార్గదర్శక పర్యటనలు|వర్క్‌షాప్‌లు|పాఠాలు|అమ్హారిక్|ఇంగ్లీష్|స్పానిష్|ఫ్రెంచ్|పోర్చుగీస్|జర్మన్|ఇటాలియన్|అరబిక్|హిందీ|చైనీస్|జపనీస్|ఎప్పుడైనా|ఈరోజు ఆన్‌లైన్|ఈ వారం ఆన్‌లైన్|ఈ నెల ఆన్‌లైన్",
    "th": "กิจกรรม|นักแปล|ปฐมพยาบาล|ศิลปะ|เกษตรกรรม|ผู้ดูแล|ก่อสร้าง|ทำอาหาร|ทำความสะอาด|งานฝีมือ|ดูแลสุขภาพ|แรงงาน|กฎหมาย|ช่างยนต์|สื่อ|ดนตรี|การขาย|จิตวิญญาณ|กีฬา|การสอน|ช่างเทคนิค|การท่องเที่ยว|เวิร์กช็อป|อื่น ๆ|รางวัลใดก็ได้|เงิน|อาหารกลางวัน|อาหารเย็น|ที่พัก|ทัวร์พร้อมไกด์|เวิร์กช็อป|บทเรียน|อัมฮาริก|อังกฤษ|สเปน|ฝรั่งเศส|โปรตุเกส|เยอรมัน|อิตาลี|อาหรับ|ฮินดี|จีน|ญี่ปุ่น|เวลาใดก็ได้|ออนไลน์วันนี้|ออนไลน์สัปดาห์นี้|ออนไลน์เดือนนี้",
    "tr": "Etkinlikler|Çevirmen|İlk yardım|Sanat|Tarım|Bakıcı|İnşaat|Aşçılık|Temizlik|El işi|Sağlık hizmeti|İşçilik|Hukuk|Mekanik|Medya|Müzik|Satış|Maneviyat|Spor|Öğretim|Teknisyen|Turizm|Atölye|Diğer|Herhangi bir ödül|Para|Öğle yemeği|Akşam yemeği|Konaklama|Rehberli turlar|Atölyeler|Dersler|Amharca|İngilizce|İspanyolca|Fransızca|Portekizce|Almanca|İtalyanca|Arapça|Hintçe|Çince|Japonca|Her zaman|Bugün çevrimiçi|Bu hafta çevrimiçi|Bu ay çevrimiçi",
    "vi": "Sự kiện|Phiên dịch viên|Sơ cứu|Nghệ thuật|Nông nghiệp|Người chăm sóc|Xây dựng|Nấu ăn|Dọn dẹp|Thủ công|Chăm sóc sức khỏe|Lao động|Pháp lý|Thợ máy|Truyền thông|Âm nhạc|Bán hàng|Tâm linh|Thể thao|Giảng dạy|Kỹ thuật viên|Du lịch|Hội thảo|Khác|Bất kỳ phần thưởng nào|Tiền|Bữa trưa|Bữa tối|Chỗ ở|Chuyến tham quan có hướng dẫn|Hội thảo|Bài học|Amhara|Tiếng Anh|Tiếng Tây Ban Nha|Tiếng Pháp|Tiếng Bồ Đào Nha|Tiếng Đức|Tiếng Ý|Tiếng Ả Rập|Tiếng Hindi|Tiếng Trung|Tiếng Nhật|Bất cứ lúc nào|Trực tuyến hôm nay|Trực tuyến tuần này|Trực tuyến tháng này",
}

SEARCH_FILTER_SUMMARY_ROWS: dict[str, str] = {
    "am": "ምድብ፦ {value}|ሽልማት፦ {value}|ቦታ፦ {value}|ዜግነት፦ {value}|የሚናገረው {value}|ደረጃ {value}%|{count} ምድቦች ተመርጠዋል|{distance} ኪ.ሜ.|{distance}+ ኪ.ሜ.",
    "ar": "الفئة: {value}|المكافأة: {value}|المكان: {value}|الجنسية: {value}|يتحدث {value}|التقييم {value}%|تم تحديد {count} فئات|{distance} كم|{distance}+ كم",
    "bn": "বিভাগ: {value}|পুরস্কার: {value}|স্থান: {value}|জাতীয়তা: {value}|{value} ভাষায় কথা বলেন|রেটিং {value}%|{count}টি বিভাগ নির্বাচিত|{distance} কিমি|{distance}+ কিমি",
    "my": "အမျိုးအစား - {value}|ဆု - {value}|နေရာ - {value}|နိုင်ငံသား - {value}|{value} ဘာသာစကားပြောသည်|အဆင့် {value}%|ရွေးထားသော အမျိုးအစား {count} ခု|{distance} ကီလိုမီတာ|{distance}+ ကီလိုမီတာ",
    "zh": "类别：{value}|奖励：{value}|地点：{value}|国籍：{value}|会说{value}语|评分 {value}%|已选{count}个类别|{distance}公里|{distance}+公里",
    "cs": "Kategorie: {value}|Odměna: {value}|Místo: {value}|Národnost: {value}|Mluví jazykem {value}|Hodnocení {value}%|Vybrané kategorie: {count}|{distance} km|{distance}+ km",
    "da": "Kategori: {value}|Belønning: {value}|Sted: {value}|Nationalitet: {value}|Taler {value}|Bedømmelse {value}%|{count} kategorier valgt|{distance} km|{distance}+ km",
    "nl": "Categorie: {value}|Beloning: {value}|Plaats: {value}|Nationaliteit: {value}|Spreekt {value}|Beoordeling {value}%|{count} categorieën geselecteerd|{distance} km|{distance}+ km",
    "fi": "Luokka: {value}|Palkkio: {value}|Paikka: {value}|Kansalaisuus: {value}|Puhuu kieltä {value}|Arvio {value}%|Valitut luokat: {count}|{distance} km|{distance}+ km",
    "fr": "Catégorie : {value}|Récompense : {value}|Lieu : {value}|Nationalité : {value}|Parle {value}|Évaluation {value}%|{count} catégories sélectionnées|{distance} km|{distance}+ km",
    "de": "Kategorie: {value}|Belohnung: {value}|Ort: {value}|Nationalität: {value}|Spricht {value}|Bewertung {value}%|{count} Kategorien ausgewählt|{distance} km|{distance}+ km",
    "el": "Κατηγορία: {value}|Ανταμοιβή: {value}|Τοποθεσία: {value}|Εθνικότητα: {value}|Μιλά {value}|Αξιολόγηση {value}%|Επιλέχθηκαν {count} κατηγορίες|{distance} χλμ.|{distance}+ χλμ.",
    "gu": "શ્રેણી: {value}|પુરસ્કાર: {value}|સ્થળ: {value}|રાષ્ટ્રીયતા: {value}|{value} બોલે છે|રેટિંગ {value}%|{count} શ્રેણીઓ પસંદ કરેલી|{distance} કિમી|{distance}+ કિમી",
    "he": "קטגוריה: {value}|תגמול: {value}|מקום: {value}|לאום: {value}|דובר {value}|דירוג {value}%|נבחרו {count} קטגוריות|{distance} ק״מ|{distance}+ ק״מ",
    "hi": "श्रेणी: {value}|इनाम: {value}|स्थान: {value}|राष्ट्रीयता: {value}|{value} बोलते हैं|रेटिंग {value}%|{count} श्रेणियाँ चुनी गईं|{distance} किमी|{distance}+ किमी",
    "hu": "Kategória: {value}|Jutalom: {value}|Hely: {value}|Állampolgárság: {value}|Beszéli: {value}|Értékelés {value}%|{count} kategória kiválasztva|{distance} km|{distance}+ km",
    "id": "Kategori: {value}|Imbalan: {value}|Tempat: {value}|Kebangsaan: {value}|Berbicara {value}|Penilaian {value}%|{count} kategori dipilih|{distance} km|{distance}+ km",
    "it": "Categoria: {value}|Ricompensa: {value}|Luogo: {value}|Nazionalità: {value}|Parla {value}|Valutazione {value}%|{count} categorie selezionate|{distance} km|{distance}+ km",
    "ja": "カテゴリー：{value}|報酬：{value}|場所：{value}|国籍：{value}|{value}語を話す|評価 {value}%|{count}個のカテゴリーを選択|{distance} km|{distance}+ km",
    "kn": "ವರ್ಗ: {value}|ಪ್ರತಿಫಲ: {value}|ಸ್ಥಳ: {value}|ರಾಷ್ಟ್ರೀಯತೆ: {value}|{value} ಮಾತನಾಡುತ್ತಾರೆ|ರೇಟಿಂಗ್ {value}%|ಆಯ್ದ ವರ್ಗಗಳು: {count}|{distance} ಕಿಮೀ|{distance}+ ಕಿಮೀ",
    "ko": "분류: {value}|보상: {value}|장소: {value}|국적: {value}|{value}어를 구사함|평점 {value}%|선택한 분류 {count}개|{distance}km|{distance}+km",
    "ml": "വിഭാഗം: {value}|പ്രതിഫലം: {value}|സ്ഥലം: {value}|ദേശീയത: {value}|{value} സംസാരിക്കുന്നു|റേറ്റിംഗ് {value}%|തിരഞ്ഞെടുത്ത വിഭാഗങ്ങൾ {count}|{distance} കി.മീ.|{distance}+ കി.മീ.",
    "mr": "श्रेणी: {value}|बक्षीस: {value}|ठिकाण: {value}|राष्ट्रीयत्व: {value}|{value} बोलतात|रेटिंग {value}%|निवडलेल्या श्रेणी {count}|{distance} किमी|{distance}+ किमी",
    "ne": "श्रेणी: {value}|पुरस्कार: {value}|स्थान: {value}|राष्ट्रियता: {value}|{value} बोल्नुहुन्छ|मूल्याङ्कन {value}%|छानिएका श्रेणी {count}|{distance} किमी|{distance}+ किमी",
    "fa": "دسته‌بندی: {value}|پاداش: {value}|مکان: {value}|ملیت: {value}|صحبت می‌کند {value}|امتیاز {value}%|{count} دسته انتخاب شد|{distance} کیلومتر|{distance}+ کیلومتر",
    "pl": "Kategoria: {value}|Nagroda: {value}|Miejsce: {value}|Narodowość: {value}|Mówi: {value}|Ocena {value}%|Wybrane kategorie: {count}|{distance} km|{distance}+ km",
    "pt": "Categoria: {value}|Recompensa: {value}|Local: {value}|Nacionalidade: {value}|Fala {value}|Avaliação {value}%|{count} categorias selecionadas|{distance} km|{distance}+ km",
    "ro": "Categorie: {value}|Recompensă: {value}|Loc: {value}|Naționalitate: {value}|Vorbește {value}|Evaluare {value}%|{count} categorii selectate|{distance} km|{distance}+ km",
    "es": "Categoría: {value}|Recompensa: {value}|Lugar: {value}|Nacionalidad: {value}|Habla {value}|Valoración {value}%|{count} categorías seleccionadas|{distance} km|{distance}+ km",
    "sw": "Aina: {value}|Zawadi: {value}|Mahali: {value}|Utaifa: {value}|Anazungumza {value}|Ukadiriaji {value}%|Aina zilizochaguliwa: {count}|{distance} km|{distance}+ km",
    "sv": "Kategori: {value}|Belöning: {value}|Plats: {value}|Nationalitet: {value}|Talar {value}|Betyg {value}%|{count} kategorier valda|{distance} km|{distance}+ km",
    "ta": "வகை: {value}|வெகுமதி: {value}|இடம்: {value}|தேசியம்: {value}|{value} பேசுகிறார்|மதிப்பீடு {value}%|{count} வகைகள் தேர்ந்தெடுக்கப்பட்டன|{distance} கிமீ|{distance}+ கிமீ",
    "te": "వర్గం: {value}|బహుమతి: {value}|స్థలం: {value}|జాతీయత: {value}|{value} మాట్లాడతారు|రేటింగ్ {value}%|ఎంచుకున్న వర్గాలు {count}|{distance} కి.మీ.|{distance}+ కి.మీ.",
    "th": "หมวดหมู่: {value}|รางวัล: {value}|สถานที่: {value}|สัญชาติ: {value}|พูดภาษา{value}|คะแนน {value}%|เลือก {count} หมวดหมู่|{distance} กม.|{distance}+ กม.",
    "tr": "Kategori: {value}|Ödül: {value}|Yer: {value}|Uyruk: {value}|{value} konuşur|Puan {value}%|{count} kategori seçildi|{distance} km|{distance}+ km",
    "vi": "Danh mục: {value}|Phần thưởng: {value}|Địa điểm: {value}|Quốc tịch: {value}|Nói tiếng {value}|Đánh giá {value}%|Đã chọn {count} danh mục|{distance} km|{distance}+ km",
}


SEARCH_FILTER_CONTROL_KEYS: tuple[str, ...] = (
    "Go — filter people requesting help and their jobs",
    "Get — filter people offering help",
    "Filter people requesting help, or people offering help",
    "Choose one or more search categories, including Events",
    "Search categories and Events",
    "Clear every selected category",
    "Distance in kilometres, zero means any distance",
    "Turn on your Approximate location first",
    "Show results on the map",
    "Show results as a list",
    "Switch between map view and list view",
    "Dismiss Search filters",
    "Filter by reward",
    "Subscribe to unlock the advanced help search options",
    "Filter by when a person was last online",
    "Minimum combined rating percentage",
    "Maximum combined rating percentage",
    "Filter by people who speak {language}",
    "Premium feature",
    "Clear categories",
    "Off",
    "Approx",
    "More filters",
    "Close Search filters",
    "People, jobs, places...",
    "Search: People, Jobs, Places",
    "Save search",
    "Save these search filters as an alert",
    "Clear filters",
    "Clear every filter",
    "Last online",
    "Portuguese",
)

SEARCH_FILTER_CONTROL_ROWS: dict[str, str] = {
    "am": "ስጥ — እርዳታ የሚጠይቁ ሰዎችንና ሥራዎቻቸውን አጣራ|ተቀበል — እርዳታ የሚሰጡ ሰዎችን አጣራ|እርዳታ የሚጠይቁ ወይም የሚሰጡ ሰዎችን አጣራ|ክስተቶችን ጨምሮ አንድ ወይም ከዚያ በላይ ምድቦችን ይምረጡ|የፍለጋ ምድቦች እና ክስተቶች|ሁሉንም የተመረጡ ምድቦች አጽዳ|ርቀት በኪሎሜትር፤ ዜሮ ማንኛውም ርቀት ማለት ነው|መጀመሪያ ግምታዊ አካባቢዎን ያብሩ|ውጤቶችን በካርታ ላይ አሳይ|ውጤቶችን እንደ ዝርዝር አሳይ|በካርታ እና በዝርዝር እይታ መካከል ቀይር|የፍለጋ ማጣሪያዎችን አስወግድ|በሽልማት አጣራ|የላቁ የእርዳታ ፍለጋ አማራጮችን ለመክፈት ይመዝገቡ|ሰውዬው መጨረሻ መቼ በመስመር ላይ እንደነበር አጣራ|ዝቅተኛ ጥምር የደረጃ መቶኛ|ከፍተኛ ጥምር የደረጃ መቶኛ|{language} ቋንቋ በሚናገሩ ሰዎች አጣራ|የፕሪሚየም ባህሪ|ምድቦችን አጽዳ|ጠፍቷል|ግምታዊ|ተጨማሪ ማጣሪያዎች|የፍለጋ ማጣሪያዎችን ዝጋ|ሰዎች፣ ሥራዎች፣ ቦታዎች...|ፈልግ፦ ሰዎች፣ ሥራዎች፣ ቦታዎች|ፍለጋን አስቀምጥ|እነዚህን የፍለጋ ማጣሪያዎች እንደ ማስጠንቀቂያ አስቀምጥ|ማጣሪያዎችን አጽዳ|ሁሉንም ማጣሪያዎች አጽዳ|መጨረሻ በመስመር ላይ|ፖርቱጋልኛ",
    "ar": "قدّم — صفِّ الأشخاص الذين يطلبون المساعدة ومهامهم|احصل — صفِّ الأشخاص الذين يقدمون المساعدة|صفِّ الأشخاص الذين يطلبون المساعدة أو يقدمونها|اختر فئة واحدة أو أكثر، بما فيها الفعاليات|فئات البحث والفعاليات|امسح جميع الفئات المحددة|المسافة بالكيلومترات، والصفر يعني أي مسافة|فعّل موقعك التقريبي أولًا|عرض النتائج على الخريطة|عرض النتائج كقائمة|التبديل بين عرض الخريطة والقائمة|إغلاق فلاتر البحث|تصفية حسب المكافأة|اشترك لفتح خيارات البحث المتقدمة عن المساعدة|تصفية حسب آخر ظهور للشخص|الحد الأدنى لنسبة التقييم المجمّع|الحد الأقصى لنسبة التقييم المجمّع|تصفية الأشخاص الذين يتحدثون {language}|ميزة مميزة|مسح الفئات|إيقاف|تقريبي|المزيد من الفلاتر|إغلاق فلاتر البحث|أشخاص، مهام، أماكن...|ابحث عن: أشخاص، مهام، أماكن|حفظ البحث|احفظ فلاتر البحث هذه كتنبيه|مسح الفلاتر|مسح جميع الفلاتر|آخر ظهور|البرتغالية",
    "bn": "দিতে চান — সাহায্যপ্রার্থী ব্যক্তি ও তাঁদের কাজ ফিল্টার করুন|পেতে চান — সাহায্যদাতাদের ফিল্টার করুন|সাহায্যপ্রার্থী বা সাহায্যদাতাদের ফিল্টার করুন|ইভেন্টসহ এক বা একাধিক বিভাগ বেছে নিন|অনুসন্ধানের বিভাগ ও ইভেন্ট|নির্বাচিত সব বিভাগ মুছুন|কিলোমিটারে দূরত্ব; শূন্য মানে যেকোনো দূরত্ব|আগে আনুমানিক অবস্থান চালু করুন|মানচিত্রে ফলাফল দেখান|তালিকা হিসেবে ফলাফল দেখান|মানচিত্র ও তালিকা দৃশ্যের মধ্যে বদলান|অনুসন্ধান ফিল্টার বন্ধ করুন|পুরস্কার অনুযায়ী ফিল্টার|উন্নত সাহায্য অনুসন্ধান বিকল্প খুলতে সাবস্ক্রাইব করুন|কেউ সর্বশেষ কখন অনলাইনে ছিলেন তা দিয়ে ফিল্টার|সর্বনিম্ন সম্মিলিত রেটিং শতাংশ|সর্বোচ্চ সম্মিলিত রেটিং শতাংশ|{language} ভাষায় কথা বলেন এমন ব্যক্তিদের ফিল্টার করুন|প্রিমিয়াম সুবিধা|বিভাগ মুছুন|বন্ধ|আনুমানিক|আরও ফিল্টার|অনুসন্ধান ফিল্টার বন্ধ করুন|ব্যক্তি, কাজ, স্থান...|অনুসন্ধান: ব্যক্তি, কাজ, স্থান|অনুসন্ধান সংরক্ষণ করুন|এই অনুসন্ধান ফিল্টারগুলো সতর্কতা হিসেবে সংরক্ষণ করুন|ফিল্টার মুছুন|সব ফিল্টার মুছুন|সর্বশেষ অনলাইন|পর্তুগিজ",
    "my": "ပေးရန် — အကူအညီတောင်းသူများနှင့် ၎င်းတို့၏အလုပ်များကို စစ်ထုတ်ရန်|ရယူရန် — အကူအညီပေးသူများကို စစ်ထုတ်ရန်|အကူအညီတောင်းသူ သို့မဟုတ် ပေးသူများကို စစ်ထုတ်ရန်|ပွဲများအပါအဝင် အမျိုးအစားတစ်ခု သို့မဟုတ် အများအပြားရွေးပါ|ရှာဖွေမှုအမျိုးအစားများနှင့် ပွဲများ|ရွေးထားသော အမျိုးအစားအားလုံးကို ရှင်းရန်|ကီလိုမီတာဖြင့် အကွာအဝေး၊ သုညသည် မည်သည့်အကွာအဝေးမဆိုဖြစ်သည်|ပထမဆုံး ခန့်မှန်းတည်နေရာကို ဖွင့်ပါ|မြေပုံပေါ်တွင် ရလဒ်များပြရန်|စာရင်းအဖြစ် ရလဒ်များပြရန်|မြေပုံနှင့် စာရင်းမြင်ကွင်းကို ပြောင်းရန်|ရှာဖွေမှုစစ်ထုတ်မှုများကို ပိတ်ရန်|ဆုအလိုက် စစ်ထုတ်ရန်|အဆင့်မြင့်အကူအညီရှာဖွေမှု ရွေးချယ်စရာများဖွင့်ရန် စာရင်းသွင်းပါ|နောက်ဆုံးအွန်လိုင်းရှိခဲ့ချိန်အလိုက် စစ်ထုတ်ရန်|အနည်းဆုံး ပေါင်းစပ်အဆင့်ရာခိုင်နှုန်း|အများဆုံး ပေါင်းစပ်အဆင့်ရာခိုင်နှုန်း|{language} ပြောသောသူများကို စစ်ထုတ်ရန်|ပရီမီယံအင်္ဂါရပ်|အမျိုးအစားများရှင်းရန်|ပိတ်|ခန့်မှန်း|နောက်ထပ်စစ်ထုတ်မှုများ|ရှာဖွေမှုစစ်ထုတ်မှုများပိတ်ရန်|လူများ၊ အလုပ်များ၊ နေရာများ...|ရှာရန်: လူများ၊ အလုပ်များ၊ နေရာများ|ရှာဖွေမှုသိမ်းရန်|ဤရှာဖွေမှုစစ်ထုတ်မှုများကို သတိပေးချက်အဖြစ်သိမ်းရန်|စစ်ထုတ်မှုများရှင်းရန်|စစ်ထုတ်မှုအားလုံးရှင်းရန်|နောက်ဆုံးအွန်လိုင်း|ပေါ်တူဂီဘာသာ",
    "zh": "提供帮助 — 筛选正在求助的人及其任务|获取帮助 — 筛选提供帮助的人|筛选求助者或提供帮助的人|选择一个或多个类别，包括活动|搜索类别和活动|清除所有已选类别|距离单位为公里，零表示不限距离|请先开启大致位置|在地图上显示结果|以列表显示结果|切换地图和列表视图|关闭搜索筛选|按奖励筛选|订阅以解锁高级求助搜索选项|按对方最近上线时间筛选|综合评分最低百分比|综合评分最高百分比|筛选会说{language}的人|高级功能|清除类别|关闭|大致位置|更多筛选|关闭搜索筛选|人物、任务、地点...|搜索：人物、任务、地点|保存搜索|将这些搜索筛选保存为提醒|清除筛选|清除所有筛选|最近上线|葡萄牙语",
    "cs": "Nabídnout — filtrovat lidi žádající o pomoc a jejich úkoly|Získat — filtrovat lidi nabízející pomoc|Filtrovat lidi žádající o pomoc nebo ji nabízející|Vyberte jednu či více kategorií včetně událostí|Kategorie vyhledávání a události|Vymazat všechny vybrané kategorie|Vzdálenost v kilometrech, nula znamená libovolnou vzdálenost|Nejprve zapněte přibližnou polohu|Zobrazit výsledky na mapě|Zobrazit výsledky jako seznam|Přepnout mezi mapou a seznamem|Zavřít filtry hledání|Filtrovat podle odměny|Předplaťte si pokročilé možnosti hledání pomoci|Filtrovat podle poslední aktivity uživatele|Minimální procento celkového hodnocení|Maximální procento celkového hodnocení|Filtrovat lidi, kteří mluví jazykem {language}|Prémiová funkce|Vymazat kategorie|Vypnuto|Přibližně|Další filtry|Zavřít filtry hledání|Lidé, úkoly, místa...|Hledat: lidé, úkoly, místa|Uložit hledání|Uložit tyto filtry hledání jako upozornění|Vymazat filtry|Vymazat všechny filtry|Naposledy online|Portugalština",
    "da": "Giv — filtrér personer, der søger hjælp, og deres opgaver|Få — filtrér personer, der tilbyder hjælp|Filtrér personer, der søger eller tilbyder hjælp|Vælg en eller flere kategorier, herunder begivenheder|Søgekategorier og begivenheder|Ryd alle valgte kategorier|Afstand i kilometer; nul betyder enhver afstand|Slå først din omtrentlige placering til|Vis resultater på kortet|Vis resultater som en liste|Skift mellem kort- og listevisning|Luk søgefiltre|Filtrér efter belønning|Abonnér for at låse op for avancerede hjælpesøgningsmuligheder|Filtrér efter hvornår en person sidst var online|Mindste samlede bedømmelsesprocent|Største samlede bedømmelsesprocent|Filtrér efter personer, der taler {language}|Premiumfunktion|Ryd kategorier|Fra|Omtrent|Flere filtre|Luk søgefiltre|Personer, opgaver, steder...|Søg: personer, opgaver, steder|Gem søgning|Gem disse søgefiltre som en besked|Ryd filtre|Ryd alle filtre|Sidst online|Portugisisk",
    "nl": "Geven — filter mensen die hulp zoeken en hun taken|Krijgen — filter mensen die hulp aanbieden|Filter mensen die hulp zoeken of aanbieden|Kies een of meer categorieën, inclusief evenementen|Zoekcategorieën en evenementen|Wis alle geselecteerde categorieën|Afstand in kilometers; nul betekent elke afstand|Schakel eerst je geschatte locatie in|Resultaten op de kaart tonen|Resultaten als lijst tonen|Wissel tussen kaart- en lijstweergave|Zoekfilters sluiten|Filteren op beloning|Abonneer om geavanceerde zoekopties voor hulp te ontgrendelen|Filter op wanneer iemand voor het laatst online was|Minimumpercentage gecombineerde beoordeling|Maximumpercentage gecombineerde beoordeling|Filter op mensen die {language} spreken|Premiumfunctie|Categorieën wissen|Uit|Geschat|Meer filters|Zoekfilters sluiten|Mensen, taken, plaatsen...|Zoeken: mensen, taken, plaatsen|Zoekopdracht opslaan|Deze zoekfilters opslaan als melding|Filters wissen|Alle filters wissen|Laatst online|Portugees",
    "fi": "Anna — suodata apua pyytävät henkilöt ja heidän tehtävänsä|Saa — suodata apua tarjoavat henkilöt|Suodata apua pyytävät tai tarjoavat henkilöt|Valitse yksi tai useampi luokka, myös tapahtumat|Hakuluokat ja tapahtumat|Tyhjennä kaikki valitut luokat|Etäisyys kilometreinä; nolla tarkoittaa mitä tahansa etäisyyttä|Ota ensin käyttöön likimääräinen sijainti|Näytä tulokset kartalla|Näytä tulokset luettelona|Vaihda kartta- ja luettelonäkymän välillä|Sulje hakusuodattimet|Suodata palkkion mukaan|Tilaa ja avaa edistyneet avun hakuvaihtoehdot|Suodata henkilön viimeisimmän verkkonäkyvyyden mukaan|Yhdistetyn arvion vähimmäisprosentti|Yhdistetyn arvion enimmäisprosentti|Suodata {language}-kieltä puhuvat henkilöt|Premium-ominaisuus|Tyhjennä luokat|Pois|Likimääräinen|Lisää suodattimia|Sulje hakusuodattimet|Ihmiset, tehtävät, paikat...|Hae: ihmiset, tehtävät, paikat|Tallenna haku|Tallenna nämä hakusuodattimet hälytykseksi|Tyhjennä suodattimet|Tyhjennä kaikki suodattimet|Viimeksi verkossa|Portugali",
    "fr": "Donner — filtrer les personnes qui demandent de l’aide et leurs tâches|Recevoir — filtrer les personnes qui proposent de l’aide|Filtrer les personnes qui demandent ou proposent de l’aide|Choisissez une ou plusieurs catégories, événements inclus|Catégories de recherche et événements|Effacer toutes les catégories sélectionnées|Distance en kilomètres, zéro signifie toute distance|Activez d’abord votre position approximative|Afficher les résultats sur la carte|Afficher les résultats sous forme de liste|Passer de la carte à la liste|Fermer les filtres de recherche|Filtrer par récompense|Abonnez-vous pour débloquer les options avancées de recherche d’aide|Filtrer selon la dernière connexion d’une personne|Pourcentage minimal de l’évaluation combinée|Pourcentage maximal de l’évaluation combinée|Filtrer les personnes qui parlent {language}|Fonctionnalité Premium|Effacer les catégories|Désactivé|Approximatif|Plus de filtres|Fermer les filtres de recherche|Personnes, tâches, lieux...|Rechercher : personnes, tâches, lieux|Enregistrer la recherche|Enregistrer ces filtres comme alerte|Effacer les filtres|Effacer tous les filtres|Dernière connexion|Portugais",
    "de": "Geben — Personen mit Hilfegesuchen und ihre Aufgaben filtern|Erhalten — Personen filtern, die Hilfe anbieten|Personen filtern, die Hilfe suchen oder anbieten|Eine oder mehrere Kategorien einschließlich Veranstaltungen auswählen|Suchkategorien und Veranstaltungen|Alle ausgewählten Kategorien löschen|Entfernung in Kilometern, null bedeutet beliebige Entfernung|Aktiviere zuerst deinen ungefähren Standort|Ergebnisse auf der Karte anzeigen|Ergebnisse als Liste anzeigen|Zwischen Karten- und Listenansicht wechseln|Suchfilter schließen|Nach Belohnung filtern|Abonniere, um erweiterte Hilfesuchoptionen freizuschalten|Nach dem letzten Online-Zeitpunkt einer Person filtern|Minimaler Prozentsatz der Gesamtbewertung|Maximaler Prozentsatz der Gesamtbewertung|Personen filtern, die {language} sprechen|Premium-Funktion|Kategorien löschen|Aus|Ungefähr|Weitere Filter|Suchfilter schließen|Personen, Aufgaben, Orte...|Suchen: Personen, Aufgaben, Orte|Suche speichern|Diese Suchfilter als Benachrichtigung speichern|Filter löschen|Alle Filter löschen|Zuletzt online|Portugiesisch",
    "el": "Προσφορά — φιλτράρισμα ατόμων που ζητούν βοήθεια και των εργασιών τους|Λήψη — φιλτράρισμα ατόμων που προσφέρουν βοήθεια|Φιλτράρισμα ατόμων που ζητούν ή προσφέρουν βοήθεια|Επιλέξτε μία ή περισσότερες κατηγορίες, μαζί με εκδηλώσεις|Κατηγορίες αναζήτησης και εκδηλώσεις|Εκκαθάριση όλων των επιλεγμένων κατηγοριών|Απόσταση σε χιλιόμετρα, το μηδέν σημαίνει οποιαδήποτε απόσταση|Ενεργοποιήστε πρώτα την κατά προσέγγιση τοποθεσία σας|Εμφάνιση αποτελεσμάτων στον χάρτη|Εμφάνιση αποτελεσμάτων ως λίστα|Εναλλαγή προβολής χάρτη και λίστας|Κλείσιμο φίλτρων αναζήτησης|Φιλτράρισμα βάσει ανταμοιβής|Εγγραφείτε για να ξεκλειδώσετε τις σύνθετες επιλογές αναζήτησης βοήθειας|Φιλτράρισμα βάσει τελευταίας σύνδεσης|Ελάχιστο ποσοστό συνδυασμένης αξιολόγησης|Μέγιστο ποσοστό συνδυασμένης αξιολόγησης|Φιλτράρισμα ατόμων που μιλούν {language}|Λειτουργία Premium|Εκκαθάριση κατηγοριών|Ανενεργό|Κατά προσέγγιση|Περισσότερα φίλτρα|Κλείσιμο φίλτρων αναζήτησης|Άτομα, εργασίες, μέρη...|Αναζήτηση: άτομα, εργασίες, μέρη|Αποθήκευση αναζήτησης|Αποθήκευση αυτών των φίλτρων ως ειδοποίηση|Εκκαθάριση φίλτρων|Εκκαθάριση όλων των φίλτρων|Τελευταία σύνδεση|Πορτογαλικά",
    "gu": "આપો — મદદ માગતા લોકો અને તેમની કામગીરી ફિલ્ટર કરો|મેળવો — મદદ આપતા લોકોને ફિલ્ટર કરો|મદદ માગતા અથવા આપતા લોકોને ફિલ્ટર કરો|ઇવેન્ટ્સ સહિત એક અથવા વધુ શ્રેણીઓ પસંદ કરો|શોધ શ્રેણીઓ અને ઇવેન્ટ્સ|પસંદ કરેલી બધી શ્રેણીઓ સાફ કરો|કિલોમીટરમાં અંતર; શૂન્ય એટલે કોઈપણ અંતર|પહેલાં તમારું અંદાજિત સ્થાન ચાલુ કરો|નકશા પર પરિણામો બતાવો|પરિણામો યાદી તરીકે બતાવો|નકશા અને યાદી દૃશ્ય વચ્ચે બદલો|શોધ ફિલ્ટર બંધ કરો|પુરસ્કાર પ્રમાણે ફિલ્ટર કરો|અદ્યતન મદદ શોધ વિકલ્પો ખોલવા સબ્સ્ક્રાઇબ કરો|વ્યક્તિ છેલ્લે ક્યારે ઑનલાઇન હતી તે પ્રમાણે ફિલ્ટર કરો|ન્યૂનતમ સંયુક્ત રેટિંગ ટકાવારી|મહત્તમ સંયુક્ત રેટિંગ ટકાવારી|{language} બોલતા લોકોને ફિલ્ટર કરો|પ્રીમિયમ સુવિધા|શ્રેણીઓ સાફ કરો|બંધ|અંદાજિત|વધુ ફિલ્ટર|શોધ ફિલ્ટર બંધ કરો|લોકો, કામ, સ્થળો...|શોધો: લોકો, કામ, સ્થળો|શોધ સાચવો|આ શોધ ફિલ્ટરને ચેતવણી તરીકે સાચવો|ફિલ્ટર સાફ કરો|બધા ફિલ્ટર સાફ કરો|છેલ્લે ઑનલાઇન|પોર્ટુગીઝ",
    "he": "תן — סנן אנשים המבקשים עזרה ואת המשימות שלהם|קבל — סנן אנשים המציעים עזרה|סנן אנשים המבקשים עזרה או מציעים אותה|בחרו קטגוריה אחת או יותר, כולל אירועים|קטגוריות חיפוש ואירועים|נקה את כל הקטגוריות שנבחרו|מרחק בקילומטרים; אפס פירושו כל מרחק|הפעילו תחילה את המיקום המשוער|הצג תוצאות במפה|הצג תוצאות כרשימה|החלף בין תצוגת מפה לרשימה|סגור מסנני חיפוש|סנן לפי תגמול|הירשמו כדי לפתוח אפשרויות חיפוש עזרה מתקדמות|סנן לפי הפעם האחרונה שאדם היה מחובר|אחוז דירוג משולב מינימלי|אחוז דירוג משולב מרבי|סנן אנשים הדוברים {language}|תכונת Premium|נקה קטגוריות|כבוי|משוער|מסננים נוספים|סגור מסנני חיפוש|אנשים, משימות, מקומות...|חיפוש: אנשים, משימות, מקומות|שמור חיפוש|שמור את מסנני החיפוש האלה כהתראה|נקה מסננים|נקה את כל המסננים|נראה לאחרונה|פורטוגזית",
    "hi": "दें — मदद माँगने वाले लोगों और उनके कामों को फ़िल्टर करें|पाएँ — मदद देने वाले लोगों को फ़िल्टर करें|मदद माँगने या देने वाले लोगों को फ़िल्टर करें|इवेंट सहित एक या अधिक श्रेणियाँ चुनें|खोज श्रेणियाँ और इवेंट|चुनी गई सभी श्रेणियाँ हटाएँ|दूरी किलोमीटर में; शून्य का अर्थ कोई भी दूरी|पहले अपना अनुमानित स्थान चालू करें|मानचित्र पर परिणाम दिखाएँ|परिणाम सूची के रूप में दिखाएँ|मानचित्र और सूची दृश्य के बीच बदलें|खोज फ़िल्टर बंद करें|इनाम के अनुसार फ़िल्टर करें|उन्नत सहायता खोज विकल्प खोलने के लिए सदस्यता लें|किसी व्यक्ति के आख़िरी बार ऑनलाइन होने के अनुसार फ़िल्टर करें|न्यूनतम संयुक्त रेटिंग प्रतिशत|अधिकतम संयुक्त रेटिंग प्रतिशत|{language} बोलने वाले लोगों को फ़िल्टर करें|प्रीमियम सुविधा|श्रेणियाँ साफ़ करें|बंद|अनुमानित|और फ़िल्टर|खोज फ़िल्टर बंद करें|लोग, काम, स्थान...|खोजें: लोग, काम, स्थान|खोज सहेजें|इन खोज फ़िल्टर को अलर्ट के रूप में सहेजें|फ़िल्टर साफ़ करें|सभी फ़िल्टर साफ़ करें|अंतिम बार ऑनलाइन|पुर्तगाली",
    "hu": "Adás — segítséget kérő emberek és feladataik szűrése|Kapás — segítséget kínáló emberek szűrése|Segítséget kérő vagy kínáló emberek szűrése|Válassz egy vagy több kategóriát, az eseményeket is beleértve|Keresési kategóriák és események|Az összes kiválasztott kategória törlése|Távolság kilométerben; a nulla bármilyen távolságot jelent|Először kapcsold be a hozzávetőleges helyzetet|Eredmények megjelenítése a térképen|Eredmények megjelenítése listaként|Váltás a térkép- és listanézet között|Keresési szűrők bezárása|Szűrés jutalom szerint|Iratkozz fel a speciális segítségkeresési lehetőségek feloldásához|Szűrés a személy legutóbbi online ideje szerint|Minimális összesített értékelési százalék|Maximális összesített értékelési százalék|{language} nyelven beszélő emberek szűrése|Prémium funkció|Kategóriák törlése|Ki|Hozzávetőleges|További szűrők|Keresési szűrők bezárása|Emberek, feladatok, helyek...|Keresés: emberek, feladatok, helyek|Keresés mentése|Ezeknek a keresési szűrőknek a mentése értesítésként|Szűrők törlése|Összes szűrő törlése|Legutóbb online|Portugál",
    "id": "Memberi — filter orang yang meminta bantuan dan tugasnya|Mendapatkan — filter orang yang menawarkan bantuan|Filter orang yang meminta atau menawarkan bantuan|Pilih satu atau beberapa kategori, termasuk acara|Kategori pencarian dan acara|Hapus semua kategori yang dipilih|Jarak dalam kilometer; nol berarti jarak apa pun|Aktifkan lokasi perkiraan terlebih dahulu|Tampilkan hasil di peta|Tampilkan hasil sebagai daftar|Beralih antara tampilan peta dan daftar|Tutup filter pencarian|Filter berdasarkan hadiah|Berlangganan untuk membuka opsi pencarian bantuan lanjutan|Filter berdasarkan kapan seseorang terakhir online|Persentase penilaian gabungan minimum|Persentase penilaian gabungan maksimum|Filter orang yang berbicara {language}|Fitur Premium|Hapus kategori|Nonaktif|Perkiraan|Filter lainnya|Tutup filter pencarian|Orang, tugas, tempat...|Cari: orang, tugas, tempat|Simpan pencarian|Simpan filter pencarian ini sebagai pemberitahuan|Hapus filter|Hapus semua filter|Terakhir online|Bahasa Portugis",
    "it": "Dare — filtra le persone che chiedono aiuto e le loro attività|Ricevere — filtra le persone che offrono aiuto|Filtra le persone che chiedono o offrono aiuto|Scegli una o più categorie, inclusi gli eventi|Categorie di ricerca ed eventi|Cancella tutte le categorie selezionate|Distanza in chilometri; zero significa qualsiasi distanza|Attiva prima la posizione approssimativa|Mostra i risultati sulla mappa|Mostra i risultati come elenco|Passa dalla mappa all’elenco|Chiudi filtri di ricerca|Filtra per ricompensa|Abbonati per sbloccare le opzioni avanzate di ricerca aiuto|Filtra in base all’ultimo accesso della persona|Percentuale minima della valutazione combinata|Percentuale massima della valutazione combinata|Filtra le persone che parlano {language}|Funzione Premium|Cancella categorie|Disattivato|Approssimativo|Altri filtri|Chiudi filtri di ricerca|Persone, attività, luoghi...|Cerca: persone, attività, luoghi|Salva ricerca|Salva questi filtri come avviso|Cancella filtri|Cancella tutti i filtri|Ultimo accesso|Portoghese",
    "ja": "提供 — 助けを求める人とその仕事を絞り込む|受け取る — 助けを提供する人を絞り込む|助けを求める人、または提供する人を絞り込む|イベントを含むカテゴリを1つ以上選択|検索カテゴリーとイベント|選択したカテゴリーをすべてクリア|距離（キロメートル）。0は距離を指定しない設定|先におおよその位置情報をオンにしてください|地図に結果を表示|結果をリストで表示|地図表示とリスト表示を切り替え|検索フィルターを閉じる|謝礼で絞り込む|登録して高度なヘルプ検索オプションを利用|最終オンライン日時で絞り込む|総合評価の最低割合|総合評価の最高割合|{language}を話す人で絞り込む|プレミアム機能|カテゴリーをクリア|オフ|おおよそ|その他のフィルター|検索フィルターを閉じる|人、仕事、場所...|検索：人、仕事、場所|検索を保存|この検索条件を通知として保存|フィルターをクリア|すべてのフィルターをクリア|最終オンライン|ポルトガル語",
    "kn": "ನೀಡಿ — ಸಹಾಯ ಕೇಳುವವರನ್ನು ಮತ್ತು ಅವರ ಕೆಲಸಗಳನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ|ಪಡೆಯಿರಿ — ಸಹಾಯ ನೀಡುವವರನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ|ಸಹಾಯ ಕೇಳುವ ಅಥವಾ ನೀಡುವವರನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ|ಕಾರ್ಯಕ್ರಮಗಳು ಸೇರಿದಂತೆ ಒಂದು ಅಥವಾ ಹೆಚ್ಚಿನ ವರ್ಗಗಳನ್ನು ಆಯ್ಕೆಮಾಡಿ|ಹುಡುಕಾಟ ವರ್ಗಗಳು ಮತ್ತು ಕಾರ್ಯಕ್ರಮಗಳು|ಆಯ್ಕೆಮಾಡಿದ ಎಲ್ಲಾ ವರ್ಗಗಳನ್ನು ತೆರವುಗೊಳಿಸಿ|ಕಿಲೋಮೀಟರ್‌ಗಳಲ್ಲಿ ದೂರ; ಶೂನ್ಯ ಎಂದರೆ ಯಾವುದೇ ದೂರ|ಮೊದಲು ಅಂದಾಜು ಸ್ಥಳವನ್ನು ಆನ್ ಮಾಡಿ|ನಕ್ಷೆಯಲ್ಲಿ ಫಲಿತಾಂಶಗಳನ್ನು ತೋರಿಸಿ|ಪಟ್ಟಿಯಾಗಿ ಫಲಿತಾಂಶ ತೋರಿಸಿ|ನಕ್ಷೆ ಮತ್ತು ಪಟ್ಟಿಯ ವೀಕ್ಷಣೆ ನಡುವೆ ಬದಲಿಸಿ|ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಮುಚ್ಚಿ|ಪ್ರತಿಫಲದಂತೆ ಫಿಲ್ಟರ್ ಮಾಡಿ|ಸುಧಾರಿತ ಸಹಾಯ ಹುಡುಕಾಟ ಆಯ್ಕೆಗಳನ್ನು ತೆರೆಯಲು ಚಂದಾದಾರರಾಗಿ|ವ್ಯಕ್ತಿ ಕೊನೆಯದಾಗಿ ಆನ್‌ಲೈನ್‌ನಲ್ಲಿದ್ದ ಸಮಯದಂತೆ ಫಿಲ್ಟರ್ ಮಾಡಿ|ಕನಿಷ್ಠ ಸಂಯೋಜಿತ ರೇಟಿಂಗ್ ಶೇಕಡಾವಾರು|ಗರಿಷ್ಠ ಸಂಯೋಜಿತ ರೇಟಿಂಗ್ ಶೇಕಡಾವಾರು|{language} ಮಾತನಾಡುವವರನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ|ಪ್ರೀಮಿಯಂ ವೈಶಿಷ್ಟ್ಯ|ವರ್ಗಗಳನ್ನು ತೆರವುಗೊಳಿಸಿ|ಆಫ್|ಅಂದಾಜು|ಹೆಚ್ಚಿನ ಫಿಲ್ಟರ್‌ಗಳು|ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಮುಚ್ಚಿ|ಜನರು, ಕೆಲಸಗಳು, ಸ್ಥಳಗಳು...|ಹುಡುಕಿ: ಜನರು, ಕೆಲಸಗಳು, ಸ್ಥಳಗಳು|ಹುಡುಕಾಟ ಉಳಿಸಿ|ಈ ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಎಚ್ಚರಿಕೆಯಾಗಿ ಉಳಿಸಿ|ಫಿಲ್ಟರ್ ತೆರವುಗೊಳಿಸಿ|ಎಲ್ಲಾ ಫಿಲ್ಟರ್ ತೆರವುಗೊಳಿಸಿ|ಕೊನೆಯದಾಗಿ ಆನ್‌ಲೈನ್|ಪೋರ್ಚುಗೀಸ್",
    "ko": "제공 — 도움을 요청하는 사람과 작업 필터링|받기 — 도움을 제공하는 사람 필터링|도움을 요청하거나 제공하는 사람 필터링|이벤트를 포함해 하나 이상의 분류 선택|검색 분류 및 이벤트|선택한 모든 분류 지우기|거리(킬로미터), 0은 모든 거리|먼저 대략적인 위치를 켜세요|지도에서 결과 보기|목록으로 결과 보기|지도 보기와 목록 보기 전환|검색 필터 닫기|보상으로 필터링|구독하여 고급 도움 검색 옵션 잠금 해제|마지막 접속 시간으로 필터링|종합 평점 최소 비율|종합 평점 최대 비율|{language}를 구사하는 사람 필터링|프리미엄 기능|분류 지우기|끄기|대략적인 위치|필터 더 보기|검색 필터 닫기|사람, 작업, 장소...|검색: 사람, 작업, 장소|검색 저장|이 검색 필터를 알림으로 저장|필터 지우기|모든 필터 지우기|마지막 온라인|포르투갈어",
    "ml": "നൽകുക — സഹായം ചോദിക്കുന്നവരെയും അവരുടെ ജോലികളെയും ഫിൽട്ടർ ചെയ്യുക|നേടുക — സഹായം നൽകുന്നവരെ ഫിൽട്ടർ ചെയ്യുക|സഹായം ചോദിക്കുന്നവരെയോ നൽകുന്നവരെയോ ഫിൽട്ടർ ചെയ്യുക|ഇവന്റുകൾ ഉൾപ്പെടെ ഒന്നോ അതിലധികമോ വിഭാഗങ്ങൾ തിരഞ്ഞെടുക്കുക|തിരയൽ വിഭാഗങ്ങളും ഇവന്റുകളും|തിരഞ്ഞെടുത്ത എല്ലാ വിഭാഗങ്ങളും മായ്ക്കുക|ദൂരം കിലോമീറ്ററിൽ; പൂജ്യം ഏത് ദൂരവും സൂചിപ്പിക്കുന്നു|ആദ്യം ഏകദേശ സ്ഥാനം ഓണാക്കുക|മാപ്പിൽ ഫലങ്ങൾ കാണിക്കുക|ഫലങ്ങൾ പട്ടികയായി കാണിക്കുക|മാപ്പ്, പട്ടിക കാഴ്ചകൾക്കിടയിൽ മാറുക|തിരയൽ ഫിൽട്ടറുകൾ അടയ്ക്കുക|പ്രതിഫലം അനുസരിച്ച് ഫിൽട്ടർ ചെയ്യുക|വിപുലമായ സഹായ തിരയൽ ഓപ്ഷനുകൾ തുറക്കാൻ സബ്‌സ്‌ക്രൈബ് ചെയ്യുക|ഒരാൾ അവസാനമായി ഓൺലൈനിലായ സമയം അനുസരിച്ച് ഫിൽട്ടർ ചെയ്യുക|കുറഞ്ഞ സംയോജിത റേറ്റിംഗ് ശതമാനം|പരമാവധി സംയോജിത റേറ്റിംഗ് ശതമാനം|{language} സംസാരിക്കുന്നവരെ ഫിൽട്ടർ ചെയ്യുക|പ്രീമിയം സൗകര്യം|വിഭാഗങ്ങൾ മായ്ക്കുക|ഓഫ്|ഏകദേശം|കൂടുതൽ ഫിൽട്ടറുകൾ|തിരയൽ ഫിൽട്ടറുകൾ അടയ്ക്കുക|ആളുകൾ, ജോലികൾ, സ്ഥലങ്ങൾ...|തിരയുക: ആളുകൾ, ജോലികൾ, സ്ഥലങ്ങൾ|തിരയൽ സംരക്ഷിക്കുക|ഈ തിരയൽ ഫിൽട്ടറുകൾ അലേർട്ടായി സംരക്ഷിക്കുക|ഫിൽട്ടറുകൾ മായ്ക്കുക|എല്ലാ ഫിൽട്ടറുകളും മായ്ക്കുക|അവസാനം ഓൺലൈൻ|പോർച്ചുഗീസ്",
    "mr": "देणे — मदत मागणारे लोक आणि त्यांची कामे फिल्टर करा|मिळवणे — मदत देणारे लोक फिल्टर करा|मदत मागणारे किंवा देणारे लोक फिल्टर करा|कार्यक्रमांसह एक किंवा अधिक श्रेणी निवडा|शोध श्रेणी आणि कार्यक्रम|निवडलेल्या सर्व श्रेणी साफ करा|अंतर किलोमीटरमध्ये; शून्य म्हणजे कोणतेही अंतर|आधी अंदाजे स्थान सुरू करा|नकाशावर परिणाम दाखवा|यादी म्हणून परिणाम दाखवा|नकाशा आणि यादी दृश्यांमध्ये बदला|शोध फिल्टर बंद करा|बक्षीसानुसार फिल्टर करा|प्रगत मदत शोध पर्याय उघडण्यासाठी सदस्यता घ्या|व्यक्ती शेवटची ऑनलाइन कधी होती त्यानुसार फिल्टर करा|किमान एकत्रित रेटिंग टक्केवारी|कमाल एकत्रित रेटिंग टक्केवारी|{language} बोलणारे लोक फिल्टर करा|प्रीमियम सुविधा|श्रेणी साफ करा|बंद|अंदाजे|अधिक फिल्टर|शोध फिल्टर बंद करा|लोक, कामे, ठिकाणे...|शोधा: लोक, कामे, ठिकाणे|शोध जतन करा|हे शोध फिल्टर सूचना म्हणून जतन करा|फिल्टर साफ करा|सर्व फिल्टर साफ करा|शेवटचे ऑनलाइन|पोर्तुगीज",
    "ne": "दिनुहोस् — मद्दत माग्ने मानिस र तिनका कामहरू फिल्टर गर्नुहोस्|पाउनुहोस् — मद्दत दिने मानिसहरू फिल्टर गर्नुहोस्|मद्दत माग्ने वा दिने मानिसहरू फिल्टर गर्नुहोस्|कार्यक्रमसहित एक वा बढी श्रेणी छान्नुहोस्|खोज श्रेणी र कार्यक्रमहरू|छानिएका सबै श्रेणी हटाउनुहोस्|दूरी किलोमिटरमा; शून्यले जुनसुकै दूरी जनाउँछ|पहिले अनुमानित स्थान खोल्नुहोस्|नक्सामा नतिजा देखाउनुहोस्|सूचीका रूपमा नतिजा देखाउनुहोस्|नक्सा र सूची दृश्यबीच बदल्नुहोस्|खोज फिल्टर बन्द गर्नुहोस्|पुरस्कारअनुसार फिल्टर गर्नुहोस्|उन्नत सहायता खोज विकल्प खोल्न सदस्यता लिनुहोस्|व्यक्ति पछिल्लो पटक अनलाइन भएको समयअनुसार फिल्टर गर्नुहोस्|न्यूनतम संयुक्त मूल्याङ्कन प्रतिशत|अधिकतम संयुक्त मूल्याङ्कन प्रतिशत|{language} बोल्ने मानिसहरू फिल्टर गर्नुहोस्|प्रिमियम सुविधा|श्रेणी हटाउनुहोस्|बन्द|अनुमानित|थप फिल्टरहरू|खोज फिल्टर बन्द गर्नुहोस्|मानिस, काम, ठाउँ...|खोज्नुहोस्: मानिस, काम, ठाउँ|खोज सुरक्षित गर्नुहोस्|यी खोज फिल्टरलाई सूचनाका रूपमा सुरक्षित गर्नुहोस्|फिल्टर हटाउनुहोस्|सबै फिल्टर हटाउनुहोस्|पछिल्लो पटक अनलाइन|पोर्तुगाली",
    "fa": "ارائه — فیلتر افراد درخواست‌کننده کمک و کارهایشان|دریافت — فیلتر افراد ارائه‌دهنده کمک|فیلتر افراد درخواست‌کننده یا ارائه‌دهنده کمک|یک یا چند دسته، از جمله رویدادها، انتخاب کنید|دسته‌های جستجو و رویدادها|پاک کردن همه دسته‌های انتخاب‌شده|فاصله بر حسب کیلومتر؛ صفر یعنی هر فاصله‌ای|ابتدا موقعیت تقریبی خود را روشن کنید|نمایش نتایج روی نقشه|نمایش نتایج به‌صورت فهرست|تغییر بین نمای نقشه و فهرست|بستن فیلترهای جستجو|فیلتر بر اساس پاداش|برای باز کردن گزینه‌های پیشرفته جستجوی کمک اشتراک بگیرید|فیلتر بر اساس آخرین زمان آنلاین بودن فرد|حداقل درصد امتیاز ترکیبی|حداکثر درصد امتیاز ترکیبی|فیلتر افراد دارای زبان {language}|ویژگی ویژه|پاک کردن دسته‌ها|خاموش|تقریبی|فیلترهای بیشتر|بستن فیلترهای جستجو|افراد، کارها، مکان‌ها...|جستجو: افراد، کارها، مکان‌ها|ذخیره جستجو|ذخیره این فیلترها به‌عنوان هشدار|پاک کردن فیلترها|پاک کردن همه فیلترها|آخرین حضور آنلاین|پرتغالی",
    "pl": "Daj — filtruj osoby proszące o pomoc i ich zadania|Otrzymaj — filtruj osoby oferujące pomoc|Filtruj osoby proszące o pomoc lub ją oferujące|Wybierz co najmniej jedną kategorię, w tym wydarzenia|Kategorie wyszukiwania i wydarzenia|Wyczyść wszystkie wybrane kategorie|Odległość w kilometrach; zero oznacza dowolną odległość|Najpierw włącz przybliżoną lokalizację|Pokaż wyniki na mapie|Pokaż wyniki jako listę|Przełącz widok mapy i listy|Zamknij filtry wyszukiwania|Filtruj według nagrody|Subskrybuj, aby odblokować zaawansowane opcje wyszukiwania pomocy|Filtruj według ostatniej aktywności osoby|Minimalny procent łącznej oceny|Maksymalny procent łącznej oceny|Filtruj osoby mówiące po {language}|Funkcja Premium|Wyczyść kategorie|Wyłączone|Przybliżona|Więcej filtrów|Zamknij filtry wyszukiwania|Osoby, zadania, miejsca...|Szukaj: osoby, zadania, miejsca|Zapisz wyszukiwanie|Zapisz te filtry jako alert|Wyczyść filtry|Wyczyść wszystkie filtry|Ostatnio online|Portugalski",
    "pt": "Dar — filtrar pessoas que pedem ajuda e as respetivas tarefas|Receber — filtrar pessoas que oferecem ajuda|Filtrar pessoas que pedem ou oferecem ajuda|Escolha uma ou mais categorias, incluindo eventos|Categorias de pesquisa e eventos|Limpar todas as categorias selecionadas|Distância em quilómetros; zero significa qualquer distância|Ative primeiro a sua localização aproximada|Mostrar resultados no mapa|Mostrar resultados em lista|Alternar entre mapa e lista|Fechar filtros de pesquisa|Filtrar por recompensa|Subscreva para desbloquear opções avançadas de pesquisa de ajuda|Filtrar pela última vez que a pessoa esteve online|Percentagem mínima da classificação combinada|Percentagem máxima da classificação combinada|Filtrar pessoas que falam {language}|Funcionalidade Premium|Limpar categorias|Desativado|Aproximado|Mais filtros|Fechar filtros de pesquisa|Pessoas, tarefas, locais...|Pesquisar: pessoas, tarefas, locais|Guardar pesquisa|Guardar estes filtros como alerta|Limpar filtros|Limpar todos os filtros|Última vez online|Português",
    "ro": "Oferă — filtrează persoanele care cer ajutor și sarcinile lor|Primește — filtrează persoanele care oferă ajutor|Filtrează persoanele care cer sau oferă ajutor|Alege una sau mai multe categorii, inclusiv evenimente|Categorii de căutare și evenimente|Șterge toate categoriile selectate|Distanța în kilometri; zero înseamnă orice distanță|Activează mai întâi locația aproximativă|Arată rezultatele pe hartă|Arată rezultatele ca listă|Comută între hartă și listă|Închide filtrele de căutare|Filtrează după recompensă|Abonează-te pentru a debloca opțiunile avansate de căutare a ajutorului|Filtrează după ultima conectare a persoanei|Procent minim al evaluării combinate|Procent maxim al evaluării combinate|Filtrează persoanele care vorbesc {language}|Funcție Premium|Șterge categoriile|Dezactivat|Aproximativ|Mai multe filtre|Închide filtrele de căutare|Persoane, sarcini, locuri...|Caută: persoane, sarcini, locuri|Salvează căutarea|Salvează aceste filtre ca alertă|Șterge filtrele|Șterge toate filtrele|Ultima conectare|Portugheză",
    "es": "Dar — filtra a las personas que piden ayuda y sus tareas|Recibir — filtrar a las personas que ofrecen ayuda|Filtrar a quienes piden u ofrecen ayuda|Elige una o más categorías, incluidos los eventos|Categorías de búsqueda y eventos|Borrar todas las categorías seleccionadas|Distancia en kilómetros; cero significa cualquier distancia|Activa primero tu ubicación aproximada|Mostrar resultados en el mapa|Mostrar resultados como lista|Cambiar entre mapa y lista|Cerrar filtros de búsqueda|Filtrar por recompensa|Suscríbete para desbloquear las opciones avanzadas de búsqueda de ayuda|Filtrar según la última conexión de una persona|Porcentaje mínimo de valoración combinada|Porcentaje máximo de valoración combinada|Filtrar por personas que hablan {language}|Función Premium|Borrar categorías|Desactivada|Aproximada|Más filtros|Cerrar filtros de búsqueda|Personas, tareas, lugares...|Buscar: personas, tareas, lugares|Guardar búsqueda|Guardar estos filtros como alerta|Borrar filtros|Borrar todos los filtros|Última conexión|Portugués",
    "sw": "Toa — chuja watu wanaoomba msaada na kazi zao|Pokea — chuja watu wanaotoa msaada|Chuja watu wanaoomba au kutoa msaada|Chagua aina moja au zaidi, pamoja na matukio|Aina za utafutaji na matukio|Futa aina zote zilizochaguliwa|Umbali kwa kilomita; sifuri humaanisha umbali wowote|Washa kwanza eneo lako la takriban|Onyesha matokeo kwenye ramani|Onyesha matokeo kama orodha|Badili kati ya ramani na orodha|Funga vichujio vya utafutaji|Chuja kwa zawadi|Jisajili ili kufungua chaguo za utafutaji wa msaada wa hali ya juu|Chuja kulingana na mara ya mwisho mtu alikuwa mtandaoni|Asilimia ya chini ya ukadiriaji wa pamoja|Asilimia ya juu ya ukadiriaji wa pamoja|Chuja watu wanaozungumza {language}|Kipengele cha Premium|Futa aina|Zima|Takriban|Vichujio zaidi|Funga vichujio vya utafutaji|Watu, kazi, maeneo...|Tafuta: watu, kazi, maeneo|Hifadhi utafutaji|Hifadhi vichujio hivi kama arifa|Futa vichujio|Futa vichujio vyote|Mara ya mwisho mtandaoni|Kireno",
    "sv": "Ge — filtrera personer som ber om hjälp och deras uppgifter|Få — filtrera personer som erbjuder hjälp|Filtrera personer som ber om eller erbjuder hjälp|Välj en eller flera kategorier, inklusive evenemang|Sökkategorier och evenemang|Rensa alla valda kategorier|Avstånd i kilometer; noll betyder valfritt avstånd|Aktivera först din ungefärliga plats|Visa resultat på kartan|Visa resultat som en lista|Växla mellan kart- och listvy|Stäng sökfilter|Filtrera efter belöning|Prenumerera för att låsa upp avancerade hjälpsökningsalternativ|Filtrera efter när en person senast var online|Minsta procent för samlat betyg|Högsta procent för samlat betyg|Filtrera personer som talar {language}|Premiumfunktion|Rensa kategorier|Av|Ungefärlig|Fler filter|Stäng sökfilter|Personer, uppgifter, platser...|Sök: personer, uppgifter, platser|Spara sökning|Spara dessa sökfilter som en avisering|Rensa filter|Rensa alla filter|Senast online|Portugisiska",
    "ta": "கொடு — உதவி கேட்பவர்களையும் அவர்களின் பணிகளையும் வடிகட்டு|பெறு — உதவி வழங்குபவர்களை வடிகட்டு|உதவி கேட்பவர்களை அல்லது வழங்குபவர்களை வடிகட்டு|நிகழ்வுகள் உட்பட ஒன்று அல்லது அதற்கு மேற்பட்ட வகைகளைத் தேர்ந்தெடுக்கவும்|தேடல் வகைகளும் நிகழ்வுகளும்|தேர்ந்தெடுத்த அனைத்து வகைகளையும் அழி|தூரம் கிலோமீட்டரில்; பூஜ்ஜியம் எந்தத் தூரத்தையும் குறிக்கும்|முதலில் தோராயமான இருப்பிடத்தை இயக்கவும்|வரைபடத்தில் முடிவுகளைக் காட்டு|பட்டியலாக முடிவுகளைக் காட்டு|வரைபடம் மற்றும் பட்டியல் காட்சிக்கு மாறு|தேடல் வடிகட்டிகளை மூடு|வெகுமதியின்படி வடிகட்டு|மேம்பட்ட உதவி தேடல் விருப்பங்களைத் திறக்க சந்தா செலுத்தவும்|ஒருவர் கடைசியாக இணையத்தில் இருந்த நேரத்தின்படி வடிகட்டு|குறைந்தபட்ச ஒருங்கிணைந்த மதிப்பீட்டு சதவீதம்|அதிகபட்ச ஒருங்கிணைந்த மதிப்பீட்டு சதவீதம்|{language} பேசுபவர்களை வடிகட்டு|பிரீமியம் அம்சம்|வகைகளை அழி|முடக்கு|தோராயம்|மேலும் வடிகட்டிகள்|தேடல் வடிகட்டிகளை மூடு|மக்கள், பணிகள், இடங்கள்...|தேடு: மக்கள், பணிகள், இடங்கள்|தேடலைச் சேமி|இந்தத் தேடல் வடிகட்டிகளை எச்சரிக்கையாகச் சேமி|வடிகட்டிகளை அழி|அனைத்து வடிகட்டிகளையும் அழி|கடைசியாக இணையத்தில்|போர்த்துகீசியம்",
    "te": "ఇవ్వండి — సహాయం కోరేవారిని, వారి పనులను ఫిల్టర్ చేయండి|పొందండి — సహాయం అందించే వారిని ఫిల్టర్ చేయండి|సహాయం కోరే లేదా అందించే వారిని ఫిల్టర్ చేయండి|ఈవెంట్‌లతో సహా ఒకటి లేదా అంతకంటే ఎక్కువ వర్గాలను ఎంచుకోండి|శోధన వర్గాలు మరియు ఈవెంట్‌లు|ఎంచుకున్న అన్ని వర్గాలను క్లియర్ చేయండి|దూరం కిలోమీటర్లలో; సున్నా అంటే ఏ దూరమైనా|ముందుగా సుమారు స్థానాన్ని ఆన్ చేయండి|మ్యాప్‌లో ఫలితాలను చూపండి|జాబితాగా ఫలితాలను చూపండి|మ్యాప్, జాబితా వీక్షణల మధ్య మారండి|శోధన ఫిల్టర్‌లను మూసివేయండి|బహుమతి ఆధారంగా ఫిల్టర్ చేయండి|అధునాతన సహాయ శోధన ఎంపికలను తెరవడానికి సభ్యత్వం పొందండి|వ్యక్తి చివరిసారిగా ఆన్‌లైన్‌లో ఉన్న సమయం ఆధారంగా ఫిల్టర్ చేయండి|కనిష్ఠ సమగ్ర రేటింగ్ శాతం|గరిష్ఠ సమగ్ర రేటింగ్ శాతం|{language} మాట్లాడే వ్యక్తులను ఫిల్టర్ చేయండి|ప్రీమియం ఫీచర్|వర్గాలను క్లియర్ చేయండి|ఆఫ్|సుమారు|మరిన్ని ఫిల్టర్‌లు|శోధన ఫిల్టర్‌లను మూసివేయండి|వ్యక్తులు, పనులు, ప్రదేశాలు...|శోధన: వ్యక్తులు, పనులు, ప్రదేశాలు|శోధనను సేవ్ చేయండి|ఈ శోధన ఫిల్టర్‌లను హెచ్చరికగా సేవ్ చేయండి|ఫిల్టర్‌లను క్లియర్ చేయండి|అన్ని ఫిల్టర్‌లను క్లియర్ చేయండి|చివరిగా ఆన్‌లైన్|పోర్చుగీస్",
    "th": "ให้ — กรองผู้ที่ขอความช่วยเหลือและงานของพวกเขา|รับ — กรองผู้ที่เสนอความช่วยเหลือ|กรองผู้ที่ขอหรือเสนอความช่วยเหลือ|เลือกหมวดหมู่อย่างน้อยหนึ่งหมวด รวมกิจกรรมด้วย|หมวดหมู่การค้นหาและกิจกรรม|ล้างหมวดหมู่ที่เลือกทั้งหมด|ระยะทางเป็นกิโลเมตร; ศูนย์หมายถึงระยะใดก็ได้|เปิดตำแหน่งโดยประมาณก่อน|แสดงผลลัพธ์บนแผนที่|แสดงผลลัพธ์เป็นรายการ|สลับระหว่างมุมมองแผนที่และรายการ|ปิดตัวกรองการค้นหา|กรองตามรางวัล|สมัครสมาชิกเพื่อปลดล็อกตัวเลือกค้นหาความช่วยเหลือขั้นสูง|กรองตามเวลาที่บุคคลออนไลน์ล่าสุด|เปอร์เซ็นต์คะแนนรวมขั้นต่ำ|เปอร์เซ็นต์คะแนนรวมสูงสุด|กรองผู้ที่พูดภาษา{language}|ฟีเจอร์พรีเมียม|ล้างหมวดหมู่|ปิด|โดยประมาณ|ตัวกรองเพิ่มเติม|ปิดตัวกรองการค้นหา|ผู้คน งาน สถานที่...|ค้นหา: ผู้คน งาน สถานที่|บันทึกการค้นหา|บันทึกตัวกรองนี้เป็นการแจ้งเตือน|ล้างตัวกรอง|ล้างตัวกรองทั้งหมด|ออนไลน์ล่าสุด|ภาษาโปรตุเกส",
    "tr": "Ver — yardım isteyen kişileri ve işlerini filtrele|Al — yardım sunan kişileri filtrele|Yardım isteyen veya sunan kişileri filtrele|Etkinlikler dâhil bir veya daha fazla kategori seçin|Arama kategorileri ve etkinlikler|Seçili tüm kategorileri temizle|Kilometre cinsinden mesafe; sıfır her mesafe demektir|Önce yaklaşık konumunuzu açın|Sonuçları haritada göster|Sonuçları liste olarak göster|Harita ve liste görünümü arasında geçiş yap|Arama filtrelerini kapat|Ödüle göre filtrele|Gelişmiş yardım arama seçeneklerini açmak için abone olun|Kişinin son çevrimiçi olma zamanına göre filtrele|En düşük birleşik puan yüzdesi|En yüksek birleşik puan yüzdesi|{language} konuşan kişileri filtrele|Premium özellik|Kategorileri temizle|Kapalı|Yaklaşık|Daha fazla filtre|Arama filtrelerini kapat|Kişiler, işler, yerler...|Ara: kişiler, işler, yerler|Aramayı kaydet|Bu arama filtrelerini uyarı olarak kaydet|Filtreleri temizle|Tüm filtreleri temizle|Son görülme|Portekizce",
    "vi": "Cho đi — lọc người đang cần trợ giúp và công việc của họ|Nhận — lọc người đang cung cấp trợ giúp|Lọc người cần hoặc cung cấp trợ giúp|Chọn một hoặc nhiều danh mục, bao gồm sự kiện|Danh mục tìm kiếm và sự kiện|Xóa mọi danh mục đã chọn|Khoảng cách tính bằng km; số không nghĩa là mọi khoảng cách|Trước tiên hãy bật vị trí gần đúng|Hiển thị kết quả trên bản đồ|Hiển thị kết quả dạng danh sách|Chuyển giữa chế độ bản đồ và danh sách|Đóng bộ lọc tìm kiếm|Lọc theo phần thưởng|Đăng ký để mở khóa tùy chọn tìm kiếm trợ giúp nâng cao|Lọc theo thời điểm một người trực tuyến lần cuối|Tỷ lệ đánh giá tổng hợp tối thiểu|Tỷ lệ đánh giá tổng hợp tối đa|Lọc người nói {language}|Tính năng Premium|Xóa danh mục|Tắt|Gần đúng|Thêm bộ lọc|Đóng bộ lọc tìm kiếm|Người, việc, địa điểm...|Tìm kiếm: người, việc, địa điểm|Lưu tìm kiếm|Lưu các bộ lọc này thành thông báo|Xóa bộ lọc|Xóa mọi bộ lọc|Trực tuyến lần cuối|Tiếng Bồ Đào Nha",
}


def _search_filter_values(row: str) -> list[str]:
    values = row.split("|")
    if len(values) == len(SEARCH_FILTER_KEYS) + 1:
        values.pop(32)
    return values


SEARCH_FILTER_CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(SEARCH_FILTER_KEYS, _search_filter_values(row), strict=True))
    for code, row in SEARCH_FILTER_ROWS.items()
}
for _code, _row in SEARCH_FILTER_UI_ROWS.items():
    SEARCH_FILTER_CATALOGS[_code].update(
        dict(zip(SEARCH_FILTER_UI_KEYS, _row.split("|"), strict=True))
    )
for _code, _row in SEARCH_FILTER_SUMMARY_ROWS.items():
    SEARCH_FILTER_CATALOGS[_code].update(
        dict(zip(SEARCH_FILTER_SUMMARY_KEYS, _row.split("|"), strict=True))
    )
if any(
    len(_row.split("|")) != len(SEARCH_FILTER_CONTROL_KEYS)
    for _row in SEARCH_FILTER_CONTROL_ROWS.values()
):
    raise ValueError("Search filter control row length is invalid")
for _code, _row in SEARCH_FILTER_CONTROL_ROWS.items():
    SEARCH_FILTER_CATALOGS[_code].update(
        dict(zip(SEARCH_FILTER_CONTROL_KEYS, _row.split("|"), strict=True))
    )
SEARCH_FILTER_KEYS = tuple(
    dict.fromkeys(
        (
            *SEARCH_FILTER_KEYS,
            *SEARCH_FILTER_UI_KEYS,
            *SEARCH_FILTER_SUMMARY_KEYS,
            *SEARCH_FILTER_CONTROL_KEYS,
        )
    )
)

_EXPECTED_LOCALES = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if set(SEARCH_FILTER_CATALOGS) != _EXPECTED_LOCALES:
    raise ValueError("Search filter catalog locale coverage is incomplete")
if set(SEARCH_FILTER_SUMMARY_ROWS) != _EXPECTED_LOCALES:
    raise ValueError("Search filter summary locale coverage is incomplete")
if set(SEARCH_FILTER_CONTROL_ROWS) != _EXPECTED_LOCALES:
    raise ValueError(
        "Search filter control catalog locale coverage is incomplete"
    )
if len(SEARCH_FILTER_KEYS) != len(set(SEARCH_FILTER_KEYS)):
    raise ValueError("Search filter catalog contains duplicate sources")
if any(
    set(entries) != set(SEARCH_FILTER_KEYS)
    for entries in SEARCH_FILTER_CATALOGS.values()
):
    raise ValueError("Search filter catalog source coverage is incomplete")
_formatter = string.Formatter()
for _locale, _entries in SEARCH_FILTER_CATALOGS.items():
    for _source, _value in _entries.items():
        _source_slots = Counter(
            name for _, name, _, _ in _formatter.parse(_source) if name
        )
        _value_slots = Counter(
            name for _, name, _, _ in _formatter.parse(_value) if name
        )
        if not _value.strip() or _source_slots != _value_slots:
            raise ValueError(
                f"Search filter catalog validation failed for {_locale}: {_source}"
            )
