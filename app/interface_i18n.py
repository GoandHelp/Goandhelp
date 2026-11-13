import reflex as rx

import json
from reflex.vars.base import VarData

from app.interface_catalog_forum import FORUM_LABEL_CATALOGS, FORUM_LABEL_KEYS
from app.interface_catalog_forum_text import (
    FORUM_TEXT_CATALOGS,
    FORUM_TEXT_KEYS,
)
from app.interface_catalog_forum_feedback import (
    FORUM_FEEDBACK_CATALOGS,
    FORUM_FEEDBACK_KEYS,
)
from app.interface_catalog_welcome import STORY_CATALOGS, STORY_KEYS
from app.interface_catalog_entry import ENTRY_CATALOGS, ENTRY_KEYS
from app.interface_catalog_confirmation import (
    CONFIRMATION_CATALOGS,
    CONFIRMATION_KEYS,
)
from app.interface_catalog_entry_feedback import (
    ENTRY_FEEDBACK_CATALOGS,
    ENTRY_FEEDBACK_KEYS,
)
from app.interface_catalog_entry_templates import (
    ENTRY_TEMPLATE_CATALOGS,
    ENTRY_TEMPLATE_KEYS,
)
from app.interface_catalog_shared import SHARED_CATALOGS, SHARED_KEYS
from app.interface_catalog_settings import SETTINGS_CATALOGS, SETTINGS_KEYS
from app.interface_catalog_settings_notifications import (
    SETTINGS_NOTIFICATION_CATALOGS,
    SETTINGS_NOTIFICATION_KEYS,
)
from app.interface_catalog_reviews import REVIEW_CATALOGS, REVIEW_KEYS
from app.interface_catalog_map import MAP_COPY_CATALOGS, MAP_COPY_KEYS
from app.interface_catalog_auth import AUTH_COPY_CATALOGS, AUTH_COPY_KEYS
from app.interface_catalog_auth_feedback import (
    AUTH_FEEDBACK_CATALOGS,
    AUTH_FEEDBACK_KEYS,
)
from app.interface_catalog_tour import TOUR_COPY_CATALOGS, TOUR_COPY_KEYS
from app.interface_catalog_onboarding import (
    EXTRA_TITLE_ROWS,
    LANGUAGE_CHOICE_CATALOGS,
    LANGUAGE_CHOICE_KEYS,
)
from app.interface_catalog_setup_privacy import (
    SETUP_PRIVACY_CATALOGS,
    SETUP_PRIVACY_KEYS,
)
from app.interface_catalog_events import EVENT_KEYS, EVENT_TRANSLATIONS
from app.interface_catalog_account_password import (
    ACCOUNT_PASSWORD_CATALOGS,
    ACCOUNT_PASSWORD_KEYS,
)
from app.interface_catalog_block import BLOCK_CATALOGS, BLOCK_KEYS
from app.interface_catalog_report import REPORT_CATALOGS, REPORT_KEYS
from app.interface_catalog_guest_intro_verification import (
    GUEST_INTRO_VERIFICATION_CATALOGS,
    GUEST_INTRO_VERIFICATION_KEYS,
)
from app.interface_catalog_legal import LEGAL_CATALOGS, LEGAL_KEYS
from app.interface_catalog_search_filters import (
    SEARCH_FILTER_CATALOGS,
    SEARCH_FILTER_KEYS,
)

