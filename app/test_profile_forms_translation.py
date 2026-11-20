import ast
import json
import re
import shutil
import subprocess
import unittest
import unicodedata
from collections import Counter
from pathlib import Path
from string import Formatter

import reflex as rx

from app.components.profile_form_feedback import (
    localized_profile_form_message,
    localized_profile_skills_summary,
)
from app.components.profile_tabs import (
    category_chip,
    details_tab,
    skills_knowledge_section,
)
from app.interface_catalog_profile_forms import (
    PROFILE_FORM_CATALOGS,
    PROFILE_FORM_KEYS,
    PROFILE_FORM_ROWS,
    PROFILE_FORM_SOURCE_COINCIDENCES,
)
from app.interface_i18n import CATALOGS, COMPLETE_KEYS, catalog, translate, ui
from app.models import CATEGORY_LABELS, LANGUAGE_OPTIONS, TASK_CATEGORIES
from app.states.auth_state import AuthState
from app.states.profile_state import ProfileState

EXPECTED_KEYS = (
    "Public handle",
    "unique, lowercase",
    "account country",
    "Biography",
    "why you help, why you need help",
    "I.e. I'm a Photographer travelling Asia, happy to help others in exchange for a accommodation...",
    "comma separated",
    "English, Portuguese, Spanish",
    "Handle",
    "Phone",
    "Email",
    "Bio",
    "Languages",
    "Password",
    "Select what you can help with",
    "Other Skills",
    "Anything the categories miss",
    "Plumber, Electrician, Hairdresser, Dentist, Tailor...",
    "Save skills and knowledge",
    "Choose the categories you can help with, and add anything else you know.",
    "No categories yet",
    "{count} other skills listed",
    "1 other skill listed",
    "Choose at least one category, or describe your other skills and knowledge.",
    "Skills and knowledge saved.",
    "Handles are 3–30 characters, lowercase letters, numbers, dots or underscores.",
    "That biography is a little long — trim it under 2000 characters.",
    "@{handle} is already claimed by another traveller — try a different handle.",
    "@{handle} is already claimed — pick another handle.",
    "We couldn't save your profile. Please try again.",
    "Profile details saved.",
    "Private — only visible to you. Your email cannot be edited here.",
    "Handle, Phone, Email, Bio, Languages, Password",
)


def slots(value: str) -> Counter[str]:
    return Counter(
        field for _, field, _, _ in Formatter().parse(value) if field
    )


def decimal_numbers(value: str) -> list[int]:
    normalized = "".join(
        str(unicodedata.decimal(char)) if char.isdecimal() else char
        for char in value
    )
    return [int(number) for number in re.findall(r"\d+", normalized)]


