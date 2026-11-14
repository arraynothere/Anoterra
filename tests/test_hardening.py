"""Headless tests for path helpers and settings defaults."""
import unittest

from core.settings import DEFAULTS
from core.utils import safe_relpath


class HardeningTests(unittest.TestCase):
    def test_plugins_are_opt_in(self):
        self.assertFalse(DEFAULTS["enable_plugins"])

    def test_safe_relpath_never_raises(self):
        self.assertEqual(safe_relpath("/a/b/c.py", "/a"), "b/c.py".replace("/", __import__("os").sep))


@unittest.skipIf(__import__("importlib.util").util.find_spec("PyQt6") is None, "PyQt6 not installed")
class SettingsUiTests(unittest.TestCase):
    def test_enable_plugins_is_exposed_in_settings_dialog(self):
        from ui.widgets import SettingsDialog
        keys = {field[0] for _, fields in SettingsDialog.PAGES for field in fields}
        self.assertIn("enable_plugins", keys)


if __name__ == "__main__":
    unittest.main()
