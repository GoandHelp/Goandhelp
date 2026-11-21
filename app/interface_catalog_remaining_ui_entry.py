import reflex as rx

from collections import Counter
from string import Formatter
from app.models import LANGUAGE_OPTIONS

REMAINING_ENTRY_KEYS: tuple[str, ...] = (
    "Loading Go and Help…",
    "Loading Go and Help",
    "Opening the map…",
    "Confirming your payment with Stripe…",
    "Premium Membership",
    "We couldn't confirm that membership",
    "Open this page from your Stripe checkout to confirm a membership.",
    "Back to the map",
    "Go and Help main navigation",
    "New activity",
)
REMAINING_ENTRY_ROWS: dict[str, str] = {
    "am": "Go and Help በመጫን ላይ…|Go and Help በመጫን ላይ|ካርታውን በመክፈት ላይ…|ክፍያዎን ከStripe ጋር በማረጋገጥ ላይ…|ፕሪሚየም አባልነት|ያንን አባልነት ማረጋገጥ አልቻልንም|አባልነትን ለማረጋገጥ ይህን ገጽ ከStripe ክፍያ ገጽዎ ይክፈቱ።|ወደ ካርታው ተመለስ|የGo and Help ዋና አሰሳ|አዲስ እንቅስቃሴ",
    "ar": "جارٍ تحميل Go and Help…|جارٍ تحميل Go and Help|جارٍ فتح الخريطة…|جارٍ تأكيد دفعتك مع Stripe…|العضوية المميزة|لم نتمكن من تأكيد تلك العضوية|افتح هذه الصفحة من صفحة الدفع في Stripe لتأكيد العضوية.|العودة إلى الخريطة|التنقل الرئيسي في Go and Help|نشاط جديد",
    "bn": "Go and Help লোড হচ্ছে…|Go and Help লোড হচ্ছে|মানচিত্র খোলা হচ্ছে…|Stripe-এর মাধ্যমে আপনার পেমেন্ট নিশ্চিত করা হচ্ছে…|প্রিমিয়াম সদস্যপদ|আমরা ওই সদস্যপদ নিশ্চিত করতে পারিনি|সদস্যপদ নিশ্চিত করতে আপনার Stripe পেমেন্ট পৃষ্ঠা থেকে এই পৃষ্ঠা খুলুন।|মানচিত্রে ফিরুন|Go and Help-এর প্রধান নেভিগেশন|নতুন কার্যকলাপ",
    "my": "Go and Help ကို ဖွင့်နေသည်…|Go and Help ကို ဖွင့်နေသည်|မြေပုံကို ဖွင့်နေသည်…|သင့်ငွေပေးချေမှုကို Stripe နှင့် အတည်ပြုနေသည်…|ပရီမီယမ်အဖွဲ့ဝင်ဖြစ်မှု|ထိုအဖွဲ့ဝင်ဖြစ်မှုကို အတည်မပြုနိုင်ခဲ့ပါ|အဖွဲ့ဝင်ဖြစ်မှုကို အတည်ပြုရန် သင့် Stripe ငွေပေးချေမှုစာမျက်နှာမှ ဤစာမျက်နှာကို ဖွင့်ပါ။|မြေပုံသို့ ပြန်သွားရန်|Go and Help အဓိကလမ်းညွှန်|လုပ်ဆောင်ချက်အသစ်",
    "zh": "正在加载 Go and Help…|正在加载 Go and Help|正在打开地图…|正在通过 Stripe 确认你的付款…|高级会员|我们无法确认该会员资格|请从你的 Stripe 结账页面打开此页面以确认会员资格。|返回地图|Go and Help 主导航|新动态",
    "cs": "Načítání Go and Help…|Načítání Go and Help|Otevírání mapy…|Potvrzování vaší platby přes Stripe…|Prémiové členství|Toto členství se nepodařilo potvrdit|Pro potvrzení členství otevřete tuto stránku z platební stránky Stripe.|Zpět na mapu|Hlavní navigace Go and Help|Nová aktivita",
    "da": "Indlæser Go and Help…|Indlæser Go and Help|Åbner kortet…|Bekræfter din betaling med Stripe…|Premiummedlemskab|Vi kunne ikke bekræfte det medlemskab|Åbn denne side fra din Stripe-betalingsside for at bekræfte et medlemskab.|Tilbage til kortet|Go and Helps hovednavigation|Ny aktivitet",
    "nl": "Go and Help wordt geladen…|Go and Help wordt geladen|De kaart wordt geopend…|Je betaling via Stripe wordt bevestigd…|Premiumlidmaatschap|We konden dat lidmaatschap niet bevestigen|Open deze pagina vanuit je Stripe-betaalpagina om een lidmaatschap te bevestigen.|Terug naar de kaart|Hoofdnavigatie van Go and Help|Nieuwe activiteit",
    "fi": "Ladataan Go and Help -palvelua…|Ladataan Go and Help -palvelua|Avataan karttaa…|Vahvistetaan maksuasi Stripen kautta…|Premium-jäsenyys|Emme voineet vahvistaa tätä jäsenyyttä|Avaa tämä sivu Stripen maksusivulta vahvistaaksesi jäsenyyden.|Takaisin kartalle|Go and Help -palvelun päävalikko|Uutta toimintaa",
    "fr": "Chargement de Go and Help…|Chargement de Go and Help|Ouverture de la carte…|Confirmation de votre paiement avec Stripe…|Abonnement premium|Nous n’avons pas pu confirmer cet abonnement|Ouvrez cette page depuis votre page de paiement Stripe pour confirmer un abonnement.|Retour à la carte|Navigation principale de Go and Help|Nouvelle activité",
    "de": "Go and Help wird geladen…|Go and Help wird geladen|Karte wird geöffnet…|Deine Zahlung wird mit Stripe bestätigt…|Premium-Mitgliedschaft|Wir konnten diese Mitgliedschaft nicht bestätigen|Öffne diese Seite über deinen Stripe-Zahlungsvorgang, um eine Mitgliedschaft zu bestätigen.|Zurück zur Karte|Hauptnavigation von Go and Help|Neue Aktivität",
    "el": "Φόρτωση του Go and Help…|Φόρτωση του Go and Help|Άνοιγμα του χάρτη…|Επιβεβαίωση της πληρωμής σας με το Stripe…|Συνδρομή προνομίων|Δεν μπορέσαμε να επιβεβαιώσουμε αυτή τη συνδρομή|Ανοίξτε αυτή τη σελίδα από τη σελίδα πληρωμής σας στο Stripe για να επιβεβαιώσετε μια συνδρομή.|Επιστροφή στον χάρτη|Κύρια πλοήγηση του Go and Help|Νέα δραστηριότητα",
    "gu": "Go and Help લોડ થઈ રહ્યું છે…|Go and Help લોડ થઈ રહ્યું છે|નકશો ખૂલી રહ્યો છે…|Stripe સાથે તમારી ચુકવણીની પુષ્ટિ થઈ રહી છે…|પ્રીમિયમ સભ્યપદ|અમે તે સભ્યપદની પુષ્ટિ કરી શક્યા નહીં|સભ્યપદની પુષ્ટિ કરવા તમારી Stripe ચુકવણીના પૃષ્ઠ પરથી આ પૃષ્ઠ ખોલો.|નકશા પર પાછા જાઓ|Go and Help નું મુખ્ય નેવિગેશન|નવી પ્રવૃત્તિ",
    "he": "Go and Help נטען…|Go and Help נטען|המפה נפתחת…|התשלום שלך מאומת מול Stripe…|מנוי פרימיום|לא הצלחנו לאשר את המנוי הזה|פתחו את הדף הזה מדף התשלום שלכם ב־Stripe כדי לאשר מנוי.|חזרה למפה|הניווט הראשי של Go and Help|פעילות חדשה",
    "hi": "Go and Help लोड हो रहा है…|Go and Help लोड हो रहा है|नक्शा खुल रहा है…|Stripe के साथ आपके भुगतान की पुष्टि हो रही है…|प्रीमियम सदस्यता|हम उस सदस्यता की पुष्टि नहीं कर सके|सदस्यता की पुष्टि के लिए अपने Stripe भुगतान पृष्ठ से यह पृष्ठ खोलें।|नक्शे पर वापस जाएँ|Go and Help का मुख्य नेविगेशन|नई गतिविधि",
    "hu": "A Go and Help betöltése…|A Go and Help betöltése|A térkép megnyitása…|Fizetésed megerősítése a Stripe-pal…|Prémium tagság|Nem tudtuk megerősíteni ezt a tagságot|A tagság megerősítéséhez nyisd meg ezt az oldalt a Stripe fizetési oldaláról.|Vissza a térképhez|A Go and Help fő navigációja|Új tevékenység",
    "id": "Memuat Go and Help…|Memuat Go and Help|Membuka peta…|Mengonfirmasi pembayaran Anda dengan Stripe…|Keanggotaan premium|Kami tidak dapat mengonfirmasi keanggotaan tersebut|Buka halaman ini dari halaman pembayaran Stripe Anda untuk mengonfirmasi keanggotaan.|Kembali ke peta|Navigasi utama Go and Help|Aktivitas baru",
    "it": "Caricamento di Go and Help…|Caricamento di Go and Help|Apertura della mappa…|Conferma del pagamento con Stripe…|Abbonamento premium|Non siamo riusciti a confermare quell’abbonamento|Apri questa pagina dalla tua pagina di pagamento Stripe per confermare un abbonamento.|Torna alla mappa|Navigazione principale di Go and Help|Nuova attività",
    "ja": "Go and Help を読み込み中…|Go and Help を読み込み中|地図を開いています…|Stripe でお支払いを確認中…|プレミアム会員|この会員登録を確認できませんでした|会員登録を確認するには、Stripe のお支払い画面からこのページを開いてください。|地図に戻る|Go and Help のメインナビゲーション|新しい活動",
    "kn": "Go and Help ಲೋಡ್ ಆಗುತ್ತಿದೆ…|Go and Help ಲೋಡ್ ಆಗುತ್ತಿದೆ|ನಕ್ಷೆ ತೆರೆಯುತ್ತಿದೆ…|Stripe ಮೂಲಕ ನಿಮ್ಮ ಪಾವತಿಯನ್ನು ದೃಢಪಡಿಸಲಾಗುತ್ತಿದೆ…|ಪ್ರೀಮಿಯಂ ಸದಸ್ಯತ್ವ|ಆ ಸದಸ್ಯತ್ವವನ್ನು ದೃಢಪಡಿಸಲು ನಮಗೆ ಸಾಧ್ಯವಾಗಲಿಲ್ಲ|ಸದಸ್ಯತ್ವವನ್ನು ದೃಢಪಡಿಸಲು ನಿಮ್ಮ Stripe ಪಾವತಿ ಪುಟದಿಂದ ಈ ಪುಟವನ್ನು ತೆರೆಯಿರಿ.|ನಕ್ಷೆಗೆ ಹಿಂತಿರುಗಿ|Go and Help ಮುಖ್ಯ ನ್ಯಾವಿಗೇಶನ್|ಹೊಸ ಚಟುವಟಿಕೆ",
    "ko": "Go and Help 로딩 중…|Go and Help 로딩 중|지도를 여는 중…|Stripe에서 결제를 확인하는 중…|프리미엄 멤버십|해당 멤버십을 확인할 수 없었습니다|멤버십을 확인하려면 Stripe 결제 페이지에서 이 페이지를 여세요.|지도로 돌아가기|Go and Help 기본 탐색|새 활동",
    "ml": "Go and Help ലോഡ് ചെയ്യുന്നു…|Go and Help ലോഡ് ചെയ്യുന്നു|ഭൂപടം തുറക്കുന്നു…|Stripe വഴി നിങ്ങളുടെ പണമടയ്ക്കൽ സ്ഥിരീകരിക്കുന്നു…|പ്രീമിയം അംഗത്വം|ആ അംഗത്വം സ്ഥിരീകരിക്കാൻ ഞങ്ങൾക്ക് കഴിഞ്ഞില്ല|അംഗത്വം സ്ഥിരീകരിക്കാൻ നിങ്ങളുടെ Stripe പണമടയ്ക്കൽ പേജിൽ നിന്ന് ഈ പേജ് തുറക്കുക.|ഭൂപടത്തിലേക്ക് മടങ്ങുക|Go and Help പ്രധാന നാവിഗേഷൻ|പുതിയ പ്രവർത്തനം",
    "mr": "Go and Help लोड होत आहे…|Go and Help लोड होत आहे|नकाशा उघडत आहे…|Stripe सोबत तुमच्या देयकाची पुष्टी होत आहे…|प्रीमियम सदस्यत्व|आम्ही त्या सदस्यत्वाची पुष्टी करू शकलो नाही|सदस्यत्वाची पुष्टी करण्यासाठी तुमच्या Stripe देयक पृष्ठातून हे पृष्ठ उघडा.|नकाशावर परत जा|Go and Help चे मुख्य नेव्हिगेशन|नवीन क्रियाकलाप",
    "ne": "Go and Help लोड हुँदैछ…|Go and Help लोड हुँदैछ|नक्सा खुल्दैछ…|Stripe मार्फत तपाईंको भुक्तानी पुष्टि हुँदैछ…|प्रिमियम सदस्यता|हामीले त्यो सदस्यता पुष्टि गर्न सकेनौँ|सदस्यता पुष्टि गर्न आफ्नो Stripe भुक्तानी पृष्ठबाट यो पृष्ठ खोल्नुहोस्।|नक्सामा फर्कनुहोस्|Go and Help को मुख्य नेभिगेसन|नयाँ गतिविधि",
    "fa": "در حال بارگذاری Go and Help…|در حال بارگذاری Go and Help|در حال باز کردن نقشه…|در حال تأیید پرداخت شما با Stripe…|عضویت ویژه|نتوانستیم آن عضویت را تأیید کنیم|برای تأیید عضویت، این صفحه را از صفحه پرداخت Stripe خود باز کنید.|بازگشت به نقشه|پیمایش اصلی Go and Help|فعالیت تازه",
    "pl": "Ładowanie Go and Help…|Ładowanie Go and Help|Otwieranie mapy…|Potwierdzanie płatności przez Stripe…|Członkostwo premium|Nie udało się potwierdzić tego członkostwa|Otwórz tę stronę ze strony płatności Stripe, aby potwierdzić członkostwo.|Powrót do mapy|Główna nawigacja Go and Help|Nowa aktywność",
    "pt": "A carregar o Go and Help…|A carregar o Go and Help|A abrir o mapa…|A confirmar o seu pagamento com a Stripe…|Adesão premium|Não conseguimos confirmar essa adesão|Abra esta página a partir da sua página de pagamento Stripe para confirmar uma adesão.|Voltar ao mapa|Navegação principal do Go and Help|Nova atividade",
    "ro": "Se încarcă Go and Help…|Se încarcă Go and Help|Se deschide harta…|Se confirmă plata ta prin Stripe…|Abonament premium|Nu am putut confirma acel abonament|Deschide această pagină din pagina ta de plată Stripe pentru a confirma un abonament.|Înapoi la hartă|Navigarea principală Go and Help|Activitate nouă",
    "es": "Cargando Go and Help…|Cargando Go and Help|Abriendo el mapa…|Confirmando tu pago con Stripe…|Membresía premium|No pudimos confirmar esa membresía|Abre esta página desde tu página de pago de Stripe para confirmar una membresía.|Volver al mapa|Navegación principal de Go and Help|Nueva actividad",
    "sw": "Inapakia Go and Help…|Inapakia Go and Help|Inafungua ramani…|Inathibitisha malipo yako kupitia Stripe…|Uanachama wa kulipia|Hatukuweza kuthibitisha uanachama huo|Fungua ukurasa huu kutoka ukurasa wako wa malipo wa Stripe ili kuthibitisha uanachama.|Rudi kwenye ramani|Urambazaji mkuu wa Go and Help|Shughuli mpya",
    "sv": "Laddar Go and Help…|Laddar Go and Help|Öppnar kartan…|Bekräftar din betalning med Stripe…|Premiummedlemskap|Vi kunde inte bekräfta det medlemskapet|Öppna den här sidan från din Stripe-betalningssida för att bekräfta ett medlemskap.|Tillbaka till kartan|Go and Helps huvudnavigering|Ny aktivitet",
    "ta": "Go and Help ஏற்றப்படுகிறது…|Go and Help ஏற்றப்படுகிறது|வரைபடம் திறக்கப்படுகிறது…|Stripe மூலம் உங்கள் கட்டணம் உறுதிப்படுத்தப்படுகிறது…|பிரீமியம் உறுப்பினர் திட்டம்|அந்த உறுப்பினர் திட்டத்தை உறுதிப்படுத்த முடியவில்லை|உறுப்பினர் திட்டத்தை உறுதிப்படுத்த உங்கள் Stripe கட்டணப் பக்கத்திலிருந்து இந்தப் பக்கத்தைத் திறக்கவும்.|வரைபடத்திற்குத் திரும்பவும்|Go and Help முதன்மை வழிசெலுத்தல்|புதிய செயல்பாடு",
    "te": "Go and Help లోడ్ అవుతోంది…|Go and Help లోడ్ అవుతోంది|మ్యాప్ తెరుచుకుంటోంది…|Stripe ద్వారా మీ చెల్లింపును నిర్ధారిస్తోంది…|ప్రీమియం సభ్యత్వం|ఆ సభ్యత్వాన్ని మేము నిర్ధారించలేకపోయాము|సభ్యత్వాన్ని నిర్ధారించడానికి మీ Stripe చెల్లింపు పేజీ నుండి ఈ పేజీని తెరవండి.|మ్యాప్‌కు తిరిగి వెళ్లండి|Go and Help ప్రధాన నావిగేషన్|కొత్త కార్యాచరణ",
    "th": "กำลังโหลด Go and Help…|กำลังโหลด Go and Help|กำลังเปิดแผนที่…|กำลังยืนยันการชำระเงินของคุณกับ Stripe…|สมาชิกพรีเมียม|เราไม่สามารถยืนยันสมาชิกนั้นได้|เปิดหน้านี้จากหน้าชำระเงิน Stripe ของคุณเพื่อยืนยันสมาชิก|กลับไปที่แผนที่|การนำทางหลักของ Go and Help|กิจกรรมใหม่",
    "tr": "Go and Help yükleniyor…|Go and Help yükleniyor|Harita açılıyor…|Ödemeniz Stripe ile doğrulanıyor…|Premium üyelik|Bu üyeliği doğrulayamadık|Üyeliği doğrulamak için bu sayfayı Stripe ödeme sayfanızdan açın.|Haritaya dön|Go and Help ana gezinme|Yeni etkinlik",
    "vi": "Đang tải Go and Help…|Đang tải Go and Help|Đang mở bản đồ…|Đang xác nhận thanh toán của bạn với Stripe…|Thành viên cao cấp|Chúng tôi không thể xác nhận tư cách thành viên đó|Mở trang này từ trang thanh toán Stripe của bạn để xác nhận tư cách thành viên.|Quay lại bản đồ|Điều hướng chính của Go and Help|Hoạt động mới",
}

_EXPECTED = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if set(REMAINING_ENTRY_ROWS) != _EXPECTED:
    raise ValueError("Remaining entry locale coverage is incomplete")
REMAINING_ENTRY_CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(REMAINING_ENTRY_KEYS, row.split("|"), strict=True))
    for code, row in REMAINING_ENTRY_ROWS.items()
}
_formatter = Formatter()
for _code, _entries in REMAINING_ENTRY_CATALOGS.items():
    for _source, _value in _entries.items():
        if not _value.strip() or _value.casefold() == _source.casefold():
            raise ValueError(
                f"Missing native remaining entry: {_code}: {_source}"
            )
        if Counter(
            slot for _, slot, _, _ in _formatter.parse(_source) if slot
        ) != Counter(
            slot for _, slot, _, _ in _formatter.parse(_value) if slot
        ):
            raise ValueError(
                f"Remaining entry slot mismatch: {_code}: {_source}"
            )
