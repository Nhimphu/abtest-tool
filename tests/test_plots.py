import os
import sys
import types
import statistics
import math
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Stubs for optional dependencies
if "plugin_loader" not in sys.modules:
    pl = types.ModuleType("plugin_loader")
    pl.load_plugins = lambda: None
    pl.get_plugin = lambda name: None
    sys.modules["plugin_loader"] = pl

if "numpy" not in sys.modules:
    np_mod = types.ModuleType("numpy")

    def linspace(a, b, n):
        step = (b - a) / (n - 1)
        return [a + step * i for i in range(n)]

    np_mod.linspace = linspace
    np_mod.asarray = lambda x, dtype=None: list(x)
    np_mod.argmax = lambda arr: arr.index(max(arr))
    np_mod.trapz = lambda y, x: sum(
        (y[i] + y[i + 1]) * (x[i + 1] - x[i]) / 2 for i in range(len(y) - 1)
    )
    rand_mod = types.ModuleType("numpy.random")
    rand_mod.binomial = lambda n, p, size=None: [0]
    rand_mod.randint = lambda a, b=None: 0
    rand_mod.random = lambda: 0.0
    np_mod.random = rand_mod
    sys.modules["numpy"] = np_mod
    sys.modules["numpy.random"] = rand_mod

if "scipy.stats" not in sys.modules:
    nd = statistics.NormalDist()

    class Norm:
        @staticmethod
        def ppf(p):
            return nd.inv_cdf(p)

        @staticmethod
        def cdf(x):
            return nd.cdf(x)

    stats_mod = types.ModuleType("scipy.stats")
    stats_mod.norm = Norm
    stats_mod.beta = types.SimpleNamespace(
        pdf=lambda *a, **k: None, cdf=lambda *a, **k: None
    )
    stats_mod.chi2 = types.SimpleNamespace(cdf=lambda x, df: 1 - math.exp(-x / 2))
    scipy_mod = types.ModuleType("scipy")
    scipy_mod.stats = stats_mod
    sys.modules["scipy"] = scipy_mod
    sys.modules["scipy.stats"] = stats_mod

plotly_mod = types.ModuleType("plotly")
go_mod = types.ModuleType("graph_objects")


class FakeScatter:
    def __init__(self, x=None, y=None, mode=None, **kwargs):
        self.x = list(x) if x is not None else []
        self.y = list(y) if y is not None else []
        self.mode = mode


class FakeFigure:
    def __init__(self):
        self.data = []

    def add_trace(self, trace):
        self.data.append(trace)

    def update_layout(self, *a, **k):
        pass

    def write_image(self, path, format=None):
        with open(path, "wb") as f:
            f.write(b"PNG")


go_mod.Figure = lambda *a, **k: FakeFigure()
go_mod.Scatter = FakeScatter
plotly_mod.graph_objects = go_mod
sys.modules["plotly"] = plotly_mod
sys.modules["plotly.graph_objects"] = go_mod

import plots as _plots

importlib.reload(_plots)
from plots import plot_alpha_spending, plot_confidence_intervals, plot_power_curve


def test_plot_alpha_spending_png(tmp_path):
    fig = plot_alpha_spending(0.05, 4)
    path = tmp_path / "alpha.png"
    fig.write_image(str(path))
    assert path.exists() and path.stat().st_size > 0
    assert len(fig.data) == 2
    assert all(len(t.x) == 4 for t in fig.data)


def test_plot_confidence_intervals_png(tmp_path):
    fig = plot_confidence_intervals(100, 10, 120, 20, alpha=0.05)
    path = tmp_path / "ci.png"
    fig.write_image(str(path))
    assert path.exists() and path.stat().st_size > 0
    assert len(fig.data) == 2
    assert all(len(t.x) == 2 for t in fig.data)


def test_plot_power_curve_png(tmp_path):
    fig = plot_power_curve(0.1, 0.05, 0.8)
    path = tmp_path / "power.png"
    fig.write_image(str(path))
    assert path.exists() and path.stat().st_size > 0
    assert len(fig.data) == 1
    assert len(fig.data[0].x) == 100
