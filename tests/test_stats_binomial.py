import pytest
from abtest_core.stats_binomial import wilson_ci, newcombe_ci, prop_diff_test


def test_binomial_ci_and_test():
    x1, n1 = 40, 200
    x2, n2 = 80, 200
    p1 = x1 / n1
    p2 = x2 / n2
    diff = p2 - p1

    lo, hi = wilson_ci(x1, n1)
    assert lo < p1 < hi

    dlo, dhi = newcombe_ci(x1, n1, x2, n2)
    assert dlo < diff < dhi

    res = prop_diff_test(x1, n1, x2, n2)
    assert res["effect"] == pytest.approx(diff)
    assert res["p_value"] < 0.05
    lo, hi = res["ci"]
    assert lo < diff < hi
