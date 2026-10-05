"""
Reusable MongoDB query helpers for Threat Incident Intelligence Platform.

All functions accept optional collection overrides so they can be used
in both notebooks and the Streamlit app without side-effects.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pymongo.collection import Collection
from pymongo.results import InsertManyResult, InsertOneResult, UpdateResult

from src.db.connection import (
    get_incidents_collection,
    get_features_collection,
    get_predictions_collection,
    get_models_metadata_collection,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read helpers – Incidents
# ---------------------------------------------------------------------------
def find_incident_by_id(
    cluster_id: str,
    collection: Optional[Collection] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return a single incident document by its cluster_id.

    Parameters
    ----------
    cluster_id : str
        Unique incident identifier.
    collection : Collection, optional
        Override the default incidents collection.
    """
    coll = collection or get_incidents_collection()
    return coll.find_one({"cluster_id": cluster_id})


def find_incidents(
    filters: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, int]] = None,
    sort: Optional[List[tuple]] = None,
    limit: int = 0,
    skip: int = 0,
    collection: Optional[Collection] = None,
) -> List[Dict[str, Any]]:
    """
    Flexible incident finder.

    Parameters
    ----------
    filters : dict, optional
        MongoDB query filter (e.g. {"urgency_level": "high"}).
    projection : dict, optional
        Fields to include/exclude.
    sort : list of tuples, optional
        e.g. [("threat_score", -1), ("first_reported", -1)]
    limit : int
        Maximum number of documents (0 = no limit).
    skip : int
        Number of documents to skip (for pagination).
    collection : Collection, optional
        Override the default incidents collection.
    """
    coll = collection or get_incidents_collection()
    cursor = coll.find(filters or {}, projection)

    if sort:
        cursor = cursor.sort(sort)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)

    return list(cursor)


def count_incidents(
    filters: Optional[Dict[str, Any]] = None,
    collection: Optional[Collection] = None,
) -> int:
    """Return the number of incidents matching the given filters."""
    coll = collection or get_incidents_collection()
    return coll.count_documents(filters or {})


def get_recent_incidents(
    n: int = 20,
    collection: Optional[Collection] = None,
) -> List[Dict[str, Any]]:
    """Return the n most recently reported incidents."""
    return find_incidents(
        sort=[("last_reported", -1)],
        limit=n,
        collection=collection,
    )


def search_incidents_by_keyword(
    keyword: str,
    fields: Optional[List[str]] = None,
    limit: int = 50,
    collection: Optional[Collection] = None,
) -> List[Dict[str, Any]]:
    """
    Simple case-insensitive keyword search across text fields.

    Parameters
    ----------
    keyword : str
        Search term.
    fields : list of str, optional
        Fields to search (default: title, summary, keywords).
    limit : int
        Maximum results.
    """
    if fields is None:
        fields = ["title", "summary", "keywords"]

    regex = {"$regex": keyword, "$options": "i"}
    or_clauses = [{field: regex} for field in fields]

    return find_incidents(
        filters={"$or": or_clauses},
        limit=limit,
        collection=collection,
    )


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------
def get_urgency_distribution(
    collection: Optional[Collection] = None,
) -> Dict[str, int]:
    """
    Return a mapping of urgency_level → count.
    """
    coll = collection or get_incidents_collection()
    pipeline = [
        {"$group": {"_id": "$urgency_level", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = list(coll.aggregate(pipeline))
    return {doc["_id"] or "unknown": doc["count"] for doc in results}


def get_score_statistics(
    score_field: str = "threat_score",
    collection: Optional[Collection] = None,
) -> Dict[str, float]:
    """
    Compute basic statistics for a numeric score field.

    Parameters
    ----------
    score_field : str
        One of: threat_score, severity_score, credibility_score, article_count, etc.
    """
    coll = collection or get_incidents_collection()
    pipeline = [
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "avg": {"$avg": f"${score_field}"},
                "min": {"$min": f"${score_field}"},
                "max": {"$max": f"${score_field}"},
                "std": {"$stdDevPop": f"${score_field}"},
            }
        }
    ]
    results = list(coll.aggregate(pipeline))
    if not results:
        return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}

    doc = results[0]
    return {
        "count": doc.get("count", 0),
        "avg": round(doc.get("avg") or 0.0, 4),
        "min": doc.get("min") or 0.0,
        "max": doc.get("max") or 0.0,
        "std": round(doc.get("std") or 0.0, 4),
    }


