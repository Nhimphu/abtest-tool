import sys
from PyQt6.QtWidgets import QApplication
from ui.ui_mainwindow import ABTestWindow


def main() -> None:
    """Launch the A/B test GUI application."""
    app = QApplication(sys.argv)
    window = ABTestWindow()
    # Skip authentication when running locally
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
