"""Data validation and inference helpers."""
from __future__ import annotations

import logging
from typing import Literal

import pandas as pd

from .types import DataSchema, MetricType

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Structured error used when data validation fails."""

    def __init__(self, code: str, title: str, details: str, fix_hint: str):
        super().__init__(title)
        self.code = code
        self.title = title
        self.details = details
        self.fix_hint = fix_hint

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "details": self.details,
            "fix_hint": self.fix_hint,
        }


def validate_dataframe(
    df: "pd.DataFrame",
    schema: DataSchema,
    nan_policy: Literal["drop", "zero", "error"] = "drop",
) -> "pd.DataFrame":
    """Validate dataframe structure and handle missing values.

    Returns the validated (and possibly modified) dataframe.
    """

    required = [schema.group_col, schema.metric_col]
    if schema.user_id:
        required.append(schema.user_id)
    if schema.preperiod_metric_col:
        required.append(schema.preperiod_metric_col)

    for col in required:
        if col not in df.columns:
            raise ValidationError(
                "missing_column",
                f"Не найдена колонка '{col}'",
                f"Column '{col}' was not found in data frame",
                "Проверьте имя колонки или обновите DataSchema",
            )
        if df[col].isna().all():
            raise ValidationError(
                "empty_column",
                f"Колонка '{col}' полностью пустая",
                f"Column '{col}' contains only NaN values",
                "Убедитесь, что колонка заполнена или удалите её",
            )

    if len(df) < 100:
        logger.warning("Dataframe has only %d rows", len(df))

    if df[schema.metric_col].isna().any():
        if nan_policy == "error":
            raise ValidationError(
                "nan_in_metric",
                "В метрике обнаружены NaN",
                f"Column '{schema.metric_col}' contains missing values",
                "Выберите nan_policy='drop' или очистите данные",
            )
        if nan_policy == "drop":
            before = len(df)
            df = df.dropna(subset=[schema.metric_col])
            removed = before - len(df)
            logger.info("Dropped %d rows due to NaN in metric column", removed)
        elif nan_policy == "zero":
            count = df[schema.metric_col].isna().sum()
            df[schema.metric_col] = df[schema.metric_col].fillna(0)
            logger.info("Filled %d NaN values in metric column with zero", count)

    return df


def infer_metric_type(df: pd.DataFrame, metric_col: str) -> MetricType:
    """Infer metric type from column values."""
    unique = set(df[metric_col].dropna().unique())
    if unique.issubset({0, 1}):
        return "binomial"
    return "continuous"
