import ast
import importlib.util
import inspect
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parent / "scripts" / "capture_screenshots.py"
spec = importlib.util.spec_from_file_location("capture_screenshots", SCRIPT)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ScreenshotRunnerTests(unittest.TestCase):
    def test_required_flags_are_exactly_once(self):
        self.assertEqual(len(runner.BROWSER_ARGS), 3)
        for flag in (
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ):
            self.assertEqual(runner.BROWSER_ARGS.count(flag), 1)

    def test_sequential_structure(self):
        source = SCRIPT.read_text()
        self.assertEqual(runner.CONCURRENCY, 1)
        self.assertNotIn("asyncio.gather", source)
        self.assertNotIn("TaskGroup", source)
        tree = ast.parse(source)
        self.assertTrue(
            any(isinstance(node, ast.For) for node in ast.walk(tree))
        )

    def test_urls_and_indexed_safe_names(self):
        self.assertEqual(
            runner.normalize_url("http://localhost:3000", "/"),
            "http://localhost:3000/",
        )
        self.assertEqual(
            runner.normalize_url("http://localhost:3000/", "verify"),
            "http://localhost:3000/verify",
        )
        self.assertEqual(runner.safe_output_filename("/", 1), "001-root.png")
        name = runner.safe_output_filename("/verify?token=secret/value", 2)
        self.assertEqual(name, "002-verify.png")
        self.assertNotIn("/", name)

    def test_defaults_and_parser(self):
        args = runner.build_parser().parse_args([])
        self.assertEqual(args.width, 1280)
        self.assertEqual(args.height, 720)
        self.assertFalse(args.full_page)
        self.assertFalse(args.strict)
        args = runner.build_parser().parse_args(
            ["--route", "/", "--route", "/verify", "--full-page", "--strict"]
        )
        self.assertEqual(args.route, ["/", "/verify"])
        self.assertTrue(args.full_page)
        self.assertTrue(args.strict)

    def test_cleanup_and_warning_structure(self):
        source = inspect.getsource(runner.capture)
        module_source = SCRIPT.read_text()
        self.assertIn(
            "python -m app.scripts.capture_screenshots --route / --route /verify",
            module_source,
        )
        self.assertGreaterEqual(source.count("await page.close()"), 1)
        self.assertGreaterEqual(source.count("await context.close()"), 1)
        self.assertGreaterEqual(source.count("await browser.close()"), 1)
        self.assertGreaterEqual(source.count("finally:"), 3)
        self.assertLess(
            source.index("await page.close()"),
            source.index("await context.close()"),
        )
        self.assertLess(
            source.index("await context.close()"),
            source.index("await browser.close()"),
        )
        self.assertIn("logger.warning", source)
        self.assertIn("type(exc).__name__", source)


if __name__ == "__main__":
    unittest.main()
