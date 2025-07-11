import math
import types
from typing import List, Optional

from metrics import track_time
import plugin_loader

try:
    import numpy as np
except Exception:
    np = types.SimpleNamespace(
        linspace=lambda a,b,n:[a+(b-a)*i/(n-1) for i in range(n)],
        random=types.SimpleNamespace(binomial=lambda *a,**k:[0], randint=lambda a,b=None:0, random=lambda:0.0),
        argmax=lambda arr:max(range(len(arr)), key=lambda i: arr[i]),
        trapz=lambda y,x: sum((y[i]+y[i+1])*(x[i+1]-x[i])/2 for i in range(len(y)-1))
    )
try:
    from scipy.stats import norm, beta, chi2
except Exception:
    import statistics, math as _math
    class _Norm:
        ppf=staticmethod(lambda p: statistics.NormalDist().inv_cdf(p))
        cdf=staticmethod(lambda x: statistics.NormalDist().cdf(x))
    class _Beta:
        pdf=staticmethod(lambda *a,**k: None)
        cdf=staticmethod(lambda *a,**k: None)
    class _Chi2:
        cdf=staticmethod(lambda x, df: 1 - _math.exp(-x/2))
    norm=_Norm(); beta=_Beta(); chi2=_Chi2()

from webhooks import send_webhook


@track_time
def required_sample_size(p1: float, p2: float, alpha: float, power: float) -> int:
    """Размер выборки на группу (двусторонний тест разности пропорций)."""
    if p1 == p2 or p1 <= 0 or p2 <= 0:
        return float('inf')
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    p_avg = (p1 + p2) / 2
    se_pooled = math.sqrt(2 * p_avg * (1 - p_avg))
    se_effect = math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    n = ((z_alpha * se_pooled + z_beta * se_effect) ** 2) / ((p1 - p2) ** 2)
    return max(1, math.ceil(n))


@track_time
def calculate_mde(sample_size: int, alpha: float, power: float, p1: float) -> float:
    """Минимальная обнаруживаемая разница при данных sample_size."""
    if sample_size <= 0 or p1 <= 0:
        return float('inf')
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    se = math.sqrt(2 * p1 * (1 - p1) / sample_size)
    return (z_alpha + z_beta) * se


# ----- A/B/N test helpers -----

def _evaluate_abn_test(
    users_a: int,
    conv_a: int,
    users_b: int,
    conv_b: int,
    users_c: Optional[int] = None,
    conv_c: Optional[int] = None,
    alpha: float = 0.05,
):
    """Внутренний A/B/n z-тест (Bonferroni)."""

    if users_a <= 0 or users_b <= 0:
        raise ValueError("Кол-во пользователей должно быть >0")

    if users_c is not None and users_c <= 0:
        raise ValueError("Кол-во пользователей должно быть >0")

    if not (0 <= conv_a <= users_a):
        raise ValueError("Количество конверсий A должно быть от 0 до users_a")

    if not (0 <= conv_b <= users_b):
        raise ValueError("Количество конверсий B должно быть от 0 до users_b")

    if users_c is not None and conv_c is not None and not (0 <= conv_c <= users_c):
        raise ValueError("Количество конверсий C должно быть от 0 до users_c")

    cr_a = conv_a / users_a
    cr_b = conv_b / users_b
    cr_c = conv_c / users_c if users_c is not None and conv_c is not None else None

    if users_c is not None and conv_c is not None:
        pooled = (conv_a + conv_b + conv_c) / (users_a + users_b + users_c)
    else:
        pooled = (conv_a + conv_b) / (users_a + users_b)

    se_ab = math.sqrt(pooled * (1 - pooled) * (1 / users_a + 1 / users_b))
    z_ab = (cr_b - cr_a) / se_ab if se_ab > 0 else 0
    p_ab = 2 * (1 - norm.cdf(abs(z_ab)))

    if users_c is not None and conv_c is not None:
        se_ac = math.sqrt(pooled * (1 - pooled) * (1 / users_a + 1 / users_c))
        z_ac = (cr_c - cr_a) / se_ac if se_ac > 0 else 0
        p_ac = 2 * (1 - norm.cdf(abs(z_ac)))
        alpha_adj = alpha / 2
        sig_ac = p_ac < alpha_adj
        h_ac = 2 * (math.asin(math.sqrt(cr_c)) - math.asin(math.sqrt(cr_a)))
        uplift_ac = (cr_c - cr_a) / cr_a * 100 if cr_a > 0 else 0
    else:
        p_ac = None
        sig_ac = None
        h_ac = None
        uplift_ac = None
        alpha_adj = alpha

    sig_ab = p_ab < alpha_adj
    h_ab = 2 * (math.asin(math.sqrt(cr_b)) - math.asin(math.sqrt(cr_a)))
    uplift_ab = (cr_b - cr_a) / cr_a * 100 if cr_a > 0 else 0

    if users_c is not None and conv_c is not None:
        winner = (
            "B"
            if sig_ab and cr_b > cr_a
            else "C" if sig_ac and cr_c > cr_a else "A" if not sig_ab and not sig_ac else "None"
        )
    else:
        winner = "B" if sig_ab and cr_b > cr_a else "A" if not sig_ab else "None"

    return {
        "cr_a": cr_a,
        "cr_b": cr_b,
        "cr_c": cr_c,
        "uplift_ab": uplift_ab,
        "uplift_ac": uplift_ac,
        "p_value_ab": p_ab,
        "p_value_ac": p_ac,
        "significant_ab": sig_ab,
        "significant_ac": sig_ac,
        "winner": winner,
        "cohens_h_ab": h_ab,
        "cohens_h_ac": h_ac,
    }


_bayes_plug = plugin_loader.get_plugin("bayesian")


