import math
import numpy as np
from scipy.stats import norm, beta, chi2
import plotly.graph_objects as go
from PyQt6.QtWidgets import QFileDialog
from webhooks import send_webhook

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

def _evaluate_abn_test(
    users_a,
    conv_a,
    users_b,
    conv_b,
    users_c=None,
    conv_c=None,
    alpha=0.05,
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

def evaluate_abn_test(
    users_a,
    conv_a,
    users_b,
    conv_b,
    users_c=None,
    conv_c=None,
    metrics=1,
    alpha=0.05,
):
    """A/B/n тест с поправкой FDR (Benjamini–Hochberg)."""
    res = _evaluate_abn_test(users_a, conv_a, users_b, conv_b, users_c, conv_c, alpha=alpha)
    p = res["p_value_ab"]
    m = max(1, int(metrics))
    p_adj = min(p * m, 1.0)
    res["p_value_fdr"] = p_adj
    res["significant_fdr"] = p_adj < alpha
    return res

def run_sequential_analysis(ua, ca, ub, cb, alpha, looks=5, webhook_url=None):
    """Sequential Pocock method.

    When ``webhook_url`` is provided, a POST notification is sent if the
    test stops early.
    """
    if looks <= 0:
        raise ValueError("looks must be positive")
    pocock_alpha = alpha / looks
    steps = []
    for i in range(1, looks+1):
        na = int(ua * i/looks)
        nb = int(ub * i/looks)
        ca_i = int(ca * i/looks + 0.5)
        cb_i = int(cb * i/looks + 0.5)
        if na == 0 or nb == 0:
            continue
        res = _evaluate_abn_test(na, ca_i, nb, cb_i, alpha=pocock_alpha)
        steps.append(res)
        if res['p_value_ab'] < pocock_alpha:
            if webhook_url:
                send_webhook(
                    webhook_url,
                    f"Sequential test stopped at look {i} p={res['p_value_ab']:.4f}",
                )
            break
    return steps, pocock_alpha

def run_obrien_fleming(ua, ca, ub, cb, alpha, looks=5, webhook_url=None):
    """Sequential O'Brien-Fleming method.

    Returns list of step results with per-look threshold.
    """
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
        res = _evaluate_abn_test(na, ca_i, nb, cb_i, alpha=alpha)
        # threshold p-value for look i
        thr = 2 * (1 - norm.cdf(base_z / math.sqrt(i)))
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
    cr_a = conv_a / users_a
    cr_b = conv_b / users_b
    samp_a = np.random.binomial(users_a, cr_a, size=iterations) / users_a
    samp_b = np.random.binomial(users_b, cr_b, size=iterations) / users_b
    diffs = samp_b - samp_a

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


# --------- Additional Methods ---------

def cuped_adjustment(x, covariate):
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


def srm_check(users_a, users_b, alpha=0.05):
    """Simple SRM check using chi-square test."""
    total = users_a + users_b
    expected = total / 2
    chi_sq = ((users_a - expected) ** 2) / expected + ((users_b - expected) ** 2) / expected
    p = 1 - chi2.cdf(chi_sq, df=1)
    return p < alpha, p


def pocock_alpha_curve(alpha, looks):
    """Return Pocock alpha spending thresholds per look."""
    if looks <= 0:
        raise ValueError("looks must be positive")
    return [alpha / looks for _ in range(looks)]


def ucb1(values, counts):
    """Return index of arm to select using UCB1."""
    t = sum(counts) + 1
    ucb_values = [v / c + math.sqrt(2 * math.log(t) / c) if c > 0 else float('inf')
                  for v, c in zip(values, counts)]
    return int(np.argmax(ucb_values))


def epsilon_greedy(values, counts, epsilon=0.1):
    """Return index of arm using epsilon-greedy selection."""
    if np.random.random() < epsilon or not any(counts):
        return int(np.random.randint(0, len(values)))
    avgs = [v / c if c > 0 else 0.0 for v, c in zip(values, counts)]
    return int(np.argmax(avgs))


def plot_alpha_spending(alpha, looks):
    """Return Plotly figure of Pocock and O'Brien-Fleming alpha spending."""
    pocock = pocock_alpha_curve(alpha, looks)
    obf = [
        2 * (1 - norm.cdf(norm.ppf(1 - alpha / 2) / math.sqrt(i)))
        for i in range(1, looks + 1)
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=list(range(1, looks + 1)), y=pocock, mode="lines+markers", name="Pocock")
    )
    fig.add_trace(
        go.Scatter(x=list(range(1, looks + 1)), y=obf, mode="lines+markers", name="O'Brien-Fleming")
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


def segment_data(records, **filters):
    """Return subset of records matching simple equality filters."""
    return [r for r in records if all(r.get(k) == v for k, v in filters.items())]


def compute_custom_metric(records, expression):
    """Evaluate expression like 'sum(conv)/sum(users)' on record list."""
    env = {
        'sum': lambda field: sum(float(r.get(field, 0)) for r in records),
        'len': lambda _: len(records)
    }
    return eval(expression, {}, env)

