"""
Models package for Threat Incident Intelligence Platform.

Shared model loading and prediction utilities used by both
Jupyter notebooks and the Streamlit application.

Architecture rule:
    - Models are trained in notebooks and saved as artifacts.
    - Both notebooks and Streamlit load the same saved artifacts.
    - Neither interface trains models at runtime in production use.
"""

from src.models.loaders import (
    get_models_dir,
    load_joblib_model,
    load_embeddings,
    load_vectorizer,
    load_model_metadata_file,
    list_available_models,
    MODEL_REGISTRY,
)

from src.models.predictors import (
    predict_urgency,
    predict_priority,
    predict_batch_urgency,
    compute_text_embedding,
    find_similar_incidents,
    explain_prediction,
)

__all__ = [
    # Loaders
    "get_models_dir",
    "load_joblib_model",
    "load_embeddings",
    "load_vectorizer",
    "load_model_metadata_file",
    "list_available_models",
    "MODEL_REGISTRY",
    # Predictors
    "predict_urgency",
    "predict_priority",
    "predict_batch_urgency",
    "compute_text_embedding",
    "find_similar_incidents",
    "explain_prediction",
]