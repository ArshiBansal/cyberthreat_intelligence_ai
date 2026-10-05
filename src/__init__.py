"""
Threat Incident Intelligence Platform
=====================================

Shared Python package used by both Jupyter notebooks and the Streamlit app.

Architecture rule:
    - Notebooks and Streamlit are completely independent at runtime.
    - Both import utilities from this package.
    - Neither interface executes or imports the other.
"""

__version__ = "1.0.0"
__author__ = "Threat Incident Intelligence Platform Team"

# Convenience re-exports (optional – keeps imports clean)
from src.config import (
    MONGODB_URI,
    MONGODB_DB,
    COLLECTIONS,
    settings,
)

__all__ = [
    "__version__",
    "MONGODB_URI",
    "MONGODB_DB",
    "COLLECTIONS",
    "settings",
]