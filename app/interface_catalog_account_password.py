import reflex as rx

import string
from collections import Counter

from app.models import LANGUAGE_OPTIONS

ACCOUNT_PASSWORD_KEYS: tuple[str, ...] = (
    "Change password",
    "Current password",
    "New password",
    "Confirm new password",
    "Changing password…",
    "Enter your current password.",
    "Passwords need at least 6 characters.",
    "The two passwords don't match.",
    "Choose a new password different from your current password.",
    "We couldn't save that password just now. Please try again.",
    "Current password is incorrect.",
    "Your password has been changed.",
    "Password changed.",
    "Your session expired — please sign in again.",
)

ACCOUNT_PASSWORD_ROWS: dict[str, str] = {
    "am": "የይለፍ ቃል ቀይር|የአሁኑ የይለፍ ቃል|አዲስ የይለፍ ቃል|አዲሱን የይለፍ ቃል አረጋግጥ|የይለፍ ቃል በመቀየር ላይ…|የአሁኑን የይለፍ ቃልዎን ያስገቡ።|የይለፍ ቃሎች ቢያንስ 6 ቁምፊዎች ሊኖሯቸው ይገባል።|ሁለቱ የይለፍ ቃሎች አይዛመዱም።|ከአሁኑ የይለፍ ቃልዎ የተለየ አዲስ የይለፍ ቃል ይምረጡ።|ያንን የይለፍ ቃል አሁን ማስቀመጥ አልቻልንም። እባክዎ እንደገና ይሞክሩ።|የአሁኑ የይለፍ ቃል ትክክል አይደለም።|የይለፍ ቃልዎ ተቀይሯል።|የይለፍ ቃል ተቀይሯል።|የመግቢያ ጊዜዎ አልቋል፤ እባክዎ እንደገና ይግቡ።",
    "ar": "تغيير كلمة المرور|كلمة المرور الحالية|كلمة المرور الجديدة|تأكيد كلمة المرور الجديدة|جارٍ تغيير كلمة المرور…|أدخل كلمة مرورك الحالية.|يجب أن تتكون كلمات المرور من 6 أحرف على الأقل.|كلمتا المرور غير متطابقتين.|اختر كلمة مرور جديدة تختلف عن كلمة مرورك الحالية.|تعذر حفظ كلمة المرور الآن. يُرجى المحاولة مجددًا.|كلمة المرور الحالية غير صحيحة.|تم تغيير كلمة مرورك.|تم تغيير كلمة المرور.|انتهت جلستك — يُرجى تسجيل الدخول مجددًا.",
    "bn": "পাসওয়ার্ড পরিবর্তন করুন|বর্তমান পাসওয়ার্ড|নতুন পাসওয়ার্ড|নতুন পাসওয়ার্ড নিশ্চিত করুন|পাসওয়ার্ড পরিবর্তন হচ্ছে…|আপনার বর্তমান পাসওয়ার্ড লিখুন।|পাসওয়ার্ডে অন্তত ৬টি অক্ষর থাকতে হবে।|পাসওয়ার্ড দুটি মেলেনি।|আপনার বর্তমান পাসওয়ার্ড থেকে আলাদা একটি নতুন পাসওয়ার্ড বেছে নিন।|এখন পাসওয়ার্ডটি সংরক্ষণ করা যায়নি। আবার চেষ্টা করুন।|বর্তমান পাসওয়ার্ড ভুল।|আপনার পাসওয়ার্ড পরিবর্তন হয়েছে।|পাসওয়ার্ড পরিবর্তন হয়েছে।|আপনার সেশনের মেয়াদ শেষ হয়েছে — আবার সাইন ইন করুন।",
    "my": "စကားဝှက်ပြောင်းရန်|လက်ရှိစကားဝှက်|စကားဝှက်အသစ်|စကားဝှက်အသစ်ကို အတည်ပြုပါ|စကားဝှက်ပြောင်းနေသည်…|သင့်လက်ရှိစကားဝှက်ကို ထည့်ပါ။|စကားဝှက်တွင် အနည်းဆုံး စာလုံး ၆ လုံး ပါရမည်။|စကားဝှက်နှစ်ခု မတူညီပါ။|လက်ရှိစကားဝှက်နှင့် မတူသော စကားဝှက်အသစ်ကို ရွေးပါ။|ယခု စကားဝှက်ကို မသိမ်းနိုင်ပါ။ ထပ်မံကြိုးစားပါ။|လက်ရှိစကားဝှက် မှားနေပါသည်။|သင့်စကားဝှက်ကို ပြောင်းပြီးပါပြီ။|စကားဝှက် ပြောင်းပြီးပါပြီ။|သင့်ဝင်ရောက်မှု သက်တမ်းကုန်သွားပါပြီ — ပြန်လည်ဝင်ရောက်ပါ။",
    "zh": "修改密码|当前密码|新密码|确认新密码|正在修改密码…|请输入当前密码。|密码至少需要6个字符。|两次输入的密码不一致。|请选择与当前密码不同的新密码。|暂时无法保存密码，请重试。|当前密码不正确。|你的密码已修改。|密码已修改。|登录已过期，请重新登录。",
    "cs": "Změnit heslo|Současné heslo|Nové heslo|Potvrdit nové heslo|Změna hesla…|Zadejte své současné heslo.|Hesla musí mít alespoň 6 znaků.|Zadaná hesla se neshodují.|Zvolte nové heslo odlišné od současného.|Heslo se nyní nepodařilo uložit. Zkuste to znovu.|Současné heslo je nesprávné.|Vaše heslo bylo změněno.|Heslo změněno.|Platnost relace vypršela — přihlaste se znovu.",
    "da": "Skift adgangskode|Nuværende adgangskode|Ny adgangskode|Bekræft ny adgangskode|Skifter adgangskode…|Indtast din nuværende adgangskode.|Adgangskoder skal have mindst 6 tegn.|De to adgangskoder er ikke ens.|Vælg en ny adgangskode, der er forskellig fra din nuværende.|Vi kunne ikke gemme adgangskoden lige nu. Prøv igen.|Den nuværende adgangskode er forkert.|Din adgangskode er blevet ændret.|Adgangskode ændret.|Din session er udløbet — log ind igen.",
    "nl": "Wachtwoord wijzigen|Huidig wachtwoord|Nieuw wachtwoord|Nieuw wachtwoord bevestigen|Wachtwoord wordt gewijzigd…|Voer je huidige wachtwoord in.|Wachtwoorden moeten minstens 6 tekens bevatten.|De twee wachtwoorden komen niet overeen.|Kies een nieuw wachtwoord dat verschilt van je huidige wachtwoord.|We konden het wachtwoord nu niet opslaan. Probeer het opnieuw.|Het huidige wachtwoord is onjuist.|Je wachtwoord is gewijzigd.|Wachtwoord gewijzigd.|Je sessie is verlopen — log opnieuw in.",
    "fi": "Vaihda salasana|Nykyinen salasana|Uusi salasana|Vahvista uusi salasana|Vaihdetaan salasanaa…|Anna nykyinen salasanasi.|Salasanoissa on oltava vähintään 6 merkkiä.|Salasanat eivät täsmää.|Valitse uusi salasana, joka eroaa nykyisestä salasanastasi.|Salasanaa ei voitu tallentaa juuri nyt. Yritä uudelleen.|Nykyinen salasana on väärä.|Salasanasi on vaihdettu.|Salasana vaihdettu.|Istuntosi on vanhentunut — kirjaudu uudelleen sisään.",
    "fr": "Changer le mot de passe|Mot de passe actuel|Nouveau mot de passe|Confirmer le nouveau mot de passe|Modification du mot de passe…|Saisissez votre mot de passe actuel.|Les mots de passe doivent contenir au moins 6 caractères.|Les deux mots de passe ne correspondent pas.|Choisissez un nouveau mot de passe différent de votre mot de passe actuel.|Impossible d’enregistrer ce mot de passe pour le moment. Veuillez réessayer.|Le mot de passe actuel est incorrect.|Votre mot de passe a été modifié.|Mot de passe modifié.|Votre session a expiré — veuillez vous reconnecter.",
    "de": "Passwort ändern|Aktuelles Passwort|Neues Passwort|Neues Passwort bestätigen|Passwort wird geändert…|Gib dein aktuelles Passwort ein.|Passwörter müssen mindestens 6 Zeichen enthalten.|Die beiden Passwörter stimmen nicht überein.|Wähle ein neues Passwort, das sich von deinem aktuellen unterscheidet.|Das Passwort konnte gerade nicht gespeichert werden. Bitte versuche es erneut.|Das aktuelle Passwort ist falsch.|Dein Passwort wurde geändert.|Passwort geändert.|Deine Sitzung ist abgelaufen — bitte melde dich erneut an.",
    "el": "Αλλαγή κωδικού πρόσβασης|Τρέχων κωδικός πρόσβασης|Νέος κωδικός πρόσβασης|Επιβεβαίωση νέου κωδικού πρόσβασης|Αλλαγή κωδικού πρόσβασης…|Εισαγάγετε τον τρέχοντα κωδικό πρόσβασής σας.|Οι κωδικοί πρόσβασης πρέπει να έχουν τουλάχιστον 6 χαρακτήρες.|Οι δύο κωδικοί πρόσβασης δεν ταιριάζουν.|Επιλέξτε έναν νέο κωδικό πρόσβασης διαφορετικό από τον τρέχοντα.|Δεν μπορέσαμε να αποθηκεύσουμε τον κωδικό πρόσβασης τώρα. Δοκιμάστε ξανά.|Ο τρέχων κωδικός πρόσβασης είναι λανθασμένος.|Ο κωδικός πρόσβασής σας άλλαξε.|Ο κωδικός πρόσβασης άλλαξε.|Η συνεδρία σας έληξε — συνδεθείτε ξανά.",
    "gu": "પાસવર્ડ બદલો|વર્તમાન પાસવર્ડ|નવો પાસવર્ડ|નવા પાસવર્ડની પુષ્ટિ કરો|પાસવર્ડ બદલાઈ રહ્યો છે…|તમારો વર્તમાન પાસવર્ડ દાખલ કરો.|પાસવર્ડમાં ઓછામાં ઓછા 6 અક્ષરો હોવા જોઈએ.|બંને પાસવર્ડ મળતા નથી.|તમારા વર્તમાન પાસવર્ડથી અલગ નવો પાસવર્ડ પસંદ કરો.|હમણાં પાસવર્ડ સાચવી શક્યા નથી. કૃપા કરીને ફરી પ્રયાસ કરો.|વર્તમાન પાસવર્ડ ખોટો છે.|તમારો પાસવર્ડ બદલાઈ ગયો છે.|પાસવર્ડ બદલાઈ ગયો છે.|તમારું સત્ર સમાપ્ત થયું છે — કૃપા કરીને ફરી સાઇન ઇન કરો.",
    "ha": "Canja kalmar sirri|Kalmar sirri ta yanzu|Sabuwar kalmar sirri|Tabbatar da sabuwar kalmar sirri|Ana canja kalmar sirri…|Shigar da kalmar sirrinka ta yanzu.|Kalmar sirri tana buƙatar aƙalla haruffa 6.|Kalmomin sirrin biyu ba su yi daidai ba.|Zaɓi sabuwar kalmar sirri dabam da wadda kake amfani da ita yanzu.|Ba mu iya ajiye kalmar sirrin yanzu ba. Da fatan a sake gwadawa.|Kalmar sirri ta yanzu ba daidai ba ce.|An canja kalmar sirrinka.|An canja kalmar sirri.|Zamanka ya ƙare — da fatan ka sake shiga.",
    "he": "שינוי סיסמה|סיסמה נוכחית|סיסמה חדשה|אישור הסיסמה החדשה|משנים את הסיסמה…|הזינו את הסיסמה הנוכחית שלכם.|סיסמאות חייבות להכיל לפחות 6 תווים.|שתי הסיסמאות אינן תואמות.|בחרו סיסמה חדשה השונה מהסיסמה הנוכחית שלכם.|לא הצלחנו לשמור את הסיסמה כרגע. נסו שוב.|הסיסמה הנוכחית שגויה.|הסיסמה שלכם שונתה.|הסיסמה שונתה.|פג תוקף ההתחברות שלכם — היכנסו שוב.",
    "hi": "पासवर्ड बदलें|वर्तमान पासवर्ड|नया पासवर्ड|नए पासवर्ड की पुष्टि करें|पासवर्ड बदला जा रहा है…|अपना वर्तमान पासवर्ड दर्ज करें।|पासवर्ड में कम से कम 6 अक्षर होने चाहिए।|दोनों पासवर्ड मेल नहीं खाते।|अपने वर्तमान पासवर्ड से अलग नया पासवर्ड चुनें।|अभी पासवर्ड सहेजा नहीं जा सका। कृपया फिर कोशिश करें।|वर्तमान पासवर्ड गलत है।|आपका पासवर्ड बदल दिया गया है।|पासवर्ड बदल दिया गया है।|आपके सत्र की समय-सीमा समाप्त हो गई है — कृपया फिर साइन इन करें।",
    "hu": "Jelszó módosítása|Jelenlegi jelszó|Új jelszó|Új jelszó megerősítése|Jelszó módosítása folyamatban…|Add meg a jelenlegi jelszavad.|A jelszavaknak legalább 6 karakterből kell állniuk.|A két jelszó nem egyezik.|Válassz a jelenlegitől eltérő új jelszót.|Most nem sikerült menteni a jelszót. Próbáld újra.|A jelenlegi jelszó helytelen.|A jelszavad megváltozott.|Jelszó módosítva.|A munkameneted lejárt — jelentkezz be újra.",
    "id": "Ubah kata sandi|Kata sandi saat ini|Kata sandi baru|Konfirmasi kata sandi baru|Mengubah kata sandi…|Masukkan kata sandi Anda saat ini.|Kata sandi harus berisi minimal 6 karakter.|Kedua kata sandi tidak cocok.|Pilih kata sandi baru yang berbeda dari kata sandi Anda saat ini.|Kami tidak dapat menyimpan kata sandi sekarang. Silakan coba lagi.|Kata sandi saat ini salah.|Kata sandi Anda telah diubah.|Kata sandi diubah.|Sesi Anda telah berakhir — silakan masuk kembali.",
    "it": "Cambia password|Password attuale|Nuova password|Conferma la nuova password|Modifica della password…|Inserisci la tua password attuale.|Le password devono contenere almeno 6 caratteri.|Le due password non corrispondono.|Scegli una nuova password diversa da quella attuale.|Non è stato possibile salvare la password in questo momento. Riprova.|La password attuale non è corretta.|La tua password è stata modificata.|Password modificata.|La sessione è scaduta — accedi di nuovo.",
    "ja": "パスワードを変更|現在のパスワード|新しいパスワード|新しいパスワードを確認|パスワードを変更中…|現在のパスワードを入力してください。|パスワードは6文字以上必要です。|2つのパスワードが一致しません。|現在のパスワードとは異なる新しいパスワードを選んでください。|今はパスワードを保存できません。もう一度お試しください。|現在のパスワードが正しくありません。|あなたのパスワードを変更しました。|パスワードを変更しました。|セッションの有効期限が切れました。再度ログインしてください。",
    "kn": "ಪಾಸ್‌ವರ್ಡ್ ಬದಲಿಸಿ|ಪ್ರಸ್ತುತ ಪಾಸ್‌ವರ್ಡ್|ಹೊಸ ಪಾಸ್‌ವರ್ಡ್|ಹೊಸ ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ|ಪಾಸ್‌ವರ್ಡ್ ಬದಲಿಸಲಾಗುತ್ತಿದೆ…|ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ.|ಪಾಸ್‌ವರ್ಡ್‌ಗಳಲ್ಲಿ ಕನಿಷ್ಠ 6 ಅಕ್ಷರಗಳು ಇರಬೇಕು.|ಎರಡು ಪಾಸ್‌ವರ್ಡ್‌ಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ.|ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಪಾಸ್‌ವರ್ಡ್‌ಗಿಂತ ಭಿನ್ನವಾದ ಹೊಸ ಪಾಸ್‌ವರ್ಡ್ ಆಯ್ಕೆಮಾಡಿ.|ಈಗ ಪಾಸ್‌ವರ್ಡ್ ಉಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.|ಪ್ರಸ್ತುತ ಪಾಸ್‌ವರ್ಡ್ ತಪ್ಪಾಗಿದೆ.|ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ಬದಲಿಸಲಾಗಿದೆ.|ಪಾಸ್‌ವರ್ಡ್ ಬದಲಿಸಲಾಗಿದೆ.|ನಿಮ್ಮ ಅವಧಿ ಮುಗಿದಿದೆ — ದಯವಿಟ್ಟು ಮತ್ತೆ ಸೈನ್ ಇನ್ ಮಾಡಿ.",
    "ko": "비밀번호 변경|현재 비밀번호|새 비밀번호|새 비밀번호 확인|비밀번호 변경 중…|현재 비밀번호를 입력하세요.|비밀번호는 최소 6자여야 합니다.|두 비밀번호가 일치하지 않습니다.|현재 비밀번호와 다른 새 비밀번호를 선택하세요.|지금 비밀번호를 저장하지 못했습니다. 다시 시도하세요.|현재 비밀번호가 올바르지 않습니다.|회원님의 비밀번호가 변경되었습니다.|비밀번호가 변경되었습니다.|세션이 만료되었습니다. 다시 로그인하세요.",
    "ml": "പാസ്‌വേഡ് മാറ്റുക|നിലവിലെ പാസ്‌വേഡ്|പുതിയ പാസ്‌വേഡ്|പുതിയ പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക|പാസ്‌വേഡ് മാറ്റുന്നു…|നിങ്ങളുടെ നിലവിലെ പാസ്‌വേഡ് നൽകുക.|പാസ്‌വേഡുകളിൽ കുറഞ്ഞത് 6 അക്ഷരങ്ങൾ ഉണ്ടായിരിക്കണം.|രണ്ട് പാസ്‌വേഡുകളും പൊരുത്തപ്പെടുന്നില്ല.|നിലവിലെ പാസ്‌വേഡിൽ നിന്ന് വ്യത്യസ്തമായ പുതിയ പാസ്‌വേഡ് തിരഞ്ഞെടുക്കുക.|ഇപ്പോൾ പാസ്‌വേഡ് സംരക്ഷിക്കാനായില്ല. വീണ്ടും ശ്രമിക്കുക.|നിലവിലെ പാസ്‌വേഡ് തെറ്റാണ്.|നിങ്ങളുടെ പാസ്‌വേഡ് മാറ്റിയിരിക്കുന്നു.|പാസ്‌വേഡ് മാറ്റി.|നിങ്ങളുടെ സെഷന്റെ കാലാവധി കഴിഞ്ഞു — വീണ്ടും സൈൻ ഇൻ ചെയ്യുക.",
    "mr": "पासवर्ड बदला|सध्याचा पासवर्ड|नवीन पासवर्ड|नवीन पासवर्डची पुष्टी करा|पासवर्ड बदलत आहे…|तुमचा सध्याचा पासवर्ड टाका।|पासवर्डमध्ये किमान 6 अक्षरे असणे आवश्यक आहे।|दोन्ही पासवर्ड जुळत नाहीत।|तुमच्या सध्याच्या पासवर्डपेक्षा वेगळा नवीन पासवर्ड निवडा।|आत्ता पासवर्ड जतन करता आला नाही. कृपया पुन्हा प्रयत्न करा।|सध्याचा पासवर्ड चुकीचा आहे।|तुमचा पासवर्ड बदलला आहे।|पासवर्ड बदलला आहे।|तुमच्या सत्राची मुदत संपली आहे — कृपया पुन्हा साइन इन करा।",
    "ne": "पासवर्ड परिवर्तन गर्नुहोस्|हालको पासवर्ड|नयाँ पासवर्ड|नयाँ पासवर्ड पुष्टि गर्नुहोस्|पासवर्ड परिवर्तन हुँदै छ…|आफ्नो हालको पासवर्ड प्रविष्ट गर्नुहोस्।|पासवर्डमा कम्तीमा ६ अक्षर हुनुपर्छ।|दुई पासवर्ड मेल खाँदैनन्।|आफ्नो हालको पासवर्डभन्दा फरक नयाँ पासवर्ड छान्नुहोस्।|अहिले पासवर्ड सुरक्षित गर्न सकेनौँ। फेरि प्रयास गर्नुहोस्।|हालको पासवर्ड गलत छ।|तपाईंको पासवर्ड परिवर्तन गरिएको छ।|पासवर्ड परिवर्तन भयो।|तपाईंको सत्रको म्याद सकियो — कृपया फेरि साइन इन गर्नुहोस्।",
    "fa": "تغییر رمز عبور|رمز عبور فعلی|رمز عبور جدید|تأیید رمز عبور جدید|در حال تغییر رمز عبور…|رمز عبور فعلی خود را وارد کنید.|رمزهای عبور باید حداقل ۶ نویسه داشته باشند.|دو رمز عبور مطابقت ندارند.|رمز عبور جدیدی متفاوت با رمز عبور فعلی خود انتخاب کنید.|اکنون نتوانستیم رمز عبور را ذخیره کنیم. لطفاً دوباره تلاش کنید.|رمز عبور فعلی نادرست است.|رمز عبور شما تغییر کرده است.|رمز عبور تغییر کرد.|نشست شما منقضی شده است — لطفاً دوباره وارد شوید.",
    "pl": "Zmień hasło|Obecne hasło|Nowe hasło|Potwierdź nowe hasło|Zmienianie hasła…|Wpisz swoje obecne hasło.|Hasła muszą zawierać co najmniej 6 znaków.|Oba hasła nie są takie same.|Wybierz nowe hasło inne niż obecne.|Nie udało się teraz zapisać hasła. Spróbuj ponownie.|Obecne hasło jest nieprawidłowe.|Twoje hasło zostało zmienione.|Hasło zmienione.|Twoja sesja wygasła — zaloguj się ponownie.",
    "pt": "Alterar palavra-passe|Palavra-passe atual|Nova palavra-passe|Confirmar nova palavra-passe|A alterar a palavra-passe…|Introduza a sua palavra-passe atual.|As palavras-passe devem ter pelo menos 6 caracteres.|As duas palavras-passe não coincidem.|Escolha uma nova palavra-passe diferente da atual.|Não foi possível guardar a palavra-passe agora. Tente novamente.|A palavra-passe atual está incorreta.|A sua palavra-passe foi alterada.|Palavra-passe alterada.|A sua sessão expirou — inicie sessão novamente.",
    "ro": "Schimbă parola|Parola actuală|Parola nouă|Confirmă parola nouă|Se schimbă parola…|Introdu parola actuală.|Parolele trebuie să aibă cel puțin 6 caractere.|Cele două parole nu coincid.|Alege o parolă nouă diferită de parola actuală.|Nu am putut salva parola acum. Încearcă din nou.|Parola actuală este incorectă.|Parola ta a fost schimbată.|Parola a fost schimbată.|Sesiunea ta a expirat — autentifică-te din nou.",
    "es": "Cambiar contraseña|Contraseña actual|Nueva contraseña|Confirmar nueva contraseña|Cambiando contraseña…|Introduce tu contraseña actual.|Las contraseñas deben tener al menos 6 caracteres.|Las dos contraseñas no coinciden.|Elige una nueva contraseña diferente de la actual.|No pudimos guardar la contraseña ahora. Inténtalo de nuevo.|La contraseña actual es incorrecta.|Tu contraseña se ha cambiado.|Contraseña cambiada.|Tu sesión ha caducado — vuelve a iniciar sesión.",
    "sw": "Badilisha nenosiri|Nenosiri la sasa|Nenosiri jipya|Thibitisha nenosiri jipya|Nenosiri linabadilishwa…|Weka nenosiri lako la sasa.|Nenosiri lazima liwe na angalau herufi 6.|Nenosiri uliloingiza mara mbili halilingani.|Chagua nenosiri jipya tofauti na nenosiri lako la sasa.|Hatukuweza kuhifadhi nenosiri sasa hivi. Tafadhali jaribu tena.|Nenosiri la sasa si sahihi.|Nenosiri lako limebadilishwa.|Nenosiri limebadilishwa.|Kipindi chako kimeisha — tafadhali ingia tena.",
    "sv": "Ändra lösenord|Nuvarande lösenord|Nytt lösenord|Bekräfta nytt lösenord|Ändrar lösenord…|Ange ditt nuvarande lösenord.|Lösenord måste innehålla minst 6 tecken.|De två lösenorden stämmer inte överens.|Välj ett nytt lösenord som skiljer sig från ditt nuvarande.|Vi kunde inte spara lösenordet just nu. Försök igen.|Det nuvarande lösenordet är felaktigt.|Ditt lösenord har ändrats.|Lösenord ändrat.|Din session har gått ut — logga in igen.",
    "ta": "கடவுச்சொல்லை மாற்றவும்|தற்போதைய கடவுச்சொல்|புதிய கடவுச்சொல்|புதிய கடவுச்சொல்லை உறுதிப்படுத்தவும்|கடவுச்சொல் மாற்றப்படுகிறது…|உங்கள் தற்போதைய கடவுச்சொல்லை உள்ளிடவும்.|கடவுச்சொற்களில் குறைந்தது 6 எழுத்துகள் இருக்க வேண்டும்.|இரண்டு கடவுச்சொற்களும் பொருந்தவில்லை.|தற்போதைய கடவுச்சொல்லிலிருந்து வேறுபட்ட புதிய கடவுச்சொல்லைத் தேர்ந்தெடுக்கவும்.|இப்போது கடவுச்சொல்லைச் சேமிக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.|தற்போதைய கடவுச்சொல் தவறானது.|உங்கள் கடவுச்சொல் மாற்றப்பட்டுள்ளது.|கடவுச்சொல் மாற்றப்பட்டது.|உங்கள் அமர்வு காலாவதியாகிவிட்டது — மீண்டும் உள்நுழையவும்.",
    "te": "పాస్‌వర్డ్ మార్చండి|ప్రస్తుత పాస్‌వర్డ్|కొత్త పాస్‌వర్డ్|కొత్త పాస్‌వర్డ్ నిర్ధారించండి|పాస్‌వర్డ్ మారుస్తున్నాం…|మీ ప్రస్తుత పాస్‌వర్డ్ నమోదు చేయండి.|పాస్‌వర్డ్‌లో కనీసం 6 అక్షరాలు ఉండాలి.|రెండు పాస్‌వర్డ్‌లు సరిపోలడం లేదు.|మీ ప్రస్తుత పాస్‌వర్డ్‌కు భిన్నమైన కొత్త పాస్‌వర్డ్ ఎంచుకోండి.|ఇప్పుడు పాస్‌వర్డ్ సేవ్ చేయలేకపోయాం. దయచేసి మళ్లీ ప్రయత్నించండి.|ప్రస్తుత పాస్‌వర్డ్ తప్పు.|మీ పాస్‌వర్డ్ మార్చబడింది.|పాస్‌వర్డ్ మార్చబడింది.|మీ సెషన్ గడువు ముగిసింది — దయచేసి మళ్లీ సైన్ ఇన్ చేయండి.",
    "th": "เปลี่ยนรหัสผ่าน|รหัสผ่านปัจจุบัน|รหัสผ่านใหม่|ยืนยันรหัสผ่านใหม่|กำลังเปลี่ยนรหัสผ่าน…|กรอกรหัสผ่านปัจจุบันของคุณ|รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร|รหัสผ่านทั้งสองไม่ตรงกัน|เลือกรหัสผ่านใหม่ที่ต่างจากรหัสผ่านปัจจุบัน|ยังบันทึกรหัสผ่านไม่ได้ในตอนนี้ โปรดลองอีกครั้ง|รหัสผ่านปัจจุบันไม่ถูกต้อง|เปลี่ยนรหัสผ่านของคุณแล้ว|เปลี่ยนรหัสผ่านแล้ว|เซสชันของคุณหมดอายุแล้ว โปรดเข้าสู่ระบบอีกครั้ง",
    "tr": "Şifreyi değiştir|Mevcut şifre|Yeni şifre|Yeni şifreyi doğrula|Şifre değiştiriliyor…|Mevcut şifrenizi girin.|Şifreler en az 6 karakter içermelidir.|İki şifre eşleşmiyor.|Mevcut şifrenizden farklı yeni bir şifre seçin.|Şifreyi şu anda kaydedemedik. Lütfen tekrar deneyin.|Mevcut şifre yanlış.|Şifreniz değiştirildi.|Şifre değiştirildi.|Oturumunuzun süresi doldu — lütfen tekrar giriş yapın.",
    "vi": "Đổi mật khẩu|Mật khẩu hiện tại|Mật khẩu mới|Xác nhận mật khẩu mới|Đang đổi mật khẩu…|Nhập mật khẩu hiện tại của bạn.|Mật khẩu phải có ít nhất 6 ký tự.|Hai mật khẩu không khớp.|Chọn mật khẩu mới khác với mật khẩu hiện tại.|Chưa thể lưu mật khẩu lúc này. Vui lòng thử lại.|Mật khẩu hiện tại không đúng.|Mật khẩu của bạn đã được thay đổi.|Đã đổi mật khẩu.|Phiên của bạn đã hết hạn — vui lòng đăng nhập lại.",
}

