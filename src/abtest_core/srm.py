"""SRM (sample ratio mismatch) check using chi-square test."""
from __future__ import annotations

from typing import Dict

from .utils import lazy_import


class SrmCheckFailed(Exception):
    """Exception raised when SRM check fails."""

    def __init__(self, result: dict):
        super().__init__("SRM: traffic imbalance")
        self.result = result

    def to_dict(self) -> dict:
        return {
            "code": "srm_failed",
            "title": "SRM: дисбаланс трафика",
            "details": {
                "expected": self.result["expected"],
                "observed": self.result["observed"],
                "p_value": self.result["p_value"],
            },
            "fix_hint": "Проверьте распределение трафика или запустите с force_run_when_srm_failed",
        }


def srm_check(counts: Dict[str, int], alpha: float = 0.001) -> dict:
    """Perform chi-square SRM check for arbitrary groups.

    Args:
        counts: Mapping of group name to observed user count.
        alpha: Significance level for the chi-square test.

    Returns:
        Dictionary with p-value, pass flag, expected and observed counts.
    """
    if not counts:
        raise ValueError("counts must not be empty")
    total = sum(counts.values())
    k = len(counts)
    if k <= 1:
        raise ValueError("at least two groups required")

    expected_count = total / k
    expected = {g: expected_count for g in counts}
    observed = {g: int(v) for g, v in counts.items()}
    chi_sq = sum((observed[g] - expected[g]) ** 2 / expected[g] for g in counts)
    try:
        chi2 = lazy_import("scipy.stats").chi2
    except Exception:  # pragma: no cover - scipy missing
        import math as _math

        class _Chi2:
            @staticmethod
            def cdf(x: float, df: int) -> float:
                return 1 - _math.exp(-x / 2)

        chi2 = _Chi2()
    p_value = 1 - chi2.cdf(chi_sq, df=k - 1)
    passed = p_value >= alpha
    return {
        "p_value": float(p_value),
        "passed": bool(passed),
        "expected": expected,
        "observed": observed,
    }
