import reflex as rx

from app.models import LANGUAGE_OPTIONS

REMAINING_ACTIONS_KEYS: tuple[str, ...] = (
    "Sending request…",
    "Send contact request",
    "Turn off",
)
REMAINING_ACTIONS_ROWS: dict[str, str] = {
    "am": "ጥያቄውን በመላክ ላይ…|የግንኙነት ጥያቄ ላክ|አሰናክል",
    "ar": "جارٍ إرسال الطلب…|إرسال طلب تواصل|تعطيل",
    "bn": "অনুরোধ পাঠানো হচ্ছে…|যোগাযোগের অনুরোধ পাঠান|নিষ্ক্রিয় করুন",
    "my": "တောင်းဆိုချက် ပို့နေသည်…|အဆက်အသွယ်ပြုရန် တောင်းဆိုချက် ပို့ပါ|ပိတ်ရန်",
    "zh": "正在发送请求…|发送联系请求|停用",
    "cs": "Odesílání žádosti…|Odeslat žádost o kontakt|Vypnout",
    "da": "Sender anmodning…|Send kontaktanmodning|Slå fra",
    "nl": "Verzoek wordt verzonden…|Contactverzoek verzenden|Uitschakelen",
    "fi": "Lähetetään pyyntöä…|Lähetä yhteydenottopyyntö|Poista käytöstä",
    "fr": "Envoi de la demande…|Envoyer une demande de contact|Désactiver",
    "de": "Anfrage wird gesendet…|Kontaktanfrage senden|Deaktivieren",
    "el": "Αποστολή αιτήματος…|Στείλτε αίτημα επικοινωνίας|Απενεργοποίηση",
    "gu": "વિનંતી મોકલાઈ રહી છે…|સંપર્ક માટે વિનંતી મોકલો|નિષ્ક્રિય કરો",
    "he": "הבקשה נשלחת…|שליחת בקשת קשר|השבתה",
    "hi": "अनुरोध भेजा जा रहा है…|संपर्क अनुरोध भेजें|निष्क्रिय करें",
    "hu": "Kérés küldése…|Kapcsolatfelvételi kérés küldése|Kikapcsolás",
    "id": "Mengirim permintaan…|Kirim permintaan kontak|Nonaktifkan",
    "it": "Invio della richiesta…|Invia richiesta di contatto|Disattiva",
    "ja": "リクエストを送信中…|連絡先追加のリクエストを送信|無効にする",
    "kn": "ವಿನಂತಿಯನ್ನು ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ…|ಸಂಪರ್ಕ ವಿನಂತಿಯನ್ನು ಕಳುಹಿಸಿ|ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಿ",
    "ko": "요청을 보내는 중…|연락처 추가 요청 보내기|비활성화",
    "ml": "അഭ്യർത്ഥന അയയ്ക്കുന്നു…|ബന്ധപ്പെടാനുള്ള അഭ്യർത്ഥന അയയ്ക്കുക|പ്രവർത്തനരഹിതമാക്കുക",
    "mr": "विनंती पाठवत आहे…|संपर्काची विनंती पाठवा|निष्क्रिय करा",
    "ne": "अनुरोध पठाइँदै छ…|सम्पर्क अनुरोध पठाउनुहोस्|निष्क्रिय गर्नुहोस्",
    "fa": "در حال ارسال درخواست…|ارسال درخواست ارتباط|غیرفعال کردن",
    "pl": "Wysyłanie prośby…|Wyślij prośbę o kontakt|Wyłącz",
    "pt": "A enviar pedido…|Enviar pedido de contacto|Desativar",
    "ro": "Se trimite cererea…|Trimite cerere de contact|Dezactivează",
    "es": "Enviando solicitud…|Enviar solicitud de contacto|Desactivar",
    "sw": "Inatuma ombi…|Tuma ombi la kuwasiliana|Zima",
    "sv": "Skickar förfrågan…|Skicka kontaktförfrågan|Stäng av",
    "ta": "கோரிக்கை அனுப்பப்படுகிறது…|தொடர்பு கோரிக்கையை அனுப்பவும்|முடக்கவும்",
    "te": "అభ్యర్థన పంపుతోంది…|సంప్రదింపు అభ్యర్థన పంపండి|నిలిపివేయండి",
    "th": "กำลังส่งคำขอ…|ส่งคำขอติดต่อ|ปิดใช้งาน",
    "tr": "İstek gönderiliyor…|İletişim isteği gönder|Devre dışı bırak",
    "vi": "Đang gửi yêu cầu…|Gửi yêu cầu liên hệ|Tắt",
}
if (
    REMAINING_ACTIONS_KEYS
    != ("Sending request…", "Send contact request", "Turn off")
    or len(set(REMAINING_ACTIONS_KEYS)) != 3
):
    raise ValueError("Remaining action source coverage is invalid")
if set(REMAINING_ACTIONS_ROWS) != {
    code for code, _ in LANGUAGE_OPTIONS if code != "en"
}:
    raise ValueError("Remaining action locale coverage is incomplete")
REMAINING_ACTIONS_CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(REMAINING_ACTIONS_KEYS, row.split("|"), strict=True))
    for code, row in REMAINING_ACTIONS_ROWS.items()
}
for _code, _entries in REMAINING_ACTIONS_CATALOGS.items():
    if tuple(_entries) != REMAINING_ACTIONS_KEYS:
        raise ValueError(f"Invalid remaining action keys: {_code}")
    for _source, _value in _entries.items():
        if not _value.strip() or _value.casefold() == _source.casefold():
            raise ValueError(
                f"Invalid remaining action phrase: {_code}: {_source}"
            )
