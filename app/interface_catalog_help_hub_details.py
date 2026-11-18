from app.models import LANGUAGE_OPTIONS

HELP_HUB_DETAIL_KEYS: tuple[str, ...] = (
    "Money",
    "Refreshments",
    "A meal",
    "Accommodation",
    "Guided tour",
    "Activity",
    "Other reward",
    "Set a budget or ask for a quote",
    "Drinks and snacks",
    "Lunch, Dinner, Cakes",
    "Work and stay",
    "I will show you around",
    "Cook, Hike, Surf...",
    "Anything else",
)

_DETAIL_ROWS: dict[str, str] = {
    "am": "ገንዘብ|መጠጦች|ምግብ|ማረፊያ|የአካባቢ ጉብኝት|እንቅስቃሴ|ሌላ ሽልማት|በጀት ያዘጋጁ ወይም የዋጋ ጥያቄ ይጠይቁ|መጠጦች እና ቀላል ምግቦች|ምሳ፣ እራት፣ ኬኮች|ሥራ እና ማረፊያ|አካባቢውን አሳይሃለሁ|ምግብ ማብሰል፣ እግር ጉዞ፣ ሰርፍ...|ሌላ ማንኛውም ነገር",
    "ar": "المال|مرطبات|وجبة|إقامة|جولة إرشادية|نشاط|مكافأة أخرى|حدّد ميزانية أو اطلب عرض سعر|مشروبات ووجبات خفيفة|غداء وعشاء وكعك|عمل وإقامة|سأريك المكان|الطبخ والمشي وركوب الأمواج...|أي شيء آخر",
    "bn": "অর্থ|পানীয় ও নাশতা|এক বেলা খাবার|থাকার ব্যবস্থা|গাইডসহ ভ্রমণ|কার্যকলাপ|অন্যান্য পুরস্কার|বাজেট নির্ধারণ করুন বা মূল্য জানতে চান|পানীয় ও হালকা খাবার|দুপুরের খাবার, রাতের খাবার, কেক|কাজ ও থাকা|আমি আপনাকে ঘুরিয়ে দেখাব|রান্না, হাইকিং, সার্ফ...|অন্য কিছু",
    "my": "ငွေ|အဖျော်ယမကာ|အစားအစာတစ်နပ်|တည်းခိုရန်|လမ်းညွှန်ခရီး|လှုပ်ရှားမှု|အခြားဆုလာဘ်|ဘတ်ဂျက်သတ်မှတ်ပါ သို့မဟုတ် ဈေးနှုန်းမေးပါ|အဖျော်ယမကာနှင့် မုန့်များ|နေ့လယ်စာ၊ ညစာ၊ ကိတ်မုန့်များ|အလုပ်နှင့်တည်းခိုရန်|နေရာကို လိုက်ပြမည်|ချက်ပြုတ်ခြင်း၊ တောင်တက်ခြင်း၊ လှိုင်းစီးခြင်း...|အခြားအရာတစ်ခုခု",
    "zh": "金钱|饮品|一餐|住宿|导览|活动|其他奖励|设定预算或询问报价|饮料和零食|午餐、晚餐、蛋糕|工作和住宿|我带你四处看看|烹饪、徒步、冲浪……|其他任何内容",
    "cs": "Peníze|Občerstvení|Jídlo|Ubytování|Komentovaná prohlídka|Aktivita|Jiná odměna|Stanovte rozpočet nebo požádejte o cenovou nabídku|Nápoje a malé občerstvení|Oběd, večeře, dorty|Práce a ubytování|Ukážu vám okolí|Vaření, turistika, surfování...|Cokoli dalšího",
    "da": "Penge|Forfriskninger|Et måltid|Overnatning|Guidet tur|Aktivitet|Anden belønning|Læg et budget eller bed om et tilbud|Drikkevarer og snacks|Frokost, aftensmad, kager|Arbejde og overnatning|Jeg viser dig rundt|Madlavning, vandring, surfing...|Noget andet",
    "nl": "Geld|Versnaperingen|Een maaltijd|Accommodatie|Rondleiding|Activiteit|Andere beloning|Stel een budget in of vraag een offerte aan|Drankjes en snacks|Lunch, diner, taart|Werk en verblijf|Ik laat je de omgeving zien|Koken, wandelen, surfen...|Iets anders",
    "fi": "Rahaa|Virvokkeita|Ateria|Majoitus|Opastettu kierros|Aktiviteetti|Muu palkkio|Aseta budjetti tai pyydä tarjous|Juomia ja välipaloja|Lounas, päivällinen, kakkuja|Työtä ja majoitus|Esittelen sinulle paikkoja|Ruoanlaittoa, patikointia, surffausta...|Jotain muuta",
    "fr": "Argent|Rafraîchissements|Un repas|Hébergement|Visite guidée|Activité|Autre récompense|Définissez un budget ou demandez un devis|Boissons et encas|Déjeuner, dîner, gâteaux|Travail et hébergement|Je vous ferai découvrir les environs|Cuisine, randonnée, surf...|Autre chose",
    "de": "Geld|Erfrischungen|Eine Mahlzeit|Unterkunft|Geführte Tour|Aktivität|Andere Belohnung|Lege ein Budget fest oder frage nach einem Angebot|Getränke und Snacks|Mittagessen, Abendessen, Kuchen|Arbeit und Unterkunft|Ich zeige dir die Umgebung|Kochen, Wandern, Surfen...|Etwas anderes",
    "el": "Χρήματα|Κεράσματα|Ένα γεύμα|Διαμονή|Ξενάγηση|Δραστηριότητα|Άλλη ανταμοιβή|Ορίστε προϋπολογισμό ή ζητήστε προσφορά|Ποτά και σνακ|Μεσημεριανό, βραδινό, κέικ|Εργασία και διαμονή|Θα σας ξεναγήσω|Μαγειρική, πεζοπορία, σερφ...|Οτιδήποτε άλλο",
    "gu": "પૈસા|નાસ્તો અને પીણાં|એક ભોજન|રહેવાની વ્યવસ્થા|માર્ગદર્શિત પ્રવાસ|પ્રવૃત્તિ|અન્ય ઇનામ|બજેટ નક્કી કરો અથવા ભાવ પૂછો|પીણાં અને નાસ્તો|બપોરનું ભોજન, રાત્રિભોજન, કેક|કામ અને રહેવાની સગવડ|હું તમને આસપાસ બતાવીશ|રસોઈ, હાઇકિંગ, સર્ફિંગ...|બીજું કંઈપણ",
    "he": "כסף|כיבוד|ארוחה|לינה|סיור מודרך|פעילות|תגמול אחר|קבעו תקציב או בקשו הצעת מחיר|משקאות ונשנושים|ארוחת צהריים, ארוחת ערב, עוגות|עבודה ולינה|אראה לכם את הסביבה|בישול, טיול רגלי, גלישה...|כל דבר אחר",
    "hi": "पैसे|जलपान|एक भोजन|ठहरने की व्यवस्था|निर्देशित भ्रमण|गतिविधि|अन्य इनाम|बजट तय करें या कीमत पूछें|पेय और स्नैक्स|दोपहर का भोजन, रात का खाना, केक|काम और ठहरना|मैं आपको आसपास घुमाऊँगा|खाना बनाना, पैदल यात्रा, सर्फ़िंग...|कुछ और",
    "hu": "Pénz|Frissítők|Egy étkezés|Szállás|Vezetett túra|Tevékenység|Egyéb jutalom|Állíts be keretet vagy kérj árajánlatot|Italok és harapnivalók|Ebéd, vacsora, sütemények|Munka és szállás|Körbevezetlek|Főzés, túrázás, szörfözés...|Bármi más",
    "id": "Uang|Minuman|Satu kali makan|Akomodasi|Tur berpemandu|Aktivitas|Imbalan lainnya|Tentukan anggaran atau minta penawaran|Minuman dan camilan|Makan siang, makan malam, kue|Bekerja dan menginap|Saya akan mengajak Anda berkeliling|Memasak, mendaki, berselancar...|Hal lainnya",
    "it": "Denaro|Rinfreschi|Un pasto|Alloggio|Visita guidata|Attività|Altra ricompensa|Definisci un budget o chiedi un preventivo|Bevande e snack|Pranzo, cena, torte|Lavoro e alloggio|Ti farò visitare i dintorni|Cucinare, fare escursioni, surf...|Qualcos'altro",
    "ja": "金銭|飲み物|食事|宿泊|ガイド付きツアー|アクティビティ|その他の謝礼|予算を設定するか見積もりを依頼|飲み物と軽食|昼食、夕食、ケーキ|仕事と宿泊|周辺をご案内します|料理、ハイキング、サーフィン...|その他何でも",
    "kn": "ಹಣ|ಪಾನೀಯಗಳು|ಒಂದು ಊಟ|ವಸತಿ|ಮಾರ್ಗದರ್ಶಿತ ಪ್ರವಾಸ|ಚಟುವಟಿಕೆ|ಇತರ ಪ್ರತಿಫಲ|ಬಜೆಟ್ ನಿಗದಿಪಡಿಸಿ ಅಥವಾ ಬೆಲೆ ಕೇಳಿ|ಪಾನೀಯಗಳು ಮತ್ತು ತಿಂಡಿಗಳು|ಮಧ್ಯಾಹ್ನದ ಊಟ, ರಾತ್ರಿ ಊಟ, ಕೇಕ್|ಕೆಲಸ ಮತ್ತು ವಸತಿ|ನಾನು ನಿಮಗೆ ಸುತ್ತಮುತ್ತ ತೋರಿಸುತ್ತೇನೆ|ಅಡುಗೆ, ಪಾದಯಾತ್ರೆ, ಸರ್ಫಿಂಗ್...|ಬೇರೆ ಏನಾದರೂ",
    "ko": "현금|음료와 다과|식사 한 끼|숙박|가이드 투어|활동|기타 보상|예산을 정하거나 견적을 요청하세요|음료와 간식|점심, 저녁, 케이크|일과 숙박|주변을 안내해 드릴게요|요리, 하이킹, 서핑...|그 밖의 모든 것",
    "ml": "പണം|ലഘുഭക്ഷണവും പാനീയങ്ങളും|ഒരു ഭക്ഷണം|താമസസൗകര്യം|ഗൈഡഡ് ടൂർ|പ്രവർത്തനം|മറ്റ് പ്രതിഫലം|ബജറ്റ് നിശ്ചയിക്കുകയോ ക്വോട്ട് ചോദിക്കുകയോ ചെയ്യുക|പാനീയങ്ങളും ലഘുഭക്ഷണവും|ഉച്ചഭക്ഷണം, അത്താഴം, കേക്കുകൾ|ജോലിയും താമസവും|ഞാൻ നിങ്ങളെ ചുറ്റിക്കാണിക്കാം|പാചകം, ഹൈക്കിംഗ്, സർഫിംഗ്...|മറ്റെന്തെങ്കിലും",
    "mr": "पैसे|अल्पोपहार|एक वेळचे जेवण|निवास|मार्गदर्शित फेरफटका|उपक्रम|इतर बक्षीस|बजेट ठरवा किंवा दर विचारा|पेय आणि खाऊ|दुपारचे जेवण, रात्रीचे जेवण, केक|काम आणि निवास|मी तुम्हाला परिसर दाखवेन|स्वयंपाक, भटकंती, सर्फिंग...|आणखी काही",
    "ne": "पैसा|खाजा र पेय|एक छाक खाना|बस्ने व्यवस्था|मार्गदर्शित भ्रमण|गतिविधि|अन्य पुरस्कार|बजेट तय गर्नुहोस् वा मूल्य सोध्नुहोस्|पेय र खाजा|दिउँसोको खाना, रातिको खाना, केक|काम र बसाइ|म तपाईंलाई वरिपरि घुमाउनेछु|खाना पकाउने, पैदल यात्रा, सर्फिङ...|अरू जे पनि",
    "fa": "پول|نوشیدنی و خوراکی|یک وعده غذا|اقامت|گردش با راهنما|فعالیت|پاداش دیگر|بودجه تعیین کنید یا درخواست قیمت بدهید|نوشیدنی و تنقلات|ناهار، شام، کیک|کار و اقامت|اطراف را به شما نشان می‌دهم|آشپزی، پیاده‌روی، موج‌سواری...|هر چیز دیگری",
    "pl": "Pieniądze|Przekąski i napoje|Posiłek|Zakwaterowanie|Wycieczka z przewodnikiem|Aktywność|Inna nagroda|Ustal budżet lub poproś o wycenę|Napoje i przekąski|Lunch, obiad, ciasta|Praca i nocleg|Pokażę ci okolicę|Gotowanie, piesze wycieczki, surfing...|Coś innego",
    "pt": "Dinheiro|Bebidas e snacks|Uma refeição|Alojamento|Visita guiada|Atividade|Outra recompensa|Defina um orçamento ou peça um orçamento|Bebidas e snacks|Almoço, jantar, bolos|Trabalho e alojamento|Mostro-lhe os arredores|Cozinhar, caminhar, surfar...|Qualquer outra coisa",
    "ro": "Bani|Băuturi și gustări|O masă|Cazare|Tur ghidat|Activitate|Altă recompensă|Stabilește un buget sau cere o ofertă|Băuturi și gustări|Prânz, cină, prăjituri|Muncă și cazare|Îți voi arăta împrejurimile|Gătit, drumeții, surf...|Orice altceva",
    "es": "Dinero|Refrigerios|Una comida|Alojamiento|Visita guiada|Actividad|Otra recompensa|Fija un presupuesto o pide un presupuesto|Bebidas y aperitivos|Almuerzo, cena, pasteles|Trabajo y alojamiento|Te enseñaré los alrededores|Cocinar, caminar, surfear...|Cualquier otra cosa",
    "sw": "Pesa|Viburudisho|Mlo mmoja|Malazi|Ziara ya kuongozwa|Shughuli|Zawadi nyingine|Weka bajeti au uombe makadirio ya bei|Vinywaji na vitafunio|Chakula cha mchana, cha jioni, keki|Kazi na malazi|Nitakuonyesha maeneo ya karibu|Kupika, kutembea, kuteleza mawimbini...|Kitu kingine chochote",
    "sv": "Pengar|Förfriskningar|En måltid|Boende|Guidad tur|Aktivitet|Annan belöning|Sätt en budget eller be om en offert|Dryck och snacks|Lunch, middag, kakor|Arbete och boende|Jag visar dig runt|Laga mat, vandra, surfa...|Något annat",
    "ta": "பணம்|பானங்கள்|ஒரு வேளை உணவு|தங்குமிடம்|வழிகாட்டியுடன் சுற்றுலா|செயல்பாடு|மற்ற வெகுமதி|பட்ஜெட்டை அமைக்கவும் அல்லது விலை கேட்கவும்|பானங்கள் மற்றும் சிற்றுண்டிகள்|மதிய உணவு, இரவு உணவு, கேக்குகள்|வேலையும் தங்குமிடமும்|சுற்றியுள்ள இடங்களைக் காட்டுகிறேன்|சமைத்தல், நடைபயணம், சர்ஃபிங்...|வேறு ஏதாவது",
    "te": "డబ్బు|పానీయాలు|ఒక భోజనం|వసతి|గైడ్‌తో పర్యటన|కార్యకలాపం|ఇతర బహుమతి|బడ్జెట్ నిర్ణయించండి లేదా ధర అడగండి|పానీయాలు మరియు చిరుతిళ్లు|మధ్యాహ్న భోజనం, రాత్రి భోజనం, కేకులు|పని మరియు బస|నేను మీకు చుట్టుపక్కల చూపిస్తాను|వంట, హైకింగ్, సర్ఫింగ్...|ఇంకేదైనా",
    "th": "เงิน|เครื่องดื่มและของว่าง|อาหารหนึ่งมื้อ|ที่พัก|ทัวร์พร้อมไกด์|กิจกรรม|รางวัลอื่น|กำหนดงบประมาณหรือขอใบเสนอราคา|เครื่องดื่มและของว่าง|อาหารกลางวัน อาหารเย็น เค้ก|ทำงานและพักอาศัย|ฉันจะพาคุณชมรอบ ๆ|ทำอาหาร เดินป่า เล่นเซิร์ฟ...|อย่างอื่น",
    "tr": "Para|İkramlar|Bir öğün yemek|Konaklama|Rehberli tur|Etkinlik|Diğer ödül|Bütçe belirleyin veya fiyat teklifi isteyin|İçecekler ve atıştırmalıklar|Öğle yemeği, akşam yemeği, kek|Çalışma ve konaklama|Size çevreyi gezdireceğim|Yemek yapmak, yürüyüş, sörf...|Başka herhangi bir şey",
    "vi": "Tiền|Đồ uống và thức ăn nhẹ|Một bữa ăn|Chỗ ở|Chuyến tham quan có hướng dẫn|Hoạt động|Phần thưởng khác|Đặt ngân sách hoặc yêu cầu báo giá|Đồ uống và đồ ăn nhẹ|Bữa trưa, bữa tối, bánh|Làm việc và lưu trú|Tôi sẽ dẫn bạn đi tham quan|Nấu ăn, đi bộ đường dài, lướt sóng...|Bất cứ điều gì khác",
}

_EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
if set(_DETAIL_ROWS) != _EXPECTED_LOCALES:
    raise ValueError(
        "Help-hub detail catalogs must cover every non-English locale"
    )
if len(HELP_HUB_DETAIL_KEYS) != 14 or len(set(HELP_HUB_DETAIL_KEYS)) != 14:
    raise ValueError("Help-hub detail sources must be exactly 14 unique keys")

HELP_HUB_DETAIL_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(HELP_HUB_DETAIL_KEYS, row.split("|"), strict=True))
    for locale, row in _DETAIL_ROWS.items()
}

for _locale, _entries in HELP_HUB_DETAIL_CATALOGS.items():
    for _source, _translation in _entries.items():
        if not _translation.strip() or _translation == _source:
            raise ValueError(
                f"Missing help-hub detail translation: {_locale}: {_source}"
            )
