"""
Model and artifact loading utilities.

All artifacts live under the project-level `models/` directory.
Both Jupyter notebooks and Streamlit import from this module
so there is a single, consistent way to load trained models.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# src/models/loaders.py → src/ → project root → models/
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent
_DEFAULT_MODELS_DIR = _PROJECT_ROOT / "models"


def get_models_dir(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Return the directory that stores model artifacts.

    Parameters
    ----------
    custom_path : str or Path, optional
        Override the default location.
    """
    if custom_path is not None:
        path = Path(custom_path)
    else:
        path = _DEFAULT_MODELS_DIR

    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Registry of expected model files (documentation + convenience)
# ---------------------------------------------------------------------------
MODEL_REGISTRY: Dict[str, str] = {
    "urgency_classifier": "urgency_classifier.joblib",
    "priority_model": "priority_model.joblib",
    "tfidf_vectorizer": "tfidf_vectorizer.joblib",
    "sentence_embeddings": "embeddings.npy",
    "cluster_ids": "cluster_ids.npy",          # parallel array for embeddings
    "metadata": "metadata.json",
}


# ---------------------------------------------------------------------------
# Core loaders
# ---------------------------------------------------------------------------
def load_joblib_model(
    model_name: str,
    *,
    models_dir: Optional[Union[str, Path]] = None,
) -> Any:
    """
    Load a joblib-serialized model or vectorizer.

    Parameters
    ----------
    model_name : str
        Key from MODEL_REGISTRY (e.g. "urgency_classifier")
        or a direct filename (e.g. "my_model.joblib").
    models_dir : path, optional
        Override the default models directory.

    Returns
    -------
    Any
        The deserialized Python object.

    Raises
    ------
    FileNotFoundError
        If the artifact does not exist.
    """
    directory = get_models_dir(models_dir)

    # Resolve filename
    if model_name in MODEL_REGISTRY:
        filename = MODEL_REGISTRY[model_name]
    else:
        filename = model_name if model_name.endswith((".joblib", ".pkl")) else f"{model_name}.joblib"

    path = directory / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path}\n"
            f"Train the model in a notebook and save it first."
        )

    logger.info("Loading joblib model from %s", path)
    return joblib.load(path)


def load_embeddings(
    *,
    models_dir: Optional[Union[str, Path]] = None,
    embeddings_file: str = "embeddings.npy",
    ids_file: str = "cluster_ids.npy",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load pre-computed sentence embeddings and their corresponding cluster_ids.

    Returns
    -------
    embeddings : np.ndarray
        Shape (n_incidents, embedding_dim)
    cluster_ids : np.ndarray
        Shape (n_incidents,) – parallel array of cluster_id strings
    """
    directory = get_models_dir(models_dir)
    emb_path = directory / embeddings_file
    ids_path = directory / ids_file

    if not emb_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {emb_path}")
    if not ids_path.exists():
        raise FileNotFoundError(f"Cluster IDs file not found: {ids_path}")

    logger.info("Loading embeddings from %s", emb_path)
    embeddings = np.load(emb_path)
    cluster_ids = np.load(ids_path, allow_pickle=True)

    if len(embeddings) != len(cluster_ids):
        raise ValueError(
            f"Mismatch: {len(embeddings)} embeddings vs {len(cluster_ids)} cluster_ids"
        )

    return embeddings, cluster_ids


def load_vectorizer(
    *,
    models_dir: Optional[Union[str, Path]] = None,
) -> Any:
    """Convenience wrapper to load the TF-IDF vectorizer."""
    return load_joblib_model("tfidf_vectorizer", models_dir=models_dir)


def load_model_metadata_file(
    *,
    models_dir: Optional[Union[str, Path]] = None,
    filename: str = "metadata.json",
) -> Dict[str, Any]:
    """
    Load the JSON metadata file that describes available models,
    training dates, metrics, feature sets, etc.
    """
    directory = get_models_dir(models_dir)
    path = directory / filename

    if not path.exists():
        logger.warning("Metadata file not found: %s – returning empty dict", path)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_available_models(
    *,
    models_dir: Optional[Union[str, Path]] = None,
) -> List[str]:
    """
    Return a list of model artifact filenames present on disk.
    """
    directory = get_models_dir(models_dir)
    if not directory.exists():
        return []

    extensions = {".joblib", ".pkl", ".npy", ".json"}
    return sorted(
        p.name for p in directory.iterdir()
        if p.is_file() and p.suffix in extensions
    )