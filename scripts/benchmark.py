import time
import numpy as np
from stats.ab_test import evaluate_abn_test, run_sequential_analysis


def generate_dataset(size: int = 1_000_000, p_a: float = 0.1, p_b: float = 0.12):
    """Return random dataset for two groups."""
    groups = np.random.randint(0, 2, size=size)
    probs = np.where(groups == 0, p_a, p_b)
    conversions = np.random.random(size) < probs
    return groups, conversions


def aggregate(groups: np.ndarray, conversions: np.ndarray):
    users_a = int(np.sum(groups == 0))
    users_b = int(np.sum(groups == 1))
    conv_a = int(np.sum(conversions[groups == 0]))
    conv_b = int(np.sum(conversions[groups == 1]))
    return users_a, conv_a, users_b, conv_b


def benchmark(iters: int = 3, size: int = 1_000_000):
    for i in range(1, iters + 1):
        groups, conversions = generate_dataset(size)
        ua, ca, ub, cb = aggregate(groups, conversions)

        start = time.perf_counter()
        evaluate_abn_test(ua, ca, ub, cb)
        eval_time = time.perf_counter() - start

        start = time.perf_counter()
        run_sequential_analysis(ua, ca, ub, cb, 0.05)
        seq_time = time.perf_counter() - start

        print(f"Iteration {i}: eval={eval_time:.3f}s seq={seq_time:.3f}s")


if __name__ == "__main__":
    benchmark()
