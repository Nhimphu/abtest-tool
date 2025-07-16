import sys
import logging
import logging.config
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

# Allow running this module directly without setting PYTHONPATH
if __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.ui_mainwindow import ABTestWindow
from utils.config import config


def main(cfg=config) -> None:
    """Launch the A/B test GUI application."""
    cfg_path = Path(__file__).resolve().parents[1] / "logging.yaml"
    if cfg_path.exists() and yaml is not None:
        root = logging.getLogger()
        existing = list(root.handlers)
        with cfg_path.open("r", encoding="utf-8") as f:
            logging.config.dictConfig(yaml.safe_load(f))
        for h in existing:
            if h not in root.handlers:
                root.addHandler(h)
    else:  # pragma: no cover - fallback if yaml not available
        logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app = QApplication(sys.argv)

    translator = QTranslator()
    locale = QLocale.system().name().split("_")[0]
    translations_dir = Path(__file__).resolve().parents[1] / "translations"
    if translator.load(str(translations_dir / f"app_{locale}.qm")):
        current_lang = locale
    else:
        translator.load(str(translations_dir / "app_en.qm"))
        current_lang = "en"
    app.installTranslator(translator)

    window = ABTestWindow(cfg, translator=translator, lang=current_lang)
    # Skip authentication when running locally
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
