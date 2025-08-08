# -*- coding: utf-8 -*-
"""Shared state for the analysis wizard."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any, List

import pandas as pd

from abtest_core.types import AnalysisConfig


@dataclass
class WizardViewModel:
    """Container holding data and configuration across wizard steps."""

    df: Optional[pd.DataFrame] = None
    config: Optional[AnalysisConfig] = None
    errors: List[dict] = field(default_factory=list)
    method_notes: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    force_run_when_srm_failed: bool = False
    preperiod_col: Optional[str] = None
