"""Optional Bayesian analysis implementation using lightweight numpy helpers."""

import math
import numpy as np
from collections.abc import Iterable, Iterator


# ---------------------------------------------------------------------------
# Compatibility shims used by tests
# ---------------------------------------------------------------------------

def trapz(y, x):
    """Return the integral of *y* with respect to *x* using the trapezoid rule."""
    return float(np.trapezoid(y, x))


def linspace(a, b, n):
    """Return a Python list of evenly spaced floats."""
    return [float(v) for v in np.linspace(a, b, n)]


class _ArrMeta(type):
    def __call__(cls, *args, **kwargs):
        if len(args) == 1:
            x = args[0]
            if isinstance(x, (np.ndarray, list, tuple)):
                return np.array(x, **kwargs)
            if isinstance(x, Iterator):
                return np.array(list(x), **kwargs)
            if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                return np.array(list(x), **kwargs)
        return np.array(*args, **kwargs)


class Arr(metaclass=_ArrMeta):
    pass


try:  # expose shims for tests expecting bare names
    import builtins

    builtins.linspace = linspace
    builtins.Arr = Arr
    builtins.trapz = trapz
except Exception:  # pragma: no cover - best effort only
    pass


# ---------------------------------------------------------------------------
# Core beta PDF/CDF utilities
# ---------------------------------------------------------------------------

def beta_pdf_scalar(x, a, b):
    return math.gamma(a + b) / (math.gamma(a) * math.gamma(b)) * (x ** (a - 1)) * ((1.0 - x) ** (b - 1))


def beta_pdf_list(xs, a, b):
    return [beta_pdf_scalar(v, a, b) for v in xs]


def beta_cdf_scalar(x, a, b, n=1000):
    if x <= 0.0:
        return 0.0
    step = x / n
    total = 0.0
    for i in range(n):
        x1 = i * step
        x2 = x1 + step
        total += (beta_pdf_scalar(x1, a, b) + beta_pdf_scalar(x2, a, b)) * step * 0.5
    return total


def beta_cdf_list(xs, a, b):
    return [beta_cdf_scalar(v, a, b) for v in xs]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["bayesian_analysis", "linspace", "Arr", "trapz"]


def bayesian_analysis(prior_a, prior_b, nA, succA, nB, succB):
    a1 = prior_a + succA
    b1 = prior_b + (nA - succA)
    a2 = prior_a + succB
    b2 = prior_b + (nB - succB)

    x = linspace(0, 1, 500)
    pa = beta_pdf_list(x, a1, b1)
    pb = beta_pdf_list(x, a2, b2)
    cdf_a = beta_cdf_list(x, a1, b1)
    integrand = [pb[i] * cdf_a[i] for i in range(len(x))]
    prob = trapz(integrand, x)

    return float(prob), x, pa, pb

