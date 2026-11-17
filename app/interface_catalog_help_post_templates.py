from app.models import LANGUAGE_OPTIONS

HELP_POST_UI_TEMPLATE_KEYS: tuple[str, ...] = (
    "{count} characters left",
    "{count} of 5 slots free",
    "{count} / 5 attached",
    "{count} created",
    "Remove “{title}” from the board?",
    "Delete {title}",
    "People required: {count}",
)
HELP_POST_COUNT_LABEL_KEYS: tuple[str, ...] = (
    "Requests posted",
    "Still open",
    "Upcoming",
)

_HELP_POST_TEMPLATE_ROWS: dict[str, str] = {
    "am": "{count} ቁምፊዎች ቀርተዋል|ከ5 ቦታዎች {count} ነፃ|{count} / 5 ተያይዘዋል|{count} ተፈጥረዋል|{title}ን ከሰሌዳው ማስወገድ?|{title}ን ሰርዝ|የሚያስፈልጉ ሰዎች: {count}|የተለጠፉ ጥያቄዎች|አሁንም ክፍት|የሚመጡ",
    "ar": "متبقي {count} حرفًا|المتاح {count} من أصل 5 أماكن|المرفق {count} / 5|تم إنشاء {count}|إزالة «{title}» من اللوحة؟|حذف {title}|عدد الأشخاص المطلوب: {count}|الطلبات المنشورة|ما زالت مفتوحة|القادمة",
    "bn": "আরও {count}টি অক্ষর লেখা যাবে|৫টি স্থানের মধ্যে {count}টি খালি|সংযুক্ত {count} / ৫|তৈরি হয়েছে {count}টি|বোর্ড থেকে “{title}” সরাবেন?|{title} মুছুন|প্রয়োজনীয় মানুষের সংখ্যা: {count}|পোস্ট করা অনুরোধ|এখনও খোলা|আসন্ন",
    "my": "စာလုံး {count} လုံး ကျန်သည်|နေရာ 5 ခုအနက် {count} ခု လွတ်နေသည်|ပူးတွဲထားသည် {count} / 5|ဖန်တီးပြီး {count}|ဘုတ်မှ “{title}” ကို ဖယ်မလား။|{title} ကို ဖျက်ရန်|လိုအပ်သော လူဦးရေ: {count}|တင်ထားသော တောင်းဆိုမှုများ|ဖွင့်ထားဆဲ|လာမည့်",
    "zh": "还可输入 {count} 个字符|5 个名额中剩余 {count} 个|已附加 {count} / 5|已创建 {count} 个|要从列表中移除“{title}”吗？|删除 {title}|所需人数：{count}|已发布的请求|仍在开放|即将开始",
    "cs": "Zbývá {count} znaků|Volná místa: {count} z 5|Přiloženo {count} / 5|Vytvořeno {count}|Odebrat položku „{title}“ z nástěnky?|Smazat {title}|Potřebný počet lidí: {count}|Zveřejněné žádosti|Stále otevřené|Nadcházející",
    "da": "{count} tegn tilbage|{count} af 5 pladser ledige|Vedhæftet {count} / 5|{count} oprettet|Fjern “{title}” fra opslagstavlen?|Slet {title}|Antal personer, der er brug for: {count}|Opslåede anmodninger|Stadig åbne|Kommende",
    "nl": "Nog {count} tekens|{count} van 5 plekken vrij|{count} / 5 toegevoegd|{count} aangemaakt|“{title}” van het bord verwijderen?|{title} verwijderen|Benodigd aantal personen: {count}|Geplaatste verzoeken|Nog open|Binnenkort",
    "fi": "{count} merkkiä jäljellä|{count} vapaana 5 paikasta|Liitetty {count} / 5|{count} luotu|Poistetaanko “{title}” ilmoitustaululta?|Poista {title}|Tarvittavien henkilöiden määrä: {count}|Julkaistut pyynnöt|Yhä avoinna|Tulossa",
    "fr": "Il reste {count} caractères|{count} places libres sur 5|{count} / 5 jointes|{count} créées|Retirer « {title} » du tableau ?|Supprimer {title}|Nombre de personnes nécessaires : {count}|Demandes publiées|Toujours ouvertes|À venir",
    "de": "Noch {count} Zeichen|{count} von 5 Plätzen frei|{count} / 5 angehängt|{count} erstellt|„{title}“ von der Pinnwand entfernen?|{title} löschen|Benötigte Personenanzahl: {count}|Veröffentlichte Anfragen|Noch offen|Demnächst",
    "el": "Απομένουν {count} χαρακτήρες|{count} από τις 5 θέσεις είναι ελεύθερες|Επισυνάφθηκαν {count} / 5|Δημιουργήθηκαν {count}|Να αφαιρεθεί το «{title}» από τον πίνακα;|Διαγραφή {title}|Απαιτούμενος αριθμός ατόμων: {count}|Δημοσιευμένα αιτήματα|Παραμένουν ανοιχτά|Προσεχώς",
    "gu": "હજુ {count} અક્ષરો બાકી|5માંથી {count} જગ્યાઓ ખાલી|જોડ્યા {count} / 5|{count} બનાવ્યા|બોર્ડમાંથી “{title}” દૂર કરવું?|{title} કાઢી નાખો|જરૂરી લોકોની સંખ્યા: {count}|પોસ્ટ કરેલી વિનંતીઓ|હજી ખુલ્લી|આગામી",
    "he": "נותרו {count} תווים|{count} מתוך 5 מקומות פנויים|צורפו {count} / 5|נוצרו {count}|להסיר את „{title}” מהלוח?|מחיקת {title}|מספר האנשים הנדרש: {count}|בקשות שפורסמו|עדיין פתוחות|בקרוב",
    "hi": "{count} अक्षर बाकी|5 में से {count} जगहें खाली|{count} / 5 संलग्न|{count} बनाए गए|बोर्ड से “{title}” हटाएँ?|{title} हटाएँ|आवश्यक लोगों की संख्या: {count}|पोस्ट किए गए अनुरोध|अभी खुले|आने वाले",
    "hu": "Még {count} karakter|{count} szabad hely az 5-ből|Csatolva: {count} / 5|{count} létrehozva|Eltávolítod a tábláról: „{title}”?|{title} törlése|Szükséges személyek száma: {count}|Közzétett kérések|Még nyitva|Közelgő",
    "id": "Sisa {count} karakter|{count} dari 5 slot tersedia|{count} / 5 terlampir|{count} dibuat|Hapus “{title}” dari papan?|Hapus {title}|Jumlah orang yang dibutuhkan: {count}|Permintaan diposting|Masih terbuka|Mendatang",
    "it": "Restano {count} caratteri|{count} posti liberi su 5|Allegate {count} / 5|{count} creati|Rimuovere “{title}” dalla bacheca?|Elimina {title}|Persone richieste: {count}|Richieste pubblicate|Ancora aperte|In arrivo",
    "ja": "残り{count}文字|5枠中{count}枠が空き|添付 {count} / 5|{count}件作成|掲示板から「{title}」を削除しますか？|{title}を削除|必要人数：{count}|投稿済みの依頼|引き続き受付中|近日予定",
    "kn": "ಇನ್ನೂ {count} ಅಕ್ಷರಗಳು|5ರಲ್ಲಿ {count} ಸ್ಥಳಗಳು ಖಾಲಿ|ಲಗತ್ತಿಸಲಾಗಿದೆ {count} / 5|{count} ರಚಿಸಲಾಗಿದೆ|ಫಲಕದಿಂದ “{title}” ತೆಗೆದುಹಾಕಬೇಕೇ?|{title} ಅಳಿಸಿ|ಅಗತ್ಯವಿರುವ ಜನರ ಸಂಖ್ಯೆ: {count}|ಪ್ರಕಟಿಸಿದ ವಿನಂತಿಗಳು|ಇನ್ನೂ ತೆರೆದಿವೆ|ಮುಂದಿನವು",
    "ko": "{count}자 남음|5자리 중 {count}자리 남음|첨부 {count} / 5|{count}개 생성됨|게시판에서 “{title}”을(를) 삭제할까요?|{title} 삭제|필요한 인원: {count}|게시된 요청|아직 열려 있음|예정",
    "ml": "ഇനി {count} അക്ഷരങ്ങൾ|5 ഇടങ്ങളിൽ {count} ഒഴിവുണ്ട്|ചേർത്തത് {count} / 5|{count} സൃഷ്ടിച്ചു|ബോർഡിൽ നിന്ന് “{title}” നീക്കണോ?|{title} നീക്കം ചെയ്യുക|ആവശ്യമായ ആളുകളുടെ എണ്ണം: {count}|പോസ്റ്റ് ചെയ്ത അഭ്യർത്ഥനകൾ|ഇപ്പോഴും തുറന്നിരിക്കുന്നു|വരാനിരിക്കുന്നത്",
    "mr": "आणखी {count} अक्षरे|५ पैकी {count} जागा रिकाम्या|जोडले {count} / 5|{count} तयार केले|फलकावरून “{title}” काढायचे?|{title} हटवा|आवश्यक लोकांची संख्या: {count}|पोस्ट केलेल्या विनंत्या|अजून खुल्या|आगामी",
    "ne": "{count} अक्षर बाँकी|५ मध्ये {count} स्थान खाली|संलग्न {count} / ५|{count} सिर्जना भए|बोर्डबाट “{title}” हटाउने?|{title} मेटाउनुहोस्|आवश्यक मानिसको सङ्ख्या: {count}|पोस्ट गरिएका अनुरोधहरू|अझै खुला|आउँदै गरेका",
    "fa": "{count} نویسه باقی مانده|{count} جای خالی از ۵ جایگاه|پیوست‌شده {count} / ۵|{count} مورد ایجاد شد|«{title}» از تابلو برداشته شود؟|حذف {title}|تعداد افراد موردنیاز: {count}|درخواست‌های منتشرشده|همچنان باز|پیش رو",
    "pl": "Pozostało {count} znaków|Wolne miejsca: {count} z 5|Załączono {count} / 5|Utworzono {count}|Usunąć „{title}” z tablicy?|Usuń {title}|Wymagana liczba osób: {count}|Opublikowane prośby|Nadal otwarte|Nadchodzące",
    "pt": "Restam {count} caracteres|{count} de 5 vagas livres|{count} / 5 anexadas|{count} criados|Remover “{title}” do quadro?|Eliminar {title}|Número de pessoas necessárias: {count}|Pedidos publicados|Ainda abertos|A seguir",
    "ro": "Mai sunt {count} caractere|{count} locuri libere din 5|Atașate {count} / 5|{count} create|Elimini „{title}” de pe panou?|Șterge {title}|Numărul de persoane necesare: {count}|Cereri publicate|Încă deschise|În curând",
    "es": "Quedan {count} caracteres|{count} de 5 plazas libres|{count} / 5 adjuntas|{count} creadas|¿Quitar «{title}» del tablón?|Eliminar {title}|Personas necesarias: {count}|Solicitudes publicadas|Siguen abiertas|Próximas",
    "sw": "Herufi {count} zimebaki|Nafasi {count} kati ya 5 ziko wazi|Zimeambatishwa {count} / 5|{count} zimeundwa|Uondoe “{title}” kwenye ubao?|Futa {title}|Idadi ya watu wanaohitajika: {count}|Maombi yaliyochapishwa|Bado wazi|Yanayokuja",
    "sv": "{count} tecken kvar|{count} av 5 platser lediga|{count} / 5 bifogade|{count} skapade|Ta bort ”{title}” från tavlan?|Ta bort {title}|Antal personer som behövs: {count}|Publicerade förfrågningar|Fortfarande öppna|Kommande",
    "ta": "மேலும் {count} எழுத்துகள்|5 இடங்களில் {count} காலியாக உள்ளன|இணைக்கப்பட்டவை {count} / 5|{count} உருவாக்கப்பட்டன|பலகையிலிருந்து “{title}” அகற்றவா?|{title} ஐ நீக்கு|தேவையான நபர்களின் எண்ணிக்கை: {count}|பதிவிட்ட கோரிக்கைகள்|இன்னும் திறந்தவை|வரவிருப்பவை",
    "te": "ఇంకా {count} అక్షరాలు|5 స్థానాల్లో {count} ఖాళీ|జతచేసినవి {count} / 5|{count} సృష్టించబడ్డాయి|బోర్డు నుంచి “{title}” తొలగించాలా?|{title} తొలగించండి|అవసరమైన వ్యక్తుల సంఖ్య: {count}|పోస్ట్ చేసిన అభ్యర్థనలు|ఇంకా తెరిచి ఉన్నాయి|రాబోయేవి",
    "th": "เหลืออีก {count} ตัวอักษร|ว่าง {count} จาก 5 ช่อง|แนบแล้ว {count} / 5|สร้างแล้ว {count}|นำ “{title}” ออกจากกระดานหรือไม่?|ลบ {title}|จำนวนคนที่ต้องการ: {count}|คำขอที่โพสต์แล้ว|ยังเปิดอยู่|เร็ว ๆ นี้",
    "tr": "{count} karakter kaldı|5 yerden {count} tanesi boş|Eklenen {count} / 5|{count} oluşturuldu|“{title}” panodan kaldırılsın mı?|{title} öğesini sil|Gerekli kişi sayısı: {count}|Yayınlanan talepler|Hâlâ açık|Yaklaşan",
    "vi": "Còn {count} ký tự|Còn trống {count} trên 5 vị trí|Đã đính kèm {count} / 5|Đã tạo {count}|Xóa “{title}” khỏi bảng?|Xóa {title}|Số người cần: {count}|Yêu cầu đã đăng|Vẫn đang mở|Sắp tới",
}

_EXPECTED_TEMPLATE_CODES = {
    code for code, _label in LANGUAGE_OPTIONS if code != "en"
}
if set(_HELP_POST_TEMPLATE_ROWS) != _EXPECTED_TEMPLATE_CODES:
    raise ValueError(
        "Help-post template catalogs must cover all non-English locales"
    )
if (
    len(HELP_POST_UI_TEMPLATE_KEYS) != 7
    or len(set(HELP_POST_UI_TEMPLATE_KEYS)) != 7
):
    raise ValueError("Help-post UI template keys must contain 7 unique entries")
if (
    len(HELP_POST_COUNT_LABEL_KEYS) != 3
    or len(set(HELP_POST_COUNT_LABEL_KEYS)) != 3
):
    raise ValueError("Help-post count label keys must contain 3 unique entries")

HELP_POST_TEMPLATE_CATALOGS: dict[str, dict[str, str]] = {
    language: dict(
        zip(
            (*HELP_POST_UI_TEMPLATE_KEYS, *HELP_POST_COUNT_LABEL_KEYS),
            row.split("|"),
            strict=True,
        )
    )
    for language, row in _HELP_POST_TEMPLATE_ROWS.items()
}
