from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from .types import AnalysisConfig
from .stats_binomial import prop_diff_test
from .stats_continuous import welch_ttest, yuen_trimmed_mean_test, bootstrap_bca_ci
from .stats_ratio import ratio_test


@dataclass
class AnalysisResult:
    p_value: float
    effect: float
    ci: Tuple[float, float]
    method_notes: str = ""


def analyze_groups(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    groups = df["group"].unique()
    if len(groups) != 2:
        raise ValueError("exactly two groups required")
    g1 = df[df["group"] == groups[0]]["metric"]
    g2 = df[df["group"] == groups[1]]["metric"]
    notes = []
    if config.metric_type == "binomial":
        x1, n1 = g1.sum(), g1.count()
        x2, n2 = g2.sum(), g2.count()
        res = prop_diff_test(int(x1), int(n1), int(x2), int(n2), alpha=config.alpha, sided=config.sided)
        p_value, effect, ci = res["p_value"], res["effect"], res["ci"]
        notes.append(res["notes"])
    elif config.metric_type == "continuous":
        if config.robust:
            res = yuen_trimmed_mean_test(g1.to_numpy(), g2.to_numpy(), alpha=config.alpha, sided=config.sided)
        else:
            mean1, var1, n1 = g1.mean(), g1.var(ddof=1), g1.count()
            mean2, var2, n2 = g2.mean(), g2.var(ddof=1), g2.count()
            res = welch_ttest(mean1, var1, n1, mean2, var2, n2, sided=config.sided, alpha=config.alpha)
        p_value, effect, ci = res["p_value"], res["effect"], res["ci"]
        notes.append(res["notes"])
        if config.bootstrap:
            ci = bootstrap_bca_ci(g1.to_numpy(), g2.to_numpy(), lambda a, b: np.mean(b) - np.mean(a), alpha=config.alpha)
            notes.append("bootstrap_bca")
    elif config.metric_type == "ratio":
        mean1, var1, n1 = g1.mean(), g1.var(ddof=1), g1.count()
        mean2, var2, n2 = g2.mean(), g2.var(ddof=1), g2.count()
        res = ratio_test(mean1, var1, n1, mean2, var2, n2, alpha=config.alpha, sided=config.sided, fieller=config.use_fieller)
        p_value, effect, ci = res["p_value"], res["effect"], res["ci"]
        notes.append(res["notes"])
    else:
        raise ValueError("unknown metric type")
    return AnalysisResult(p_value=p_value, effect=effect, ci=ci, method_notes=", ".join(notes))
