from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence  # noqa: F401

from .utils import lazy_import

if TYPE_CHECKING:
    from numpy.typing import NDArray
    import numpy as np  # noqa: F401


def apply_cuped(
    post: Sequence[float] | "NDArray[Any]",
    pre: Sequence[float] | "NDArray[Any]",
    theta: float,
) -> "NDArray[Any]":
    """Return CUPED-adjusted post metrics."""
    np = lazy_import("numpy")
    pre = np.asarray(pre, dtype=float)
    post = np.asarray(post, dtype=float)
    pre_c = pre - pre.mean()
    return post - theta * pre_c


def estimate_theta(
    pre: Sequence[float] | "NDArray[Any]",
    post: Sequence[float] | "NDArray[Any]",
    ridge_alpha: float = 0.0,
) -> Dict[str, Any]:
    """Estimate optimal theta and report variance reduction.

    Theta is estimated as cov(pre, post)/var(pre). If ``ridge_alpha`` is
    provided, ``var(pre) + ridge_alpha`` is used in the denominator for
    stability. The function returns a dictionary with the estimated theta and
    the percentage of variance reduction after applying CUPED.
    """
    np = lazy_import("numpy")
    pre = np.asarray(pre, dtype=float)
    post = np.asarray(post, dtype=float)
    cov_matrix = np.cov(pre, post, ddof=1)
    try:
        cov = cov_matrix[0, 1]  # type: ignore[index]
    except Exception:
        cov = cov_matrix[0][1]
    var_pre = np.var(pre, ddof=1)
    denom = var_pre + ridge_alpha
    theta = 0.0 if denom == 0 else cov / denom
    adjusted = apply_cuped(post, pre, theta)
    var_post = np.var(post, ddof=1)
    var_adj = np.var(adjusted, ddof=1)
    reduction = 0.0 if var_post == 0 else (1 - var_adj / var_post) * 100.0
    return {"theta": float(theta), "variance_reduction_pct": float(reduction)}
