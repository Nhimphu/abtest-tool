import math
import numpy as np
import plotly.graph_objects as go
from typing import Any

# ``scipy`` is an optional dependency. ``stats.ab_test`` provides a
# compatible ``norm`` object with fallbacks when SciPy is unavailable.
from stats.ab_test import norm

from stats.ab_test import required_sample_size, bayesian_analysis, pocock_alpha_curve


def plot_bayesian_posterior(
    alpha_prior: float,
    beta_prior: float,
    users_a: int,
    conv_a: int,
    users_b: int,
    conv_b: int,
) -> Any:
    """Возвращает Plotly-фигуру постериорных Beta-распределений."""
    prob, x, pdf_a, pdf_b = bayesian_analysis(
        alpha_prior, beta_prior, users_a, conv_a, users_b, conv_b
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=pdf_a, mode="lines", name="Posterior A"))
    fig.add_trace(go.Scatter(x=x, y=pdf_b, mode="lines", name="Posterior B"))
    fig.update_layout(
        title=f"P(B > A) = {prob:.2%}",
        xaxis_title="Conversion rate",
        yaxis_title="Density",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def plot_confidence_intervals(
    users_a: int,
    conv_a: int,
    users_b: int,
    conv_b: int,
    alpha: float = 0.05,
) -> Any:
    """Возвращает Plotly-фигуру доверительных интервалов для A и B."""
    cr_a = conv_a / users_a
    cr_b = conv_b / users_b
    se_a = math.sqrt(cr_a * (1 - cr_a) / users_a)
    se_b = math.sqrt(cr_b * (1 - cr_b) / users_b)
    margin_a = norm.ppf(1 - alpha / 2) * se_a
    margin_b = norm.ppf(1 - alpha / 2) * se_b
    ci_a = (cr_a - margin_a, cr_a + margin_a)
    ci_b = (cr_b - margin_b, cr_b + margin_b)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[ci_a[0], ci_a[1]],
            y=[1, 1],
            mode="lines",
            line=dict(width=10),
            name=f"A CI {(1-alpha)*100:.0f}%",
            hovertemplate="A: %{x:.2%}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[ci_b[0], ci_b[1]],
            y=[0, 0],
            mode="lines",
            line=dict(width=10),
            name=f"B CI {(1-alpha)*100:.0f}%",
            hovertemplate="B: %{x:.2%}<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"{(1-alpha)*100:.0f}% Confidence Intervals",
        xaxis_title="Conversion Rate",
        yaxis=dict(tickmode="array", tickvals=[0, 1], ticktext=["B", "A"]),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def plot_power_curve(p1: float, alpha: float, power: float) -> Any:
    """Возвращает график требуемого размера выборки от конверсии B."""
    p2s = np.linspace(max(0.001, p1 * 1.01), min(0.999, p1 * 2), 100)
    ns = [required_sample_size(p1, p2, alpha, power) for p2 in p2s]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=p2s,
            y=ns,
            mode="lines",
            hovertemplate="CR B: %{x:.2%}<br>n: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Required Sample Size vs. CR B",
        xaxis_title="CR B",
        yaxis_title="Required Sample Size",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def plot_bootstrap_distribution(
    users_a: int,
    conv_a: int,
    users_b: int,
    conv_b: int,
    iterations: int = 5000,
) -> Any:
    """Возвращает Plotly-гистограмму бутстрап-разницы (B−A)."""
    cr_a = conv_a / users_a
    cr_b = conv_b / users_b
    samp_a = np.random.binomial(users_a, cr_a, size=iterations) / users_a
    samp_b = np.random.binomial(users_b, cr_b, size=iterations) / users_b
    diffs = samp_b - samp_a

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=diffs,
            nbinsx=50,
            histnorm="probability",
            hovertemplate="%{x:.2%}<br>%{y:.1%}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="black")
    fig.update_layout(
        title="Bootstrap Distribution of Δ (B−A)",
        xaxis_title="Difference in CR",
        yaxis_title="Probability",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def plot_alpha_spending(alpha: float, looks: int) -> Any:
    """Return Plotly figure of Pocock and O'Brien-Fleming alpha spending."""
    pocock = pocock_alpha_curve(alpha, looks)
    obf = [
        2 * (1 - norm.cdf(norm.ppf(1 - alpha / 2) / math.sqrt(i)))
        for i in range(1, looks + 1)
    ]
    fig = go.Figure()
    hover = "Look %{x}<br>α=%{y:.4f}<extra></extra>"
    fig.add_trace(
        go.Scatter(
            x=list(range(1, looks + 1)),
            y=pocock,
            mode="lines+markers",
            name="Pocock",
            hovertemplate=hover,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=list(range(1, looks + 1)),
            y=obf,
            mode="lines+markers",
            name="O'Brien-Fleming",
            hovertemplate=hover,
        )
    )
    fig.update_layout(
        title="Alpha Spending",
        xaxis_title="Look",
        yaxis_title="Alpha",
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True)),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def save_plot() -> None:
    """Сохраняет последнюю Matplotlib фигуру (если используется)."""
    import matplotlib.pyplot as plt
    from PyQt6.QtWidgets import QFileDialog

    path, _ = QFileDialog.getSaveFileName(
        None, "Save plot", "", "PNG Files (*.png);;PDF Files (*.pdf)"
    )
    if path:
        plt.savefig(path)
