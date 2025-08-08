# -*- coding: utf-8 -*-
"""Step 1: load data and map columns."""
from __future__ import annotations

import pandas as pd

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QComboBox,
        QFileDialog,
        QTableWidget,
        QTableWidgetItem,
    )
except Exception:  # pragma: no cover - provide minimal stubs for tests without PyQt
    class _Stub:
        def __init__(self, *a, **k):
            pass

        def addWidget(self, *a, **k):
            pass

        def setLayout(self, *a, **k):
            pass

        def setText(self, *a, **k):
            pass

        def text(self):
            return ""

        def addItems(self, *a, **k):
            pass

        def currentText(self):
            return ""

        def setRowCount(self, *a, **k):
            pass

        def setColumnCount(self, *a, **k):
            pass

        def setHorizontalHeaderLabels(self, *a, **k):
            pass

        def setItem(self, *a, **k):
            pass

    QWidget = QVBoxLayout = QHBoxLayout = QLabel = QPushButton = QLineEdit = QComboBox = QFileDialog = QTableWidget = QTableWidgetItem = _Stub

from abtest_core.validation import validate_dataframe, ValidationError
from abtest_core.types import DataSchema
from .viewmodel import WizardViewModel


class StepData(QWidget):
    """Widget allowing the user to load data and select column mapping."""

    def __init__(self, vm: WizardViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.vm = vm
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("ui.wizard.step_data.title")))

        file_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        load_btn = QPushButton("…")
        load_btn.clicked.connect(self._choose_file)
        file_row.addWidget(self.path_edit)
        file_row.addWidget(load_btn)
        layout.addLayout(file_row)

        map_row = QHBoxLayout()
        self.group_combo = QComboBox()
        self.metric_combo = QComboBox()
        self.pre_combo = QComboBox()
        map_row.addWidget(QLabel(self.tr("ui.wizard.step_data.group")))
        map_row.addWidget(self.group_combo)
        map_row.addWidget(QLabel(self.tr("ui.wizard.step_data.metric")))
        map_row.addWidget(self.metric_combo)
        map_row.addWidget(QLabel(self.tr("ui.wizard.step_data.preperiod")))
        map_row.addWidget(self.pre_combo)
        layout.addLayout(map_row)

        self.preview = QTableWidget()
        layout.addWidget(self.preview)

    # File loading helpers -------------------------------------------------
    def _choose_file(self) -> None:  # pragma: no cover - GUI only
        try:
            path, _ = QFileDialog.getOpenFileName(self, "CSV", "", "CSV Files (*.csv)")
        except Exception:
            path = ""
        if path:
            self.path_edit.setText(path)
            self.load_csv(path)

    def load_csv(self, path: str) -> None:
        """Load dataframe from a CSV file and show preview."""
        try:
            df = pd.read_csv(path)
        except Exception:
            self.vm.errors.append({"title": "failed_to_load", "details": path})
            return
        self.vm.df = df
        cols = list(df.columns)
        self.group_combo.addItems(cols)
        self.metric_combo.addItems(cols)
        self.pre_combo.addItems(["" ] + cols)
        try:
            self.preview.setRowCount(min(len(df), 5))
            self.preview.setColumnCount(len(cols))
            self.preview.setHorizontalHeaderLabels(cols)
            for r in range(min(len(df), 5)):
                for c, col in enumerate(cols):
                    self.preview.setItem(r, c, QTableWidgetItem(str(df.iloc[r, c])))
        except Exception:  # pragma: no cover - stubs
            pass

    def validate(self) -> bool:
        """Validate dataframe and selected columns."""
        if self.vm.df is None:
            self.vm.errors.append({"title": "no_dataframe"})
            return False
        g = self.group_combo.currentText() or "group"
        m = self.metric_combo.currentText() or "metric"
        p = self.pre_combo.currentText() or None
        schema = DataSchema(
            group_col=g,
            metric_col=m,
            preperiod_metric_col=p,
        )
        try:
            self.vm.df = validate_dataframe(self.vm.df, schema)
            rename_map = {g: "group", m: "metric"}
            if p:
                rename_map[p] = p
            self.vm.df = self.vm.df.rename(columns=rename_map)
            self.vm.preperiod_col = p
        except ValidationError as e:
            self.vm.errors.append(e.to_dict())
            return False
        return True
