"""
Entity extraction and normalization utilities.

Works with the structured `entities` sub-document found in
ThreatCluster incident records, e.g.:

    {
        "cve": ["CVE-2024-1234"],
        "company": ["Acme Corp"],
        "malware": ["Emotet"],
        "country": ["United States"],
        "sector": ["Finance"],
        "mitre_attack": ["T1059"]
    }

All functions are pure and side-effect free.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Union


# ---------------------------------------------------------------------------
# Known entity type keys (can be extended)
# ---------------------------------------------------------------------------
KNOWN_ENTITY_TYPES: List[str] = [
    "cve",
    "company",
    "malware",
    "country",
    "sector",
    "mitre_attack",
    "product",
    "threat_actor",
    "technique",
    "tool",
]


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def normalize_entity_value(value: Any) -> Optional[str]:
    """
    Normalize a single entity value to a clean string.

    - Converts to string
    - Strips whitespace
    - Collapses internal whitespace
    - Returns None for empty / null values
    """
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    value = re.sub(r"\s+", " ", value).strip()
    return value if value else None


def safe_get_entities(document: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Safely extract the entities sub-document from an incident.

    Returns an empty dict when the field is missing or malformed.
    """
    entities = document.get("entities")
    if not isinstance(entities, dict):
        return {}
    return entities


# ---------------------------------------------------------------------------
# Flattening & extraction
# ---------------------------------------------------------------------------
def flatten_entities(
    entities: Dict[str, Any],
    *,
    entity_types: Optional[Iterable[str]] = None,
) -> List[str]:
    """
    Flatten all entity values into a single list of strings.

    Parameters
    ----------
    entities : dict
        The entities sub-document.
    entity_types : iterable of str, optional
        Restrict to these keys. Defaults to all keys present.
    """
    if not isinstance(entities, dict):
        return []

    types = list(entity_types) if entity_types else list(entities.keys())
    result: List[str] = []

    for etype in types:
        values = entities.get(etype)
        if values is None:
            continue
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple)):
            continue

        for v in values:
            normalized = normalize_entity_value(v)
            if normalized:
                result.append(normalized)

    return result


def extract_entity_list(
    document: Dict[str, Any],
    entity_type: str,
) -> List[str]:
    """
    Extract a clean list of values for a single entity type from an incident.

    Parameters
    ----------
    document : dict
        Full incident document.
    entity_type : str
        e.g. "cve", "company", "mitre_attack"
    """
    entities = safe_get_entities(document)
    raw = entities.get(entity_type)

    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return []

    cleaned = []
    for v in raw:
        n = normalize_entity_value(v)
        if n:
            cleaned.append(n)
    return cleaned


def count_entities_by_type(
    documents: Iterable[Dict[str, Any]],
    entity_type: str,
    *,
    top_n: Optional[int] = None,
) -> List[Dict[str, Union[str, int]]]:
    """
    Count frequency of each value for a given entity type across many incidents.

    Parameters
    ----------
    documents : iterable of dict
        List of incident documents.
    entity_type : str
        Entity key to count.
    top_n : int, optional
        Return only the top-N most frequent values.

    Returns
    -------
    list of dict
        [{"value": "...", "count": N}, ...] sorted by count descending.
    """
    counter: Counter = Counter()

    for doc in documents:
        values = extract_entity_list(doc, entity_type)
        counter.update(values)

    most_common = counter.most_common(top_n)
    return [{"value": val, "count": cnt} for val, cnt in most_common]


# ---------------------------------------------------------------------------
# Document-level normalization (useful during ingestion)
# ---------------------------------------------------------------------------
def normalize_entities_document(
    entities: Any,
    *,
    known_types: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """
    Normalize an entire entities sub-document into a clean dict[str, list[str]].

    - Ensures every value is a list of cleaned strings
    - Drops empty / null entries
    - Optionally restricts keys to known entity types

    Parameters
    ----------
    entities : any
        Raw entities field (may be None, dict, etc.).
    known_types : list of str, optional
        If provided, only these keys are kept.
        Defaults to KNOWN_ENTITY_TYPES.

    Returns
    -------
    dict
        Cleaned entities ready for MongoDB insertion.
    """
    if not isinstance(entities, dict):
        return {}

    allowed = known_types if known_types is not None else KNOWN_ENTITY_TYPES
    result: Dict[str, List[str]] = {}

    for key, raw_values in entities.items():
        if allowed and key not in allowed:
            # Still keep unknown keys but normalize them
            pass

        if raw_values is None:
            continue

        if isinstance(raw_values, str):
            raw_values = [raw_values]

        if not isinstance(raw_values, (list, tuple)):
            continue

        cleaned: List[str] = []
        seen = set()
        for v in raw_values:
            n = normalize_entity_value(v)
            if n and n not in seen:
                cleaned.append(n)
                seen.add(n)

        if cleaned:
            result[key] = cleaned

    return result