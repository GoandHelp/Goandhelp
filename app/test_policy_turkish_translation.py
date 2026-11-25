import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_turkish as agreement_data
from app import policy_catalog_howto_turkish as howto_data
from app import policy_catalog_privacy_turkish as privacy_data
from app.interface_i18n import catalog
from app.policies import POLICY_DOCUMENTS, SAFETY_PRECAUTIONS
from app.policy_catalog import (
    CREDITS_ROWS,
    DOCUMENT_SOURCE_KEYS,
    POLICY_CATALOGS,
    POLICY_LOCALES,
    SOURCE_KEYS,
    missing_policy_sources,
    placeholders,
    validate_rows,
)
from app.policy_catalog_agreement_turkish import AGREEMENT_TURKISH_ROWS
from app.policy_catalog_howto_turkish import HOWTO_TURKISH_ROWS
from app.policy_catalog_privacy_turkish import PRIVACY_TURKISH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_TURKISH_ROWS", HOWTO_TURKISH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_TURKISH_ROWS", PRIVACY_TURKISH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_TURKISH_ROWS",
        AGREEMENT_TURKISH_ROWS,
        51,
    ),
)
PROPER_NAMES = (
    "Go and Help",
    "Stripe",
    "Resend",
    "OpenFreeMap",
    "OpenStreetMap",
    "MapLibre",
    "Planetiler",
    "Open Database License",
    "ODbL",
    "©",
    "SHA-256",
    "https://",
)
TURKISH_LETTERS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["tr"], strict=True))


