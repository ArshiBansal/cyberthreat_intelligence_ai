"""
Threat Analytics — charts for scores, urgency, and temporal trends.

Fully independent of Jupyter notebooks; reads only from MongoDB.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import (
    ping_database,
    count_incidents,
    find_incidents,
    get_urgency_distribution,
    get_score_statistics,
)
from src.utils import format_score

st.set_page_config(
    page_title="Analytics — Threat Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Threat Analytics")
st.caption("Score distributions, urgency breakdown, and temporal trends")


@st.cache_resource(show_spinner=False)
def _check_mongo() -> bool:
    try:
        validate_config()
        return ping_database()
    except Exception:
        return False


if not _check_mongo():
    st.error("Cannot reach MongoDB. Check `.env` and ensure the server is running.")
    st.stop()


@st.cache_data(ttl=180, show_spinner="Loading analytics data…")
def load_analytics_frame(limit: int = 8000) -> pd.DataFrame:
    docs = find_incidents(
        projection={
            "_id": 0,
            "cluster_id": 1,
            "threat_score": 1,
            "severity_score": 1,
            "credibility_score": 1,
            "urgency_level": 1,
            "source_count": 1,
            "article_count": 1,
            "first_reported": 1,
            "last_reported": 1,
        },
        limit=limit,
        sort=[("last_reported", -1)],
    )
    df = pd.DataFrame(docs)
    for col in ["first_reported", "last_reported"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["threat_score", "severity_score", "credibility_score", "source_count", "article_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "urgency_level" in df.columns:
        df["urgency_level"] = df["urgency_level"].fillna("unknown").astype(str).str.lower()
    return df


@st.cache_data(ttl=180)
def load_kpis() -> dict:
    return {
        "total": count_incidents(),
        "urgency": get_urgency_distribution(),
        "threat": get_score_statistics("threat_score"),
        "severity": get_score_statistics("severity_score"),
        "credibility": get_score_statistics("credibility_score"),
    }


df = load_analytics_frame()
kpis = load_kpis()

if df.empty:
    st.warning("No data available. Run ingestion first.")
    st.stop()

st.caption(f"Analysing **{len(df):,}** sampled incidents (of {kpis['total']:,} total)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sample size", f"{len(df):,}")
c2.metric("Threat mean / max", f"{format_score(kpis['threat'].get('avg'))} / {format_score(kpis['threat'].get('max'))}")
c3.metric("Severity mean", format_score(kpis["severity"].get("avg")))
c4.metric("Credibility mean", format_score(kpis["credibility"].get("avg")))

st.divider()

st.subheader("Score Distributions")

score_cols = [c for c in ["threat_score", "severity_score", "credibility_score"] if c in df.columns]
if score_cols:
    tabs = st.tabs([c.replace("_", " ").title() for c in score_cols])
    for tab, col in zip(tabs, score_cols):
        with tab:
            data = df[col].dropna()
            fig = px.histogram(data, x=col, nbins=40, title=None)
            fig.add_vline(x=data.mean(), line_dash="dash", line_color="red",
                          annotation_text=f"mean={data.mean():.1f}")
            fig.update_layout(height=350, margin=dict(t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.write(
                f"count={len(data):,} · mean={data.mean():.2f} · "
                f"median={data.median():.2f} · std={data.std():.2f} · "
                f"min={data.min():.2f} · max={data.max():.2f}"
            )
else:
    st.info("No score columns available.")

st.subheader("Urgency Breakdown")

left, right = st.columns(2)
urg = kpis["urgency"]

with left:
    if urg:
        urg_df = pd.DataFrame({"urgency": list(urg.keys()), "count": list(urg.values())})
        urg_df = urg_df.sort_values("count", ascending=False)
        fig = px.pie(urg_df, names="urgency", values="count", hole=0.35)
        fig.update_layout(height=360, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No urgency data.")

with right:
    if "urgency_level" in df.columns and "threat_score" in df.columns:
        fig = px.box(
            df.dropna(subset=["threat_score"]),
            x="urgency_level",
            y="threat_score",
            title=None,
        )
        fig.update_layout(height=360, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need urgency_level + threat_score for box plot.")

st.subheader("Temporal Trends")

if "first_reported" in df.columns and df["first_reported"].notna().any():
    tmp = df.dropna(subset=["first_reported"]).copy()
    tmp["month"] = tmp["first_reported"].dt.to_period("M").astype(str)
    monthly = tmp.groupby("month").size().reset_index(name="count")

    fig = px.line(monthly, x="month", y="count", markers=True, title=None)
    fig.update_layout(height=360, margin=dict(t=10, b=10), xaxis_title="Month", yaxis_title="Incidents")
    st.plotly_chart(fig, use_container_width=True)

    if "threat_score" in tmp.columns:
        monthly_threat = (
            tmp.groupby("month")["threat_score"].mean().reset_index(name="avg_threat")
        )
        fig2 = px.line(monthly_threat, x="month", y="avg_threat", markers=True, title="Avg threat score by month")
        fig2.update_layout(height=320, margin=dict(t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No usable first_reported dates for temporal charts.")

st.subheader("Reporting Volume")

v1, v2 = st.columns(2)
with v1:
    if "source_count" in df.columns:
        data = df["source_count"].dropna().clip(upper=df["source_count"].quantile(0.99))
        fig = px.histogram(data, x="source_count", nbins=30, title="Source count")
        fig.update_layout(height=320, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("source_count not available")

with v2:
    if "article_count" in df.columns:
        data = df["article_count"].dropna().clip(upper=df["article_count"].quantile(0.99))
        fig = px.histogram(data, x="article_count", nbins=30, title="Article count")
        fig.update_layout(height=320, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("article_count not available")

st.subheader("Feature Correlation")

corr_cols = [c for c in ["threat_score", "severity_score", "credibility_score",
                          "source_count", "article_count"] if c in df.columns]
if len(corr_cols) >= 2:
    corr = df[corr_cols].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(height=400, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough numeric columns for correlation.")

st.divider()
st.caption(
    f"DB: **{settings.mongodb_db}** · "
    "Scores are dataset ranking signals, not universal severity standards."
)