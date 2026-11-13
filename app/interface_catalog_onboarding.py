import reflex as rx

LANGUAGE_CHOICE_KEYS = (
    "Interface language is separate from the languages you speak. You can change it later in Settings.|Some text is not yet translated and will appear in English. Member posts and messages stay in their original language."
).split("|")
LANGUAGE_CHOICE_ROWS: dict[str, str] = {
    "am": "የመተግበሪያው ቋንቋ ከሚናገሩት ቋንቋዎች የተለየ ነው። በኋላ በቅንብሮች ውስጥ መቀየር ይችላሉ።|አንዳንድ ጽሑፎች ገና አልተተረጎሙም እና በእንግሊዝኛ ይታያሉ። የአባላት ልጥፎች እና መልዕክቶች በመጀመሪያ ቋንቋቸው ይቀራሉ።",
    "ar": "لغة الواجهة منفصلة عن اللغات التي تتحدثها. يمكنك تغييرها لاحقًا في الإعدادات.|بعض النصوص لم تُترجم بعد وستظهر بالإنجليزية. تبقى منشورات الأعضاء ورسائلهم بلغتها الأصلية.",
    "bn": "অ্যাপের ভাষা আর আপনার কথ্য ভাষা আলাদা। পরে সেটিংসে এটি বদলাতে পারবেন।|কিছু লেখা এখনও অনূদিত হয়নি এবং ইংরেজিতে দেখাবে। সদস্যদের পোস্ট ও বার্তা মূল ভাষাতেই থাকবে।",
    "my": "အက်ပ်ဘာသာစကားနှင့် သင်ပြောသောဘာသာစကားများသည် သီးခြားဖြစ်သည်။ နောက်မှ ဆက်တင်များတွင် ပြောင်းနိုင်သည်။|စာသားအချို့ကို ဘာသာမပြန်ရသေး၍ အင်္ဂလိပ်လိုပြမည်။ အဖွဲ့ဝင်များ၏ပို့စ်နှင့်စာများသည် မူရင်းဘာသာစကားအတိုင်းရှိမည်။",
    "zh": "界面语言与你使用的交流语言相互独立。你可以稍后在设置中更改。|部分文字尚未翻译，将以英语显示。成员发布的帖子和消息保留原始语言。",
    "cs": "Jazyk rozhraní je nezávislý na jazycích, kterými mluvíte. Později jej můžete změnit v nastavení.|Některé texty ještě nejsou přeloženy a zobrazí se anglicky. Příspěvky a zprávy členů zůstávají v původním jazyce.",
    "da": "Appens sprog er uafhængigt af de sprog, du taler. Du kan ændre det senere i indstillingerne.|Nogle tekster er endnu ikke oversat og vises på engelsk. Medlemmernes opslag og beskeder forbliver på originalsproget.",
    "nl": "De taal van de app staat los van de talen die je spreekt. Je kunt deze later wijzigen in Instellingen.|Sommige teksten zijn nog niet vertaald en verschijnen in het Engels. Berichten van leden blijven in hun oorspronkelijke taal.",
    "fi": "Sovelluksen kieli on erillinen puhumistasi kielistä. Voit vaihtaa sen myöhemmin asetuksissa.|Joitakin tekstejä ei ole vielä käännetty, ja ne näkyvät englanniksi. Jäsenten julkaisut ja viestit säilyvät alkuperäisellä kielellään.",
    "fr": "La langue de l’application est distincte des langues que vous parlez. Vous pourrez la modifier dans les paramètres.|Certains textes non encore traduits apparaîtront en anglais. Les publications et messages restent dans leur langue d’origine.",
    "de": "Die App-Sprache ist unabhängig von deinen gesprochenen Sprachen. Du kannst sie später in den Einstellungen ändern.|Noch nicht übersetzte Texte erscheinen auf Englisch. Beiträge und Nachrichten bleiben in ihrer Originalsprache.",
    "el": "Η γλώσσα της εφαρμογής είναι ανεξάρτητη από τις γλώσσες που μιλάτε. Μπορείτε να την αλλάξετε αργότερα στις ρυθμίσεις.|Ορισμένα κείμενα δεν έχουν μεταφραστεί ακόμη και θα εμφανίζονται στα αγγλικά. Οι αναρτήσεις και τα μηνύματα των μελών παραμένουν στην αρχική τους γλώσσα.",
    "gu": "એપની ભાષા તમે બોલો છો તે ભાષાઓથી અલગ છે. તમે તેને પછી સેટિંગ્સમાં બદલી શકો છો.|કેટલાક લખાણો હજી અનુવાદિત નથી અને અંગ્રેજીમાં દેખાશે. સભ્યોની પોસ્ટ અને સંદેશા મૂળ ભાષામાં જ રહેશે.",
    "ha": "Harshen manhaja ya bambanta da harsunan da kake magana. Za ka iya sauya shi daga baya a Saituna.|Ba a fassara wasu rubutu ba tukuna kuma za su bayyana da Turanci. Rubutun mambobi da saƙonninsu suna nan a harshensu na asali.",
    "he": "שפת הממשק נפרדת מהשפות שאתם מדברים. תוכלו לשנות אותה בהמשך בהגדרות.|חלק מהטקסטים עדיין לא תורגמו ויופיעו באנגלית. פרסומי החברים וההודעות נשארים בשפת המקור.",
    "hi": "ऐप की भाषा आपकी बोली जाने वाली भाषाओं से अलग है। आप इसे बाद में सेटिंग्स में बदल सकते हैं।|कुछ पाठ का अभी अनुवाद नहीं हुआ है और वह अंग्रेज़ी में दिखेगा। सदस्यों की पोस्ट और संदेश अपनी मूल भाषा में ही रहेंगे।",
    "hu": "Az alkalmazás nyelve független az általad beszélt nyelvektől. Később a beállításokban módosíthatod.|Néhány szöveg még nincs lefordítva, és angolul jelenik meg. A tagok bejegyzései és üzenetei az eredeti nyelvükön maradnak.",
    "id": "Bahasa antarmuka terpisah dari bahasa yang Anda gunakan untuk berbicara. Anda dapat mengubahnya nanti di Pengaturan.|Sebagian teks belum diterjemahkan dan akan tampil dalam bahasa Inggris. Postingan dan pesan anggota tetap dalam bahasa aslinya.",
    "it": "La lingua dell’app è distinta dalle lingue che parli. Puoi cambiarla in seguito nelle Impostazioni.|Alcuni testi non sono ancora tradotti e appariranno in inglese. I post e i messaggi dei membri restano nella lingua originale.",
    "ja": "アプリの言語と、会話に使う言語は別々に設定できます。後で設定から変更できます。|まだ翻訳されていない一部の文章は英語で表示されます。メンバーの投稿やメッセージは元の言語のままです。",
    "kn": "ಆ್ಯಪ್‌ನ ಭಾಷೆ ನೀವು ಮಾತನಾಡುವ ಭಾಷೆಗಳಿಂದ ಪ್ರತ್ಯೇಕವಾಗಿದೆ. ನಂತರ ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಬದಲಾಯಿಸಬಹುದು.|ಕೆಲವು ಪಠ್ಯಗಳನ್ನು ಇನ್ನೂ ಅನುವಾದಿಸಿಲ್ಲ ಮತ್ತು ಅವು ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಕಾಣುತ್ತವೆ. ಸದಸ್ಯರ ಪೋಸ್ಟ್‌ಗಳು ಮತ್ತು ಸಂದೇಶಗಳು ಮೂಲ ಭಾಷೆಯಲ್ಲೇ ಉಳಿಯುತ್ತವೆ.",
    "ko": "앱 언어는 대화에 사용하는 언어와 별도로 설정합니다. 나중에 설정에서 변경할 수 있습니다.|아직 번역되지 않은 일부 문구는 영어로 표시됩니다. 회원의 게시물과 메시지는 원래 언어로 유지됩니다.",
    "ml": "ആപ്പിന്റെ ഭാഷ നിങ്ങൾ സംസാരിക്കുന്ന ഭാഷകളിൽ നിന്ന് വേറിട്ടതാണ്. പിന്നീട് ക്രമീകരണങ്ങളിൽ മാറ്റാം.|ചില വാചകങ്ങൾ ഇനിയും വിവർത്തനം ചെയ്തിട്ടില്ല; അവ ഇംഗ്ലീഷിൽ കാണും. അംഗങ്ങളുടെ പോസ്റ്റുകളും സന്ദേശങ്ങളും മൂലഭാഷയിൽ തുടരും.",
    "mr": "ॲपची भाषा तुम्ही बोलता त्या भाषांपासून वेगळी आहे. ती नंतर सेटिंग्जमध्ये बदलता येते.|काही मजकूर अजून अनुवादित नाही आणि इंग्रजीत दिसेल. सदस्यांच्या पोस्ट आणि संदेश त्यांच्या मूळ भाषेतच राहतील.",
    "ne": "एपको भाषा तपाईंले बोल्ने भाषाहरूभन्दा अलग हो। पछि सेटिङमा परिवर्तन गर्न सक्नुहुन्छ।|केही पाठ अझै अनुवादित छैनन् र अङ्ग्रेजीमा देखिनेछन्। सदस्यका पोस्ट र सन्देश मूल भाषामै रहनेछन्।",
    "fa": "زبان رابط برنامه از زبان‌هایی که صحبت می‌کنید جداست. می‌توانید بعداً آن را در تنظیمات تغییر دهید.|بعضی متن‌ها هنوز ترجمه نشده‌اند و به انگلیسی نمایش داده می‌شوند. نوشته‌ها و پیام‌های اعضا به زبان اصلی باقی می‌مانند.",
    "pl": "Język aplikacji jest niezależny od języków, którymi mówisz. Możesz go później zmienić w ustawieniach.|Niektóre teksty nie są jeszcze przetłumaczone i pojawią się po angielsku. Posty i wiadomości członków pozostają w oryginalnym języku.",
    "pt": "O idioma da aplicação é independente dos idiomas que fala. Pode alterá-lo mais tarde nas Definições.|Alguns textos ainda não estão traduzidos e aparecerão em inglês. As publicações e mensagens dos membros mantêm o idioma original.",
    "ro": "Limba interfeței este separată de limbile pe care le vorbești. O poți schimba mai târziu în Setări.|Unele texte nu sunt încă traduse și vor apărea în engleză. Postările și mesajele membrilor rămân în limba originală.",
    "es": "El idioma de la aplicación es independiente de los idiomas que hablas. Puedes cambiarlo después en Ajustes.|Algunos textos aún no están traducidos y aparecerán en inglés. Las publicaciones y mensajes conservan su idioma original.",
    "sw": "Lugha ya programu ni tofauti na lugha unazozungumza. Unaweza kuibadilisha baadaye kwenye Mipangilio.|Baadhi ya maandishi bado hayajatafsiriwa na yataonekana kwa Kiingereza. Machapisho na ujumbe wa wanachama hubaki katika lugha yao ya asili.",
    "sv": "Appens språk är skilt från de språk du talar. Du kan ändra det senare i Inställningar.|Vissa texter är ännu inte översatta och visas på engelska. Medlemmarnas inlägg och meddelanden förblir på originalspråket.",
    "ta": "செயலியின் மொழி நீங்கள் பேசும் மொழிகளிலிருந்து தனியானது. பிறகு அமைப்புகளில் மாற்றலாம்.|சில உரைகள் இன்னும் மொழிபெயர்க்கப்படவில்லை; அவை ஆங்கிலத்தில் தோன்றும். உறுப்பினர்களின் பதிவுகளும் செய்திகளும் மூல மொழியிலேயே இருக்கும்.",
    "te": "యాప్ భాష మీరు మాట్లాడే భాషలకు వేరుగా ఉంటుంది. తర్వాత సెట్టింగ్‌లలో మార్చవచ్చు.|కొన్ని వచనాలు ఇంకా అనువదించబడలేదు, అవి ఆంగ్లంలో కనిపిస్తాయి. సభ్యుల పోస్ట్‌లు, సందేశాలు అసలు భాషలోనే ఉంటాయి.",
    "th": "ภาษาของแอปแยกจากภาษาที่คุณพูด คุณเปลี่ยนได้ภายหลังในการตั้งค่า|ข้อความบางส่วนยังไม่ได้แปลและจะแสดงเป็นภาษาอังกฤษ โพสต์และข้อความของสมาชิกจะคงภาษาต้นฉบับไว้",
    "tr": "Uygulama dili konuştuğunuz dillerden ayrıdır. Daha sonra Ayarlar’dan değiştirebilirsiniz.|Bazı metinler henüz çevrilmedi ve İngilizce görünecek. Üyelerin gönderileri ve mesajları özgün dillerinde kalır.",
    "vi": "Ngôn ngữ giao diện tách biệt với ngôn ngữ bạn nói. Bạn có thể thay đổi sau trong Cài đặt.|Một số văn bản chưa được dịch và sẽ hiển thị bằng tiếng Anh. Bài đăng và tin nhắn của thành viên giữ nguyên ngôn ngữ gốc.",
}