# Source strings are stable keys. Never pass member-authored text to ui().
CORE_KEYS = "Continue|Back|Next|Finish|Profile|Requests|Map|Community|Inbox|Forum|Events|Reviews|Settings|Notifications|Search filters|Send|Cancel|Close|Save changes|App Language|Choose your language|Welcome to Go and Help|Languages|Get help|Give help|Your location|Skip for now|New|Email|Password|Sign in|Register".split(
    "|"
)
CORE_ROWS: dict[str, str] = {
    "am": "ቀጥል|ተመለስ|ቀጣይ|ጨርስ|መገለጫ|ጥያቄዎች|ካርታ|ማህበረሰብ|የገቢ መልዕክት|መድረክ|ዝግጅቶች|ግምገማዎች|ቅንብሮች|ማሳወቂያዎች|የፍለጋ ማጣሪያዎች|ላክ|ሰርዝ|ዝጋ|ለውጦችን አስቀምጥ|የመተግበሪያ ቋንቋ|ቋንቋዎን ይምረጡ|ወደ Go and Help እንኳን ደህና መጡ|ቋንቋዎች|እርዳታ ያግኙ|እርዳታ ይስጡ|የእርስዎ አካባቢ|ለአሁን ዝለል|አዲስ|ኢሜይል|የይለፍ ቃል|ግባ|ይመዝገቡ",
    "ar": "متابعة|رجوع|التالي|إنهاء|الملف الشخصي|الطلبات|الخريطة|المجتمع|الوارد|المنتدى|الفعاليات|التقييمات|الإعدادات|الإشعارات|مرشحات البحث|إرسال|إلغاء|إغلاق|حفظ التغييرات|لغة التطبيق|اختر لغتك|مرحبًا بك في Go and Help|اللغات|احصل على مساعدة|قدّم المساعدة|موقعك|تخطي الآن|جديد|البريد الإلكتروني|كلمة المرور|تسجيل الدخول|التسجيل",
    "bn": "চালিয়ে যান|ফিরে যান|পরবর্তী|শেষ করুন|প্রোফাইল|অনুরোধ|মানচিত্র|সম্প্রদায়|ইনবক্স|ফোরাম|অনুষ্ঠান|পর্যালোচনা|সেটিংস|বিজ্ঞপ্তি|অনুসন্ধান ফিল্টার|পাঠান|বাতিল|বন্ধ|পরিবর্তন সংরক্ষণ|অ্যাপের ভাষা|আপনার ভাষা বেছে নিন|Go and Help-এ স্বাগতম|ভাষা|সাহায্য নিন|সাহায্য দিন|আপনার অবস্থান|এখন এড়িয়ে যান|নতুন|ইমেইল|পাসওয়ার্ড|সাইন ইন|নিবন্ধন",
    "my": "ဆက်လုပ်ရန်|နောက်သို့|ရှေ့သို့|ပြီးဆုံးရန်|ကိုယ်ရေးအချက်အလက်|တောင်းဆိုချက်များ|မြေပုံ|အသိုင်းအဝိုင်း|ဝင်စာ|ဖိုရမ်|ပွဲများ|သုံးသပ်ချက်များ|ဆက်တင်များ|အသိပေးချက်များ|ရှာဖွေမှုစစ်ထုတ်မှုများ|ပို့ရန်|ပယ်ဖျက်ရန်|ပိတ်ရန်|ပြောင်းလဲမှုများသိမ်းရန်|အက်ပ်ဘာသာစကား|သင့်ဘာသာစကားကိုရွေးပါ|Go and Help မှကြိုဆိုပါသည်|ဘာသာစကားများ|အကူအညီရယူရန်|အကူအညီပေးရန်|သင့်တည်နေရာ|ယခုကျော်ရန်|အသစ်|အီးမေးလ်|စကားဝှက်|ဝင်ရန်|စာရင်းသွင်းရန်",
    "zh": "继续|返回|下一步|完成|个人资料|请求|地图|社区|收件箱|论坛|活动|评价|设置|通知|搜索筛选|发送|取消|关闭|保存更改|应用语言|选择你的语言|欢迎来到 Go and Help|语言|获得帮助|提供帮助|你的位置|暂时跳过|新建|电子邮箱|密码|登录|注册",
    "cs": "Pokračovat|Zpět|Další|Dokončit|Profil|Žádosti|Mapa|Komunita|Doručená pošta|Fórum|Události|Hodnocení|Nastavení|Oznámení|Filtry vyhledávání|Odeslat|Zrušit|Zavřít|Uložit změny|Jazyk aplikace|Vyberte svůj jazyk|Vítejte v Go and Help|Jazyky|Získat pomoc|Poskytnout pomoc|Vaše poloha|Prozatím přeskočit|Nové|E-mail|Heslo|Přihlásit se|Registrovat se",
    "da": "Fortsæt|Tilbage|Næste|Afslut|Profil|Anmodninger|Kort|Fællesskab|Indbakke|Forum|Begivenheder|Anmeldelser|Indstillinger|Notifikationer|Søgefiltre|Send|Annuller|Luk|Gem ændringer|Appens sprog|Vælg dit sprog|Velkommen til Go and Help|Sprog|Få hjælp|Giv hjælp|Din placering|Spring over nu|Ny|E-mail|Adgangskode|Log ind|Registrer",
    "nl": "Doorgaan|Terug|Volgende|Voltooien|Profiel|Verzoeken|Kaart|Gemeenschap|Postvak IN|Forum|Evenementen|Beoordelingen|Instellingen|Meldingen|Zoekfilters|Verzenden|Annuleren|Sluiten|Wijzigingen opslaan|App-taal|Kies je taal|Welkom bij Go and Help|Talen|Hulp krijgen|Hulp bieden|Je locatie|Voorlopig overslaan|Nieuw|E-mail|Wachtwoord|Inloggen|Registreren",
    "fi": "Jatka|Takaisin|Seuraava|Valmis|Profiili|Pyynnöt|Kartta|Yhteisö|Saapuneet|Foorumi|Tapahtumat|Arvostelut|Asetukset|Ilmoitukset|Hakusuodattimet|Lähetä|Peruuta|Sulje|Tallenna muutokset|Sovelluksen kieli|Valitse kielesi|Tervetuloa Go and Help -palveluun|Kielet|Saa apua|Anna apua|Sijaintisi|Ohita nyt|Uusi|Sähköposti|Salasana|Kirjaudu sisään|Rekisteröidy",
    "fr": "Continuer|Retour|Suivant|Terminer|Profil|Demandes|Carte|Communauté|Boîte de réception|Forum|Événements|Avis|Paramètres|Notifications|Filtres de recherche|Envoyer|Annuler|Fermer|Enregistrer les modifications|Langue de l’application|Choisissez votre langue|Bienvenue sur Go and Help|Langues|Recevoir de l’aide|Aider|Votre position|Passer pour le moment|Nouveau|E-mail|Mot de passe|Se connecter|S’inscrire",
    "de": "Weiter|Zurück|Nächste|Abschließen|Profil|Anfragen|Karte|Gemeinschaft|Posteingang|Forum|Veranstaltungen|Bewertungen|Einstellungen|Benachrichtigungen|Suchfilter|Senden|Abbrechen|Schließen|Änderungen speichern|App-Sprache|Wähle deine Sprache|Willkommen bei Go and Help|Sprachen|Hilfe erhalten|Hilfe geben|Dein Standort|Jetzt überspringen|Neu|E-Mail|Passwort|Anmelden|Registrieren",
    "el": "Συνέχεια|Πίσω|Επόμενο|Τέλος|Προφίλ|Αιτήματα|Χάρτης|Κοινότητα|Εισερχόμενα|Φόρουμ|Εκδηλώσεις|Αξιολογήσεις|Ρυθμίσεις|Ειδοποιήσεις|Φίλτρα αναζήτησης|Αποστολή|Ακύρωση|Κλείσιμο|Αποθήκευση αλλαγών|Γλώσσα εφαρμογής|Επιλέξτε τη γλώσσα σας|Καλώς ήρθατε στο Go and Help|Γλώσσες|Λάβετε βοήθεια|Προσφέρετε βοήθεια|Η τοποθεσία σας|Παράλειψη για τώρα|Νέο|Email|Κωδικός πρόσβασης|Σύνδεση|Εγγραφή",
    "gu": "ચાલુ રાખો|પાછા|આગળ|પૂર્ણ કરો|પ્રોફાઇલ|વિનંતીઓ|નકશો|સમુદાય|ઇનબોક્સ|ફોરમ|કાર્યક્રમો|સમીક્ષાઓ|સેટિંગ્સ|સૂચનાઓ|શોધ ફિલ્ટર|મોકલો|રદ કરો|બંધ કરો|ફેરફારો સાચવો|એપની ભાષા|તમારી ભાષા પસંદ કરો|Go and Help માં સ્વાગત છે|ભાષાઓ|મદદ મેળવો|મદદ કરો|તમારું સ્થાન|હમણાં છોડો|નવું|ઇમેઇલ|પાસવર્ડ|સાઇન ઇન|નોંધણી",
    "ha": "Ci gaba|Komawa|Na gaba|Gama|Bayanan mutum|Buƙatu|Taswira|Al’umma|Saƙonnin shigowa|Dandalin tattaunawa|Taro|Ra’ayoyi|Saituna|Sanarwa|Matatun bincike|Aika|Soke|Rufe|Ajiye canje-canje|Harshen manhaja|Zaɓi harshenka|Barka da zuwa Go and Help|Harsuna|Samu taimako|Ba da taimako|Wurinka|Tsallake yanzu|Sabo|Imel|Kalmar sirri|Shiga|Yi rajista",
    "he": "המשך|חזרה|הבא|סיום|פרופיל|בקשות|מפה|קהילה|דואר נכנס|פורום|אירועים|ביקורות|הגדרות|התראות|מסנני חיפוש|שליחה|ביטול|סגירה|שמירת שינויים|שפת היישום|בחרו את השפה שלכם|ברוכים הבאים ל־Go and Help|שפות|קבלת עזרה|מתן עזרה|המיקום שלכם|דלגו בינתיים|חדש|דוא״ל|סיסמה|כניסה|הרשמה",
    "hi": "जारी रखें|वापस|अगला|पूरा करें|प्रोफ़ाइल|अनुरोध|नक्शा|समुदाय|इनबॉक्स|फ़ोरम|कार्यक्रम|समीक्षाएँ|सेटिंग्स|सूचनाएँ|खोज फ़िल्टर|भेजें|रद्द करें|बंद करें|बदलाव सहेजें|ऐप की भाषा|अपनी भाषा चुनें|Go and Help में आपका स्वागत है|भाषाएँ|मदद लें|मदद करें|आपका स्थान|अभी छोड़ें|नया|ईमेल|पासवर्ड|साइन इन|पंजीकरण",
    "hu": "Folytatás|Vissza|Következő|Befejezés|Profil|Kérések|Térkép|Közösség|Beérkezett üzenetek|Fórum|Események|Értékelések|Beállítások|Értesítések|Keresési szűrők|Küldés|Mégse|Bezárás|Módosítások mentése|Alkalmazás nyelve|Válassz nyelvet|Üdvözöl a Go and Help|Nyelvek|Segítség kérése|Segítség nyújtása|Tartózkodási helyed|Kihagyás most|Új|E-mail|Jelszó|Bejelentkezés|Regisztráció",
    "id": "Lanjutkan|Kembali|Berikutnya|Selesai|Profil|Permintaan|Peta|Komunitas|Kotak masuk|Forum|Acara|Ulasan|Pengaturan|Notifikasi|Filter pencarian|Kirim|Batal|Tutup|Simpan perubahan|Bahasa aplikasi|Pilih bahasa Anda|Selamat datang di Go and Help|Bahasa|Dapatkan bantuan|Berikan bantuan|Lokasi Anda|Lewati untuk sekarang|Baru|Email|Kata sandi|Masuk|Daftar",
    "it": "Continua|Indietro|Avanti|Termina|Profilo|Richieste|Mappa|Comunità|Posta in arrivo|Forum|Eventi|Recensioni|Impostazioni|Notifiche|Filtri di ricerca|Invia|Annulla|Chiudi|Salva modifiche|Lingua dell’app|Scegli la tua lingua|Benvenuto su Go and Help|Lingue|Ricevi aiuto|Offri aiuto|La tua posizione|Salta per ora|Nuovo|Email|Password|Accedi|Registrati",
    "ja": "続ける|戻る|次へ|完了|プロフィール|リクエスト|地図|コミュニティ|受信トレイ|フォーラム|イベント|レビュー|設定|通知|検索フィルター|送信|キャンセル|閉じる|変更を保存|アプリの言語|言語を選択|Go and Help へようこそ|言語|助けを得る|助ける|現在地|今はスキップ|新規|メール|パスワード|ログイン|登録",
    "kn": "ಮುಂದುವರಿಸಿ|ಹಿಂದೆ|ಮುಂದೆ|ಮುಗಿಸಿ|ಪ್ರೊಫೈಲ್|ವಿನಂತಿಗಳು|ನಕ್ಷೆ|ಸಮುದಾಯ|ಇನ್‌ಬಾಕ್ಸ್|ವೇದಿಕೆ|ಕಾರ್ಯಕ್ರಮಗಳು|ವಿಮರ್ಶೆಗಳು|ಸೆಟ್ಟಿಂಗ್‌ಗಳು|ಅಧಿಸೂಚನೆಗಳು|ಹುಡುಕಾಟ ಫಿಲ್ಟರ್‌ಗಳು|ಕಳುಹಿಸಿ|ರದ್ದುಮಾಡಿ|ಮುಚ್ಚಿ|ಬದಲಾವಣೆಗಳನ್ನು ಉಳಿಸಿ|ಆ್ಯಪ್ ಭಾಷೆ|ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ|Go and Help ಗೆ ಸ್ವಾಗತ|ಭಾಷೆಗಳು|ಸಹಾಯ ಪಡೆಯಿರಿ|ಸಹಾಯ ನೀಡಿ|ನಿಮ್ಮ ಸ್ಥಳ|ಈಗ ಬಿಟ್ಟುಬಿಡಿ|ಹೊಸದು|ಇಮೇಲ್|ಪಾಸ್‌ವರ್ಡ್|ಸೈನ್ ಇನ್|ನೋಂದಣಿ",
    "ko": "계속|뒤로|다음|완료|프로필|요청|지도|커뮤니티|받은 편지함|포럼|이벤트|리뷰|설정|알림|검색 필터|보내기|취소|닫기|변경 사항 저장|앱 언어|언어를 선택하세요|Go and Help에 오신 것을 환영합니다|언어|도움 받기|도움 주기|내 위치|지금 건너뛰기|새로 만들기|이메일|비밀번호|로그인|가입",
    "ml": "തുടരുക|പിന്നോട്ട്|അടുത്തത്|പൂർത്തിയാക്കുക|പ്രൊഫൈൽ|അഭ്യർത്ഥനകൾ|ഭൂപടം|സമൂഹം|ഇൻബോക്സ്|ഫോറം|പരിപാടികൾ|അവലോകനങ്ങൾ|ക്രമീകരണങ്ങൾ|അറിയിപ്പുകൾ|തിരയൽ ഫിൽട്ടറുകൾ|അയയ്ക്കുക|റദ്ദാക്കുക|അടയ്ക്കുക|മാറ്റങ്ങൾ സംരക്ഷിക്കുക|ആപ്പിന്റെ ഭാഷ|നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക|Go and Help ലേക്ക് സ്വാഗതം|ഭാഷകൾ|സഹായം നേടുക|സഹായം നൽകുക|നിങ്ങളുടെ സ്ഥാനം|ഇപ്പോൾ ഒഴിവാക്കുക|പുതിയത്|ഇമെയിൽ|പാസ്‌വേഡ്|സൈൻ ഇൻ|രജിസ്റ്റർ",
    "mr": "पुढे चला|मागे|पुढील|पूर्ण करा|प्रोफाइल|विनंत्या|नकाशा|समुदाय|इनबॉक्स|मंच|कार्यक्रम|पुनरावलोकने|सेटिंग्ज|सूचना|शोध फिल्टर|पाठवा|रद्द करा|बंद करा|बदल जतन करा|ॲपची भाषा|तुमची भाषा निवडा|Go and Help मध्ये स्वागत आहे|भाषा|मदत मिळवा|मदत करा|तुमचे स्थान|आत्ता वगळा|नवीन|ईमेल|पासवर्ड|साइन इन|नोंदणी",
    "ne": "जारी राख्नुहोस्|पछाडि|अर्को|पूरा गर्नुहोस्|प्रोफाइल|अनुरोधहरू|नक्सा|समुदाय|इनबक्स|मञ्च|कार्यक्रमहरू|समीक्षाहरू|सेटिङहरू|सूचनाहरू|खोज फिल्टरहरू|पठाउनुहोस्|रद्द गर्नुहोस्|बन्द गर्नुहोस्|परिवर्तन सुरक्षित गर्नुहोस्|एपको भाषा|आफ्नो भाषा छान्नुहोस्|Go and Help मा स्वागत छ|भाषाहरू|मद्दत लिनुहोस्|मद्दत गर्नुहोस्|तपाईंको स्थान|अहिले छोड्नुहोस्|नयाँ|इमेल|पासवर्ड|साइन इन|दर्ता",
    "fa": "ادامه|بازگشت|بعدی|پایان|نمایه|درخواست‌ها|نقشه|جامعه|صندوق ورودی|انجمن|رویدادها|دیدگاه‌ها|تنظیمات|اعلان‌ها|فیلترهای جستجو|ارسال|لغو|بستن|ذخیره تغییرات|زبان برنامه|زبان خود را انتخاب کنید|به Go and Help خوش آمدید|زبان‌ها|کمک بگیرید|کمک کنید|موقعیت شما|فعلاً رد شوید|جدید|ایمیل|رمز عبور|ورود|ثبت‌نام",
    "pl": "Kontynuuj|Wstecz|Dalej|Zakończ|Profil|Prośby|Mapa|Społeczność|Skrzynka odbiorcza|Forum|Wydarzenia|Opinie|Ustawienia|Powiadomienia|Filtry wyszukiwania|Wyślij|Anuluj|Zamknij|Zapisz zmiany|Język aplikacji|Wybierz swój język|Witaj w Go and Help|Języki|Uzyskaj pomoc|Udziel pomocy|Twoja lokalizacja|Pomiń na razie|Nowe|E-mail|Hasło|Zaloguj się|Zarejestruj się",
    "pt": "Continuar|Voltar|Seguinte|Concluir|Perfil|Pedidos|Mapa|Comunidade|Caixa de entrada|Fórum|Eventos|Avaliações|Definições|Notificações|Filtros de pesquisa|Enviar|Cancelar|Fechar|Guardar alterações|Idioma da aplicação|Escolha o seu idioma|Bem-vindo ao Go and Help|Idiomas|Receber ajuda|Dar ajuda|A sua localização|Ignorar por agora|Novo|Email|Palavra-passe|Entrar|Registar",
    "ro": "Continuă|Înapoi|Următorul|Finalizează|Profil|Cereri|Hartă|Comunitate|Mesaje primite|Forum|Evenimente|Recenzii|Setări|Notificări|Filtre de căutare|Trimite|Anulează|Închide|Salvează modificările|Limba aplicației|Alege limba|Bun venit la Go and Help|Limbi|Primește ajutor|Oferă ajutor|Locația ta|Omite deocamdată|Nou|Email|Parolă|Autentificare|Înregistrare",
    "sw": "Endelea|Rudi|Inayofuata|Maliza|Wasifu|Maombi|Ramani|Jumuiya|Kikasha|Jukwaa|Matukio|Maoni|Mipangilio|Arifa|Vichujio vya utafutaji|Tuma|Ghairi|Funga|Hifadhi mabadiliko|Lugha ya programu|Chagua lugha yako|Karibu Go and Help|Lugha|Pata msaada|Toa msaada|Mahali ulipo|Ruka kwa sasa|Mpya|Barua pepe|Nenosiri|Ingia|Jisajili",
    "sv": "Fortsätt|Tillbaka|Nästa|Slutför|Profil|Förfrågningar|Karta|Gemenskap|Inkorg|Forum|Evenemang|Omdömen|Inställningar|Aviseringar|Sökfilter|Skicka|Avbryt|Stäng|Spara ändringar|Appens språk|Välj ditt språk|Välkommen till Go and Help|Språk|Få hjälp|Ge hjälp|Din plats|Hoppa över nu|Ny|E-post|Lösenord|Logga in|Registrera",
    "ta": "தொடரவும்|பின்செல்|அடுத்து|முடிக்கவும்|சுயவிவரம்|கோரிக்கைகள்|வரைபடம்|சமூகம்|இன்பாக்ஸ்|மன்றம்|நிகழ்வுகள்|மதிப்புரைகள்|அமைப்புகள்|அறிவிப்புகள்|தேடல் வடிகட்டிகள்|அனுப்பு|ரத்துசெய்|மூடு|மாற்றங்களைச் சேமி|செயலியின் மொழி|உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்|Go and Help க்கு வரவேற்கிறோம்|மொழிகள்|உதவி பெறுங்கள்|உதவி செய்யுங்கள்|உங்கள் இருப்பிடம்|இப்போது தவிர்|புதியது|மின்னஞ்சல்|கடவுச்சொல்|உள்நுழை|பதிவு செய்",
    "te": "కొనసాగించండి|వెనుకకు|తదుపరి|పూర్తి చేయండి|ప్రొఫైల్|అభ్యర్థనలు|పటం|సమాజం|ఇన్‌బాక్స్|వేదిక|కార్యక్రమాలు|సమీక్షలు|సెట్టింగ్‌లు|నోటిఫికేషన్‌లు|శోధన ఫిల్టర్‌లు|పంపండి|రద్దు చేయండి|మూసివేయండి|మార్పులను సేవ్ చేయండి|యాప్ భాష|మీ భాషను ఎంచుకోండి|Go and Help కు స్వాగతం|భాషలు|సహాయం పొందండి|సహాయం చేయండి|మీ స్థానం|ఇప్పుడు దాటవేయండి|కొత్తది|ఇమెయిల్|పాస్‌వర్డ్|సైన్ ఇన్|నమోదు",
    "th": "ดำเนินการต่อ|ย้อนกลับ|ถัดไป|เสร็จสิ้น|โปรไฟล์|คำขอ|แผนที่|ชุมชน|กล่องข้อความ|กระดานสนทนา|กิจกรรม|รีวิว|การตั้งค่า|การแจ้งเตือน|ตัวกรองการค้นหา|ส่ง|ยกเลิก|ปิด|บันทึกการเปลี่ยนแปลง|ภาษาของแอป|เลือกภาษาของคุณ|ยินดีต้อนรับสู่ Go and Help|ภาษา|รับความช่วยเหลือ|ให้ความช่วยเหลือ|ตำแหน่งของคุณ|ข้ามไปก่อน|ใหม่|อีเมล|รหัสผ่าน|เข้าสู่ระบบ|ลงทะเบียน",
    "tr": "Devam et|Geri|Sonraki|Bitir|Profil|Talepler|Harita|Topluluk|Gelen kutusu|Forum|Etkinlikler|Değerlendirmeler|Ayarlar|Bildirimler|Arama filtreleri|Gönder|İptal|Kapat|Değişiklikleri kaydet|Uygulama dili|Dilinizi seçin|Go and Help’e hoş geldiniz|Diller|Yardım alın|Yardım edin|Konumunuz|Şimdilik atla|Yeni|E-posta|Şifre|Giriş yap|Kaydol",
    "vi": "Tiếp tục|Quay lại|Tiếp theo|Hoàn tất|Hồ sơ|Yêu cầu|Bản đồ|Cộng đồng|Hộp thư đến|Diễn đàn|Sự kiện|Đánh giá|Cài đặt|Thông báo|Bộ lọc tìm kiếm|Gửi|Hủy|Đóng|Lưu thay đổi|Ngôn ngữ ứng dụng|Chọn ngôn ngữ của bạn|Chào mừng đến với Go and Help|Ngôn ngữ|Nhận trợ giúp|Giúp đỡ|Vị trí của bạn|Bỏ qua lúc này|Mới|Email|Mật khẩu|Đăng nhập|Đăng ký",
}
CORE_ROWS["es"] = (
    "Continuar|Atrás|Siguiente|Terminar|Perfil|Solicitudes|Mapa|Comunidad|Bandeja de entrada|Foro|Eventos|Reseñas|Ajustes|Notificaciones|Filtros de búsqueda|Enviar|Cancelar|Cerrar|Guardar cambios|Idioma de la aplicación|Elige tu idioma|Bienvenido a Go and Help|Idiomas|Recibe ayuda|Ayuda a otros|Tu ubicación|Omitir por ahora|Nuevo|Correo electrónico|Contraseña|Iniciar sesión|Registrarse"
)

CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(CORE_KEYS, row.split("|"), strict=True))
    for code, row in CORE_ROWS.items()
}


CATALOGS["es"].update(
    {
        "Community in your hands": "La comunidad en tus manos",
        "What is Go and Help?": "¿Qué es Go and Help?",
        "Offer a reward": "Ofrece una recompensa",
        "Help and travel": "Ayuda y viaja",
        "Join or create an Event for larger projects": "Únete a un evento o crea uno para proyectos más grandes",
        "How can you help?": "¿Cómo puedes ayudar?",
        "Select your Skills and Knowledge that you can help others with": "Selecciona las habilidades y conocimientos con los que puedes ayudar a otros",
        "In what languages can you give and get help?": "¿En qué idiomas puedes ofrecer y recibir ayuda?",
        "Community commitments": "Compromisos de la comunidad",
        "Read them, then confirm you're in.": "Léelos y confirma tu compromiso.",
        "Notifications permissions.": "Permisos de notificaciones.",
        "Need help with a job?": "¿Necesitas ayuda con una tarea?",
        "Go and Help is a community of good people giving and receiving help across a many fields of knowledge": "Go and Help es una comunidad de buenas personas que ofrecen y reciben ayuda en muchos campos del conocimiento",
        "A helper: Someone who gives help": "Una persona que ayuda: alguien que ofrece ayuda",
        "A helpee: someone who receives help": "Una persona que recibe ayuda: alguien que necesita apoyo",
        "Help people with simple or technical tasks": "Ayuda a las personas con tareas sencillas o técnicas",
        "locally or globally": "a nivel local o mundial",
        "All give good Karma...": "Todo genera buen karma...",
        "Whatever tasks in life have not yet accomplished, there may be a helper out there who is happy to help": "Para las tareas que aún no has podido realizar, puede haber alguien dispuesto a ayudarte",
        "Whether a second hand bicycle, vintage music records, lunch, cake or cash.": "Ya sea una bicicleta de segunda mano, discos antiguos, un almuerzo, un pastel o dinero.",
        "Select what you can offer to thank a helper": "Selecciona lo que puedes ofrecer para agradecer la ayuda",
        "Can you give first aid, play a gig or fix a leaky bamboo roof?": "¿Puedes prestar primeros auxilios, dar un concierto o reparar un techo de bambú con goteras?",
        "From Bangkok to Berlin use Go and Help while travelling. Swap your knowledge and skills for food and accommodation.": "De Bangkok a Berlín, usa Go and Help cuando viajes. Intercambia tus conocimientos y habilidades por comida y alojamiento.",
        "Many hands make light work, so joining an event allows many people to come together and help your community.": "Muchas manos aligeran el trabajo. Participar en un evento permite reunir a muchas personas para ayudar a tu comunidad.",
        "Festivals": "Festivales",
        "Community projects": "Proyectos comunitarios",
        "Disaster relief": "Ayuda en desastres",
        "Choose your nationality:": "Elige tu nacionalidad:",
        "Choose your country": "Elige tu país",
        "Choose your username:": "Elige tu nombre de usuario:",
        "3–30 lowercase letters, numbers, periods or underscores": "Entre 3 y 30 letras minúsculas, números, puntos o guiones bajos",
        "Checking availability…": "Comprobando disponibilidad…",
        "Username available": "Nombre de usuario disponible",
        "That username is already taken.": "Ese nombre de usuario ya está en uso.",
        "Any more details?": "¿Algún detalle más?",
        "Optional": "Opcional",
        "You can change these later in your profile.": "Puedes cambiarlos más adelante en tu perfil.",
        "Any other languages:": "Otros idiomas:",
        "Approx": "Aproximada",
        "Off": "Desactivada",
        "When you request help, your location is shown approximately between 500m and 1km away from you.": "Cuando solicitas ayuda, tu ubicación se muestra aproximadamente entre 500 m y 1 km de tu posición real.",
        "Only a confirmed helper is shown your accurate job location": "Solo la persona confirmada para ayudarte ve la ubicación exacta de la tarea",
        "As a helper, setting your location to 'Approximate' allows a helpee to send you direct help requests. Showing your location is not necessary for helping others.": "Como ayudante, activar la ubicación aproximada permite recibir solicitudes directas. No es necesario mostrar tu ubicación para ayudar a otros.",
        "Kindness first": "La amabilidad primero",
        "No harassment, discrimination or pressure — ever.": "Nada de acoso, discriminación ni presión, nunca.",
        "Agree in the app": "Acuerda los detalles en la aplicación",
        "Task, time, place and reward are agreed before you meet.": "Acordad la tarea, la hora, el lugar y la recompensa antes de reuniros.",
        "Meet safely": "Reúnete de forma segura",
        "Public places for first meetings, and share your plan.": "Elegid lugares públicos para la primera reunión y compartid vuestro plan.",
        "Report anything off": "Denuncia los problemas",
        "Use report and block; we read every report.": "Usa las opciones de denunciar y bloquear; leemos todas las denuncias.",
        "Disregard to these rules will result in a blocked account": "Incumplir estas normas puede provocar el bloqueo de la cuenta",
        "I agree to these community rules": "Acepto estas normas de la comunidad",
        "Camera & photos": "Cámara y fotos",
        "For your profile photo and clear pictures of a task.": "Para tu foto de perfil y fotos claras de una tarea.",
        "This choice controls notifications sent to your phone/device for messages, accepted offers and check-in reminders. In-app notifications are always on.": "Esta opción controla las notificaciones de mensajes, ofertas aceptadas y recordatorios en tu dispositivo. Las notificaciones dentro de la aplicación siempre están activadas.",
        "Nothing is requested yet. Your device only asks when you first use a feature.": "Todavía no se solicita ningún permiso. Tu dispositivo solo lo pide al usar una función por primera vez.",
        "Camera and photos permissions.": "Permisos de cámara y fotos.",
        "Turn on": "Activar",
        "Not now": "Ahora no",
        "Post your first help request here": "Publica aquí tu primera solicitud de ayuda",
        "Let's go and help!": "¡Vamos a ayudar!",
        "Saving…": "Guardando…",
        "Your Profile": "Tu perfil",
        "Update your skills": "Actualiza tus habilidades",
        "Start tour": "Iniciar recorrido",
        "Restart tour": "Reiniciar recorrido",
        "Guided tour": "Recorrido guiado",
        "Learn how to navigate the app": "Aprende a usar la aplicación",
        "Take a quick tour of the main controls, or explore on your own.": "Haz un breve recorrido por los controles principales o explora por tu cuenta.",
        "Job Title": "Título de la tarea",
        "Job description": "Descripción de la tarea",
        "Job category": "Categoría de la tarea",
        "Date": "Fecha",
        "Rewards": "Recompensas",
        "Currency": "Moneda",
        "Enter your budget": "Introduce tu presupuesto",
        "Location of this request": "Ubicación de esta solicitud",
        "Your exact pin stays private. Helpers see an approximate area until confirmed.": "Tu ubicación exacta es privada. Las personas ven una zona aproximada hasta que confirmas su ayuda.",
        "optional — defaults to Free": "opcional: gratis por defecto",
        "Choose…": "Elige…",
        "Please specify for each one below": "Especifica cada recompensa a continuación",
        "Ask helper for an estimate price": "Pide un presupuesto a la persona que ayuda",
        "Go and Help receives an 8% fee": "Go and Help recibe una comisión del 8%",
        "My information": "Mi información",
        "My Skills": "Mis habilidades",
        "Sign out": "Cerrar sesión",
        "Ask for help": "Pedir ayuda",
        "Find people": "Buscar personas",
        "Contacts": "Contactos",
        "Profile details": "Detalles del perfil",
        "Local area": "Zona local",
        "Activity": "Actividad",
        "Recent activity": "Actividad reciente",
        "Mark all read": "Marcar todo como leído",
        "Try again": "Intentar de nuevo",
        "No notifications yet": "Todavía no hay notificaciones",
        "New activity matching your preferences will appear here.": "La actividad que coincida con tus preferencias aparecerá aquí.",
        "Loading notifications…": "Cargando notificaciones…",
        "View matching requests": "Ver solicitudes coincidentes",
        "Requests in my field": "Solicitudes en mi especialidad",
        "Messages": "Mensajes",
        "First name": "Nombre",
        "Family name": "Apellidos",
        "Save": "Guardar",
        "Search": "Buscar",
        "Search...": "Buscar...",
        "Search: People, Jobs, Places": "Buscar: personas, tareas, lugares",
        "Interface language is separate from the languages you speak. You can change it later in Settings.": "El idioma de la aplicación es independiente de los idiomas que hablas. Puedes cambiarlo después en Ajustes.",
        "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language.": "Algunos textos aún no están traducidos y aparecerán en inglés. Las publicaciones y mensajes conservan su idioma original.",
        "Could not save language. Please try again.": "No se pudo guardar el idioma. Inténtalo de nuevo.",
    }
)
CATALOGS["fr"].update(
    {
        "Community in your hands": "La communauté entre vos mains",
        "What is Go and Help?": "Qu’est-ce que Go and Help ?",
        "Offer a reward": "Offrez une récompense",
        "Help and travel": "Aidez et voyagez",
        "Join or create an Event for larger projects": "Rejoignez ou créez un événement pour de grands projets",
        "How can you help?": "Comment pouvez-vous aider ?",
        "Select your Skills and Knowledge that you can help others with": "Sélectionnez les compétences et connaissances avec lesquelles vous pouvez aider",
        "In what languages can you give and get help?": "Dans quelles langues pouvez-vous donner et recevoir de l’aide ?",
        "Community commitments": "Engagements communautaires",
        "Read them, then confirm you're in.": "Lisez-les, puis confirmez votre engagement.",
        "Notifications permissions.": "Autorisations de notification.",
        "Need help with a job?": "Besoin d’aide pour une tâche ?",
        "Choose your nationality:": "Choisissez votre nationalité :",
        "Choose your country": "Choisissez votre pays",
        "Choose your username:": "Choisissez votre nom d’utilisateur :",
        "Any more details?": "D’autres précisions ?",
        "Optional": "Facultatif",
        "Any other languages:": "Autres langues :",
        "You can change these later in your profile.": "Vous pourrez modifier ces choix dans votre profil.",
        "I agree to these community rules": "J’accepte ces règles communautaires",
        "Turn on": "Activer",
        "Not now": "Pas maintenant",
        "Saving…": "Enregistrement…",
        "Let's go and help!": "Allons aider !",
        "Post your first help request here": "Publiez ici votre première demande d’aide",
        "Job Title": "Titre de la tâche",
        "Job description": "Description de la tâche",
        "Job category": "Catégorie de la tâche",
        "Rewards": "Récompenses",
        "My information": "Mes informations",
        "My Skills": "Mes compétences",
        "Sign out": "Se déconnecter",
        "Ask for help": "Demander de l’aide",
        "Find people": "Trouver des personnes",
        "Contacts": "Contacts",
        "Messages": "Messages",
        "Start tour": "Commencer la visite",
        "Restart tour": "Recommencer la visite",
        "Learn how to navigate the app": "Apprenez à utiliser l’application",
        "Interface language is separate from the languages you speak. You can change it later in Settings.": "La langue de l’application est distincte des langues que vous parlez. Vous pourrez la modifier dans les paramètres.",
        "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language.": "Certains textes non encore traduits apparaîtront en anglais. Les publications et messages restent dans leur langue d’origine.",
    }
)
CATALOGS["de"].update(
    {
        "Community in your hands": "Gemeinschaft in deinen Händen",
        "What is Go and Help?": "Was ist Go and Help?",
        "Offer a reward": "Biete eine Belohnung an",
        "Help and travel": "Helfen und reisen",
        "Join or create an Event for larger projects": "Tritt einer Veranstaltung für größere Projekte bei oder erstelle eine",
        "How can you help?": "Wie kannst du helfen?",
        "Select your Skills and Knowledge that you can help others with": "Wähle Fähigkeiten und Wissen, mit denen du anderen helfen kannst",
        "In what languages can you give and get help?": "In welchen Sprachen kannst du Hilfe geben und erhalten?",
        "Community commitments": "Gemeinschaftsregeln",
        "Read them, then confirm you're in.": "Lies sie und bestätige deine Zustimmung.",
        "Notifications permissions.": "Benachrichtigungsberechtigungen.",
        "Need help with a job?": "Brauchst du Hilfe bei einer Aufgabe?",
        "Choose your nationality:": "Wähle deine Staatsangehörigkeit:",
        "Choose your country": "Wähle dein Land",
        "Choose your username:": "Wähle deinen Benutzernamen:",
        "Optional": "Optional",
        "Any more details?": "Weitere Angaben?",
        "Any other languages:": "Weitere Sprachen:",
        "Saving…": "Wird gespeichert…",
        "Let's go and help!": "Los geht’s, helfen wir!",
        "I agree to these community rules": "Ich stimme diesen Gemeinschaftsregeln zu",
        "Turn on": "Aktivieren",
        "Not now": "Nicht jetzt",
        "Post your first help request here": "Veröffentliche hier deine erste Hilfeanfrage",
        "Job Title": "Aufgabentitel",
        "Job description": "Aufgabenbeschreibung",
        "Job category": "Aufgabenkategorie",
        "Rewards": "Belohnungen",
        "My information": "Meine Angaben",
        "My Skills": "Meine Fähigkeiten",
        "Sign out": "Abmelden",
        "Ask for help": "Um Hilfe bitten",
        "Find people": "Personen finden",
        "Contacts": "Kontakte",
        "Messages": "Nachrichten",
        "Start tour": "Tour starten",
        "Restart tour": "Tour neu starten",
        "Interface language is separate from the languages you speak. You can change it later in Settings.": "Die App-Sprache ist unabhängig von deinen gesprochenen Sprachen. Du kannst sie später in den Einstellungen ändern.",
        "Some text is not yet translated and will appear in English. Member posts and messages stay in their original language.": "Noch nicht übersetzte Texte erscheinen auf Englisch. Beiträge und Nachrichten bleiben in ihrer Originalsprache.",
    }
)


