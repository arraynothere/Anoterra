"""Headless tests for the pure-Python core (no Qt needed)."""
import json
import os
import tempfile
import unittest

from core.analysis import check_syntax, extract_symbols, format_source, search_in_files
from core.languages import RunError, detect_language, run_plan
from core.settings import DEFAULTS, coerce
from core.theme_data import THEMES, classify_style
from core.utils import (
    BinaryFileError, apply_save_transforms, build_pattern, detect_eol, fuzzy_filter, parse_location,
    read_text_file, write_text_file,
)


class LanguageTests(unittest.TestCase):
    def test_detection(self):
        self.assertEqual(detect_language("a.py").key, "python")
        self.assertEqual(detect_language("Makefile").key, "makefile")
        self.assertEqual(detect_language("x.TS").key, "typescript")
        self.assertEqual(detect_language("unknown.zzz").key, "text")

    def test_run_plan(self):
        self.assertIn("-u", run_plan("/tmp/a.py").run)
        with self.assertRaises(RunError):
            run_plan("/tmp/a.xyz")


class AnalysisTests(unittest.TestCase):
    def test_python_syntax_error_reported(self):
        problems = check_syntax("def broken(:\n    pass\n", "python")
        self.assertEqual(problems[0].line, 1)
        self.assertEqual(check_syntax("x = 1\n", "python"), [])

    def test_json_error(self):
        self.assertEqual(check_syntax('{"a": }', "json")[0].line, 1)

    def test_outline_nests_methods(self):
        text = "class A:\n    def m(self):\n        pass\n\ndef f():\n    pass\n"
        kinds = [(s.kind, s.name, s.level) for s in extract_symbols(text, "python")]
        self.assertEqual(kinds, [("class", "A", 0), ("method", "m", 1), ("function", "f", 0)])

    def test_formatter_keeps_multiline_strings(self):
        source = 'def a():\n    x = """keep   \n    me   """\n    return x\nclass B:\n    pass\n'
        formatted, _engine = format_source(source, "python")
        self.assertIn("keep   \n", formatted)
        self.assertIn("\n\n\nclass B:", formatted)

    def test_json_formatter(self):
        formatted, engine = format_source('{"a":1,"b":[1,2]}', "json")
        self.assertEqual(engine, "json")
        self.assertEqual(json.loads(formatted), {"a": 1, "b": [1, 2]})

    def test_search_in_files(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "a.py"), "w", encoding="utf-8") as handle:
                handle.write("alpha\nBeta beta\n")
            os.makedirs(os.path.join(root, "node_modules"))
            with open(os.path.join(root, "node_modules", "skip.py"), "w", encoding="utf-8") as handle:
                handle.write("beta\n")
            hits = list(search_in_files(root, build_pattern("beta"), ["*.py"]))
            self.assertEqual([(h[1], h[3]) for h in hits], [(2, 0), (2, 5)])


class UtilTests(unittest.TestCase):
    def test_pattern_options(self):
        self.assertEqual(len(list(build_pattern("red", whole_word=True).finditer("red redder RED"))), 2)
        self.assertEqual(len(list(build_pattern("red", case_sensitive=True).finditer("red RED"))), 1)

    def test_fuzzy(self):
        self.assertEqual(fuzzy_filter("mw", ["main_window.py", "README.md"]), ["main_window.py"])

    def test_parse_location(self):
        self.assertEqual(parse_location('  File "/tmp/a.py", line 12, in <module>'), ("/tmp/a.py", 12, None))
        self.assertEqual(parse_location("main.cpp:10:5: error"), ("main.cpp", 10, 5))
        self.assertIsNone(parse_location("hello"))

    def test_file_roundtrip_preserves_crlf_and_bom(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "x.txt")
            write_text_file(path, "a\r\nb\r\n", "utf-8-sig")
            loaded = read_text_file(path)
            self.assertEqual((loaded.text, loaded.encoding, loaded.eol), ("a\r\nb\r\n", "utf-8-sig", "\r\n"))

    def test_binary_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "x.bin")
            with open(path, "wb") as handle:
                handle.write(b"\x00\x01\x02")
            with self.assertRaises(BinaryFileError):
                read_text_file(path)

    def test_save_transforms(self):
        self.assertEqual(apply_save_transforms("a  \nb\t", True, True), "a\nb\n")
        self.assertEqual(detect_eol("a\nb\r\nc\r\n"), "\r\n")

    def test_settings_coercion(self):
        self.assertIs(coerce("use_tabs", "false"), False)
        self.assertEqual(coerce("tab_width", "999"), 16)
        self.assertEqual(set(DEFAULTS["theme"] for _ in [0]), {"dark"})


class ThemeTests(unittest.TestCase):
    def test_every_theme_has_all_roles(self):
        reference = set(THEMES["dark"])
        for name, palette in THEMES.items():
            self.assertEqual(set(palette), reference, name)

    def test_style_classification(self):
        self.assertEqual(classify_style("Double-quoted string"), "string")
        self.assertEqual(classify_style("Keyword"), "keyword")
        self.assertEqual(classify_style("Comment line"), "comment")


if __name__ == "__main__":
    unittest.main()
