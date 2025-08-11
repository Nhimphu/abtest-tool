"""UI panel for dataset filtering and live metric updates."""

from typing import Any, Dict, List
import re

from abtest_core.utils import lazy_import

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
    QVBoxLayout = QHBoxLayout = type(
        "Layout",
        (),
        {"addWidget": lambda *a, **k: None, "setContentsMargins": lambda *a, **k: None},
    )
    QLabel = QComboBox = QLineEdit = type(
        "Widget",
        (),
        {
            "currentText": lambda self: "",
            "text": lambda self: "",
            "addItem": lambda *a, **k: None,
            "addItems": lambda *a, **k: None,
            "setPlaceholderText": lambda *a, **k: None,
            "setEditable": lambda *a, **k: None,
        },
    )
    pyqtSignal = lambda *a, **k: None

from utils import segment_data


class FiltersPanel(QWidget):
    """Panel providing simple attribute filters."""

    metrics_updated = pyqtSignal(dict)

    def __init__(
        self, records: List[Dict[str, Any]], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._records = records
        try:  # Optional dependency used for query filtering
            pd = lazy_import("pandas")
        except Exception:  # pragma: no cover - allow running without pandas
            pd = None  # type: ignore

        self.device_combo = QComboBox()
        self.country_combo = QComboBox()
        self.utm_edit = QLineEdit()
        self.trait_edit = QLineEdit()

        for combo in (self.device_combo, self.country_combo):
            combo.addItem("")
            combo.setEditable(False)

        self.utm_edit.setPlaceholderText("utm_campaign")
        self.trait_edit.setPlaceholderText("custom trait=value")

        if pd is not None and hasattr(pd, "DataFrame"):
            try:
                self._df = pd.DataFrame(records)  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover - fall back if malformed
                self._df = None
        else:  # pragma: no cover - pandas missing
            self._df = None

        self._init_values()
        self._build_ui()
        self._connect_signals()
        self._recalculate()

    def _init_values(self) -> None:
        devices = sorted(
            {r.get("device", "") for r in self._records if r.get("device")}
        )
        countries = sorted(
            {r.get("country", "") for r in self._records if r.get("country")}
        )
        self.device_combo.addItems(devices)
        self.country_combo.addItems(countries)

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
        layout.addWidget(row("UTM", self.utm_edit))
        layout.addWidget(row("Trait", self.trait_edit))

    def _connect_signals(self) -> None:
        for combo in (self.device_combo, self.country_combo):
            if hasattr(combo, "currentTextChanged"):
                combo.currentTextChanged.connect(self._recalculate)  # type: ignore
        for edit in (self.utm_edit, self.trait_edit):
            if hasattr(edit, "textChanged"):
                edit.textChanged.connect(self._recalculate)  # type: ignore

    def _apply_df_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return ``records`` subset using ``pandas.DataFrame.query``."""

        if self._df is None or not filters:
            return self._records

        conditions = []
        local_vars: Dict[str, Any] = {}
        for i, (key, value) in enumerate(filters.items()):
            if key not in self._df.columns:
                continue
            if not re.fullmatch(r"\w+", key):
                continue
            if isinstance(value, str) and re.search(r"[\"';]", value):
                # basic sanitation for unsafe characters
                continue
            var = f"val{i}"
            local_vars[var] = value
            conditions.append(f"`{key}` == @{var}")

        if not conditions:
            return self._records

        query_str = " and ".join(conditions)
        try:
            df_subset = self._df.query(query_str, local_dict=local_vars)
        except Exception:  # pragma: no cover - invalid query
            return []
        return df_subset.to_dict("records")

    # ----- metric calculations -----
    def _recalculate(self) -> None:
        filters: Dict[str, Any] = {}
        dev = self.device_combo.currentText()
        if dev:
            filters["device"] = dev
        country = self.country_combo.currentText()
        if country:
            filters["country"] = country
        utm = self.utm_edit.text().strip()
        if utm:
            filters["utm"] = utm
        trait_raw = self.trait_edit.text()
        if trait_raw and "=" in trait_raw:
            key, val = trait_raw.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key and val:
                filters[key] = val

        if self._df is not None:
            subset = self._apply_df_filters(filters)
        else:
            subset = segment_data(self._records, **filters)

        stats = self._calc_metrics(subset)
        if callable(self.metrics_updated):
            self.metrics_updated.emit(stats)  # type: ignore

    def _calc_metrics(self, subset: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats_mod = lazy_import("stats.ab_test")
        evaluate_abn_test = stats_mod.evaluate_abn_test
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
        res.update(
            {"users_a": users_a, "users_b": users_b, "conv_a": conv_a, "conv_b": conv_b}
        )
        return res
