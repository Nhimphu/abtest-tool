"""Typed configuration models used across analysis core."""
from __future__ import annotations

from typing import Literal, Optional, List

from pydantic import BaseModel

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
    use_sequential: bool = False
    sequential_preset: Optional[Literal["pocock", "obf"]] = None
    nan_policy: Literal["drop", "zero", "error"] = "drop"
    metric_type: MetricType
    segments: List[str] = []
    multiple_testing: Literal["none", "holm", "bonferroni", "by"] = "holm"