_expected_locales = {code for code, _ in LANGUAGE_OPTIONS if code != "en"} | {
    "ha"
}
if set(ACCOUNT_PASSWORD_ROWS) != _expected_locales:
    raise ValueError("Account password locale coverage is incomplete")
if len(ACCOUNT_PASSWORD_KEYS) != 14 or len(set(ACCOUNT_PASSWORD_KEYS)) != 14:
    raise ValueError("Account password source coverage is invalid")

_formatter = string.Formatter()
ACCOUNT_PASSWORD_CATALOGS: dict[str, dict[str, str]] = {}
for _locale, _row in ACCOUNT_PASSWORD_ROWS.items():
    _catalog = dict(zip(ACCOUNT_PASSWORD_KEYS, _row.split("|"), strict=True))
    for _source, _value in _catalog.items():
        if not _value.strip() or _value == _source:
            raise ValueError(
                f"Missing account password translation: {_locale}: {_source}"
            )
        _source_slots = Counter(
            name for _, name, _, _ in _formatter.parse(_source) if name
        )
        _value_slots = Counter(
            name for _, name, _, _ in _formatter.parse(_value) if name
        )
        if _source_slots != _value_slots:
            raise ValueError(
                f"Invalid account password placeholders: {_locale}: {_source}"
            )
    ACCOUNT_PASSWORD_CATALOGS[_locale] = _catalog
