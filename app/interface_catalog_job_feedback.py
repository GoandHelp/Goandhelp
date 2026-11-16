from app.models import LANGUAGE_OPTIONS

JOB_FEEDBACK_TOAST_KEYS: tuple[str, ...] = (
    "Request accepted. Job confirmed.",
    "Request declined.",
    "Task completed.",
    "Completion confirmed.",
    "Your review is now public.",
    "Report sent privately to our team.",
)

_JOB_FEEDBACK_TOAST_ROWS: dict[str, str] = {
    "am": "ጥያቄው ተቀብሏል። ሥራው ተረጋግጧል።¦ጥያቄው ውድቅ ተደርጓል።¦ሥራው ተጠናቋል።¦ማጠናቀቁ ተረጋግጧል።¦ግምገማዎ አሁን ይፋ ሆኗል።¦ሪፖርቱ በግል ወደ ቡድናችን ተልኳል።",
    "ar": "تم قبول الطلب وتأكيد المهمة.¦تم رفض الطلب.¦اكتملت المهمة.¦تم تأكيد الإكمال.¦أصبح تقييمك عامًا الآن.¦أُرسل البلاغ إلى فريقنا بسرية.",
    "bn": "অনুরোধ গৃহীত হয়েছে। কাজ নিশ্চিত হয়েছে।¦অনুরোধ প্রত্যাখ্যান করা হয়েছে।¦কাজ সম্পন্ন হয়েছে।¦সম্পন্ন হওয়া নিশ্চিত হয়েছে।¦আপনার পর্যালোচনা এখন প্রকাশ্য।¦প্রতিবেদনটি ব্যক্তিগতভাবে আমাদের দলে পাঠানো হয়েছে।",
    "my": "တောင်းဆိုချက်ကို လက်ခံပြီး အလုပ်ကို အတည်ပြုပြီးပါပြီ။¦တောင်းဆိုချက်ကို ငြင်းပယ်ပြီးပါပြီ။¦အလုပ်ပြီးဆုံးပါပြီ။¦ပြီးဆုံးကြောင်း အတည်ပြုပြီးပါပြီ။¦သင့်သုံးသပ်ချက်ကို ယခု အများမြင်နိုင်ပါပြီ။¦အစီရင်ခံစာကို ကျွန်ုပ်တို့အဖွဲ့ထံ သီးသန့်ပို့ပြီးပါပြီ။",
    "zh": "请求已接受，工作已确认。¦请求已拒绝。¦任务已完成。¦已确认完成。¦你的评价现已公开。¦报告已私下发送给我们的团队。",
    "cs": "Žádost přijata. Práce je potvrzena.¦Žádost byla odmítnuta.¦Úkol byl dokončen.¦Dokončení bylo potvrzeno.¦Vaše hodnocení je nyní veřejné.¦Hlášení bylo soukromě odesláno našemu týmu.",
    "da": "Anmodningen er accepteret. Jobbet er bekræftet.¦Anmodningen blev afvist.¦Opgaven er fuldført.¦Fuldførelsen er bekræftet.¦Din anmeldelse er nu offentlig.¦Rapporten er sendt privat til vores team.",
    "nl": "Verzoek geaccepteerd. De klus is bevestigd.¦Verzoek geweigerd.¦Taak voltooid.¦Voltooiing bevestigd.¦Je beoordeling is nu openbaar.¦Melding privé naar ons team verzonden.",
    "fi": "Pyyntö hyväksytty. Työ on vahvistettu.¦Pyyntö hylätty.¦Tehtävä suoritettu.¦Valmistuminen vahvistettu.¦Arvostelusi on nyt julkinen.¦Ilmoitus lähetettiin yksityisesti tiimillemme.",
    "fr": "Demande acceptée. Tâche confirmée.¦Demande refusée.¦Tâche terminée.¦Fin de tâche confirmée.¦Votre avis est maintenant public.¦Le signalement a été envoyé en privé à notre équipe.",
    "de": "Anfrage angenommen. Aufgabe bestätigt.¦Anfrage abgelehnt.¦Aufgabe abgeschlossen.¦Abschluss bestätigt.¦Deine Bewertung ist jetzt öffentlich.¦Der Bericht wurde privat an unser Team gesendet.",
    "el": "Το αίτημα έγινε δεκτό. Η εργασία επιβεβαιώθηκε.¦Το αίτημα απορρίφθηκε.¦Η εργασία ολοκληρώθηκε.¦Η ολοκλήρωση επιβεβαιώθηκε.¦Η αξιολόγησή σου είναι πλέον δημόσια.¦Η αναφορά στάλθηκε ιδιωτικά στην ομάδα μας.",
    "gu": "વિનંતી સ્વીકારાઈ. કામની પુષ્ટિ થઈ.¦વિનંતી નકારાઈ.¦કાર્ય પૂર્ણ થયું.¦પૂર્ણતાની પુષ્ટિ થઈ.¦તમારી સમીક્ષા હવે જાહેર છે.¦રિપોર્ટ ખાનગી રીતે અમારી ટીમને મોકલાયો.",
    "he": "הבקשה התקבלה. העבודה אושרה.¦הבקשה נדחתה.¦המשימה הושלמה.¦ההשלמה אושרה.¦הביקורת שלך כעת ציבורית.¦הדיווח נשלח באופן פרטי לצוות שלנו.",
    "hi": "अनुरोध स्वीकार हुआ। काम की पुष्टि हुई।¦अनुरोध अस्वीकार हुआ।¦काम पूरा हुआ।¦काम पूरा होने की पुष्टि हुई।¦आपकी समीक्षा अब सार्वजनिक है।¦रिपोर्ट हमारी टीम को निजी रूप से भेजी गई।",
    "hu": "A kérést elfogadtuk. A munka megerősítve.¦A kérést elutasítottuk.¦A feladat elkészült.¦A befejezést megerősítettük.¦Az értékelésed mostantól nyilvános.¦A jelentést bizalmasan elküldtük a csapatunknak.",
    "id": "Permintaan diterima. Pekerjaan dikonfirmasi.¦Permintaan ditolak.¦Tugas selesai.¦Penyelesaian dikonfirmasi.¦Ulasan Anda kini tersedia untuk umum.¦Laporan dikirim secara pribadi kepada tim kami.",
    "it": "Richiesta accettata. Lavoro confermato.¦Richiesta rifiutata.¦Attività completata.¦Completamento confermato.¦La tua recensione è ora pubblica.¦La segnalazione è stata inviata privatamente al nostro team.",
    "ja": "依頼を承認しました。仕事が確定しました。¦依頼を辞退しました。¦作業が完了しました。¦完了を確認しました。¦レビューが公開されました。¦報告をチームに非公開で送信しました。",
    "kn": "ವಿನಂತಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಕೆಲಸ ದೃಢೀಕರಿಸಲಾಗಿದೆ.¦ವಿನಂತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ.¦ಕೆಲಸ ಪೂರ್ಣಗೊಂಡಿದೆ.¦ಪೂರ್ಣಗೊಳಿಸುವಿಕೆ ದೃಢೀಕರಿಸಲಾಗಿದೆ.¦ನಿಮ್ಮ ವಿಮರ್ಶೆ ಈಗ ಸಾರ್ವಜನಿಕವಾಗಿದೆ.¦ವರದಿಯನ್ನು ನಮ್ಮ ತಂಡಕ್ಕೆ ಖಾಸಗಿಯಾಗಿ ಕಳುಹಿಸಲಾಗಿದೆ.",
    "ko": "요청을 수락했습니다. 작업이 확인되었습니다.¦요청을 거절했습니다.¦작업이 완료되었습니다.¦완료가 확인되었습니다.¦리뷰가 공개되었습니다.¦신고를 팀에 비공개로 보냈습니다.",
    "ml": "അഭ്യർത്ഥന അംഗീകരിച്ചു. ജോലി സ്ഥിരീകരിച്ചു.¦അഭ്യർത്ഥന നിരസിച്ചു.¦ജോലി പൂർത്തിയായി.¦പൂർത്തീകരണം സ്ഥിരീകരിച്ചു.¦നിങ്ങളുടെ അവലോകനം ഇപ്പോൾ പൊതുവായതാണ്.¦റിപ്പോർട്ട് ഞങ്ങളുടെ സംഘത്തിന് സ്വകാര്യമായി അയച്ചു.",
    "mr": "विनंती स्वीकारली. कामाची पुष्टी झाली.¦विनंती नाकारली.¦काम पूर्ण झाले.¦पूर्णत्वाची पुष्टी झाली.¦तुमची समीक्षा आता सार्वजनिक आहे.¦अहवाल आमच्या टीमला खाजगीपणे पाठवला.",
    "ne": "अनुरोध स्वीकारियो। काम पुष्टि भयो।¦अनुरोध अस्वीकार गरियो।¦काम सम्पन्न भयो।¦सम्पन्न भएको पुष्टि भयो।¦तपाईंको समीक्षा अब सार्वजनिक छ।¦रिपोर्ट हाम्रो टोलीलाई निजी रूपमा पठाइयो।",
    "fa": "درخواست پذیرفته شد. کار تأیید شد.¦درخواست رد شد.¦کار تکمیل شد.¦تکمیل کار تأیید شد.¦دیدگاه شما اکنون عمومی است.¦گزارش به‌صورت خصوصی برای تیم ما ارسال شد.",
    "pl": "Prośba zaakceptowana. Zadanie potwierdzone.¦Prośba odrzucona.¦Zadanie ukończone.¦Ukończenie potwierdzone.¦Twoja opinia jest teraz publiczna.¦Zgłoszenie wysłano prywatnie do naszego zespołu.",
    "pt": "Pedido aceite. Trabalho confirmado.¦Pedido recusado.¦Tarefa concluída.¦Conclusão confirmada.¦A sua avaliação está agora pública.¦A denúncia foi enviada em privado à nossa equipa.",
    "ro": "Cerere acceptată. Lucrarea este confirmată.¦Cerere refuzată.¦Sarcină finalizată.¦Finalizarea a fost confirmată.¦Recenzia ta este acum publică.¦Raportul a fost trimis în privat echipei noastre.",
    "es": "Solicitud aceptada. Trabajo confirmado.¦Solicitud rechazada.¦Tarea completada.¦Finalización confirmada.¦Tu reseña ya es pública.¦El informe se envió en privado a nuestro equipo.",
    "sw": "Ombi limekubaliwa. Kazi imethibitishwa.¦Ombi limekataliwa.¦Kazi imekamilika.¦Ukamilishaji umethibitishwa.¦Tathmini yako sasa iko wazi kwa umma.¦Ripoti imetumwa kwa timu yetu kwa faragha.",
    "sv": "Förfrågan accepterad. Jobbet är bekräftat.¦Förfrågan avböjd.¦Uppgiften är slutförd.¦Slutförandet är bekräftat.¦Din recension är nu offentlig.¦Rapporten har skickats privat till vårt team.",
    "ta": "கோரிக்கை ஏற்கப்பட்டது. பணி உறுதிப்படுத்தப்பட்டது.¦கோரிக்கை நிராகரிக்கப்பட்டது.¦பணி முடிந்தது.¦பணி முடிந்தது உறுதிப்படுத்தப்பட்டது.¦உங்கள் மதிப்பாய்வு இப்போது பொதுவானது.¦அறிக்கை எங்கள் குழுவிற்கு தனிப்பட்ட முறையில் அனுப்பப்பட்டது.",
    "te": "అభ్యర్థన ఆమోదించబడింది. పని నిర్ధారించబడింది.¦అభ్యర్థన తిరస్కరించబడింది.¦పని పూర్తయింది.¦పూర్తయినట్లు నిర్ధారించబడింది.¦మీ సమీక్ష ఇప్పుడు పబ్లిక్‌గా ఉంది.¦నివేదికను మా బృందానికి ప్రైవేట్‌గా పంపాం.",
    "th": "ยอมรับคำขอแล้ว ยืนยันงานแล้ว¦ปฏิเสธคำขอแล้ว¦งานเสร็จสมบูรณ์แล้ว¦ยืนยันการเสร็จสิ้นแล้ว¦รีวิวของคุณเผยแพร่แล้ว¦ส่งรายงานให้ทีมของเราเป็นการส่วนตัวแล้ว",
    "tr": "İstek kabul edildi. İş onaylandı.¦İstek reddedildi.¦Görev tamamlandı.¦Tamamlanma onaylandı.¦Değerlendirmen artık herkese açık.¦Bildirim ekibimize özel olarak gönderildi.",
    "vi": "Đã chấp nhận yêu cầu. Công việc đã được xác nhận.¦Đã từ chối yêu cầu.¦Công việc đã hoàn thành.¦Đã xác nhận hoàn thành.¦Đánh giá của bạn hiện đã công khai.¦Báo cáo đã được gửi riêng cho nhóm của chúng tôi.",
}