def lookup(values: dict[str, str], document: str, prefix: str) -> str:
    matches = [
        values[source]
        for source in DOCUMENT_SOURCE_KEYS[document]
        if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def normalized_numbers(text: str) -> set[str]:
    return {
        number.replace(",", ".")
        for number in re.findall(r"\d+(?:[.,]\d+)?", text)
    }


class TurkishPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_turkish_rows_are_complete_and_native(self):
        total = 0
        all_sources: set[str] = set()
        row_count = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"tr"})
                self.assertIsInstance(rows["tr"], tuple)
                self.assertEqual(len(rows["tr"]), count)
                self.assertEqual(len(DOCUMENT_SOURCE_KEYS[document]), count)
                tree = ast.parse(
                    Path(inspect.getfile(module)).read_text(encoding="utf-8")
                )
                assignments = [
                    node
                    for node in tree.body
                    if isinstance(node, ast.AnnAssign)
                ]
                self.assertEqual(len(assignments), 1)
                self.assertEqual(assignments[0].target.id, name)
                self.assertEqual(ast.literal_eval(assignments[0].value), rows)
                self.assertFalse(
                    any(
                        isinstance(
                            node,
                            (
                                ast.Call,
                                ast.FunctionDef,
                                ast.ClassDef,
                                ast.Import,
                                ast.ImportFrom,
                                ast.For,
                                ast.ListComp,
                                ast.DictComp,
                            ),
                        )
                        for node in ast.walk(tree)
                    )
                )
                validated = validate_rows(DOCUMENT_SOURCE_KEYS[document], rows)[
                    "tr"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                row_count += len(rows["tr"])
                self.assertTrue(TURKISH_LETTERS.search(" ".join(rows["tr"])))
                for source, value in entries.items():
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertEqual(placeholders(source), placeholders(value))
                    self.assertEqual(validated[source], value)
                    for proper in PROPER_NAMES:
                        if proper in source:
                            self.assertIn(proper, value)
                    self.assertTrue(
                        normalized_numbers(source) <= normalized_numbers(value),
                        msg=f"Lost numeric fact: {source[:90]}",
                    )
                    if len(source) >= 280:
                        self.assertGreaterEqual(len(value), len(source) * 0.60)
                        self.assertGreaterEqual(
                            len(value.split()), len(source.split()) * 0.35
                        )
                    self.assertNotIn("This ", value)
                    self.assertNotIn("We do not ", value)
                total += count
        self.assertEqual(total, 177)
        self.assertEqual(row_count, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            mapped("howto", HOWTO_TURKISH_ROWS)["How to use Go and Help"],
            "Go and Help nasıl kullanılır",
        )
        self.assertEqual(
            mapped("privacy", PRIVACY_TURKISH_ROWS)[
                "Privacy and cookies policy"
            ],
            "Gizlilik ve çerez politikası",
        )
        self.assertEqual(
            mapped("agreement", AGREEMENT_TURKISH_ROWS)["User agreement"],
            "Kullanıcı sözleşmesi",
        )
        plan_copy = lookup(
            mapped("howto", HOWTO_TURKISH_ROWS),
            "howto",
            "There are two options",
        )
        self.assertIn("Aylık bilet", plan_copy)
        self.assertIn("Yıllık geçiş", plan_copy)
        for _, _, _, rows, _ in BATCH:
            self.assertEqual(
                rows["tr"].count(
                    "Güncellendi ve 1 Haziran 2024 itibarıyla yürürlükte"
                ),
                1,
            )

    def test_turkish_sources_and_existing_credits_are_complete(self):
        authored = POLICY_CATALOGS["tr"]
        effective = catalog("tr")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "tr"), ())
        self.assertEqual(missing_policy_sources(effective, "tr"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["tr"], strict=True
            )
        )
        frozen_turkish_credits = (
            "Teşekkürler",
            "Her Go and Help haritasını çizen açık haritalar ve açık kaynaklı projeler.",
            "Güncellendi ve 1 Haziran 2024 itibarıyla yürürlükte",
            "Go and Help, dünyanın dört bir yanındaki gönüllülerce oluşturulan açık veriler üzerinde çizilir. Bu teşekkürler, memnuniyetle uyduğumuz lisans koşullarının bir parçasıdır.",
            "Haritalar ve harita verileri",
            "Harita döşemeleri OpenFreeMap tarafından sağlanır; veriler © OpenStreetMap katkıda bulunanları, Open Database License (ODbL) kapsamındadır.",
            "Harita verileri OpenStreetMap tarafından Open Database License (ODbL) kapsamında sunulur.",
            "OpenFreeMap, MapLibre, Planetiler ve OpenMapTiles gibi araçlar da dahil olmak üzere çeşitli harika açık kaynaklı projeler üzerine kuruludur.",
        )
        self.assertEqual(CREDITS_ROWS["tr"], frozen_turkish_credits)
        self.assertEqual(len(credits), 8)
        self.assertEqual(authored["Credits"], "Teşekkürler")
        self.assertEqual(effective["Credits"], "Katkıda bulunanlar")
        effective_credit_overrides = {"Credits": "Katkıda bulunanlar"}
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(
                effective[source], effective_credit_overrides.get(source, value)
            )
        self.assertEqual(authored["Reviews"], "Değerlendirmeler")
        self.assertEqual(effective["Reviews"], "Değerlendirmeler")
        self.assertEqual(authored["Emergencies"], "Acil durumlar")
        self.assertEqual(effective["Emergencies"], "Acil durumlar")
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 3262)
        self.assertGreaterEqual(effective_total, 3367)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["tr"], 0)

    def test_merged_safety_and_canonical_privacy_and_agreement_clauses(self):
        howto = mapped("howto", HOWTO_TURKISH_ROWS)
        privacy = mapped("privacy", PRIVACY_TURKISH_ROWS)
        agreement = mapped("agreement", AGREEMENT_TURKISH_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        checks = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "üç seçenek sunar",
                    "kaydedilmiş koordinatlarınız hesabınızda kalır",
                    "hiçbir koordinat hiçbir yere gönderilmez",
                    "500m ile 1km",
                    "tam konumunuzu gizli tutar",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                (
                    "112",
                    "999",
                    "911",
                    "000",
                    "Avrupa Birliği genelinde",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Kapalı, her hesap için varsayılan ayardır",
                    "hiç kimseye gösterilmez",
                    "haritalarda veya kişi aramasında görünmezsiniz",
                    "hiçbir koordinat iletilmez",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "konumunuzu tarayıcınızdan bir kez okur",
                    "özel olarak saklar",
                    "Arka planda izleme veya cihazınızı sürekli takip etme yoktur",
                    "tarayıcınız izninizi ister",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "Kaydettiğiniz noktayı asla yayımlamayız",
                    "500m ile 1km arasında",
                    "paylaşımı hemen durdurur",
                    "kaydettiğiniz koordinatları silmeden",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "yazdığınız adres hiçbir zaman yayımlanmaz",
                    "yalnızca onayladığınız yardımcıyla paylaşılır",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "en az 16 yaşında olmanız gerekir",
                    "Çocuklardan bilerek bilgi toplamıyoruz",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "Aylık üyelik her ay",
                    "yıllık üyelik ise her yıl",
                    "siz iptal edene kadar otomatik olarak yenilenir",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "istediğiniz zaman iptal edebilirsiniz",
                    "daha önce ödediğiniz dönemin sonuna kadar sürer",
                    "Yerel hukukun aksini gerektirdiği durumlar dışında",
                    "dönemin kalan kısmı için geri ödeme yapılmaz",
                    "kanuni cayma veya iptal hakkı geçerliliğini korur",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "aşağıdaki iki tutarın yüksek olanıyla sınırlıdır",
                    "talep öncesindeki 12 ay içinde bize ödediğiniz üyelik ücretleri",
                    "50 ABD doları",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "hiçbir hüküm",
                    "hukukun dışlanmasına veya sınırlandırılmasına izin vermediği sorumluluğu",
                    "ihmalden kaynaklanan ölüm veya bedensel yaralanma",
                    "dolandırıcılık ya da hileli beyan",
                    "zorunlu tüketici hakları",
                    "yerel hukuktan doğan zorunlu haklarınız etkilenmez",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "tüketiciyseniz",
                    "zorunlu tüketici hukuku korumasını",
                    "yerel mahkemelerinizde dava açma hakkınızı",
                    "zorunlu kural uygulanır",
                ),
            ),
        )
        for values, document, prefix, tokens in checks:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(prefix=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertGreater(len(maximum.split()), 30)
        self.assertIn("12 ay", maximum)
        self.assertIn("50 ABD doları", maximum)

    def test_canonical_english_source_checksum_is_unchanged(self):
        frozen = json.dumps(
            POLICY_DOCUMENTS,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        self.assertEqual(
            hashlib.sha256(frozen).hexdigest(),
            "404ee59a08a5b8fc3f5238768659a8df32b7ff7eda9279353cb86110ff575f3d",
        )
        self.assertEqual(len(SOURCE_KEYS), 182)
