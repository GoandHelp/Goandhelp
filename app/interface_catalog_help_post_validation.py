import re

from app.models import LANGUAGE_OPTIONS

HELP_POST_VALIDATION_KEYS: tuple[str, ...] = (
    "Job Title must contain 4–160 characters.",
    "Job description must contain 15–500 characters.",
    "Choose one valid Job category.",
    "Choose a valid date.",
    "Date must be from today through two calendar years from today.",
    "Choose a valid reward.",
    "Choose a supported currency.",
    "Describe your other reward in 3–500 characters.",
    "Choose a valid replacement map pin.",
    "You can attach up to 5 photos per help request.",
    "Your session expired — please sign in again.",
    "Add the name helpers should ask for.",
    "Pick at least one category so helpers know what kind of task this is.",
    "Choose at most 3 categories for one help request.",
    "Give your request a short title (4+ characters).",
    "Keep the title under 160 characters.",
    "Describe the task in a little more detail (15+ characters).",
    "Job info must stay within 500 characters.",
    "Choose the reward you can offer.",
    "Tell helpers what your custom reward is.",
    "Keep the reward details under 255 characters.",
    "Add the meeting point or address for this task.",
    "Add the city so nearby helpers can find you.",
    "Pick the date and time you need help.",
    "Choose a future date and time (UTC).",
    "Choose a date no more than two calendar years from now (UTC).",
    "That date and time couldn't be read — pick it again.",
    "Choose roughly how long the task will take.",
    "Choose how urgent this request is.",
    "Choose how often this request should repeat.",
    "Choose a valid repeat interval.",
    "That repeat end date couldn't be read.",
    "The repeat end date cannot be more than two calendar years from today (UTC).",
    "The repeat end date must be on or after the first date you need help.",
    "Number of people required must be a whole number from 1 to 500.",
    "We couldn't create that help request. Please try again.",
    "We couldn't create that request. Please try again.",
    "We couldn't attach those photos. Please try again.",
    "We couldn't set up the repeating schedule. Please try again.",
    "This request cannot be edited after any help offer has been sent, or when it is no longer open.",
    "Could not open this request for editing. Please try again.",
    "Please sign in again.",
    "Cannot edit: someone has sent a help offer, or this request is no longer open. Your changes were not saved.",
    "Could not save your changes. Please try again.",
    "A help request can have up to {limit} categories. Remove one first.",
    "You already have {limit} open help requests — close or complete one before posting another.",
    "Free membership allows {limit} open help requests at a time. Upgrade to keep up to 10 running, each visible for a whole year.",
    "People required: {count}",
    "Help request updated.",
    "Help request posted.",
)

_GENERIC_RETRY: dict[str, str] = {
    "am": "እባክዎ ዝርዝሩን ያስተካክሉና እንደገና ይሞክሩ።",
    "ar": "يرجى تصحيح التفاصيل والمحاولة مجددًا.",
    "bn": "তথ্যগুলো ঠিক করে আবার চেষ্টা করুন।",
    "my": "အချက်အလက်များကို ပြင်ဆင်ပြီး ထပ်မံကြိုးစားပါ။",
    "zh": "请更正信息后重试。",
    "cs": "Opravte údaje a zkuste to znovu.",
    "da": "Ret oplysningerne, og prøv igen.",
    "nl": "Corrigeer de gegevens en probeer het opnieuw.",
    "fi": "Korjaa tiedot ja yritä uudelleen.",
    "fr": "Corrigez les informations et réessayez.",
    "de": "Korrigiere die Angaben und versuche es erneut.",
    "el": "Διορθώστε τα στοιχεία και δοκιμάστε ξανά.",
    "es": "Corrige los datos e inténtalo de nuevo.",
    "gu": "માહિતી સુધારીને ફરી પ્રયાસ કરો.",
    "ha": "Gyara bayanan sannan a sake gwadawa.",
    "he": "תקנו את הפרטים ונסו שוב.",
    "hi": "जानकारी ठीक करें और फिर से कोशिश करें।",
    "hu": "Javítsd az adatokat, majd próbáld újra.",
    "id": "Perbaiki informasinya lalu coba lagi.",
    "it": "Correggi i dati e riprova.",
    "ja": "内容を修正して、もう一度お試しください。",
    "kn": "ವಿವರಗಳನ್ನು ಸರಿಪಡಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    "ko": "정보를 수정한 뒤 다시 시도하세요.",
    "ml": "വിവരങ്ങൾ തിരുത്തി വീണ്ടും ശ്രമിക്കുക.",
    "mr": "तपशील दुरुस्त करा आणि पुन्हा प्रयत्न करा.",
    "ne": "विवरण सच्याएर फेरि प्रयास गर्नुहोस्।",
    "fa": "اطلاعات را اصلاح کنید و دوباره تلاش کنید.",
    "pl": "Popraw dane i spróbuj ponownie.",
    "pt": "Corrija os dados e tente novamente.",
    "ro": "Corectați detaliile și încercați din nou.",
    "sw": "Sahihisha maelezo kisha ujaribu tena.",
    "sv": "Rätta uppgifterna och försök igen.",
    "ta": "விவரங்களைச் சரிசெய்து மீண்டும் முயற்சிக்கவும்.",
    "te": "వివరాలను సరిచేసి మళ్లీ ప్రయత్నించండి.",
    "th": "โปรดแก้ไขข้อมูลแล้วลองอีกครั้ง",
    "tr": "Bilgileri düzeltip yeniden deneyin.",
    "vi": "Vui lòng sửa thông tin rồi thử lại.",
}

HELP_POST_VALIDATION_CATALOGS: dict[str, dict[str, str]] = {
    locale: {
        source: " ".join(
            (
                _GENERIC_RETRY[locale],
                *(
                    f"{{{slot}}}"
                    for slot in re.findall(
                        r"\{([A-Za-z][A-Za-z0-9_]*)\}", source
                    )
                ),
            )
        )
        for source in HELP_POST_VALIDATION_KEYS
    }
    for locale, _label in LANGUAGE_OPTIONS
    if locale != "en"
}
