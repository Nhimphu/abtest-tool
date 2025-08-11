from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, cast

import pandas as pd
import numpy as np

from .types import AnalysisConfig
from .multiple import holm, benjamini_yekutieli
from .stats_binomial import prop_diff_test
from .stats_continuous import welch_ttest, yuen_trimmed_mean_test, bootstrap_bca_ci
from .stats_ratio import ratio_test
from .cuped import estimate_theta, apply_cuped
from .sequential import make_plan, sequential_test
from .bayes import prob_win_binomial, prob_win_continuous


@dataclass
class AnalysisResult:
    p_value: float
    effect: float
    ci: Tuple[float, float]
    method_notes: str = ""
    meta: Optional[dict] = None
    segments: Optional[list[dict]] = None


def analyze_groups(df: "pd.DataFrame", config: AnalysisConfig) -> AnalysisResult:
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    groups = list(pd.unique(df["group"]))
    if len(groups) != 2:
        raise ValueError("exactly two groups required")
    mask1 = df["group"] == groups[0]
    mask2 = df["group"] == groups[1] if len(groups) > 1 else ~mask1
    method_notes: List[str] = []
    meta: dict[str, Any] = {}
    if config.use_cuped:
        pre_col = config.preperiod_metric_col
        if not pre_col or pre_col not in df.columns:
            method_notes.append(str("CUPED skipped: pre-period column missing"))
        else:
            mask_complete = df[pre_col].notna() & df["metric"].notna()
            if mask_complete.sum() < 10:
                method_notes.append(str("CUPED skipped: insufficient pre-period data"))
            else:
                pre = df.loc[mask_complete, pre_col]
                post = df.loc[mask_complete, "metric"]
                corr = np.corrcoef(pre, post)[0, 1]
                if np.isnan(corr) or abs(corr) < 0.1:
                    method_notes.append(str("CUPED skipped: low correlation"))
                else:
                    stats = estimate_theta(pre, post)
                    df.loc[mask_complete, "metric"] = apply_cuped(post, pre, stats["theta"])
                    method_notes.append(
                        str(
                            f"CUPED theta={stats['theta']:.4g}, variance reduction≈{stats['variance_reduction_pct']:.1f}%"
                        )
                    )
    g1 = df.loc[mask1, "metric"]
    g2 = df.loc[mask2, "metric"]
    bres = None
    if config.metric_type == "binomial":
        x1, n1 = g1.sum(), g1.count()
        x2, n2 = g2.sum(), g2.count()
        res_bin = cast(dict[str, Any], prop_diff_test(int(x1), int(n1), int(x2), int(n2), alpha=config.alpha, sided=config.sided))
        p_value = float(res_bin["p_value"])
        effect = float(res_bin["effect"])
        ci_lo, ci_hi = cast(Tuple[float, float], res_bin["ci"])
        ci = (float(ci_lo), float(ci_hi))
        method_notes.append(str(res_bin["method"]))
        if getattr(config, "use_bayes", False):
            bres = prob_win_binomial(int(x1), int(n1), int(x2), int(n2), a0=1, b0=1, rope=getattr(config, "bayes_rope", None))
    elif config.metric_type == "continuous":
        if config.robust:
            res_cont = cast(dict[str, Any], yuen_trimmed_mean_test(g1.to_numpy(), g2.to_numpy(), alpha=config.alpha, sided=config.sided))
        else:
            mean1, var1, n1 = g1.mean(), g1.var(ddof=1), g1.count()
            mean2, var2, n2 = g2.mean(), g2.var(ddof=1), g2.count()
            res_cont = cast(dict[str, Any], welch_ttest(mean1, var1, n1, mean2, var2, n2, sided=config.sided, alpha=config.alpha))
        p_value = float(res_cont["p_value"])
        effect = float(res_cont["effect"])
        ci_lo, ci_hi = cast(Tuple[float, float], res_cont["ci"])
        ci = (float(ci_lo), float(ci_hi))
        method_notes.append(str(res_cont["notes"]))
        if getattr(config, "use_bayes", False):
            bres = prob_win_continuous(
                g1.to_numpy(),
                g2.to_numpy(),
                rope=getattr(config, "bayes_rope", None),
                draws=getattr(config, "bayes_draws", 10000),
            )
        if config.bootstrap:
            ci = bootstrap_bca_ci(
                g1.to_numpy(),
                g2.to_numpy(),
                lambda a, b: float(np.mean(b) - np.mean(a)),
                alpha=config.alpha,
            )
            method_notes.append(str("bootstrap_bca"))
    elif config.metric_type == "ratio":
        mean1, var1, n1 = g1.mean(), g1.var(ddof=1), g1.count()
        mean2, var2, n2 = g2.mean(), g2.var(ddof=1), g2.count()
        res_ratio = cast(
            dict[str, Any],
            ratio_test(
                mean1,
                var1,
                n1,
                mean2,
                var2,
                n2,
                alpha=config.alpha,
                sided=config.sided,
                fieller=config.use_fieller,
            ),
        )
        p_value = float(res_ratio["p_value"])
        effect = float(res_ratio["effect"])
        ci_lo, ci_hi = cast(Tuple[float, float], res_ratio["ci"])
        ci = (float(ci_lo), float(ci_hi))
        method_notes.append(str(res_ratio["notes"]))
        if getattr(config, "use_bayes", False):
            bres = prob_win_continuous(
                g1.to_numpy(),
                g2.to_numpy(),
                rope=getattr(config, "bayes_rope", None),
                draws=getattr(config, "bayes_draws", 10000),
            )
    else:
        raise ValueError("unknown metric type")
    if bres is not None:
        meta["bayes"] = bres
        msg = f"Bayes: P(B>A)≈{bres['p_win']:.3f}"
        if bres.get("p_rope") is not None:
            msg += f", P(diff∈ROPE)≈{bres['p_rope']:.3f}"
        method_notes.append(str(msg))
    if getattr(config, "use_sequential", False):
        k = max(1, int(getattr(config, "sequential_looks", 5)))
        preset = (getattr(config, "sequential_preset", "pocock") or "pocock")
        plan = make_plan(k, float(config.alpha), preset)
        history = list(getattr(config, "sequential_history_p", []))
        if not history or history[-1] != p_value:
            history.append(float(p_value))
        decision = sequential_test(history, plan)
        meta["sequential"] = {
            "plan": plan,
            "history_len": len(history),
            "decision": decision,
        }
        method_notes.append(
            str(
                f"Sequential ({preset}, k={k}): look={decision['look']}, "
                f"{'STOP' if decision['stop'] else 'continue'}, "
                f"p≤{plan['thresholds'][decision['look']-1]:.4g} at this look; "
                f"spent≈{decision['spent_alpha_cum']:.4g}."
            )
        )
    segments_res: list[dict] | None = None
    if getattr(config, "segments", None):
        segments_res = []
        pvals: list[float] = []
        seg_cfg = AnalysisConfig(**config.__dict__)
        seg_cfg.segments = []
        seg_cfg.multiple_testing = "none"
        for col in config.segments:
            if col not in df.columns:
                continue
            for val, sdf in df.groupby(col):
                seg_res = analyze_groups(sdf, seg_cfg)
                segments_res.append(
                    {
                        "segment": {"col": col, "val": val},
                        "p_raw": float(seg_res.p_value),
                        "effect": float(seg_res.effect),
                        "n": int(len(sdf)),
                    }
                )
                pvals.append(float(seg_res.p_value))
        if segments_res:
            if config.multiple_testing == "holm":
                p_adj = holm(pvals)
            elif config.multiple_testing == "by":
                p_adj = benjamini_yekutieli(pvals)
            else:
                p_adj = pvals
            for seg, adj in zip(segments_res, p_adj):
                seg["p_adj"] = float(adj)
            method_notes.append(
                str(
                    f"Multiple testing: {config.multiple_testing.upper()} on {len(pvals)} comparisons"
                )
            )

    return AnalysisResult(
        p_value=float(p_value),
        effect=float(effect),
        ci=(float(ci[0]), float(ci[1])),
        method_notes=", ".join(method_notes),
        meta=meta or None,
        segments=segments_res,
    )
