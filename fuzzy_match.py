"""
Fuzzy matching utility for resolving LLM-extracted field values
against known config keys.

Handles cases like:
  - "Beverly Hill" → "Beverly Hills"
  - "residential" → "Residential"
  - "Single Family" → "Single Family Residence"
"""

from thefuzz import process


# Minimum similarity score (0-100) to accept a fuzzy match.
# Below this threshold, the lookup returns None instead of a bad match.
FUZZY_THRESHOLD = 70


def fuzzy_lookup(query: str, mapping: dict[str, int], threshold: int = FUZZY_THRESHOLD) -> int | None:
    """
    Resolve a possibly-inexact string to a code using fuzzy matching.

    Args:
        query: The value extracted by the LLM (may be inexact).
        mapping: A dict of { label: code } from field_codes.py.
        threshold: Minimum similarity score to accept (0-100).

    Returns:
        The matched code (int) if a good match is found, else None.
    """
    if not mapping or not query:
        return None

    # 1. Try exact match first (case-insensitive)
    query_lower = query.strip().lower()
    for key, code in mapping.items():
        if key.strip().lower() == query_lower:
            return code

    # 2. Fall back to fuzzy match
    keys = list(mapping.keys())
    result = process.extractOne(query, keys, score_cutoff=threshold)

    if result is None:
        return None

    best_match, score, *_ = result
    return mapping[best_match]


def fuzzy_match_name(query: str, choices: list[str], threshold: int = FUZZY_THRESHOLD) -> str | None:
    """
    Resolve a possibly-inexact string against a flat list of valid names.

    Useful for fields like City where there's no numeric code — we just
    need to correct the spelling to match a known value.

    Args:
        query: The value extracted by the LLM (may be inexact).
        choices: A list of valid names (e.g. city names).
        threshold: Minimum similarity score to accept (0-100).

    Returns:
        The best matching name (str) if found, else the original query unchanged.
    """
    if not choices or not query:
        return query

    # 1. Try exact match first (case-insensitive)
    query_lower = query.strip().lower()
    for name in choices:
        if name.strip().lower() == query_lower:
            return name

    # 2. Fall back to fuzzy match
    result = process.extractOne(query, choices, score_cutoff=threshold)

    if result is None:
        # No good match — return original so the API still gets something
        return query

    best_match, score, *_ = result
    return best_match


def fuzzy_lookup_many(queries: list[str], mapping: dict[str, int], threshold: int = FUZZY_THRESHOLD) -> list[int]:
    """
    Resolve a list of possibly-inexact strings to codes.
    Silently skips any query that doesn't meet the threshold.

    Args:
        queries: List of values extracted by the LLM.
        mapping: A dict of { label: code } from field_codes.py.
        threshold: Minimum similarity score to accept (0-100).

    Returns:
        List of matched codes (may be shorter than input if some didn't match).
    """
    codes = []
    for q in queries:
        code = fuzzy_lookup(q, mapping, threshold)
        if code is not None:
            codes.append(code)
    return codes
