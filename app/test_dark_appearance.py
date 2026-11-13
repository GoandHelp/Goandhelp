import inspect
import unittest
from pathlib import Path

from app.components import community_panel, profile_tabs
from app.components.header import minimal_header
from app.states.profile_state import ProfileState


APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent


class DarkAppearanceTests(unittest.IsolatedAsyncioTestCase):
    async def test_appearance_preference_event_accepts_modes_and_falls_back(
        self,
    ):
        state = ProfileState(appearance="system")
        for mode in ("light", "dark", "system"):
            ProfileState.set_appearance.fn(state, mode)
            self.assertEqual(state.appearance, mode)
        ProfileState.set_appearance.fn(state, "invalid")
        self.assertEqual(state.appearance, "system")

    async def test_settings_wire_modes_to_reflex_color_mode(self):
        source = inspect.getsource(profile_tabs.appearance_control)
        self.assertIn('ProfileState.set_appearance("light")', source)
        self.assertIn('ProfileState.set_appearance("dark")', source)
        self.assertIn('ProfileState.set_appearance("system")', source)
        self.assertIn('set_color_mode("light")', source)
        self.assertIn('set_color_mode("dark")', source)
        self.assertIn('set_color_mode("system")', source)
        profile_source = (APP_DIR / "states" / "profile_state.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'rx.LocalStorage("system", name="gah_appearance")', profile_source
        )

    def test_dark_mode_stylesheet_has_no_trailing_selector_comma_before_declaration(
        self,
    ):
        css = (ROOT_DIR / "assets" / "dark_mode.css").read_text(
            encoding="utf-8"
        )
        self.assertNotRegex(css, r",\s*\n\s*background-color\s*:")

    def test_effective_dark_mode_palette_is_loaded_after_map_styles(self):
        config = (ROOT_DIR / "rxconfig.py").read_text(encoding="utf-8")
        self.assertIn('default_color_mode="light"', config)
        self.assertNotIn('appearance="light"', config)
        self.assertIn('appearance="inherit"', config)
        app_source = (APP_DIR / "app.py").read_text(encoding="utf-8")
        self.assertLess(
            app_source.index('"/map.css"'), app_source.index('"/dark_mode.css"')
        )
        css = (ROOT_DIR / "assets" / "dark_mode.css").read_text(
            encoding="utf-8"
        )
        for required in (
            "html.dark",
            "#090b0f",
            "#15191f",
            "#20262e",
            '[class~="bg-white"]',
            '[class~="bg-[#fff7e8]"]',
            "::placeholder",
            '[role="dialog"]',
            "[data-radix-popper-content-wrapper]",
            ".gah-community-context-header::after",
            "maplibregl-canvas",
        ):
            with self.subTest(token=required):
                self.assertIn(required, css)
        self.assertIn("filter: none !important", css)

        for broad_selector in (
            '[class*="bg-white"]',
            '[class*="bg-white/"]',
            '[class*="bg-[#fff"]',
            '[class*="bg-[#ffffff]"]',
            '[class*="bg-[#fba922]"]',
            '[class*="bg-[#e08b12]"]',
            '[class*="bg-[#b86e08]"]',
        ):
            with self.subTest(selector=broad_selector):
                self.assertNotIn(broad_selector, css)

        for exact_selector in (
            '[class~="bg-white"]',
            '[class~="bg-[#ffffff]"]',
            '[class~="bg-[#fff]"]',
            '[class~="bg-[#fff7e8]"]',
            '[class~="bg-[#fff0d6]"]',
            '[class~="bg-[#fffaf0]"]',
            '[class~="bg-[#f9fafb]"]',
            '[class~="bg-white/20"]',
            '[class~="bg-white/90"]',
            '[class~="bg-[#ffffff]/20"]',
            '[class~="bg-[#fba922]"]',
            '[class~="bg-[#e08b12]"]',
            '[class~="bg-[#b86e08]"]',
        ):
            with self.subTest(selector=exact_selector):
                self.assertIn(exact_selector, css)

    def test_community_header_is_opaque_without_changing_sticky_tabs(self):
        header_source = inspect.getsource(minimal_header)
        self.assertIn('ProfileState.active_tab == "community"', header_source)
        self.assertIn("gah-community-context-header", header_source)
        self.assertIn("bg-white sticky top-0 z-40", header_source)
        self.assertIn("after:bg-white", header_source)
        self.assertIn("bg-white/20 backdrop-blur-sm", header_source)

        sticky = inspect.getsource(community_panel.community_header)
        for token in ("sticky", "top-0", "z-30", "bg-white", "pb-2"):
            self.assertIn(token, sticky)
        shell = inspect.getsource(profile_tabs.profile_tabs)
        self.assertIn('ProfileState.active_tab == "community"', shell)
        self.assertIn("flex-1 overflow-y-auto", shell)
        self.assertIn("flex-col min-h-0 w-full flex-1 overflow-hidden", shell)


if __name__ == "__main__":
    unittest.main()
