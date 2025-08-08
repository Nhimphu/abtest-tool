import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import pytest

from abtest_core import DataSchema, validate_dataframe, ValidationError, infer_metric_type


def _sample_df():
    return pd.DataFrame(
        {
            "user": [1, 2, 3, 4],
            "group": ["A", "B", "A", "B"],
            "metric": [1, 0, None, 1],
            "pre": [0.1, 0.2, 0.3, 0.4],
        }
    )


def test_validate_dataframe_drop(caplog):
    df = _sample_df()
    schema = DataSchema(user_id="user", group_col="group", metric_col="metric", preperiod_metric_col="pre")
    caplog.set_level("INFO")
    cleaned = validate_dataframe(df, schema, nan_policy="drop")
    assert len(cleaned) == 3
    assert "Dropped" in caplog.text


def test_validate_dataframe_missing_column():
    df = _sample_df().drop(columns=["group"])
    schema = DataSchema(user_id="user", group_col="group", metric_col="metric", preperiod_metric_col="pre")
    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)
    assert exc.value.code == "missing_column"
    assert "Не найдена колонка" in exc.value.title


def test_validate_dataframe_nan_error():
    df = _sample_df()
    schema = DataSchema(user_id="user", group_col="group", metric_col="metric", preperiod_metric_col="pre")
    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema, nan_policy="error")
    assert exc.value.code == "nan_in_metric"
    assert "nan_policy='drop'" in exc.value.fix_hint


def test_infer_metric_type():
    df_bin = pd.DataFrame({"metric": [0, 1, 0, 1]})
    assert infer_metric_type(df_bin, "metric") == "binomial"

    df_cont = pd.DataFrame({"metric": [0.1, 1.2, 0.3]})
    assert infer_metric_type(df_cont, "metric") == "continuous"
