import sys
from PyQt6.QtWidgets import QApplication
from .ui_mainwindow import ABTestWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ABTestWindow()
    window.authenticate()
    if window.token is not None:
        window.show()
        sys.exit(app.exec())
