from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable, Dict, Tuple

from statistics import NormalDist
from .utils import lazy_import

if TYPE_CHECKING:
    from numpy.typing import NDArray

norm = NormalDist()


def welch_ttest(
    mean1: float,
    var1: float,
    n1: int,
    mean2: float,
    var2: float,
    n2: int,
    sided: str = "two",
    alpha: float = 0.05,
) -> Dict[str, object]:
    effect = mean2 - mean1
    se = math.sqrt(var1 / n1 + var2 / n2)
    t_stat = effect / se if se > 0 else 0.0
    if sided == "two":
        p_value = 2 * (1 - norm.cdf(abs(t_stat)))
        t_crit = norm.inv_cdf(1 - alpha / 2)
    elif sided == "left":
        p_value = norm.cdf(t_stat)
        t_crit = norm.inv_cdf(1 - alpha)
    elif sided == "right":
        p_value = 1 - norm.cdf(t_stat)
        t_crit = norm.inv_cdf(1 - alpha)
    else:
        raise ValueError("sided must be 'two', 'left', or 'right'")
    ci = (effect - t_crit * se, effect + t_crit * se)
    return {
        "p_value": float(p_value),
        "effect": float(effect),
        "ci": (float(ci[0]), float(ci[1])),
        "notes": "welch",
    }


def yuen_trimmed_mean_test(
    a: "NDArray[Any]",
    b: "NDArray[Any]",
    trim: float = 0.2,
    alpha: float = 0.05,
    sided: str = "two",
) -> Dict[str, object]:
    np = lazy_import("numpy")
    a = np.asarray(a)
    b = np.asarray(b)
    g1 = int(trim * len(a))
    g2 = int(trim * len(b))
    a_sorted = np.sort(a)
    b_sorted = np.sort(b)
    a_trim = a_sorted[g1: len(a) - g1] if g1 > 0 else a_sorted
    b_trim = b_sorted[g2: len(b) - g2] if g2 > 0 else b_sorted
    m1 = a_trim.mean()
    m2 = b_trim.mean()
    effect = m2 - m1
    a_win = a_sorted.copy()
    b_win = b_sorted.copy()
    if g1 > 0:
        a_win[:g1] = a_win[g1]
        a_win[-g1:] = a_win[-g1 - 1]
    if g2 > 0:
        b_win[:g2] = b_win[g2]
        b_win[-g2:] = b_win[-g2 - 1]
    wv1 = np.var(a_win, ddof=1)
    wv2 = np.var(b_win, ddof=1)
    n1 = len(a_trim)
    n2 = len(b_trim)
    se = math.sqrt(wv1 / (n1 * (n1 - 1)) + wv2 / (n2 * (n2 - 1)))
    t_stat = effect / se if se > 0 else 0.0
    if sided == "two":
        p_value = 2 * (1 - norm.cdf(abs(t_stat)))
        t_crit = norm.inv_cdf(1 - alpha / 2)
    elif sided == "left":
        p_value = norm.cdf(t_stat)
        t_crit = norm.inv_cdf(1 - alpha)
    elif sided == "right":
        p_value = 1 - norm.cdf(t_stat)
        t_crit = norm.inv_cdf(1 - alpha)
    else:
        raise ValueError("sided must be 'two', 'left', or 'right'")
    ci = (effect - t_crit * se, effect + t_crit * se)
    return {
        "p_value": float(p_value),
        "effect": float(effect),
        "ci": (float(ci[0]), float(ci[1])),
        "notes": "yuen",
    }


def bootstrap_bca_ci(
    a: "NDArray[Any]",
    b: "NDArray[Any]",
    fn_effect: Callable[["NDArray[Any]", "NDArray[Any]"], float],
    alpha: float = 0.05,
    iters: int = 5000,
) -> Tuple[float, float]:
    np = lazy_import("numpy")
    a = np.asarray(a)
    b = np.asarray(b)
    obs = fn_effect(a, b)
    boot = []
    n1, n2 = len(a), len(b)
    for _ in range(iters):
        sa = np.random.choice(a, n1, replace=True)
        sb = np.random.choice(b, n2, replace=True)
        boot.append(fn_effect(sa, sb))
    boot = np.sort(boot)
    z0 = norm.inv_cdf((boot < obs).mean())
    jacks = []
    for i in range(n1):
        jacks.append(fn_effect(np.delete(a, i), b))
    for i in range(n2):
        jacks.append(fn_effect(a, np.delete(b, i)))
    jacks = np.array(jacks)
    jack_mean = jacks.mean()
    num = np.sum((jack_mean - jacks) ** 3)
    den = 6 * (np.sum((jack_mean - jacks) ** 2) ** 1.5)
    a_hat = num / den if den != 0 else 0.0
    al = norm.cdf(z0 + (z0 + norm.inv_cdf(alpha / 2)) / (1 - a_hat * (z0 + norm.inv_cdf(alpha / 2))))
    au = norm.cdf(z0 + (z0 + norm.inv_cdf(1 - alpha / 2)) / (1 - a_hat * (z0 + norm.inv_cdf(1 - alpha / 2))))
    lo = float(np.percentile(boot, al * 100))
    hi = float(np.percentile(boot, au * 100))
    return lo, hi
