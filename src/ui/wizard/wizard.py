# -*- coding: utf-8 -*-
"""Main wizard window composed of three steps."""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
        QPushButton,
    )
except Exception:  # pragma: no cover - stubs
    class _Stub:
        def __init__(self, *a, **k):
            pass

        def addWidget(self, *a, **k):
            pass

        def setCurrentIndex(self, *a, **k):
            pass

        def currentIndex(self):
            return 0

        def count(self):
            return 0

        def setLayout(self, *a, **k):
            pass

        def setEnabled(self, *a, **k):
            pass

        def setText(self, *a, **k):
            pass

        def clicked(self):
            return lambda func: None

    QDialog = QVBoxLayout = QHBoxLayout = QStackedWidget = QPushButton = _Stub

from .viewmodel import WizardViewModel
from .step_data import StepData
from .step_config import StepConfig
from .step_result import StepResult


class Wizard(QDialog):
    """Simple QStackedWidget-based wizard."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.vm = WizardViewModel()
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.step_data = StepData(self.vm)
        self.step_config = StepConfig(self.vm)
        self.step_result = StepResult(self.vm)
        self.stack.addWidget(self.step_data)
        self.stack.addWidget(self.step_config)
        self.stack.addWidget(self.step_result)
        layout.addWidget(self.stack)
        btns = QHBoxLayout()
        self.back_btn = QPushButton(self.tr("ui.wizard.back"))
        self.next_btn = QPushButton(self.tr("ui.wizard.next"))
        try:
            self.back_btn.clicked.connect(self.prev_step)  # type: ignore[attr-defined]
            self.next_btn.clicked.connect(self.next_step)  # type: ignore[attr-defined]
        except Exception:
            pass
        btns.addWidget(self.back_btn)
        btns.addWidget(self.next_btn)
        layout.addLayout(btns)
        self._update_buttons()

    def _update_buttons(self) -> None:
        idx = self.stack.currentIndex()
        try:
            self.back_btn.setEnabled(idx > 0)
            if idx == self.stack.count() - 1:
                self.next_btn.setText(self.tr("ui.wizard.run"))
            else:
                self.next_btn.setText(self.tr("ui.wizard.next"))
        except Exception:
            pass

    def next_step(self) -> None:
        idx = self.stack.currentIndex()
        if idx == 0 and not self.step_data.validate():
            return
        if idx == 1 and not self.step_config.validate():
            return
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
            self._update_buttons()
        else:
            self.step_result.run_analysis()

    def prev_step(self) -> None:
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._update_buttons()
