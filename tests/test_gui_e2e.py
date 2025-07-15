import os
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWizard

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from ui.ui_mainwindow import ABTestWindow
from ui import wizard as wizard_mod
from utils.config import Config


def test_quick_ab_e2e(qtbot, tmp_path, monkeypatch):
    cfg = Config()
    cfg._data['history_db'] = str(tmp_path / 'history.db')
    window = ABTestWindow(cfg)
    qtbot.addWidget(window)
    window.show()

    original_exec = wizard_mod.QuickABTestWizard.exec

    def auto_exec(self):
        def fill_and_accept():
            self.flag_combo.addItem('demo-flag')
            self.flag_combo.setCurrentText('demo-flag')
            self.rollout_edit.setText('50')
            self.primary_edit.setText('conversion')
            self.seq_check.setChecked(True)
            self.accept()
        QTimer.singleShot(0, fill_and_accept)
        return original_exec(self)

    monkeypatch.setattr(wizard_mod.QuickABTestWizard, 'exec', auto_exec)
    window._open_quick_ab_test()

    text = window.results_text.toPlainText()
    assert 'demo-flag' in text
    assert 'conversion' in text

    window.close()
