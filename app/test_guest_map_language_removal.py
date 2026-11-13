import ast
import unittest
from pathlib import Path


GUEST_MAP_PATH = Path(__file__).parent / "components" / "guest_map.py"


class GuestMapLanguageRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GUEST_MAP_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.functions = {
            node.name: node
            for node in cls.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def _function_source(self, name: str) -> str:
        return ast.get_source_segment(self.source, self.functions[name]) or ""

    def test_floating_map_stack_has_no_language_control(self):
        stack_source = self._function_source("guest_control_stack")
        self.assertNotIn("guest-map-language", stack_source)
        self.assertNotIn("language_control", stack_source)
        self.assertNotIn("rx.el.select", stack_source)
        self.assertEqual(
            stack_source.count("guest_utility_button("),
            2,
        )
        self.assertIn(
            'guest_utility_button("bell", "Notifications")', stack_source
        )
        self.assertIn(
            'guest_utility_button("settings", "Settings")', stack_source
        )
        self.assertIn("gap-1", stack_source)
        self.assertIn("top-3 right-3 sm:right-[22px]", stack_source)

    def test_map_stack_component_renders_only_the_two_utilities(self):
        from app.components.guest_map import guest_control_stack

        component = guest_control_stack()
        rendered = str(component)
        self.assertNotIn("guest-map-language", rendered)
        self.assertNotIn("language_control", rendered)
        self.assertNotIn("select", rendered.lower())
        self.assertIn("Notifications", rendered)
        self.assertIn("Settings", rendered)
        self.assertEqual(rendered.count("gah-map-utility"), 2)
        self.assertIn("size-[43px]", rendered)

    def test_utility_button_behavior_and_accessibility_are_preserved(self):
        utility_source = self._function_source("guest_utility_button")
        self.assertIn("map_utility_icon(icon)", utility_source)
        self.assertIn("title=ui(label)", utility_source)
        self.assertIn("aria_label=ui(label)", utility_source)
        self.assertIn("on_click=GuestMapState.open_wall(", utility_source)
        self.assertIn("size-[43px]", utility_source)
        self.assertIn("text-white", utility_source)

    def test_auth_wall_language_control_is_removed(self):
        from app.components.guest_map import guest_wall_auth_body

        auth_body_source = self._function_source("guest_wall_auth_body")
        imports = [
            node
            for node in self.tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "app.components.language_control"
        ]
        self.assertFalse(imports)
        self.assertNotIn("guest-auth-language", auth_body_source)
        self.assertNotIn("language_control", auth_body_source)
        self.assertIn("member_benefits_box()", auth_body_source)
        self.assertIn('guest_wall_tab("Register", "register"', auth_body_source)
        self.assertIn('guest_wall_tab("Sign in", "signin"', auth_body_source)
        self.assertIn("register_form()", auth_body_source)
        self.assertIn("sign_in_form()", auth_body_source)
        self.assertIn("local_preview_button()", auth_body_source)
        self.assertIn("legal_dialog()", auth_body_source)

        function = self.functions["guest_wall_auth_body"]
        returned = function.body[-1]
        self.assertIsInstance(returned, ast.Return)
        body_call = returned.value
        self.assertIsInstance(body_call, ast.Call)
        self.assertTrue(body_call.args)
        first_child = body_call.args[0]
        self.assertIsInstance(first_child, ast.Call)
        self.assertEqual(first_child.func.id, "member_benefits_box")

        rendered = str(guest_wall_auth_body())
        self.assertTrue(rendered)
        self.assertNotIn("guest-auth-language", rendered)


if __name__ == "__main__":
    unittest.main()
