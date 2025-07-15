# ui_mainwindow.py

import sys
import sqlite3
import os

from migrations_runner import run_migrations
import csv
from typing import Dict
import json
import urllib.request

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QTextBrowser,
    QComboBox,
    QGroupBox,
)
from PyQt6.QtGui import (
    QPalette,
    QColor,
    QIntValidator,
    QDoubleValidator,
    QAction,
)

try:
    from PyQt6.QtGui import QIcon
except Exception:  # pragma: no cover - optional

    class QIcon:
        def __init__(self, *a, **k):
            pass


try:
    from PyQt6.QtCore import Qt, QDateTime, QEvent, QDir, QTranslator, QLocale
except Exception:  # pragma: no cover - optional
    from PyQt6.QtCore import Qt, QDateTime  # type: ignore

    class QEvent:
        class Type:
            FocusIn = 0
            FocusOut = 1

    class QDir:
        @staticmethod
        def addSearchPath(*a, **k):
            pass

    class QTranslator:
        def load(self, *a, **k):
            return False

    class QLocale:
        @staticmethod
        def system():
            return type("QLocale", (), {"name": lambda: "en_US"})()


from .widgets import with_help_label

from .login import LoginDialog

try:
    from PyQt6.QtWidgets import QStatusBar
except Exception:  # pragma: no cover - optional

    class QStatusBar:
        def __init__(self, *a, **k):
            pass

        def showMessage(self, *a, **k):
            pass

        def clearMessage(self):
            pass


try:  # Optional dependency
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore
except Exception:  # pragma: no cover - optional
    QWebEngineView = None

from stats.ab_test import (
    required_sample_size,
    calculate_mde,
    evaluate_abn_test,
    bayesian_analysis,
    run_aa_simulation,
    run_sequential_analysis,
    run_obrien_fleming,
    calculate_roi,
    srm_check,
    cuped_adjustment,
)
import plugin_loader
from plots import (
    plot_bayesian_posterior,
    plot_confidence_intervals,
    plot_power_curve,
    plot_bootstrap_distribution,
    plot_alpha_spending,
    save_plot,
)
import utils
from pathlib import Path

# Register path prefix for icons used via the Qt resource scheme
QDir.addSearchPath("resources", str(Path(__file__).resolve().parent / "resources"))


def show_error(parent, msg):
    QMessageBox.critical(parent, "Ошибка", msg)


class PlotWindow:
    """Display Plotly figures in-app when possible."""

    def __init__(self, parent=None):
        self.parent = parent
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            self._view = None
        else:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout

            dlg = QDialog(parent)
            dlg.setWindowTitle(dlg.tr("Plot"))
            dlg.resize(700, 500)
            layout = QVBoxLayout(dlg)
            self._view = QWebEngineView(dlg)
            layout.addWidget(self._view)
            self._dialog = dlg

    def display_plot(self, fig):
        import tempfile
        import webbrowser
        import plotly.io as pio

        html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
        if getattr(self, "_view", None):
            self._view.setHtml(html)
            self._dialog.exec()
        else:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as f:
                f.write(html)
                path = f.name
            webbrowser.open(f"file://{path}")


