"""
Entity Explorer — browse CVEs, companies, malware, countries, sectors, ATT&CK.

Fully independent of Jupyter notebooks; reads only from MongoDB.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import (
    ping_database,
    get_entity_values,
    find_incidents,
    count_incidents,
)
from src.utils import truncate_text, format_score

st.set_page_config(
    page_title="Entities — Threat Intelligence",
    page_icon="🏷️",
    layout="wide",
)

st.title("🏷️ Entity Explorer")
st.caption("Explore CVEs, companies, malware, countries, sectors, and ATT&CK techniques")


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


ENTITY_TYPES = [
    "cve",
    "company",
    "malware",
    "country",
    "sector",
    "mitre_attack",
    "product",
    "threat_actor",
]


@st.cache_data(ttl=300, show_spinner="Loading entity frequencies…")
def load_entity_top(entity_type: str, limit: int = 40) -> List[Dict[str, Any]]:
    return get_entity_values(entity_type, limit=limit)


@st.cache_data(ttl=120, show_spinner="Finding incidents…")
def incidents_with_entity(entity_type: str, value: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Find incidents whose entities.<type> array contains value."""
    filt = {f"entities.{entity_type}": value}
    return find_incidents(
        filters=filt,
        projection={
            "_id": 0,
            "cluster_id": 1,
            "title": 1,
            "urgency_level": 1,
            "threat_score": 1,
            "severity_score": 1,
            "source_count": 1,
        },
        sort=[("threat_score", -1)],
        limit=limit,
    )


with st.sidebar:
    st.header("Entity type")
    etype = st.selectbox("Type", ENTITY_TYPES, index=0)
    top_n = st.slider("Top N values", 10, 50, 25, 5)
    st.caption(f"Total incidents in DB: **{count_incidents():,}**")


st.subheader(f"Top {etype} values")

values = load_entity_top(etype, limit=top_n)

if not values:
    st.info(f"No data for entity type `{etype}`.")
    st.stop()

freq_df = pd.DataFrame(values)
freq_df["label"] = freq_df["value"].apply(lambda v: truncate_text(str(v), 40))

fig = px.bar(
    freq_df.sort_values("count", ascending=True).tail(top_n),
    x="count",
    y="label",
    orientation="h",
    title=None,
)
fig.update_layout(height=max(320, top_n * 18), margin=dict(t=10, b=10), yaxis_title="")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    freq_df[["value", "count"]].rename(columns={"value": etype, "count": "incidents"}),
    use_container_width=True,
    hide_index=True,
)

st.divider()

st.subheader("Drill-down: incidents for a value")

selected_value = st.selectbox(
    f"Select a {etype}",
    options=freq_df["value"].tolist(),
    format_func=lambda v: f"{truncate_text(str(v), 50)} ({freq_df.loc[freq_df['value']==v, 'count'].values[0]})",
)

if selected_value:
    hits = incidents_with_entity(etype, selected_value, limit=40)
    st.write(f"**{len(hits)}** incident(s) containing `{selected_value}`")

    if hits:
        rows = []
        for d in hits:
            rows.append(
                {
                    "cluster_id": d.get("cluster_id", ""),
                    "title": truncate_text(str(d.get("title") or ""), 70),
                    "urgency": d.get("urgency_level") or "—",
                    "threat": format_score(d.get("threat_score")),
                    "severity": format_score(d.get("severity_score")),
                    "sources": d.get("source_count") or 0,
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No matching incidents (entity field may use different casing).")

st.divider()
st.caption(f"DB: **{settings.mongodb_db}** · Entity data comes from the ThreatCluster dataset.")