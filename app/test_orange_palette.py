import reflex as rx

import ast
import logging
from pathlib import Path
import re
import unittest


APP_DIR = Path(__file__).resolve().parent
OBSOLETE_COLORS = (
    "#2362ef",
    "#1a4bc4",
    "#e0ebff",
    "#eef3ff",
    "#dbe3f2",
    "#d8e2fb",
    "#c7dbff",
    "#9dc0ff",
)
ORANGE_COLORS = (
    "#fba922",
    "#e08b12",
    "#b86e08",
    "#fff7e8",
    "#f7d9a0",
    "#f6c66f",
    "#f2bd5a",
)


def read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        logging.exception(f"Error: {e}")
        raise


class OrangePaletteTests(unittest.TestCase):
    def test_production_has_no_obsolete_palette(self):
        paths = sorted(
            path
            for path in APP_DIR.rglob("*.py")
            if not path.name.startswith("test_")
        )
        paths.append(APP_DIR.parent / "rxconfig.py")
        self.assertTrue(paths)
        for path in paths:
            source = read_source(path)
            with self.subTest(file=path.name):
                for color in OBSOLETE_COLORS:
                    self.assertNotIn(color, source.lower())
                self.assertIsNone(
                    re.search(
                        r"accent_color\s*=\s*[\"\']blue[\"\']", source, re.I
                    )
                )

    def test_orange_replacements_are_present(self):
        source = "\n".join(
            read_source(path)
            for path in sorted(APP_DIR.rglob("*.py"))
            if not path.name.startswith("test_")
        )
        for color in ORANGE_COLORS:
            with self.subTest(color=color):
                self.assertIn(color, source)

    def test_both_theme_declarations_are_orange(self):
        for path in (APP_DIR / "app.py", APP_DIR.parent / "rxconfig.py"):
            tree = ast.parse(read_source(path))
            accents = [
                keyword.value.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                for keyword in node.keywords
                if keyword.arg == "accent_color"
                and isinstance(keyword.value, ast.Constant)
            ]
            with self.subTest(file=path.name):
                self.assertTrue(accents)
                self.assertEqual(set(accents), {"orange"})
        self.assertIsNotNone(
            rx.theme(appearance="light", accent_color="orange")
        )


if __name__ == "__main__":
    unittest.main()