# Complete the locales missing from the existing onboarding heading catalog.
EXTRA_TITLE_ROWS: dict[str, str] = {
    "am": "Go and Help ምንድን ነው?|ሽልማት አቅርብ|እርዳታ እና ጉዞ|ለትልቅ ፕሮጀክቶች ዝግጅት ይቀላቀሉ ወይም ይፍጠሩ|እንዴት መርዳት ይችላሉ?|የማህበረሰብ ቃል ኪዳኖች|የማሳወቂያ ፈቃዶች።|ለስራ እርዳታ ይፈልጋሉ?",
    "my": "Go and Help ဆိုတာဘာလဲ?|ဆုလာဘ်ကမ်းလှမ်းရန်|ကူညီခြင်းနှင့်ခရီးသွားခြင်း|ပရောဂျက်ကြီးများအတွက် ပွဲတစ်ခုပါဝင်ပါ သို့မဟုတ် ဖန်တီးပါ|သင်ဘယ်လိုကူညီနိုင်သလဲ?|အသိုင်းအဝိုင်းကတိကဝတ်များ|အသိပေးချက်ခွင့်ပြုချက်များ။|အလုပ်အတွက်အကူအညီလိုသလား?",
    "cs": "Co je Go and Help?|Nabídněte odměnu|Pomáhejte a cestujte|Připojte se k události pro větší projekty nebo ji vytvořte|Jak můžete pomoci?|Závazky komunity|Oprávnění k oznámením.|Potřebujete pomoc s úkolem?",
    "da": "Hvad er Go and Help?|Tilbyd en belønning|Hjælp og rejs|Deltag i eller opret en begivenhed til større projekter|Hvordan kan du hjælpe?|Fællesskabets forpligtelser|Tilladelser til notifikationer.|Brug for hjælp til en opgave?",
    "fi": "Mikä Go and Help on?|Tarjoa palkkio|Auta ja matkusta|Liity suuremman projektin tapahtumaan tai luo sellainen|Miten voit auttaa?|Yhteisön sitoumukset|Ilmoitusten käyttöoikeudet.|Tarvitsetko apua tehtävään?",
    "el": "Τι είναι το Go and Help;|Προσφέρετε ανταμοιβή|Βοηθήστε και ταξιδέψτε|Συμμετέχετε ή δημιουργήστε εκδήλωση για μεγαλύτερα έργα|Πώς μπορείτε να βοηθήσετε;|Δεσμεύσεις κοινότητας|Άδειες ειδοποιήσεων.|Χρειάζεστε βοήθεια με μια εργασία;",
    "gu": "Go and Help શું છે?|પુરસ્કાર આપો|મદદ કરો અને પ્રવાસ કરો|મોટા પ્રોજેક્ટ માટે કાર્યક્રમમાં જોડાઓ અથવા બનાવો|તમે કેવી રીતે મદદ કરી શકો?|સમુદાયની પ્રતિબદ્ધતાઓ|સૂચનાઓની પરવાનગીઓ.|કામમાં મદદ જોઈએ છે?",
    "ha": "Mene ne Go and Help?|Bayar da lada|Taimaka kuma yi tafiya|Shiga ko shirya taro don manyan ayyuka|Ta yaya za ka taimaka?|Alƙawuran al’umma|Izinin sanarwa.|Kana buƙatar taimako da aiki?",
    "he": "מה זה Go and Help?|הציעו תגמול|עזרו וטיילו|הצטרפו לאירוע או צרו אירוע לפרויקטים גדולים|איך תוכלו לעזור?|התחייבויות הקהילה|הרשאות להתראות.|צריכים עזרה במשימה?",
    "hu": "Mi az a Go and Help?|Ajánlj fel jutalmat|Segíts és utazz|Csatlakozz egy eseményhez vagy hozz létre egyet nagyobb projektekhez|Hogyan tudsz segíteni?|Közösségi vállalások|Értesítési engedélyek.|Segítség kell egy feladathoz?",
    "kn": "Go and Help ಎಂದರೇನು?|ಪ್ರತಿಫಲ ನೀಡಿ|ಸಹಾಯ ಮಾಡಿ ಮತ್ತು ಪ್ರಯಾಣಿಸಿ|ದೊಡ್ಡ ಯೋಜನೆಗಳಿಗಾಗಿ ಕಾರ್ಯಕ್ರಮ ಸೇರಿ ಅಥವಾ ರಚಿಸಿ|ನೀವು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?|ಸಮುದಾಯದ ಬದ್ಧತೆಗಳು|ಅಧಿಸೂಚನೆಗಳ ಅನುಮತಿಗಳು.|ಕೆಲಸಕ್ಕೆ ಸಹಾಯ ಬೇಕೇ?",
    "ml": "Go and Help എന്താണ്?|പ്രതിഫലം വാഗ്ദാനം ചെയ്യുക|സഹായിക്കുകയും യാത്ര ചെയ്യുകയും ചെയ്യുക|വലിയ പദ്ധതികൾക്കായി പരിപാടിയിൽ ചേരുക അല്ലെങ്കിൽ സൃഷ്ടിക്കുക|നിങ്ങൾക്ക് എങ്ങനെ സഹായിക്കാം?|സമൂഹത്തിന്റെ പ്രതിബദ്ധതകൾ|അറിയിപ്പുകൾക്കുള്ള അനുമതികൾ.|ജോലിക്ക് സഹായം വേണോ?",
    "mr": "Go and Help म्हणजे काय?|बक्षीस द्या|मदत करा आणि प्रवास करा|मोठ्या प्रकल्पांसाठी कार्यक्रमात सामील व्हा किंवा तयार करा|तुम्ही कशी मदत करू शकता?|समुदायाची वचनबद्धता|सूचनांच्या परवानग्या.|कामात मदत हवी आहे?",
    "ne": "Go and Help के हो?|पुरस्कार दिनुहोस्|मद्दत गर्नुहोस् र यात्रा गर्नुहोस्|ठूला परियोजनाका लागि कार्यक्रममा सामेल हुनुहोस् वा बनाउनुहोस्|तपाईं कसरी मद्दत गर्न सक्नुहुन्छ?|समुदायका प्रतिबद्धताहरू|सूचनाको अनुमति।|काममा मद्दत चाहिन्छ?",
    "fa": "Go and Help چیست؟|پاداش پیشنهاد کنید|کمک کنید و سفر کنید|برای پروژه‌های بزرگ به رویداد بپیوندید یا آن را ایجاد کنید|چگونه می‌توانید کمک کنید؟|تعهدات جامعه|مجوزهای اعلان‌ها.|برای کاری کمک می‌خواهید؟",
    "ta": "Go and Help என்றால் என்ன?|வெகுமதி வழங்குங்கள்|உதவுங்கள், பயணம் செய்யுங்கள்|பெரிய திட்டங்களுக்கான நிகழ்வில் சேருங்கள் அல்லது உருவாக்குங்கள்|நீங்கள் எப்படி உதவலாம்?|சமூகத்தின் உறுதிமொழிகள்|அறிவிப்பு அனுமதிகள்.|வேலைக்கு உதவி வேண்டுமா?",
    "te": "Go and Help అంటే ఏమిటి?|బహుమతి అందించండి|సహాయం చేయండి, ప్రయాణించండి|పెద్ద ప్రాజెక్టుల కోసం కార్యక్రమంలో చేరండి లేదా సృష్టించండి|మీరు ఎలా సహాయపడగలరు?|సమాజ కట్టుబాట్లు|నోటిఫికేషన్ అనుమతులు.|పనికి సహాయం కావాలా?",
}
LANGUAGE_CHOICE_CATALOGS: dict[str, dict[str, str]] = {
    code: dict(zip(LANGUAGE_CHOICE_KEYS, row.split("|"), strict=True))
    for code, row in LANGUAGE_CHOICE_ROWS.items()
}
