import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import AnoterraMainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    if os.name == "nt":
        icon_path = "anoterra.ico"
    else:
        icon_path = "anoterra.png"
        
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    anoterra_app = AnoterraMainWindow()
    anoterra_app.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
