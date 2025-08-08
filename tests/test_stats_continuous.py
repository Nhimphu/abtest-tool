import numpy as np
import pytest

from abtest_core.stats_continuous import welch_ttest, yuen_trimmed_mean_test, bootstrap_bca_ci


def test_welch_ttest():
    np.random.seed(0)
    a = np.random.normal(0, 1, 200)
    b = np.random.normal(0.5, 1, 180)
    mean1, var1, n1 = a.mean(), a.var(ddof=1), len(a)
    mean2, var2, n2 = b.mean(), b.var(ddof=1), len(b)
    res = welch_ttest(mean1, var1, n1, mean2, var2, n2)
    diff = mean2 - mean1
    assert diff > 0
    lo, hi = res["ci"]
    assert lo < diff < hi
    assert res["p_value"] < 0.05


def test_yuen_trimmed_mean():
    np.random.seed(1)
    a = np.concatenate([np.random.normal(0, 1, 200), np.array([20])])
    b = np.random.normal(1, 1, 201)
    res = yuen_trimmed_mean_test(a, b, trim=0.2)
    eff = res["effect"]
    assert eff > 0
    lo, hi = res["ci"]
    assert lo < eff < hi
    assert res["p_value"] < 0.05


def test_bootstrap_bca_ci():
    np.random.seed(2)
    a = np.random.normal(0, 1, 50)
    b = np.random.normal(0.5, 1, 50)
    fn = lambda x, y: np.mean(y) - np.mean(x)
    lo, hi = bootstrap_bca_ci(a, b, fn, iters=2000)
    diff = fn(a, b)
    assert lo < diff < hi