JOB_FEEDBACK_LITERAL_KEYS: tuple[str, ...] = (
    "Your session expired — please sign in again.",
    "That request is no longer open — it may have been withdrawn, already answered, or given to another helper.",
    "Request accepted. Job confirmed.",
    "Request declined — the conversation stays open.",
    "Request declined.",
    "We couldn't load your Inbox just now. Please use Refresh to try again.",
    "We couldn't load this conversation. Please try again.",
    "Open a conversation first.",
    "Write something before sending.",
    "Keep messages under 2000 characters.",
    "We couldn't send your message. Please try again.",
    "Only accepted jobs can be marked complete.",
    "This job is already fully confirmed.",
    "Choose how long the task actually took.",
    "Keep the story note under 2000 characters.",
    "Keep the reward under 255 characters.",
    "This job is no longer available to complete.",
    "Job completed by both sides — leave a review to close the loop.",
    "Your side is confirmed. Waiting for the other person.",
    "Task completed.",
    "Completion confirmed.",
    "Confirm your side of the job before writing a review.",
    "You've already reviewed this task.",
    "Give a 1–5 star score for all four categories before saving.",
    "Keep your review to 500 words or fewer.",
    "This review is not eligible for this completed task.",
    "We couldn't save your review. Please try again.",
    "Your review is now public. Thank you for sharing your experience.",
    "Your review is now public.",
    "Write a response of 1–500 words.",
    "A response has already been posted. Responses can only be written once.",
    "This review cannot be updated right now.",
    "We couldn't save your response. Please try again.",
    "Photos open once both sides confirm the job is finished.",
    "Choose at least one photo to add.",
    "Only the two people who did this job can add photos.",
    "We couldn't save those photos — please try again.",
    "No photo could be added. Check the format (JPG, PNG, WebP, maximum 3 MB, static images only, no video) and the five-photo limit.",
    "Photo removed from the story.",
    "Your device share sheet opened — finish the post in the app you picked.",
    "Sharing isn't available in this browser, so your caption and link were copied — paste them into the app.",
    "Share cancelled — nothing was posted.",
    "We couldn't open a share sheet or copy automatically. Select the caption above and copy it by hand.",
    "Reports open once the job is confirmed complete.",
    "You've already reported this job. Our team has it.",
    "Choose what happened so we route it correctly.",
    "Please describe what happened in a little more detail (20 characters or more).",
    "Keep the description under 2000 characters.",
    "We couldn't find that completed job.",
    "Only the two people on this job can report it.",
    "A report can only be about the other person on this job.",
    "Reports open once both sides confirm the job.",
    "You've already reported this job.",
    "Thank you — this report is private and now with our review team. Nothing is published and no one is accused publicly.",
    "Report sent privately to our team.",
)

