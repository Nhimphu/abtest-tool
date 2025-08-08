import pandas as pd
import pytest
import random
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from abtest_core.multiple import holm, benjamini_yekutieli
from abtest_core.engine import analyze_groups
from abtest_core.types import AnalysisConfig


def test_holm_properties():
    pvals = [0.001, 0.02, 0.04, 0.2]
    adj = holm(pvals)
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj_sorted = [adj[i] for i in order]
    raw_sorted = [pvals[i] for i in order]
    m = len(pvals)
    expected = []
    cur = 0.0
    for i, p in enumerate(raw_sorted):
        val = (m - i) * p
        cur = max(cur, val)
        expected.append(min(1.0, cur))
    for i in range(1, m):
        assert adj_sorted[i] >= adj_sorted[i - 1]
    assert all(abs(a - b) < 1e-12 for a, b in zip(adj_sorted, expected))
    for a, b in zip(adj, pvals):
        assert a >= b


def test_by_basic():
    pvals = [0.001, 0.02, 0.04, 0.2]
    adj = benjamini_yekutieli(pvals)
    order_raw = sorted(range(len(pvals)), key=lambda i: pvals[i])
    order_adj = sorted(range(len(adj)), key=lambda i: adj[i])
    assert order_raw == order_adj
    for a, b in zip(adj, pvals):
        assert a >= b
    rng = random.Random(0)
    m, sims = 8, 200
    total = 0
    for _ in range(sims):
        pv = [rng.random() for _ in range(m)]
        adj_pv = benjamini_yekutieli(pv)
        total += sum(1 for p in adj_pv if p <= 0.1)
    fdr = total / (m * sims)
    assert fdr <= 0.12


def test_segment_integration_smoke():
    df = pd.DataFrame({
        "group": ["A", "A", "B", "B", "A", "B", "A", "B"],
        "metric": [1, 0, 1, 0, 1, 1, 0, 0],
        "seg": ["US", "US", "US", "US", "EU", "EU", "EU", "EU"],
    })
    config = AnalysisConfig(alpha=0.05, metric_type="binomial", segments=["seg"], multiple_testing="holm")
    res = analyze_groups(df, config)
    assert res.segments is not None
    assert len(res.segments) == 2
    for seg in res.segments:
        assert "p_adj" in seg
        assert seg["p_adj"] >= seg["p_raw"]