ONBOARDING_TITLE_KEYS = "What is Go and Help?|Offer a reward|Help and travel|Join or create an Event for larger projects|How can you help?|Community commitments|Notifications permissions.|Need help with a job?".split(
    "|"
)
ONBOARDING_TITLE_ROWS: dict[str, str] = {
    "ar": "ما هو Go and Help؟|قدّم مكافأة|ساعد وسافر|انضم إلى فعالية أو أنشئ واحدة للمشاريع الكبيرة|كيف يمكنك المساعدة؟|التزامات المجتمع|أذونات الإشعارات.|هل تحتاج مساعدة في مهمة؟",
    "bn": "Go and Help কী?|পুরস্কার দিন|সাহায্য ও ভ্রমণ|বড় প্রকল্পের জন্য অনুষ্ঠানে যোগ দিন বা তৈরি করুন|আপনি কীভাবে সাহায্য করতে পারেন?|সম্প্রদায়ের অঙ্গীকার|বিজ্ঞপ্তির অনুমতি।|কাজে সাহায্য দরকার?",
    "zh": "什么是 Go and Help？|提供奖励|帮助与旅行|加入或创建大型项目活动|你能提供什么帮助？|社区承诺|通知权限。|需要帮忙完成任务吗？",
    "hi": "Go and Help क्या है?|इनाम दें|मदद और यात्रा|बड़ी परियोजनाओं के लिए कार्यक्रम बनाएँ या जुड़ें|आप कैसे मदद कर सकते हैं?|समुदाय की प्रतिबद्धताएँ|सूचनाओं की अनुमति।|किसी काम में मदद चाहिए?",
    "id": "Apa itu Go and Help?|Tawarkan imbalan|Bantu dan bepergian|Ikuti atau buat acara untuk proyek besar|Bagaimana Anda dapat membantu?|Komitmen komunitas|Izin notifikasi.|Perlu bantuan untuk tugas?",
    "it": "Che cos’è Go and Help?|Offri una ricompensa|Aiuta e viaggia|Partecipa o crea un evento per progetti più grandi|Come puoi aiutare?|Impegni della comunità|Permessi delle notifiche.|Hai bisogno di aiuto per un lavoro?",
    "ja": "Go and Help とは？|お礼を提供する|助け合いと旅|大きなプロジェクトのイベントに参加・作成|どんなお手伝いができますか？|コミュニティの約束|通知の許可。|仕事の手助けが必要ですか？",
    "ko": "Go and Help란 무엇인가요?|보상 제공하기|도움과 여행|대규모 프로젝트 이벤트에 참여하거나 만들기|어떻게 도울 수 있나요?|커뮤니티 약속|알림 권한.|작업에 도움이 필요하신가요?",
    "nl": "Wat is Go and Help?|Bied een beloning|Help en reis|Doe mee of maak een evenement voor grotere projecten|Hoe kun je helpen?|Gemeenschapsafspraken|Toestemming voor meldingen.|Hulp nodig bij een taak?",
    "pl": "Czym jest Go and Help?|Zaoferuj nagrodę|Pomagaj i podróżuj|Dołącz lub utwórz wydarzenie dla większych projektów|Jak możesz pomóc?|Zobowiązania społeczności|Uprawnienia powiadomień.|Potrzebujesz pomocy w zadaniu?",
    "pt": "O que é Go and Help?|Ofereça uma recompensa|Ajude e viaje|Participe ou crie um evento para projetos maiores|Como pode ajudar?|Compromissos da comunidade|Permissões de notificações.|Precisa de ajuda numa tarefa?",
    "ro": "Ce este Go and Help?|Oferă o recompensă|Ajută și călătorește|Participă sau creează un eveniment pentru proiecte mari|Cum poți ajuta?|Angajamentele comunității|Permisiuni pentru notificări.|Ai nevoie de ajutor cu o sarcină?",
    "sv": "Vad är Go and Help?|Erbjud en belöning|Hjälp och res|Delta i eller skapa ett evenemang för större projekt|Hur kan du hjälpa?|Gemenskapens åtaganden|Behörigheter för aviseringar.|Behöver du hjälp med en uppgift?",
    "sw": "Go and Help ni nini?|Toa zawadi|Saidia na safiri|Jiunge au unda tukio kwa miradi mikubwa|Unaweza kusaidiaje?|Ahadi za jumuiya|Ruhusa za arifa.|Unahitaji msaada kwa kazi?",
    "th": "Go and Help คืออะไร?|เสนอรางวัล|ช่วยเหลือและเดินทาง|เข้าร่วมหรือสร้างกิจกรรมสำหรับโครงการขนาดใหญ่|คุณช่วยอะไรได้บ้าง?|ข้อตกลงของชุมชน|สิทธิ์การแจ้งเตือน|ต้องการความช่วยเหลือในการทำงานไหม?",
    "tr": "Go and Help nedir?|Ödül teklif edin|Yardım edin ve seyahat edin|Büyük projeler için etkinliğe katılın veya oluşturun|Nasıl yardım edebilirsiniz?|Topluluk taahhütleri|Bildirim izinleri.|Bir iş için yardıma mı ihtiyacınız var?",
    "vi": "Go and Help là gì?|Đề nghị phần thưởng|Giúp đỡ và du lịch|Tham gia hoặc tạo sự kiện cho dự án lớn|Bạn có thể giúp như thế nào?|Cam kết cộng đồng|Quyền thông báo.|Cần giúp đỡ với công việc?",
}
for _code, _row in ONBOARDING_TITLE_ROWS.items():
    CATALOGS[_code].update(
        dict(zip(ONBOARDING_TITLE_KEYS, _row.split("|"), strict=True))
    )

