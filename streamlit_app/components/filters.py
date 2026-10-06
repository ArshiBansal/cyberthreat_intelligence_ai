"""
Streamlit sidebar / form filter widgets.

Return plain Python values so pages can build MongoDB queries or
post-filter result lists. No database calls here.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Tuple

import streamlit as st


URGENCY_OPTIONS: List[str] = ["(any)", "critical", "high", "medium", "low", "unknown"]

ENTITY_TYPE_OPTIONS: List[str] = [
    "cve",
    "company",
    "malware",
    "country",
    "sector",
    "mitre_attack",
    "product",
    "threat_actor",
]


def keyword_input(
    label: str = "Query",
    *,
    placeholder: str = "e.g. ransomware hospital",
    key: Optional[str] = None,
) -> str:
    """Text input for keyword / semantic query. Returns stripped string."""
    return st.text_input(label, placeholder=placeholder, key=key).strip()


def urgency_select(
    label: str = "Urgency level",
    *,
    options: Optional[List[str]] = None,
    default_index: int = 0,
    key: Optional[str] = None,
) -> Optional[str]:
    """Urgency dropdown. Returns None when '(any)' is chosen."""
    opts = options or URGENCY_OPTIONS
    choice = st.selectbox(label, opts, index=default_index, key=key)
    if choice == "(any)":
        return None
    return choice


def threat_range(
    *,
    min_default: float = 0.0,
    max_default: float = 100.0,
    step: float = 5.0,
    key_prefix: str = "threat",
) -> Tuple[float, float]:
    """Two number inputs for min / max threat score."""
    col_a, col_b = st.columns(2)
    with col_a:
        lo = st.number_input(
            "Min threat score",
            min_value=0.0,
            max_value=100.0,
            value=min_default,
            step=step,
            key=f"{key_prefix}_min",
        )
    with col_b:
        hi = st.number_input(
            "Max threat score",
            min_value=0.0,
            max_value=100.0,
            value=max_default,
            step=step,
            key=f"{key_prefix}_max",
        )
    return float(lo), float(hi)


def source_count_min(
    label: str = "Min source count",
    *,
    default: int = 0,
    key: Optional[str] = None,
) -> int:
    """Minimum source_count filter."""
    return int(
        st.number_input(label, min_value=0, value=default, step=1, key=key)
    )


def top_k_slider(
    label: str = "Max results",
    *,
    min_value: int = 5,
    max_value: int = 100,
    default: int = 25,
    step: int = 5,
    key: Optional[str] = None,
) -> int:
    """Slider for result limit / top-k."""
    return int(
        st.slider(label, min_value=min_value, max_value=max_value, value=default, step=step, key=key)
    )


def entity_type_select(
    label: str = "Entity type",
    *,
    options: Optional[List[str]] = None,
    default_index: int = 0,
    key: Optional[str] = None,
) -> str:
    """Dropdown of known entity types."""
    opts = options or ENTITY_TYPE_OPTIONS
    return st.selectbox(label, opts, index=default_index, key=key)


def date_range_filter(
    label: str = "Date range",
    *,
    min_date: Optional[date] = None,
    max_date: Optional[date] = None,
    key_prefix: str = "date",
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Optional start / end date inputs."""
    st.caption(label)
    col_a, col_b = st.columns(2)
    with col_a:
        start = st.date_input("From", value=min_date, key=f"{key_prefix}_from")
    with col_b:
        end = st.date_input("To", value=max_date, key=f"{key_prefix}_to")

    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None
    return start_dt, end_dt


def build_score_filter(
    min_threat: float = 0.0,
    max_threat: float = 100.0,
    field: str = "threat_score",
) -> Optional[dict]:
    """Build a MongoDB range filter dict for a score field, or None if full range."""
    clause = {}
    if min_threat > 0:
        clause["$gte"] = min_threat
    if max_threat < 100:
        clause["$lte"] = max_threat
    if not clause:
        return None
    return {field: clause}