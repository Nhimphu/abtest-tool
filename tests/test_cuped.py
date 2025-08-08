import numpy as np
import pandas as pd

from abtest_core.cuped import estimate_theta, apply_cuped
from abtest_core.types import AnalysisConfig
from abtest_core.engine import analyze_groups


def _simulate(corr: float, n: int = 1000):
    cov = [[1, corr], [corr, 1]]
    data = np.random.default_rng(0).multivariate_normal([0, 0], cov, size=n)
    pre, post = data[:, 0], data[:, 1]
    return pre, post


def test_cuped_reduces_variance():
    pre, post = _simulate(0.5, 2000)
    stats = estimate_theta(pre, post)
    adjusted = apply_cuped(post, pre, stats["theta"])
    assert np.var(adjusted, ddof=1) < np.var(post, ddof=1)


def test_cuped_skips_when_correlation_low():
    pre, post = _simulate(0.0, 2000)
    df = pd.DataFrame(
        {
            "group": ["A"] * 1000 + ["B"] * 1000,
            "metric": post,
            "pre": pre,
        }
    )
    config = AnalysisConfig(
        alpha=0.05,
        metric_type="continuous",
        use_cuped=True,
        preperiod_metric_col="pre",
    )
    res = analyze_groups(df, config)
    assert "CUPED" in res.method_notes
    assert "skipped" in res.method_notes
