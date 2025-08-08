import math
from typing import Tuple, Dict

from scipy.stats import norm


def wilson_ci(x: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    p = x / n
    z = norm.ppf(1 - alpha / 2)
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def newcombe_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> Tuple[float, float]:
    p1_lo, p1_hi = wilson_ci(x1, n1, alpha)
    p2_lo, p2_hi = wilson_ci(x2, n2, alpha)
    lo = p2_lo - p1_hi
    hi = p2_hi - p1_lo
    return min(lo, hi), max(lo, hi)


def _p_value_from_z(z: float, sided: str = "two") -> float:
    if sided == "two":
        return 2 * (1 - norm.cdf(abs(z)))
    if sided == "left":
        return norm.cdf(z)
    if sided == "right":
        return 1 - norm.cdf(z)
    raise ValueError("sided must be 'two', 'left', or 'right'")


def prop_diff_test(
    x1: int,
    n1: int,
    x2: int,
    n2: int,
    alpha: float = 0.05,
    sided: str = "two",
) -> Dict[str, object]:
    if n1 <= 0 or n2 <= 0:
        raise ValueError("sample sizes must be >0")
    p1 = x1 / n1
    p2 = x2 / n2
    effect = p2 - p1
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = effect / se if se > 0 else 0.0
    p_value = _p_value_from_z(z, sided)
    ci = newcombe_ci(x1, n1, x2, n2, alpha)
    return {
        "p_value": p_value,
        "effect": effect,
        "ci": ci,
        "method": "newcombe_wilson_diff",
    }
