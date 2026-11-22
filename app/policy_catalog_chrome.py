"""Offline reader chrome for Russian and Urdu; other locales already have it."""

POLICY_CHROME_KEYS: tuple[str, ...] = (
    "Back",
    "Back to your profile",
    "Section {count}",
    "This screen is part of the Go and Help app. It is written for adults everywhere and is not legal advice for any particular country.",
    "How to use Go and Help",
    "Privacy and cookies policy",
    "User agreement",
)
POLICY_CHROME_ROWS: dict[str, tuple[str, ...]] = {
    "ru": (
        "Назад",
        "Вернуться в свой профиль",
        "Раздел {count}",
        "Этот экран — часть приложения Go and Help. Он написан для взрослых во всём мире и не является юридической консультацией применительно к какой-либо конкретной стране.",
        "Как пользоваться Go and Help",
        "Политика конфиденциальности и файлов cookie",
        "Пользовательское соглашение",
    ),
    "ur": (
        "واپس",
        "اپنے پروفائل پر واپس جائیں",
        "حصہ {count}",
        "یہ اسکرین Go and Help ایپ کا حصہ ہے۔ یہ دنیا بھر کے بالغ افراد کے لیے لکھی گئی ہے اور کسی مخصوص ملک کے لیے قانونی مشورہ نہیں ہے۔",
        "Go and Help استعمال کرنے کا طریقہ",
        "رازداری اور کوکیز کی پالیسی",
        "صارف کا معاہدہ",
    ),
}