CATALOGS["es"].update(
    {
        "Let's go!": "¡Vamos!",
        "Creating your account…": "Creando tu cuenta…",
        "Signing in…": "Iniciando sesión…",
        "Confirm password": "Confirmar contraseña",
        "Phone": "Teléfono",
        "6+ characters": "6 caracteres o más",
        "Search: Contacts, Messages...": "Buscar: contactos, mensajes...",
        "Filters": "Filtros",
        "New message": "Nuevo mensaje",
        "Remove from Inbox": "Quitar de la bandeja de entrada",
        "No messages yet": "Todavía no hay mensajes",
        "No conversations yet": "Todavía no hay conversaciones",
        "Nothing matches that search": "No hay coincidencias",
        "Clear search": "Borrar búsqueda",
        "Clear": "Borrar",
        "clear": "borrar",
        "My contacts": "Mis contactos",
        "Back to Inbox": "Volver a la bandeja de entrada",
        "Show original language": "Mostrar el idioma original",
        "Show on map": "Mostrar en el mapa",
        "Request help": "Solicitar ayuda",
        "Offer help": "Ofrecer ayuda",
        "Description": "Descripción",
        "Send request": "Enviar solicitud",
        "Add contact": "Añadir contacto",
        "Report": "Denunciar",
        "Block": "Bloquear",
    }
)
CATALOGS["fr"].update(
    {
        "Let's go!": "Allons-y !",
        "Creating your account…": "Création du compte…",
        "Signing in…": "Connexion…",
        "First name": "Prénom",
        "Family name": "Nom de famille",
        "Show original language": "Afficher la langue d’origine",
    }
)
CATALOGS["de"].update(
    {
        "Let's go!": "Los geht’s!",
        "Creating your account…": "Konto wird erstellt…",
        "Signing in…": "Anmeldung…",
        "First name": "Vorname",
        "Family name": "Nachname",
        "Show original language": "Originalsprache anzeigen",
    }
)


