import math
import numpy as np
from scipy.stats import norm, beta
import plotly.graph_objects as go
from PyQt6.QtWidgets import QFileDialog

def required_sample_size(p1, p2, alpha, power):
    """Размер выборки на группу (двусторонний тест разности пропорций)."""
    if p1 == p2 or p1 <= 0 or p2 <= 0:
        return float('inf')
    z_alpha = norm.ppf(1 - alpha/2)
    z_beta  = norm.ppf(power)
    p_avg   = (p1 + p2)/2
    se_pooled = math.sqrt(2 * p_avg * (1 - p_avg))
    se_effect = math.sqrt(p1*(1-p1) + p2*(1-p2))
    n = ((z_alpha*se_pooled + z_beta*se_effect)**2)/((p1 - p2)**2)
    # n already represents the sample size required per group.
    # Returning ``n/2`` underestimates the needed observations and
    # leads to underpowered experiments.
    return max(1, math.ceil(n))

def calculate_mde(sample_size, alpha, power, p1):
    """Минимальная обнаруживаемая разница при данных sample_size."""
    if sample_size <= 0 or p1 <= 0:
        return float('inf')
    z_alpha = norm.ppf(1 - alpha/2)
    z_beta  = norm.ppf(power)
    se = math.sqrt(2 * p1 * (1 - p1) / sample_size)
    return (z_alpha + z_beta) * se

def evaluate_abn_test(
    users_a,
    conv_a,
    users_b,
    conv_b,
    users_c=None,
    conv_c=None,
    alpha=0.05,
):
    """A/B/n z-тест (Bonferroni). Третий вариант необязателен."""

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
        h_ac = 2 * (
            math.asin(math.sqrt(cr_c)) - math.asin(math.sqrt(cr_a))
        )
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

def bayesian_analysis(alpha_prior, beta_prior, users_a, conv_a, users_b, conv_b):
    """
    Bayesian A/B: Beta(alpha_prior+conv, beta_prior+nonconv).
    Возвращает:
      prob: P(B > A)
      x: массив точек
      pdf_a, pdf_b: плотности A/B
    """
    a1 = alpha_prior + conv_a
    b1 = beta_prior  + (users_a - conv_a)
    a2 = alpha_prior + conv_b
    b2 = beta_prior  + (users_b - conv_b)
    x = np.linspace(0,1,500)
    pdf_a = beta.pdf(x, a1, b1)
    pdf_b = beta.pdf(x, a2, b2)
    cdf_a = beta.cdf(x, a1, b1)
    prob  = np.trapz(pdf_b * cdf_a, x)
    return prob, x, pdf_a, pdf_b

def plot_bayesian_posterior(alpha_prior, beta_prior, users_a, conv_a, users_b, conv_b):
    """
    Возвращает Plotly-фигуру постериорных Beta-распределений.
    """
    prob, x, pdf_a, pdf_b = bayesian_analysis(
        alpha_prior, beta_prior, users_a, conv_a, users_b, conv_b
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=pdf_a, mode='lines', name='Posterior A'))
    fig.add_trace(go.Scatter(x=x, y=pdf_b, mode='lines', name='Posterior B'))
    fig.update_layout(
        title=f"P(B > A) = {prob:.2%}",
        xaxis_title='Conversion rate',
        yaxis_title='Density',
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig

def run_aa_simulation(baseline, total_users, alpha, num_sim=1000):
    """A/A симуляция, возвращает фактический FPR."""
    false = 0
    for _ in range(num_sim):
        ua = total_users // 2
        ub = total_users - ua
        ca = np.random.binomial(ua, baseline)
        cb = np.random.binomial(ub, baseline)
        if evaluate_abn_test(ua, ca, ub, cb, alpha=alpha)['significant_ab']:
            false += 1
    return false / num_sim

def run_sequential_analysis(ua, ca, ub, cb, alpha, looks=5):
    """
    Последовательный Pocock: возвращает (steps, pocock_alpha).
    """
    pocock_alpha = alpha * (1 - (1 - 0.5**(1/looks)) / (1 - 0.5))
    steps = []
    for i in range(1, looks+1):
        na = int(ua * i/looks)
        nb = int(ub * i/looks)
        ca_i = int(ca * i/looks + 0.5)
        cb_i = int(cb * i/looks + 0.5)
        if na == 0 or nb == 0:
            continue
        res = evaluate_abn_test(na, ca_i, nb, cb_i, alpha=pocock_alpha)
        steps.append(res)
        if res['p_value_ab'] < pocock_alpha:
            break
    return steps, pocock_alpha

def calculate_roi(rpu, cost, budget, baseline_cr, uplift):
    """
    ROI = (new_rev - base_rev) / budget * 100.
    """
    users    = budget / cost
    base_rev = users * baseline_cr * rpu
    new_rev  = users * (baseline_cr*(1+uplift)) * rpu
    profit   = new_rev - base_rev
    roi      = profit / budget * 100
    return users, base_rev, new_rev, profit, roi

def plot_confidence_intervals(users_a, conv_a, users_b, conv_b, alpha=0.05):
    """
    Возвращает Plotly-фигуру доверительных интервалов для A и B.
    """
    cr_a = conv_a / users_a
    cr_b = conv_b / users_b
    se_a = math.sqrt(cr_a * (1 - cr_a) / users_a)
    se_b = math.sqrt(cr_b * (1 - cr_b) / users_b)
    margin_a = norm.ppf(1 - alpha/2) * se_a
    margin_b = norm.ppf(1 - alpha/2) * se_b
    ci_a = (cr_a - margin_a, cr_a + margin_a)
    ci_b = (cr_b - margin_b, cr_b + margin_b)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[ci_a[0], ci_a[1]], y=[1,1],
        mode='lines', line=dict(width=10),
        name=f'A CI {(1-alpha)*100:.0f}%',
        hovertemplate='A: %{x:.2%}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=[ci_b[0], ci_b[1]], y=[0,0],
        mode='lines', line=dict(width=10),
        name=f'B CI {(1-alpha)*100:.0f}%',
        hovertemplate='B: %{x:.2%}<extra></extra>'
    ))
    fig.update_layout(
        title=f'{(1-alpha)*100:.0f}% Confidence Intervals',
        xaxis_title='Conversion Rate',
        yaxis=dict(tickmode='array', tickvals=[0,1], ticktext=['B','A']),
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig

def plot_power_curve(p1, alpha, power):
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

def plot_bootstrap_distribution(users_a, conv_a, users_b, conv_b, iterations=5000):
    """
    Возвращает Plotly-гистограмму бутстрап-разницы (B−A).
    """
    data_a = np.array([1]*conv_a + [0]*(users_a-conv_a))
    data_b = np.array([1]*conv_b + [0]*(users_b-conv_b))
    diffs = [
        np.mean(np.random.choice(data_b, users_b, True))
        - np.mean(np.random.choice(data_a, users_a, True))
        for _ in range(iterations)
    ]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=diffs, nbinsx=50, histnorm='probability',
        hovertemplate='%{x:.2%}<br>%{y:.1%}<extra></extra>'
    ))
    fig.add_vline(x=0, line_dash='dash', line_color='black')
    fig.update_layout(
        title='Bootstrap Distribution of Δ (B−A)',
        xaxis_title='Difference in CR',
        yaxis_title='Probability',
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig

def save_plot():
    """Сохраняет последнюю Matplotlib фигуру (если используется)."""
    import matplotlib.pyplot as plt
    path, _ = QFileDialog.getSaveFileName(None, "Save plot", "", "PNG Files (*.png);;PDF Files (*.pdf)")
    if path:
        plt.savefig(path)
