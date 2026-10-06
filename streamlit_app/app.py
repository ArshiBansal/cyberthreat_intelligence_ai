"""
Threat Incident Intelligence Platform — Streamlit entry point.

Run from the project root:

    streamlit run streamlit_app/app.py

Multipage navigation is automatic: every script under streamlit_app/pages/
appears in the sidebar. This file is the home / landing page.

Architecture rule:
    - No Jupyter notebook imports or execution.
    - All data access goes through src.db (MongoDB / PyMongo).
    - ML artifacts are loaded from models/ via src.models when needed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Ensure project root is importable (streamlit_app/ → project root)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import ping_database, count_incidents, get_recent_incidents, get_urgency_distribution
from src.utils import truncate_text, format_score

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Threat Incident Intelligence Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛡️ Threat Incident Intelligence Platform")
st.caption(
    "Defensive cybersecurity analytics · MongoDB · NLP / ML · independent of Jupyter runtime"
)

# ---------------------------------------------------------------------------
# Connectivity banner
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _mongo_status() -> tuple[bool, str]:
    try:
        validate_config()
        ok = ping_database()
        return ok, settings.mongodb_db
    except Exception as exc:
        return False, str(exc)


mongo_ok, mongo_info = _mongo_status()

if not mongo_ok:
    st.error(
        f"Cannot reach MongoDB ({mongo_info}). "
        "Set `MONGODB_URI` in `.env` and ensure the server is running. "
        "Ingest data with notebook `01_data_ingestion.ipynb` before using the app."
    )
    st.stop()

st.success(f"Connected to MongoDB database **{mongo_info}**")

# ---------------------------------------------------------------------------
# Quick KPIs
# ---------------------------------------------------------------------------
@st.cache_data(ttl=120)
def _quick_stats():
    total = count_incidents()
    urgency = get_urgency_distribution()
    recent = get_recent_incidents(n=5)
    return total, urgency, recent


total, urgency, recent = _quick_stats()

c1, c2, c3 = st.columns(3)
c1.metric("Total incidents", f"{total:,}")
c2.metric("Urgency classes", str(len(urgency)))
c3.metric("Database", mongo_info)

if total == 0:
    st.warning(
        "No incidents in the database yet. "
        "Run `notebooks/01_data_ingestion.ipynb` to load the Hugging Face dataset."
    )

# ---------------------------------------------------------------------------
# Navigation guide
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Navigate")

st.markdown(
    """
Use the **sidebar** to open any page:

| Page | Purpose |
|------|---------|
| **Home** | KPIs, urgency chart, recent incidents |
| **Incident Search** | Keyword + semantic search with filters |
| **Incident Explorer** | Deep dive into a single incident |
| **Threat Analytics** | Score distributions, trends, correlations |
| **Entity Explorer** | CVEs, companies, malware, ATT&CK, sectors |
| **AI / NLP Insights** | Urgency/priority prediction, similar incidents |
| **About** | Architecture, dataset attribution, ethics |
"""
)

# ---------------------------------------------------------------------------
# Recent snapshot
# ---------------------------------------------------------------------------
if recent:
    st.subheader("Most recent incidents")
    import pandas as pd

    rows = [
        {
            "cluster_id": d.get("cluster_id", ""),
            "title": truncate_text(str(d.get("title") or ""), 70),
            "urgency": d.get("urgency_level") or "—",
            "threat": format_score(d.get("threat_score")),
        }
        for d in recent
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Dataset: [ThreatCluster](https://huggingface.co/datasets/threatcluster/threat-incident-clusters) (CC-BY-4.0) · "
    "Defensive research only — model predictions are not verified facts · "
    "Notebooks and Streamlit share MongoDB only; neither executes the other."
)