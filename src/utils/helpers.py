"""
General-purpose helper functions.

Pure utilities with no side-effects (except logging setup).
Safe to import from both notebooks and Streamlit.
"""

from __future__ import annotations

import logging
import re
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, Iterable, List, Optional, Union


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging(
    level: str = "INFO",
    *,
    name: Optional[str] = None,
    fmt: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
) -> logging.Logger:
    """
    Configure and return a logger.

    Parameters
    ----------
    level : str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    name : str, optional
        Logger name. Defaults to the root logger when None.
    fmt : str
        Log message format.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers when called multiple times (e.g. in notebooks)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)

    return logger


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------
_DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
]


def parse_date(
    value: Any,
    *,
    default: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Robustly parse a date/datetime value into a datetime object.

    Accepts:
        - datetime instances (returned as-is)
        - ISO-like strings
        - None / empty → returns default

    Parameters
    ----------
    value : any
        Raw date value.
    default : datetime, optional
        Value to return when parsing fails.
    """
    if value is None or value == "":
        return default

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    # Last resort: fromisoformat (Python 3.7+)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Safe getters / type coercion
# ---------------------------------------------------------------------------
def safe_get(
    document: Dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """
    Dictionary get that never raises and treats empty strings as missing.
    """
    if not isinstance(document, dict):
        return default
    value = document.get(key, default)
    if value == "" or value is None:
        return default
    return value


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Convert value to float; return default on failure."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Convert value to int; return default on failure."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))  # handles "3.0" → 3
    except (TypeError, ValueError):
        return default


def ensure_list(value: Any) -> List[Any]:
    """
    Guarantee the return value is a list.

    - None → []
    - single item → [item]
    - list/tuple → list(...)
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def truncate_text(
    text: str,
    max_length: int = 120,
    *,
    suffix: str = "…",
) -> str:
    """
    Truncate a string to max_length characters, appending a suffix if needed.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix


def format_score(
    value: Any,
    *,
    decimals: int = 2,
    default: str = "N/A",
) -> str:
    """
    Format a numeric score for display (e.g. in Streamlit tables).
    """
    if value is None or value == "":
        return default
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
_CLUSTER_ID_RE = re.compile(r"^[a-f0-9]{6,64}$", re.IGNORECASE)


def is_valid_cluster_id(value: Any) -> bool:
    """
    Basic sanity check for a cluster_id (hex-like string of reasonable length).
    """
    if not isinstance(value, str):
        return False
    return bool(_CLUSTER_ID_RE.match(value.strip()))


# ---------------------------------------------------------------------------
# Iteration & timing
# ---------------------------------------------------------------------------
def batch_iterator(
    iterable: Iterable[Any],
    batch_size: int = 500,
) -> Generator[List[Any], None, None]:
    """
    Yield successive batches from an iterable.

    Useful for bulk MongoDB inserts or embedding computation.
    """
    batch: List[Any] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


@contextmanager
def timer(label: str = "Elapsed"):
    """
    Context manager that prints wall-clock time.

    Example
    -------
    >>> with timer("Ingestion"):
    ...     do_heavy_work()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[timer] {label}: {elapsed:.2f}s")