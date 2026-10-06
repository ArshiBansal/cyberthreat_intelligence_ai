"""
Home / Overview page — Threat Incident Intelligence Platform.

Shows dataset KPIs, recent incidents, and high-level score distributions.
Fully independent of Jupyter notebooks; reads only from MongoDB.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Project root on path (streamlit_app/pages → project root)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import (
    ping_database,
    count_incidents,
    get_recent_incidents,
    get_urgency_distribution,
    get_score_statistics,
    find_incidents,
)
from src.utils import truncate_text, format_score

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Home — Threat Intelligence",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Threat Incident Intelligence Platform")
st.caption(
    "Defensive cybersecurity analytics · MongoDB-backed · AI/NLP-assisted"
)


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _check_mongo() -> bool:
    try:
        validate_config()
        return ping_database()
    except Exception:
        return False


if not _check_mongo():
    st.error(
        "Cannot reach MongoDB. Check `MONGODB_URI` in `.env` and ensure the "
        "server is running. Run notebook `01_data_ingestion.ipynb` first."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------------------
@st.cache_data(ttl=120, show_spinner="Loading KPIs…")
def load_kpis() -> dict:
    total = count_incidents()
    urgency = get_urgency_distribution()
    threat_stats = get_score_statistics("threat_score")
    severity_stats = get_score_statistics("severity_score")
    return {
        "total": total,
        "urgency": urgency,
        "threat": threat_stats,
        "severity": severity_stats,
    }


@st.cache_data(ttl=120, show_spinner="Loading recent incidents…")
def load_recent(n: int = 15) -> list:
    return get_recent_incidents(n=n)


@st.cache_data(ttl=300, show_spinner="Loading score samples…")
def load_score_sample(limit: int = 3000) -> pd.DataFrame:
    docs = find_incidents(
        projection={
            "_id": 0,
            "threat_score": 1,
            "severity_score": 1,
            "credibility_score": 1,
            "urgency_level": 1,
            "first_reported": 1,
        },
        limit=limit,
        sort=[("last_reported", -1)],
    )
    return pd.DataFrame(docs)


# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
kpis = load_kpis()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Incidents", f"{kpis['total']:,}")
c2.metric(
    "Avg Threat Score",
    format_score(kpis["threat"].get("avg")),
)
c3.metric(
    "Avg Severity Score",
    format_score(kpis["severity"].get("avg")),
)
c4.metric(
    "Urgency Levels",
    str(len(kpis["urgency"])),
)

st.divider()

# ---------------------------------------------------------------------------
# Urgency distribution + score histograms
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Urgency Distribution")
    urg = kpis["urgency"]
    if urg:
        urg_df = (
            pd.DataFrame({"urgency": list(urg.keys()), "count": list(urg.values())})
            .sort_values("count", ascending=False)
        )
        fig = px.bar(
            urg_df,
            x="urgency",
            y="count",
            color="urgency",
            text="count",
            title=None,
        )
        fig.update_layout(showlegend=False, height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No urgency data available.")

with right:
    st.subheader("Threat Score Distribution")
    sample = load_score_sample()
    if not sample.empty and "threat_score" in sample.columns:
        fig2 = px.histogram(
            sample.dropna(subset=["threat_score"]),
            x="threat_score",
            nbins=40,
            title=None,
        )
        fig2.update_layout(height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No threat_score data available.")

# ---------------------------------------------------------------------------
# Recent incidents table
# ---------------------------------------------------------------------------
st.subheader("Recent Incidents")
recent = load_recent(15)

if not recent:
    st.warning("No incidents found. Run data ingestion first.")
else:
    rows = []
    for doc in recent:
        rows.append(
            {
                "cluster_id": doc.get("cluster_id", ""),
                "title": truncate_text(str(doc.get("title") or ""), 80),
                "urgency": doc.get("urgency_level") or "—",
                "threat": format_score(doc.get("threat_score")),
                "severity": format_score(doc.get("severity_score")),
                "sources": doc.get("source_count") or 0,
                "last_reported": str(doc.get("last_reported") or "")[:10],
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    f"Database: **{settings.mongodb_db}** · "
    "Dataset: [ThreatCluster](https://huggingface.co/datasets/threatcluster/threat-incident-clusters) (CC-BY-4.0) · "
    "Defensive use only — predictions are not verified facts."
)