"""
Preprocessing package for Threat Incident Intelligence Platform.

Shared text-cleaning, tokenization and entity-normalization utilities
used by both Jupyter notebooks and the Streamlit application.

Architecture rule:
    - Pure functions only – no side-effects, no MongoDB calls.
    - Notebooks and Streamlit import these helpers; they never duplicate logic.
"""

from src.preprocessing.text import (
    normalize_whitespace,
    normalize_unicode,
    clean_text,
    remove_urls,
    remove_emails,
    simple_tokenize,
    tokenize_and_clean,
    build_tfidf_corpus,
    get_stopwords,
)

from src.preprocessing.entities import (
    normalize_entity_value,
    flatten_entities,
    extract_entity_list,
    count_entities_by_type,
    safe_get_entities,
    normalize_entities_document,
)

__all__ = [
    # Text helpers
    "normalize_whitespace",
    "normalize_unicode",
    "clean_text",
    "remove_urls",
    "remove_emails",
    "simple_tokenize",
    "tokenize_and_clean",
    "build_tfidf_corpus",
    "get_stopwords",
    # Entity helpers
    "normalize_entity_value",
    "flatten_entities",
    "extract_entity_list",
    "count_entities_by_type",
    "safe_get_entities",
    "normalize_entities_document",
]