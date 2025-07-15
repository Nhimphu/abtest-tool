import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWizard

from ui.ui_mainwindow import ABTestWindow
from ui.wizard import QuickABTestWizard
from utils.config import config


def test_gui_end_to_end(qtbot, monkeypatch):
    window = ABTestWindow(config)
    qtbot.addWidget(window)
    window.show()

    # toggle themes twice
    qtbot.mouseClick(window.theme_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.theme_button, Qt.MouseButton.LeftButton)

    # prepare wizard to auto accept
    sample = {
        "flag": "demo",
        "primary_metric": "metric",
        "sequential": False,
        "cuped": False,
        "srm": False,
    }
    monkeypatch.setattr(QuickABTestWizard, "data", lambda self: sample)

    orig_exec = QWizard.exec

    def auto_exec(self):
        qtbot.addWidget(self)
        QTimer.singleShot(0, self.accept)
        return orig_exec(self)

    monkeypatch.setattr(QuickABTestWizard, "exec", auto_exec, raising=False)

    window._open_quick_ab_test()
    assert "Flag" in window.results_text.toPlainText()

    # run basic analysis
    window.users_A_var.setText("100")
    window.conv_A_var.setText("10")
    window.users_B_var.setText("100")
    window.conv_B_var.setText("20")
    window.users_C_var.setText("0")
    window.conv_C_var.setText("0")

    qtbot.mouseClick(window.analyze_button, Qt.MouseButton.LeftButton)

    assert "Winner" in window.results_text.toPlainText()