JOB_FEEDBACK_TEMPLATE_KEYS: tuple[str, ...] = (
    "Accepted — you're helping with “{title}”.",
    "{added} photo(s) added. {skipped} were skipped — five photos per story, common image formats only.",
    "{added} photo(s) added to your story.",
    "Preparing your {network_label} share…",
)

_JOB_FEEDBACK_ROWS: dict[str, str] = {
    "am": "ተቀብለዋል — “{title}”ን እንዲረዱ እየረዱ ነው።¦{added} ፎቶ(ዎች) ታክለዋል። {skipped} ተዘልለዋል — በአንድ ታሪክ እስከ አምስት ፎቶዎች፣ የተለመዱ የምስል ቅርጸቶች ብቻ።¦{added} ፎቶ(ዎች) ወደ ታሪክዎ ታክለዋል።¦የ{network_label} ማጋራትዎን በማዘጋጀት ላይ…",
    "ar": "تم القبول — أنت تساعد في «{title}».¦أُضيفت {added} صورة. تم تخطي {skipped} — خمس صور لكل قصة، وبصيغ الصور الشائعة فقط.¦أُضيفت {added} صورة إلى قصتك.¦جارٍ إعداد المشاركة عبر {network_label}…",
    "bn": "গৃহীত — আপনি “{title}” কাজে সাহায্য করছেন।¦{added}টি ছবি যোগ হয়েছে। {skipped}টি বাদ গেছে — প্রতি গল্পে পাঁচটি ছবি, শুধু প্রচলিত ছবির ফরম্যাট।¦আপনার গল্পে {added}টি ছবি যোগ হয়েছে।¦আপনার {network_label} শেয়ার প্রস্তুত করা হচ্ছে…",
    "my": "လက်ခံပြီး — “{title}” တွင် ကူညီနေပါသည်။¦ဓာတ်ပုံ {added} ပုံ ထည့်ပြီးပါပြီ။ {skipped} ပုံကို ကျော်သွားသည် — ဇာတ်လမ်းတစ်ခုလျှင် ဓာတ်ပုံငါးပုံ၊ အသုံးများသောပုံဖော်မတ်များသာ။¦သင့်ဇာတ်လမ်းတွင် ဓာတ်ပုံ {added} ပုံ ထည့်ပြီးပါပြီ။¦သင့် {network_label} မျှဝေမှုကို ပြင်ဆင်နေသည်…",
    "zh": "已接受 — 你将帮助完成“{title}”。¦已添加 {added} 张照片。已跳过 {skipped} 张 — 每个故事最多五张照片，仅支持常见图片格式。¦已向你的故事添加 {added} 张照片。¦正在准备通过 {network_label} 分享…",
    "cs": "Přijato — pomůžete s úkolem „{title}“.¦Přidáno fotografií: {added}. Přeskočeno: {skipped} — nejvýše pět fotek na příběh, pouze běžné obrazové formáty.¦Do příběhu přidáno fotografií: {added}.¦Připravuje se sdílení přes {network_label}…",
    "da": "Accepteret — du hjælper med “{title}”.¦{added} foto(fotos) tilføjet. {skipped} blev sprunget over — fem fotos pr. historie, kun almindelige billedformater.¦{added} foto(fotos) tilføjet til din historie.¦Forbereder din {network_label}-deling…",
    "nl": "Geaccepteerd — je helpt met ‘{title}’.¦{added} foto('s) toegevoegd. {skipped} overgeslagen — vijf foto's per verhaal, alleen gangbare afbeeldingsformaten.¦{added} foto('s) aan je verhaal toegevoegd.¦Je {network_label}-deling voorbereiden…",
    "fi": "Hyväksytty — autat tehtävässä ”{title}”.¦Lisättiin {added} kuva(a). Ohitettiin {skipped} — enintään viisi kuvaa tarinaa kohti, vain yleiset kuvamuodot.¦Tarinaasi lisättiin {added} kuva(a).¦Valmistellaan {network_label}-jakoa…",
    "fr": "Demande acceptée — vous allez aider pour « {title} ».¦{added} photo(s) ajoutée(s). {skipped} ignorée(s) — cinq photos par récit, formats d’image courants uniquement.¦{added} photo(s) ajoutée(s) à votre récit.¦Préparation du partage sur {network_label}…",
    "de": "Angenommen — du hilfst bei „{title}“.¦{added} Foto(s) hinzugefügt. {skipped} übersprungen — fünf Fotos pro Geschichte, nur gängige Bildformate.¦{added} Foto(s) zu deiner Geschichte hinzugefügt.¦Dein {network_label}-Beitrag wird vorbereitet…",
    "el": "Έγινε δεκτό — βοηθάς στην εργασία «{title}».¦Προστέθηκαν {added} φωτογραφίες. Παραλείφθηκαν {skipped} — πέντε φωτογραφίες ανά ιστορία, μόνο συνήθεις μορφές εικόνας.¦Προστέθηκαν {added} φωτογραφίες στην ιστορία σου.¦Προετοιμασία κοινοποίησης στο {network_label}…",
    "gu": "સ્વીકાર્યું — તમે “{title}”માં મદદ કરી રહ્યા છો.¦{added} ફોટા ઉમેરાયા. {skipped} છોડી દેવાયા — પ્રતિ વાર્તા પાંચ ફોટા, ફક્ત સામાન્ય છબી ફોર્મેટ.¦તમારી વાર્તામાં {added} ફોટા ઉમેરાયા.¦તમારું {network_label} શેર તૈયાર થઈ રહ્યું છે…",
    "he": "התקבל — עוזרים במשימה „{title}”.¦נוספו {added} תמונות. {skipped} דולגו — חמש תמונות לכל סיפור, בפורמטים נפוצים בלבד.¦נוספו {added} תמונות לסיפור שלך.¦מכינים את השיתוף שלך ב־{network_label}…",
    "hi": "स्वीकृत — आप “{title}” में मदद कर रहे हैं।¦{added} फ़ोटो जोड़ी गईं। {skipped} छोड़ दी गईं — हर कहानी में पाँच फ़ोटो, केवल सामान्य छवि प्रारूप।¦आपकी कहानी में {added} फ़ोटो जोड़ी गईं।¦आपका {network_label} शेयर तैयार किया जा रहा है…",
    "hu": "Elfogadva — segítesz ebben: „{title}”.¦{added} fénykép hozzáadva. {skipped} kimaradt — történetenként öt fénykép, csak elterjedt képformátumok.¦{added} fénykép került a történetedbe.¦A {network_label}-megosztás előkészítése…",
    "id": "Diterima — Anda membantu untuk “{title}”.¦{added} foto ditambahkan. {skipped} dilewati — lima foto per cerita, hanya format gambar umum.¦{added} foto ditambahkan ke cerita Anda.¦Menyiapkan berbagi melalui {network_label}…",
    "it": "Accettata — aiuterai per “{title}”.¦Aggiunte {added} foto. {skipped} ignorate — cinque foto per storia, solo formati immagine comuni.¦Aggiunte {added} foto alla tua storia.¦Preparazione della condivisione su {network_label}…",
    "ja": "承認されました —「{title}」の手伝いをします。¦写真を{added}枚追加しました。{skipped}枚はスキップしました — 1つのストーリーにつき5枚まで、一般的な画像形式のみ。¦ストーリーに写真を{added}枚追加しました。¦{network_label}での共有を準備しています…",
    "kn": "ಸ್ವೀಕರಿಸಲಾಗಿದೆ — ನೀವು “{title}” ಕೆಲಸಕ್ಕೆ ಸಹಾಯ ಮಾಡುತ್ತಿದ್ದೀರಿ.¦{added} ಫೋಟೋಗಳನ್ನು ಸೇರಿಸಲಾಗಿದೆ. {skipped} ಬಿಟ್ಟುಬಿಡಲಾಗಿದೆ — ಪ್ರತಿ ಕಥೆಗೆ ಐದು ಫೋಟೋಗಳು, ಸಾಮಾನ್ಯ ಚಿತ್ರ ಸ್ವರೂಪಗಳು ಮಾತ್ರ.¦ನಿಮ್ಮ ಕಥೆಗೆ {added} ಫೋಟೋಗಳನ್ನು ಸೇರಿಸಲಾಗಿದೆ.¦ನಿಮ್ಮ {network_label} ಹಂಚಿಕೆಯನ್ನು ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ…",
    "ko": "수락됨 — “{title}” 작업을 돕게 됩니다.¦사진 {added}장 추가됨. {skipped}장 건너뜀 — 스토리당 사진 5장, 일반 이미지 형식만 지원합니다.¦스토리에 사진 {added}장이 추가되었습니다.¦{network_label} 공유를 준비하고 있습니다…",
    "ml": "അംഗീകരിച്ചു — “{title}” ജോലിയിൽ നിങ്ങൾ സഹായിക്കുന്നു.¦{added} ഫോട്ടോകൾ ചേർത്തു. {skipped} ഒഴിവാക്കി — ഓരോ കഥയ്ക്കും അഞ്ച് ഫോട്ടോകൾ, സാധാരണ ചിത്ര ഫോർമാറ്റുകൾ മാത്രം.¦നിങ്ങളുടെ കഥയിൽ {added} ഫോട്ടോകൾ ചേർത്തു.¦നിങ്ങളുടെ {network_label} പങ്കിടൽ തയ്യാറാക്കുന്നു…",
    "mr": "स्वीकारले — तुम्ही “{title}” कामात मदत करत आहात.¦{added} फोटो जोडले. {skipped} वगळले — प्रत्येक कथेसाठी पाच फोटो, फक्त सामान्य प्रतिमा स्वरूपे.¦तुमच्या कथेत {added} फोटो जोडले.¦तुमचे {network_label} शेअर तयार करत आहोत…",
    "ne": "स्वीकार गरियो — तपाईं “{title}” मा सहयोग गर्दै हुनुहुन्छ।¦{added} फोटो थपियो। {skipped} छोडियो — प्रत्येक कथामा पाँच फोटो, सामान्य छवि ढाँचाहरू मात्र।¦तपाईंको कथामा {added} फोटो थपियो।¦तपाईंको {network_label} साझेदारी तयार हुँदैछ…",
    "fa": "پذیرفته شد — در «{title}» کمک می‌کنید.¦{added} عکس اضافه شد. {skipped} مورد رد شد — پنج عکس برای هر داستان، فقط قالب‌های رایج تصویر.¦{added} عکس به داستان شما اضافه شد.¦در حال آماده‌سازی اشتراک‌گذاری در {network_label}…",
    "pl": "Zaakceptowano — pomożesz przy „{title}”.¦Dodano {added} zdjęć. Pominięto {skipped} — pięć zdjęć na historię, tylko popularne formaty obrazów.¦Dodano {added} zdjęć do twojej historii.¦Przygotowywanie udostępniania przez {network_label}…",
    "pt": "Aceite — vai ajudar em “{title}”.¦{added} foto(s) adicionada(s). {skipped} ignorada(s) — cinco fotos por história, apenas formatos de imagem comuns.¦{added} foto(s) adicionada(s) à sua história.¦A preparar a partilha em {network_label}…",
    "ro": "Acceptat — ajuți la „{title}”.¦S-au adăugat {added} fotografii. S-au omis {skipped} — cinci fotografii per poveste, doar formate obișnuite de imagine.¦S-au adăugat {added} fotografii în povestea ta.¦Se pregătește distribuirea prin {network_label}…",
    "es": "Aceptada — ayudarás con «{title}».¦Se añadieron {added} foto(s). Se omitieron {skipped} — cinco fotos por historia, solo formatos de imagen comunes.¦Se añadieron {added} foto(s) a tu historia.¦Preparando cómo compartir en {network_label}…",
    "sw": "Imekubaliwa — unasaidia kwenye “{title}”.¦Picha {added} zimeongezwa. {skipped} zimerukwa — picha tano kwa kila hadithi, miundo ya kawaida ya picha pekee.¦Picha {added} zimeongezwa kwenye hadithi yako.¦Tunatayarisha kushiriki kupitia {network_label}…",
    "sv": "Godkänt — du hjälper till med ”{title}”.¦{added} foto(n) har lagts till. {skipped} hoppades över — fem foton per berättelse, endast vanliga bildformat.¦{added} foto(n) har lagts till i din berättelse.¦Förbereder delning via {network_label}…",
    "ta": "ஏற்கப்பட்டது — “{title}” பணிக்கு நீங்கள் உதவுகிறீர்கள்.¦{added} புகைப்படங்கள் சேர்க்கப்பட்டன. {skipped} தவிர்க்கப்பட்டன — ஒவ்வொரு கதைக்கும் ஐந்து புகைப்படங்கள், பொதுவான பட வடிவங்கள் மட்டுமே.¦உங்கள் கதையில் {added} புகைப்படங்கள் சேர்க்கப்பட்டன.¦உங்கள் {network_label} பகிர்வைத் தயாரிக்கிறது…",
    "te": "ఆమోదించబడింది — మీరు “{title}” పనిలో సహాయం చేస్తున్నారు.¦{added} ఫోటోలు జోడించబడ్డాయి. {skipped} దాటవేయబడ్డాయి — ఒక్కో కథకు ఐదు ఫోటోలు, సాధారణ చిత్ర ఫార్మాట్‌లు మాత్రమే.¦మీ కథకు {added} ఫోటోలు జోడించబడ్డాయి.¦మీ {network_label} భాగస్వామ్యాన్ని సిద్ధం చేస్తోంది…",
    "th": "ยอมรับแล้ว — คุณกำลังช่วยงาน “{title}”¦เพิ่มรูป {added} รูป ข้ามไป {skipped} รูป — เรื่องละห้ารูป รองรับเฉพาะรูปแบบภาพทั่วไป¦เพิ่มรูป {added} รูปในเรื่องราวของคุณแล้ว¦กำลังเตรียมแชร์ผ่าน {network_label}…",
    "tr": "Kabul edildi — “{title}” işine yardım ediyorsun.¦{added} fotoğraf eklendi. {skipped} fotoğraf atlandı — hikâye başına beş fotoğraf, yalnızca yaygın görsel biçimleri.¦Hikâyene {added} fotoğraf eklendi.¦{network_label} paylaşımın hazırlanıyor…",
    "vi": "Đã chấp nhận — bạn sẽ giúp việc “{title}”.¦Đã thêm {added} ảnh. Đã bỏ qua {skipped} ảnh — tối đa năm ảnh mỗi câu chuyện, chỉ dùng định dạng ảnh phổ biến.¦Đã thêm {added} ảnh vào câu chuyện của bạn.¦Đang chuẩn bị chia sẻ qua {network_label}…",
}

