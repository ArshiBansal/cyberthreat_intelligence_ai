"""
Incident Explorer — browse a single incident in depth.

Select by cluster_id or from recent / filtered lists.
Shows summary, scores, entities, sources, keywords, dates.
Fully independent of Jupyter notebooks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import (
    ping_database,
    find_incident_by_id,
    find_incidents,
    get_recent_incidents,
    search_incidents_by_keyword,
    count_incidents,
)
from src.utils import truncate_text, format_score

st.set_page_config(
    page_title="Explorer — Threat Intelligence",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Incident Explorer")
st.caption("Inspect a single incident: summary, scores, entities, sources, dates")


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


@st.cache_data(ttl=120)
def load_recent_ids(n: int = 50) -> List[str]:
    docs = get_recent_incidents(n=n)
    return [d.get("cluster_id") for d in docs if d.get("cluster_id")]


@st.cache_data(ttl=60)
def search_ids(keyword: str, limit: int = 30) -> List[Dict[str, Any]]:
    if not keyword.strip():
        return []
    return search_incidents_by_keyword(keyword.strip(), limit=limit)


with st.sidebar:
    st.header("Select incident")

    mode = st.radio("Lookup by", ["Recent list", "Keyword search", "cluster_id"], index=0)

    selected_id: Optional[str] = None

    if mode == "Recent list":
        ids = load_recent_ids(50)
        if ids:
            selected_id = st.selectbox("Recent cluster_id", ids)
        else:
            st.warning("No incidents found.")

    elif mode == "Keyword search":
        kw = st.text_input("Keyword", placeholder="ransomware, CVE-2024, …")
        if kw.strip():
            hits = search_ids(kw, limit=30)
            if hits:
                labels = {
                    d["cluster_id"]: f"{d['cluster_id']} — {truncate_text(str(d.get('title') or ''), 40)}"
                    for d in hits if d.get("cluster_id")
                }
                selected_id = st.selectbox(
                    "Matches",
                    list(labels.keys()),
                    format_func=lambda x: labels.get(x, x),
                )
            else:
                st.info("No matches.")
        else:
            st.caption("Type a keyword to search.")

    else:
        selected_id = st.text_input("cluster_id", placeholder="e.g. 971184ec").strip() or None

    load_btn = st.button("Load incident", type="primary", use_container_width=True)


if not load_btn and not selected_id:
    st.info(
        f"Database holds **{count_incidents():,}** incidents. "
        "Pick one from the sidebar and click **Load incident**."
    )
    st.stop()

if not selected_id:
    st.warning("No cluster_id selected.")
    st.stop()

doc = find_incident_by_id(selected_id)

if not doc:
    st.error(f"Incident `{selected_id}` not found.")
    st.stop()

st.subheader(doc.get("title") or selected_id)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Urgency", str(doc.get("urgency_level") or "—"))
m2.metric("Threat", format_score(doc.get("threat_score")))
m3.metric("Severity", format_score(doc.get("severity_score")))
m4.metric("Credibility", format_score(doc.get("credibility_score")))
m5.metric("Sources", str(doc.get("source_count") or 0))

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### Summary")
    st.write(doc.get("summary") or "_No summary available._")

    st.markdown("### Keywords")
    kws = doc.get("keywords") or []
    if kws:
        st.write(", ".join(str(k) for k in kws))
    else:
        st.caption("None")

with col_right:
    st.markdown("### Timeline")
    st.write(f"**First reported:** {doc.get('first_reported') or '—'}")
    st.write(f"**Last reported:** {doc.get('last_reported') or '—'}")
    st.write(f"**Article count:** {doc.get('article_count') or 0}")
    st.write(f"**cluster_id:** `{doc.get('cluster_id')}`")
    if doc.get("url"):
        st.markdown(f"[Open source URL]({doc['url']})")

st.markdown("### Entities")
ents = doc.get("entities") or {}
if isinstance(ents, dict) and ents:
    ent_cols = st.columns(min(3, len(ents)))
    for i, (etype, values) in enumerate(ents.items()):
        with ent_cols[i % len(ent_cols)]:
            st.markdown(f"**{etype}**")
            if values:
                for v in values:
                    st.write(f"- {v}")
            else:
                st.caption("—")
else:
    st.caption("No structured entities.")

st.markdown("### Sources")
sources = doc.get("sources") or []
if sources:
    for s in sources:
        st.write(f"- {s}")
else:
    st.caption("No sources listed.")

with st.expander("Raw document (JSON)"):
    import json
    from datetime import datetime as _dt

    def _ser(obj):
        if isinstance(obj, _dt):
            return obj.isoformat()
        return str(obj)

    st.code(json.dumps({k: v for k, v in doc.items() if k != "_id"}, default=_ser, indent=2), language="json")

st.divider()
st.caption(f"DB: **{settings.mongodb_db}** · Defensive use only.")