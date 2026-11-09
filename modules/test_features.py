import os
import sys
import tempfile
import time
import unittest

from PyQt6.QtWidgets import QApplication

from core.theme_data import THEMES
from core.utils import build_pattern
from ui.main_window import AnoterraMainWindow
from ui.widgets import SettingsDialog


def _pump(app, condition, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.02)
    return False


class FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = AnoterraMainWindow()

    def tearDown(self):
        self.window.close()

    def test_toggle_comment_round_trip(self):
        editor = self.window.current_editor()
        editor.setText("a = 1\nb = 2\n")
        editor.setSelection(0, 0, 1, 5)
        editor.toggle_comment()
        self.assertEqual(editor.text(), "# a = 1\n# b = 2\n")
        editor.setSelection(0, 0, 1, 7)
        editor.toggle_comment()
        self.assertEqual(editor.text(), "a = 1\nb = 2\n")

    def test_regex_replace_all_is_one_undo_step(self):
        editor = self.window.current_editor()
        editor.setText("one two\nthree four")
        count = editor.replace_all_matches(build_pattern(r"(\w+) (\w+)", regex=True), r"\2 \1", True)
        self.assertEqual(count, 2)
        self.assertEqual(editor.text(), "two one\nfour three")
        editor.undo()
        self.assertEqual(editor.text(), "one two\nthree four")

    def test_goto_match_cycles_and_wraps(self):
        editor = self.window.current_editor()
        editor.setText("x a x\nx")
        pattern = build_pattern("x")
        self.assertEqual(editor.goto_match(pattern, True), (1, 3))
        self.assertEqual(editor.goto_match(pattern, True), (2, 3))
        self.assertEqual(editor.goto_match(pattern, True), (3, 3))
        self.assertEqual(editor.goto_match(pattern, True), (1, 3))

    def test_bookmarks(self):
        editor = self.window.current_editor()
        editor.setText("a\nb\nc\nd")
        editor.toggle_bookmark(1)
        editor.toggle_bookmark(3)
        self.assertEqual(editor.bookmarks(), [1, 3])
        editor.toggle_bookmark(1)
        self.assertEqual(editor.bookmarks(), [3])

    def test_auto_close_pairs(self):
        editor = self.window.current_editor()
        editor.setText("")
        self.assertTrue(editor._handle_pair_typing("("))
        self.assertEqual(editor.text(), "()")
        self.assertEqual(editor.getCursorPosition(), (0, 1))
        self.assertTrue(editor._handle_pair_typing(")"))
        self.assertEqual(editor.getCursorPosition(), (0, 2))

    def test_live_lint_marks_syntax_errors(self):
        editor = self.window.current_editor()
        editor.setText("def broken(:\n    pass\n")
        self.window._run_lint()
        self.assertEqual(len(editor.problems), 1)
        self.assertEqual(self.window.problems_page.topLevelItemCount(), 1)

    def test_every_theme_applies(self):
        editor = self.window.current_editor()
        for name in THEMES:
            self.window._set_theme(name)
            self.assertEqual(self.window.current_theme, name)
            self.assertEqual(editor.theme_name, name)
        self.window._set_theme("dark")

    def test_command_palette_lists_menu_actions(self):
        self.window._show_command_palette()
        labels = [item[0] for item in self.window._quick_dialog.items]
        self.assertIn("Execution: Run Script", labels)
        self.assertIn("Edit: Toggle Comment", labels)
        self.window._quick_dialog.close()

    def test_settings_dialog_round_trip(self):
        dialog = SettingsDialog(self.window.prefs)
        values = dialog.values()
        self.assertEqual(values["tab_width"], self.window.prefs["tab_width"])
        self.assertEqual(values["theme"], self.window.prefs["theme"])

    def test_closing_last_tab_shows_welcome_page(self):
        self.window._close_tab(0)
        self.assertEqual(self.window.editor_tabs.count(), 0)
        self.assertEqual(self.window.editor_stack.currentIndex(), 0)

    def test_opening_a_file_replaces_pristine_untitled_tab(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "a.py")
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write("print(1)\r\n")
            editor = self.window._open_path(path)
            self.assertEqual(self.window.editor_tabs.count(), 1)
            self.assertEqual(editor.eol, "\r\n")

    def test_runner_streams_output_and_accepts_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "echo.py")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("name = input('who? ')\nprint('hi', name)\n")
            from core.runner import CodeRunnerEngine
            chunks, done = [], []
            runner = CodeRunnerEngine(path)
            runner.output_signal.connect(chunks.append)
            runner.finished_signal.connect(lambda code, metrics: done.append((code, metrics)))
            runner.start()
            self.assertTrue(_pump(self.app, lambda: "".join(chunks).startswith("who?")))
            runner.send_input("Ana")
            self.assertTrue(_pump(self.app, lambda: bool(done)))
            self.assertEqual(done[0][0], 0)
            self.assertIn("hi Ana", "".join(chunks))

    def test_runner_stop_kills_long_process(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "loop.py")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("import time\nwhile True:\n    time.sleep(0.1)\n")
            from core.runner import CodeRunnerEngine
            done = []
            runner = CodeRunnerEngine(path)
            runner.finished_signal.connect(lambda code, metrics: done.append(metrics))
            runner.start()
            time.sleep(0.5)
            runner.stop()
            self.assertTrue(_pump(self.app, lambda: bool(done)))
            self.assertTrue(done[0]["stopped"])


if __name__ == "__main__":
    unittest.main()
