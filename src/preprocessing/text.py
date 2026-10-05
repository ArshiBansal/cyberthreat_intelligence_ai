"""
Text cleaning, normalization and tokenization utilities.

Designed for cybersecurity incident titles and summaries.
All functions are pure (no side-effects) so they can be safely
used from both Jupyter notebooks and the Streamlit app.
"""

from __future__ import annotations

import re
import string
import unicodedata
from typing import Iterable, List, Optional, Set

# ---------------------------------------------------------------------------
# Optional NLTK stopwords (graceful fallback if NLTK data is missing)
# ---------------------------------------------------------------------------
try:
    import nltk
    from nltk.corpus import stopwords as nltk_stopwords

    try:
        _ENGLISH_STOPWORDS: Set[str] = set(nltk_stopwords.words("english"))
    except LookupError:
        # NLTK data not downloaded – use a minimal fallback list
        _ENGLISH_STOPWORDS = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must",
            "shall", "can", "need", "this", "that", "these", "those", "it",
            "its", "i", "you", "he", "she", "we", "they", "me", "him", "her",
            "us", "them", "my", "your", "his", "our", "their",
        }
except ImportError:
    _ENGLISH_STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must",
        "shall", "can", "need", "this", "that", "these", "those", "it",
        "its", "i", "you", "he", "she", "we", "they", "me", "him", "her",
        "us", "them", "my", "your", "his", "our", "their",
    }


# ---------------------------------------------------------------------------
# Regex patterns (compiled once)
# ---------------------------------------------------------------------------
_URL_RE = re.compile(
    r"https?://\S+|www\.\S+",
    flags=re.IGNORECASE,
)
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
)
_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s\-_/]")  # keep hyphen, slash, underscore for CVEs etc.


# ---------------------------------------------------------------------------
# Core cleaning functions
# ---------------------------------------------------------------------------
def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into a single space and strip."""
    if not text or not isinstance(text, str):
        return ""
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_unicode(text: str, form: str = "NFKC") -> str:
    """
    Normalize Unicode characters.

    Parameters
    ----------
    form : str
        Unicode normalization form (NFKC recommended for search).
    """
    if not text or not isinstance(text, str):
        return ""
    return unicodedata.normalize(form, text)


def remove_urls(text: str) -> str:
    """Remove HTTP/HTTPS and www URLs."""
    if not text:
        return ""
    return _URL_RE.sub(" ", text)


def remove_emails(text: str) -> str:
    """Remove email addresses."""
    if not text:
        return ""
    return _EMAIL_RE.sub(" ", text)


def clean_text(
    text: str,
    *,
    lower: bool = True,
    remove_url: bool = True,
    remove_email: bool = True,
    remove_punctuation: bool = False,
    keep_cve_style: bool = True,
) -> str:
    """
    Full cleaning pipeline for incident titles / summaries.

    Parameters
    ----------
    text : str
        Raw input text.
    lower : bool
        Convert to lowercase.
    remove_url : bool
        Strip URLs.
    remove_email : bool
        Strip email addresses.
    remove_punctuation : bool
        Remove most punctuation. When keep_cve_style=True, hyphens,
        slashes and underscores are preserved (useful for CVE-2024-1234).
    keep_cve_style : bool
        If True, retain characters commonly found in CVE / MITRE IDs.

    Returns
    -------
    str
        Cleaned text.
    """
    if not text or not isinstance(text, str):
        return ""

    text = normalize_unicode(text)
    text = normalize_whitespace(text)

    if remove_url:
        text = remove_urls(text)
    if remove_email:
        text = remove_emails(text)

    if lower:
        text = text.lower()

    if remove_punctuation:
        if keep_cve_style:
            # Keep alphanumerics + hyphen / underscore / slash
            text = _NON_ALNUM_RE.sub(" ", text)
        else:
            translator = str.maketrans("", "", string.punctuation)
            text = text.translate(translator)

    return normalize_whitespace(text)


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------
def simple_tokenize(text: str) -> List[str]:
    """
    Simple whitespace tokenizer after basic cleaning.
    Returns an empty list for empty / non-string input.
    """
    cleaned = clean_text(text, remove_punctuation=True)
    if not cleaned:
        return []
    return cleaned.split()


def tokenize_and_clean(
    text: str,
    *,
    remove_stopwords: bool = True,
    min_token_length: int = 2,
    extra_stopwords: Optional[Iterable[str]] = None,
) -> List[str]:
    """
    Tokenize, optionally remove stopwords, and filter short tokens.

    Parameters
    ----------
    text : str
        Raw text.
    remove_stopwords : bool
        Drop English stopwords.
    min_token_length : int
        Discard tokens shorter than this length.
    extra_stopwords : iterable of str, optional
        Additional domain-specific stopwords.
    """
    tokens = simple_tokenize(text)

    stop: Set[str] = set()
    if remove_stopwords:
        stop = set(_ENGLISH_STOPWORDS)
    if extra_stopwords:
        stop.update(w.lower() for w in extra_stopwords)

    return [
        t for t in tokens
        if len(t) >= min_token_length and t not in stop
    ]


def get_stopwords() -> Set[str]:
    """Return the current English stopword set (read-only copy)."""
    return set(_ENGLISH_STOPWORDS)


# ---------------------------------------------------------------------------
# Corpus helpers (for TF-IDF pipelines)
# ---------------------------------------------------------------------------
def build_tfidf_corpus(
    texts: Iterable[str],
    *,
    remove_stopwords: bool = True,
    min_token_length: int = 2,
) -> List[str]:
    """
    Convert a list of raw texts into space-joined cleaned token strings
    ready for TfidfVectorizer.

    Example
    -------
    >>> corpus = build_tfidf_corpus(df["summary"].tolist())
    >>> vectorizer = TfidfVectorizer()
    >>> X = vectorizer.fit_transform(corpus)
    """
    return [
        " ".join(
            tokenize_and_clean(
                t,
                remove_stopwords=remove_stopwords,
                min_token_length=min_token_length,
            )
        )
        for t in texts
    ]