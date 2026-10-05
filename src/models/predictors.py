"""
Prediction helpers for Threat Incident Intelligence Platform.

Provides high-level functions for:
    - Urgency classification
    - Priority classification
    - Text embedding + semantic similarity search

All functions load artifacts on demand (or accept pre-loaded objects)
so they work identically from notebooks and Streamlit.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from src.models.loaders import (
    load_joblib_model,
    load_embeddings,
    load_vectorizer,
)
from src.preprocessing.text import clean_text, build_tfidf_corpus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Urgency classification
# ---------------------------------------------------------------------------
def predict_urgency(
    text: str,
    *,
    model: Any = None,
    vectorizer: Any = None,
    return_proba: bool = False,
) -> Union[str, Tuple[str, Dict[str, float]]]:
    """
    Predict urgency level from incident title + summary text.

    Parameters
    ----------
    text : str
        Combined title and/or summary.
    model : optional
        Pre-loaded classifier. If None, loads "urgency_classifier".
    vectorizer : optional
        Pre-loaded TF-IDF vectorizer. If None, loads "tfidf_vectorizer".
    return_proba : bool
        If True, also return class probabilities.

    Returns
    -------
    str or (str, dict)
        Predicted urgency label, optionally with probability dict.
    """
    if model is None:
        model = load_joblib_model("urgency_classifier")
    if vectorizer is None:
        vectorizer = load_vectorizer()

    cleaned = clean_text(text)
    X = vectorizer.transform([cleaned])

    label = model.predict(X)[0]

    if not return_proba:
        return str(label)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = model.classes_
        proba_dict = {str(c): float(p) for c, p in zip(classes, proba)}
    else:
        proba_dict = {str(label): 1.0}

    return str(label), proba_dict


def predict_batch_urgency(
    texts: List[str],
    *,
    model: Any = None,
    vectorizer: Any = None,
) -> List[str]:
    """
    Predict urgency for a batch of texts (more efficient than looping).
    """
    if model is None:
        model = load_joblib_model("urgency_classifier")
    if vectorizer is None:
        vectorizer = load_vectorizer()

    cleaned = [clean_text(t) for t in texts]
    X = vectorizer.transform(cleaned)
    predictions = model.predict(X)
    return [str(p) for p in predictions]


# ---------------------------------------------------------------------------
# Priority classification
# ---------------------------------------------------------------------------
def predict_priority(
    features: Dict[str, Any],
    *,
    model: Any = None,
    return_proba: bool = False,
) -> Union[str, Tuple[str, Dict[str, float]]]:
    """
    Predict a priority class (Low / Medium / High / Critical)
    from structured features + optional text signals.

    Parameters
    ----------
    features : dict
        Feature dictionary. Expected keys depend on how the model
        was trained (e.g. threat_score, severity_score, article_count, …).
        The function expects a flat dict that can be turned into a
        single-row DataFrame or array matching the training schema.
    model : optional
        Pre-loaded priority model.
    return_proba : bool
        If True, also return class probabilities.

    Notes
    -----
    This is a thin wrapper. In practice you will adapt the feature
    vector construction to match exactly what was used during training
    (see the ML training notebook).
    """
    if model is None:
        model = load_joblib_model("priority_model")

    # Minimal safe conversion – users should replace with their exact schema
    try:
        import pandas as pd
        X = pd.DataFrame([features])
    except Exception:
        # Fallback: assume the model accepts a list of values in sorted key order
        X = [list(features.values())]

    label = model.predict(X)[0]

    if not return_proba:
        return str(label)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = model.classes_
        proba_dict = {str(c): float(p) for c, p in zip(classes, proba)}
    else:
        proba_dict = {str(label): 1.0}

    return str(label), proba_dict


# ---------------------------------------------------------------------------
# Semantic similarity
# ---------------------------------------------------------------------------
def compute_text_embedding(
    text: str,
    *,
    model_name: str = "all-MiniLM-L6-v2",
    sentence_model: Any = None,
) -> np.ndarray:
    """
    Compute a sentence embedding for the given text.

    Parameters
    ----------
    text : str
        Input text (title + summary recommended).
    model_name : str
        Hugging Face sentence-transformers model name
        (only used when sentence_model is None).
    sentence_model : optional
        Pre-loaded SentenceTransformer instance.
    """
    if sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            sentence_model = SentenceTransformer(model_name)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for embedding computation. "
                "Install it with: pip install sentence-transformers"
            ) from exc

    cleaned = clean_text(text, remove_punctuation=False)
    embedding = sentence_model.encode([cleaned], convert_to_numpy=True)[0]
    return embedding


def find_similar_incidents(
    query_text: str,
    *,
    top_k: int = 5,
    embeddings: Optional[np.ndarray] = None,
    cluster_ids: Optional[np.ndarray] = None,
    sentence_model: Any = None,
    models_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most similar incidents to a natural-language query.

    Parameters
    ----------
    query_text : str
        Free-text security query.
    top_k : int
        Number of results to return.
    embeddings : np.ndarray, optional
        Pre-loaded embedding matrix. If None, loads from disk.
    cluster_ids : np.ndarray, optional
        Parallel array of cluster_ids.
    sentence_model : optional
        Pre-loaded SentenceTransformer.
    models_dir : str, optional
        Override models directory.

    Returns
    -------
    list of dict
        [{"cluster_id": "...", "score": 0.87}, ...] sorted by similarity desc.
    """
    if embeddings is None or cluster_ids is None:
        embeddings, cluster_ids = load_embeddings(models_dir=models_dir)

    query_vec = compute_text_embedding(query_text, sentence_model=sentence_model)

    # Cosine similarity
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    emb_norms = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10)
    scores = emb_norms @ query_norm

    # Top-k indices
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "cluster_id": str(cluster_ids[idx]),
            "score": float(scores[idx]),
        })
    return results


