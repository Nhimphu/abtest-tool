import math
from typing import Tuple, Dict

from scipy.stats import norm


def delta_mean_diff_ci(mean1: float, var1: float, n1: int, mean2: float, var2: float, n2: int, alpha: float = 0.05) -> Tuple[float, float]:
    effect = mean2 - mean1
    se = math.sqrt(var1 / n1 + var2 / n2)
    z = norm.ppf(1 - alpha / 2)
    return effect - z * se, effect + z * se


def delta_ratio_ci(mean1: float, var1: float, n1: int, mean2: float, var2: float, n2: int, alpha: float = 0.05) -> Tuple[float, float]:
    ratio = mean2 / mean1
    se = ratio * math.sqrt(var1 / (n1 * mean1 ** 2) + var2 / (n2 * mean2 ** 2))
    z = norm.ppf(1 - alpha / 2)
    return ratio - z * se, ratio + z * se


def fieller_ratio_ci(mean1: float, var1: float, n1: int, mean2: float, var2: float, n2: int, alpha: float = 0.05) -> Tuple[Tuple[float, float], str]:
    a = mean1
    b = mean2
    va = var1 / n1
    vb = var2 / n2
    z = norm.ppf(1 - alpha / 2)
    g = a * b
    h = a ** 2 - z ** 2 * va
    k = b ** 2 - z ** 2 * vb
    if h <= 0:
        return (-math.inf, math.inf), "fieller_unbounded"
    discr = g ** 2 - h * k
    if discr < 0:
        discr = 0
    root = math.sqrt(discr)
    lo = (g - root) / h
    hi = (g + root) / h
    return (lo, hi), "fieller"


def ratio_test(
    mean1: float,
    var1: float,
    n1: int,
    mean2: float,
    var2: float,
    n2: int,
    alpha: float = 0.05,
    sided: str = "two",
    fieller: bool = False,
) -> Dict[str, object]:
    ratio = mean2 / mean1
    log_ratio = math.log(ratio)
    se_log = math.sqrt(var1 / (n1 * mean1 ** 2) + var2 / (n2 * mean2 ** 2))
    z_stat = log_ratio / se_log if se_log > 0 else 0.0
    if sided == "two":
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    elif sided == "left":
        p_value = norm.cdf(z_stat)
    elif sided == "right":
        p_value = 1 - norm.cdf(z_stat)
    else:
        raise ValueError("sided must be 'two', 'left', or 'right'")
    if fieller:
        ci, note = fieller_ratio_ci(mean1, var1, n1, mean2, var2, n2, alpha)
    else:
        ci = delta_ratio_ci(mean1, var1, n1, mean2, var2, n2, alpha)
        note = "delta"
    return {"p_value": p_value, "effect": ratio, "ci": ci, "notes": note}