@track_time
def bayesian_analysis(alpha_prior: float, beta_prior: float, users_a: int, conv_a: int, users_b: int, conv_b: int):
    """Bayesian A/B analysis delegated to plugin if available."""
    if _bayes_plug and hasattr(_bayes_plug, "bayesian_analysis"):
        return _bayes_plug.bayesian_analysis(alpha_prior, beta_prior, users_a, conv_a, users_b, conv_b)
    raise ImportError("Bayesian analysis plugin not available")


@track_time
def run_aa_simulation(baseline: float, total_users: int, alpha: float, num_sim: int = 1000) -> float:
    """A/A симуляция, возвращает фактический FPR."""
    ua = total_users // 2
    ub = total_users - ua

    ca = np.random.binomial(ua, baseline, size=num_sim)
    cb = np.random.binomial(ub, baseline, size=num_sim)

    cr_a = ca / ua
    cr_b = cb / ub
    pooled = (ca + cb) / (ua + ub)
    se = np.sqrt(pooled * (1 - pooled) * (1 / ua + 1 / ub))
    z = np.divide(cr_b - cr_a, se, out=np.zeros_like(cr_a, dtype=float), where=se > 0)
    p_vals = 2 * (1 - norm.cdf(np.abs(z)))
    return float(np.mean(p_vals < alpha))


@track_time
def evaluate_abn_test(
    users_a: int,
    conv_a: int,
    users_b: int,
    conv_b: int,
    users_c: Optional[int] = None,
    conv_c: Optional[int] = None,
    metrics: int = 1,
    alpha: float = 0.05,
):
    """A/B/n тест с поправкой FDR (Benjamini–Hochberg)."""
    res = _evaluate_abn_test(users_a, conv_a, users_b, conv_b, users_c, conv_c, alpha=alpha)
    p = res["p_value_ab"]
    m = max(1, int(metrics))
    p_adj = min(p * m, 1.0)
    res["p_value_fdr"] = p_adj
    res["significant_fdr"] = p_adj < alpha
    return res


@track_time
def run_sequential_analysis(ua: int, ca: int, ub: int, cb: int, alpha: float, looks: int = 5, webhook_url: Optional[str] = None):
    """Sequential Pocock method."""
    if looks <= 0:
        raise ValueError("looks must be positive")
    pocock_alpha = alpha / looks
    steps = []
    for i in range(1, looks + 1):
        na = int(ua * i / looks)
        nb = int(ub * i / looks)
        ca_i = int(ca * i / looks + 0.5)
        cb_i = int(cb * i / looks + 0.5)
        if na == 0 or nb == 0:
            continue
        res = _evaluate_abn_test(na, ca_i, nb, cb_i, alpha=pocock_alpha)
        steps.append(res)
        if res["p_value_ab"] < pocock_alpha:
            if webhook_url:
                send_webhook(
                    webhook_url,
                    f"Sequential test stopped at look {i} p={res['p_value_ab']:.4f}",
                )
            break
    return steps, pocock_alpha


@track_time
def run_obrien_fleming(ua: int, ca: int, ub: int, cb: int, alpha: float, looks: int = 5, webhook_url: Optional[str] = None):
    """Sequential O'Brien-Fleming method."""
    if looks <= 0:
        raise ValueError("looks must be positive")

    base_z = norm.ppf(1 - alpha / 2)
    steps = []
    for i in range(1, looks + 1):
        na = int(ua * i / looks)
        nb = int(ub * i / looks)
        ca_i = int(ca * i / looks + 0.5)
        cb_i = int(cb * i / looks + 0.5)
        if na == 0 or nb == 0:
            continue
        thr = 2 * (1 - norm.cdf(base_z / math.sqrt(i / looks)))
        res = _evaluate_abn_test(na, ca_i, nb, cb_i, alpha=thr)
        res["threshold"] = thr
        steps.append(res)
        if res["p_value_ab"] < thr:
            if webhook_url:
                send_webhook(
                    webhook_url,
                    f"OBF test stopped at look {i} p={res['p_value_ab']:.4f}",
                )
            break
    return steps


def calculate_roi(rpu: float, cost: float, budget: float, baseline_cr: float, uplift: float):
    """Return ROI metrics."""
    users = budget / cost
    base_rev = users * baseline_cr * rpu
    new_rev = users * (baseline_cr * (1 + uplift)) * rpu
    profit = new_rev - base_rev
    roi = profit / budget * 100
    return users, base_rev, new_rev, profit, roi


# ----- Additional helpers -----

def cuped_adjustment(x: List[float], covariate: List[float]):
    """Return CUPED-adjusted metric array."""
    x = [float(v) for v in x]
    c = [float(v) for v in covariate]
    mean_x = sum(x) / len(x)
    mean_c = sum(c) / len(c)
    cov = sum((xi - mean_x) * (ci - mean_c) for xi, ci in zip(x, c)) / (len(x) - 1)
    var_c = sum((ci - mean_c) ** 2 for ci in c) / (len(c) - 1)
    if var_c == 0:
        return x
    theta = cov / var_c
    return [xi - theta * ci for xi, ci in zip(x, c)]


def srm_check(users_a: int, users_b: int, alpha: float = 0.05):
    """Simple SRM check using chi-square test."""
    total = users_a + users_b
    expected = total / 2
    chi_sq = ((users_a - expected) ** 2) / expected + ((users_b - expected) ** 2) / expected
    p = 1 - chi2.cdf(chi_sq, df=1)
    return p < alpha, p


def pocock_alpha_curve(alpha: float, looks: int):
    """Return Pocock alpha spending thresholds per look."""
    if looks <= 0:
        raise ValueError("looks must be positive")
    return [alpha / looks for _ in range(looks)]