_EXPECTED_FEEDBACK_LOCALES = {
    code for code, _label in LANGUAGE_OPTIONS if code != "en"
}
if set(_JOB_FEEDBACK_ROWS) != _EXPECTED_FEEDBACK_LOCALES:
    raise ValueError("Job feedback template locale coverage is incomplete")

JOB_FEEDBACK_TEMPLATE_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(JOB_FEEDBACK_TEMPLATE_KEYS, row.split("¦"), strict=True))
    for locale, row in _JOB_FEEDBACK_ROWS.items()
}

if set(_JOB_FEEDBACK_TOAST_ROWS) != _EXPECTED_FEEDBACK_LOCALES:
    raise ValueError("Job feedback toast locale coverage is incomplete")

JOB_FEEDBACK_TOAST_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(JOB_FEEDBACK_TOAST_KEYS, row.split("¦"), strict=True))
    for locale, row in _JOB_FEEDBACK_TOAST_ROWS.items()
}

JOB_FEEDBACK_KEYS: tuple[str, ...] = (
    *JOB_FEEDBACK_TEMPLATE_KEYS,
    *JOB_FEEDBACK_TOAST_KEYS,
)
JOB_FEEDBACK_CATALOGS: dict[str, dict[str, str]] = {
    locale: {
        **JOB_FEEDBACK_TEMPLATE_CATALOGS[locale],
        **JOB_FEEDBACK_TOAST_CATALOGS[locale],
    }
    for locale in _EXPECTED_FEEDBACK_LOCALES
}
