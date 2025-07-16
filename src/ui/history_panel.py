"""History panel with undo/redo and share functionality."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from migrations_runner import run_migrations
from utils.config import config

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QMessageBox,
    )
    from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
except Exception:  # pragma: no cover - allow running tests without PyQt
    QWidget = type("QWidget", (), {"__init__": lambda self, *a, **k: None})
    QVBoxLayout = QHBoxLayout = type(
        "Layout",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "addWidget": lambda *a, **k: None,
            "addLayout": lambda *a, **k: None,
            "setContentsMargins": lambda *a, **k: None,
        },
    )
    QPushButton = QTableWidget = QTableWidgetItem = QMessageBox = type(
        "Widget",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setText": lambda *a, **k: None,
            "clicked": type("Sig", (), {"connect": lambda *a, **k: None})(),
            "setToolTip": lambda *a, **k: None,
            "setRange": lambda *a, **k: None,
            "setValue": lambda *a, **k: None,
            "setSortingEnabled": lambda *a, **k: None,
            "setHorizontalHeaderLabels": lambda *a, **k: None,
            "insertRow": lambda *a, **k: None,
            "setItem": lambda *a, **k: None,
            "setCellWidget": lambda *a, **k: None,
            "removeRow": lambda *a, **k: None,
            "item": lambda *a, **k: None,
            "selectionModel": lambda self: type(
                "SelModel",
                (),
                {"selectedRows": lambda *a, **k: []},
            )(),
            "setRowCount": lambda *a, **k: None,
            "rowCount": lambda *a, **k: 0,
            "currentRow": lambda *a, **k: 0,
            "selectRow": lambda *a, **k: None,
        },
    )

    class DummyDt:
        def toString(self) -> str:
            return ""

    QDateTime = type(
        "QDateTime", (), {"currentDateTime": staticmethod(lambda: DummyDt())}
    )
    Qt = type("Qt", (), {"ItemDataRole": type("IDR", (), {"UserRole": 0})})
    pyqtSignal = lambda *a, **k: lambda *args, **kw: None


class HistoryPanel(QWidget):
    """Widget showing session states with undo/redo and share buttons."""

    state_loaded = pyqtSignal(dict)

    def __init__(
        self, conn: sqlite3.Connection | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        path = config.get("history_db", "history.db")
        self.conn = conn or sqlite3.connect(path)
        run_migrations(self.conn)

        self._states: List[Dict[str, Any]] = []
        self._index: int = -1

        self.undo_button = QPushButton("Undo")
        self.redo_button = QPushButton("Redo")
        self.share_button = QPushButton("Share")
        self.delete_button = QPushButton("Delete selected")
        self.table = QTableWidget(0, 3)
        if hasattr(self.table, "setHorizontalHeaderLabels"):
            self.table.setHorizontalHeaderLabels(["Timestamp", "Test", "Result"])
        if hasattr(self.table, "setSortingEnabled"):
            self.table.setSortingEnabled(True)

        if hasattr(self.undo_button, "clicked"):
            self.undo_button.clicked.connect(self.undo_state)  # type: ignore
        if hasattr(self.redo_button, "clicked"):
            self.redo_button.clicked.connect(self.redo_state)  # type: ignore
        if hasattr(self.share_button, "clicked"):
            self.share_button.clicked.connect(self.share_state)  # type: ignore
        if hasattr(self.delete_button, "clicked"):
            self.delete_button.clicked.connect(self._on_delete_selected)  # type: ignore

        layout = QVBoxLayout(self)
        hl = QHBoxLayout()
        hl.addWidget(self.undo_button)
        hl.addWidget(self.redo_button)
        hl.addWidget(self.share_button)
        hl.addWidget(self.delete_button)
        layout.addLayout(hl)
        layout.addWidget(self.table)

        self.load_states()
        self.load_history()

    # ----- database -----

    def load_states(self) -> None:
        c = self.conn.cursor()
        c.execute("SELECT id, payload, timestamp FROM session_states ORDER BY id")
        rows = c.fetchall()
        self._states = [{"id": i, "payload": p, "timestamp": ts} for i, p, ts in rows]
        if hasattr(self.table, "setRowCount"):
            self.table.setRowCount(0)
        for row in self._states:
            if hasattr(self.table, "insertRow"):
                r = self.table.rowCount()
                self.table.insertRow(r)
                item = QTableWidgetItem(row["timestamp"])
                if hasattr(item, "setData"):
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
                self.table.setItem(r, 0, item)
        if self._states:
            self._load_state(len(self._states) - 1)

    def load_history(self) -> None:
        """Load analysis history table."""
        c = self.conn.cursor()
        c.execute("SELECT id, timestamp, test, result FROM history ORDER BY id")
        rows = c.fetchall()
        if hasattr(self.table, "setRowCount"):
            self.table.setRowCount(0)
        for rec_id, ts, test_name, res in rows:
            if hasattr(self.table, "insertRow"):
                r = self.table.rowCount()
                self.table.insertRow(r)
                try:
                    ts_fmt = datetime.fromisoformat(ts).strftime("%d.%m.%Y %H:%M")
                except Exception:
                    ts_fmt = ts
                item_ts = QTableWidgetItem(ts_fmt)
                if hasattr(item_ts, "setData"):
                    item_ts.setData(Qt.ItemDataRole.UserRole, rec_id)
                self.table.setItem(r, 0, item_ts)
                self.table.setItem(r, 1, QTableWidgetItem(test_name))
                try:
                    res_dict = json.loads(res)
                    res_text = ", ".join(f"{k}: {v}" for k, v in res_dict.items())
                except Exception:
                    res_text = res
                self.table.setItem(r, 2, QTableWidgetItem(res_text))

    def add_state(self, payload: Dict[str, Any]) -> None:
        ts = ""
        try:
            ts = QDateTime.currentDateTime().toString()
        except Exception:
            pass
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO session_states(payload, timestamp) VALUES(?,?)",
            (json.dumps(payload), ts),
        )
        self.conn.commit()
        self.load_states()

    def _load_state(self, index: int) -> None:
        if index < 0 or index >= len(self._states):
            return
        self._index = index
        payload = self._states[index]["payload"]
        try:
            data = json.loads(payload)
        except Exception:
            data = {}
        if hasattr(self.state_loaded, "emit"):
            self.state_loaded.emit(data)  # type: ignore
        elif callable(self.state_loaded):
            self.state_loaded(data)  # type: ignore
        if hasattr(self.table, "selectRow"):
            self.table.selectRow(index)

    # ----- controls -----
    def undo_state(self) -> None:
        if self._index > 0:
            self._load_state(self._index - 1)

    def redo_state(self) -> None:
        if self._index < len(self._states) - 1:
            self._load_state(self._index + 1)

    def share_state(self) -> str | None:
        if self._index < 0 or self._index >= len(self._states):
            return None
        state_id = self._states[self._index]["id"]
        link = f"abtest://load?state={state_id}"
        qr_text = ""
        try:
            import pyqrcode  # type: ignore

            qr = pyqrcode.create(link)
            qr_text = qr.terminal(quiet_zone=1)
        except Exception:
            pass
        msg = link if not qr_text else f"{link}\n{qr_text}"
        try:
            QMessageBox.information(self, "Share", msg)
        except Exception:
            pass
        return link

    def load_from_link(self, link: str) -> None:
        if "state=" not in link:
            return
        try:
            state_id = int(link.split("state=")[1])
        except Exception:
            return
        for idx, st in enumerate(self._states):
            if st["id"] == state_id:
                self._load_state(idx)
                return
        c = self.conn.cursor()
        row = c.execute(
            "SELECT id, payload, timestamp FROM session_states WHERE id=?",
            (state_id,),
        ).fetchone()
        if row:
            self._states.append({"id": row[0], "payload": row[1], "timestamp": row[2]})
            if hasattr(self.table, "insertRow"):
                r = self.table.rowCount()
                self.table.insertRow(r)
                item = QTableWidgetItem(row[2])
                if hasattr(item, "setData"):
                    item.setData(Qt.ItemDataRole.UserRole, row[0])
                self.table.setItem(r, 0, item)
            self._load_state(len(self._states) - 1)

    def _on_delete_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Ничего не выбрано"))
            return
        indexes = sorted((idx.row() for idx in rows), reverse=True)
        ids = []
        for row in indexes:
            item = self.table.item(row, 0)
            if item is not None:
                val = item.data(Qt.ItemDataRole.UserRole)
                if val is not None:
                    ids.append((val,))
        if ids:
            c = self.conn.cursor()
            c.executemany("DELETE FROM history WHERE id=?", ids)
            self.conn.commit()
        for row in indexes:
            self.table.removeRow(row)
        self.load_history()
