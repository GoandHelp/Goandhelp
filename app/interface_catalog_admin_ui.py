from collections import Counter
import string

from app.models import LANGUAGE_OPTIONS

ADMIN_UI_KEYS: tuple[str, ...] = (
    "Rows appear here as neighbours sign up, post, chat and review.",
    "Profile, message and community reports",
    "Up to 60 reports, open and reviewing first. Use the admin note above for your next decision.",
    "Completed-job safety reports",
)

ADMIN_UI_ROWS: dict[str, str] = {
    "am": "ነዋሪዎች ሲመዘገቡ፣ ልጥፍ ሲያደርጉ፣ ሲወያዩና ሲገምግሙ ረድፎች እዚህ ይታያሉ።|የመገለጫ፣ የመልዕክት እና የማህበረሰብ ሪፖርቶች|እስከ 60 ሪፖርቶች፤ መጀመሪያ ክፍት ያሉትንና እየተገመገሙ ያሉትን ይመልከቱ። ለሚቀጥለው ውሳኔዎ ከላይ ያለውን የአስተዳዳሪ ማስታወሻ ይጠቀሙ።|የተጠናቀቁ ሥራዎች የደህንነት ሪፖርቶች",
    "ar": "ستظهر الصفوف هنا مع انضمام الجيران ونشرهم ومحادثتهم وكتابتهم للتقييمات.|بلاغات الملفات الشخصية والرسائل والمجتمع|حتى 60 بلاغًا؛ تُعرض المفتوحة وقيد المراجعة أولًا. استخدم ملاحظة المشرف أعلاه لاتخاذ قرارك التالي.|بلاغات السلامة المتعلقة بالمهام المكتملة",
    "bn": "প্রতিবেশীরা যোগ দিলে, পোস্ট করলে, চ্যাট করলে ও পর্যালোচনা করলে সারিগুলো এখানে দেখা যাবে।|প্রোফাইল, বার্তা ও সম্প্রদায়ের প্রতিবেদন|সর্বোচ্চ ৬০টি প্রতিবেদন; খোলা ও পর্যালোচনাধীনগুলো আগে দেখানো হয়। পরবর্তী সিদ্ধান্তের জন্য ওপরের প্রশাসকের নোট ব্যবহার করুন।|সম্পন্ন কাজের নিরাপত্তা প্রতিবেদন",
    "my": "အနီးအနားရှိသူများ စာရင်းသွင်းခြင်း၊ ပို့စ်တင်ခြင်း၊ စကားပြောခြင်းနှင့် သုံးသပ်ခြင်းတို့ ပြုလုပ်သည့်အခါ ဤနေရာတွင် အတန်းများပေါ်လာမည်။|ပရိုဖိုင်၊ မက်ဆေ့ချ်နှင့် အသိုင်းအဝိုင်း တိုင်ကြားချက်များ|တိုင်ကြားချက် ၆၀ ခုအထိ၊ ဖွင့်ထားသောနှင့် စစ်ဆေးနေသောအရာများကို ဦးစွာပြသမည်။ နောက်ဆုံးဖြတ်ချက်အတွက် အပေါ်ရှိ စီမံခန့်ခွဲသူမှတ်ချက်ကို အသုံးပြုပါ။|ပြီးဆုံးသောအလုပ်များ၏ ဘေးကင်းရေးတိုင်ကြားချက်များ",
    "zh": "邻居注册、发布内容、聊天和评价后，相关记录会显示在这里。|个人资料、消息和社区举报|最多显示 60 条举报，未处理和审核中的举报优先。请使用上方的管理员备注作出下一项决定。|已完成任务的安全举报",
    "cs": "Řádky se zde zobrazí, až se sousedé zaregistrují, zveřejní příspěvek, budou chatovat a hodnotit.|Hlášení profilů, zpráv a komunity|Nejvýše 60 hlášení; otevřená a právě kontrolovaná se zobrazí jako první. Při dalším rozhodnutí použijte poznámku správce výše.|Bezpečnostní hlášení k dokončeným úkolům",
    "da": "Rækker vises her, når naboer tilmelder sig, opretter opslag, chatter og anmelder.|Rapporter om profiler, beskeder og fællesskabet|Op til 60 rapporter; åbne og under gennemgang vises først. Brug administratorens note ovenfor til din næste beslutning.|Sikkerhedsrapporter om afsluttede opgaver",
    "nl": "Hier verschijnen regels wanneer buurtgenoten zich aanmelden, berichten plaatsen, chatten en beoordelingen schrijven.|Meldingen over profielen, berichten en de community|Maximaal 60 meldingen; openstaande en beoordeelde meldingen staan vooraan. Gebruik de beheerdersnotitie hierboven voor je volgende beslissing.|Veiligheidsmeldingen over afgeronde taken",
    "fi": "Rivit näkyvät tässä, kun naapurit rekisteröityvät, julkaisevat, keskustelevat ja arvioivat.|Profiili-, viesti- ja yhteisöilmoitukset|Enintään 60 ilmoitusta; avoimet ja käsittelyssä olevat näytetään ensin. Käytä yllä olevaa ylläpitäjän muistiinpanoa seuraavan päätöksen tekemiseen.|Valmiiden tehtävien turvallisuusilmoitukset",
    "fr": "Les lignes apparaîtront ici lorsque des voisins s’inscriront, publieront, discuteront et laisseront un avis.|Signalements de profils, de messages et de la communauté|Jusqu’à 60 signalements ; les signalements ouverts et en cours d’examen apparaissent d’abord. Utilisez la note d’administration ci-dessus pour prendre votre prochaine décision.|Signalements de sécurité concernant les tâches terminées",
    "de": "Hier erscheinen Einträge, wenn Nachbarn sich anmelden, Beiträge veröffentlichen, chatten und Bewertungen abgeben.|Meldungen zu Profilen, Nachrichten und der Community|Bis zu 60 Meldungen; offene und in Prüfung befindliche zuerst. Nutze den Admin-Hinweis oben für deine nächste Entscheidung.|Sicherheitsmeldungen zu abgeschlossenen Aufgaben",
    "el": "Οι εγγραφές θα εμφανίζονται εδώ όταν οι γείτονες εγγράφονται, δημοσιεύουν, συνομιλούν και αξιολογούν.|Αναφορές προφίλ, μηνυμάτων και κοινότητας|Έως 60 αναφορές· πρώτα εμφανίζονται οι ανοιχτές και οι υπό εξέταση. Χρησιμοποιήστε τη σημείωση διαχειριστή παραπάνω για την επόμενη απόφασή σας.|Αναφορές ασφάλειας για ολοκληρωμένες εργασίες",
    "gu": "પાડોશીઓ નોંધણી કરે, પોસ્ટ કરે, ચેટ કરે અને સમીક્ષા આપે ત્યારે અહીં પંક્તિઓ દેખાશે.|પ્રોફાઇલ, સંદેશ અને સમુદાયના અહેવાલો|વધુમાં વધુ 60 અહેવાલો; ખુલ્લા અને સમીક્ષાધીન અહેવાલો પહેલાં દેખાશે. આગળના નિર્ણય માટે ઉપરની સંચાલક નોંધનો ઉપયોગ કરો.|પૂર્ણ થયેલા કામ અંગે સલામતી અહેવાલો",
    "he": "רשומות יופיעו כאן כשאנשים מהסביבה יירשמו, יפרסמו, ישוחחו ויכתבו ביקורות.|דיווחים על פרופילים, הודעות והקהילה|עד 60 דיווחים; הפתוחים והנבדקים מוצגים תחילה. השתמשו בהערת המנהל שלמעלה כדי לקבל את ההחלטה הבאה.|דיווחי בטיחות על משימות שהושלמו",
    "hi": "पड़ोसी साइन अप, पोस्ट, चैट और समीक्षा करेंगे तो पंक्तियाँ यहाँ दिखाई देंगी।|प्रोफ़ाइल, संदेश और समुदाय की रिपोर्टें|अधिकतम 60 रिपोर्टें; खुली और समीक्षााधीन रिपोर्टें पहले दिखाई जाती हैं। अगले निर्णय के लिए ऊपर दिए व्यवस्थापक नोट का उपयोग करें।|पूरे किए गए कामों की सुरक्षा रिपोर्टें",
    "hu": "Itt jelennek meg a sorok, amikor a szomszédok regisztrálnak, közzétesznek, csevegnek és értékelnek.|Profil-, üzenet- és közösségi jelentések|Legfeljebb 60 jelentés; a nyitott és felülvizsgálat alatt álló jelentések jelennek meg először. A következő döntéshez használd a fenti adminisztrátori megjegyzést.|Befejezett feladatok biztonsági jelentései",
    "id": "Baris akan muncul di sini saat warga sekitar mendaftar, membuat postingan, mengobrol, dan memberi ulasan.|Laporan profil, pesan, dan komunitas|Hingga 60 laporan; laporan terbuka dan sedang ditinjau ditampilkan lebih dahulu. Gunakan catatan admin di atas untuk keputusan berikutnya.|Laporan keselamatan untuk tugas yang selesai",
    "it": "Le righe appariranno qui quando le persone della comunità si registrano, pubblicano, chattano e recensiscono.|Segnalazioni di profili, messaggi e comunità|Fino a 60 segnalazioni; prima quelle aperte e in fase di revisione. Usa la nota dell’amministratore qui sopra per la prossima decisione.|Segnalazioni di sicurezza per attività completate",
    "ja": "近隣の人が登録、投稿、チャット、レビューを行うと、ここに一覧が表示されます。|プロフィール、メッセージ、コミュニティの報告|最大60件の報告を表示します。未対応と確認中の報告が先に表示されます。次の判断には上の管理者メモを使用してください。|完了した作業に関する安全報告",
    "kn": "ನೆರೆಹೊರೆಯವರು ಸೈನ್ ಅಪ್ ಮಾಡಿ, ಪೋಸ್ಟ್ ಮಾಡಿ, ಚಾಟ್ ಮಾಡಿ ಮತ್ತು ವಿಮರ್ಶೆ ನೀಡಿದಾಗ ಸಾಲುಗಳು ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ.|ಪ್ರೊಫೈಲ್, ಸಂದೇಶ ಮತ್ತು ಸಮುದಾಯ ವರದಿಗಳು|ಗರಿಷ್ಠ 60 ವರದಿಗಳು; ತೆರೆದಿರುವ ಮತ್ತು ಪರಿಶೀಲನೆಯಲ್ಲಿರುವವು ಮೊದಲು ಕಾಣಿಸುತ್ತವೆ. ಮುಂದಿನ ನಿರ್ಧಾರಕ್ಕೆ ಮೇಲಿನ ನಿರ್ವಾಹಕರ ಟಿಪ್ಪಣಿಯನ್ನು ಬಳಸಿ.|ಪೂರ್ಣಗೊಂಡ ಕೆಲಸಗಳ ಸುರಕ್ಷತಾ ವರದಿಗಳು",
    "ko": "이웃이 가입하고 게시물을 올리고 채팅하고 리뷰를 작성하면 여기에 항목이 표시됩니다.|프로필, 메시지 및 커뮤니티 신고|최대 60건의 신고를 표시하며 미처리 및 검토 중인 신고가 먼저 표시됩니다. 다음 결정을 위해 위의 관리자 메모를 사용하세요.|완료된 작업의 안전 신고",
    "ml": "അയൽക്കാർ സൈൻ അപ്പ് ചെയ്യുകയും പോസ്റ്റ് ചെയ്യുകയും ചാറ്റ് ചെയ്യുകയും അവലോകനം നൽകുകയും ചെയ്യുമ്പോൾ വരികൾ ഇവിടെ കാണിക്കും.|പ്രൊഫൈൽ, സന്ദേശം, സമൂഹം എന്നിവയെക്കുറിച്ചുള്ള റിപ്പോർട്ടുകൾ|പരമാവധി 60 റിപ്പോർട്ടുകൾ; തുറന്നതും അവലോകനത്തിലുള്ളതും ആദ്യം കാണിക്കും. അടുത്ത തീരുമാനത്തിന് മുകളിലെ അഡ്മിൻ കുറിപ്പ് ഉപയോഗിക്കുക.|പൂർത്തിയായ ജോലികളിലെ സുരക്ഷാ റിപ്പോർട്ടുകൾ",
    "mr": "शेजारी नोंदणी करतील, पोस्ट करतील, चॅट करतील आणि पुनरावलोकन देतील तेव्हा नोंदी येथे दिसतील.|प्रोफाइल, संदेश आणि समुदाय अहवाल|कमाल ६० अहवाल; खुले आणि पुनरावलोकनाधीन अहवाल आधी दाखवले जातील. पुढील निर्णयासाठी वरील प्रशासकाची नोंद वापरा.|पूर्ण झालेल्या कामांचे सुरक्षा अहवाल",
    "ne": "छिमेकीहरू दर्ता, पोस्ट, च्याट र समीक्षा गर्दा पङ्क्तिहरू यहाँ देखिनेछन्।|प्रोफाइल, सन्देश र समुदायका रिपोर्टहरू|६० वटासम्म रिपोर्ट; खुला र समीक्षामा रहेका रिपोर्ट पहिले देखाइन्छन्। अर्को निर्णयका लागि माथिको प्रशासक टिप्पणी प्रयोग गर्नुहोस्।|सम्पन्न कामका सुरक्षा रिपोर्टहरू",
    "fa": "با ثبت‌نام، انتشار مطلب، گفتگو و ثبت نظر همسایه‌ها، ردیف‌ها اینجا نمایش داده می‌شوند.|گزارش‌های نمایه، پیام و جامعه|حداکثر ۶۰ گزارش؛ گزارش‌های باز و در حال بررسی ابتدا نمایش داده می‌شوند. برای تصمیم بعدی از یادداشت مدیر در بالا استفاده کنید.|گزارش‌های ایمنی کارهای تکمیل‌شده",
    "pl": "Wiersze pojawią się tutaj, gdy sąsiedzi dołączą, opublikują wpis, porozmawiają i wystawią opinię.|Zgłoszenia profili, wiadomości i społeczności|Maksymalnie 60 zgłoszeń; najpierw otwarte i sprawdzane. Użyj notatki administratora powyżej przy podejmowaniu kolejnej decyzji.|Zgłoszenia bezpieczeństwa dotyczące ukończonych zadań",
    "pt": "As linhas aparecerão aqui quando os vizinhos se inscreverem, publicarem, conversarem e avaliarem.|Denúncias de perfis, mensagens e comunidade|Até 60 denúncias; as abertas e em análise aparecem primeiro. Use a nota administrativa acima para tomar a próxima decisão.|Denúncias de segurança sobre tarefas concluídas",
    "ro": "Rândurile vor apărea aici când vecinii se înscriu, publică, discută și oferă recenzii.|Raportări privind profiluri, mesaje și comunitate|Până la 60 de raportări; cele deschise și în curs de examinare apar primele. Folosește nota administratorului de mai sus pentru următoarea decizie.|Raportări de siguranță privind sarcinile finalizate",
    "es": "Las filas aparecerán aquí cuando los vecinos se registren, publiquen, conversen y escriban reseñas.|Denuncias de perfiles, mensajes y comunidad|Hasta 60 denuncias; primero se muestran las abiertas y en revisión. Usa la nota de administración de arriba para tomar la siguiente decisión.|Denuncias de seguridad de tareas completadas",
    "sw": "Mistari itaonekana hapa majirani wanapojiandikisha, kuchapisha, kupiga gumzo na kutoa maoni.|Ripoti za wasifu, ujumbe na jumuiya|Hadi ripoti 60; zilizo wazi na zinazokaguliwa huonyeshwa kwanza. Tumia dokezo la msimamizi hapo juu kufanya uamuzi unaofuata.|Ripoti za usalama za kazi zilizokamilika",
    "sv": "Rader visas här när grannar registrerar sig, publicerar, chattar och skriver omdömen.|Rapporter om profiler, meddelanden och gemenskapen|Upp till 60 rapporter; öppna rapporter och rapporter under granskning visas först. Använd administratörsanteckningen ovan för nästa beslut.|Säkerhetsrapporter om slutförda uppgifter",
    "ta": "அக்கம்பக்கத்தினர் பதிவு செய்து, இடுகையிட்டு, அரட்டை செய்து, மதிப்பாய்வு வழங்கும்போது வரிசைகள் இங்கே தோன்றும்.|சுயவிவரம், செய்தி மற்றும் சமூக அறிக்கைகள்|அதிகபட்சம் 60 அறிக்கைகள்; திறந்த மற்றும் மதிப்பாய்வில் உள்ளவை முதலில் காட்டப்படும். அடுத்த முடிவுக்கு மேலே உள்ள நிர்வாகக் குறிப்பைப் பயன்படுத்தவும்.|முடிக்கப்பட்ட பணிகளுக்கான பாதுகாப்பு அறிக்கைகள்",
    "te": "పొరుగువారు సైన్ అప్ చేసి, పోస్ట్ చేసి, చాట్ చేసి, సమీక్షించినప్పుడు వరుసలు ఇక్కడ కనిపిస్తాయి.|ప్రొఫైల్, సందేశం మరియు సమాజ నివేదికలు|గరిష్ఠంగా 60 నివేదికలు; తెరిచి ఉన్నవి, సమీక్షలో ఉన్నవి ముందుగా కనిపిస్తాయి. తదుపరి నిర్ణయం కోసం పైనున్న నిర్వాహక గమనికను ఉపయోగించండి.|పూర్తయిన పనుల భద్రతా నివేదికలు",
    "th": "รายการจะแสดงที่นี่เมื่อเพื่อนบ้านสมัคร โพสต์ แชต และเขียนรีวิว|รายงานเกี่ยวกับโปรไฟล์ ข้อความ และชุมชน|สูงสุด 60 รายงาน โดยแสดงรายงานที่เปิดอยู่และอยู่ระหว่างตรวจสอบก่อน ใช้บันทึกของผู้ดูแลด้านบนเพื่อประกอบการตัดสินใจครั้งต่อไป|รายงานความปลอดภัยเกี่ยวกับงานที่เสร็จแล้ว",
    "tr": "Komşular kaydolup gönderi paylaştığında, sohbet ettiğinde ve değerlendirme yaptığında satırlar burada görünür.|Profil, mesaj ve topluluk raporları|En fazla 60 rapor; açık ve incelenen raporlar önce gösterilir. Sonraki kararınız için yukarıdaki yönetici notunu kullanın.|Tamamlanan işler hakkındaki güvenlik raporları",
    "vi": "Các mục sẽ xuất hiện tại đây khi hàng xóm đăng ký, đăng bài, trò chuyện và đánh giá.|Báo cáo về hồ sơ, tin nhắn và cộng đồng|Tối đa 60 báo cáo; báo cáo đang mở và đang xem xét được hiển thị trước. Hãy dùng ghi chú quản trị viên ở trên cho quyết định tiếp theo.|Báo cáo an toàn về công việc đã hoàn thành",
}

ADMIN_UI_LOCALES = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if set(ADMIN_UI_ROWS) != ADMIN_UI_LOCALES:
    raise ValueError("Admin UI catalog locale coverage is incomplete")
if any(
    len(row.split("|")) != len(ADMIN_UI_KEYS) for row in ADMIN_UI_ROWS.values()
):
    raise ValueError("Admin UI catalog row length is invalid")
ADMIN_UI_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(ADMIN_UI_KEYS, row.split("|"), strict=True))
    for locale, row in ADMIN_UI_ROWS.items()
}
_formatter = string.Formatter()
for _locale, _entries in ADMIN_UI_CATALOGS.items():
    for _source, _value in _entries.items():
        _source_slots = Counter(
            name for _, name, _, _ in _formatter.parse(_source) if name
        )
        _value_slots = Counter(
            name for _, name, _, _ in _formatter.parse(_value) if name
        )
        if not _value.strip() or _source_slots != _value_slots:
            raise ValueError(
                f"Admin UI catalog validation failed for {_locale}: {_source}"
            )
