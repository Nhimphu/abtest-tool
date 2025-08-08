import numpy as np
import pytest

from abtest_core.stats_ratio import ratio_test


def test_ratio_delta_and_fieller():
    np.random.seed(0)
    a = np.random.normal(10, 2, 200)
    b = np.random.normal(12, 2, 180)
    mean1, var1, n1 = a.mean(), a.var(ddof=1), len(a)
    mean2, var2, n2 = b.mean(), b.var(ddof=1), len(b)
    effect = mean2 / mean1

    res_delta = ratio_test(mean1, var1, n1, mean2, var2, n2)
    assert res_delta["effect"] == pytest.approx(effect)
    lo, hi = res_delta["ci"]
    assert lo < effect < hi
    assert res_delta["p_value"] < 0.05

    res_fieller = ratio_test(mean1, var1, n1, mean2, var2, n2, fieller=True)
    lo2, hi2 = res_fieller["ci"]
    assert lo2 < effect < hi2
    assert "fieller" in res_fieller["notes"]

