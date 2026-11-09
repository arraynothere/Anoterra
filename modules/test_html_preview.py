import os
import tempfile
import unittest

from PyQt6.QtWidgets import QApplication, QTextBrowser

from ui.main_window import AnoterraMainWindow


class HtmlPreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_new_html_file_gets_html_lexer_and_starter_page(self):
        window = AnoterraMainWindow()
        try:
            window._create_new_tab("Untitled.html")
            editor = window.editor_tabs.currentWidget()
            self.assertEqual(editor.lexer().language(), "HTML")
            self.assertIn("<!DOCTYPE html>", editor.text())
        finally:
            window.close()

    def test_run_html_opens_rendered_preview_inside_anoterra(self):
        window = AnoterraMainWindow()
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "page.html")
            page = "<!DOCTYPE html><html><body><h1>Preview works</h1></body></html>"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(page)
            try:
                window._create_new_tab("page.html", file_path=file_path, content=page)
                window._execute_code("run")
                preview = window.editor_tabs.currentWidget()
                self.assertIsInstance(preview, QTextBrowser)
                self.assertIn("Preview works", preview.toPlainText())
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
