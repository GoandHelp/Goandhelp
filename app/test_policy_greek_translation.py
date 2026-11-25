import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

from app import policy_catalog_agreement_greek as agreement_data
from app import policy_catalog_howto_greek as howto_data
from app import policy_catalog_privacy_greek as privacy_data
from app.interface_i18n import catalog, translate
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
from app.policy_catalog_agreement_greek import AGREEMENT_GREEK_ROWS
from app.policy_catalog_howto_greek import HOWTO_GREEK_ROWS
from app.policy_catalog_privacy_greek import PRIVACY_GREEK_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_GREEK_ROWS", HOWTO_GREEK_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_GREEK_ROWS", PRIVACY_GREEK_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_GREEK_ROWS",
        AGREEMENT_GREEK_ROWS,
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
GREEK_LETTERS = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")


def mapped(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["el"], strict=True))


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


class GreekPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_greek_rows_are_complete_and_native(self):
        total = 0
        all_sources: set[str] = set()
        row_count = 0
        for document, module, name, rows, count in BATCH:
            with self.subTest(document=document):
                self.assertEqual(set(rows), {"el"})
                self.assertIsInstance(rows["el"], tuple)
                self.assertEqual(len(rows["el"]), count)
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
                    "el"
                ]
                entries = mapped(document, rows)
                all_sources.update(entries)
                row_count += len(rows["el"])
                for source, value in entries.items():
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertIsNotNone(GREEK_LETTERS.search(value))
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
                            len(value.split()), len(source.split()) * 0.50
                        )
                    self.assertNotIn("This ", value)
                    self.assertNotIn("We do not ", value)
                total += count
        self.assertEqual(total, 177)
        self.assertEqual(row_count, 177)
        self.assertEqual(len(all_sources), 175)
        credits_date = POLICY_DOCUMENTS["credits"]["updated"]
        self.assertEqual(len(all_sources - {credits_date}), 174)
        howto = mapped("howto", HOWTO_GREEK_ROWS)
        self.assertEqual(
            howto["How to use Go and Help"],
            "Πώς να χρησιμοποιήσετε το Go and Help",
        )
        self.assertEqual(
            mapped("privacy", PRIVACY_GREEK_ROWS)["Privacy and cookies policy"],
            "Πολιτική απορρήτου και cookies",
        )
        self.assertEqual(
            mapped("agreement", AGREEMENT_GREEK_ROWS)["User agreement"],
            "Συμφωνία χρήστη",
        )
        plans = lookup(
            howto,
            "howto",
            "There are two options",
        )
        self.assertIn("Μηνιαίο εισιτήριο", plans)
        self.assertIn("Ετήσιο πάσο", plans)

    def test_all_greek_sources_and_credits_are_native_and_complete(self):
        authored = POLICY_CATALOGS["el"]
        effective = catalog("el")
        self.assertEqual(len(set(SOURCE_KEYS) & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "el"), ())
        self.assertEqual(missing_policy_sources(effective, "el"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(authored[source], source)
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("el", source), effective[source])
            self.assertEqual(translate("en", source), source)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["el"], strict=True
            )
        )
        self.assertEqual(len(credits), 8)
        self.assertEqual(authored["Credits"], "Ευχαριστίες")
        self.assertEqual(effective["Credits"], "Ευχαριστίες")
        for source, value in credits.items():
            self.assertEqual(authored[source], value)
            self.assertEqual(effective[source], value)
        expected_effective_precedence = {
            # Preserve the established shared-catalog heading synonym.
            "Emergencies": "Επείγοντα",
        }
        for document, _, _, rows, expected in BATCH:
            self.assertEqual(len(rows["el"]), expected)
            for source, value in mapped(document, rows).items():
                self.assertEqual(authored[source], value)
                self.assertEqual(
                    effective[source],
                    expected_effective_precedence.get(source, value),
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
        self.assertGreaterEqual(authored_total, 3088)
        self.assertGreaterEqual(effective_total, 3198)
        self.assertEqual(effective_total + sum(gaps.values()), 6916)
        self.assertEqual(gaps["el"], 0)

    def test_merged_safety_and_source_bound_privacy_agreement_clauses(self):
        howto = mapped("howto", HOWTO_GREEK_ROWS)
        privacy = mapped("privacy", PRIVACY_GREEK_ROWS)
        agreement = mapped("agreement", AGREEMENT_GREEK_ROWS)
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
                    "τρεις επιλογές και τίποτα ενδιάμεσο",
                    "οι αποθηκευμένες συντεταγμένες σας παραμένουν στον λογαριασμό σας",
                    "καμία συντεταγμένη δεν μεταδίδεται πουθενά",
                    "500m έως 1km",
                    "το ακριβές σημείο σας",
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
                    "Ευρωπαϊκή Ένωση",
                ),
            ),
            (
                privacy,
                "privacy",
                "Off is the default for every account",
                (
                    "Η επιλογή «Ανενεργή» είναι η προεπιλογή",
                    "δεν εμφανίζονται σε κανέναν",
                    "δεν εμφανίζεστε σε χάρτες ή στην αναζήτηση ατόμων",
                    "καμία συντεταγμένη δεν μεταδίδεται",
                ),
            ),
            (
                privacy,
                "privacy",
                "Approximate reads your position from your browser once",
                (
                    "αποθηκεύει ιδιωτικά αυτό το σημείο",
                    "Δεν υπάρχει παρακολούθηση στο παρασκήνιο",
                    "θα ζητήσει την άδειά σας",
                ),
            ),
            (
                privacy,
                "privacy",
                "We never publish your stored point",
                (
                    "Δεν δημοσιεύουμε ποτέ το αποθηκευμένο σημείο σας",
                    "500m έως 1km",
                    "η κοινοποίηση σταματά αμέσως",
                    "χωρίς να διαγραφούν οι συντεταγμένες που αποθηκεύσατε",
                ),
            ),
            (
                privacy,
                "privacy",
                "Help requests work the same way",
                (
                    "0.5–1 km",
                    "η διεύθυνση που πληκτρολογείτε δεν δημοσιεύεται ποτέ",
                    "μόνο στον βοηθό που επιβεβαιώνετε",
                ),
            ),
            (
                privacy,
                "privacy",
                "Go and Help is for people aged 16 and over",
                (
                    "τουλάχιστον 16 ετών",
                    "Δεν συλλέγουμε εν γνώσει μας πληροφορίες για παιδιά",
                ),
            ),
            (
                agreement,
                "agreement",
                "Using Go and Help to offer and give help is free",
                (
                    "Stripe",
                    "Η μηνιαία συνδρομή ανανεώνεται κάθε μήνα",
                    "η ετήσια συνδρομή ανανεώνεται κάθε χρόνο",
                    "μέχρι να την ακυρώσετε",
                ),
            ),
            (
                agreement,
                "agreement",
                "You can cancel at any time from the billing portal",
                (
                    "έως το τέλος της περιόδου που έχετε ήδη πληρώσει",
                    "Εκτός αν η τοπική νομοθεσία ορίζει διαφορετικά",
                    "δεν επιστρέφονται χρήματα για τμήματα περιόδου",
                    "Κάθε νόμιμο δικαίωμα υπαναχώρησης ή ακύρωσης",
                ),
            ),
            (
                agreement,
                "agreement",
                "To the same extent",
                (
                    "στο μεγαλύτερο από τα δύο ποσά",
                    "κατά τους 12 μήνες πριν από την αξίωση",
                    "50 δολάρια ΗΠΑ",
                ),
            ),
            (
                agreement,
                "agreement",
                "Nothing in this agreement excludes or limits liability",
                (
                    "Τίποτα σε αυτή τη συμφωνία δεν αποκλείει ούτε περιορίζει ευθύνη",
                    "που ο νόμος δεν επιτρέπει να αποκλειστεί ή να περιοριστεί",
                    "για θάνατο ή σωματική βλάβη που προκαλείται από αμέλεια",
                    "για απάτη ή δόλια παραπλάνηση",
                    "των υποχρεωτικών δικαιωμάτων των καταναλωτών",
                    "τα υποχρεωτικά τοπικά δικαιώματά σας δεν επηρεάζονται",
                ),
            ),
            (
                agreement,
                "agreement",
                "This agreement is governed by the law stated",
                (
                    "αν είστε καταναλωτής",
                    "αναγκαστική νομοθεσία περί καταναλωτών",
                    "τοπικά δικαστήρια",
                    "υπερισχύει ο αναγκαστικός κανόνας",
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
        self.assertIn("το μεγαλύτερο από τα δύο ποσά", maximum)
        self.assertIn("12 μήνες", maximum)
        self.assertIn("50 δολάρια ΗΠΑ", maximum)

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


if __name__ == "__main__":
    unittest.main()
