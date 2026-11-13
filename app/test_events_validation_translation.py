import re
import unicodedata
import unittest
from string import Formatter

from app.interface_catalog_events import EVENT_TRANSLATIONS
from app.interface_catalog_events_validation import (
    EVENT_VALIDATION_KEYS,
    EVENT_VALIDATION_LOCALES,
    EVENT_VALIDATION_TRANSLATIONS,
    EXPECTED_EVENT_VALIDATION_LOCALES,
)
from app.models import LANGUAGE_OPTIONS


OFFERED_NON_ENGLISH = {
    code for code, _label in LANGUAGE_OPTIONS if code != "en"
}
VALID_IDENTICAL_TRANSLATIONS = {("es", "Error")}
FIVE_PHOTO_WORDS = {
    "am": "አምስት",
    "ar": "خمس",
    "bn": "পাঁচ",
    "my": "ငါး",
    "zh": "五",
    "cs": "pět",
    "da": "fem",
    "nl": "vijf",
    "fi": "viisi",
    "fr": "cinq",
    "de": "fünf",
    "el": "πέντε",
    "gu": "પાંચ",
    "ha": "biyar",
    "he": "חמש",
    "hi": "पाँच",
    "hu": "öt",
    "id": "lima",
    "it": "cinque",
    "ja": "5 枚",
    "kn": "ಐದು",
    "ko": "5장",
    "ml": "അഞ്ച്",
    "mr": "पाच",
    "ne": "पाँच",
    "fa": "پنج",
    "pl": "pięć",
    "pt": "cinco",
    "ro": "cinci",
    "es": "cinco",
    "sw": "tano",
    "sv": "fem",
    "ta": "ஐந்து",
    "te": "ఐదు",
    "th": "ห้า",
    "tr": "Beş",
    "vi": "năm",
}
RETENTION_MEANING_FIXTURES = {
    "am": ("ዝግጅትዎን ማተም አልቻለም", "ቅጽዎና ፎቶዎችዎ እዚሁ አሉ", "እንደገና ይሞክሩ"),
    "ar": (
        "تعذّر نشر فعاليتك",
        "ما زال النموذج والصور محفوظين هنا",
        "المحاولة مجددًا",
    ),
    "bn": ("অনুষ্ঠান প্রকাশ করা যায়নি", "ফর্ম ও ছবিগুলো এখানেই আছে", "আবার চেষ্টা করুন"),
    "my": ("သင့်ပွဲကို မထုတ်ဝေနိုင်ပါ", "သင့်ဖောင်နှင့် ဓာတ်ပုံများ ဒီမှာပဲ ရှိနေသည်", "ထပ်မံကြိုးစားပါ"),
    "zh": ("活动无法发布", "表单和照片仍保留在这里", "请重试"),
    "cs": (
        "Událost se nepodařilo zveřejnit",
        "Formulář i fotografie zde zůstaly",
        "zkuste to prosím znovu",
    ),
    "da": (
        "kunne ikke udgives",
        "formular og dine billeder er stadig her",
        "prøv igen",
    ),
    "nl": (
        "kon niet worden gepubliceerd",
        "formulier en foto's zijn hier nog",
        "probeer het opnieuw",
    ),
    "fi": (
        "Tapahtumaa ei voitu julkaista",
        "Lomake ja kuvat ovat yhä täällä",
        "yritä uudelleen",
    ),
    "fr": (
        "n’avons pas pu publier",
        "formulaire et vos photos sont toujours là",
        "veuillez réessayer",
    ),
    "de": (
        "konnte nicht veröffentlicht werden",
        "Formular und deine Fotos sind noch vorhanden",
        "versuche es erneut",
    ),
    "el": (
        "Δεν ήταν δυνατή η δημοσίευση",
        "Η φόρμα και οι φωτογραφίες σας παραμένουν εδώ",
        "δοκιμάστε ξανά",
    ),
    "gu": ("પ્રકાશિત થઈ શક્યો નથી", "ફોર્મ અને ફોટા અહીં જ છે", "ફરી પ્રયાસ કરો"),
    "ha": (
        "Ba a iya wallafa taronka ba",
        "Fom ɗinka da hotunanka suna nan har yanzu",
        "sake gwadawa",
    ),
    "he": ("לא ניתן לפרסם את האירוע", "הטופס והתמונות עדיין כאן", "לנסות שוב"),
    "hi": (
        "कार्यक्रम प्रकाशित नहीं हो सका",
        "फ़ॉर्म और फ़ोटो अभी भी यहाँ हैं",
        "फिर कोशिश करें",
    ),
    "hu": (
        "Nem sikerült közzétenni az eseményt",
        "Az űrlap és a fényképek továbbra is itt vannak",
        "próbálja újra",
    ),
    "id": (
        "tidak dapat diterbitkan",
        "Formulir dan foto Anda masih tersimpan di sini",
        "coba lagi",
    ),
    "it": (
        "Non è stato possibile pubblicare",
        "Il modulo e le foto sono ancora qui",
        "riprova",
    ),
    "ja": (
        "イベントを公開できませんでした",
        "フォームと写真はここに残っています",
        "もう一度お試しください",
    ),
    "kn": ("ಕಾರ್ಯಕ್ರಮವನ್ನು ಪ್ರಕಟಿಸಲಾಗಲಿಲ್ಲ", "ಫಾರ್ಮ್ ಮತ್ತು ಫೋಟೋಗಳು ಇನ್ನೂ ಇಲ್ಲಿವೆ", "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ"),
    "ko": (
        "이벤트를 게시할 수 없습니다",
        "양식과 사진은 그대로 남아 있습니다",
        "다시 시도해 주세요",
    ),
    "ml": (
        "പരിപാടി പ്രസിദ്ധീകരിക്കാനായില്ല",
        "ഫോമും ഫോട്ടോകളും ഇവിടെ തന്നെയുണ്ട്",
        "വീണ്ടും ശ്രമിക്കുക",
    ),
    "mr": (
        "कार्यक्रम प्रकाशित करता आला नाही",
        "फॉर्म आणि फोटो अजूनही येथे आहेत",
        "पुन्हा प्रयत्न करा",
    ),
    "ne": (
        "कार्यक्रम प्रकाशित गर्न सकिएन",
        "फाराम र तस्बिर यहीँ छन्",
        "फेरि प्रयास गर्नुहोस्",
    ),
    "fa": (
        "رویداد شما منتشر نشد",
        "فرم و عکس‌هایتان همچنان اینجا هستند",
        "دوباره تلاش کنید",
    ),
    "pl": (
        "Nie udało się opublikować wydarzenia",
        "Formularz i zdjęcia nadal tu są",
        "spróbuj ponownie",
    ),
    "pt": (
        "Não foi possível publicar o seu evento",
        "o formulário e as fotografias continuam aqui",
        "tente novamente",
    ),
    "ro": (
        "Evenimentul nu a putut fi publicat",
        "Formularul și fotografiile sunt încă aici",
        "încearcă din nou",
    ),
    "es": (
        "No se pudo publicar tu evento",
        "El formulario y las fotos siguen aquí",
        "inténtalo de nuevo",
    ),
    "sw": (
        "Tukio lako halikuweza kuchapishwa",
        "Fomu na picha zako bado zipo hapa",
        "jaribu tena",
    ),
    "sv": (
        "gick inte att publicera evenemanget",
        "Formuläret och fotona finns kvar här",
        "försök igen",
    ),
    "ta": (
        "உங்கள் நிகழ்வை வெளியிட முடியவில்லை",
        "படிவமும் புகைப்படங்களும் இங்கேயே உள்ளன",
        "மீண்டும் முயற்சிக்கவும்",
    ),
    "te": (
        "మీ కార్యక్రమాన్ని ప్రచురించలేకపోయాం",
        "మీ ఫారమ్ మరియు ఫోటోలు ఇక్కడే ఉన్నాయి",
        "మళ్లీ ప్రయత్నించండి",
    ),
    "th": ("เผยแพร่กิจกรรมของคุณไม่ได้", "แบบฟอร์มและรูปภาพยังอยู่ที่นี่", "โปรดลองอีกครั้ง"),
    "tr": (
        "Etkinliğiniz yayımlanamadı",
        "Formunuz ve fotoğraflarınız hâlâ burada",
        "yeniden deneyin",
    ),
    "vi": (
        "Không thể đăng sự kiện",
        "Biểu mẫu và ảnh của bạn vẫn còn ở đây",
        "vui lòng thử lại",
    ),
}


