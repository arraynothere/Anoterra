import os
import tempfile
import unittest

from PyQt6.QtWidgets import QApplication

from ui.main_window import AnoterraMainWindow

class IDEUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_replace_all_is_undoable_as_one_action(self):
        window = AnoterraMainWindow()
        try:
            editor = window.editor_tabs.currentWidget()
            editor.setText("red blue red")
            editor.replace_all_text("red", "green")
            self.assertEqual(editor.text(), "green blue green")
            editor.undo()
            self.assertEqual(editor.text(), "red blue red")
        finally:
            window.close()

    def test_goto_line_accepts_one_based_line_number(self):
        window = AnoterraMainWindow()
        try:
            editor = window.editor_tabs.currentWidget()
            editor.setText("first\nsecond\nthird")
            editor.go_to_line(3)
            self.assertEqual(editor.getCursorPosition(), (2, 0))
        finally:
            window.close()

    def test_save_all_writes_every_named_editor_and_skips_untitled_tabs(self):
        window = AnoterraMainWindow()
        with tempfile.TemporaryDirectory() as temp_dir:
            first_path = os.path.join(temp_dir, "first.py")
            second_path = os.path.join(temp_dir, "second.html")
            try:
                window._create_new_tab("first.py", file_path=first_path, content="print('one')")
                window._create_new_tab("second.html", file_path=second_path, content="<h1>two</h1>")
                saved_count = window._save_all_files()
                self.assertEqual(saved_count, 2)
                with open(first_path, encoding="utf-8") as file:
                    self.assertEqual(file.read(), "print('one')")
                with open(second_path, encoding="utf-8") as file:
                    self.assertEqual(file.read(), "<h1>two</h1>")
            finally:
                window.close()

if __name__ == "__main__":
    unittest.main()
