try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QToolTip,
    )
    from PyQt6.QtCore import pyqtSignal
except Exception:  # pragma: no cover - allow running tests without PyQt installed
    QWidget = type("QWidget", (), {"__init__": lambda self, *a, **k: None})
    QVBoxLayout = type(
        "QVBoxLayout",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "addWidget": lambda *a, **k: None,
            "setContentsMargins": lambda *a, **k: None,
        },
    )

    class DummySig:
        def connect(self, *a, **k):
            pass

    QLabel = QLineEdit = QPushButton = type(
        "Widget",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "text": lambda self: "",
            "setPlaceholderText": lambda *a, **k: None,
            "textChanged": DummySig(),
            "clicked": DummySig(),
            "setToolTip": lambda *a, **k: None,
        },
    )
    QToolTip = type("QToolTip", (), {"showText": lambda *a, **k: None})
    pyqtSignal = lambda *a, **k: lambda *args, **kwargs: None

import json
import urllib.request

from utils.safe_eval import validate_expression


class SettingsWidget(QWidget):
    """Simple settings panel."""

    metric_changed = pyqtSignal(str)  # emitted with valid expression
    log_message = pyqtSignal(str)  # emitted with webhook test result

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.metric_edit = QLineEdit()
        self.metric_edit.setPlaceholderText('sum("conv")/sum("users")')

        self.webhook_edit = QLineEdit()
        self.webhook_edit.setPlaceholderText('https://example.com/webhook')
        self.test_button = QPushButton('Test webhook')
        if hasattr(self.test_button, 'clicked'):
            self.test_button.clicked.connect(self._on_test_webhook)  # type: ignore

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Custom metric expression"))
        layout.addWidget(self.metric_edit)
        layout.addWidget(QLabel("Webhook URL"))
        layout.addWidget(self.webhook_edit)
        layout.addWidget(self.test_button)

        if hasattr(self.metric_edit, "textChanged"):
            self.metric_edit.textChanged.connect(self._on_text_changed)  # type: ignore

    # ----- validation -----
    def _on_text_changed(self, text: str) -> None:
        try:
            validate_expression(text)
        except Exception as e:  # ValueError
            self.metric_edit.setToolTip(self.tr(str(e)))
            if hasattr(QToolTip, "showText"):
                QToolTip.showText(self.metric_edit.mapToGlobal(self.metric_edit.rect().bottomLeft()), str(e))
        else:
            self.metric_edit.setToolTip(self.tr(""))
            if callable(self.metric_changed):
                self.metric_changed.emit(text)  # type: ignore

    def _on_test_webhook(self) -> None:
        url = self.webhook_edit.text()
        if not url:
            msg = "Webhook URL is empty"
        else:
            data = json.dumps({"text": "test"}).encode()
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = resp.read().decode(errors="ignore")
                    msg = f"Webhook response {resp.status}: {body}"
            except Exception as e:
                msg = f"Webhook error: {e}"

        if callable(self.log_message):
            self.log_message.emit(msg)  # type: ignore