class EventsValidationTranslationTests:
    def test_exact_source_and_locale_coverage_is_merged(self):
        self.assertEqual(len(EVENT_VALIDATION_KEYS), 25)
        self.assertEqual(len(set(EVENT_VALIDATION_KEYS)), 25)
        self.assertEqual(
            EVENT_VALIDATION_LOCALES,
            OFFERED_NON_ENGLISH | {"ha"},
        )
        self.assertEqual(
            EVENT_VALIDATION_LOCALES,
            EXPECTED_EVENT_VALIDATION_LOCALES,
        )
        self.assertEqual(
            set(EVENT_VALIDATION_TRANSLATIONS),
            OFFERED_NON_ENGLISH | {"ha"},
        )
        for locale, entries in EVENT_VALIDATION_TRANSLATIONS.items():
            with self.subTest(locale=locale):
                self.assertEqual(set(entries), set(EVENT_VALIDATION_KEYS))
                self.assertEqual(
                    {key: entries[key] for key in EVENT_VALIDATION_KEYS},
                    {
                        key: EVENT_TRANSLATIONS[locale][key]
                        for key in EVENT_VALIDATION_KEYS
                    },
                )
                for source, translated in entries.items():
                    self.assertTrue(translated.strip(), source)
                    if (locale, source) not in VALID_IDENTICAL_TRANSLATIONS:
                        self.assertNotEqual(translated, source, source)
                    self.assertNotIn("TODO", translated)
                    self.assertNotIn("TRANSLATE_ME", translated)
                    self.assertFalse(
                        translated.startswith((f"[{locale}]", f"{locale}:"))
                    )

    def test_named_limit_slot_is_preserved_exactly(self):
        formatter = Formatter()
        parameterized = (
            "Event titles can be at most {limit} characters.",
            "The details are longer than {limit} words.",
        )
        for locale, entries in EVENT_VALIDATION_TRANSLATIONS.items():
            for source in parameterized:
                source_slots = [
                    field
                    for _literal, field, _spec, _conversion in formatter.parse(
                        source
                    )
                    if field
                ]
                translated_slots = [
                    field
                    for _literal, field, _spec, _conversion in formatter.parse(
                        entries[source]
                    )
                    if field
                ]
                self.assertEqual(
                    translated_slots,
                    source_slots,
                    (locale, source, entries[source]),
                )

    def test_photo_and_publication_constraints_remain_explicit(self):
        photo_sources = (
            EVENT_VALIDATION_KEYS[0],
            EVENT_VALIDATION_KEYS[2],
            EVENT_VALIDATION_KEYS[3],
        )
        retention = EVENT_VALIDATION_KEYS[21]
        expected_size_unit = {"fr": "Mo", "fi": "Mt"}
        for locale, entries in EVENT_VALIDATION_TRANSLATIONS.items():
            with self.subTest(locale=locale):
                for source in photo_sources:
                    value = entries[source]
                    self.assertTrue(
                        all(name in value for name in ("JPEG", "PNG", "WebP")),
                        (locale, source, value),
                    )
                    digits = "".join(
                        str(unicodedata.digit(char))
                        for char in value
                        if char.isdecimal()
                    )
                    self.assertIn("3", digits, (locale, source, value))
                    self.assertIn(
                        expected_size_unit.get(locale, "MB"),
                        value,
                        (locale, source, value),
                    )
                retain_text = entries[retention]
                for phrase in RETENTION_MEANING_FIXTURES[locale]:
                    self.assertIn(phrase, retain_text, (locale, retain_text))
                self.assertNotEqual(retain_text, entries["Error"])
                self.assertNotEqual(
                    retain_text, entries["Choose an event category."]
                )
                self.assertNotEqual(
                    entries["Choose an event category."], entries["Error"]
                )

    def test_numeric_limits_and_representative_full_phrases(self):
        five_photo_source = (
            "Attach no more than five photos. Remove one before adding more."
        )
        numeric_sources = {
            "Reward and details must fit within 1,000 characters.": {1000},
            "Number of helpers must be a whole number between 1 and 100.": {
                1,
                100,
            },
        }
        self.assertEqual(
            set(FIVE_PHOTO_WORDS), set(EVENT_VALIDATION_TRANSLATIONS)
        )
        self.assertEqual(
            set(RETENTION_MEANING_FIXTURES), set(EVENT_VALIDATION_TRANSLATIONS)
        )
        for locale, entries in EVENT_VALIDATION_TRANSLATIONS.items():
            self.assertIn(
                FIVE_PHOTO_WORDS[locale],
                entries[five_photo_source],
                (locale, entries[five_photo_source]),
            )
            for source, required in numeric_sources.items():
                number_runs = re.findall(
                    r"\d(?:[\d\s,٬،٫.．\u202f\u00a0]*\d)?",
                    entries[source],
                )
                normalized = {
                    int(
                        "".join(
                            str(unicodedata.digit(char))
                            for char in match
                            if char.isdecimal()
                        )
                    )
                    for match in number_runs
                    if any(char.isdecimal() for char in match)
                }
                self.assertTrue(
                    required <= normalized,
                    (locale, source, entries[source], normalized),
                )
        self.assertEqual(
            EVENT_VALIDATION_TRANSLATIONS["es"][
                "We couldn't publish your event. Your form and photos are still here — please try again."
            ],
            "No se pudo publicar tu evento. El formulario y las fotos siguen aquí — inténtalo de nuevo.",
        )
        self.assertEqual(
            EVENT_VALIDATION_TRANSLATIONS["fr"][
                "Choose a future start within the next two calendar years."
            ],
            "Choisissez un début futur dans les deux prochaines années civiles.",
        )
        self.assertEqual(
            EVENT_VALIDATION_TRANSLATIONS["zh"][
                "Number of helpers must be a whole number between 1 and 100."
            ],
            "帮手人数必须是 1 到 100 之间的整数。",
        )

    def test_other_shared_catalog_labels_are_not_replaced(self):
        for locale, entries in EVENT_VALIDATION_TRANSLATIONS.items():
            self.assertNotIn("Money", entries)
            self.assertNotIn("Other", entries)
            self.assertNotIn("Guided tour", entries)
            self.assertIn("Describe your Other reward.", entries)
            self.assertTrue(EVENT_TRANSLATIONS[locale]["Money"])
            self.assertTrue(EVENT_TRANSLATIONS[locale]["Other"])
            self.assertTrue(EVENT_TRANSLATIONS[locale]["Guided tour"])


if __name__ == "__main__":
    unittest.main()
