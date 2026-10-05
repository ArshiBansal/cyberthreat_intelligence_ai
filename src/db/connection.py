"""
MongoDB connection management.

Single source of truth for creating and sharing the PyMongo client.
Both Jupyter notebooks and Streamlit must import from this module.
"""

from __future__ import annotations

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.config import settings, COLLECTIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton client (lazy initialised)
# ---------------------------------------------------------------------------
_client: Optional[MongoClient] = None


def get_client(force_new: bool = False) -> MongoClient:
    """
    Return a shared MongoClient instance.

    Parameters
    ----------
    force_new : bool
        If True, close any existing client and create a fresh one.

    Returns
    -------
    MongoClient
    """
    global _client

    if force_new and _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None

    if _client is None:
        logger.info("Creating new MongoClient → %s", settings.mongodb_uri)
        _client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,   # fail fast if Mongo is down
            connectTimeoutMS=5000,
            maxPoolSize=50,
            retryWrites=True,
        )
    return _client


def get_db(db_name: Optional[str] = None) -> Database:
    """
    Return the application database.

    Parameters
    ----------
    db_name : str, optional
        Override the default database name from settings.
    """
    client = get_client()
    name = db_name or settings.mongodb_db
    return client[name]


def get_collection(logical_name: str) -> Collection:
    """
    Return a collection by its logical name.

    Parameters
    ----------
    logical_name : str
        One of: "incidents", "features", "predictions", "models_metadata"

    Raises
    ------
    KeyError
        If the logical name is not configured.
    """
    if logical_name not in COLLECTIONS:
        raise KeyError(
            f"Unknown collection '{logical_name}'. "
            f"Valid names: {list(COLLECTIONS.keys())}"
        )
    db = get_db()
    return db[COLLECTIONS[logical_name]]


# ---------------------------------------------------------------------------
# Convenience shortcuts for the four main collections
# ---------------------------------------------------------------------------
def get_incidents_collection() -> Collection:
    return get_collection("incidents")


def get_features_collection() -> Collection:
    return get_collection("features")


def get_predictions_collection() -> Collection:
    return get_collection("predictions")


def get_models_metadata_collection() -> Collection:
    return get_collection("models_metadata")


# ---------------------------------------------------------------------------
# Health-check & cleanup
# ---------------------------------------------------------------------------
def ping_database() -> bool:
    """
    Check whether MongoDB is reachable.

    Returns
    -------
    bool
        True if the server responds to a ping, False otherwise.
    """
    try:
        client = get_client()
        client.admin.command("ping")
        logger.info("MongoDB ping successful")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("MongoDB ping failed: %s", exc)
        return False


def close_connection() -> None:
    """Close the shared MongoClient (call at the end of a notebook or process)."""
    global _client
    if _client is not None:
        try:
            _client.close()
            logger.info("MongoClient closed")
        except Exception as exc:
            logger.warning("Error while closing MongoClient: %s", exc)
        finally:
            _client = None