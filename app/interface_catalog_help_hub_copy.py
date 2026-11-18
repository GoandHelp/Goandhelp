from app.models import LANGUAGE_OPTIONS

HELP_HUB_COPY_KEYS: tuple[str, ...] = (
    "Rewards",
    "Address",
    "Start time",
    "No reviews yet",
    "Deny",
    "This helper didn't add a message.",
    "I'm moving out of a fourth-floor flat and need someone strong for a couple of hours…",
    "Job description",
)

_COPY_ROWS: dict[str, str] = {
    "am": "ሽልማቶች|አድራሻ|የመጀመሪያ ሰዓት|ገና ግምገማ የለም|እምቢ በል|ይህ አጋዥ መልዕክት አልጨመረም።|ከአራተኛ ፎቅ አፓርታማ እየወጣሁ ነው፤ ለሁለት ሰዓታት ጠንካራ ሰው እፈልጋለሁ…|የሥራ መግለጫ",
    "ar": "المكافآت|العنوان|وقت البدء|لا توجد تقييمات بعد|رفض|لم يضف هذا المساعد رسالة.|أنتقل من شقة في الطابق الرابع وأحتاج إلى شخص قوي لمساعدتي لبضع ساعات…|وصف العمل",
    "bn": "পুরস্কার|ঠিকানা|শুরুর সময়|এখনও কোনো পর্যালোচনা নেই|প্রত্যাখ্যান|এই সহায়তাকারী কোনো বার্তা যোগ করেননি।|আমি চতুর্থ তলার ফ্ল্যাট থেকে উঠছি এবং কয়েক ঘণ্টার জন্য একজন শক্তসমর্থ মানুষ দরকার…|কাজের বিবরণ",
    "my": "ဆုလာဘ်များ|လိပ်စာ|စတင်ချိန်|သုံးသပ်ချက်မရှိသေးပါ|ငြင်းပယ်ရန်|ဤအကူအညီပေးသူသည် မက်ဆေ့ချ်မထည့်ခဲ့ပါ။|လေးထပ်အိမ်ခန်းမှ ပြောင်းရွှေ့နေပြီး နာရီအနည်းငယ်အတွက် သန်မာသူတစ်ဦး လိုအပ်သည်…|အလုပ်ဖော်ပြချက်",
    "zh": "奖励|地址|开始时间|暂无评价|拒绝|这位帮手没有添加消息。|我正从四楼公寓搬出，需要一位力气大的帮手帮忙几个小时……|工作说明",
    "cs": "Odměny|Adresa|Čas začátku|Zatím žádná hodnocení|Odmítnout|Tento pomocník nepřidal žádnou zprávu.|Stěhuji se z bytu ve čtvrtém patře a na několik hodin potřebuji někoho silného…|Popis práce",
    "da": "Belønninger|Adresse|Starttidspunkt|Ingen anmeldelser endnu|Afvis|Hjælperen har ikke tilføjet en besked.|Jeg flytter fra en lejlighed på fjerde sal og har brug for en stærk person i et par timer…|Jobbeskrivelse",
    "nl": "Beloningen|Adres|Begintijd|Nog geen beoordelingen|Weigeren|Deze helper heeft geen bericht toegevoegd.|Ik verhuis uit een flat op de vierde verdieping en heb een sterke helper nodig voor een paar uur…|Beschrijving van de klus",
    "fi": "Palkkiot|Osoite|Aloitusaika|Ei vielä arvosteluja|Hylkää|Tämä auttaja ei lisännyt viestiä.|Muutan pois neljännen kerroksen asunnosta ja tarvitsen vahvan apulaisen muutamaksi tunniksi…|Työn kuvaus",
    "fr": "Récompenses|Adresse|Heure de début|Pas encore d’avis|Refuser|Cette personne n’a pas ajouté de message.|Je déménage d’un appartement au quatrième étage et j’ai besoin d’une personne robuste pendant quelques heures…|Description de la tâche",
    "de": "Belohnungen|Adresse|Startzeit|Noch keine Bewertungen|Ablehnen|Diese helfende Person hat keine Nachricht hinzugefügt.|Ich ziehe aus einer Wohnung im vierten Stock aus und brauche für ein paar Stunden eine kräftige Person…|Aufgabenbeschreibung",
    "el": "Ανταμοιβές|Διεύθυνση|Ώρα έναρξης|Δεν υπάρχουν ακόμη αξιολογήσεις|Απόρριψη|Αυτός ο βοηθός δεν πρόσθεσε μήνυμα.|Μετακομίζω από διαμέρισμα στον τέταρτο όροφο και χρειάζομαι ένα δυνατό άτομο για λίγες ώρες…|Περιγραφή εργασίας",
    "gu": "ઇનામો|સરનામું|શરૂઆતનો સમય|હજી કોઈ સમીક્ષા નથી|નકારો|આ મદદગારે કોઈ સંદેશ ઉમેર્યો નથી.|હું ચોથા માળના ફ્લેટમાંથી સ્થળાંતર કરું છું અને થોડા કલાકો માટે મજબૂત વ્યક્તિ જોઈએ છે…|કામનું વર્ણન",
    "he": "תגמולים|כתובת|שעת התחלה|אין עדיין ביקורות|דחייה|העוזר הזה לא הוסיף הודעה.|אני עובר מדירה בקומה הרביעית וצריך אדם חזק לכמה שעות…|תיאור העבודה",
    "hi": "इनाम|पता|शुरू होने का समय|अभी तक कोई समीक्षा नहीं|अस्वीकार करें|इस मददगार ने कोई संदेश नहीं जोड़ा।|मैं चौथी मंज़िल के फ़्लैट से जा रहा हूँ और कुछ घंटों के लिए ताकतवर व्यक्ति चाहिए…|काम का विवरण",
    "hu": "Jutalmak|Cím|Kezdési idő|Még nincs értékelés|Elutasítás|Ez a segítő nem írt üzenetet.|Kiköltözöm egy negyedik emeleti lakásból, és néhány órára szükségem van egy erős emberre…|A munka leírása",
    "id": "Imbalan|Alamat|Waktu mulai|Belum ada ulasan|Tolak|Pembantu ini tidak menambahkan pesan.|Saya pindah dari flat lantai empat dan membutuhkan orang yang kuat selama beberapa jam…|Deskripsi pekerjaan",
    "it": "Ricompense|Indirizzo|Ora di inizio|Ancora nessuna recensione|Rifiuta|Questa persona non ha aggiunto un messaggio.|Sto traslocando da un appartamento al quarto piano e mi serve una persona forte per un paio d’ore…|Descrizione del lavoro",
    "ja": "謝礼|住所|開始時刻|レビューはまだありません|拒否|このヘルパーはメッセージを追加していません。|4階のアパートから引っ越すため、数時間ほど力のある人に手伝ってほしいです…|仕事内容",
    "kn": "ಪ್ರತಿಫಲಗಳು|ವಿಳಾಸ|ಆರಂಭದ ಸಮಯ|ಇನ್ನೂ ವಿಮರ್ಶೆಗಳಿಲ್ಲ|ನಿರಾಕರಿಸಿ|ಈ ಸಹಾಯಕರು ಸಂದೇಶವನ್ನು ಸೇರಿಸಿಲ್ಲ.|ನಾಲ್ಕನೇ ಮಹಡಿಯ ಫ್ಲಾಟ್‌ನಿಂದ ಸ್ಥಳಾಂತರವಾಗುತ್ತಿದ್ದೇನೆ; ಕೆಲವು ಗಂಟೆಗಳ ಕಾಲ ಬಲಶಾಲಿ ವ್ಯಕ್ತಿ ಬೇಕು…|ಕೆಲಸದ ವಿವರಣೆ",
    "ko": "보상|주소|시작 시간|아직 리뷰가 없습니다|거절|이 도움 제공자는 메시지를 추가하지 않았습니다.|4층 아파트에서 이사하며 몇 시간 동안 힘센 분의 도움이 필요합니다…|작업 설명",
    "ml": "പ്രതിഫലങ്ങൾ|വിലാസം|ആരംഭ സമയം|ഇതുവരെ അവലോകനങ്ങളില്ല|നിരസിക്കുക|ഈ സഹായി സന്ദേശം ചേർത്തിട്ടില്ല.|നാലാം നിലയിലെ ഫ്ലാറ്റിൽ നിന്ന് മാറുകയാണ്; കുറച്ച് മണിക്കൂറുകൾക്ക് ശക്തനായ ഒരാളുടെ സഹായം വേണം…|ജോലിയുടെ വിവരണം",
    "mr": "बक्षिसे|पत्ता|सुरुवातीची वेळ|अद्याप कोणतीही समीक्षा नाही|नाकारा|या मदतनीसाने संदेश जोडलेला नाही.|मी चौथ्या मजल्यावरील फ्लॅटमधून जात आहे आणि काही तासांसाठी ताकदवान व्यक्ती हवी आहे…|कामाचे वर्णन",
    "ne": "पुरस्कारहरू|ठेगाना|सुरु हुने समय|अहिलेसम्म समीक्षा छैन|अस्वीकार गर्नुहोस्|यो सहयोगीले कुनै सन्देश थपेको छैन।|म चौथो तलाको फ्ल्याटबाट सर्दैछु र केही घण्टाका लागि बलियो व्यक्ति चाहिन्छ…|कामको विवरण",
    "fa": "پاداش‌ها|نشانی|زمان شروع|هنوز دیدگاهی ثبت نشده|رد کردن|این کمک‌کننده پیامی اضافه نکرده است.|از آپارتمان طبقه چهارم اسباب‌کشی می‌کنم و برای چند ساعت به فردی نیرومند نیاز دارم…|شرح کار",
    "pl": "Nagrody|Adres|Godzina rozpoczęcia|Brak ocen|Odmów|Ta osoba pomagająca nie dodała wiadomości.|Wyprowadzam się z mieszkania na czwartym piętrze i potrzebuję silnej osoby na kilka godzin…|Opis zadania",
    "pt": "Recompensas|Morada|Hora de início|Ainda sem avaliações|Recusar|Este ajudante não adicionou uma mensagem.|Estou a mudar-me de um apartamento no quarto andar e preciso de alguém forte durante algumas horas…|Descrição do trabalho",
    "ro": "Recompense|Adresă|Ora de început|Nu există încă evaluări|Refuză|Acest ajutor nu a adăugat niciun mesaj.|Mă mut dintr-un apartament de la etajul patru și am nevoie de o persoană puternică pentru câteva ore…|Descrierea activității",
    "es": "Recompensas|Dirección|Hora de inicio|Aún no hay reseñas|Rechazar|Esta persona no ha añadido ningún mensaje.|Me mudo de un piso en una cuarta planta y necesito a alguien fuerte durante un par de horas…|Descripción del trabajo",
    "sw": "Zawadi|Anwani|Muda wa kuanza|Bado hakuna tathmini|Kataa|Msaidizi huyu hakuongeza ujumbe.|Ninahama kutoka kwenye nyumba ya ghorofa ya nne na ninahitaji mtu mwenye nguvu kwa saa chache…|Maelezo ya kazi",
    "sv": "Belöningar|Adress|Starttid|Inga omdömen ännu|Avböj|Hjälparen har inte lagt till något meddelande.|Jag flyttar från en lägenhet på fjärde våningen och behöver en stark person i några timmar…|Jobbeskrivning",
    "ta": "வெகுமதிகள்|முகவரி|தொடக்க நேரம்|இன்னும் மதிப்புரைகள் இல்லை|மறுக்கவும்|இந்த உதவியாளர் செய்தி எதையும் சேர்க்கவில்லை.|நான்காவது மாடி குடியிருப்பிலிருந்து மாறுகிறேன்; சில மணிநேரங்களுக்கு வலிமையான ஒருவர் தேவை…|வேலை விளக்கம்",
    "te": "బహుమతులు|చిరునామా|ప్రారంభ సమయం|ఇంకా సమీక్షలు లేవు|తిరస్కరించండి|ఈ సహాయకుడు సందేశాన్ని జోడించలేదు.|నాలుగో అంతస్తు ఫ్లాట్‌ నుంచి మారుతున్నాను; కొన్ని గంటల పాటు బలమైన వ్యక్తి కావాలి…|పని వివరణ",
    "th": "สิ่งตอบแทน|ที่อยู่|เวลาเริ่มต้น|ยังไม่มีรีวิว|ปฏิเสธ|ผู้ช่วยคนนี้ไม่ได้เพิ่มข้อความ|ฉันกำลังย้ายออกจากแฟลตชั้นสี่และต้องการคนแข็งแรงมาช่วยสักสองสามชั่วโมง…|รายละเอียดงาน",
    "tr": "Ödüller|Adres|Başlangıç saati|Henüz değerlendirme yok|Reddet|Bu yardımcı bir mesaj eklemedi.|Dördüncü kattaki dairemden taşınıyorum ve birkaç saatliğine güçlü birine ihtiyacım var…|İş açıklaması",
    "vi": "Phần thưởng|Địa chỉ|Giờ bắt đầu|Chưa có đánh giá|Từ chối|Người hỗ trợ này chưa thêm lời nhắn.|Tôi đang chuyển khỏi căn hộ tầng bốn và cần một người khỏe giúp trong vài giờ…|Mô tả công việc",
}

_EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
if set(_COPY_ROWS) != _EXPECTED_LOCALES:
    raise ValueError(
        "Help-hub copy catalogs must cover every non-English locale"
    )
if len(HELP_HUB_COPY_KEYS) != 8 or len(set(HELP_HUB_COPY_KEYS)) != 8:
    raise ValueError("Help-hub copy sources must be exactly 8 unique keys")

HELP_HUB_COPY_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(HELP_HUB_COPY_KEYS, row.split("|"), strict=True))
    for locale, row in _COPY_ROWS.items()
}

for _locale, _entries in HELP_HUB_COPY_CATALOGS.items():
    for _source, _translation in _entries.items():
        if not _translation.strip() or _translation == _source:
            raise ValueError(
                f"Missing help-hub copy translation: {_locale}: {_source}"
            )