class AddDataSourceDialog:
    """Dialog to collect connection information for a new data source."""

    def __init__(self, parent=None):
        from PyQt6 import QtWidgets

        QDialog = getattr(
            QtWidgets,
            "QDialog",
            type(
                "QDialog",
                (),
                {
                    "__init__": lambda self, *a, **k: None,
                    "exec": lambda self: 0,
                    "accept": lambda self: None,
                    "reject": lambda self: None,
                    "setWindowTitle": lambda self, *a, **k: None,
                    "tr": lambda self, text: text,
                },
            ),
        )
        if hasattr(QtWidgets, "QDialogButtonBox"):
            QDialogButtonBox = QtWidgets.QDialogButtonBox
        else:  # pragma: no cover - used in tests without PyQt installed

            class DummySig:
                def connect(self, *a, **k):
                    pass

            class QDialogButtonBox:
                class StandardButton:
                    Ok = 1
                    Cancel = 2

                def __init__(self, *a, **k):
                    self.accepted = DummySig()
                    self.rejected = DummySig()

        def _layout_stub(*a, **k):
            return type(
                "Layout",
                (),
                {
                    "setContentsMargins": lambda *a, **k: None,
                    "addWidget": lambda *a, **k: None,
                },
            )()

        QVBoxLayout_cls = getattr(QtWidgets, "QVBoxLayout", _layout_stub)
        if not hasattr(QVBoxLayout_cls, "addWidget"):
            QVBoxLayout_cls = _layout_stub
        QHBoxLayout_cls = getattr(QtWidgets, "QHBoxLayout", _layout_stub)
        if not hasattr(QHBoxLayout_cls, "addWidget"):
            QHBoxLayout_cls = _layout_stub
        QLabel = getattr(
            QtWidgets,
            "QLabel",
            lambda *a, **k: type("QLabel", (), {"setText": lambda *a, **k: None})(),
        )
        QLineEdit = getattr(
            QtWidgets,
            "QLineEdit",
            lambda *a, **k: type(
                "QLineEdit",
                (),
                {"text": lambda self: "", "setText": lambda *a, **k: None},
            )(),
        )
        QComboBox = getattr(
            QtWidgets,
            "QComboBox",
            lambda *a, **k: type(
                "QComboBox",
                (),
                {"addItems": lambda *a, **k: None, "currentText": lambda self: ""},
            )(),
        )
        if not hasattr(QComboBox, "addItems"):
            QComboBox = type(
                "QComboBox",
                (),
                {"addItems": lambda *a, **k: None, "currentText": lambda self: ""},
            )

        class _Sig:
            def connect(self, *a, **k):
                pass

        QPushButton = getattr(
            QtWidgets,
            "QPushButton",
            lambda *a, **k: type("QPushButton", (), {"clicked": _Sig()})(),
        )
        QWidget = getattr(
            QtWidgets,
            "QWidget",
            lambda *a, **k: type(
                "QWidget",
                (),
                {"setLayout": lambda *a, **k: None, "setVisible": lambda *a, **k: None},
            )(),
        )
        if not hasattr(QWidget, "setVisible"):
            QWidget = type(
                "QWidget",
                (),
                {"setLayout": lambda *a, **k: None, "setVisible": lambda *a, **k: None},
            )

        self.parent = parent
        self._dialog = QDialog(parent)
        if parent is not None:
            try:
                self._dialog.setPalette(parent.palette())
                self._dialog.setStyleSheet(parent.styleSheet())
            except Exception:
                pass
        try:
            layout = QVBoxLayout_cls(self._dialog)
        except Exception:
            layout = QVBoxLayout_cls()
        self._dialog.setWindowTitle(self._dialog.tr("Add Data Source"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["BigQuery", "Redshift"])
        lbl = QLabel()
        if hasattr(lbl, "setText"):
            lbl.setText(self._dialog.tr("Type"))
        layout.addWidget(lbl)
        layout.addWidget(self.type_combo)

        self.rows = {}
        for name in [
            "Project",
            "Credentials",
            "Host",
            "Port",
            "Database",
            "User",
            "Password",
        ]:
            row = QWidget()
            hl = QHBoxLayout_cls(row)
            hl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel()
            if hasattr(lbl, "setText"):
                lbl.setText(self._dialog.tr(name))
            fld = QLineEdit()
            if hasattr(fld, "setText"):
                fld.setText("5439" if name == "Port" else "")
            if name == "Password" and hasattr(QLineEdit, "EchoMode"):
                fld.setEchoMode(QLineEdit.EchoMode.Password)
            hl.addWidget(lbl)
            hl.addWidget(fld)
            layout.addWidget(row)
            self.rows[name.lower()] = (row, fld)
        self.rs_host = self.rows["host"][1]
        self.rs_port = self.rows["port"][1]
        self.rs_db = self.rows["database"][1]
        self.rs_user = self.rows["user"][1]
        self.rs_pass = self.rows["password"][1]
        self.bq_project = self.rows["project"][1]
        self.bq_creds = self.rows["credentials"][1]

        self.test_button = QPushButton()
        if hasattr(self.test_button, "setText"):
            self.test_button.setText(self._dialog.tr("Test Connection"))
        if hasattr(self.test_button, "clicked"):
            self.test_button.clicked.connect(self._on_test)  # type: ignore
        layout.addWidget(self.test_button)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self._dialog.accept)
        self.buttons.rejected.connect(self._dialog.reject)

        if hasattr(self.type_combo, "currentTextChanged"):
            self.type_combo.currentTextChanged.connect(self._update_fields)  # type: ignore
        self._update_fields(self.type_combo.currentText())

    def _on_test(self) -> bool:
        """Attempt to connect using provided credentials."""
        try:
            from utils.connectors import BigQueryConnector, RedshiftConnector

            if self.type_combo.currentText() == "BigQuery":
                conn = BigQueryConnector(
                    self.bq_project.text(),
                    self.bq_creds.text(),
                )
            else:
                conn = RedshiftConnector(
                    host=self.rs_host.text(),
                    port=int(self.rs_port.text() or 0),
                    database=self.rs_db.text(),
                    user=self.rs_user.text(),
                    password=self.rs_pass.text(),
                )
            conn.query("SELECT 1")
            if hasattr(conn, "close"):
                conn.close()
        except Exception as e:  # pragma: no cover - optional deps
            if hasattr(QMessageBox, "critical"):
                QMessageBox.critical(
                    self._dialog,
                    "Error",
                    f"{self._dialog.tr('Connection failed')}: {e}",
                )
            return False
        if hasattr(QMessageBox, "information"):
            QMessageBox.information(
                self._dialog,
                "Success",
                self._dialog.tr("Connection successful"),
            )
        return True

    def _update_fields(self, text: str) -> None:
        is_bq = text == "BigQuery"
        for key in ["project", "credentials"]:
            self.rows[key][0].setVisible(is_bq)
        for key in ["host", "port", "database", "user", "password"]:
            self.rows[key][0].setVisible(not is_bq)
        if hasattr(self._dialog, "adjustSize"):
            self._dialog.adjustSize()
        if hasattr(self._dialog, "setFixedSize") and hasattr(self._dialog, "sizeHint"):
            self._dialog.setFixedSize(self._dialog.sizeHint())

    def data(self) -> Dict[str, str]:
        if self.type_combo.currentText() == "BigQuery":
            return {
                "type": "bigquery",
                "project": self.bq_project.text(),
                "credentials": self.bq_creds.text(),
            }
        return {
            "type": "redshift",
            "host": self.rs_host.text(),
            "port": self.rs_port.text(),
            "database": self.rs_db.text(),
            "user": self.rs_user.text(),
            "password": self.rs_pass.text(),
        }

    def exec(self) -> int:
        return self._dialog.exec()


