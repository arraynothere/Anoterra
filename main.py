import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from ui.main_window import AnoterraMainWindow

def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def _excepthook(exc_type, exc, tb):
    import traceback
    traceback.print_exception(exc_type, exc, tb)
    try:
        from PyQt6.QtWidgets import QMessageBox
        if QApplication.instance() is not None:
            QMessageBox.critical(None, "Unexpected error", f"{exc_type.__name__}: {exc}")
    except Exception:
        pass

def main():
    sys.excepthook = _excepthook
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Anoterra")
    app.setOrganizationName("Anoterra")

    icon_path = resource_path("anoterra.ico" if os.name == "nt" else "anoterra.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = AnoterraMainWindow()
    window.show()
    
    for argument in sys.argv[1:]:
        if os.path.exists(argument):
            window.open_path(argument)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
