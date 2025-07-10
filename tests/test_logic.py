import os
import sys
import types
import statistics
import math
import csv
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Minimal stubs for optional dependencies
if 'numpy' not in sys.modules:
    np_mod = types.ModuleType('numpy')
    def linspace(a, b, n):
        step = (b - a) / (n - 1)
        return [a + step * i for i in range(n)]
    np_mod.linspace = linspace
    np_mod.trapz = lambda y, x: sum((y[i] + y[i+1]) * (x[i+1] - x[i]) / 2 for i in range(len(y)-1))
    np_mod.random = types.SimpleNamespace(binomial=lambda n, p, size=None: [0])
    sys.modules['numpy'] = np_mod

if 'scipy.stats' not in sys.modules:
    nd = statistics.NormalDist()
    class Norm:
        @staticmethod
        def ppf(p):
            return nd.inv_cdf(p)
        @staticmethod
        def cdf(x):
            return nd.cdf(x)
    stats_mod = types.ModuleType('scipy.stats')
    stats_mod.norm = Norm
    stats_mod.beta = types.SimpleNamespace(pdf=lambda *a, **k: None,
                                           cdf=lambda *a, **k: None)
    scipy_mod = types.ModuleType('scipy')
    scipy_mod.stats = stats_mod
    sys.modules['scipy'] = scipy_mod
    sys.modules['scipy.stats'] = stats_mod

if 'plotly.graph_objects' not in sys.modules:
    plotly_mod = types.ModuleType('plotly')
    go_mod = types.ModuleType('graph_objects')
    plotly_mod.graph_objects = go_mod
    sys.modules['plotly'] = plotly_mod
    sys.modules['plotly.graph_objects'] = go_mod

if 'PyQt6.QtWidgets' not in sys.modules:
    pyqt6_mod = types.ModuleType('PyQt6')
    widgets_mod = types.ModuleType('PyQt6.QtWidgets')
    class QFileDialog:
        @staticmethod
        def getSaveFileName(*args, **kwargs):
            return ('', '')
    widgets_mod.QFileDialog = QFileDialog
    class QMessageBox:
        @staticmethod
        def critical(*args, **kwargs):
            pass
    widgets_mod.QMessageBox = QMessageBox
    pyqt6_mod.QtWidgets = widgets_mod
    sys.modules['PyQt6'] = pyqt6_mod
    sys.modules['PyQt6.QtWidgets'] = widgets_mod

if 'pandas' not in sys.modules:
    sys.modules['pandas'] = types.ModuleType('pandas')

if 'reportlab' not in sys.modules:
    rl_mod = types.ModuleType('reportlab')
    lib_mod = types.ModuleType('reportlab.lib')
    pagesizes_mod = types.ModuleType('reportlab.lib.pagesizes')
    pagesizes_mod.letter = (0, 0)
    pdfgen_mod = types.ModuleType('reportlab.pdfgen')
    pdfgen_mod.canvas = types.SimpleNamespace(Canvas=lambda *a, **k: None)
    pdfbase_mod = types.ModuleType('reportlab.pdfbase')
    pdfmetrics_mod = types.ModuleType('reportlab.pdfbase.pdfmetrics')
    pdfmetrics_mod.registerFont = lambda *a, **k: None
    ttfonts_mod = types.ModuleType('reportlab.pdfbase.ttfonts')
    ttfonts_mod.TTFont = type('TTFont', (), {})
    rl_mod.lib = lib_mod
    rl_mod.pdfgen = pdfgen_mod
    rl_mod.pdfbase = pdfbase_mod
    sys.modules['reportlab'] = rl_mod
    sys.modules['reportlab.lib'] = lib_mod
    sys.modules['reportlab.lib.pagesizes'] = pagesizes_mod
    sys.modules['reportlab.pdfgen'] = pdfgen_mod
    sys.modules['reportlab.pdfbase'] = pdfbase_mod
    sys.modules['reportlab.pdfbase.pdfmetrics'] = pdfmetrics_mod
    sys.modules['reportlab.pdfbase.ttfonts'] = ttfonts_mod

from logic import (
    required_sample_size,
    evaluate_abn_test,
    run_obrien_fleming,
)


def test_required_sample_size_positive():
    n = required_sample_size(0.1, 0.15, 0.05, 0.8)
    assert math.isfinite(n) and n > 0


def test_evaluate_abn_test_no_difference():
    res = evaluate_abn_test(1000, 100, 1000, 100, 1000, 100)
    assert not res['significant_ab']
    assert not res['significant_ac']


def test_evaluate_abn_test_invalid_counts():
    with pytest.raises(ValueError):
        evaluate_abn_test(10, -1, 10, 0)

    with pytest.raises(ValueError):
        evaluate_abn_test(10, 5, 10, 11)

    with pytest.raises(ValueError):
        evaluate_abn_test(10, 5, 10, 5, 5, 6)


def test_evaluate_abn_test_fdr_adjustment():
    res = evaluate_abn_test(100, 10, 100, 20, metrics=2, alpha=0.05)
    assert 'p_value_fdr' in res
    assert math.isclose(res['p_value_fdr'], min(res['p_value_ab'] * 2, 1.0))


def test_run_obrien_fleming_steps():
    steps = run_obrien_fleming(100, 10, 100, 20, alpha=0.05, looks=3)
    assert isinstance(steps, list) and steps
    assert 'threshold' in steps[0]
