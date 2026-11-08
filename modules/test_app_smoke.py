import unittest
from PyQt6.QtWidgets import QApplication
from ui.main_window import AnoterraMainWindow

class ApplicationSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_initializes(self):
        window = AnoterraMainWindow()
        self.assertEqual(window.editor_tabs.count(), 1)
        window.close()

if __name__ == "__main__":
    unittest.main()
