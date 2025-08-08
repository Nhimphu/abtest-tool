"""Minimal numpy stub for testing."""


class ndarray(list):
    pass


def corrcoef(a, b):
    return [[1.0, 0.0], [0.0, 1.0]]


def isnan(x):
    return False


def mean(a):
    return sum(a) / len(a)


def var(a, ddof=0):
    m = mean(a)
    return sum((x - m) ** 2 for x in a) / (len(a) - ddof)


def array(x):
    return list(x)


class random:
    class Generator:
        pass

    @staticmethod
    def default_rng(seed=None):
        return random()
