"""Black formatting (skipped when Black is not installed)."""
import importlib.util
import unittest

from core.analysis import format_source


@unittest.skipIf(importlib.util.find_spec("black") is None, "black not installed")
class BlackFormatTests(unittest.TestCase):
    def test_python_is_formatted_with_black(self):
        text, engine = format_source("x = {  'a':1,'b':2 }\n", "python")
        self.assertEqual(engine, "black")
        self.assertEqual(text, 'x = {"a": 1, "b": 2}\n')

    def test_invalid_python_falls_back_to_builtin_formatter(self):
        _, engine = format_source("def broken(:\n", "python")
        self.assertEqual(engine, "built-in")


if __name__ == "__main__":
    unittest.main()
