from __future__ import annotations
import math
from statistics import NormalDist

nd = NormalDist()

def pocock_thresholds(k: int, alpha: float) -> list[float]:
    if k < 1:
        raise ValueError("k>=1")
    # Equal alpha spending per look (matches tests): sum == alpha
    per = float(alpha) / float(k)
    return [per] * k

def obf_thresholds(k: int, alpha: float) -> list[float]:
    """
    Lan–DeMets spending approx for two-sided OBF: cumulative alpha at info t is
    A(t)=2 - 2*Phi(z_{alpha/2}/sqrt(t)). Per-look increment = A(t_i)-A(t_{i-1}).
    """
    z = nd.inv_cdf(1.0 - alpha/2.0)
    thr = []
    prev = 0.0
    for i in range(1, k+1):
        t = i / k
        cum = 2.0 - 2.0 * nd.cdf(z / math.sqrt(t))
        inc = max(0.0, cum - prev)
        thr.append(inc)
        prev = cum
    # numeric guard: scale to sum exactly alpha
    s = sum(thr)
    if s > 0:
        thr = [alpha * x / s for x in thr]
    return thr

def make_plan(k: int, alpha: float, preset: str = "pocock") -> dict:
    if k < 1:
        raise ValueError("k>=1")
    preset = preset.lower()
    if preset == "pocock":
        th = pocock_thresholds(k, alpha)
    elif preset in ("obf", "o'brien-fleming", "obrien-fleming"):
        th = obf_thresholds(k, alpha)
    else:
        raise ValueError("unknown preset")
    return {"k": k, "alpha": alpha, "preset": preset, "thresholds": th, "cum": _cum(th, alpha)}

def _cum(th, alpha):
    out = []
    acc = 0.0
    for v in th[:-1]:
        acc = math.fsum((acc, v))
        out.append(acc)
    if th:
        out.append(float(alpha))
    return out

def sequential_test(p_values: list[float], plan: dict) -> dict:
    """Stop on the first look i with p_i <= thresholds[i-1]."""
    th = plan["thresholds"]
    k = plan["k"]
    looks = min(len(p_values), k)
    spent = 0.0
    for i in range(looks):
        spent += th[i]
        if p_values[i] <= th[i]:
            return {
                "stop": True,
                "look": i + 1,
                "threshold": th[i],
                "spent_alpha_cum": spent,
                "preset": plan["preset"],
            }
    return {
        "stop": False,
        "look": looks,
        "threshold": th[looks - 1] if looks else None,
        "spent_alpha_cum": sum(th[:looks]),
        "preset": plan["preset"],
    }
