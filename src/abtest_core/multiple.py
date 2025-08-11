"""Multiple testing correction methods."""
from __future__ import annotations

def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni step-down procedure.

    Returns a list of adjusted p-values aligned with the input order.
    """
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    sorted_p = [pvals[i] for i in order]
    adj = [0.0] * m
    prev = 0.0
    for i, p in enumerate(sorted_p):
        val = (m - i) * p
        if val > 1.0:
            val = 1.0
        if val < prev:
            val = prev
        prev = val
        adj[i] = val
    # reorder to original positions
    out = [0.0] * m
    for idx, orig in enumerate(order):
        out[orig] = adj[idx]
    return out


def benjamini_yekutieli(pvals: list[float]) -> list[float]:
    """Benjamini-Yekutieli FDR control under dependence."""
    m = len(pvals)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvals[i])
    sorted_p = [pvals[i] for i in order]
    c_m = sum(1.0 / (i + 1) for i in range(m))
    adj = [0.0] * m
    prev = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        val = sorted_p[i] * m * c_m / rank
        if val > prev:
            val = prev
        if val > 1.0:
            val = 1.0
        prev = val
        adj[i] = val
    out = [0.0] * m
    for idx, orig in enumerate(order):
        out[orig] = adj[idx]
    return out
