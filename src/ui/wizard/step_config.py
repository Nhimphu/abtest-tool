# -*- coding: utf-8 -*-
"""Step 2: configure analysis options and run SRM gate."""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QComboBox,
        QCheckBox,
    )
except Exception:  # pragma: no cover - stubs
    class _Stub:
        def __init__(self, *a, **k):
            pass

        def addWidget(self, *a, **k):
            pass

        def text(self):
            return ""

        def currentText(self):
            return ""

        def isChecked(self):
            return False

    QWidget = QVBoxLayout = QHBoxLayout = QLabel = QLineEdit = QComboBox = QCheckBox = _Stub

from abtest_core.types import AnalysisConfig
from abtest_core.srm import srm_check, SrmCheckFailed
from .viewmodel import WizardViewModel


class StepConfig(QWidget):
    """Widget to input analysis configuration parameters."""

    def __init__(self, vm: WizardViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.vm = vm
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(self.tr("ui.wizard.step_config.title")))

        row1 = QHBoxLayout()
        row1.addWidget(QLabel(self.tr("alpha")))
        self.alpha_edit = QLineEdit("0.05")
        row1.addWidget(self.alpha_edit)
        row1.addWidget(QLabel(self.tr("sided")))
        self.sided = QComboBox()
        try:
            self.sided.addItems(["two", "left", "right"])
        except Exception:
            pass
        row1.addWidget(self.sided)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel(self.tr("metric_type")))
        self.metric_type = QComboBox()
        try:
            self.metric_type.addItems(["binomial", "continuous", "ratio"])
        except Exception:
            pass
        row2.addWidget(self.metric_type)
        self.cuped = QCheckBox(self.tr("cuped"))
        row2.addWidget(self.cuped)
        lay.addLayout(row2)

    def build_config(self) -> AnalysisConfig:
        alpha = float(self.alpha_edit.text() or 0.05)
        sided = self.sided.currentText() or "two"
        metric_type = self.metric_type.currentText() or "binomial"
        cfg = AnalysisConfig(
            alpha=alpha,
            sided=sided,  # type: ignore[arg-type]
            metric_type=metric_type,  # type: ignore[arg-type]
            use_cuped=self.cuped.isChecked(),
            preperiod_metric_col=self.vm.preperiod_col,
        )
        return cfg

    def validate(self) -> bool:
        if self.vm.df is None:
            return False
        counts = self.vm.df["group"].value_counts().to_dict()
        res = srm_check(counts)
        if not res["passed"] and not self.vm.force_run_when_srm_failed:
            err = SrmCheckFailed(res).to_dict()
            self.vm.errors.append(err)
            return False
        self.vm.config = self.build_config()
        return True
