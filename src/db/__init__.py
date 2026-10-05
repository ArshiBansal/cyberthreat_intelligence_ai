"""
Database package for Threat Incident Intelligence Platform.

Provides a shared MongoDB access layer used by both Jupyter notebooks
and the Streamlit application.

Architecture rule:
    - This package is the ONLY place that creates MongoDB connections.
    - Notebooks and Streamlit import from here; they never create their own clients.
"""

from src.db.connection import (
    get_client,
    get_db,
    get_collection,
    close_connection,
    ping_database,
    get_incidents_collection,
    get_features_collection,
    get_predictions_collection,
    get_models_metadata_collection,
)

from src.db.queries import (
    find_incident_by_id,
    find_incidents,
    count_incidents,
    get_urgency_distribution,
    get_score_statistics,
    get_recent_incidents,
    search_incidents_by_keyword,
    get_entity_values,
    insert_incident,
    insert_many_incidents,
    update_incident,
    upsert_prediction,
    get_model_metadata,
    save_model_metadata,
)

__all__ = [
    # Connection helpers
    "get_client",
    "get_db",
    "get_collection",
    "close_connection",
    "ping_database",
    "get_incidents_collection",
    "get_features_collection",
    "get_predictions_collection",
    "get_models_metadata_collection",
    # Query helpers
    "find_incident_by_id",
    "find_incidents",
    "count_incidents",
    "get_urgency_distribution",
    "get_score_statistics",
    "get_recent_incidents",
    "search_incidents_by_keyword",
    "get_entity_values",
    "insert_incident",
    "insert_many_incidents",
    "update_incident",
    "upsert_prediction",
    "get_model_metadata",
    "save_model_metadata",
]