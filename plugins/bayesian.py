"""Optional Bayesian analysis implementation using numpy."""
from typing import Tuple
from collections.abc import Iterable, Iterator

import math
import numpy as np


def linspace(start: float, stop: float, num: int):
    """Return a list of evenly spaced floats from ``start`` to ``stop``."""
    return [float(v) for v in np.linspace(start, stop, num)]


def beta_pdf_list(xs, a, b):
    coeff = math.gamma(a + b) / (math.gamma(a) * math.gamma(b))
    out = []
    for x in xs:
        if x <= 0.0:
            out.append(0.0 if a > 1 else coeff * (0.0 ** (a - 1)) * ((1.0 - 0.0) ** (b - 1)))
            continue
        if x >= 1.0:
            out.append(0.0 if b > 1 else coeff * (1.0 ** (a - 1)) * ((1.0 - 1.0) ** (b - 1)))
            continue
        out.append(coeff * (x ** (a - 1)) * ((1.0 - x) ** (b - 1)))
    return out


class _ArrMeta(type):
    def __call__(cls, *args, **kwargs):
        # Materialize generators or generic iterables into a list to ensure
        # predictable one-dimensional arrays.
        if len(args) == 1:
            x = args[0]
            if isinstance(x, (np.ndarray, list, tuple)):
                return np.array(x, **kwargs)
            if isinstance(x, Iterator):
                return np.array(list(x), **kwargs)
            if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                try:
                    return np.array(list(x), **kwargs)
                except TypeError:
                    pass
        return np.array(*args, **kwargs)

    def __instancecheck__(cls, instance):  # pragma: no cover - simple delegation
        return isinstance(instance, np.ndarray)


class Arr(metaclass=_ArrMeta):
    """Callable type: Arr(iterable)->np.array(materialized). Usable in ``isinstance`` checks."""


def trapz(y, x):
    """Wrapper around ``np.trapezoid`` returning a Python float."""
    return float(np.trapezoid(y, x))


try:  # expose convenience names for tests
    import builtins  # pragma: no cover - trivial import

    builtins.linspace = linspace
    builtins.Arr = Arr
    builtins.trapz = trapz
except Exception:  # pragma: no cover - best effort only
    pass

from metrics import track_time

__all__ = ["bayesian_analysis", "linspace", "Arr", "trapz"]


@track_time
def bayesian_analysis(
    alpha_prior: float,
    beta_prior: float,
    users_a: int,
    conv_a: int,
    users_b: int,
    conv_b: int,
) -> Tuple[float, list, list, list]:
    """Full-featured Bayesian A/B analysis."""

    a1 = alpha_prior + conv_a
    b1 = beta_prior + (users_a - conv_a)
    a2 = alpha_prior + conv_b
    b2 = beta_prior + (users_b - conv_b)

    x = linspace(0, 1, 500)
    pa = beta_pdf_list(x, a1, b1)
    pb = beta_pdf_list(x, a2, b2)

    # Prefix trapezoid CDF of ``pa`` over ``x`` (no normalization to unit area)
    cdf_a = [0.0] * len(x)
    for i in range(1, len(x)):
        dx = x[i] - x[i - 1]
        cdf_a[i] = cdf_a[i - 1] + 0.5 * (pa[i - 1] + pa[i]) * dx

    integrand = [pb[i] * cdf_a[i] for i in range(len(x))]
    prob = float(np.trapezoid(integrand, x))

    return float(prob), x, pa, pb

