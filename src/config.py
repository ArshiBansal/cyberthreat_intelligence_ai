"""
Configuration module for Threat Incident Intelligence Platform.

Loads environment variables from .env (via python-dotenv) and exposes
typed settings used by both Jupyter notebooks and the Streamlit app.

Usage:
    from src.config import settings, MONGODB_URI, MONGODB_DB, COLLECTIONS
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Locate and load .env
# ---------------------------------------------------------------------------
# Walk up from this file until we find a .env (project root)
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent  # src/ -> project root

_ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    # Fallback: try loading from current working directory
    load_dotenv()


# ---------------------------------------------------------------------------
# Settings dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment variables."""

    # MongoDB connection
    mongodb_uri: str = field(
        default_factory=lambda: os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    )
    mongodb_db: str = field(
        default_factory=lambda: os.getenv("MONGODB_DB", "threat_intelligence")
    )

    # Collection names
    collection_incidents: str = field(
        default_factory=lambda: os.getenv("MONGODB_COLLECTION_INCIDENTS", "incidents")
    )
    collection_features: str = field(
        default_factory=lambda: os.getenv("MONGODB_COLLECTION_FEATURES", "incident_features")
    )
    collection_predictions: str = field(
        default_factory=lambda: os.getenv(
            "MONGODB_COLLECTION_PREDICTIONS", "predictions"
        )
    )
    collection_models_metadata: str = field(
        default_factory=lambda: os.getenv(
            "MONGODB_COLLECTION_MODELS_METADATA", "models_metadata"
        )
    )

    # Optional Hugging Face token
    hf_token: str | None = field(
        default_factory=lambda: os.getenv("HF_TOKEN") or None
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )

    @property
    def collections(self) -> Dict[str, str]:
        """Return a mapping of logical name → actual collection name."""
        return {
            "incidents": self.collection_incidents,
            "features": self.collection_features,
            "predictions": self.collection_predictions,
            "models_metadata": self.collection_models_metadata,
        }


# ---------------------------------------------------------------------------
# Singleton instance & convenience exports
# ---------------------------------------------------------------------------
settings: Settings = Settings()

# Short aliases (backward-compatible with earlier design)
MONGODB_URI: str = settings.mongodb_uri
MONGODB_DB: str = settings.mongodb_db
COLLECTIONS: Dict[str, str] = settings.collections


def get_settings() -> Settings:
    """Return the global Settings instance (useful for dependency injection)."""
    return settings


def validate_config() -> None:
    """
    Quick sanity check – raises ValueError if critical settings are missing.
    Call this at the start of notebooks or the Streamlit app.
    """
    if not settings.mongodb_uri:
        raise ValueError(
            "MONGODB_URI is not set. "
            "Copy .env.example to .env and fill in the connection string."
        )
    if not settings.mongodb_db:
        raise ValueError("MONGODB_DB is not set.")
    print(f"[config] MongoDB URI loaded (db={settings.mongodb_db})")
    print(f"[config] Collections: {list(settings.collections.values())}")