# ---------------------------------------------------------------------------
# Lightweight explainability helper
# ---------------------------------------------------------------------------
def explain_prediction(
    text: str,
    *,
    model: Any = None,
    vectorizer: Any = None,
    top_n_features: int = 10,
) -> Dict[str, Any]:
    """
    Return a simple explanation for an urgency prediction
    based on the highest-weighted TF-IDF features.

    Works best with linear models (LogisticRegression, LinearSVC).
    For tree-based models it falls back to feature importances if available.
    """
    if model is None:
        model = load_joblib_model("urgency_classifier")
    if vectorizer is None:
        vectorizer = load_vectorizer()

    cleaned = clean_text(text)
    X = vectorizer.transform([cleaned])
    label = str(model.predict(X)[0])

    feature_names = np.array(vectorizer.get_feature_names_out())
    explanation: Dict[str, Any] = {
        "predicted_label": label,
        "top_features": [],
    }

    # Linear models
    if hasattr(model, "coef_"):
        classes = list(model.classes_)
        try:
            class_idx = classes.index(label)
        except ValueError:
            class_idx = 0

        coefs = model.coef_[class_idx] if model.coef_.ndim > 1 else model.coef_
        row = X.toarray()[0]
        present_idx = np.where(row > 0)[0]
        if len(present_idx) == 0:
            return explanation

        weighted = coefs[present_idx] * row[present_idx]
        top_local = present_idx[np.argsort(np.abs(weighted))[::-1][:top_n_features]]

        explanation["top_features"] = [
            {
                "feature": feature_names[i],
                "tfidf": float(row[i]),
                "coefficient": float(coefs[i]),
                "contribution": float(weighted[np.where(present_idx == i)[0][0]]),
            }
            for i in top_local
        ]
        return explanation

    # Tree-based fallback
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        row = X.toarray()[0]
        present_idx = np.where(row > 0)[0]
        scored = present_idx[np.argsort(importances[present_idx])[::-1][:top_n_features]]
        explanation["top_features"] = [
            {
                "feature": feature_names[i],
                "tfidf": float(row[i]),
                "importance": float(importances[i]),
            }
            for i in scored
        ]

    return explanation