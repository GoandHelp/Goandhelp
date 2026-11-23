import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import unittest

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
from app import policy_catalog_agreement_spanish as agreement_data
from app import policy_catalog_howto_spanish as howto_data
from app import policy_catalog_privacy_spanish as privacy_data
from app.policy_catalog_agreement_spanish import AGREEMENT_SPANISH_ROWS
from app.policy_catalog_howto_spanish import HOWTO_SPANISH_ROWS
from app.policy_catalog_privacy_spanish import PRIVACY_SPANISH_ROWS

BATCH = (
    ("howto", howto_data, "HOWTO_SPANISH_ROWS", HOWTO_SPANISH_ROWS, 85),
    ("privacy", privacy_data, "PRIVACY_SPANISH_ROWS", PRIVACY_SPANISH_ROWS, 41),
    (
        "agreement",
        agreement_data,
        "AGREEMENT_SPANISH_ROWS",
        AGREEMENT_SPANISH_ROWS,
        51,
    ),
)
NAMES = (
    "Go and Help",
    "Stripe",
    "Resend",
    "OpenFreeMap",
    "SHA-256",
    "https://",
)


def entries(document: str, rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return dict(zip(DOCUMENT_SOURCE_KEYS[document], rows["es"], strict=True))


def by_prefix(values: dict[str, str], prefix: str) -> str:
    matches = [
        value for source, value in values.items() if source.startswith(prefix)
    ]
    assert len(matches) == 1, prefix
    return matches[0]


class SpanishPolicyTranslationTests(unittest.TestCase):
    def test_exact_literal_rows_validate_as_native_whole_fields(self):
        total = 0
        for document, module, name, rows, count in BATCH:
            self.assertEqual(set(rows), {"es"})
            self.assertIsInstance(rows["es"], tuple)
            self.assertEqual(len(rows["es"]), count)
            self.assertEqual(len(DOCUMENT_SOURCE_KEYS[document]), count)
            tree = ast.parse(
                Path(inspect.getfile(module)).read_text(encoding="utf-8")
            )
            assignments = [
                node for node in tree.body if isinstance(node, ast.AnnAssign)
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
                "es"
            ]
            for source, value in entries(document, rows).items():
                with self.subTest(document=document, source=source[:40]):
                    self.assertTrue(value.strip())
                    self.assertNotEqual(value, source)
                    self.assertNotIn(source, value)
                    self.assertEqual(placeholders(source), placeholders(value))
                    self.assertEqual(validated[source], value)
                    self.assertNotRegex(value, r"\b(?:[Uu]sted|[Uu]stedes)\b")
                    for proper in NAMES:
                        if proper in source:
                            self.assertIn(proper, value)
                    for number in re.findall(r"\d+(?:[.,]\d+)?", source):
                        self.assertIn(number, value)
                    english_words = source.split()
                    if len(english_words) >= 35:
                        self.assertGreaterEqual(
                            len(value.split()), len(english_words) * 0.8
                        )
                        words = re.findall(r"[A-Za-z]+", source)
                        for index in range(len(words) - 5):
                            self.assertNotIn(
                                " ".join(words[index : index + 6]), value
                            )
            total += len(rows["es"])
        self.assertEqual(total, 177)

    def test_all_spanish_sources_authored_and_effective(self):
        sources = set(SOURCE_KEYS)
        authored = POLICY_CATALOGS["es"]
        effective = catalog("es")
        self.assertEqual(len(sources & set(authored)), 182)
        self.assertEqual(missing_policy_sources(authored, "es"), ())
        self.assertEqual(missing_policy_sources(effective, "es"), ())
        for source in SOURCE_KEYS:
            self.assertNotEqual(effective[source], source)
            self.assertEqual(translate("es", source), effective[source])
            self.assertEqual(translate("en", source), source)
        credits = dict(
            zip(
                DOCUMENT_SOURCE_KEYS["credits"], CREDITS_ROWS["es"], strict=True
            )
        )
        for source, original in credits.items():
            self.assertEqual(authored[source], original)
            self.assertEqual(effective[source], original)
        date = POLICY_DOCUMENTS["howto"]["updated"]
        for _, _, _, rows, _ in BATCH:
            self.assertEqual(entries_for_date(rows), credits[date])
        batch_sources = set()
        for document, _, _, rows, _ in BATCH:
            batch_sources |= set(DOCUMENT_SOURCE_KEYS[document])
            for source, value in entries(document, rows).items():
                self.assertEqual(authored[source], value)
        self.assertEqual(len(batch_sources - set(credits)), 174)
        gaps = {
            locale: len(missing_policy_sources(catalog(locale), locale))
            for locale in POLICY_LOCALES
        }
        authored_total = sum(
            len(sources & set(POLICY_CATALOGS[locale]))
            for locale in POLICY_LOCALES
        )
        effective_total = sum(len(SOURCE_KEYS) - gap for gap in gaps.values())
        self.assertGreaterEqual(authored_total, 1174)
        self.assertGreaterEqual(effective_total, 1339)
        self.assertEqual(effective_total + sum(gaps.values()), 38 * 182)
        for locale in ("fr", "de", "es", "ru", "ur"):
            self.assertEqual(gaps[locale], 0)

    def test_merged_safety_and_representative_legal_paragraphs(self):
        howto = entries("howto", HOWTO_SPANISH_ROWS)
        privacy = entries("privacy", PRIVACY_SPANISH_ROWS)
        agreement = entries("agreement", AGREEMENT_SPANISH_ROWS)
        safety = [SAFETY_PRECAUTIONS["notice"]]
        for section in SAFETY_PRECAUTIONS["sections"]:
            safety.append(section["heading"])
            safety.extend(section["paragraphs"])
        self.assertEqual(len(safety), 51)
        self.assertTrue(set(safety) <= set(howto))
        fixtures = (
            (
                howto,
                "Go and Help is an introduction tool",
                (
                    "documentos de identidad",
                    "antecedentes penales",
                    "nunca una garantía",
                    "Tu propio criterio",
                ),
            ),
            (
                howto,
                "Set my location offers",
                ("500m", "1km", "ninguna coordenada", "todos los usuarios"),
            ),
            (
                howto,
                "Learn the emergency number",
                ("112", "999", "911", "000", "Unión Europea"),
            ),
            (
                howto,
                "Do not take on work",
                (
                    "adultos vulnerables",
                    "tala de árboles",
                    "no es una cualificación",
                ),
            ),
            (
                howto,
                "Go and Help is used all over",
                ("visado o inmigración", "no la nuestra"),
            ),
            (
                howto,
                "There are two options",
                ("Billete mensual", "Pase anual", "Stripe"),
            ),
            (
                privacy,
                "We never publish your stored point",
                ("500m", "1km", "de inmediato", "sin borrar"),
            ),
            (
                privacy,
                "Help requests work the same way",
                ("0.5–1 km", "nunca se publica"),
            ),
            (
                privacy,
                "Go and Help is for people",
                ("16", "a sabiendas", "menor"),
            ),
            (
                privacy,
                "Depending on where you live",
                ("autoridad local de protección de datos", "procede de ti"),
            ),
            (agreement, "You must be at least 16", ("16", "capacidad legal")),
            (
                agreement,
                "Using Go and Help to offer",
                (
                    "Stripe",
                    "se renueva cada mes",
                    "se renueva cada año",
                    "hasta que la canceles",
                ),
            ),
            (
                agreement,
                "You can cancel at any time",
                (
                    "periodo que ya pagaste",
                    "Salvo que la ley local",
                    "no se reembolsan",
                    "desistimiento",
                ),
            ),
            (
                agreement,
                "To the same extent",
                (
                    "la cantidad mayor",
                    "doce meses",
                    "cincuenta dólares estadounidenses",
                ),
            ),
            (
                agreement,
                "Nothing in this agreement excludes",
                ("negligencia", "fraude", "derechos locales obligatorios"),
            ),
            (
                agreement,
                "You agree to indemnify",
                ("salvo en la medida", "por nuestra parte"),
            ),
            (
                agreement,
                "This agreement is governed",
                ("consumidor", "prevalece la norma obligatoria"),
            ),
        )
        for values, prefix, tokens in fixtures:
            value = by_prefix(values, prefix)
            for token in tokens:
                with self.subTest(prefix=prefix, token=token):
                    self.assertIn(token, value)

    def test_canonical_english_checksum_unchanged(self):
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


def entries_for_date(rows: dict[str, tuple[str, ...]]) -> str:
    date = POLICY_DOCUMENTS["howto"]["updated"]
    for document, _, _, candidate, _ in BATCH:
        if candidate is rows:
            return entries(document, rows)[date]
    raise KeyError(date)


if __name__ == "__main__":
    unittest.main()
