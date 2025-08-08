import random
from abtest_core.srm import srm_check


def test_srm_equal_counts_pass():
    res = srm_check({"A": 100, "B": 100})
    assert res["passed"]


def test_srm_detects_imbalance():
    res = srm_check({"A": 1000, "B": 100})
    assert not res["passed"]


def test_srm_false_positive_rate():
    alpha = 0.001
    trials = 500
    n = 1000
    rng = random.Random(0)
    fails = 0
    for _ in range(trials):
        a = sum(1 for _ in range(n) if rng.random() < 0.5)
        b = n - a
        res = srm_check({"A": a, "B": b}, alpha=alpha)
        if not res["passed"]:
            fails += 1
    rate = fails / trials
    assert abs(rate - alpha) < 0.005
