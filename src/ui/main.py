import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale

# Allow running this module directly without setting PYTHONPATH
if __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.ui_mainwindow import ABTestWindow
from utils.config import config


def main(cfg=config) -> None:
    """Launch the A/B test GUI application."""
    app = QApplication(sys.argv)

    translator = QTranslator()
    locale = QLocale.system().name().split("_")[0]
    translations_dir = Path(__file__).resolve().parents[1] / "translations"
    if translator.load(str(translations_dir / f"app_{locale}.qm")):
        app.installTranslator(translator)
    else:
        # Fallback to English if translation for the current locale isn't found
        translator.load(str(translations_dir / "app_en.qm"))
        app.installTranslator(translator)

    window = ABTestWindow(cfg)
    # Skip authentication when running locally
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
