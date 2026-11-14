import unittest

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtWidgets import QApplication

from ui.main_window import AnoterraMainWindow

class EditorViewOptionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_zoom_in_and_reset_change_editor_scale(self):
        window = AnoterraMainWindow()
        try:
            editor = window.editor_tabs.currentWidget()
            initial_zoom = editor.SendScintilla(QsciScintilla.SCI_GETZOOM)
            window._zoom_in()
            self.assertGreater(editor.SendScintilla(QsciScintilla.SCI_GETZOOM), initial_zoom)
            window._reset_zoom()
            self.assertEqual(editor.SendScintilla(QsciScintilla.SCI_GETZOOM), 0)
        finally:
            window.close()

    def test_word_wrap_can_be_toggled_on_and_off(self):
        window = AnoterraMainWindow()
        try:
            editor = window.editor_tabs.currentWidget()
            window._toggle_word_wrap(True)
            self.assertEqual(editor.wrapMode(), QsciScintilla.WrapMode.WrapWord)
            window._toggle_word_wrap(False)
            self.assertEqual(editor.wrapMode(), QsciScintilla.WrapMode.WrapNone)
        finally:
            window.close()

if __name__ == "__main__":
    unittest.main()
