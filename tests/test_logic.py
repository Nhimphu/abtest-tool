import os
import sys
import types
import statistics
import math
import csv
import pytest
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Minimal stubs for optional dependencies
if 'numpy' not in sys.modules:
    np_mod = types.ModuleType('numpy')
    def linspace(a, b, n):
        step = (b - a) / (n - 1)
        return [a + step * i for i in range(n)]
    np_mod.linspace = linspace
    np_mod.asarray = lambda x, dtype=None: list(x)
    np_mod.argmax = lambda arr: arr.index(max(arr))
    def cov(a, b, ddof=1):
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        cov_ab = sum((ai - mean_a) * (bi - mean_b) for ai, bi in zip(a, b)) / (len(a)-ddof)
        var_a = sum((ai - mean_a) ** 2 for ai in a) / (len(a)-ddof)
        var_b = sum((bi - mean_b) ** 2 for bi in b) / (len(a)-ddof)
        return [[var_a, cov_ab], [cov_ab, var_b]]
    np_mod.cov = cov
    np_mod.var = lambda x, ddof=1: sum((xi - sum(x)/len(x))**2 for xi in x) / (len(x)-ddof)
    np_mod.trapz = lambda y, x: sum((y[i] + y[i+1]) * (x[i+1] - x[i]) / 2 for i in range(len(y)-1))
    rand_mod = types.ModuleType('numpy.random')
    rand_mod.binomial = lambda n, p, size=None: [0]
    rand_mod.randint = lambda a, b=None: 0
    rand_mod.random = lambda: 0.0
    np_mod.random = rand_mod
    sys.modules['numpy'] = np_mod
    sys.modules['numpy.random'] = rand_mod

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
    stats_mod.chi2 = types.SimpleNamespace(cdf=lambda x, df: 1 - math.exp(-x/2))
    scipy_mod = types.ModuleType('scipy')
    scipy_mod.stats = stats_mod
    sys.modules['scipy'] = scipy_mod
    sys.modules['scipy.stats'] = stats_mod

if 'plotly.graph_objects' not in sys.modules:
    plotly_mod = types.ModuleType('plotly')
    go_mod = types.ModuleType('graph_objects')
    class _Fig:
        def add_trace(self, *a, **k):
            pass
        def update_layout(self, *a, **k):
            pass
    go_mod.Figure = lambda *a, **k: _Fig()
    go_mod.Scatter = lambda *a, **k: object()
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
    widgets_mod.QComboBox = type('QComboBox', (), {})
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

from stats.ab_test import (
    required_sample_size,
    evaluate_abn_test,
    run_obrien_fleming,
    cuped_adjustment,
    pocock_alpha_curve,
)
from bandit.strategies import ucb1, epsilon_greedy
from plots import plot_alpha_spending
from utils import segment_data, compute_custom_metric


def test_required_sample_size_positive():
    n = required_sample_size(0.1, 0.15, 0.05, 0.8)
    assert math.isfinite(n) and n > 0


def test_evaluate_abn_test_no_difference():
    res = evaluate_abn_test(1000, 100, 1000, 100, 1000, 100)
    assert not res['significant_ab']
    assert not res['significant_ac']


def test_evaluate_abn_test_trivial_logs(caplog):
    caplog.set_level(logging.INFO)
    res = evaluate_abn_test(100, 10, 100, 10)
    assert res['p_value_ab'] == 1.0
    assert res['uplift_ab'] == 0.0
    assert not res['significant_ab']
    assert res['winner'] == 'A'
    assert any('Trivial A/A case' in r.message for r in caplog.records)


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

def test_run_obrien_fleming_threshold_used():
    steps = run_obrien_fleming(100, 10, 100, 20, alpha=0.05, looks=3)
    thr = steps[0]['threshold']
    assert steps[0]['significant_ab'] == (steps[0]['p_value_ab'] < thr)


def test_sequential_webhook_called(monkeypatch):
    import stats.ab_test as logic
    called = {}
    monkeypatch.setattr(logic, 'send_webhook', lambda url, msg: called.setdefault('url', url))
    logic.run_sequential_analysis(100, 10, 100, 50, 0.05, looks=2, webhook_url='http://example.com')
    assert called.get('url') == 'http://example.com'

def test_cuped_no_change_with_zero_covariate():
    x = [1, 2, 3]
    adjusted = cuped_adjustment(x, [0, 0, 0])
    assert all(math.isclose(a, b) for a, b in zip(x, adjusted))
def test_pocock_alpha_curve_len():
    curve = pocock_alpha_curve(0.05, 3)
    assert len(curve) == 3 and all(0 < a < 0.05 for a in curve)
    assert math.isclose(sum(curve), 0.05)


def test_ucb1_selects_unseen_arm():
    arm = ucb1([1.0, 1.0], [10, 0])
    assert arm == 1


def test_epsilon_greedy_random(monkeypatch):
    arm = epsilon_greedy([1.0, 2.0], [1, 1], epsilon=1.0)
    assert arm in (0, 1)


def test_plot_alpha_spending_returns_fig():
    fig = plot_alpha_spending(0.05, 3)
    assert fig is not None


def test_segment_and_metric():
    data = [
        {'device': 'mobile', 'users': 10, 'conv': 2},
        {'device': 'desktop', 'users': 5, 'conv': 1},
    ]
    seg = segment_data(data, device='mobile')
    assert len(seg) == 1
    metric = compute_custom_metric(data, 'sum("conv")/sum("users")')
    assert 0 < metric < 1


def test_compute_custom_metric_rejects_eval(monkeypatch):
    data = [{'users': 1, 'conv': 1}]
    with pytest.raises(ValueError):
        compute_custom_metric(data, '__import__("os").system("echo hi")')