for _language, _entries in SETUP_PRIVACY_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in SETTINGS_NOTIFICATION_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in SHARED_CATALOGS.items():
    CATALOGS[_language].update(_entries)
    CATALOGS[_language].update(SETTINGS_CATALOGS[_language])
    CATALOGS[_language].update(REVIEW_CATALOGS[_language])
    CATALOGS[_language].update(LANGUAGE_CHOICE_CATALOGS[_language])
    CATALOGS[_language].update(MAP_COPY_CATALOGS[_language])
    CATALOGS[_language].update(AUTH_COPY_CATALOGS[_language])

for _language, _entries in TOUR_COPY_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for language, entries in STORY_CATALOGS.items():
    CATALOGS[language].update(entries)
    CATALOGS[language].update(ENTRY_CATALOGS[language])
    CATALOGS[language].update(CONFIRMATION_CATALOGS[language])
    CATALOGS[language].update(ENTRY_FEEDBACK_CATALOGS[language])
    CATALOGS[language].update(ENTRY_TEMPLATE_CATALOGS[language])
    CATALOGS[language][
        "This reset link has already been used or has expired. Request a fresh one from the sign-in panel."
    ] = f"{ENTRY_CATALOGS[language]['This reset link has already been used or has expired.']} {ENTRY_CATALOGS[language]['Back to sign in']}"
    CATALOGS[language]["Back to sign-in"] = ENTRY_CATALOGS[language][
        "Back to sign in"
    ]

