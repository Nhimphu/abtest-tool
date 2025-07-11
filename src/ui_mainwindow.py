# ui_mainwindow.py

import sys
import sqlite3
import csv
import pandas as pd
import numpy as np

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
    QMessageBox,
    QFileDialog,
    QTextBrowser,
    QComboBox,
    QInputDialog,
    QCheckBox,
)
from PyQt6.QtGui import QPalette, QColor, QIntValidator, QDoubleValidator, QAction
from PyQt6.QtCore import Qt, QDateTime

from logic import (
    required_sample_size,
    calculate_mde,
    evaluate_abn_test,
    bayesian_analysis,
    plot_bayesian_posterior,
    run_aa_simulation,
    run_sequential_analysis,
    run_obrien_fleming,
    calculate_roi,
    plot_confidence_intervals,
    plot_power_curve,
    plot_bootstrap_distribution,
    save_plot,
    cuped_adjustment,
    srm_check,
    ucb1,
    epsilon_greedy
)
from i18n import i18n, detect_language
from flags import FeatureFlagStore
from webhooks import send_webhook
import utils


def show_error(parent, msg):
    QMessageBox.critical(parent, "Ошибка", msg)


class PlotWindow:
    """Utility for displaying Plotly figures in the user's browser."""

    def __init__(self, parent=None):
        self.parent = parent

    def display_plot(self, fig):
        import tempfile
        import webbrowser
        import plotly.io as pio

        html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as f:
            f.write(html)
            path = f.name
        webbrowser.open(f"file://{path}")


