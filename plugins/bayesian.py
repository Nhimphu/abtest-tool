"""Optional Bayesian analysis implementation using numpy and scipy."""
from typing import Tuple

import numpy as np
from numpy import linspace

try:  # optional dependency
    from scipy.stats import beta
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    import logging

    logging.warning(
        "scipy is not installed; the bayesian plugin will be disabled"
    )
    raise

from metrics import track_time

__all__ = ["bayesian_analysis", "linspace"]

# ``np.trapz`` is deprecated in favour of ``np.trapezoid`` in newer numpy
# versions.  When running under lightweight stubs that do not provide
# ``trapezoid`` we gracefully fall back to ``trapz``.
_trapz = getattr(np, "trapezoid", np.trapz)


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

    prob = float(_trapz(pdf_b * cdf_a, x))

    def _to_list(arr):
        return arr.tolist() if hasattr(arr, "tolist") else list(arr)

    return prob, x, _to_list(pdf_a), _to_list(pdf_b)

