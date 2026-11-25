import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_indonesian as agreement_data
from app import policy_catalog_howto_indonesian as howto_data
from app import policy_catalog_privacy_indonesian as privacy_data
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
from app.policy_catalog_agreement_indonesian import AGREEMENT_INDONESIAN_ROWS
from app.policy_catalog_howto_indonesian import HOWTO_INDONESIAN_ROWS
from app.policy_catalog_privacy_indonesian import PRIVACY_INDONESIAN_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_INDONESIAN_ROWS", HOWTO_INDONESIAN_ROWS, 85),
    (
        "privacy",
        privacy_data,
        "PRIVACY_INDONESIAN_ROWS",
        PRIVACY_INDONESIAN_ROWS,
        41,
    ),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_INDONESIAN_ROWS",
        AGREEMENT_INDONESIAN_ROWS,
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
NUMBERS = re.compile(r"\d+(?:[.,]\d+)?")


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["id"], strict=True))


def lookup(values: dict[str, str], document: str, prefix: str) -> str:
    matches = [
        values[source]
        for source in DOCUMENT_SOURCE_KEYS[document]
        if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def normalized_numbers(text: str) -> set[str]:
    return {number.replace(",", ".") for number in NUMBERS.findall(text)}


class IndonesianPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_indonesian_rows_are_complete_and_native(self):
        total_rows = 0
        all_sources: set[str] = set()
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"id"})
                self.assertIsInstance(rows["id"], tuple)
                self.assertEqual(len(rows["id"]), count)
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
                    "id"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                total_rows += len(rows["id"])
                for source, value in entries.items():
                    with self.subTest(source=source[:75]):
                        self.assertTrue(value.strip())
                        self.assertNotEqual(value, source)
                        self.assertEqual(
                            placeholders(source), placeholders(value)
                        )
                        self.assertEqual(validated[source], value)
                        for proper in PROPER_NAMES:
                            if proper in source:
                                self.assertIn(proper, value)
                        self.assertTrue(
                            normalized_numbers(source)
                            <= normalized_numbers(value),
                            msg=f"Lost numeric fact: {source[:100]}",
                        )
                        if len(source) >= 280:
                            self.assertGreaterEqual(
                                len(value), len(source) * 0.60
                            )
                            self.assertGreaterEqual(
                                len(value.split()), len(source.split()) * 0.50
                            )
                        self.assertNotIn("This ", value)
                        self.assertNotIn("We do not ", value)
                        self.assertNotIn("You can ", value)
        self.assertEqual(total_rows, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(
            sum(
                row["id"].count("Diperbarui dan berlaku sejak 1 Juni 2024")
                for *_, row, _ in BATCH
            ),
            3,
        )
        self.assertEqual(len(all_sources - {credits_date}), 174)
        self.assertEqual(
            mapped("howto", HOWTO_INDONESIAN_ROWS)["How to use Go and Help"],
            "Cara menggunakan Go and Help",
        )
        self.assertEqual(
            mapped("privacy", PRIVACY_INDONESIAN_ROWS)[
                "Privacy and cookies policy"
            ],
            "Kebijakan privasi dan cookie",
        )
        self.assertEqual(
            mapped("agreement", AGREEMENT_INDONESIAN_ROWS)["User agreement"],
            "Perjanjian pengguna",
        )
        howto = mapped("howto", HOWTO_INDONESIAN_ROWS)
        self.assertEqual(howto["Reviews"], "Ulasan")
        self.assertEqual(howto["Emergencies"], "Keadaan darurat")
        membership = lookup(howto, "howto", "There are two options")
        self.assertIn("Tiket bulanan", membership)
        self.assertIn("Pas tahunan", membership)

    def test_indonesian_sources_credits_and_global_coverage(self):
        authored = POLICY_CATALOGS["id"]
        effective = catalog("id")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "id"), ())
        self.assertEqual(missing_policy_sources(effective, "id"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
        frozen_credits = (
            "Penghargaan",
            "Peta terbuka dan proyek sumber terbuka yang menggambar setiap peta Go and Help.",
            "Diperbarui dan berlaku sejak 1 Juni 2024",
            "Go and Help digambar di atas data terbuka yang dibuat oleh sukarelawan dari seluruh dunia. Penghargaan ini merupakan bagian dari ketentuan lisensi yang dengan senang hati kami patuhi.",
            "Peta dan data peta",
            "Ubin peta oleh OpenFreeMap, data © kontributor OpenStreetMap, di bawah Open Database License (ODbL).",
            "Data peta disediakan oleh OpenStreetMap di bawah Open Database License (ODbL).",
            "OpenFreeMap dibangun di atas beberapa proyek sumber terbuka yang luar biasa, termasuk alat seperti MapLibre, Planetiler, dan OpenMapTiles.",
        )
        self.assertEqual(CREDITS_ROWS["id"], frozen_credits)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["id"], strict=True
            )
        )
        self.assertEqual(authored["Credits"], "Penghargaan")
        self.assertEqual(effective["Credits"], "Penghargaan untuk kontributor")
        effective_credit_overrides = {
            "Credits": "Penghargaan untuk kontributor"
        }
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(
                effective[source], effective_credit_overrides.get(source, value)
            )
        authored_total = sum(
            len(set(SOURCE_KEYS) & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 3436)
        self.assertGreaterEqual(effective_total, 3536)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["id"], 0)

    def test_merged_safety_and_canonical_full_paragraph_safeguards(self):
        howto = mapped("howto", HOWTO_INDONESIAN_ROWS)
        privacy = mapped("privacy", PRIVACY_INDONESIAN_ROWS)
        agreement = mapped("agreement", AGREEMENT_INDONESIAN_ROWS)
        safety_fields = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety_fields.append(section["heading"])
            safety_fields.extend(section["paragraphs"])
        self.assertEqual(len(safety_fields), 51)
        self.assertTrue(set(safety_fields) <= set(howto))
        clauses = (
            (
                howto,
                "howto",
                "Set my location offers three positions",
                (
                    "tiga pilihan",
                    "koordinat yang tersimpan tetap berada di akun Anda",
                    "tidak ada koordinat yang dikirim ke mana pun",
                    "antara 500m dan 1km",
                    "menjaga titik persis Anda tetap pribadi",
                ),
            ),
            (
                howto,
                "howto",
                "Learn the emergency number where you are",
                ("112", "999", "911", "000", "di seluruh Uni Eropa"),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Nonaktif adalah pengaturan bawaan setiap akun",
                    "tidak ditampilkan kepada siapa pun",
                    "Anda tidak muncul di peta atau pencarian orang",
                    "tidak ada koordinat yang dikirimkan",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "membaca lokasi Anda dari peramban satu kali",
                    "menyimpan titik tersebut secara pribadi",
                    "Tidak ada pelacakan di latar belakang",
                    "Peramban akan meminta izin",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "Kami tidak pernah menerbitkan titik tersimpan Anda",
                    "antara 500m dan 1km",
                    "langsung menghentikan pembagian",
                    "tanpa menghapus koordinat yang Anda simpan",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "alamat yang Anda ketik tidak pernah diterbitkan",
                    "hanya dibagikan kepada penolong yang Anda konfirmasi",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "Go and Help ditujukan bagi orang berusia 16 tahun ke atas",
                    "setidaknya 16 tahun",
                    "tidak dengan sengaja mengumpulkan informasi dari anak-anak",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "diperpanjang otomatis setiap bulan",
                    "diperpanjang otomatis setiap tahun",
                    "sampai Anda membatalkannya",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "Anda dapat membatalkan kapan saja",
                    "sampai akhir periode yang telah Anda bayar",
                    "Kecuali jika hukum setempat mewajibkan sebaliknya",
                    "sisa periode tidak dikembalikan dananya",
                    "Hak penarikan atau pembatalan menurut undang-undang",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "jumlah yang lebih besar dari dua nilai berikut",
                    "selama 12 bulan sebelum tuntutan",
                    "50 dolar Amerika Serikat",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "Tidak ada ketentuan dalam perjanjian ini",
                    "tidak boleh dikecualikan atau dibatasi menurut hukum",
                    "kematian atau cedera tubuh akibat kelalaian",
                    "penipuan atau pernyataan palsu yang disengaja",
                    "hak konsumen yang wajib dilindungi",
                    "hak wajib Anda menurut hukum setempat tidak terpengaruh",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "jika Anda adalah konsumen",
                    "perlindungan hukum konsumen wajib",
                    "hak Anda untuk mengajukan tuntutan di pengadilan setempat",
                    "aturan wajib yang berlaku",
                ),
            ),
        )
        for values, document, prefix, tokens in clauses:
            value = lookup(values, document, prefix)
            for token in tokens:
                with self.subTest(source=prefix, token=token):
                    self.assertIn(token, value)
        maximum = lookup(agreement, "agreement", "To the same extent")
        self.assertGreaterEqual(len(maximum.split()), 30)
        self.assertIn("12 bulan", maximum)
        self.assertIn("50 dolar Amerika Serikat", maximum)

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
