import os
import sys
import types
import statistics
import math
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Minimal stubs for optional dependencies
if 'numpy' not in sys.modules:
    sys.modules['numpy'] = types.ModuleType('numpy')

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
    pyqt6_mod.QtWidgets = widgets_mod
    sys.modules['PyQt6'] = pyqt6_mod
    sys.modules['PyQt6.QtWidgets'] = widgets_mod

from logic import required_sample_size, evaluate_abn_test


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