class FlagsWindow(QMainWindow):
    """Simple no-code editor for feature flags."""

    def __init__(self, store: FeatureFlagStore):
        super().__init__()
        self.store = store
        self.setWindowTitle("Feature Flags")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Enabled", "Rollout %"])
        self.table.cellChanged.connect(self._on_cell_changed)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_flag)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(add_btn)
        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)
        self.reload()

    def reload(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for flag in self.store.list_flags():
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(flag.name))
            chk = QCheckBox()
            chk.setChecked(flag.enabled)
            self.table.setCellWidget(r, 1, chk)
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setValue(flag.rollout)
            spin.setSuffix(" %")
            self.table.setCellWidget(r, 2, spin)
        self.table.blockSignals(False)

    def _add_flag(self):
        name, ok = QInputDialog.getText(self, "Name", "Flag name:")
        if not ok or not name:
            return
        try:
            self.store.create_flag(name)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.reload()

    def _on_cell_changed(self, row, col):
        name = self.table.item(row, 0).text()
        enabled = self.table.cellWidget(row, 1).isChecked()
        rollout = self.table.cellWidget(row, 2).value()
        try:
            self.store.update_flag(name, enabled=enabled, rollout=rollout)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class ABTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = detect_language()
        self.i18n = i18n
        self.flag_store = FeatureFlagStore()
        self.flags_window = None

        self.setWindowTitle(self.i18n[self.lang]['title'])
        self.setGeometry(100, 100, 1000, 800)

        # Инициализируем историю
        self._init_history_db()
        # Создаём виджеты
        self._prepare_widgets()
        # Строим интерфейс
        self._build_ui()
        # Применяем тёмную тему
        self.apply_dark_theme()
        # Загружаем историю
        self._load_history()
        # Обновляем тексты
        self.update_ui_text()

    # ————— История (SQLite) —————

    def _init_history_db(self):
        self.conn = sqlite3.connect('history.db')
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                test TEXT,
                result TEXT
            )''')
        self.conn.commit()

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

    def _add_history(self, name, content):
        ts = QDateTime.currentDateTime().toString()
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO history(timestamp,test,result) VALUES(?,?,?)",
            (ts, name, content.replace("<pre>", "").replace("</pre>", ""))
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
        self.history_table.setItem(r, 3, QTableWidgetItem(content.replace("<pre>", "").replace("</pre>", "")))
        if not hasattr(self, 'undo_stack'):
            self.undo_stack = []
        self.undo_stack.append(self.results_text.toHtml())

    def _delete_selected_history(self):
        for r in reversed(range(self.history_table.rowCount())):
            item = self.history_table.item(r, 0)
            if item.checkState() == Qt.CheckState.Checked:
                rec_id = item.data(Qt.ItemDataRole.UserRole)
                self.conn.cursor().execute("DELETE FROM history WHERE id=?", (rec_id,))
                self.conn.commit()
                self.history_table.removeRow(r)

    def _clear_all_history(self):
        self.conn.cursor().execute("DELETE FROM history")
        self.conn.commit()
        self.history_table.setRowCount(0)

    def _export_history_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save History CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        c = self.conn.cursor()
        c.execute("SELECT timestamp,test,result FROM history ORDER BY id")
        rows = c.fetchall()
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['Timestamp', 'Test', 'Result'])
                w.writerows(rows)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def _export_history_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save History Excel", "", "Excel Files (*.xlsx)")
        if not path:
            return
        df = pd.read_sql_query(
            "SELECT timestamp AS Timestamp, test AS Test, result AS Result FROM history ORDER BY id",
            self.conn
        )
        try:
            df.to_excel(path, index=False)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    # ————— Подготовка виджетов —————

    def _prepare_widgets(self):
        # Слайдеры
        self.baseline_slider = QSlider(Qt.Orientation.Horizontal)
        self.baseline_slider.setRange(0, 1000)
        self.baseline_slider.setValue(40)
        self.baseline_slider.valueChanged.connect(self.update_ui_text)
        self.baseline_slider.setToolTip("Baseline conversion rate")

        self.uplift_slider = QSlider(Qt.Orientation.Horizontal)
        self.uplift_slider.setRange(0, 1000)
        self.uplift_slider.setValue(100)
        self.uplift_slider.valueChanged.connect(self.update_ui_text)

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(5)
        self.alpha_slider.valueChanged.connect(self.update_ui_text)
        self.alpha_slider.setToolTip("Significance level")

        self.power_slider = QSlider(Qt.Orientation.Horizontal)
        self.power_slider.setRange(0, 100)
        self.power_slider.setValue(90)
        self.power_slider.valueChanged.connect(self.update_ui_text)

        # Кнопка расчёта
        self.calc_button = QPushButton()
        self.calc_button.clicked.connect(self.calculate_sample_size)

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
        self.analyze_button.clicked.connect(self._on_analyze_abn)
        self.conf_button = QPushButton()
        self.conf_button.clicked.connect(self._on_plot_confidence_intervals)
        self.bayes_button = QPushButton()
        self.bayes_button.clicked.connect(self._on_run_bayesian)
        self.aa_button = QPushButton()
        self.aa_button.clicked.connect(self._on_run_aa)
        self.seq_button = QPushButton()
        self.seq_button.clicked.connect(self._on_run_sequential)
        self.obf_button = QPushButton()
        self.obf_button.clicked.connect(self._on_run_obrien_fleming)

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
        self.revenue_per_user_var   = QLineEdit("50")
        self.revenue_per_user_var.setValidator(QDoubleValidator(0, 1e9, 2))
        self.traffic_cost_label     = QLabel()
        self.traffic_cost_var       = QLineEdit("10")
        self.traffic_cost_var.setValidator(QDoubleValidator(0, 1e9, 2))
        self.budget_label           = QLabel()
        self.budget_var             = QLineEdit("10000")
        self.budget_var.setValidator(QDoubleValidator(0, 1e12, 2))
        self.roi_button             = QPushButton()
        self.roi_button.clicked.connect(self._on_calculate_roi)

        # Segmentation & Custom metric
        self.filter_device  = QLineEdit()
        self.filter_country = QLineEdit()
        self.filter_utm     = QLineEdit()
        self.custom_metric  = QLineEdit("sum('conv')/sum('users')")

        self.undo_button = QPushButton('Undo')
        self.undo_button.clicked.connect(self.undo)
        self.redo_button = QPushButton('Redo')
        self.redo_button.clicked.connect(self.redo)
        self.share_button = QPushButton('Share')
        self.share_button.clicked.connect(self.share_session)

        # Графики
        self.plot_ci_button       = QPushButton()
        self.plot_ci_button.clicked.connect(self._on_plot_confidence_intervals)
        self.plot_power_button    = QPushButton()
        self.plot_power_button.clicked.connect(self._on_plot_power_curve)
        self.plot_alpha_button    = QPushButton()
        self.plot_alpha_button.clicked.connect(self._on_plot_alpha_spending)
        self.plot_bootstrap_button = QPushButton()
        self.plot_bootstrap_button.clicked.connect(self._on_plot_bootstrap_distribution)
        self.save_plot_button     = QPushButton()
        self.save_plot_button.clicked.connect(save_plot)

        # Результаты
        self.results_text = QTextBrowser()

        # Загрузка / Очистка
        self.pre_exp_data = None
        self.load_pre_exp_button = QPushButton()
        self.load_pre_exp_button.clicked.connect(self.load_pre_experiment_data)
        self.clear_button        = QPushButton()
        self.clear_button.clicked.connect(lambda: self.results_text.setHtml("<pre></pre>"))

        # История
        self.history_table      = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["✓", "Дата", "Тест", "Результат"])
        self.history_table.setSortingEnabled(True)
        self.del_selected_button = QPushButton()
        self.del_selected_button.clicked.connect(self._delete_selected_history)
        self.clear_history_button = QPushButton()
        self.clear_history_button.clicked.connect(self._clear_all_history)

    # ————— Построение интерфейса —————

    def _build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
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
        left.addWidget(QLabel())
        left.addWidget(self.baseline_slider)
        left.addWidget(QLabel())
        left.addWidget(self.uplift_slider)
        left.addWidget(QLabel())
        left.addWidget(self.alpha_slider)
        left.addWidget(QLabel())
        left.addWidget(self.power_slider)
        left.addWidget(self.calc_button)

        for G in ["A", "B", "C"]:
            left.addWidget(getattr(self, f"users_{G}_label"))
            left.addWidget(getattr(self, f"users_{G}_var"))
            left.addWidget(getattr(self, f"conv_{G}_label"))
            left.addWidget(getattr(self, f"conv_{G}_var"))

        left.addWidget(self.analyze_button)
        left.addWidget(self.conf_button)
        left.addWidget(QLabel("α-prior:"))
        left.addWidget(self.prior_alpha_spin)
        left.addWidget(QLabel("β-prior:"))
        left.addWidget(self.prior_beta_spin)
        left.addWidget(self.bayes_button)
        left.addWidget(self.bandit_label)
        left.addWidget(self.bandit_combo)
        left.addWidget(self.aa_button)
        left.addWidget(self.seq_button)
        left.addWidget(self.obf_button)

        left.addWidget(self.revenue_per_user_label)
        left.addWidget(self.revenue_per_user_var)
        left.addWidget(self.traffic_cost_label)
        left.addWidget(self.traffic_cost_var)
        left.addWidget(self.budget_label)
        left.addWidget(self.budget_var)
        left.addWidget(self.roi_button)
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
            self.save_plot_button
        ]:
            btns.addWidget(btn)
        right.addLayout(btns)
        right.addWidget(self.results_text)

        seg = QGridLayout()
        seg.addWidget(QLabel("Device"), 0, 0)
        seg.addWidget(self.filter_device, 0, 1)
        seg.addWidget(QLabel("Country"), 1, 0)
        seg.addWidget(self.filter_country, 1, 1)
        seg.addWidget(QLabel("UTM"), 2, 0)
        seg.addWidget(self.filter_utm, 2, 1)
        seg.addWidget(QLabel("Metric"), 3, 0)
        seg.addWidget(self.custom_metric, 3, 1)
        right.addLayout(seg)

        btns2 = QHBoxLayout()
        for btn in [
            self.load_pre_exp_button,
            self.clear_button
        ]:
            btns2.addWidget(btn)
        right.addLayout(btns2)

        collab = QHBoxLayout()
        for btn in [self.undo_button, self.redo_button, self.share_button]:
            collab.addWidget(btn)
        right.addLayout(collab)

        rw = QWidget()
        rw.setLayout(right)
        g.addWidget(rw, 0, 1)

        # История
        tab_hist = QWidget()
        self.tab_widget.addTab(tab_hist, "")
        vh = QVBoxLayout(tab_hist)
        vh.addWidget(self.history_table)
        hh = QHBoxLayout()
        hh.addWidget(self.del_selected_button)
        hh.addWidget(self.clear_history_button)
        vh.addLayout(hh)

        # Меню
        self._build_menu()

    def _build_menu(self):
        L = self.i18n[self.lang]
        mb = self.menuBar()
        # File / Файл
        fm = mb.addMenu(L['file'])
        fm.addSeparator()
        a3 = QAction(L['export_pdf'], self)
        a3.triggered.connect(self.export_pdf)
        fm.addAction(a3)
        a4 = QAction(L['export_excel'], self)
        a4.triggered.connect(self.export_excel)
        fm.addAction(a4)
        a5 = QAction(L['export_csv'], self)
        a5.triggered.connect(self.export_csv)
        fm.addAction(a5)
        md = QAction('Export MD', self)
        md.triggered.connect(self.export_markdown)
        fm.addAction(md)
        nb = QAction('Export Notebook', self)
        nb.triggered.connect(self.export_notebook)
        fm.addAction(nb)
        ff = QAction('Feature Flags', self)
        ff.triggered.connect(self.show_flags_editor)
        fm.addAction(ff)

        # Tutorial / Справка
        hm = mb.addMenu(L['tutorial'])
        tut = QAction(L['tutorial'], self)
        tut.triggered.connect(self.show_tutorial)
        hm.addAction(tut)


        # Language switch
        cw = QWidget()
        cl = QHBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lang_button = QPushButton("🌐")
        self.lang_button.setFixedSize(30, 30)
        self.lang_button.clicked.connect(self.toggle_language)
        cl.addWidget(self.lang_button)
        self.theme_button = QPushButton("☀")
        self.theme_button.setFixedSize(30, 30)
        self.theme_button.clicked.connect(self.toggle_theme)
        cl.addWidget(self.theme_button)
        mb.setCornerWidget(cw, Qt.Corner.TopRightCorner)

    def apply_dark_theme(self):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        self.setPalette(p)

    def apply_light_theme(self):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        self.setPalette(p)

    def update_ui_text(self):
        L = self.i18n[self.lang]
        self.setWindowTitle(L['title'])
        self.tab_widget.setTabText(0, L['main'])
        self.tab_widget.setTabText(1, L['history'])

        # Слайдерные лейблы
        g = self.baseline_slider.parentWidget().layout()
        g.itemAt(0).widget().setText(f"{L['baseline']} {self.baseline_slider.value()/10:.1f}%")
        g.itemAt(2).widget().setText(f"{L['uplift']} {self.uplift_slider.value()/10:.1f}%")
        g.itemAt(4).widget().setText(f"{L['alpha']} {self.alpha_slider.value()/100:.2f}")
        g.itemAt(6).widget().setText(f"{L['power']} {self.power_slider.value()/100:.2f}")

        # Кнопки и поля
        self.calc_button.setText(L['calculate_sample_size'])
        for G in ["A", "B", "C"]:
            getattr(self, f"users_{G}_label").setText(
                f"{G} – {'Пользователи' if self.lang=='RU' else 'Users'}:"
            )
            getattr(self, f"conv_{G}_label").setText(
                f"{G} – {'Конверсии' if self.lang=='RU' else 'Conversions'}:"
            )
        self.analyze_button.setText(L['analyze_ab'])
        self.conf_button.setText(L['confidence_intervals'])
        self.bayes_button.setText(L['bayesian_analysis'])
        self.bandit_label.setText('Bandit:')
        self.aa_button.setText(L['aa_testing'])
        self.seq_button.setText(L['sequential_testing'])
        self.obf_button.setText(L['obrien_fleming'])
        self.revenue_per_user_label.setText(L['revenue_per_user'])
        self.traffic_cost_label.setText(L['traffic_cost'])
        self.budget_label.setText(L['budget'])
        self.roi_button.setText(L['calculate_roi'])
        self.load_pre_exp_button.setText(L['pre_exp_data'])
        self.clear_button.setText(L['clear_results'])
        self.plot_ci_button.setText(L['confidence_intervals'])
        self.plot_power_button.setText(L['power_curve'])
        self.plot_alpha_button.setText('α-spending')
        self.plot_bootstrap_button.setText(L['bootstrap'])
        self.save_plot_button.setText(L['save_plot'])
        self.del_selected_button.setText(L['delete_selected'])
        self.clear_history_button.setText(L['clear_history'])
        self.filter_device.setPlaceholderText('mobile/desktop')
        self.filter_country.setPlaceholderText('US')
        self.filter_utm.setPlaceholderText('campaign')
        self.custom_metric.setToolTip("e.g., sum('conv')/sum('users')")

    # ————— Обработчики —————

    def calculate_sample_size(self):
        try:
            p1     = self.baseline_slider.value()/1000
            uplift = self.uplift_slider.value()/1000
            alpha  = self.alpha_slider.value()/100
            power  = self.power_slider.value()/100
            p2     = p1*(1+uplift)
            n      = required_sample_size(p1, p2, alpha, power)
            mde    = calculate_mde(n, alpha, power, p1)
            html = (f"<pre>CR A={p1:.2%}, CR B={p2:.2%}\n"
                    f"α={alpha:.2f}, Power={power:.2f}\n\n"
                    f"Size/group: {n}\n"
                    f"MDE: {mde:.2%}</pre>")
            self.results_text.setHtml(html)
            self._add_history("Sample Size", html)
        except Exception as e:
            show_error(self, str(e))

    def _on_analyze_abn(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            uc, cc = int(self.users_C_var.text()), int(self.conv_C_var.text())
            alpha  = self.alpha_slider.value()/100
            if self.pre_exp_data:
                conv, cov = self.pre_exp_data
                adj = cuped_adjustment(conv, cov)
                ca = int(sum(adj[:ua]))
                cb = int(sum(adj[ua:ua+ub]))
            if getattr(self, 'records', None):
                recs = self.records
                filt = {}
                if self.filter_device.text():
                    filt['device'] = self.filter_device.text()
                if self.filter_country.text():
                    filt['country'] = self.filter_country.text()
                if self.filter_utm.text():
                    filt['utm'] = self.filter_utm.text()
                if filt:
                    recs = segment_data(recs, **filt)
                metric = compute_custom_metric(recs, self.custom_metric.text())
            res    = evaluate_abn_test(ua, ca, ub, cb, uc, cc, alpha=alpha)
            srm_flag, p_srm = srm_check(ua, ub)
            metric_val = locals().get('metric', None)
            rec_arm = self._recommend_bandit(ca, ua, cb, ub)
            html   = (f"<pre>A {res['cr_a']:.2%} ({ca}/{ua})\n"
                      f"B {res['cr_b']:.2%} ({cb}/{ub})\n"
                      f"C {res['cr_c']:.2%} ({cc}/{uc})\n\n"
                      f"P(A vs B)={res['p_value_ab']:.4f}\n"
                      f"Winner: {res['winner']}\n"
                      f"SRM p={p_srm:.3f}{' ⚠' if srm_flag else ''}\n"
                      f"Metric={metric_val:.4f}" if metric_val is not None else ""
                      f"\nNext arm: {rec_arm}</pre>")
            self.results_text.setHtml(html)
            self._add_history("A/B/n Test", html)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_confidence_intervals(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            alpha  = self.alpha_slider.value()/100
            fig    = plot_confidence_intervals(ua, ca, ub, cb, alpha)
            w      = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_power_curve(self):
        try:
            p1    = self.baseline_slider.value()/1000
            alpha = self.alpha_slider.value()/100
            pw    = self.power_slider.value()/100
            fig   = plot_power_curve(p1, alpha, pw)
            w     = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_alpha_spending(self):
        try:
            alpha = self.alpha_slider.value()/100
            fig = plot_alpha_spending(alpha, looks=5)
            w = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_plot_bootstrap_distribution(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            fig    = plot_bootstrap_distribution(ua, ca, ub, cb)
            w      = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_run_bayesian(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            a0     = self.prior_alpha_spin.value()
            b0     = self.prior_beta_spin.value()
            prob, x, pa, pb = bayesian_analysis(a0, b0, ua, ca, ub, cb)
            html = f"<pre>P(B>A) = {prob:.2%}</pre>"
            self.results_text.setHtml(html)
            self._add_history("Bayesian Analysis", html)
            fig = plot_bayesian_posterior(a0, b0, ua, ca, ub, cb)
            w   = PlotWindow(self)
            w.display_plot(fig)
        except Exception as e:
            show_error(self, str(e))

    def _on_run_aa(self):
        try:
            p     = self.baseline_slider.value()/1000
            n     = int(self.users_A_var.text()) + int(self.users_B_var.text())
            alpha = self.alpha_slider.value()/100
            fpr   = run_aa_simulation(p, n, alpha)
            html  = f"<pre>Exp FPR: {alpha:.1%}, Actual FPR: {fpr:.1%}</pre>"
            self.results_text.setHtml(html)
            self._add_history("A/A Test", html)
        except Exception as e:
            show_error(self, str(e))

    def _on_run_sequential(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            alpha  = self.alpha_slider.value()/100
            steps, pa = run_sequential_analysis(ua, ca, ub, cb, alpha)
            txt = f"<pre>Pocock α={pa:.4f}\n"
            for i, r in enumerate(steps, 1):
                txt += f"Step{i}: p={r['p_value_ab']:.4f}, win={r['winner']}\n"
            txt += "</pre>"
            self.results_text.setHtml(txt)
            self._add_history("Sequential Analysis", txt)
            if len(steps) < 5:
                send_webhook('http://example.com', 'Sequential test stopped early')
        except Exception as e:
            show_error(self, str(e))

    def _on_run_obrien_fleming(self):
        try:
            ua, ca = int(self.users_A_var.text()), int(self.conv_A_var.text())
            ub, cb = int(self.users_B_var.text()), int(self.conv_B_var.text())
            alpha  = self.alpha_slider.value()/100
            steps = run_obrien_fleming(ua, ca, ub, cb, alpha)
            txt = "<pre>O'Brien-Fleming\n"
            for i, r in enumerate(steps, 1):
                txt += (
                    f"Step{i}: p={r['p_value_ab']:.4f} "
                    f"thr={r['threshold']:.4f} win={r['winner']}\n"
                )
            txt += "</pre>"
            self.results_text.setHtml(txt)
            self._add_history("OBrien-Fleming", txt)
            if len(steps) < 5:
                send_webhook('http://example.com', 'OBF test stopped early')
        except Exception as e:
            show_error(self, str(e))

    def _on_calculate_roi(self):
        try:
            rpu = float(self.revenue_per_user_var.text())
            cost = float(self.traffic_cost_var.text())
            bud = float(self.budget_var.text())
            p1 = self.baseline_slider.value()/1000
            up = self.uplift_slider.value()/1000
            u, br, nr, pf, ro = calculate_roi(rpu, cost, bud, p1, up)
            html = (
                f"<pre>Users: {u:.0f}\n"
                f"Base rev: {br:.2f}\n"
                f"New rev:  {nr:.2f}\n"
                f"Profit:   {pf:.2f}\n"
                f"ROI:      {ro:.2f}%</pre>"
            )
            self.results_text.setHtml(html)
            self._add_history("ROI", html)
        except Exception as e:
            show_error(self, str(e))


    def show_tutorial(self):
        QMessageBox.information(
            self,
            self.i18n[self.lang]['tutorial'],
            "🔹 Слайдеры CR, uplift, α, power\n"
            "🔹 Поля A/B/C\n"
            "🔹 Bayesian с priors\n"
            "🔹 ROI встроен\n"
            "🔹 История с экспортом"
        )

    def toggle_language(self):
        self.lang = "EN" if self.lang == "RU" else "RU"
        self.update_ui_text()

    def show_flags_editor(self):
        if self.flags_window is None:
            self.flags_window = FlagsWindow(self.flag_store)
        self.flags_window.reload()
        self.flags_window.show()

    def toggle_theme(self):
        if self.palette().color(QPalette.ColorRole.Window) == QColor(53, 53, 53):
            self.apply_light_theme()
            self.theme_button.setText("☾")
        else:
            self.apply_dark_theme()
            self.theme_button.setText("☀")

    def load_pre_experiment_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            conv = []
            cov = []
            records = []
            with open(path, newline="", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    records.append(row)
                    conv.append(float(row.get("conv", 0)))
                    cov.append(float(row.get("cov", 0)))
            self.pre_exp_data = (conv, cov)
            self.records = records
            QMessageBox.information(self, "Loaded", f"Loaded {len(records)} rows")
        except Exception as e:
            show_error(self, str(e))

    def undo(self):
        if hasattr(self, 'undo_stack') and self.undo_stack:
            state = self.undo_stack.pop()
            self.results_text.setHtml(state)

    def redo(self):
        # simple placeholder, real stack not implemented
        pass

    def _recommend_bandit(self, conv_a, users_a, conv_b, users_b):
        alg = self.bandit_combo.currentText()
        values = [conv_a, conv_b]
        counts = [users_a, users_b]
        if alg == "UCB1":
            idx = ucb1(values, counts)
        elif alg == "ε-greedy":
            idx = epsilon_greedy(values, counts, epsilon=0.1)
        else:  # Thompson sampling
            a1, b1 = conv_a + 1, users_a - conv_a + 1
            a2, b2 = conv_b + 1, users_b - conv_b + 1
            idx = 0 if np.random.beta(a1, b1) > np.random.beta(a2, b2) else 1
        return "A" if idx == 0 else "B"

    def share_session(self):
        txt = self.results_text.toPlainText()
        QMessageBox.information(self, "Share", txt if txt else "Nothing to share")

    # ————— Сессионные функции и экспорт результатов —————


    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            utils.export_pdf(self.results_text.toPlainText(), path)
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
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            sections = {"Results": self.results_text.toPlainText().splitlines()}
            utils.export_csv(sections, path)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))

    def export_markdown(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown", "", "Markdown Files (*.md)"
        )
        if not path:
            return
        try:
            sections = {"Results": self.results_text.toPlainText().splitlines()}
            utils.export_markdown(sections, path)
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
            sections = {"Results": self.results_text.toPlainText().splitlines()}
            utils.export_notebook(sections, path)
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            show_error(self, str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ABTestWindow()
    w.show()
    sys.exit(app.exec())
