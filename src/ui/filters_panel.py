"""UI panel for dataset filtering and live metric updates."""

from typing import Any, Dict, List

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QComboBox,
        QLineEdit,
    )
    from PyQt6.QtCore import pyqtSignal
except Exception:  # pragma: no cover - allow running tests without PyQt
    QWidget = type("QWidget", (), {})
    QVBoxLayout = QHBoxLayout = type("Layout", (), {"addWidget": lambda *a, **k: None, "setContentsMargins": lambda *a, **k: None})
    QLabel = QComboBox = QLineEdit = type("Widget", (), {"currentText": lambda self: "", "text": lambda self: "", "addItem": lambda *a, **k: None, "addItems": lambda *a, **k: None, "setPlaceholderText": lambda *a, **k: None, "setEditable": lambda *a, **k: None})
    pyqtSignal = lambda *a, **k: None

from stats.ab_test import evaluate_abn_test
from utils import segment_data


class FiltersPanel(QWidget):
    """Panel providing simple attribute filters."""

    metrics_updated = pyqtSignal(dict)

    def __init__(self, records: List[Dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._records = records

        self.device_combo = QComboBox()
        self.country_combo = QComboBox()
        self.utm_combo = QComboBox()
        self.trait_edit = QLineEdit()

        for combo in (self.device_combo, self.country_combo, self.utm_combo):
            combo.addItem("")
            combo.setEditable(False)

        self.trait_edit.setPlaceholderText("custom trait=value")

        self._init_values()
        self._build_ui()
        self._connect_signals()
        self._recalculate()

    def _init_values(self) -> None:
        devices = sorted({r.get("device", "") for r in self._records if r.get("device")})
        countries = sorted({r.get("country", "") for r in self._records if r.get("country")})
        utms = sorted({r.get("utm", "") for r in self._records if r.get("utm")})

        self.device_combo.addItems(devices)
        self.country_combo.addItems(countries)
        self.utm_combo.addItems(utms)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        def row(lbl: str, widget: Any) -> QWidget:
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.addWidget(QLabel(lbl))
            hl.addWidget(widget)
            return w

        layout.addWidget(row("Device", self.device_combo))
        layout.addWidget(row("Country", self.country_combo))
        layout.addWidget(row("UTM", self.utm_combo))
        layout.addWidget(row("Trait", self.trait_edit))

    def _connect_signals(self) -> None:
        for combo in (self.device_combo, self.country_combo, self.utm_combo):
            if hasattr(combo, "currentTextChanged"):
                combo.currentTextChanged.connect(self._recalculate)  # type: ignore
        if hasattr(self.trait_edit, "textChanged"):
            self.trait_edit.textChanged.connect(self._recalculate)  # type: ignore

    # ----- metric calculations -----
    def _recalculate(self) -> None:
        filters: Dict[str, Any] = {}
        dev = self.device_combo.currentText()
        if dev:
            filters["device"] = dev
        country = self.country_combo.currentText()
        if country:
            filters["country"] = country
        utm = self.utm_combo.currentText()
        if utm:
            filters["utm"] = utm
        trait_raw = self.trait_edit.text()
        if trait_raw and "=" in trait_raw:
            key, val = trait_raw.split("=", 1)
            filters[key.strip()] = val.strip()

        subset = segment_data(self._records, **filters)
        stats = self._calc_metrics(subset)
        if callable(self.metrics_updated):
            self.metrics_updated.emit(stats)  # type: ignore

    def _calc_metrics(self, subset: List[Dict[str, Any]]) -> Dict[str, Any]:
        group_a = [r for r in subset if r.get("group") == "A"]
        group_b = [r for r in subset if r.get("group") == "B"]
        users_a = len(group_a)
        users_b = len(group_b)
        conv_a = sum(1 for r in group_a if r.get("converted"))
        conv_b = sum(1 for r in group_b if r.get("converted"))
        if users_a and users_b:
            res = evaluate_abn_test(users_a, conv_a, users_b, conv_b)
        else:
            res = {
                "cr_a": 0.0,
                "cr_b": 0.0,
                "p_value_ab": 1.0,
                "significant_ab": False,
                "winner": "",
            }
        res.update({"users_a": users_a, "users_b": users_b, "conv_a": conv_a, "conv_b": conv_b})
        return res