def get_entity_values(
    entity_type: str,
    limit: int = 50,
    collection: Optional[Collection] = None,
) -> List[Dict[str, Any]]:
    """
    Return the most frequent values for a given entity type.

    Parameters
    ----------
    entity_type : str
        Key inside the entities sub-document, e.g. "cve", "company",
        "malware", "country", "sector", "mitre_attack".
    limit : int
        Maximum number of distinct values to return.
    """
    coll = collection or get_incidents_collection()
    pipeline = [
        {"$unwind": f"$entities.{entity_type}"},
        {"$group": {"_id": f"$entities.{entity_type}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    results = list(coll.aggregate(pipeline))
    return [{"value": doc["_id"], "count": doc["count"]} for doc in results]


# ---------------------------------------------------------------------------
# Write helpers – Incidents
# ---------------------------------------------------------------------------
def insert_incident(
    document: Dict[str, Any],
    collection: Optional[Collection] = None,
) -> InsertOneResult:
    """Insert a single incident document."""
    coll = collection or get_incidents_collection()
    return coll.insert_one(document)


def insert_many_incidents(
    documents: List[Dict[str, Any]],
    ordered: bool = False,
    collection: Optional[Collection] = None,
) -> InsertManyResult:
    """
    Bulk-insert multiple incident documents.

    Parameters
    ----------
    ordered : bool
        If False (default), continue inserting even if some documents fail.
    """
    coll = collection or get_incidents_collection()
    return coll.insert_many(documents, ordered=ordered)


def update_incident(
    cluster_id: str,
    update_fields: Dict[str, Any],
    collection: Optional[Collection] = None,
) -> UpdateResult:
    """
    Update fields of an existing incident.

    Parameters
    ----------
    cluster_id : str
        Document key.
    update_fields : dict
        Fields to set (will be wrapped in $set).
    """
    coll = collection or get_incidents_collection()
    return coll.update_one(
        {"cluster_id": cluster_id},
        {"$set": update_fields},
    )


# ---------------------------------------------------------------------------
# Predictions & Model metadata
# ---------------------------------------------------------------------------
def upsert_prediction(
    cluster_id: str,
    prediction: Dict[str, Any],
    collection: Optional[Collection] = None,
) -> UpdateResult:
    """
    Insert or update a prediction document for a given cluster_id.

    The prediction dict is stored under the key "prediction" and a
    timestamp is automatically added.
    """
    coll = collection or get_predictions_collection()
    payload = {
        "cluster_id": cluster_id,
        "prediction": prediction,
        "updated_at": datetime.utcnow(),
    }
    return coll.update_one(
        {"cluster_id": cluster_id},
        {"$set": payload},
        upsert=True,
    )


def get_model_metadata(
    model_name: str,
    collection: Optional[Collection] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a named model."""
    coll = collection or get_models_metadata_collection()
    return coll.find_one({"model_name": model_name})


def save_model_metadata(
    model_name: str,
    metadata: Dict[str, Any],
    collection: Optional[Collection] = None,
) -> UpdateResult:
    """
    Persist model metadata (version, metrics, training date, etc.).

    Parameters
    ----------
    model_name : str
        Unique model identifier.
    metadata : dict
        Arbitrary metadata; a timestamp is added automatically.
    """
    coll = collection or get_models_metadata_collection()
    payload = {
        "model_name": model_name,
        **metadata,
        "saved_at": datetime.utcnow(),
    }
    return coll.update_one(
        {"model_name": model_name},
        {"$set": payload},
        upsert=True,
    )