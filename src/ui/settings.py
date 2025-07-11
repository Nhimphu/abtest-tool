try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QToolTip
    from PyQt6.QtCore import pyqtSignal
except Exception:  # pragma: no cover - allow running tests without PyQt installed
    QWidget = type("QWidget", (), {})
    QVBoxLayout = type("QVBoxLayout", (), {"addWidget": lambda *a, **k: None, "setContentsMargins": lambda *a, **k: None})
    QLabel = QLineEdit = type("Widget", (), {"text": lambda self: "", "setPlaceholderText": lambda *a, **k: None, "textChanged": lambda *a, **k: None, "setToolTip": lambda *a, **k: None})
    QToolTip = type("QToolTip", (), {"showText": lambda *a, **k: None})
    pyqtSignal = lambda *a, **k: None

from utils.safe_eval import validate_expression


class SettingsWidget(QWidget):
    """Simple settings panel."""

    metric_changed = pyqtSignal(str)  # emitted with valid expression

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.metric_edit = QLineEdit()
        self.metric_edit.setPlaceholderText('sum("conv")/sum("users")')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Custom metric expression"))
        layout.addWidget(self.metric_edit)

        if hasattr(self.metric_edit, "textChanged"):
            self.metric_edit.textChanged.connect(self._on_text_changed)  # type: ignore

    # ----- validation -----
    def _on_text_changed(self, text: str) -> None:
        try:
            validate_expression(text)
        except Exception as e:  # ValueError
            self.metric_edit.setToolTip(str(e))
            if hasattr(QToolTip, "showText"):
                QToolTip.showText(self.metric_edit.mapToGlobal(self.metric_edit.rect().bottomLeft()), str(e))
        else:
            self.metric_edit.setToolTip("")
            if callable(self.metric_changed):
                self.metric_changed.emit(text)  # type: ignore
