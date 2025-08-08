import math
from abtest_core.sequential import make_plan, pocock_thresholds, obf_thresholds, sequential_test


def test_pocock_shape():
    th = pocock_thresholds(5, 0.05)
    assert len(th) == 5
    assert all(abs(v - th[0]) < 1e-12 for v in th)
    assert abs(sum(th) - 0.05) < 1e-12


def test_obf_shape_and_spending():
    th = obf_thresholds(5, 0.05)
    assert len(th) == 5
    assert th[0] < th[-1]
    assert abs(sum(th) - 0.05) < 1e-12
    plan = make_plan(5, 0.05, "obf")
    assert all(plan["cum"][i] <= plan["cum"][i + 1] for i in range(4))


def test_decisions():
    plan = make_plan(5, 0.05, "pocock")
    d = sequential_test([0.5, 0.2, 0.2], plan)
    assert d["stop"] is False and d["look"] == 3
    d = sequential_test([1e-6], plan)
    assert d["stop"] is True and d["look"] == 1
    d = sequential_test([0.5, 0.2, plan["thresholds"][2] / 2], plan)
    assert d["stop"] is True and d["look"] == 3
