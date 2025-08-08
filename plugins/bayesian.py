"""Optional Bayesian analysis implementation using lightweight numpy helpers."""

import math
import numpy as np
from collections.abc import Iterable, Iterator


# ---------------------------------------------------------------------------
# Compatibility shims used by tests
# ---------------------------------------------------------------------------

def linspace(start: float, stop: float, num: int):
    """Return a Python list of evenly spaced floats."""
    return [float(v) for v in np.linspace(start, stop, num)]


def trapz(y, x):
    """Return the integral of *y* with respect to *x* using the trapezoid rule."""
    return float(np.trapezoid(y, x))


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

def beta_pdf_list(xs, a, b):
    coeff = math.gamma(a + b) / (math.gamma(a) * math.gamma(b))
    out = []
    for x in xs:
        out.append(coeff * (x ** (a - 1)) * ((1.0 - x) ** (b - 1)))
    return out


def beta_cdf_prefix(xs, pdf_values):
    cdf = [0.0] * len(xs)
    for i in range(1, len(xs)):
        cdf[i] = trapz(pdf_values[: i + 1], xs[: i + 1])
    return cdf


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

    cdf_a = beta_cdf_prefix(x, pa)
    integrand = [pb[i] * cdf_a[i] for i in range(len(x))]
    prob = trapz(integrand, x)

    return float(prob), x, pa, pb

