import reflex as rx

from collections import Counter
from string import Formatter

from app.models import LANGUAGE_OPTIONS

INBOX_DIRECT_KEYS: tuple[str, ...] = (
    "they can reply without becoming a contact",
    "Hello! I'm passing through your city next week — could you point me to a good bike repair spot?",
    "Send message",
    "Close message",
    "Message",
    "Message {name}",
    "Replies are welcome either way",
    "No messages in this conversation yet.",
    "Reply — you don't need to be contacts",
    "Not a contact · Replies are welcome either way",
    "No messages yet",
)

INBOX_DIRECT_ROWS: dict[str, str] = {
    "am": "እውቂያ ሳይሆኑም መልስ ሊሰጡ ይችላሉ|ሰላም! በሚቀጥለው ሳምንት ከከተማዎ እያለፍኩ ነው — ጥሩ የብስክሌት ጥገና ቦታ ሊጠቁሙኝ ይችላሉ?|መልዕክት ላክ|መልዕክት ዝጋ|መልዕክት|መልዕክት {name}|በሁለቱም መንገድ ምላሽ ይቀበላል|በዚህ ውይይት ውስጥ ገና መልዕክት የለም።|መልስ — እውቂያ መሆን አያስፈልግም|እውቂያ አይደለም · ምላሽ በሁለቱም መንገድ ይቀበላል|ገና መልዕክት የለም",
    "ar": "يمكنهم الرد دون أن يصبحوا جهة اتصال|مرحبًا! سأمر بمدينتك الأسبوع المقبل — هل يمكنك أن ترشدني إلى مكان جيد لإصلاح الدراجات؟|إرسال رسالة|إغلاق الرسالة|رسالة|رسالة إلى {name}|الردود مرحب بها في كل الأحوال|لا توجد رسائل في هذه المحادثة بعد.|الرد — لا يلزم أن تكونا جهة اتصال|ليس جهة اتصال · الردود مرحب بها في كل الأحوال|لا توجد رسائل بعد",
    "bn": "পরিচিতি না হয়েও তারা উত্তর দিতে পারবেন|হ্যালো! আগামী সপ্তাহে আপনার শহর দিয়ে যাচ্ছি — ভালো সাইকেল মেরামতের জায়গা কোথায় বলতে পারবেন?|বার্তা পাঠান|বার্তা বন্ধ করুন|বার্তা|{name}-কে বার্তা|যেকোনোভাবেই উত্তর স্বাগত|এই কথোপকথনে এখনও কোনো বার্তা নেই।|উত্তর দিন — পরিচিতি হওয়ার দরকার নেই|পরিচিতি নন · যেকোনোভাবেই উত্তর স্বাগত|এখনও কোনো বার্তা নেই",
    "my": "၎င်းတို့သည် အဆက်အသွယ်မဖြစ်ဘဲ ပြန်စာပို့နိုင်သည်|မင်္ဂလာပါ! နောက်အပတ်မှာ သင့်မြို့ကို ဖြတ်သွားမှာပါ — စက်ဘီးပြင်ဖို့နေရာကောင်းတစ်ခု ညွှန်ပြပေးနိုင်မလား?|မက်ဆေ့ချ်ပို့ရန်|မက်ဆေ့ချ်ပိတ်ရန်|မက်ဆေ့ချ်|{name} ထံ မက်ဆေ့ချ်|ဘယ်လိုပဲဖြစ်ဖြစ် ပြန်စာကို ကြိုဆိုပါတယ်|ဤစကားဝိုင်းတွင် မက်ဆေ့ချ် မရှိသေးပါ။|ပြန်စာပို့ပါ — အဆက်အသွယ်ဖြစ်ရန် မလိုပါ|အဆက်အသွယ် မဟုတ်ပါ · ဘယ်လိုပဲဖြစ်ဖြစ် ပြန်စာကြိုဆိုပါတယ်|မက်ဆေ့ချ် မရှိသေးပါ",
    "zh": "对方无需成为联系人也可以回复|你好！我下周会经过你的城市 — 可以告诉我哪里有不错的自行车维修店吗？|发送消息|关闭消息|消息|给{name}发消息|无论如何都欢迎回复|此对话中还没有消息。|回复 — 你们不必成为联系人|不是联系人 · 无论如何都欢迎回复|暂无消息",
    "cs": "Mohou odpovědět, aniž by se stali kontaktem|Ahoj! Příští týden projíždím vaším městem — doporučíte mi dobrý servis na kola?|Odeslat zprávu|Zavřít zprávu|Zpráva|Zpráva pro {name}|Odpovědi jsou vítány tak jako tak|V této konverzaci zatím nejsou žádné zprávy.|Odpovědět — nemusíte být kontakty|Není kontaktem · Odpovědi jsou vítány tak jako tak|Zatím žádné zprávy",
    "da": "De kan svare uden at blive en kontakt|Hej! Jeg kommer gennem din by i næste uge — kan du anbefale et godt cykelværksted?|Send besked|Luk besked|Besked|Besked til {name}|Svar er velkomne uanset hvad|Der er endnu ingen beskeder i denne samtale.|Svar — I behøver ikke være kontakter|Ikke en kontakt · Svar er velkomne uanset hvad|Ingen beskeder endnu",
    "nl": "Ze kunnen antwoorden zonder contact te worden|Hallo! Volgende week kom ik door je stad — kun je een goede fietsenmaker aanbevelen?|Bericht versturen|Bericht sluiten|Bericht|Bericht aan {name}|Iedereen mag reageren|Er staan nog geen berichten in dit gesprek.|Reageren — jullie hoeven geen contacten te zijn|Geen contact · Iedereen mag reageren|Nog geen berichten",
    "fi": "He voivat vastata ryhtymättä yhteyshenkilöksi|Hei! Kuljen kaupunkisi kautta ensi viikolla — osaisitko suositella hyvää pyöräkorjaamoa?|Lähetä viesti|Sulje viesti|Viesti|Viesti henkilölle {name}|Vastaukset ovat tervetulleita joka tapauksessa|Tässä keskustelussa ei ole vielä viestejä.|Vastaa — teidän ei tarvitse olla yhteyshenkilöitä|Ei yhteyshenkilö · Vastaukset ovat tervetulleita joka tapauksessa|Ei vielä viestejä",
    "fr": "Ils peuvent répondre sans devenir un contact|Bonjour ! Je passerai dans votre ville la semaine prochaine — pourriez-vous m’indiquer un bon atelier de réparation de vélos ?|Envoyer un message|Fermer le message|Message|Message à {name}|Les réponses sont les bienvenues dans tous les cas|Aucun message dans cette conversation pour le moment.|Répondre — vous n’avez pas besoin d’être contacts|Pas un contact · Les réponses sont les bienvenues dans tous les cas|Aucun message pour le moment",
    "de": "Sie können antworten, ohne Kontakt zu werden|Hallo! Ich komme nächste Woche durch deine Stadt — kannst du mir eine gute Fahrradwerkstatt empfehlen?|Nachricht senden|Nachricht schließen|Nachricht|Nachricht an {name}|Antworten sind in jedem Fall willkommen|In dieser Unterhaltung gibt es noch keine Nachrichten.|Antworten — ihr müsst keine Kontakte sein|Kein Kontakt · Antworten sind in jedem Fall willkommen|Noch keine Nachrichten",
    "el": "Μπορούν να απαντήσουν χωρίς να γίνουν επαφή|Γεια! Θα περάσω από την πόλη σου την επόμενη εβδομάδα — μπορείς να μου προτείνεις ένα καλό συνεργείο ποδηλάτων;|Αποστολή μηνύματος|Κλείσιμο μηνύματος|Μήνυμα|Μήνυμα προς {name}|Οι απαντήσεις είναι ευπρόσδεκτες σε κάθε περίπτωση|Δεν υπάρχουν ακόμη μηνύματα σε αυτή τη συνομιλία.|Απάντησε — δεν χρειάζεται να είστε επαφές|Δεν είναι επαφή · οι απαντήσεις είναι πάντα ευπρόσδεκτες|Δεν υπάρχουν ακόμη μηνύματα",
    "gu": "સંપર્ક બન્યા વિના તેઓ જવાબ આપી શકે છે|નમસ્તે! આવતા અઠવાડિયે તમારા શહેરમાંથી પસાર થઈશ — સારી સાયકલ રિપેરની દુકાન ક્યાં છે તે કહેશો?|સંદેશ મોકલો|સંદેશ બંધ કરો|સંદેશ|{name}ને સંદેશ|કોઈપણ રીતે જવાબ આવકાર્ય છે|આ વાતચીતમાં હજી કોઈ સંદેશ નથી.|જવાબ આપો — તમારે સંપર્ક હોવાની જરૂર નથી|સંપર્ક નથી · કોઈપણ રીતે જવાબ આવકાર્ય છે|હજી સંદેશા નથી",
    "he": "אפשר להשיב בלי להפוך לאיש קשר|שלום! אעבור בעיר שלך בשבוע הבא — אפשר להמליץ לי על מקום טוב לתיקון אופניים?|שליחת הודעה|סגירת הודעה|הודעה|הודעה אל {name}|תגובות מתקבלות בברכה בכל מקרה|עדיין אין הודעות בשיחה הזו.|להשיב — אין צורך להיות אנשי קשר|לא איש קשר · תגובות מתקבלות בברכה בכל מקרה|אין הודעות עדיין",
    "hi": "वे संपर्क बने बिना जवाब दे सकते हैं|नमस्ते! अगले सप्ताह आपके शहर से गुजर रहा हूँ — क्या आप साइकिल मरम्मत की अच्छी जगह बता सकते हैं?|संदेश भेजें|संदेश बंद करें|संदेश|{name} को संदेश|हर हाल में जवाब का स्वागत है|इस बातचीत में अभी कोई संदेश नहीं है।|जवाब दें — आप दोनों का संपर्क होना ज़रूरी नहीं|संपर्क नहीं · हर हाल में जवाब का स्वागत है|अभी कोई संदेश नहीं",
    "hu": "Kapcsolattá válás nélkül is válaszolhatnak|Szia! Jövő héten áthaladok a városodon — tudsz ajánlani egy jó kerékpárszervizt?|Üzenet küldése|Üzenet bezárása|Üzenet|Üzenet {name} részére|Bármilyen válasz szívesen fogadott|Ebben a beszélgetésben még nincsenek üzenetek.|Válasz — nem kell kapcsolatnak lennetek|Nem kapcsolat · Bármilyen válasz szívesen fogadott|Még nincs üzenet",
    "id": "Mereka dapat membalas tanpa menjadi kontak|Halo! Minggu depan saya melewati kotamu — bisakah kamu merekomendasikan tempat servis sepeda yang bagus?|Kirim pesan|Tutup pesan|Pesan|Pesan untuk {name}|Balasan selalu diterima|Belum ada pesan dalam percakapan ini.|Balas — kalian tidak harus menjadi kontak|Bukan kontak · Balasan selalu diterima|Belum ada pesan",
    "it": "Possono rispondere senza diventare un contatto|Ciao! La prossima settimana passerò dalla tua città — puoi consigliarmi una buona officina per biciclette?|Invia messaggio|Chiudi messaggio|Messaggio|Messaggio per {name}|Le risposte sono benvenute in ogni caso|Non ci sono ancora messaggi in questa conversazione.|Rispondi — non è necessario essere contatti|Non è un contatto · Le risposte sono benvenute in ogni caso|Ancora nessun messaggio",
    "ja": "連絡先にならなくても返信できます|こんにちは！来週あなたの街を通る予定です — おすすめの自転車修理店を教えてもらえますか？|メッセージを送信|メッセージを閉じる|メッセージ|{name}にメッセージ|どちらの場合も返信を歓迎します|この会話にはまだメッセージがありません。|返信する — 連絡先になる必要はありません|連絡先ではありません · どちらの場合も返信を歓迎します|まだメッセージはありません",
    "kn": "ಸಂಪರ್ಕವಾಗದೆಯೂ ಅವರು ಉತ್ತರಿಸಬಹುದು|ನಮಸ್ಕಾರ! ಮುಂದಿನ ವಾರ ನಿಮ್ಮ ನಗರದ ಮೂಲಕ ಹೋಗುತ್ತೇನೆ — ಒಳ್ಳೆಯ ಸೈಕಲ್ ದುರಸ್ತಿ ಸ್ಥಳವನ್ನು ಸೂಚಿಸಬಹುದೇ?|ಸಂದೇಶ ಕಳುಹಿಸಿ|ಸಂದೇಶ ಮುಚ್ಚಿ|ಸಂದೇಶ|{name}ಗೆ ಸಂದೇಶ|ಯಾವುದೇ ರೀತಿಯ ಪ್ರತಿಕ್ರಿಯೆಗೂ ಸ್ವಾಗತ|ಈ ಸಂಭಾಷಣೆಯಲ್ಲಿ ಇನ್ನೂ ಸಂದೇಶಗಳಿಲ್ಲ.|ಉತ್ತರಿಸಿ — ನೀವು ಸಂಪರ್ಕಗಳಾಗಿರಬೇಕಿಲ್ಲ|ಸಂಪರ್ಕವಲ್ಲ · ಯಾವುದೇ ರೀತಿಯ ಪ್ರತಿಕ್ರಿಯೆಗೂ ಸ್ವಾಗತ|ಇನ್ನೂ ಸಂದೇಶಗಳಿಲ್ಲ",
    "ko": "연락처가 되지 않아도 답장을 보낼 수 있습니다|안녕하세요! 다음 주에 당신의 도시를 지나갈 예정인데 — 좋은 자전거 수리점을 알려 주실 수 있나요?|메시지 보내기|메시지 닫기|메시지|{name}에게 메시지|어떤 경우든 답장을 환영합니다|이 대화에는 아직 메시지가 없습니다.|답장 — 서로 연락처가 아니어도 됩니다|연락처가 아님 · 어떤 경우든 답장을 환영합니다|아직 메시지가 없습니다",
    "ml": "കോൺടാക്റ്റാകാതെ തന്നെ അവർക്ക് മറുപടി നൽകാം|ഹലോ! അടുത്ത ആഴ്ച നിങ്ങളുടെ നഗരത്തിലൂടെ പോകും — നല്ലൊരു സൈക്കിൾ റിപ്പയർ സ്ഥലം പറഞ്ഞുതരാമോ?|സന്ദേശം അയയ്ക്കുക|സന്ദേശം അടയ്ക്കുക|സന്ദേശം|{name}ന് സന്ദേശം|എന്തായാലും മറുപടികൾ സ്വാഗതം|ഈ സംഭാഷണത്തിൽ ഇതുവരെ സന്ദേശങ്ങളില്ല.|മറുപടി നൽകുക — നിങ്ങൾ കോൺടാക്റ്റുകളാകേണ്ടതില്ല|കോൺടാക്റ്റല്ല · എന്തായാലും മറുപടികൾ സ്വാഗതം|ഇതുവരെ സന്ദേശങ്ങളില്ല",
    "mr": "संपर्क न बनताही ते उत्तर देऊ शकतात|नमस्कार! पुढच्या आठवड्यात तुमच्या शहरातून जाणार आहे — सायकल दुरुस्तीचे चांगले ठिकाण सांगाल का?|संदेश पाठवा|संदेश बंद करा|संदेश|{name}ला संदेश|कोणत्याही परिस्थितीत उत्तरांचे स्वागत आहे|या संभाषणात अजून संदेश नाहीत.|उत्तर द्या — तुम्ही संपर्क असण्याची गरज नाही|संपर्क नाही · कोणत्याही परिस्थितीत उत्तरांचे स्वागत आहे|अजून संदेश नाहीत",
    "ne": "सम्पर्क नबनीकन पनि उनीहरूले जवाफ दिन सक्छन्|नमस्कार! अर्को हप्ता तपाईंको सहर हुँदै जानेछु — राम्रो साइकल मर्मत गर्ने ठाउँ बताइदिनुहुन्छ?|सन्देश पठाउनुहोस्|सन्देश बन्द गर्नुहोस्|सन्देश|{name} लाई सन्देश|जवाफ सधैँ स्वागतयोग्य छन्|यस कुराकानीमा अहिलेसम्म कुनै सन्देश छैन।|जवाफ दिनुहोस् — तपाईंहरू सम्पर्क हुनुपर्दैन|सम्पर्क होइन · जवाफ सधैँ स्वागतयोग्य छन्|अहिलेसम्म सन्देश छैन",
    "fa": "آن‌ها می‌توانند بدون تبدیل‌شدن به مخاطب پاسخ دهند|سلام! هفته آینده از شهر شما عبور می‌کنم — می‌توانید یک تعمیرگاه خوب دوچرخه معرفی کنید؟|ارسال پیام|بستن پیام|پیام|پیام به {name}|در هر صورت از پاسخ استقبال می‌شود|هنوز پیامی در این گفتگو نیست.|پاسخ دهید — لازم نیست مخاطب یکدیگر باشید|مخاطب نیست · در هر صورت از پاسخ استقبال می‌شود|هنوز پیامی نیست",
    "pl": "Mogą odpisać, nie zostając kontaktem|Cześć! W przyszłym tygodniu będę przejeżdżać przez Twoje miasto — polecisz dobry serwis rowerowy?|Wyślij wiadomość|Zamknij wiadomość|Wiadomość|Wiadomość do {name}|Odpowiedzi są mile widziane w każdej sytuacji|W tej rozmowie nie ma jeszcze wiadomości.|Odpowiedz — nie musicie być kontaktami|Nie jest kontaktem · Odpowiedzi są mile widziane w każdej sytuacji|Brak wiadomości",
    "pt": "Podem responder sem se tornarem contactos|Olá! Vou passar pela sua cidade na próxima semana — pode indicar-me uma boa oficina de bicicletas?|Enviar mensagem|Fechar mensagem|Mensagem|Mensagem para {name}|As respostas são sempre bem-vindas|Ainda não há mensagens nesta conversa.|Responder — não precisam de ser contactos|Não é um contacto · As respostas são sempre bem-vindas|Ainda não há mensagens",
    "ro": "Pot răspunde fără să devină un contact|Salut! Săptămâna viitoare trec prin orașul tău — îmi poți recomanda un atelier bun de reparații biciclete?|Trimite mesaj|Închide mesajul|Mesaj|Mesaj către {name}|Răspunsurile sunt binevenite oricum|Nu există încă mesaje în această conversație.|Răspunde — nu trebuie să fiți contacte|Nu este contact · Răspunsurile sunt binevenite oricum|Nu există încă mesaje",
    "es": "Pueden responder sin convertirse en contacto|¡Hola! La semana que viene pasaré por tu ciudad — ¿podrías recomendarme un buen taller de bicicletas?|Enviar mensaje|Cerrar mensaje|Mensaje|Mensaje para {name}|Las respuestas son bienvenidas en cualquier caso|Todavía no hay mensajes en esta conversación.|Responder — no tenéis que ser contactos|No es un contacto · Las respuestas son bienvenidas en cualquier caso|Todavía no hay mensajes",
    "sw": "Wanaweza kujibu bila kuwa mtu wa mawasiliano|Habari! Nitapitia mjini kwako wiki ijayo — unaweza kunielekeza kwenye sehemu nzuri ya kutengeneza baiskeli?|Tuma ujumbe|Funga ujumbe|Ujumbe|Ujumbe kwa {name}|Majibu yanakaribishwa kwa hali yoyote|Bado hakuna ujumbe katika mazungumzo haya.|Jibu — si lazima muwe watu wa mawasiliano|Si mtu wa mawasiliano · Majibu yanakaribishwa kwa hali yoyote|Bado hakuna ujumbe",
    "sv": "De kan svara utan att bli en kontakt|Hej! Nästa vecka passerar jag din stad — kan du tipsa om en bra cykelverkstad?|Skicka meddelande|Stäng meddelande|Meddelande|Meddelande till {name}|Svar är välkomna oavsett|Det finns inga meddelanden i den här konversationen ännu.|Svara — ni behöver inte vara kontakter|Inte en kontakt · Svar är välkomna oavsett|Inga meddelanden ännu",
    "ta": "தொடர்பாக மாறாமலேயே அவர்கள் பதிலளிக்கலாம்|வணக்கம்! அடுத்த வாரம் உங்கள் நகரம் வழியாகச் செல்கிறேன் — நல்ல மிதிவண்டி பழுதுபார்க்கும் இடத்தைச் சொல்ல முடியுமா?|செய்தி அனுப்பு|செய்தியை மூடு|செய்தி|{name}க்கு செய்தி|எப்படியிருந்தாலும் பதில்கள் வரவேற்கப்படுகின்றன|இந்த உரையாடலில் இன்னும் செய்திகள் இல்லை.|பதிலளி — நீங்கள் தொடர்புகளாக இருக்க வேண்டியதில்லை|தொடர்பு அல்ல · எப்படியிருந்தாலும் பதில்கள் வரவேற்கப்படுகின்றன|இன்னும் செய்திகள் இல்லை",
    "te": "పరిచయంగా మారకుండానే వారు సమాధానం ఇవ్వవచ్చు|హలో! వచ్చే వారం మీ నగరం గుండా వెళ్తాను — మంచి సైకిల్ మరమ్మత్తు స్థలాన్ని సూచించగలరా?|సందేశం పంపండి|సందేశాన్ని మూసివేయండి|సందేశం|{name}కు సందేశం|ఎలాగైనా సమాధానాలు స్వాగతం|ఈ సంభాషణలో ఇంకా సందేశాలు లేవు.|సమాధానం ఇవ్వండి — మీరు పరిచయాలు కావాల్సిన అవసరం లేదు|పరిచయం కాదు · ఎలాగైనా సమాధానాలు స్వాగతం|ఇంకా సందేశాలు లేవు",
    "th": "พวกเขาสามารถตอบกลับได้โดยไม่ต้องเป็นผู้ติดต่อ|สวัสดี! สัปดาห์หน้าฉันจะผ่านเมืองของคุณ — ช่วยแนะนำร้านซ่อมจักรยานดี ๆ ได้ไหม|ส่งข้อความ|ปิดข้อความ|ข้อความ|ข้อความถึง {name}|ยินดีรับคำตอบไม่ว่าจะเป็นอย่างไร|ยังไม่มีข้อความในการสนทนานี้|ตอบกลับ — คุณไม่จำเป็นต้องเป็นผู้ติดต่อกัน|ไม่ใช่ผู้ติดต่อ · ยินดีรับคำตอบไม่ว่าจะเป็นอย่างไร|ยังไม่มีข้อความ",
    "tr": "Kişi olmadan da yanıt verebilirler|Merhaba! Gelecek hafta şehrinizden geçeceğim — iyi bir bisiklet tamircisi önerebilir misiniz?|Mesaj gönder|Mesajı kapat|Mesaj|{name} kişisine mesaj|Her durumda yanıtlar memnuniyetle karşılanır|Bu konuşmada henüz mesaj yok.|Yanıtla — kişi olmanız gerekmiyor|Kişi değil · Her durumda yanıtlar memnuniyetle karşılanır|Henüz mesaj yok",
    "vi": "Họ có thể trả lời mà không cần trở thành liên hệ|Xin chào! Tuần tới tôi sẽ đi qua thành phố của bạn — bạn có thể chỉ cho tôi một tiệm sửa xe đạp tốt không?|Gửi tin nhắn|Đóng tin nhắn|Tin nhắn|Tin nhắn cho {name}|Mọi câu trả lời đều được chào đón|Chưa có tin nhắn nào trong cuộc trò chuyện này.|Trả lời — hai bạn không cần là liên hệ|Không phải liên hệ · Mọi câu trả lời đều được chào đón|Chưa có tin nhắn",
}

_expected_locales = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if set(INBOX_DIRECT_ROWS) != _expected_locales:
    raise ValueError(
        "Inbox direct-message catalog locale coverage is incomplete"
    )
INBOX_DIRECT_CATALOGS: dict[str, dict[str, str]] = {
    language: dict(zip(INBOX_DIRECT_KEYS, row.split("|"), strict=True))
    for language, row in INBOX_DIRECT_ROWS.items()
}
_formatter = Formatter()
for _language, _entries in INBOX_DIRECT_CATALOGS.items():
    for _source, _value in _entries.items():
        if not _value.strip() or (_value == _source and len(_source) > 24):
            raise ValueError(
                f"Missing inbox direct translation: {_language}: {_source}"
            )
        if Counter(
            slot for _, slot, _, _ in _formatter.parse(_source) if slot
        ) != Counter(
            slot for _, slot, _, _ in _formatter.parse(_value) if slot
        ):
            raise ValueError(
                f"Inbox direct slot mismatch: {_language}: {_source}"
            )
