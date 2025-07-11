"""Optional Bayesian analysis implementation using numpy and scipy."""
from typing import Tuple
import numpy as np
from scipy.stats import beta
from metrics import track_time


@track_time
def bayesian_analysis(alpha_prior: float, beta_prior: float, users_a: int, conv_a: int, users_b: int, conv_b: int) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Full-featured Bayesian A/B analysis."""
    a1 = alpha_prior + conv_a
    b1 = beta_prior + (users_a - conv_a)
    a2 = alpha_prior + conv_b
    b2 = beta_prior + (users_b - conv_b)
    x = np.linspace(0, 1, 500)
    pdf_a = beta.pdf(x, a1, b1)
    pdf_b = beta.pdf(x, a2, b2)
    cdf_a = beta.cdf(x, a1, b1)
    prob = np.trapz(pdf_b * cdf_a, x)
    return prob, x, pdf_a, pdf_b