class ABTestWindow(QMainWindow):
    def __init__(self, cfg=None, translator=None, lang=None):
        super().__init__()

        from utils.config import config as _cfg

        self._config = cfg or _cfg

        # Language setup
        self.translator = translator or QTranslator()
        self.lang = lang or QLocale.system().name().split("_")[0]
        if translator is None:
            self._load_translation(self.lang)
        else:
            QApplication.instance().installTranslator(self.translator)

        # Начальные настройки темы
        self.is_dark = self._config.get("theme", "dark") == "dark"
        if self.is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

        self.setWindowTitle(self.tr("Ultimate A/B Testing Tool"))
        self.setGeometry(100, 100, 1000, 800)

        # Инициализируем историю
        self._init_history_db()
        # Создаём виджеты
        self._prepare_widgets()
        # Строим интерфейс
        self._build_ui()
        # Устанавливаем фильтры событий
        self._install_event_filters()
        # Загружаем историю
        self._load_history()
        # Обновляем тексты
        self.update_ui_text()
        self.sources = []
        self.token = None
        self.refresh_token = None

    def closeEvent(self, event):
        """Ensure database connection is closed on exit."""
        try:
            self.conn.close()
        finally:
            super().closeEvent(event)

    # ————— История (SQLite) —————

    def _init_history_db(self):
        path = self._config.get("history_db", "history.db")
        self.conn = sqlite3.connect(path)
        run_migrations(self.conn)

    def _load_history(self):
        c = self.conn.cursor()
        c.execute("SELECT id,timestamp,test,result FROM history ORDER BY id")
        rows = c.fetchall()
        self.history_table.setRowCount(0)
        for rec_id, ts, test, res in rows:
            r = self.history_table.rowCount()
            self.history_table.insertRow(r)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.CheckState.Unchecked)
            chk.setData(Qt.ItemDataRole.UserRole, rec_id)
            self.history_table.setItem(r, 0, chk)
            self.history_table.setItem(r, 1, QTableWidgetItem(ts))
            self.history_table.setItem(r, 2, QTableWidgetItem(test))
            self.history_table.setItem(r, 3, QTableWidgetItem(res))
            pb = self._build_inline_chart(res)
            self.history_table.setCellWidget(r, 4, pb)

    def _add_history(self, name, content):
        ts = QDateTime.currentDateTime().toString()
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO history(timestamp,test,result) VALUES(?,?,?)",
            (ts, name, content.replace("<pre>", "").replace("</pre>", "")),
        )
        self.conn.commit()
        rec_id = c.lastrowid
        r = self.history_table.rowCount()
        self.history_table.insertRow(r)
        chk = QTableWidgetItem()
        chk.setCheckState(Qt.CheckState.Unchecked)
        chk.setData(Qt.ItemDataRole.UserRole, rec_id)
        self.history_table.setItem(r, 0, chk)
        self.history_table.setItem(r, 1, QTableWidgetItem(ts))
        self.history_table.setItem(r, 2, QTableWidgetItem(name))
        self.history_table.setItem(
            r, 3, QTableWidgetItem(content.replace("<pre>", "").replace("</pre>", ""))
        )
        pb = self._build_inline_chart(content)
        self.history_table.setCellWidget(r, 4, pb)

    def _on_delete_selected(self):
        """Delete currently selected rows from history."""
        model = self.history_table.selectionModel()
        if not model or not model.selectedRows():
            QMessageBox.warning(self, "Warning", "Nothing selected")
            return
        rows = sorted((idx.row() for idx in model.selectedRows()), reverse=True)
        for row in rows:
            item = self.history_table.item(row, 0)
            if item is not None:
                rec_id = item.data(Qt.ItemDataRole.UserRole)
                self.conn.cursor().execute("DELETE FROM history WHERE id=?", (rec_id,))
        self.conn.commit()
        for row in rows:
            self.history_table.removeRow(row)
        self._load_history()

    def _clear_all_history(self):
        self.conn.cursor().execute("DELETE FROM history")
        self.conn.commit()
        self.history_table.setRowCount(0)

    def _filter_history(self, text):
        text = text.lower()
        for r in range(self.history_table.rowCount()):
            show = False
            for c in range(1, self.history_table.columnCount() - 1):
                item = self.history_table.item(r, c)
                if item and text in item.text().lower():
                    show = True
                    break
            self.history_table.setRowHidden(r, not show)

    def _build_inline_chart(self, text):
        pb = QProgressBar()
        pb.setRange(0, 100)
        pb.setTextVisible(False)
        pb.setValue(abs(hash(text)) % 100)
        return pb

    def _export_history_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save History CSV", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        c = self.conn.cursor()
        c.execute("SELECT timestamp,test,result FROM history ORDER BY id")
        rows = c.fetchall()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Timestamp", "Test", "Result"])
                w.writerows(rows)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def _export_history_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save History Markdown", "", "Markdown Files (*.md)"
        )
        if not path:
            return
        c = self.conn.cursor()
        c.execute("SELECT timestamp, test, result FROM history ORDER BY id")
        rows = c.fetchall()
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("| Timestamp | Test | Result |\n")
                f.write("|---|---|---|\n")
                for ts, test, result in rows:
                    f.write(f"| {ts} | {test} | {result} |\n")
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def _save_current_plot(self):
        if not self._last_fig:
            QMessageBox.information(self, "Info", "No plot to save")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "HTML Files (*.html)"
        )
        if not path:
            return
        try:
            import plotly.io as pio

            pio.write_html(
                self._last_fig,
                file=path,
                auto_open=False,
                include_plotlyjs="cdn",
            )
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:  # pragma: no cover - file errors
            show_error(self, str(e))

    # ————— Подготовка виджетов —————

    def _prepare_widgets(self):
        # Слайдеры
        self.baseline_slider = QSlider(Qt.Orientation.Horizontal)
        self.baseline_slider.setRange(0, 1000)
        self.baseline_slider.setValue(40)
        self.baseline_slider.valueChanged.connect(self.update_ui_text)
        self.baseline_slider.setToolTip(self.tr("Baseline conversion"))
        self.baseline_slider.setStatusTip(self.tr("Baseline conversion"))
        self.baseline_label = QLabel()

        self.uplift_slider = QSlider(Qt.Orientation.Horizontal)
        self.uplift_slider.setRange(0, 1000)
        self.uplift_slider.setValue(100)
        self.uplift_slider.valueChanged.connect(self.update_ui_text)
        self.uplift_slider.setToolTip(self.tr("Expected uplift of variant"))
        self.uplift_slider.setStatusTip(self.tr("Expected uplift of variant"))
        self.uplift_label = QLabel()

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(5)
        self.alpha_slider.valueChanged.connect(self.update_ui_text)
        self.alpha_slider.setToolTip(self.tr("Significance level"))
        self.alpha_slider.setStatusTip(self.tr("Significance level"))
        self.alpha_label = QLabel()

        self.power_slider = QSlider(Qt.Orientation.Horizontal)
        self.power_slider.setRange(0, 100)
        self.power_slider.setValue(90)
        self.power_slider.valueChanged.connect(self.update_ui_text)
        self.power_slider.setToolTip(self.tr("Statistical power"))
        self.power_slider.setStatusTip(self.tr("Statistical power"))
        self.power_label = QLabel()

        # Кнопка расчёта
        self.calc_button = QPushButton()
        self.calc_button.clicked.connect(self.calculate_sample_size)
        self.calc_button.setToolTip(self.tr("Calculate sample size"))
        self.calc_button.setStatusTip(self.tr("Calculate sample size"))

        # Поля A/B/C
        for G in ["A", "B", "C"]:
            lbl_u = QLabel()
            fld_u = QLineEdit("1000")
            fld_u.setValidator(QIntValidator(1, 10**9))
            lbl_c = QLabel()
            fld_c = QLineEdit("50")
            fld_c.setValidator(QIntValidator(0, 10**9))
            setattr(self, f"users_{G}_label", lbl_u)
            setattr(self, f"users_{G}_var", fld_u)
            setattr(self, f"conv_{G}_label", lbl_c)
            setattr(self, f"conv_{G}_var", fld_c)

        # Кнопки анализа
        self.analyze_button = QPushButton()
        self.analyze_button.setIcon(QIcon("resources:run.svg"))
        self.analyze_button.clicked.connect(self._on_analyze)
        self.analyze_button.setToolTip(self.tr("Run A/B/n test"))
        self.analyze_button.setStatusTip(self.tr("Run A/B/n test"))
        self.conf_button = QPushButton()
        self.conf_button.clicked.connect(self._on_plot_confidence_intervals)
        self.conf_button.setToolTip(self.tr("Plot confidence intervals"))
        self.conf_button.setStatusTip(self.tr("Plot confidence intervals"))
        self.bayes_button = QPushButton()
        self.bayes_button.clicked.connect(self._on_bayes)
        self.bayes_button.setToolTip(self.tr("Run Bayesian analysis"))
        self.bayes_button.setStatusTip(self.tr("Run Bayesian analysis"))
        if not plugin_loader.get_plugin("bayesian"):
            self.bayes_button.setEnabled(False)
        self.aa_button = QPushButton()
        self.aa_button.clicked.connect(self._on_run_aa)
        self.aa_button.setToolTip(self.tr("Run A/A simulation"))
        self.aa_button.setStatusTip(self.tr("Run A/A simulation"))
        self.seq_button = QPushButton()
        self.seq_button.clicked.connect(self._on_run_sequential)
        self.seq_button.setToolTip(self.tr("Run sequential analysis"))
        self.seq_button.setStatusTip(self.tr("Run sequential analysis"))
        self.obf_button = QPushButton()
        self.obf_button.clicked.connect(self._on_run_obrien_fleming)
        self.obf_button.setToolTip(self.tr("O'Brien-Fleming analysis"))
        self.obf_button.setStatusTip(self.tr("O'Brien-Fleming analysis"))

        # Priors для байес
        self.prior_alpha_spin = QDoubleSpinBox()
        self.prior_alpha_spin.setRange(0.1, 10.0)
        self.prior_alpha_spin.setSingleStep(0.1)
        self.prior_alpha_spin.setValue(1.0)
        self.prior_beta_spin = QDoubleSpinBox()
        self.prior_beta_spin.setRange(0.1, 10.0)
        self.prior_beta_spin.setSingleStep(0.1)
        self.prior_beta_spin.setValue(1.0)

        self.bandit_label = QLabel()
        self.bandit_combo = QComboBox()
        self.bandit_combo.addItems(["Thompson", "UCB1", "ε-greedy"])

        # ROI
        self.revenue_per_user_label = QLabel()
        self.revenue_per_user_var = QLineEdit("50")
        self.revenue_per_user_var.setValidator(QDoubleValidator(0, 1e9, 2))
        self.revenue_per_user_var.setToolTip(self.tr("Revenue per user"))
        self.traffic_cost_label = QLabel()
        self.traffic_cost_var = QLineEdit("10")
        self.traffic_cost_var.setValidator(QDoubleValidator(0, 1e9, 2))
        self.traffic_cost_var.setToolTip(self.tr("Traffic cost per user"))
        self.budget_label = QLabel()
        self.budget_var = QLineEdit("10000")
        self.budget_var.setValidator(QDoubleValidator(0, 1e12, 2))
        self.budget_var.setToolTip(self.tr("Available budget"))
        self.roi_button = QPushButton()
        self.roi_button.clicked.connect(self._on_calculate_roi)
        self.roi_button.setToolTip(self.tr("Calculate ROI"))
        self.roi_button.setStatusTip(self.tr("Calculate ROI"))

        # Графики
        self.plot_ci_button = QPushButton()
        self.plot_ci_button.clicked.connect(self._on_plot_confidence_intervals)
        self.plot_ci_button.setToolTip(self.tr("Confidence intervals plot"))
        self.plot_ci_button.setStatusTip(self.tr("Confidence intervals plot"))
        self.plot_power_button = QPushButton()
        self.plot_power_button.clicked.connect(self._on_plot_power_curve)
        self.plot_power_button.setToolTip(self.tr("Required sample size curve"))
        self.plot_power_button.setStatusTip(self.tr("Required sample size curve"))
        self.plot_alpha_button = QPushButton()
        self.plot_alpha_button.clicked.connect(self._on_plot_alpha_spending)
        self.plot_alpha_button.setToolTip(self.tr("Alpha spending plot"))
        self.plot_alpha_button.setStatusTip(self.tr("Alpha spending plot"))
        self.plot_bootstrap_button = QPushButton()
        self.plot_bootstrap_button.clicked.connect(self._on_plot_bootstrap_distribution)
        self.plot_bootstrap_button.setToolTip(self.tr("Bootstrap distribution"))
        self.plot_bootstrap_button.setStatusTip(self.tr("Bootstrap distribution"))
        self.save_plot_button = QPushButton()
        self.save_plot_button.setIcon(QIcon("resources:export.svg"))
        self.save_plot_button.clicked.connect(self._save_current_plot)
        self.save_plot_button.setToolTip(self.tr("Save last plot"))
        self.save_plot_button.setStatusTip(self.tr("Save last plot"))

        # Area to embed Plotly plots if QtWebEngine is available
        self._last_fig = None
        self.alpha_plot_view = QWebEngineView() if QWebEngineView else None
        if self.alpha_plot_view:
            self.alpha_plot_view.setZoomFactor(1.0)
            self.alpha_plot_view.setVisible(False)

        # Результаты
        self.results_text = QTextBrowser()

        # Загрузка / Очистка
        self.load_pre_exp_button = QPushButton()
        self.load_pre_exp_button.clicked.connect(
            lambda: QMessageBox.information(self, "Info", "Pre-exp not implemented")
        )
        self.load_pre_exp_button.setToolTip(self.tr("Load pre-experiment data"))
        self.load_pre_exp_button.setStatusTip(self.tr("Load pre-experiment data"))
        self.clear_button = QPushButton()
        self.clear_button.setIcon(QIcon("resources:undo.svg"))
        self.clear_button.clicked.connect(
            lambda: self.results_text.setHtml("<pre></pre>")
        )
        self.clear_button.setToolTip(self.tr("Clear results"))
        self.clear_button.setStatusTip(self.tr("Clear results"))

        # История
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(
            ["✓", "Дата", "Тест", "Результат", "⇵"]
        )
        self.history_table.setSortingEnabled(True)
        self.history_filter = QLineEdit()
        self.history_filter.setPlaceholderText(self.tr("Filter history"))
        self.history_filter.textChanged.connect(self._filter_history)
        self.delete_button = QPushButton()
        self.delete_button.clicked.connect(self._on_delete_selected)
        self.delete_button.setToolTip(self.tr("Delete selected history rows"))
        self.delete_button.setStatusTip(self.tr("Delete selected history rows"))
        self.clear_history_button = QPushButton()
        self.clear_history_button.clicked.connect(self._clear_all_history)
        self.clear_history_button.setToolTip(self.tr("Clear all history"))
        self.clear_history_button.setStatusTip(self.tr("Clear all history"))

    # ————— Построение интерфейса —————

    def _build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        ml = QVBoxLayout(cw)

        # Вкладки
        self.tab_widget = QTabWidget()
        ml.addWidget(self.tab_widget)

        # Основной
        tab_main = QWidget()
        self.tab_widget.addTab(tab_main, "")
        g = QGridLayout(tab_main)

        # Левая панель
        left = QVBoxLayout()
        # подписи для слайдеров создаются динамически
        left.addWidget(with_help_label(self.baseline_label, "Baseline conversion rate"))
        left.addWidget(self.baseline_slider)
        left.addWidget(with_help_label(self.uplift_label, "Expected uplift of variant"))
        left.addWidget(self.uplift_slider)
        left.addWidget(with_help_label(self.alpha_label, "Significance level"))
        left.addWidget(self.alpha_slider)
        left.addWidget(with_help_label(self.power_label, "Statistical power"))
        left.addWidget(self.power_slider)
        left.addWidget(self.calc_button)

        for G in ["A", "B", "C"]:
            left.addWidget(
                with_help_label(
                    getattr(self, f"users_{G}_label"),
                    f"Users in group {G}",
                )
            )
            left.addWidget(getattr(self, f"users_{G}_var"))
            left.addWidget(
                with_help_label(
                    getattr(self, f"conv_{G}_label"),
                    f"Conversions in group {G}",
                )
            )
        left.addWidget(getattr(self, f"conv_{G}_var"))

        left.addWidget(self.analyze_button)
        advanced_box = QGroupBox(self.tr("Advanced"))
        advanced_box.setCheckable(True)
        adv_layout = QVBoxLayout(advanced_box)

        alpha_prior_label = QLabel(self.tr("α-prior:"))
        beta_prior_label = QLabel(self.tr("β-prior:"))
        bandit_help = with_help_label(self.bandit_label, "Bandit strategy")
        rpu_help = with_help_label(self.revenue_per_user_label, "Revenue per user")
        cost_help = with_help_label(self.traffic_cost_label, "Traffic cost per user")
        bud_help = with_help_label(self.budget_label, "Available budget")

        adv_widgets = [
            alpha_prior_label,
            self.prior_alpha_spin,
            beta_prior_label,
            self.prior_beta_spin,
            self.bayes_button,
            bandit_help,
            self.bandit_combo,
            self.aa_button,
            self.seq_button,
            self.obf_button,
            rpu_help,
            self.revenue_per_user_var,
            cost_help,
            self.traffic_cost_var,
            bud_help,
            self.budget_var,
            self.roi_button,
        ]

        for w in adv_widgets:
            adv_layout.addWidget(w)

        def _toggle_adv(checked: bool) -> None:
            for w in adv_widgets:
                w.setVisible(checked)

        advanced_box.toggled.connect(_toggle_adv)
        _toggle_adv(advanced_box.isChecked())

        left.addWidget(advanced_box)
        left.addStretch()

        lw = QWidget()
        lw.setLayout(left)
        lw.setMaximumWidth(300)
        g.addWidget(lw, 0, 0)

        # Правая панель
        right = QVBoxLayout()
        btns = QHBoxLayout()
        for btn in [
            self.plot_ci_button,
            self.plot_power_button,
            self.plot_alpha_button,
            self.plot_bootstrap_button,
            self.save_plot_button,
        ]:
            btns.addWidget(btn)
        right.addLayout(btns)
        if self.alpha_plot_view:
            right.addWidget(self.alpha_plot_view)
        # Display analysis results using a readable font
        self.results_text.setStyleSheet("font-size:14pt; font-family:Arial;")
        right.addWidget(self.results_text)

        btns2 = QHBoxLayout()
        for btn in [self.load_pre_exp_button, self.clear_button]:
            btns2.addWidget(btn)
        right.addLayout(btns2)

        rw = QWidget()
        rw.setLayout(right)
        g.addWidget(rw, 0, 1)

        # История
        tab_hist = QWidget()
        self.tab_widget.addTab(tab_hist, "")
        vh = QVBoxLayout(tab_hist)
        vh.addWidget(self.history_filter)
        vh.addWidget(self.history_table)
        hh = QHBoxLayout()
        hh.addWidget(self.delete_button)
        hh.addWidget(self.clear_history_button)
        vh.addLayout(hh)

        # Меню
        self._build_menu()

    def _install_event_filters(self):
        widgets = [
            self.baseline_slider,
            self.uplift_slider,
            self.alpha_slider,
            self.power_slider,
            self.calc_button,
            self.analyze_button,
            self.conf_button,
            self.bayes_button,
            self.aa_button,
            self.seq_button,
            self.obf_button,
            self.roi_button,
            self.plot_ci_button,
            self.plot_power_button,
            self.plot_alpha_button,
            self.plot_bootstrap_button,
            self.save_plot_button,
            self.load_pre_exp_button,
            self.clear_button,
            self.delete_button,
            self.clear_history_button,
        ]
        for w in widgets:
            w.installEventFilter(self)

    def _build_menu(self):
        mb = self.menuBar()
        # File / Файл
        fm = mb.addMenu(self.tr("File"))
        add_ds = QAction(self.tr("Add Data Source"), self)
        add_ds.triggered.connect(self._on_add_data_source)
        fm.addAction(add_ds)
        quick = QAction(self.tr("Quick AB Test"), self)
        quick.triggered.connect(self._open_quick_ab_test)
        fm.addAction(quick)
        oneclick = QAction(self.tr("One-click AB"), self)
        oneclick.triggered.connect(self._run_one_click_ab)
        fm.addAction(oneclick)
        fm.addSeparator()
        a3 = QAction(self.tr("Export PDF"), self)
        a3.triggered.connect(self.export_pdf)
        fm.addAction(a3)
        a4 = QAction(self.tr("Export Excel"), self)
        a4.triggered.connect(self.export_excel)
        fm.addAction(a4)
        a5 = QAction(self.tr("Export CSV"), self)
        a5.triggered.connect(self.export_csv)
        fm.addAction(a5)
        nb = QAction(self.tr("Export Notebook"), self)
        nb.triggered.connect(self.export_notebook)
        fm.addAction(nb)

        # Tutorial / Справка
        hm = mb.addMenu(self.tr("Tutorial"))
        tut = QAction(self.tr("Tutorial"), self)
        tut.triggered.connect(self.show_tutorial)
        hm.addAction(tut)

        # Language & theme switch
        cw = QWidget()
        cl = QHBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lang_button = QPushButton("RU" if self.lang == "en" else "EN")
        self.lang_button.setFixedSize(30, 30)
        self.lang_button.clicked.connect(self.toggle_language)
        self.theme_button = QPushButton(self.tr("☀"))
        self.theme_button.setFixedSize(30, 30)
        self.theme_button.clicked.connect(self.toggle_theme)
        cl.addWidget(self.lang_button)
        cl.addWidget(self.theme_button)
        mb.setCornerWidget(cw, Qt.Corner.TopRightCorner)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            tip = getattr(obj, "statusTip", lambda: "")()
            if tip:
                self.status.showMessage(tip)
        elif event.type() == QEvent.Type.FocusOut:
            self.status.clearMessage()
        return super().eventFilter(obj, event)

    def apply_dark_theme(self):
        p = QPalette()
        # Основной фон
        p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        p.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        # Текст
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        # Кнопки
        p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        # Выделение
        p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        # Всплывающие подсказки
        p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        # Применение
        QApplication.setPalette(p)
        # Сброс custom stylesheet, если есть
        self.setStyleSheet("")

    def apply_light_theme(self):
        p = QPalette()
        # Основной фон
        p.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.AlternateBase, Qt.GlobalColor.lightGray)
        # Текст
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        # Кнопки
        p.setColor(QPalette.ColorRole.Button, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        # Выделение
        p.setColor(QPalette.ColorRole.Highlight, QColor(30, 144, 255))
        p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        # Всплывающие подсказки
        p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
        p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        # Применение
        QApplication.setPalette(p)
        # Сброс custom stylesheet, если есть
        self.setStyleSheet("")

    def _load_translation(self, lang: str) -> bool:
        """Load Qt translation for the given language."""
        translations_dir = Path(__file__).resolve().parents[1] / "translations"
        qm_path = translations_dir / f"app_{lang}.qm"
        if not qm_path.exists():
            QMessageBox.critical(self, "Error", f"{qm_path} not found")
            return False
        app = QApplication.instance()
        if hasattr(self, "translator"):
            app.removeTranslator(self.translator)
        self.translator = QTranslator()
        if not self.translator.load(str(qm_path)):
            QMessageBox.critical(self, "Error", f"Failed to load {qm_path}")
            return False
        app.installTranslator(self.translator)
        self.lang = lang
        return True

    def update_ui_text(self):
        self.setWindowTitle(self.tr("Ultimate A/B Testing Tool"))
        self.tab_widget.setTabText(0, self.tr("Main"))
        self.tab_widget.setTabText(1, self.tr("History"))

        # Слайдерные лейблы
        self.baseline_label.setText(
            self.tr("Baseline conversion rate")
            + f" {self.baseline_slider.value()/10:.1f}%"
        )
        self.uplift_label.setText(
            self.tr("Expected uplift") + f" {self.uplift_slider.value()/10:.1f}%"
        )
        self.alpha_label.setText(
            self.tr("Significance level") + f" {self.alpha_slider.value()/100:.2f}"
        )
        self.power_label.setText(
            self.tr("Statistical power") + f" {self.power_slider.value()/100:.2f}"
        )

        # Кнопки и поля
        self.calc_button.setText(self.tr("Calculate"))
        for G in ["A", "B", "C"]:
            getattr(self, f"users_{G}_label").setText(self.tr(f"{G} - Users:"))
            getattr(self, f"conv_{G}_label").setText(self.tr(f"{G} - Conversions:"))
        self.analyze_button.setText(self.tr("A/B/n Analysis"))
        self.conf_button.setText(self.tr("Confidence Intervals"))
        self.bayes_button.setText(self.tr("Bayesian Analysis"))
        self.bandit_label.setText(self.tr("Bandit:"))
        self.aa_button.setText(self.tr("A/A Test"))
        self.seq_button.setText(self.tr("Sequential Analysis"))
        self.obf_button.setText(self.tr("O'Brien-Fleming"))
        self.revenue_per_user_label.setText(self.tr("Revenue per user"))
        self.traffic_cost_label.setText(self.tr("Traffic cost"))
        self.budget_label.setText(self.tr("Budget"))
        self.roi_button.setText(self.tr("Calculate ROI"))
        self.load_pre_exp_button.setText(self.tr("Load Pre-exp Data"))
        self.clear_button.setText(self.tr("Clear"))
        self.plot_ci_button.setText(self.tr("Confidence Intervals"))
        self.plot_power_button.setText(self.tr("Sample Size Curve"))
        self.plot_alpha_button.setText(self.tr("α-spending"))
        self.plot_bootstrap_button.setText(self.tr("Bootstrap"))
        self.save_plot_button.setText(self.tr("Save Plot"))
        self.delete_button.setText(self.tr("Delete Selected"))
        self.clear_history_button.setText(self.tr("Clear All"))

    # ----- auth -----
    def authenticate(self):
        self._auth_buttons = [
            self.calc_button,
            self.analyze_button,
            self.conf_button,
            self.bayes_button,
            self.aa_button,
            self.seq_button,
            self.obf_button,
            self.roi_button,
        ]
        for b in self._auth_buttons:
            if hasattr(b, "setEnabled"):
                b.setEnabled(False)

        if not hasattr(LoginDialog, "exec"):
            return

        dlg = LoginDialog(self)
        if dlg.exec():
            token, refresh = self._request_token(*dlg.credentials())
            if token:
                self.token = token
                self.refresh_token = refresh
                for b in self._auth_buttons:
                    b.setEnabled(True)

    def _request_token(self, username: str, password: str) -> str | None:
        data = json.dumps({"username": username, "password": password}).encode()
        api_url = os.environ.get("API_URL", "http://localhost:5000")
        req = urllib.request.Request(
            f"{api_url.rstrip('/')}/login",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                js = json.loads(resp.read().decode())
                return js.get("access_token"), js.get("refresh_token")
        except Exception:
            return None, None

    # ————— Обработчики —————

    def calculate_sample_size(self):
        try:
            p1 = self.baseline_slider.value() / 1000
            uplift = self.uplift_slider.value() / 1000
            alpha = self.alpha_slider.value() / 100
            power = self.power_slider.value() / 100
            p2 = p1 * (1 + uplift)
            n = required_sample_size(p1, p2, alpha, power)
            mde = calculate_mde(n, alpha, power, p1)
            html = (
                f"<pre>{self.tr('CR A')}={p1:.2%}, {self.tr('CR B')}={p2:.2%}\n"
                f"α={alpha:.2f}, {self.tr('Power')}={power:.2f}\n\n"
                f"{self.tr('Size/group')}: {n}\n"
                f"{self.tr('MDE')}: {mde:.2%}</pre>"
            )
            self.results_text.setHtml(html)
            self._add_history("Sample Size", html)
        except Exception as e:
            show_error(self, str(e))

    def _on_analyze(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            uc, cc = int(self.users_C_var.text()), int(self.conv_C_var.text())
            alpha = self.alpha_slider.value() / 100

            flag, p = srm_check(ua, ub, alpha=alpha)
            if flag:
                SB = getattr(
                    QMessageBox,
                    "StandardButton",
                    type("SB", (), {"Ignore": 1, "Cancel": 2}),
                )
                btn = QMessageBox.warning(
                    self,
                    "SRM detected",
                    f"SRM check failed (p={p:.3f}). Results may be biased.",
                    getattr(SB, "Ignore", 1) | getattr(SB, "Cancel", 2),
                )
                if btn != getattr(SB, "Ignore", btn):
                    return

            if hasattr(self, "metric_a") and hasattr(self, "covariate_a"):
                adj = cuped_adjustment(self.metric_a, self.covariate_a)
                ca = int(round(sum(adj)))
                ua = len(adj)
            if hasattr(self, "metric_b") and hasattr(self, "covariate_b"):
                adj = cuped_adjustment(self.metric_b, self.covariate_b)
                cb = int(round(sum(adj)))
                ub = len(adj)
            if hasattr(self, "metric_c") and hasattr(self, "covariate_c"):
                adj = cuped_adjustment(self.metric_c, self.covariate_c)
                cc = int(round(sum(adj)))
                uc = len(adj)

            res = evaluate_abn_test(ua, ca, ub, cb, uc, cc, alpha=alpha)
            html = (
                f"<pre>{self.tr('A')} {res['cr_a']:.2%} ({ca}/{ua})\n"
                f"{self.tr('B')} {res['cr_b']:.2%} ({cb}/{ub})\n"
                f"{self.tr('C')} {res['cr_c']:.2%} ({cc}/{uc})\n\n"
                f"{self.tr('P(A vs B)')}={res['p_value_ab']:.4f}\n"
                f"{self.tr('Winner')}: {res['winner']}</pre>"
            )
            self.results_text.setHtml(html)
            self._add_history("A/B/n Test", html)
        except Exception as e:
            show_error(self, str(e))

    _on_analyze_abn = _on_analyze

    def _on_plot_confidence_intervals(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            alpha = self.alpha_slider.value() / 100
            fig = plot_confidence_intervals(ua, ca, ub, cb, alpha)
            self._last_fig = fig
            w = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_power_curve(self):
        try:
            p1 = self.baseline_slider.value() / 1000
            alpha = self.alpha_slider.value() / 100
            pw = self.power_slider.value() / 100
            fig = plot_power_curve(p1, alpha, pw)
            self._last_fig = fig
            w = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_alpha_spending(self):
        try:
            alpha = self.alpha_slider.value() / 100
            fig = plot_alpha_spending(alpha, looks=5)
            self._last_fig = fig
            if self.alpha_plot_view:
                import plotly.io as pio

                html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
                self.alpha_plot_view.setHtml(html)
                self.alpha_plot_view.setVisible(True)
            else:
                w = PlotWindow(self)
                w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_bootstrap_distribution(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            fig = plot_bootstrap_distribution(ua, ca, ub, cb)
            self._last_fig = fig
            w = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_bayes(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            a0 = self.prior_alpha_spin.value()
            b0 = self.prior_beta_spin.value()
            prob, x, pa, pb = bayesian_analysis(a0, b0, ua, ca, ub, cb)
            tr = getattr(self, "tr", lambda x: x)
            html = f"<pre>{tr('P(B>A)')} = {prob:.2%}</pre>"
            self.results_text.setHtml(html)
            self._add_history("Bayesian Analysis", html)
            fig = plot_bayesian_posterior(a0, b0, ua, ca, ub, cb)
            self._last_fig = fig
            w = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def _on_run_aa(self):
        try:
            p = self.baseline_slider.value() / 1000
            n = int(self.users_A_var.text()) + int(self.users_B_var.text())
            alpha = self.alpha_slider.value() / 100
            fpr = run_aa_simulation(p, n, alpha)
            html = (
                f"<pre>{self.tr('Exp FPR')}: {alpha:.1%}, "
                f"{self.tr('Actual FPR')}: {fpr:.1%}</pre>"
            )
            self.results_text.setHtml(html)
            self._add_history("A/A Test", html)
            self._last_fig = None
        except Exception as e:
            show_error(self, str(e))

    def _on_run_sequential(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            alpha = self.alpha_slider.value() / 100
            url = self._config.get("webhook_url") or None
            steps, pa = run_sequential_analysis(ua, ca, ub, cb, alpha, webhook_url=url)
            txt = f"<pre>{self.tr('Pocock α')}={pa:.4f}\n"
            for i, r in enumerate(steps, 1):
                txt += f"{self.tr('Step')}{i}: p={r['p_value_ab']:.4f}, {self.tr('win')}={r['winner']}\n"
            txt += "</pre>"
            self.results_text.setHtml(txt)
            self._add_history("Sequential Analysis", txt)
            self._last_fig = None
        except Exception as e:
            show_error(self, str(e))

    def _on_run_obrien_fleming(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            alpha = self.alpha_slider.value() / 100
            url = self._config.get("webhook_url") or None
            steps = run_obrien_fleming(ua, ca, ub, cb, alpha, webhook_url=url)
            txt = "<pre>" + self.tr("O'Brien-Fleming") + "\n"
            for i, r in enumerate(steps, 1):
                txt += (
                    f"{self.tr('Step')}{i}: p={r['p_value_ab']:.4f} "
                    f"{self.tr('thr')}={r['threshold']:.4f} "
                    f"{self.tr('win')}={r['winner']}\n"
                )
            txt += "</pre>"
            self.results_text.setHtml(txt)
            self._add_history("OBrien-Fleming", txt)
            self._last_fig = None
        except Exception as e:
            show_error(self, str(e))

    def _on_calculate_roi(self):
        try:
            rpu = float(self.revenue_per_user_var.text())
            cost = float(self.traffic_cost_var.text())
            bud = float(self.budget_var.text())
            p1 = self.baseline_slider.value() / 1000
            up = self.uplift_slider.value() / 1000
            u, br, nr, pf, ro = calculate_roi(rpu, cost, bud, p1, up)
            html = (
                f"<pre>{self.tr('Users')}: {u:.0f}\n"
                f"{self.tr('Base rev')}: {br:.2f}\n"
                f"{self.tr('New rev')}:  {nr:.2f}\n"
                f"{self.tr('Profit')}:   {pf:.2f}\n"
                f"{self.tr('ROI')}:      {ro:.2f}%</pre>"
            )
            self.results_text.setHtml(html)
            self._add_history("ROI", html)
        except Exception as e:
            show_error(self, str(e))

    def show_tutorial(self):
        QMessageBox.information(
            self,
            self.tr("Tutorial"),
            "🔹 Слайдеры CR, uplift, α, power\n"
            "🔹 Поля A/B/C\n"
            "🔹 Bayesian с priors\n"
            "🔹 ROI встроен\n"
            "🔹 История с экспортом",
        )

    def toggle_theme(self):
        if getattr(self, "is_dark", True):
            self.apply_light_theme()
            self.theme_button.setText(self.tr("☾"))
            self.is_dark = False
        else:
            self.apply_dark_theme()
            self.theme_button.setText(self.tr("☀"))
            self.is_dark = True

    def toggle_language(self):
        """Switch between English and Russian translations."""
        new_lang = "ru" if self.lang == "en" else "en"
        if self._load_translation(new_lang):
            self.lang_button.setText("EN" if new_lang == "ru" else "RU")
            self.retranslateUi()

    def retranslateUi(self):
        """Update UI texts after language change."""
        self.menuBar().clear()
        self._build_menu()
        self.update_ui_text()
        self.lang_button.setText("RU" if self.lang == "en" else "EN")

    def _on_add_data_source(self):
        dlg = AddDataSourceDialog(self)
        if dlg.exec():
            self.sources.append(dlg.data())
            QMessageBox.information(self, "Info", "Data source added")

    def _open_quick_ab_test(self):
        """Launch the quick A/B test wizard."""
        try:
            from .wizard import QuickABTestWizard
        except Exception:
            return
        wiz = QuickABTestWizard(self)
        res = getattr(wiz, "exec", lambda: 0)()
        if res:
            data = wiz.data()
            msg = (
                f"{self.tr('Flag')}: {data['flag']}\n"
                f"{self.tr('Metric')}: {data['primary_metric']}\n"
                f"{self.tr('Sequential')}={data['sequential']} "
                f"{self.tr('CUPED')}={data['cuped']} "
                f"{self.tr('SRM')}={data['srm']}"
            )
            self.results_text.setHtml(f"<pre>{msg}</pre>")
            self._add_history("Quick AB Test", f"<pre>{msg}</pre>")

    def _run_one_click_ab(self):
        """Run a preconfigured A/B test without user input."""
        data = {
            "flag": "demo-flag",
            "primary_metric": "conversion",
            "sequential": True,
            "cuped": False,
            "srm": True,
        }
        msg = (
            f"{self.tr('Flag')}: {data['flag']}\n"
            f"{self.tr('Metric')}: {data['primary_metric']}\n"
            f"{self.tr('Sequential')}={data['sequential']} "
            f"{self.tr('CUPED')}={data['cuped']} "
            f"{self.tr('SRM')}={data['srm']}"
        )
        self.results_text.setHtml(f"<pre>{msg}</pre>")
        self._add_history("One-click AB", f"<pre>{msg}</pre>")

    # ————— Сессионные функции и экспорт результатов —————

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            sections = {
                "Описание": [],
                "Результаты": self.results_text.toPlainText().splitlines(),
                "Визуализации": [],
                "Интерпретация": [],
            }
            utils.export_pdf(sections, path)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", "", "Excel Files (*.xlsx)"
        )
        if not path:
            return
        try:
            sections = {"Results": self.results_text.toPlainText().splitlines()}
            utils.export_excel(sections, path)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            sections = {"Results": self.results_text.toPlainText().splitlines()}
            utils.export_csv(sections, path)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def export_notebook(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Notebook", "", "Notebook Files (*.ipynb)"
        )
        if not path:
            return
        try:
            sections = {
                "Описание": [],
                "Результаты": self.results_text.toPlainText().splitlines(),
                "Визуализации": [],
                "Интерпретация": [],
            }
            utils.export_notebook(sections, path)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ABTestWindow()
    w.show()
    sys.exit(app.exec())
