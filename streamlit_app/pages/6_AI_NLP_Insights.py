"""
AI / NLP Insights — urgency & priority predictions, semantic similarity.

Loads model artifacts from models/ when available.
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
    get_recent_incidents,
    count_incidents,
)
from src.utils import truncate_text, format_score, safe_float

st.set_page_config(
    page_title="AI Insights — Threat Intelligence",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AI / NLP Insights")
st.caption("Urgency & priority prediction · semantic similar-incident search")


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


@st.cache_resource(show_spinner="Loading ML artifacts…")
def load_ml_stack():
    """Return dict with vectorizer, urgency_model, priority_model, embeddings, etc."""
    out: Dict[str, Any] = {
        "vectorizer": None,
        "urgency_model": None,
        "priority_model": None,
        "priority_meta": None,
        "embeddings": None,
        "cluster_ids": None,
        "sentence_model": None,
        "errors": [],
    }
    try:
        from src.models.loaders import load_vectorizer, load_joblib_model, load_embeddings
        import joblib
        from src.models.loaders import get_models_dir

        try:
            out["vectorizer"] = load_vectorizer()
        except Exception as e:
            out["errors"].append(f"vectorizer: {e}")

        try:
            out["urgency_model"] = load_joblib_model("urgency_classifier")
        except Exception as e:
            out["errors"].append(f"urgency: {e}")

        try:
            out["priority_model"] = load_joblib_model("priority_model")
            out["priority_meta"] = joblib.load(get_models_dir() / "priority_meta.joblib")
        except Exception as e:
            out["errors"].append(f"priority: {e}")

        try:
            emb, ids = load_embeddings()
            out["embeddings"] = emb
            out["cluster_ids"] = ids
            from sentence_transformers import SentenceTransformer
            out["sentence_model"] = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            out["errors"].append(f"embeddings: {e}")

    except Exception as e:
        out["errors"].append(str(e))

    return out


ml = load_ml_stack()

if ml["errors"]:
    with st.expander("Model load notes (some features may be unavailable)"):
        for e in ml["errors"]:
            st.caption(f"• {e}")
        st.caption("Run notebooks 03–05 to generate missing artifacts.")


tab_pred, tab_sim, tab_batch = st.tabs(
    ["Predict urgency / priority", "Similar incidents", "Batch recent"]
)


with tab_pred:
    st.subheader("Predict from free text + optional scores")

    text = st.text_area(
        "Incident title / summary",
        height=120,
        placeholder="Ransomware encrypts hospital EHR systems and demands bitcoin ransom…",
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    threat = c1.number_input("Threat score", 0.0, 100.0, 50.0, 1.0)
    severity = c2.number_input("Severity score", 0.0, 100.0, 50.0, 1.0)
    credibility = c3.number_input("Credibility", 0.0, 1.0, 0.5, 0.05)
    source_count = c4.number_input("Source count", 0, 100, 2, 1)
    article_count = c5.number_input("Article count", 0, 500, 3, 1)

    if st.button("Run prediction", type="primary"):
        if not text.strip():
            st.warning("Enter some text first.")
        else:
            if ml["urgency_model"] is not None and ml["vectorizer"] is not None:
                from src.models.predictors import predict_urgency

                label, proba = predict_urgency(
                    text,
                    model=ml["urgency_model"],
                    vectorizer=ml["vectorizer"],
                    return_proba=True,
                )
                st.markdown(f"### Predicted urgency: **{label}**")
                if isinstance(proba, dict):
                    proba_df = pd.DataFrame(
                        [{"class": k, "probability": v} for k, v in sorted(proba.items(), key=lambda x: -x[1])]
                    )
                    st.bar_chart(proba_df.set_index("class"))
            else:
                st.info("Urgency model not loaded.")

            if ml["priority_model"] is not None:
                from src.models.predictors import predict_priority

                cols = (ml["priority_meta"] or {}).get(
                    "feature_columns",
                    ["threat_score", "severity_score", "credibility_score", "source_count", "article_count"],
                )
                feat = {
                    "threat_score": threat,
                    "severity_score": severity,
                    "credibility_score": credibility,
                    "source_count": source_count,
                    "article_count": article_count,
                }
                feat = {c: feat.get(c, 0) for c in cols}
                prio, pprio = predict_priority(feat, model=ml["priority_model"], return_proba=True)
                st.markdown(f"### Predicted priority: **{prio}**")
                if isinstance(pprio, dict):
                    st.write({k: round(v, 3) for k, v in pprio.items()})
            else:
                st.info("Priority model not loaded.")

            st.caption("Predictions are model outputs — not verified security facts.")


with tab_sim:
    st.subheader("Find semantically similar incidents")

    if ml["embeddings"] is None:
        st.warning(
            "Embeddings not available. Run notebook `04_embeddings_similarity.ipynb` first."
        )
    else:
        q = st.text_input(
            "Natural-language query",
            placeholder="zero-day VPN appliance exploitation",
        )
        top_k = st.slider("Top K", 3, 20, 8)

        if st.button("Search similar", type="primary"):
            if not q.strip():
                st.warning("Enter a query.")
            else:
                from src.models.predictors import find_similar_incidents

                hits = find_similar_incidents(
                    q.strip(),
                    top_k=top_k,
                    embeddings=ml["embeddings"],
                    cluster_ids=ml["cluster_ids"],
                    sentence_model=ml["sentence_model"],
                )
                rows = []
                for h in hits:
                    doc = find_incident_by_id(h["cluster_id"])
                    rows.append(
                        {
                            "score": round(h["score"], 4),
                            "cluster_id": h["cluster_id"],
                            "title": truncate_text(str((doc or {}).get("title") or ""), 70),
                            "urgency": (doc or {}).get("urgency_level") or "—",
                            "threat": format_score((doc or {}).get("threat_score")),
                        }
                    )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                if rows:
                    pick = st.selectbox("Inspect", [r["cluster_id"] for r in rows])
                    detail = find_incident_by_id(pick)
                    if detail:
                        st.markdown(f"**{detail.get('title')}**")
                        st.write(detail.get("summary") or "")


with tab_batch:
    st.subheader("Predict urgency for recent incidents")

    n = st.slider("How many recent incidents", 5, 50, 15)

    if st.button("Score recent", type="primary"):
        if ml["urgency_model"] is None or ml["vectorizer"] is None:
            st.warning("Urgency model / vectorizer not loaded.")
        else:
            from src.models.predictors import predict_urgency

            recent = get_recent_incidents(n=n)
            rows = []
            for doc in recent:
                text = " ".join(
                    filter(
                        None,
                        [
                            str(doc.get("title") or ""),
                            str(doc.get("summary") or ""),
                        ],
                    )
                )
                try:
                    pred = predict_urgency(
                        text,
                        model=ml["urgency_model"],
                        vectorizer=ml["vectorizer"],
                        return_proba=False,
                    )
                except Exception:
                    pred = "?"
                rows.append(
                    {
                        "cluster_id": doc.get("cluster_id", ""),
                        "title": truncate_text(str(doc.get("title") or ""), 55),
                        "actual_urgency": doc.get("urgency_level") or "—",
                        "predicted": pred,
                        "threat": format_score(doc.get("threat_score")),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.caption(
    f"DB: **{settings.mongodb_db}** · "
    f"Incidents: **{count_incidents():,}** · "
    "Defensive research only — do not treat predictions as verified facts."
)