class ProfileFormsTranslationTests(unittest.TestCase):
    def test_exact_catalog_coverage_templates_and_numeric_rules(self):
        self.assertEqual(PROFILE_FORM_KEYS, EXPECTED_KEYS)
        self.assertEqual(len(set(EXPECTED_KEYS)), 33)
        self.assertTrue(set(EXPECTED_KEYS) <= set(COMPLETE_KEYS))
        offered = {code for code, _ in LANGUAGE_OPTIONS}
        self.assertEqual(len(LANGUAGE_OPTIONS), 37)
        self.assertEqual(len(offered), 37)
        self.assertIn("en", offered)
        non_english = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
        self.assertEqual(set(PROFILE_FORM_ROWS), non_english)
        self.assertEqual(set(PROFILE_FORM_CATALOGS), non_english)
        self.assertNotIn("en", PROFILE_FORM_CATALOGS)
        self.assertNotIn("ha", PROFILE_FORM_CATALOGS)
        for locale, row in PROFILE_FORM_ROWS.items():
            with self.subTest(locale=locale):
                self.assertEqual(len(row), 32)
                self.assertEqual(
                    tuple(PROFILE_FORM_CATALOGS[locale]), EXPECTED_KEYS
                )
                for source, value in PROFILE_FORM_CATALOGS[locale].items():
                    self.assertTrue(value.strip())
                    if value == source:
                        self.assertIn(
                            (locale, source), PROFILE_FORM_SOURCE_COINCIDENCES
                        )
                    else:
                        self.assertNotEqual(value, source)
                    self.assertEqual(slots(value), slots(source))
                    if source in {"Phone", "Email", "Languages", "Password"}:
                        self.assertIn(source, CATALOGS[locale])
                        merged = CATALOGS[locale][source]
                        self.assertIsInstance(merged, str)
                        self.assertTrue(merged.strip())
                        self.assertEqual(slots(merged), slots(source))
                        self.assertEqual(translate(locale, source), merged)
                    else:
                        self.assertEqual(translate(locale, source), value)
                    self.assertEqual(translate("en", source), source)
                    self.assertEqual(translate("unlisted", source), source)
                handle_rule = PROFILE_FORM_CATALOGS[locale][EXPECTED_KEYS[25]]
                bio_rule = PROFILE_FORM_CATALOGS[locale][EXPECTED_KEYS[26]]
                self.assertEqual(decimal_numbers(handle_rule), [3, 30])
                self.assertEqual(decimal_numbers(bio_rule), [2000])
                self.assertTrue(
                    PROFILE_FORM_CATALOGS[locale][EXPECTED_KEYS[22]]
                )

        preserved = {
            ("el", "Email"): "Email",
            ("id", "Email"): "Email",
            ("it", "Email"): "Email",
            ("it", "Languages"): "Lingue",
            ("it", "Password"): "Password",
            ("ja", "Phone"): "電話",
            ("ja", "Email"): "メール",
            ("ko", "Phone"): "전화",
            ("fa", "Password"): "رمز عبور",
            ("pt", "Email"): "Email",
            ("ro", "Email"): "Email",
        }
        for (locale, source), expected in preserved.items():
            with self.subTest(preserved_locale=locale, source=source):
                self.assertEqual(CATALOGS[locale][source], expected)
                self.assertEqual(translate(locale, source), expected)
        corrections = {
            ("it", "Bio"): "Breve biografia",
            ("it", "Languages"): "Lingue",
            ("it", "Password"): "Parola d'accesso",
            ("pt", "Email"): "Correio eletrónico",
            ("pt", "Bio"): "Apresentação",
        }
        for (locale, source), expected in corrections.items():
            with self.subTest(corrected_locale=locale, source=source):
                self.assertEqual(
                    PROFILE_FORM_CATALOGS[locale][source], expected
                )
                self.assertEqual(
                    PROFILE_FORM_ROWS[locale][EXPECTED_KEYS.index(source)],
                    expected,
                )

    def test_source_coincidences_are_exactly_the_four_native_labels(self):
        expected = frozenset(
            {
                ("pl", "Bio"),
                ("ro", "Bio"),
                ("es", "Bio"),
                ("vi", "Email"),
            }
        )
        self.assertIsInstance(PROFILE_FORM_SOURCE_COINCIDENCES, frozenset)
        self.assertEqual(PROFILE_FORM_SOURCE_COINCIDENCES, expected)
        actual = frozenset(
            (locale, source)
            for locale, entries in PROFILE_FORM_CATALOGS.items()
            for source, value in entries.items()
            if value == source
        )
        self.assertEqual(actual, expected)

    def test_actual_startup_guard_rejects_blanks_and_unapproved_english(self):
        path = "app/interface_catalog_profile_forms.py"
        tree = ast.parse(Path(path).read_text())
        guards = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Constant)
                and isinstance(child.value, str)
                and "Missing native profile-form phrase:" in child.value
                for statement in node.body
                for child in ast.walk(statement)
            )
        ]
        self.assertEqual(len(guards), 1)
        guard = compile(
            ast.Module(body=[guards[0]], type_ignores=[]), path, "exec"
        )
        for locale, entries in PROFILE_FORM_CATALOGS.items():
            for source, value in entries.items():
                namespace = {
                    "PROFILE_FORM_SOURCE_COINCIDENCES": PROFILE_FORM_SOURCE_COINCIDENCES,
                    "_locale": locale,
                    "_source": source,
                    "_value": value,
                }
                with self.subTest(locale=locale, source=source):
                    exec(guard, namespace)
                    for blank in ("", " ", "\t\n"):
                        namespace["_value"] = blank
                        with self.assertRaisesRegex(
                            ValueError, "Missing native profile-form phrase:"
                        ):
                            exec(guard, namespace)
                    namespace["_value"] = source
                    if (locale, source) in PROFILE_FORM_SOURCE_COINCIDENCES:
                        exec(guard, namespace)
                    else:
                        with self.assertRaisesRegex(
                            ValueError, "Missing native profile-form phrase:"
                        ):
                            exec(guard, namespace)

    def test_catalog_rows_are_literal_offline_locale_data(self):
        groups = (
            (
                "app/interface_catalog_profile_forms_a.py",
                "PROFILE_FORM_ROWS_A",
                list,
            ),
            (
                "app/interface_catalog_profile_forms_b.py",
                "PROFILE_FORM_ROWS_B",
                list,
            ),
            (
                "app/interface_catalog_profile_forms_c.py",
                "PROFILE_FORM_ROWS_C",
                list,
            ),
            (
                "app/interface_catalog_profile_forms_subtitle.py",
                "PROFILE_FORM_SUBTITLE_ROWS",
                str,
            ),
        )
        for path, name, value_type in groups:
            tree = ast.parse(Path(path).read_text())
            definition = next(
                node
                for node in tree.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == name
            )
            self.assertIsInstance(definition.value, ast.Dict)
            for value in definition.value.values:
                if value_type is list:
                    self.assertIsInstance(value, ast.List)
                    self.assertTrue(
                        all(
                            isinstance(item, ast.Constant)
                            and isinstance(item.value, str)
                            for item in value.elts
                        )
                    )
                else:
                    self.assertIsInstance(value, ast.Constant)
                    self.assertIsInstance(value.value, str)
            roots = {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            for forbidden in (
                "httpx",
                "requests",
                "urllib",
                "openai",
                "subprocess",
            ):
                self.assertNotIn(forbidden, roots)

    def test_full_example_and_amharic_script_are_preserved(self):
        example = EXPECTED_KEYS[5]
        for locale in ("fr", "ar", "am", "ja"):
            translated = PROFILE_FORM_CATALOGS[locale][example]
            with self.subTest(locale=locale):
                self.assertTrue(translated)
                if locale == "am":
                    self.assertTrue(
                        any("\u1200" <= char <= "\u137f" for char in translated)
                    )
                    self.assertFalse(
                        any("\u10a0" <= char <= "\u10ff" for char in translated)
                    )
        self.assertIn(
            "photographe", PROFILE_FORM_CATALOGS["fr"][example].lower()
        )
        self.assertIn("asie", PROFILE_FORM_CATALOGS["fr"][example].lower())
        self.assertIn("写真家", PROFILE_FORM_CATALOGS["ja"][example])
        self.assertIn("アジア", PROFILE_FORM_CATALOGS["ja"][example])
        self.assertIn("宿泊", PROFILE_FORM_CATALOGS["ja"][example])
        self.assertIn("إقامة", PROFILE_FORM_CATALOGS["ar"][example])

    def test_category_taxonomy_and_components_keep_storage_contracts(self):
        self.assertEqual(len(TASK_CATEGORIES), 23)
        self.assertEqual(set(CATEGORY_LABELS), set(TASK_CATEGORIES))
        for locale, _ in LANGUAGE_OPTIONS:
            if locale != "en":
                self.assertTrue(
                    {CATEGORY_LABELS[key] for key in TASK_CATEGORIES}
                    <= set(CATALOGS[locale])
                )
        components = (
            details_tab(),
            skills_knowledge_section(),
            category_chip("translator"),
        )
        self.assertTrue(all(component.render() for component in components))
        details_source = Path("app/components/profile_tabs.py").read_text()
        self.assertIn("default_value=ProfileState.username", details_source)
        self.assertIn("default_value=ProfileState.bio", details_source)
        self.assertIn("default_value=ProfileState.languages", details_source)
        self.assertIn("on_submit=ProfileState.save_details", details_source)
        self.assertIn("on_submit=ProfileState.save_skills", details_source)
        self.assertIn(
            "on_click=lambda: ProfileState.toggle_category(category)",
            details_source,
        )
        self.assertIn("ui(CATEGORY_LABELS.get(category", details_source)
        self.assertIn("ProfileState.skill_list.length()", details_source)
        self.assertIn("tag_chip", details_source)
        profile = ProfileState(_reflex_internal_init=True)
        self.assertEqual(profile.username, "")

    def test_component_feedback_and_database_boundaries_are_display_only(self):
        self.assertTrue(details_tab().render())
        self.assertTrue(skills_knowledge_section().render())
        tree = ast.parse(Path("app/states/profile_state.py").read_text())
        methods = {
            node.name: ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for method in ("save_skills", "save_details"):
            self.assertIn("await asession.commit()", methods[method])
            self.assertIn("translate(language", methods[method])
            self.assertIn("rx.toast", methods[method])
        self.assertIn("USERNAME_PATTERN.match(handle)", methods["save_details"])
        self.assertIn("len(bio) > 2000", methods["save_details"])
        self.assertIn("[:500]", methods["save_skills"])
        self.assertIn("show_phone = False", methods["save_details"])

    def test_actual_compiled_lookups_and_member_value_safety_in_node(self):
        node = shutil.which("node")
        self.assertIsNotNone(node)
        raw_message = rx.Var(_js_expr="messageSource", _var_type=str).to(str)
        text_expression = str(ui(raw_message)).replace(
            str(AuthState.interface_text), "interfaceTextFixture"
        )
        feedback_expression = str(
            localized_profile_form_message(raw_message)
        ).replace(str(AuthState.interface_text), "interfaceTextFixture")
        categories = rx.Var(_js_expr="categorySources", _var_type=list[str]).to(
            list[str]
        )
        count = rx.Var(_js_expr="skillCount", _var_type=int).to(int)
        summary_expression = str(
            localized_profile_skills_summary(categories, count)
        ).replace(str(AuthState.preferred_language), "languageFixture")

        expressions = {
            "lookup": text_expression,
            "feedback": feedback_expression,
            "summary": summary_expression,
        }
        cases: list[dict[str, object]] = []
        catalogs: dict[str, dict[str, str]] = {}
        selected_keys = (
            set(EXPECTED_KEYS)
            | set(CATEGORY_LABELS.values())
            | {"Your session expired — please sign in again."}
        )
        sources = (
            "@maya.lisbon is already claimed by another traveller — try a different handle.",
            "@maya.lisbon is already claimed — pick another handle.",
            "We couldn't save your profile. Please try again.",
            "Your session expired — please sign in again.",
            "A member wrote {keep} — don't translate this.",
        )
        category_sets = (
            ([], 0),
            (["Translator", "First-aid"], 0),
            ([], 1),
            (["Translator"], 4),
        )
        for locale, _ in LANGUAGE_OPTIONS:
            selected_catalog = catalog(locale)
            catalogs[locale] = {
                key: value
                for key, value in selected_catalog.items()
                if key in selected_keys
            }
            self.assertTrue(
                all(
                    isinstance(value, str)
                    for value in catalogs[locale].values()
                )
            )
            for source in EXPECTED_KEYS:
                cases.append(
                    {
                        "locale": locale,
                        "kind": "lookup",
                        "source": source,
                        "categories": [],
                        "count": 0,
                        "expected": translate(locale, source),
                    }
                )
            for source in sources:
                if source.startswith("@maya"):
                    template_key = (
                        "@{handle} is already claimed by another traveller — try a different handle."
                        if "another traveller" in source
                        else "@{handle} is already claimed — pick another handle."
                    )
                    expected = translate(locale, template_key).replace(
                        "{handle}", "maya.lisbon"
                    )
                else:
                    expected = translate(locale, source)
                if source.startswith("A member wrote"):
                    expected = source
                cases.append(
                    {
                        "locale": locale,
                        "kind": "feedback",
                        "source": source,
                        "categories": [],
                        "count": 0,
                        "expected": expected,
                    }
                )
            for selected, amount in category_sets:
                labels = [translate(locale, label) for label in selected]
                if not selected and amount == 0:
                    expected = translate(
                        locale,
                        "Choose the categories you can help with, and add anything else you know.",
                    )
                else:
                    prefix = (
                        ", ".join(labels)
                        if labels
                        else translate(locale, "No categories yet")
                    )
                    if amount:
                        extra_source = (
                            "1 other skill listed"
                            if amount == 1
                            else "{count} other skills listed"
                        )
                        extra = translate(locale, extra_source).replace(
                            "{count}", str(amount)
                        )
                        expected = f"{prefix} · {extra}"
                    else:
                        expected = prefix
                cases.append(
                    {
                        "locale": locale,
                        "kind": "summary",
                        "source": "",
                        "categories": selected,
                        "count": amount,
                        "expected": expected,
                    }
                )
        self.assertEqual(len(cases), 1554)
        self.assertEqual(
            set(catalogs), {locale for locale, _ in LANGUAGE_OPTIONS}
        )
        self.assertTrue(
            all(
                set(case)
                == {
                    "locale",
                    "kind",
                    "source",
                    "categories",
                    "count",
                    "expected",
                }
                for case in cases
            )
        )

        script = """
const fs = require('fs');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const isTrue = value => Boolean(value);
const results = payload.cases.map(item => {
  const interfaceTextFixture = payload.catalogs[item.locale];
  const messageSource = item.source;
  const categorySources = item.categories;
  const skillCount = item.count;
  const languageFixture = item.locale;
  return eval(payload.expressions[item.kind]);
});
process.stdout.write(JSON.stringify(results));
"""
        payload = {
            "expressions": expressions,
            "catalogs": catalogs,
            "cases": cases,
        }
        result = subprocess.run(
            [node, "-e", script],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        actual_results = json.loads(result.stdout)
        self.assertEqual(len(actual_results), len(cases))
        for case, actual in zip(cases, actual_results, strict=True):
            with self.subTest(
                locale=case["locale"],
                kind=case["kind"],
                source=case["source"],
                categories=case["categories"],
                count=case["count"],
            ):
                self.assertEqual(actual, case["expected"])


if __name__ == "__main__":
    unittest.main()
