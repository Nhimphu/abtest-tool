try:
    from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout
    from PyQt6.QtGui import QCursor
    from PyQt6.QtCore import Qt
except Exception:  # pragma: no cover - allow tests without PyQt installed
    class QLabel:
        def __init__(self, *a, **k):
            pass
        def setText(self, *a, **k):
            pass
        def setCursor(self, *a, **k):
            pass
        def setToolTip(self, *a, **k):
            pass
    QWidget = type("QWidget", (), {"__init__": lambda self, *a, **k: None})
    QHBoxLayout = type(
        "QHBoxLayout",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "addWidget": lambda *a, **k: None,
            "addStretch": lambda *a, **k: None,
            "setContentsMargins": lambda *a, **k: None,
        },
    )
    class _Qt:
        class CursorShape:
            PointingHandCursor = 0
    Qt = _Qt()
    def QCursor(*a, **k):
        return None

import logging

logger = logging.getLogger(__name__)

class HelpIcon(QLabel):
    """Small '?' label that shows a tooltip."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__('?', parent)
        try:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        except Exception as e:
            logger.debug("help widget: cursor/tooltips setup failed: %s", e)
        self.setToolTip(self.tr(text))


def with_help_label(label: QLabel, help_text: str) -> QWidget:
    """Return container with label and help icon."""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(label)
    layout.addWidget(HelpIcon(help_text, container))
    layout.addStretch()
    return container

__all__ = ["HelpIcon", "with_help_label"]
