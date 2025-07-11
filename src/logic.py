"""Compatibility wrapper importing public helpers from new modules."""

from stats.ab_test import (
    required_sample_size,
    calculate_mde,
    evaluate_abn_test,
    bayesian_analysis,
    run_aa_simulation,
    run_sequential_analysis,
    run_obrien_fleming,
    calculate_roi,
    cuped_adjustment,
    srm_check,
    pocock_alpha_curve,
)

from bandit.strategies import thompson_sampling, ucb1, epsilon_greedy

from plots import (
    plot_bayesian_posterior,
    plot_confidence_intervals,
    plot_power_curve,
    plot_bootstrap_distribution,
    plot_alpha_spending,
    save_plot,
)

from utils import segment_data, compute_custom_metric
