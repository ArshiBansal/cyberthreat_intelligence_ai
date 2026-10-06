"""
Incident Search page — keyword filters + semantic search.

Fully independent of Jupyter notebooks; reads MongoDB and optional
embedding artifacts from models/.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Project root on path
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import (
    ping_database,
    find_incidents,
    search_incidents_by_keyword,
    find_incident_by_id,
    count_incidents,
)
from src.utils import truncate_text, format_score

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Search — Threat Intelligence",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Incident Search")
st.caption("Keyword filters and optional semantic (embedding) search")


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
    st.error("Cannot reach MongoDB. Check `.env` and ensure the server is running.")
    st.stop()


# ---------------------------------------------------------------------------
# Optional embeddings (semantic search)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading embeddings…")
def load_semantic_backend():
    """Return (embeddings, cluster_ids, sentence_model) or (None, None, None)."""
    try:
        from src.models.loaders import load_embeddings
        from sentence_transformers import SentenceTransformer

        emb, ids = load_embeddings()
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return emb, ids, model
    except Exception:
        return None, None, None


embeddings, cluster_ids, sentence_model = load_semantic_backend()
semantic_available = embeddings is not None


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    search_mode = st.radio(
        "Search mode",
        options=["Keyword", "Semantic"] if semantic_available else ["Keyword"],
        index=0,
        help="Semantic mode requires embeddings from notebook 04.",
    )

    query = st.text_input(
        "Query",
        placeholder="e.g. ransomware hospital  OR  CVE-2024",
    )

    urgency_options = ["(any)", "critical", "high", "medium", "low", "unknown"]
    urgency = st.selectbox("Urgency level", urgency_options, index=0)

    col_a, col_b = st.columns(2)
    with col_a:
        min_threat = st.number_input("Min threat score", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
    with col_b:
        max_threat = st.number_input("Max threat score", min_value=0.0, max_value=100.0, value=100.0, step=5.0)

    min_sources = st.number_input("Min source count", min_value=0, value=0, step=1)

    top_k = st.slider("Max results", min_value=5, max_value=100, value=25, step=5)

    run = st.button("Search", type="primary", use_container_width=True)

if not semantic_available:
    st.info(
        "Semantic search is unavailable (embeddings not found). "
        "Run notebook `04_embeddings_similarity.ipynb` to enable it. "
        "Keyword search still works."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_mongo_filter() -> Dict[str, Any]:
    filt: Dict[str, Any] = {}
    if urgency != "(any)":
        filt["urgency_level"] = urgency
    score_clause: Dict[str, float] = {}
    if min_threat > 0:
        score_clause["$gte"] = min_threat
    if max_threat < 100:
        score_clause["$lte"] = max_threat
    if score_clause:
        filt["threat_score"] = score_clause
    if min_sources > 0:
        filt["source_count"] = {"$gte": min_sources}
    return filt


def docs_to_table(docs: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for d in docs:
        rows.append(
            {
                "cluster_id": d.get("cluster_id", ""),
                "title": truncate_text(str(d.get("title") or ""), 70),
                "urgency": d.get("urgency_level") or "—",
                "threat": format_score(d.get("threat_score")),
                "severity": format_score(d.get("severity_score")),
                "sources": d.get("source_count") or 0,
                "score": d.get("_sim_score"),
            }
        )
    df = pd.DataFrame(rows)
    if "score" in df.columns and df["score"].isna().all():
        df = df.drop(columns=["score"])
    return df


def apply_post_filters(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply urgency / threat / source filters in Python (for semantic path)."""
    out = []
    for d in docs:
        if urgency != "(any)" and str(d.get("urgency_level") or "").lower() != urgency:
            continue
        ts = d.get("threat_score")
        if ts is not None:
            try:
                ts_f = float(ts)
                if ts_f < min_threat or ts_f > max_threat:
                    continue
            except (TypeError, ValueError):
                pass
        sc = d.get("source_count") or 0
        try:
            if int(sc) < min_sources:
                continue
        except (TypeError, ValueError):
            pass
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# Search execution
# ---------------------------------------------------------------------------
if run:
    if not query.strip() and search_mode == "Semantic":
        st.warning("Enter a natural-language query for semantic search.")
        st.stop()

    with st.spinner("Searching…"):
        results: List[Dict[str, Any]] = []

        if search_mode == "Keyword":
            mongo_filt = build_mongo_filter()
            if query.strip():
                hits = search_incidents_by_keyword(query.strip(), limit=top_k * 3)
                results = apply_post_filters(hits)[:top_k]
                if not results and mongo_filt:
                    results = find_incidents(
                        filters=mongo_filt,
                        sort=[("threat_score", -1)],
                        limit=top_k,
                    )
            else:
                results = find_incidents(
                    filters=mongo_filt or None,
                    sort=[("threat_score", -1)],
                    limit=top_k,
                )

        else:  # Semantic
            from src.models.predictors import find_similar_incidents

            hits = find_similar_incidents(
                query.strip(),
                top_k=top_k * 2,
                embeddings=embeddings,
                cluster_ids=cluster_ids,
                sentence_model=sentence_model,
            )
            hydrated = []
            for h in hits:
                doc = find_incident_by_id(h["cluster_id"])
                if doc:
                    doc["_sim_score"] = round(h["score"], 4)
                    hydrated.append(doc)
            results = apply_post_filters(hydrated)[:top_k]

    st.success(f"Found **{len(results)}** result(s)")

    if not results:
        st.info("No incidents matched your query / filters.")
    else:
        table = docs_to_table(results)
        st.dataframe(table, use_container_width=True, hide_index=True)

        st.subheader("Result details")
        id_list = [d.get("cluster_id") for d in results if d.get("cluster_id")]
        selected = st.selectbox("Select incident", id_list)
        if selected:
            detail = next((d for d in results if d.get("cluster_id") == selected), None)
            if detail is None:
                detail = find_incident_by_id(selected)
            if detail:
                c1, c2, c3 = st.columns(3)
                c1.metric("Urgency", str(detail.get("urgency_level") or "—"))
                c2.metric("Threat", format_score(detail.get("threat_score")))
                c3.metric("Severity", format_score(detail.get("severity_score")))

                st.markdown(f"**Title:** {detail.get('title') or '—'}")
                st.markdown(f"**Summary:** {detail.get('summary') or '—'}")

                ents = detail.get("entities") or {}
                if isinstance(ents, dict) and ents:
                    with st.expander("Entities"):
                        for k, v in ents.items():
                            st.write(f"**{k}:** {', '.join(str(x) for x in (v or []))}")

                kws = detail.get("keywords") or []
                if kws:
                    st.write("**Keywords:** " + ", ".join(str(k) for k in kws[:30]))

                if detail.get("url"):
                    st.markdown(f"[Source link]({detail['url']})")

else:
    st.info(
        f"Database holds **{count_incidents():,}** incidents. "
        "Set filters in the sidebar and click **Search**."
    )

st.divider()
st.caption(
    f"DB: **{settings.mongodb_db}** · "
    "Semantic search uses `all-MiniLM-L6-v2` embeddings when available."
)