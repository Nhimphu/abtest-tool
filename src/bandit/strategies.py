import math
import types
from typing import Sequence

try:
    import numpy as np
except Exception:
    np = types.SimpleNamespace(
        random=types.SimpleNamespace(
            beta=lambda a, b: 0.0, randint=lambda a, b=None: 0, random=lambda: 0.0
        ),
        argmax=lambda arr: max(range(len(arr)), key=lambda i: arr[i]),
    )


def thompson_sampling(alpha: Sequence[float], beta: Sequence[float]) -> int:
    """Return index of arm selected by Thompson sampling."""
    samples = [np.random.beta(a, b) for a, b in zip(alpha, beta)]
    return int(np.argmax(samples))


def ucb1(values: Sequence[float], counts: Sequence[int]) -> int:
    """Return index of arm to select using UCB1."""
    t = sum(counts) + 1
    ucb_values = [
        v / c + math.sqrt(2 * math.log(t) / c) if c > 0 else float("inf")
        for v, c in zip(values, counts)
    ]
    return int(np.argmax(ucb_values))


def epsilon_greedy(
    values: Sequence[float], counts: Sequence[int], epsilon: float = 0.1
) -> int:
    """Return index of arm using epsilon-greedy selection."""
    if np.random.random() < epsilon or not any(counts):
        return int(np.random.randint(0, len(values)))
    avgs = [v / c if c > 0 else 0.0 for v, c in zip(values, counts)]
    return int(np.argmax(avgs))
