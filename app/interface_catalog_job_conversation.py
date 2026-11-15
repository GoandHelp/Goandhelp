from app.models import LANGUAGE_OPTIONS

JOB_CONVERSATION_KEYS: tuple[str, ...] = (
    "Timeliness",
    "Work ethic",
    "Skill",
    "Friendliness",
    "Give Help score",
    "Get Help score",
    "Helper photo",
    "Helpee photo",
)

JOB_CONVERSATION_ROWS: dict[str, str] = {
    "am": "በሰዓቱ መገኘት|የሥራ ትጋት|ችሎታ|ወዳጃዊነት|የእርዳታ መስጠት ውጤት|የእርዳታ መቀበል ውጤት|የረዳት ፎቶ|የእርዳታ ተቀባይ ፎቶ",
    "ar": "الالتزام بالمواعيد|أخلاقيات العمل|المهارة|الودّ|تقييم تقديم المساعدة|تقييم تلقي المساعدة|صورة المساعد|صورة متلقي المساعدة",
    "bn": "সময়নিষ্ঠা|কাজের নৈতিকতা|দক্ষতা|বন্ধুত্বপূর্ণ আচরণ|সাহায্য দেওয়ার স্কোর|সাহায্য নেওয়ার স্কোর|সাহায্যকারীর ছবি|সাহায্যগ্রহীতার ছবি",
    "my": "အချိန်တိကျမှု|အလုပ်ကျင့်ဝတ်|ကျွမ်းကျင်မှု|ဖော်ရွေမှု|အကူအညီပေးမှု အမှတ်|အကူအညီရယူမှု အမှတ်|ကူညီသူ၏ဓာတ်ပုံ|အကူအညီလက်ခံသူ၏ဓာတ်ပုံ",
    "zh": "守时|工作态度|技能|友善程度|提供帮助评分|接受帮助评分|帮助者照片|求助者照片",
    "cs": "Dochvilnost|Pracovní morálka|Dovednosti|Vstřícnost|Hodnocení poskytnuté pomoci|Hodnocení přijaté pomoci|Fotografie pomocníka|Fotografie příjemce pomoci",
    "da": "Punktlighed|Arbejdsmoral|Færdigheder|Venlighed|Bedømmelse af hjælp givet|Bedømmelse af hjælp modtaget|Hjælperens foto|Modtagerens foto",
    "nl": "Stiptheid|Werkethiek|Vaardigheid|Vriendelijkheid|Score voor gegeven hulp|Score voor ontvangen hulp|Foto van de helper|Foto van de hulpvrager",
    "fi": "Täsmällisyys|Työmoraali|Taidot|Ystävällisyys|Annetun avun arvosana|Saadun avun arvosana|Auttajan kuva|Avun saajan kuva",
    "fr": "Ponctualité|Éthique professionnelle|Compétence|Amabilité|Note pour l’aide apportée|Note pour l’aide reçue|Photo de l’aidant|Photo de la personne aidée",
    "de": "Pünktlichkeit|Arbeitsmoral|Fähigkeit|Freundlichkeit|Bewertung der geleisteten Hilfe|Bewertung der erhaltenen Hilfe|Foto der helfenden Person|Foto der hilfesuchenden Person",
    "el": "Συνέπεια στην ώρα|Εργασιακή ηθική|Δεξιότητα|Φιλικότητα|Βαθμολογία προσφοράς βοήθειας|Βαθμολογία λήψης βοήθειας|Φωτογραφία βοηθού|Φωτογραφία ατόμου που λαμβάνει βοήθεια",
    "gu": "સમયપાલન|કામની નૈતિકતા|કુશળતા|મૈત્રીપૂર્ણ વર્તન|આપેલી મદદનો ગુણ|મેળવેલી મદદનો ગુણ|મદદગારનો ફોટો|મદદ મેળવનારનો ફોટો",
    "he": "עמידה בזמנים|מוסר עבודה|מיומנות|ידידותיות|ציון על מתן עזרה|ציון על קבלת עזרה|תמונת העוזר|תמונת מקבל העזרה",
    "hi": "समयनिष्ठा|काम की नैतिकता|कौशल|मित्रता|दी गई मदद का स्कोर|मिली मदद का स्कोर|मददगार की फ़ोटो|मदद पाने वाले की फ़ोटो",
    "hu": "Pontosság|Munkamorál|Készség|Barátságosság|A nyújtott segítség értékelése|A kapott segítség értékelése|A segítő fotója|A segítséget kapó fotója",
    "id": "Ketepatan waktu|Etos kerja|Keterampilan|Keramahan|Nilai bantuan yang diberikan|Nilai bantuan yang diterima|Foto penolong|Foto penerima bantuan",
    "it": "Puntualità|Etica del lavoro|Competenza|Cordialità|Punteggio per l’aiuto offerto|Punteggio per l’aiuto ricevuto|Foto di chi aiuta|Foto di chi riceve aiuto",
    "ja": "時間厳守|仕事への姿勢|技能|親しみやすさ|提供した支援の評価|受けた支援の評価|支援者の写真|支援を受ける人の写真",
    "kn": "ಸಮಯಪಾಲನೆ|ಕೆಲಸದ ನೀತಿ|ಕೌಶಲ್ಯ|ಸ್ನೇಹಪರತೆ|ನೀಡಿದ ಸಹಾಯದ ಅಂಕ|ಪಡೆದ ಸಹಾಯದ ಅಂಕ|ಸಹಾಯಕರ ಫೋಟೋ|ಸಹಾಯ ಪಡೆದವರ ಫೋಟೋ",
    "ko": "시간 준수|직업 윤리|기술|친절함|도움을 준 점수|도움을 받은 점수|도움 제공자 사진|도움 요청자 사진",
    "ml": "കൃത്യനിഷ്ഠ|തൊഴിൽമര്യാദ|കഴിവ്|സൗഹൃദപരത|നൽകിയ സഹായത്തിന്റെ സ്കോർ|ലഭിച്ച സഹായത്തിന്റെ സ്കോർ|സഹായകന്റെ ഫോട്ടോ|സഹായം സ്വീകരിക്കുന്നയാളുടെ ഫോട്ടോ",
    "mr": "वेळेचे पालन|कामाची नैतिकता|कौशल्य|मैत्रीपूर्णपणा|दिलेल्या मदतीचा गुण|मिळालेल्या मदतीचा गुण|मदतनीसाचा फोटो|मदत घेणाऱ्याचा फोटो",
    "ne": "समयनिष्ठा|काम गर्ने नैतिकता|सीप|मित्रवत व्यवहार|दिएको सहयोगको अङ्क|पाएको सहयोगको अङ्क|सहयोगीको तस्बिर|सहयोग पाउने व्यक्तिको तस्बिर",
    "fa": "وقت‌شناسی|اخلاق کاری|مهارت|خوش‌برخوردی|امتیاز کمک ارائه‌شده|امتیاز کمک دریافت‌شده|عکس کمک‌کننده|عکس دریافت‌کننده کمک",
    "pl": "Punktualność|Etyka pracy|Umiejętności|Życzliwość|Ocena udzielonej pomocy|Ocena otrzymanej pomocy|Zdjęcie osoby pomagającej|Zdjęcie osoby otrzymującej pomoc",
    "pt": "Pontualidade|Ética de trabalho|Competência|Simpatia|Pontuação da ajuda prestada|Pontuação da ajuda recebida|Fotografia de quem ajuda|Fotografia de quem recebe ajuda",
    "ro": "Punctualitate|Etică profesională|Competență|Amabilitate|Scor pentru ajutorul oferit|Scor pentru ajutorul primit|Fotografia persoanei care ajută|Fotografia persoanei care primește ajutor",
    "es": "Puntualidad|Ética de trabajo|Habilidad|Amabilidad|Puntuación de la ayuda ofrecida|Puntuación de la ayuda recibida|Foto de quien ayuda|Foto de quien recibe ayuda",
    "sw": "Kufika kwa wakati|Maadili ya kazi|Ujuzi|Urafiki|Alama ya msaada uliotolewa|Alama ya msaada uliopokelewa|Picha ya msaidizi|Picha ya mpokeaji msaada",
    "sv": "Punktlighet|Arbetsmoral|Skicklighet|Vänlighet|Betyg för hjälp som getts|Betyg för hjälp som fåtts|Foto på hjälparen|Foto på den som får hjälp",
    "ta": "நேரம் தவறாமை|வேலை நெறிமுறை|திறன்|நட்புணர்வு|வழங்கிய உதவிக்கான மதிப்பெண்|பெற்ற உதவிக்கான மதிப்பெண்|உதவியாளரின் புகைப்படம்|உதவி பெறுபவரின் புகைப்படம்",
    "te": "సమయపాలన|పని నైతికత|నైపుణ్యం|స్నేహపూర్వకత|అందించిన సహాయానికి స్కోరు|పొందిన సహాయానికి స్కోరు|సహాయకుడి ఫోటో|సహాయం పొందేవారి ఫోటో",
    "th": "การตรงต่อเวลา|จรรยาบรรณในการทำงาน|ทักษะ|ความเป็นมิตร|คะแนนการให้ความช่วยเหลือ|คะแนนการรับความช่วยเหลือ|รูปภาพผู้ช่วย|รูปภาพผู้รับความช่วยเหลือ",
    "tr": "Dakiklik|İş ahlakı|Beceri|Arkadaş canlısı olma|Verilen yardım puanı|Alınan yardım puanı|Yardım eden kişinin fotoğrafı|Yardım alan kişinin fotoğrafı",
    "vi": "Đúng giờ|Đạo đức nghề nghiệp|Kỹ năng|Thân thiện|Điểm trợ giúp đã cung cấp|Điểm trợ giúp đã nhận|Ảnh người hỗ trợ|Ảnh người nhận trợ giúp",
}

_EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
if set(JOB_CONVERSATION_ROWS) != _EXPECTED_LOCALES:
    raise ValueError("Job conversation locale coverage is incomplete")

JOB_CONVERSATION_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(JOB_CONVERSATION_KEYS, row.split("|"), strict=True))
    for locale, row in JOB_CONVERSATION_ROWS.items()
}
for _locale, _entries in JOB_CONVERSATION_CATALOGS.items():
    if set(_entries) != set(JOB_CONVERSATION_KEYS):
        raise ValueError(
            f"Job conversation source coverage is incomplete: {_locale}"
        )
    for _source, _translation in _entries.items():
        if not _translation.strip() or _translation == _source:
            raise ValueError(
                f"Missing job conversation translation: {_locale}: {_source}"
            )
