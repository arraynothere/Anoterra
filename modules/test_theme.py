import unittest

from PyQt6.QtWidgets import QApplication

from ui.main_window import AnoterraMainWindow

class ThemeSwitchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_theme_switch_updates_window_and_editor(self):
        window = AnoterraMainWindow()
        try:
            window._set_theme("light")
            editor = window.editor_tabs.widget(0)
            self.assertEqual(window.current_theme, "light")
            self.assertEqual(editor.theme_name, "light")
            self.assertIn("#f7f8fb", window.styleSheet())
        finally:
            window._set_theme("dark")
            window.close()

if __name__ == "__main__":
    unittest.main()