for _language, _entries in AUTH_FEEDBACK_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _key, _value in ENTRY_FEEDBACK_CATALOGS["ha"].items():
    CATALOGS["ha"].setdefault(_key, _value)

for _language, _row in EXTRA_TITLE_ROWS.items():
    CATALOGS[_language].update(
        dict(zip(ONBOARDING_TITLE_KEYS, _row.split("|"), strict=True))
    )

FORUM_KEYS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [
            *FORUM_LABEL_KEYS,
            *FORUM_TEXT_KEYS,
            *FORUM_FEEDBACK_KEYS,
        ]
    )
)
for _language, _entries in FORUM_LABEL_CATALOGS.items():
    CATALOGS[_language].update(_entries)
    CATALOGS[_language].update(FORUM_TEXT_CATALOGS[_language])
    CATALOGS[_language].update(FORUM_FEEDBACK_CATALOGS[_language])

EVENT_CONTEXT_KEYS = {
    "Money",
    "Other",
    "Guided tour",
    "Your session expired — please sign in again.",
}

if any(
    set(_entries) != set(EVENT_KEYS) for _entries in EVENT_TRANSLATIONS.values()
):
    raise ValueError("Events catalog source coverage is incomplete")

for _language, _entries in EVENT_TRANSLATIONS.items():
    CATALOGS[_language].update(
        {
            _key: _value
            for _key, _value in _entries.items()
            if _key not in EVENT_CONTEXT_KEYS
        }
    )

