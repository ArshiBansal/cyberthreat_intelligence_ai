"""
Create recommended indexes for the cyberthreat_intelligence_ai MongoDB collections.

Safe to run multiple times (idempotent).
Local MongoDB Community Server only.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


def get_mongo_client() -> MongoClient:
    try:
        client = MongoClient(**settings.get_mongo_client_kwargs())
        client.admin.command("ping")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[ERROR] Cannot connect to MongoDB at {settings.MONGO_URI}")
        print(f"        {e}")
        sys.exit(1)


def create_indexes() -> None:
    print("=" * 70)
    print("Creating indexes for cyberthreat_intelligence_ai")
    print("=" * 70)
    print(f"MongoDB URI : {settings.MONGO_URI}")
    print(f"Database    : {settings.MONGO_DB_NAME}")
    print()

    client = get_mongo_client()
    db = client[settings.MONGO_DB_NAME]

    # incidents collection

    incidents = db[settings.COLLECTION_INCIDENTS]
    print(f"→ {settings.COLLECTION_INCIDENTS}")

    # Unique identifier
    incidents.create_index([("cluster_id", ASCENDING)], unique=True, name="idx_cluster_id_unique")
    print("  ✓ cluster_id (unique)")

    # Common filters
    incidents.create_index([("urgency_level", ASCENDING)], name="idx_urgency_level")
    print("  ✓ urgency_level")

    incidents.create_index([("first_reported", DESCENDING)], name="idx_first_reported_desc")
    print("  ✓ first_reported (desc)")

    incidents.create_index([("last_reported", DESCENDING)], name="idx_last_reported_desc")
    print("  ✓ last_reported (desc)")

    incidents.create_index([("threat_score", DESCENDING)], name="idx_threat_score_desc")
    print("  ✓ threat_score (desc)")

    incidents.create_index([("severity_score", DESCENDING)], name="idx_severity_score_desc")
    print("  ✓ severity_score (desc)")

    # Compound index useful for filtered + sorted queries
    incidents.create_index(
        [("urgency_level", ASCENDING), ("first_reported", DESCENDING)],
        name="idx_urgency_first_reported",
    )
    print("  ✓ urgency_level + first_reported")

    # Text index for simple search (optional but useful)
    try:
        incidents.create_index(
            [("title", "text"), ("summary", "text"), ("text", "text")],
            name="idx_text_search",
            default_language="english",
        )
        print("  ✓ text index (title + summary + text)")
    except Exception as e:
        print(f"  ⚠ text index skipped or already exists: {e}")

    # predictions collection

    predictions = db[settings.COLLECTION_PREDICTIONS]
    print(f"\n→ {settings.COLLECTION_PREDICTIONS}")

    predictions.create_index([("timestamp", DESCENDING)], name="idx_timestamp_desc")
    print("  ✓ timestamp (desc)")

    predictions.create_index([("model_version", ASCENDING)], name="idx_model_version")
    print("  ✓ model_version")

    predictions.create_index(
        [("model_version", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_model_version_timestamp",
    )
    print("  ✓ model_version + timestamp")

    # model_metadata collection

    model_meta = db[settings.COLLECTION_MODEL_METADATA]
    print(f"\n→ {settings.COLLECTION_MODEL_METADATA}")

    model_meta.create_index([("version", ASCENDING)], unique=True, name="idx_version_unique")
    print("  ✓ version (unique)")

    model_meta.create_index([("created_at", DESCENDING)], name="idx_created_at_desc")
    print("  ✓ created_at (desc)")

    # analysis_results collection (optional)

    analysis = db[settings.COLLECTION_ANALYSIS_RESULTS]
    print(f"\n→ {settings.COLLECTION_ANALYSIS_RESULTS}")

    analysis.create_index([("analysis_type", ASCENDING)], name="idx_analysis_type")
    print("  ✓ analysis_type")

    analysis.create_index([("created_at", DESCENDING)], name="idx_created_at_desc")
    print("  ✓ created_at (desc)")

    print("\n" + "=" * 70)
    print("INDEX CREATION COMPLETE")
    print("=" * 70)

    # Show current indexes for verification
    print("\nCurrent indexes on incidents:")
    for idx in incidents.list_indexes():
        print(f"  - {idx['name']}: {idx.get('key')}")

    client.close()


if __name__ == "__main__":
    create_indexes()