import os
import sys
import types
import random
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# stub pandas if missing
if 'pandas' not in sys.modules:
    pd_mod = types.ModuleType('pandas')
    pd_mod.DataFrame = type('DataFrame', (), {})
    sys.modules['pandas'] = pd_mod

try:  # provide minimal numpy if real package missing
    import numpy as np  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed in stripped envs
    np_mod = types.ModuleType("numpy")

    class Arr(list):
        @property
        def size(self):
            return len(self)

        def mean(self):
            return sum(self) / len(self)

        def __sub__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v - other for v in self)
            return Arr(v - w for v, w in zip(self, other))

        def __rsub__(self, other):
            if isinstance(other, (int, float)):
                return Arr(other - v for v in self)
            return Arr(w - v for v, w in zip(self, other))

        def __pow__(self, power):
            return Arr(v ** power for v in self)

        def __mul__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v * other for v in self)
            return Arr(v * w for v, w in zip(self, other))

        __rmul__ = __mul__

        def __truediv__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v / other for v in self)
            return Arr(v / w for v, w in zip(self, other))

        def __rtruediv__(self, other):
            if isinstance(other, (int, float)):
                return Arr(other / v for v in self)
            return Arr(w / v for v, w in zip(self, other))

        def __add__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v + other for v in self)
            return Arr(v + w for v, w in zip(self, other))

        __radd__ = __add__

        def __gt__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v > other for v in self)
            return Arr(v > w for v, w in zip(self, other))

        def __ge__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v >= other for v in self)
            return Arr(v >= w for v, w in zip(self, other))

        def __le__(self, other):
            if isinstance(other, (int, float)):
                return Arr(v <= other for v in self)
            return Arr(v <= w for v, w in zip(self, other))

        def __and__(self, other):
            return Arr(bool(v) and bool(w) for v, w in zip(self, other))

    def asarray(x, dtype=None):
        if isinstance(x, Arr):
            return x
        return Arr(x)

    def linspace(a, b, n):
        step = (b - a) / (n - 1)
        return Arr(a + i * step for i in range(n))

    def trapz(y, x):
        return sum((y[i] + y[i + 1]) * (x[i + 1] - x[i]) / 2 for i in range(len(y) - 1))

    def clip(arr, lo, hi):
        return Arr(max(lo, min(hi, v)) for v in arr)

    def mean(arr):
        return sum(arr) / len(arr)

    def vectorize(func):
        return lambda arr: Arr(func(v) for v in arr)

    np_mod.asarray = asarray
    np_mod.linspace = linspace
    np_mod.trapz = trapz
    np_mod.clip = clip
    np_mod.mean = mean
    np_mod.sum = lambda arr: sum(arr)
    def sqrt(x):
        if isinstance(x, Arr):
            return Arr(math.sqrt(v) for v in x)
        return math.sqrt(x)

    np_mod.sqrt = sqrt
    np_mod.vectorize = vectorize
    np_mod.ndarray = Arr

    class RNG:
        def __init__(self, seed=None):
            self._rng = random.Random(seed)

        def normal(self, loc=0.0, scale=1.0, size=None):
            if size is None:
                return self._rng.gauss(loc, scale)
            if isinstance(scale, Arr):
                return Arr(self._rng.gauss(loc, s) for s in scale)
            return Arr(self._rng.gauss(loc, scale) for _ in range(size))

        def gamma(self, shape, scale=1.0, size=None):
            if size is None:
                return self._rng.gammavariate(shape, scale)
            return Arr(self._rng.gammavariate(shape, scale) for _ in range(size))

    def default_rng(seed=None):
        return RNG(seed)

    rand_mod = types.ModuleType("numpy.random")
    rand_mod.default_rng = default_rng
    rand_mod.Generator = RNG
    np_mod.random = rand_mod

    sys.modules["numpy"] = np_mod
    sys.modules["numpy.random"] = rand_mod
    np = np_mod

from abtest_core.bayes import prob_win_binomial, prob_win_continuous


def test_prob_win_binomial_sanity():
    res = prob_win_binomial(40, 200, 80, 200)
    assert res["p_win"] > 0.95
    res_rope = prob_win_binomial(40, 200, 80, 200, rope=(-0.02, 0.02))
    assert res_rope["p_rope"] < 0.1


def test_prob_win_continuous_sanity():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 400)
    b = rng.normal(0.2, 1, 400)
    res = prob_win_continuous(a, b)
    assert res["p_win"] > 0.8
    res_rope = prob_win_continuous(a, b, rope=(-0.05, 0.05))
    assert res_rope["p_rope"] < 0.2