EVENT_CATALOGS: dict[str, dict[str, str]] = {
    _language: {
        key: value
        for key, value in CATALOGS[_language].items()
        if key in EVENT_KEYS
    }
    for _language in EVENT_TRANSLATIONS
}

for _language, _entries in ACCOUNT_PASSWORD_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in BLOCK_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in REPORT_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in GUEST_INTRO_VERIFICATION_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in LEGAL_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

for _language, _entries in SEARCH_FILTER_CATALOGS.items():
    for _key, _value in _entries.items():
        CATALOGS[_language].setdefault(_key, _value)

COMPLETE_KEYS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [
            *CORE_KEYS,
            *SHARED_KEYS,
            *SETTINGS_KEYS,
            *SETTINGS_NOTIFICATION_KEYS,
            *ACCOUNT_PASSWORD_KEYS,
            *BLOCK_KEYS,
            *REPORT_KEYS,
            *GUEST_INTRO_VERIFICATION_KEYS,
            *LEGAL_KEYS,
            *SEARCH_FILTER_KEYS,
            *REVIEW_KEYS,
            *LANGUAGE_CHOICE_KEYS,
            *SETUP_PRIVACY_KEYS,
            *ONBOARDING_TITLE_KEYS,
            *MAP_COPY_KEYS,
            *AUTH_COPY_KEYS,
            *AUTH_FEEDBACK_KEYS,
            *TOUR_COPY_KEYS,
            *STORY_KEYS,
            *ENTRY_KEYS,
            *CONFIRMATION_KEYS,
            *ENTRY_FEEDBACK_KEYS,
            *ENTRY_TEMPLATE_KEYS,
            *FORUM_KEYS,
            *EVENT_KEYS,
            "clear",
            "optional",
        ]
    )
)


def translate(language: str, source: str) -> str:
    return CATALOGS.get(language, {}).get(source, source)


def catalog(language: str) -> dict[str, str]:
    return dict(CATALOGS.get(language, {}))


def ui(source: str | rx.Var[str]) -> rx.Var[str]:
    from app.states.auth_state import AuthState

    return AuthState.interface_text.get(source, source)


def ui_template(
    source: str | rx.Var[str], parameter: str, value: str | rx.Var[str]
) -> rx.Var[str]:
    """Substitute a named slot without reinterpreting its value."""
    template = ui(source)
    replacement = rx.Var.create(value)
    data = VarData.merge(
        template._get_all_var_data(), replacement._get_all_var_data()
    )
    return rx.Var(
        _js_expr=f"({template}).split({json.dumps(f'{{{parameter}}}')}).join({replacement})",
        _var_type=str,
        _var_data=data,
    ).to(str)
