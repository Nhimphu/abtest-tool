from __future__ import annotations

from typing import Sequence, Optional, Dict

import pandas as pd
import numpy as np


def apply_cuped(post: Sequence[float], pre: Sequence[float], theta: float) -> "np.ndarray":
    """Return CUPED-adjusted post metrics."""
    post_arr = np.asarray(post, dtype=float)
    pre_arr = np.asarray(pre, dtype=float)
    return post_arr - theta * pre_arr


def estimate_theta(
    pre: Sequence[float],
    post: Sequence[float],
    ridge_alpha: Optional[float] = None,
) -> Dict[str, float]:
    """Estimate optimal theta and report variance reduction.

    Theta is estimated as cov(pre, post)/var(pre). If ``ridge_alpha`` is
    provided, ``var(pre) + ridge_alpha`` is used in the denominator for
    stability. The function returns a dictionary with the estimated theta and
    the percentage of variance reduction after applying CUPED.
    """
    pre_arr = np.asarray(pre, dtype=float)
    post_arr = np.asarray(post, dtype=float)
    cov_matrix = np.cov(pre_arr, post_arr, ddof=1)
    try:
        cov = cov_matrix[0, 1]  # type: ignore[index]
    except Exception:
        cov = cov_matrix[0][1]
    var_pre = np.var(pre_arr, ddof=1)
    denom = var_pre + (ridge_alpha or 0.0)
    theta = 0.0 if denom == 0 else cov / denom
    adjusted = apply_cuped(post_arr, pre_arr, theta)
    var_post = np.var(post_arr, ddof=1)
    var_adj = np.var(adjusted, ddof=1)
    reduction = 0.0 if var_post == 0 else (1 - var_adj / var_post) * 100
    return {"theta": theta, "variance_reduction_pct": reduction}
