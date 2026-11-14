"""Qt-level checks for the debugger markers and wiring (need PyQt6; run with the offscreen platform)."""
import unittest

from PyQt6.QtWidgets import QApplication

from ui.main_window import AnoterraMainWindow


class DebuggerUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_breakpoint_markers_toggle_and_clear(self):
        window = AnoterraMainWindow()
        try:
            editor = window.current_editor()
            editor.setText("a = 1\nb = 2\nc = 3\n")
            editor.toggle_breakpoint(1)
            editor.toggle_breakpoint(2)
            self.assertEqual(editor.breakpoint_lines(), [1, 2])
            editor.toggle_breakpoint(1)
            self.assertEqual(editor.breakpoint_lines(), [2])
            editor.clear_breakpoints()
            self.assertEqual(editor.breakpoint_lines(), [])
        finally:
            window.close()

    def test_debug_line_marker_moves_and_clears(self):
        window = AnoterraMainWindow()
        try:
            editor = window.current_editor()
            editor.setText("a = 1\nb = 2\n")
            editor.set_debug_line(1)
            editor.set_debug_line(0)
            editor.set_debug_line(None)
            editor.set_debug_line(99)      # out of range: ignored
        finally:
            window.close()

    def test_debug_tab_and_controller_exist(self):
        window = AnoterraMainWindow()
        try:
            self.assertGreaterEqual(window.bottom_tabs.indexOf(window.debug.panel), 0)
            self.assertEqual(window.debug.collect_breakpoints(), {})     # unsaved file: no breakpoints
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
