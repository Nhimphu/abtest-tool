"""Optional Bayesian analysis implementation using numpy and scipy."""
from typing import Tuple
from collections.abc import Iterable, Iterator

import numpy as np


def linspace(start: float, stop: float, num: int):
    """Return a list of evenly spaced floats from ``start`` to ``stop``."""
    return [float(v) for v in np.linspace(start, stop, num)]


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

try:  # optional dependency
    from scipy.stats import beta
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    import logging

    logging.warning(
        "scipy is not installed; the bayesian plugin will be disabled"
    )
    raise

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
    pdf_a = beta.pdf(x, a1, b1)
    pdf_b = beta.pdf(x, a2, b2)
    cdf_a = beta.cdf(x, a1, b1)

    # use the newer ``trapezoid`` integration to avoid deprecation warnings
    prob = float(np.trapezoid(pdf_b * cdf_a, x))

    return float(prob), x, pdf_a, pdf_b

