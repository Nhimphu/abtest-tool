import math
from typing import Tuple, Callable, Dict

import numpy as np
from scipy.stats import t, trim_mean, ttest_ind, norm


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
    df_num = (var1 / n1 + var2 / n2) ** 2
    df_den = (var1 ** 2) / (n1 ** 2 * (n1 - 1)) + (var2 ** 2) / (n2 ** 2 * (n2 - 1))
    df = df_num / df_den if df_den > 0 else 1
    t_stat = effect / se if se > 0 else 0.0
    if sided == "two":
        p_value = 2 * (1 - t.cdf(abs(t_stat), df))
        t_crit = t.ppf(1 - alpha / 2, df)
    elif sided == "left":
        p_value = t.cdf(t_stat, df)
        t_crit = t.ppf(1 - alpha, df)
    elif sided == "right":
        p_value = 1 - t.cdf(t_stat, df)
        t_crit = t.ppf(1 - alpha, df)
    else:
        raise ValueError("sided must be 'two', 'left', or 'right'")
    ci = (effect - t_crit * se, effect + t_crit * se)
    return {"p_value": p_value, "effect": effect, "ci": ci, "notes": "welch"}


def yuen_trimmed_mean_test(
    a: np.ndarray,
    b: np.ndarray,
    trim: float = 0.2,
    alpha: float = 0.05,
    sided: str = "two",
) -> Dict[str, object]:
    a = np.asarray(a)
    b = np.asarray(b)
    stat, p_value = ttest_ind(a, b, equal_var=False, trim=trim)
    m1 = trim_mean(a, proportiontocut=trim)
    m2 = trim_mean(b, proportiontocut=trim)
    effect = m2 - m1
    g1 = int(trim * len(a))
    g2 = int(trim * len(b))
    a_win = np.sort(a)
    b_win = np.sort(b)
    if g1 > 0:
        a_win[:g1] = a_win[g1]
        a_win[-g1:] = a_win[-g1 - 1]
    if g2 > 0:
        b_win[:g2] = b_win[g2]
        b_win[-g2:] = b_win[-g2 - 1]
    wv1 = np.var(a_win, ddof=1)
    wv2 = np.var(b_win, ddof=1)
    n1 = len(a) - 2 * g1
    n2 = len(b) - 2 * g2
    se = math.sqrt(wv1 / (n1 * (n1 - 1)) + wv2 / (n2 * (n2 - 1)))
    df_num = (wv1 / (n1 * (n1 - 1)) + wv2 / (n2 * (n2 - 1))) ** 2
    df_den = (wv1 ** 2) / ((n1 ** 2) * (n1 - 1) ** 2 * (n1 - 1)) + (wv2 ** 2) / ((n2 ** 2) * (n2 - 1) ** 2 * (n2 - 1))
    df = df_num / df_den if df_den > 0 else n1 + n2 - 2
    if sided == "two":
        t_crit = t.ppf(1 - alpha / 2, df)
    else:
        t_crit = t.ppf(1 - alpha, df)
    ci = (effect - t_crit * se, effect + t_crit * se)
    return {"p_value": p_value, "effect": effect, "ci": ci, "notes": "yuen"}


def bootstrap_bca_ci(
    a: np.ndarray,
    b: np.ndarray,
    fn_effect: Callable[[np.ndarray, np.ndarray], float],
    alpha: float = 0.05,
    iters: int = 5000,
) -> Tuple[float, float]:
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
    z0 = norm.ppf((boot < obs).mean())
    # jackknife
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
    al = norm.cdf(z0 + (z0 + norm.ppf(alpha / 2)) / (1 - a_hat * (z0 + norm.ppf(alpha / 2))))
    au = norm.cdf(z0 + (z0 + norm.ppf(1 - alpha / 2)) / (1 - a_hat * (z0 + norm.ppf(1 - alpha / 2))))
    lo = np.percentile(boot, al * 100)
    hi = np.percentile(boot, au * 100)
    return lo, hi
