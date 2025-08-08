"""Step 3: run analysis asynchronously and show results."""
from __future__ import annotations

import threading

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QPushButton,
    )
except Exception:  # pragma: no cover - stubs
    class _Stub:
        def __init__(self, *a, **k):
            pass

        def addWidget(self, *a, **k):
            pass

        def setText(self, *a, **k):
            pass

        def clicked(self):
            return lambda func: None

    QWidget = QVBoxLayout = QLabel = QPushButton = _Stub

from abtest_core.engine import analyze_groups, AnalysisResult
from .viewmodel import WizardViewModel


class StepResult(QWidget):
    """Run analysis in background thread and display summary."""

    def __init__(self, vm: WizardViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.vm = vm
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(self.tr("ui.wizard.step_result.title")))
        self.run_btn = QPushButton(self.tr("ui.wizard.run"))
        try:
            self.run_btn.clicked.connect(self.run_analysis)  # type: ignore[attr-defined]
        except Exception:
            pass
        lay.addWidget(self.run_btn)
        self.output = QLabel("")
        lay.addWidget(self.output)

    def run_analysis(self) -> None:
        def worker() -> None:
            try:
                res: AnalysisResult = analyze_groups(self.vm.df, self.vm.config)  # type: ignore[arg-type]
                self.vm.result = res
                if res.method_notes:
                    self.vm.method_notes = res.method_notes.split(", ")
                text = f"p={res.p_value:.4g}, effect={res.effect:.4g}, ci={res.ci}"
            except Exception as e:  # pragma: no cover - handle gracefully
                self.vm.errors.append(getattr(e, "to_dict", lambda: {"title": str(e)})())
                text = str(e)
            try:
                self.output.setText(text)
            except Exception:
                pass
        t = threading.Thread(target=worker, daemon=True)
        t.start()
