import math
from typing import Dict, Optional, Tuple

import numpy as np

try:  # pragma: no cover - fallback when scipy not available
    from scipy.stats import beta as beta_dist
except Exception:  # pragma: no cover - minimal beta pdf/cdf
    def _beta_pdf_scalar(x: float, a: float, b: float) -> float:
        coeff = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b))
        return coeff * (x ** (a - 1)) * ((1.0 - x) ** (b - 1))

    def _beta_cdf_scalar(x: float, a: float, b: float, n: int = 1000) -> float:
        if x <= 0.0:
            return 0.0
        xs = np.linspace(0.0, x, n)
        ys = _beta_pdf_scalar(xs, a, b)
        return float(np.trapz(ys, xs))

    class _Beta:
        @staticmethod
        def pdf(x, a, b):
            x_arr = np.asarray(x)
            return np.vectorize(lambda v: _beta_pdf_scalar(float(v), a, b))(x_arr)

        @staticmethod
        def cdf(x, a, b):
            x_arr = np.asarray(x)
            return np.vectorize(lambda v: _beta_cdf_scalar(float(v), a, b))(x_arr)

    beta_dist = _Beta()


# ---------------------------------------------------------------------------
# Conjugate updates
# ---------------------------------------------------------------------------


def beta_post(a_prior: float, b_prior: float, x: int, n: int) -> Tuple[float, float]:
    """Posterior parameters for Beta-Binomial model."""
    return a_prior + x, b_prior + n - x


def normal_inv_gamma_post(
    mu0: float,
    k0: float,
    alpha0: float,
    beta0: float,
    data: np.ndarray,
) -> Dict[str, float]:
    """Posterior parameters of Normal-Inverse-Gamma prior given data."""
    data = np.asarray(data, dtype=float)
    n = data.size
    if n == 0:
        return {"mu": mu0, "k": k0, "alpha": alpha0, "beta": beta0}
    mean = data.mean()
    k_n = k0 + n
    mu_n = (k0 * mu0 + n * mean) / k_n
    alpha_n = alpha0 + n / 2
    ss = np.sum((data - mean) ** 2)
    beta_n = beta0 + 0.5 * ss + (k0 * n * (mean - mu0) ** 2) / (2 * k_n)
    return {"mu": float(mu_n), "k": float(k_n), "alpha": float(alpha_n), "beta": float(beta_n)}


# ---------------------------------------------------------------------------
# Probability of win calculations
# ---------------------------------------------------------------------------


def prob_win_binomial(
    x1: int,
    n1: int,
    x2: int,
    n2: int,
    a0: float = 1,
    b0: float = 1,
    rope: Optional[Tuple[float, float]] = None,
    grid: int = 2000,
) -> Dict[str, Optional[float]]:
    """Probability B wins for binomial metrics with optional ROPE."""
    a1, b1 = beta_post(a0, b0, x1, n1)
    a2, b2 = beta_post(a0, b0, x2, n2)
    xs = np.linspace(0.0, 1.0, grid)
    f1 = beta_dist.pdf(xs, a1, b1)
    cdf2 = beta_dist.cdf(xs, a2, b2)
    p_win = float(np.trapz(f1 * (1 - cdf2), xs))
    p_rope: Optional[float] = None
    if rope is not None:
        lo, hi = rope
        hi_cdf = beta_dist.cdf(np.clip(xs + hi, 0.0, 1.0), a2, b2)
        lo_cdf = beta_dist.cdf(np.clip(xs + lo, 0.0, 1.0), a2, b2)
        p_rope = float(np.trapz(f1 * (hi_cdf - lo_cdf), xs))
    return {"p_win": p_win, "p_rope": p_rope, "rope": rope}


def _sample_mean_from_post(post: Dict[str, float], rng: np.random.Generator, size: int) -> np.ndarray:
    alpha, beta, k, mu = post["alpha"], post["beta"], post["k"], post["mu"]
    sigma2 = beta / rng.gamma(alpha, 1.0, size=size)
    return rng.normal(mu, np.sqrt(sigma2 / k), size=size)


def prob_win_continuous(
    a: np.ndarray,
    b: np.ndarray,
    rope: Optional[Tuple[float, float]] = None,
    draws: int = 10000,
    seed: int = 0,
) -> Dict[str, Optional[float]]:
    """Probability B wins for continuous metrics using Normal-Inverse-Gamma posterior."""
    rng = np.random.default_rng(seed)
    prior = {"mu": 0.0, "k": 1e-6, "alpha": 1e-6, "beta": 1e-6}
    post_a = normal_inv_gamma_post(prior["mu"], prior["k"], prior["alpha"], prior["beta"], np.asarray(a, dtype=float))
    post_b = normal_inv_gamma_post(prior["mu"], prior["k"], prior["alpha"], prior["beta"], np.asarray(b, dtype=float))
    mu_a = _sample_mean_from_post(post_a, rng, draws)
    mu_b = _sample_mean_from_post(post_b, rng, draws)
    diff = mu_b - mu_a
    p_win = float(np.mean(diff > 0))
    p_rope: Optional[float] = None
    if rope is not None:
        lo, hi = rope
        p_rope = float(np.mean((diff >= lo) & (diff <= hi)))
    return {"p_win": p_win, "p_rope": p_rope, "rope": rope}
