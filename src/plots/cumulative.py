from __future__ import annotations

try:
    import pandas as pd  # type: ignore
except Exception as e:  # pragma: no cover - optional dependency
    raise ImportError("pandas is required for cumulative plots") from e

import plotly.graph_objects as go


def plot_cumulative_conversion(data: pd.DataFrame) -> go.Figure:
    """Return cumulative conversion curve by group using Plotly."""
    required = {"date", "group", "conversion"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(sorted(missing))}")

    if len(data) < 100:
        raise ValueError("Недостаточно данных для построения графика (минимум 100 строк)")

    df = data.copy()
    df = df.sort_values("date")

    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception as e:
            raise ValueError("Колонка date должна быть датой") from e

    df["conv_cum"] = df.groupby("group")["conversion"].cumsum()
    df["obs_cum"] = df.groupby("group").cumcount() + 1
    df["cr"] = df["conv_cum"] / df["obs_cum"]

    fig = go.Figure()
    for grp, gdf in df.groupby("group"):
        fig.add_trace(
            go.Scatter(
                x=gdf["date"],
                y=gdf["cr"],
                mode="lines+markers",
                name=str(grp),
            )
        )

    fig.update_layout(
        title="Cumulative Conversion",
        xaxis_title="Date",
        yaxis_title="Conversion Rate",
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True)),
        margin=dict(l=40, r=20, t=50, b=40),
    )

    return fig
