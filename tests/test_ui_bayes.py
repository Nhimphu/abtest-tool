import os
import sys
import types
import math
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Provide minimal numpy/scipy stubs so the plugin can be imported

np_mod = types.ModuleType('numpy')

class Arr(list):
    def __mul__(self, other):
        if isinstance(other, (list, Arr)):
            return Arr(a*b for a, b in zip(self, other))
        return Arr(a*other for a in self)
    __rmul__ = __mul__

def linspace(a, b, n):
    step = (b - a) / (n - 1)
    return Arr(a + step * i for i in range(n))

np_mod.linspace = linspace

def trapz(y, x):
    return sum((y[i] + y[i+1]) * (x[i+1] - x[i]) / 2 for i in range(len(y)-1))

np_mod.trapz = trapz
np_mod.ndarray = list
sys.modules['numpy'] = np_mod

# simple beta pdf/cdf helpers

def beta_pdf(x, a, b):
    coeff = math.gamma(a + b) / (math.gamma(a) * math.gamma(b))
    if isinstance(x, (list, Arr)):
        return Arr(beta_pdf(v, a, b) for v in x)
    return coeff * (x ** (a - 1)) * ((1 - x) ** (b - 1))


def beta_cdf(x, a, b):
    if isinstance(x, (list, Arr)):
        return Arr(beta_cdf(v, a, b) for v in x)
    n = 1000
    step = x / n
    total = 0.0
    for i in range(n):
        x1 = i * step
        x2 = x1 + step
        total += (beta_pdf(x1, a, b) + beta_pdf(x2, a, b)) * step / 2
    return total

stats_mod = types.ModuleType('scipy.stats')
stats_mod.beta = types.SimpleNamespace(pdf=beta_pdf, cdf=beta_cdf)
scipy_mod = types.ModuleType('scipy')
scipy_mod.stats = stats_mod
sys.modules['scipy'] = scipy_mod
sys.modules['scipy.stats'] = stats_mod

# Stub plotly module required by ui_mainwindow imports
plotly_mod = types.ModuleType('plotly')
go_mod = types.ModuleType('graph_objects')
plotly_mod.graph_objects = go_mod
sys.modules['plotly'] = plotly_mod
sys.modules['plotly.graph_objects'] = go_mod

# Minimal PyQt6 stubs for ui_mainwindow import
pyqt6_mod = types.ModuleType('PyQt6')
widgets_mod = types.ModuleType('PyQt6.QtWidgets')
gui_mod = types.ModuleType('PyQt6.QtGui')
core_mod = types.ModuleType('PyQt6.QtCore')
for name in [
    'QApplication', 'QMainWindow', 'QWidget', 'QVBoxLayout', 'QHBoxLayout',
    'QGridLayout', 'QLabel', 'QLineEdit', 'QPushButton', 'QSlider',
    'QDoubleSpinBox', 'QTabWidget', 'QTableWidget', 'QTableWidgetItem',
    'QProgressBar', 'QTextBrowser', 'QComboBox', 'QGroupBox'
]:
    setattr(widgets_mod, name, type(name, (), {}))
class QFileDialog:
    @staticmethod
    def getSaveFileName(*a, **k):
        return ('', '')
    @staticmethod
    def getOpenFileName(*a, **k):
        return ('', '')
widgets_mod.QFileDialog = QFileDialog
class QMessageBox:
    @staticmethod
    def information(*a, **k):
        pass
    @staticmethod
    def critical(*a, **k):
        pass
    @staticmethod
    def warning(*a, **k):
        pass
widgets_mod.QMessageBox = QMessageBox
for name in ['QPalette', 'QColor', 'QIntValidator', 'QDoubleValidator', 'QAction']:
    setattr(gui_mod, name, type(name, (), {}))
core_mod.Qt = type('Qt', (), {})
core_mod.QDateTime = type('QDateTime', (), {})
core_mod.QDir = type('QDir', (), {'addSearchPath': staticmethod(lambda *a, **k: None)})
pyqt6_mod.QtWidgets = widgets_mod
pyqt6_mod.QtGui = gui_mod
pyqt6_mod.QtCore = core_mod
sys.modules['PyQt6'] = pyqt6_mod
sys.modules['PyQt6.QtWidgets'] = widgets_mod
sys.modules['PyQt6.QtGui'] = gui_mod
sys.modules['PyQt6.QtCore'] = core_mod

import plugin_loader
importlib.reload(plugin_loader)

from plugins import bayesian
from ui import ui_mainwindow


def test_bayesian_analysis_computes_probability():
    prob, x, pa, pb = bayesian.bayesian_analysis(1, 1, 100, 10, 120, 20)
    a1 = 1 + 10
    b1 = 1 + 90
    a2 = 1 + 20
    b2 = 1 + 100
    expected_x = linspace(0, 1, 500)
    expected_pa = beta_pdf(expected_x, a1, b1)
    expected_pb = beta_pdf(expected_x, a2, b2)
    expected_cdf_a = beta_cdf(expected_x, a1, b1)
    expected_prob = trapz([expected_pb[i] * expected_cdf_a[i] for i in range(len(expected_x))], expected_x)
    assert abs(prob - expected_prob) < 1e-6
    assert x == expected_x
    assert pa == expected_pa
    assert pb == expected_pb


def test_ui_renders_bayes(monkeypatch):
    called = {}

    class DummyWindow:
        users_A_var = types.SimpleNamespace(text=lambda: '100')
        conv_A_var = types.SimpleNamespace(text=lambda: '10')
        users_B_var = types.SimpleNamespace(text=lambda: '120')
        conv_B_var = types.SimpleNamespace(text=lambda: '20')
        prior_alpha_spin = types.SimpleNamespace(value=lambda: 1.0)
        prior_beta_spin = types.SimpleNamespace(value=lambda: 1.0)
        results_text = types.SimpleNamespace(setHtml=lambda html: called.setdefault('html', html))
        _add_history = lambda *a, **k: None

    monkeypatch.setattr(plugin_loader, 'get_plugin', lambda name: types.SimpleNamespace(bayesian_analysis=lambda *a: (0.6, [], [], [])))
    monkeypatch.setattr(ui_mainwindow, 'plot_bayesian_posterior', lambda *a, **k: 'fig')
    monkeypatch.setattr(ui_mainwindow, 'PlotWindow', lambda *a, **k: types.SimpleNamespace(display_plot=lambda f: called.setdefault('fig', f)))

    ui_mainwindow.ABTestWindow._on_run_bayes(DummyWindow())

    assert '60' in called['html']
    assert called['fig'] == 'fig'
