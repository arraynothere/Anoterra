import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from ui.main_window import AnoterraMainWindow


def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Anoterra")
    app.setOrganizationName("Anoterra")

    icon_path = resource_path("anoterra.ico" if os.name == "nt" else "anoterra.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = AnoterraMainWindow()
    window.show()

    # `python main.py file.py folder/` opens files (and sets a folder as workspace).
    for argument in sys.argv[1:]:
        if os.path.exists(argument):
            window._open_path(argument)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
