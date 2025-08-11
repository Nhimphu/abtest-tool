"""Typed configuration models used across analysis core."""
from __future__ import annotations

from typing import Literal, Optional

try:  # pragma: no cover - allow running without pydantic
    from pydantic import BaseModel
except Exception:  # pragma: no cover - minimal stub
    class BaseModel:  # type: ignore
        def __init__(self, **data):
            for k, v in data.items():
                setattr(self, k, v)

        def dict(self) -> dict:
            return self.__dict__.copy()

MetricType = Literal["binomial", "continuous", "ratio"]


class DataSchema(BaseModel):
    """Describes required dataframe column names for analysis."""

    user_id: Optional[str] = None
    group_col: str
    metric_col: str
    preperiod_metric_col: Optional[str] = None


class AnalysisConfig(BaseModel):
    """Configuration for analysis parameters."""

    alpha: float
    sided: Literal["two", "left", "right"] = "two"
    use_cuped: bool = False
    preperiod_metric_col: Optional[str] = None
    use_sequential: bool = False
    sequential_preset: Optional[Literal["pocock", "obf"]] = None
    sequential_looks: int = 5
    sequential_history_p: list[float] = []  # optional, allow external history
    nan_policy: Literal["drop", "zero", "error"] = "drop"
    metric_type: MetricType
    segments: list[str] = []
    multiple_testing: Literal["none", "holm", "by"] = "holm"
    robust: bool = False
    bootstrap: bool = False
    use_fieller: bool = False
    use_bayes: bool = False
    bayes_rope: tuple[float, float] | None = None
    bayes_draws: int = 10000
