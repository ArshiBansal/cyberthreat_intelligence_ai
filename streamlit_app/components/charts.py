"""
Plotly chart helpers for Streamlit pages.

Pure rendering functions — they accept data and return Plotly figures
(or write directly to Streamlit when `render=True`).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def kpi_row(metrics: Dict[str, Any], *, columns: Optional[int] = None) -> None:
    """Render a row of st.metric widgets."""
    if not metrics:
        return
    n = columns or len(metrics)
    cols = st.columns(n)
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)


def urgency_bar_chart(
    urgency_counts: Dict[str, int],
    *,
    height: int = 320,
    render: bool = True,
) -> go.Figure:
    """Bar chart of urgency_level → count."""
    df = (
        pd.DataFrame({"urgency": list(urgency_counts.keys()), "count": list(urgency_counts.values())})
        .sort_values("count", ascending=False)
    )
    fig = px.bar(df, x="urgency", y="count", color="urgency", text="count")
    fig.update_layout(showlegend=False, height=height, margin=dict(t=10, b=10))
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig


def urgency_pie_chart(
    urgency_counts: Dict[str, int],
    *,
    height: int = 360,
    hole: float = 0.35,
    render: bool = True,
) -> go.Figure:
    """Donut / pie chart of urgency distribution."""
    df = pd.DataFrame({"urgency": list(urgency_counts.keys()), "count": list(urgency_counts.values())})
    fig = px.pie(df, names="urgency", values="count", hole=hole)
    fig.update_layout(height=height, margin=dict(t=10, b=10))
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig


def score_histogram(
    series: pd.Series,
    *,
    title: Optional[str] = None,
    nbins: int = 40,
    show_mean: bool = True,
    height: int = 350,
    render: bool = True,
) -> go.Figure:
    """Histogram of a numeric score column."""
    data = series.dropna()
    col_name = series.name or "score"
    fig = px.histogram(data, x=col_name, nbins=nbins, title=title)
    if show_mean and len(data):
        fig.add_vline(
            x=float(data.mean()),
            line_dash="dash",
            line_color="red",
            annotation_text=f"mean={data.mean():.1f}",
        )
    fig.update_layout(height=height, margin=dict(t=40 if title else 20, b=10))
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig


def score_boxplot(
    df: pd.DataFrame,
    *,
    x: str = "urgency_level",
    y: str = "threat_score",
    height: int = 360,
    render: bool = True,
) -> go.Figure:
    """Box plot of a score grouped by a categorical column."""
    plot_df = df.dropna(subset=[y])
    fig = px.box(plot_df, x=x, y=y)
    fig.update_layout(height=height, margin=dict(t=10, b=10))
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig


def temporal_line_chart(
    df: pd.DataFrame,
    *,
    date_col: str = "first_reported",
    freq: str = "M",
    height: int = 360,
    title: Optional[str] = None,
    render: bool = True,
) -> go.Figure:
    """Line chart of incident counts over time."""
    tmp = df.dropna(subset=[date_col]).copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col])
    tmp["period"] = tmp[date_col].dt.to_period(freq).astype(str)
    monthly = tmp.groupby("period").size().reset_index(name="count")

    fig = px.line(monthly, x="period", y="count", markers=True, title=title)
    fig.update_layout(
        height=height,
        margin=dict(t=40 if title else 10, b=10),
        xaxis_title="Period",
        yaxis_title="Incidents",
    )
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig


def entity_hbar_chart(
    items: List[Dict[str, Any]],
    *,
    value_key: str = "value",
    count_key: str = "count",
    title: Optional[str] = None,
    max_label_len: int = 40,
    height: Optional[int] = None,
    render: bool = True,
) -> go.Figure:
    """Horizontal bar chart for entity frequency lists."""
    if not items:
        fig = go.Figure()
        fig.update_layout(title=title or "No data", height=200)
        if render:
            st.plotly_chart(fig, use_container_width=True)
        return fig

    df = pd.DataFrame(items)
    df["label"] = df[value_key].astype(str).str.slice(0, max_label_len)
    df = df.sort_values(count_key, ascending=True)

    h = height or max(280, len(df) * 18)
    fig = px.bar(df, x=count_key, y="label", orientation="h", title=title)
    fig.update_layout(height=h, margin=dict(t=40 if title else 10, b=10), yaxis_title="")
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig


def correlation_heatmap(
    df: pd.DataFrame,
    columns: Optional[Sequence[str]] = None,
    *,
    height: int = 400,
    render: bool = True,
) -> go.Figure:
    """Correlation heatmap for numeric columns."""
    cols = list(columns) if columns else [
        c for c in ["threat_score", "severity_score", "credibility_score",
                     "source_count", "article_count"]
        if c in df.columns
    ]
    if len(cols) < 2:
        fig = go.Figure()
        fig.update_layout(title="Not enough numeric columns", height=200)
        if render:
            st.plotly_chart(fig, use_container_width=True)
        return fig

    corr = df[cols].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(height=height, margin=dict(t=10, b=10))
    if render:
        st.plotly_chart(fig, use_container_width=True)
    return fig