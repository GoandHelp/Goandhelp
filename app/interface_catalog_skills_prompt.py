from app.models import LANGUAGE_OPTIONS

SKILLS_PROMPT_KEYS: tuple[str, ...] = (
    "Please fill out your Skills and Knowledge in order to be seen on the map",
    "Choose a category or add your skills so people know how you can help.",
    "Let people know how I can help",
)

SKILLS_PROMPT_ROWS: dict[str, str] = {
    "am": "ካርታው ላይ እንዲታዩ እባክዎ ክህሎቶችዎን እና እውቀትዎን ያሟሉ|ሰዎች እንዴት ሊረዱ እንደሚችሉ እንዲያውቁ ምድብ ይምረጡ ወይም ክህሎቶችዎን ያክሉ።|ሰዎች እንዴት ልረዳ እንደምችል ያሳውቁ",
    "ar": "يرجى استكمال المهارات والمعارف لديك حتى تظهر على الخريطة|اختر فئة أو أضف مهاراتك ليعرف الناس كيف يمكنك مساعدتهم.|أخبر الناس كيف يمكنني المساعدة",
    "bn": "মানচিত্রে দেখা যেতে আপনার দক্ষতা ও জ্ঞান পূরণ করুন|একটি বিভাগ বেছে নিন বা আপনার দক্ষতা যোগ করুন, যাতে মানুষ জানতে পারে আপনি কীভাবে সাহায্য করতে পারেন।|আমি কীভাবে সাহায্য করতে পারি তা মানুষকে জানান",
    "my": "မြေပုံပေါ်တွင် မြင်ရစေရန် သင့်ကျွမ်းကျင်မှုများနှင့် အသိပညာကို ဖြည့်စွက်ပါ|လူများက သင်မည်သို့ ကူညီနိုင်သည်ကို သိနိုင်ရန် အမျိုးအစားတစ်ခု ရွေးပါ သို့မဟုတ် သင့်ကျွမ်းကျင်မှုများကို ထည့်ပါ။|ကျွန်ုပ် မည်သို့ကူညီနိုင်ကြောင်း လူများကို အသိပေးပါ",
    "zh": "请填写您的技能和知识，以便在地图上显示|选择一个类别或添加您的技能，让大家了解您可以提供哪些帮助。|告诉大家我可以如何提供帮助",
    "cs": "Doplňte prosím své dovednosti a znalosti, abyste byli vidět na mapě|Vyberte kategorii nebo přidejte své dovednosti, aby lidé věděli, jak můžete pomoci.|Dejte lidem vědět, jak mohu pomoci",
    "da": "Udfyld dine færdigheder og din viden, så du kan ses på kortet|Vælg en kategori eller tilføj dine færdigheder, så folk ved, hvordan du kan hjælpe.|Fortæl folk, hvordan jeg kan hjælpe",
    "nl": "Vul je vaardigheden en kennis in, zodat je op de kaart zichtbaar bent|Kies een categorie of voeg je vaardigheden toe, zodat mensen weten hoe je kunt helpen.|Laat mensen weten hoe ik kan helpen",
    "fi": "Täydennä taitosi ja tietosi, jotta näyt kartalla|Valitse luokka tai lisää taitojasi, jotta ihmiset tietävät, miten voit auttaa.|Kerro ihmisille, miten voin auttaa",
    "fr": "Veuillez renseigner vos compétences et connaissances afin d’apparaître sur la carte|Choisissez une catégorie ou ajoutez vos compétences pour que les gens sachent comment vous pouvez aider.|Faites savoir aux autres comment je peux aider",
    "de": "Bitte ergänze deine Fähigkeiten und Kenntnisse, damit du auf der Karte angezeigt wirst|Wähle eine Kategorie oder füge deine Fähigkeiten hinzu, damit andere wissen, wie du helfen kannst.|Lass andere wissen, wie ich helfen kann",
    "el": "Συμπληρώστε τις δεξιότητες και τις γνώσεις σας για να εμφανίζεστε στον χάρτη|Επιλέξτε μια κατηγορία ή προσθέστε τις δεξιότητές σας, ώστε οι άλλοι να γνωρίζουν πώς μπορείτε να βοηθήσετε.|Ενημερώστε τους άλλους πώς μπορώ να βοηθήσω",
    "gu": "નકશા પર દેખાવા માટે કૃપા કરીને તમારી કુશળતા અને જ્ઞાન ભરો|લોકોને તમે કેવી રીતે મદદ કરી શકો તે જાણવા માટે કોઈ શ્રેણી પસંદ કરો અથવા તમારી કુશળતા ઉમેરો.|હું કેવી રીતે મદદ કરી શકું તે લોકોને જણાવો",
    "he": "נא למלא את הכישורים והידע שלך כדי שיופיעו במפה|בחרו קטגוריה או הוסיפו את הכישורים שלכם כדי שאנשים ידעו כיצד תוכלו לעזור.|ספרו לאנשים כיצד אוכל לעזור",
    "hi": "कृपया मानचित्र पर दिखाई देने के लिए अपने कौशल और ज्ञान भरें|कोई श्रेणी चुनें या अपने कौशल जोड़ें, ताकि लोगों को पता चले कि आप कैसे मदद कर सकते हैं।|लोगों को बताएँ कि मैं कैसे मदद कर सकता हूँ",
    "hu": "Add meg a készségeidet és az ismereteidet, hogy megjelenj a térképen|Válassz kategóriát vagy add meg a készségeidet, hogy mások tudják, hogyan segíthetsz.|Tudasd másokkal, hogyan tudok segíteni",
    "id": "Lengkapi keterampilan dan pengetahuan Anda agar terlihat di peta|Pilih kategori atau tambahkan keterampilan agar orang tahu bagaimana Anda dapat membantu.|Beri tahu orang lain bagaimana saya dapat membantu",
    "it": "Completa le tue competenze e conoscenze per comparire sulla mappa|Scegli una categoria o aggiungi le tue competenze, così le persone sapranno come puoi aiutare.|Fai sapere agli altri come posso aiutare",
    "ja": "地図に表示されるよう、スキルと知識を入力してください|カテゴリーを選ぶかスキルを追加して、どのような支援ができるかを周りの人に伝えましょう。|どのような手助けができるかを周りの人に伝える",
    "kn": "ನಕ್ಷೆಯಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಕೌಶಲ್ಯಗಳು ಮತ್ತು ಜ್ಞಾನವನ್ನು ಭರ್ತಿ ಮಾಡಿ|ಜನರಿಗೆ ನೀವು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು ಎಂದು ತಿಳಿಯಲು ಒಂದು ವರ್ಗವನ್ನು ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ನಿಮ್ಮ ಕೌಶಲ್ಯಗಳನ್ನು ಸೇರಿಸಿ.|ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು ಎಂಬುದನ್ನು ಜನರಿಗೆ ತಿಳಿಸಿ",
    "ko": "지도에 표시되도록 보유한 기술과 지식을 입력해 주세요|사람들이 어떤 도움을 받을 수 있는지 알 수 있도록 분야를 선택하거나 기술을 추가하세요.|제가 어떻게 도울 수 있는지 사람들에게 알려주세요",
    "ml": "മാപ്പിൽ ദൃശ്യമാകാൻ നിങ്ങളുടെ കഴിവുകളും അറിവും പൂരിപ്പിക്കുക|നിങ്ങൾക്ക് എങ്ങനെ സഹായിക്കാനാകുമെന്ന് ആളുകൾക്ക് അറിയാൻ ഒരു വിഭാഗം തിരഞ്ഞെടുക്കുകയോ നിങ്ങളുടെ കഴിവുകൾ ചേർക്കുകയോ ചെയ്യുക.|എനിക്ക് എങ്ങനെ സഹായിക്കാനാകുമെന്ന് ആളുകളെ അറിയിക്കുക",
    "mr": "नकाशावर दिसण्यासाठी कृपया तुमची कौशल्ये आणि ज्ञान भरा|लोकांना तुम्ही कशी मदत करू शकता हे कळण्यासाठी एखादा वर्ग निवडा किंवा तुमची कौशल्ये जोडा.|मी कशी मदत करू शकते हे लोकांना कळवा",
    "ne": "नक्सामा देखिनका लागि कृपया आफ्ना सीप र ज्ञान भर्नुहोस्|मानिसहरूले तपाईंले कसरी मद्दत गर्न सक्नुहुन्छ भन्ने जानून् भनेर कुनै श्रेणी छान्नुहोस् वा आफ्ना सीप थप्नुहोस्।|म कसरी मद्दत गर्न सक्छु भनेर मानिसहरूलाई बताउनुहोस्",
    "fa": "لطفاً مهارت‌ها و دانش خود را تکمیل کنید تا در نقشه دیده شوید|یک دسته‌بندی انتخاب کنید یا مهارت‌های خود را اضافه کنید تا دیگران بدانند چگونه می‌توانید کمک کنید.|به دیگران بگویید چگونه می‌توانم کمک کنم",
    "pl": "Uzupełnij swoje umiejętności i wiedzę, aby było Cię widać na mapie|Wybierz kategorię lub dodaj umiejętności, aby inni wiedzieli, jak możesz pomóc.|Powiedz innym, jak mogę pomóc",
    "pt": "Preencha as suas competências e conhecimentos para aparecer no mapa|Escolha uma categoria ou adicione as suas competências para que as pessoas saibam como pode ajudar.|Diga às pessoas como posso ajudar",
    "ro": "Completează-ți abilitățile și cunoștințele pentru a apărea pe hartă|Alege o categorie sau adaugă-ți abilitățile, astfel încât oamenii să știe cum poți ajuta.|Spune-le oamenilor cum pot ajuta",
    "es": "Completa tus habilidades y conocimientos para aparecer en el mapa|Elige una categoría o añade tus habilidades para que la gente sepa cómo puedes ayudar.|Cuéntales a los demás cómo puedo ayudar",
    "sw": "Jaza ujuzi na maarifa yako ili uonekane kwenye ramani|Chagua kategoria au ongeza ujuzi wako ili watu wajue jinsi unavyoweza kusaidia.|Waambie watu jinsi ninavyoweza kusaidia",
    "sv": "Fyll i dina färdigheter och kunskaper så att du syns på kartan|Välj en kategori eller lägg till dina färdigheter så att andra vet hur du kan hjälpa till.|Berätta för andra hur jag kan hjälpa till",
    "ta": "வரைபடத்தில் தோன்ற உங்கள் திறன்களையும் அறிவையும் நிரப்பவும்|மக்களுக்கு நீங்கள் எவ்வாறு உதவ முடியும் என்பதைத் தெரிவிக்க ஒரு வகையைத் தேர்ந்தெடுக்கவும் அல்லது உங்கள் திறன்களைச் சேர்க்கவும்.|என்னால் எவ்வாறு உதவ முடியும் என்பதை மக்களுக்குத் தெரிவிக்கவும்",
    "te": "మ్యాప్‌లో కనిపించడానికి దయచేసి మీ నైపుణ్యాలు మరియు జ్ఞానాన్ని నమోదు చేయండి|మీరు ఎలా సహాయం చేయగలరో ఇతరులకు తెలియడానికి ఒక వర్గాన్ని ఎంచుకోండి లేదా మీ నైపుణ్యాలను జోడించండి.|నేను ఎలా సహాయం చేయగలనో ఇతరులకు తెలియజేయండి",
    "th": "กรุณากรอกทักษะและความรู้ของคุณเพื่อให้แสดงบนแผนที่|เลือกหมวดหมู่หรือเพิ่มทักษะของคุณ เพื่อให้ผู้คนรู้ว่าคุณช่วยเหลืออะไรได้บ้าง|บอกให้ผู้คนรู้ว่าฉันช่วยเหลืออะไรได้บ้าง",
    "tr": "Haritada görünmek için lütfen becerilerinizi ve bilginizi doldurun|İnsanların nasıl yardımcı olabileceğinizi bilmesi için bir kategori seçin veya becerilerinizi ekleyin.|İnsanlara nasıl yardımcı olabileceğimi bildirin",
    "vi": "Vui lòng điền kỹ năng và kiến thức của bạn để xuất hiện trên bản đồ|Hãy chọn một danh mục hoặc thêm kỹ năng để mọi người biết bạn có thể giúp đỡ như thế nào.|Cho mọi người biết tôi có thể giúp đỡ như thế nào",
}

_EXPECTED_LOCALES = {code for code, _label in LANGUAGE_OPTIONS if code != "en"}
if set(SKILLS_PROMPT_ROWS) != _EXPECTED_LOCALES:
    raise ValueError("Skills prompt catalog locale coverage is incomplete")
SKILLS_PROMPT_CATALOGS: dict[str, dict[str, str]] = {
    language: dict(zip(SKILLS_PROMPT_KEYS, row.split("|"), strict=True))
    for language, row in SKILLS_PROMPT_ROWS.items()
}
for _language, _entries in SKILLS_PROMPT_CATALOGS.items():
    for _source, _translation in _entries.items():
        if not _translation.strip() or _translation == _source:
            raise ValueError(
                f"Missing skills prompt translation: {_language}: {_source}"
            )
