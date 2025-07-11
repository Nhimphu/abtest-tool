try:
    from prometheus_client import Counter, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST
except Exception:  # pragma: no cover - fallback stub
    class _Timer:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    class _Metric:
        def __init__(self, *a, **k):
            pass
        def labels(self, *a, **k):
            return self
        def inc(self, amount=1):
            pass
        def time(self):
            return _Timer()

    Counter = Histogram = Summary = _Metric  # type: ignore
    def generate_latest(reg=None):
        return b""
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

import functools

REQUEST_COUNTER = Counter(
    "api_requests_total",
    "Total API requests",
    ["endpoint", "method", "status"],
)

FUNCTION_DURATION = Histogram(
    "heavy_function_seconds",
    "Time spent in heavy functions",
    ["function"],
)


def track_time(func):
    """Decorator to measure execution time using FUNCTION_DURATION."""
    metric = FUNCTION_DURATION.labels(func.__name__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with metric.time():
            return func(*args, **kwargs)

    return wrapper
