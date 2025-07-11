import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Allow running this module directly without setting PYTHONPATH
if __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

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
