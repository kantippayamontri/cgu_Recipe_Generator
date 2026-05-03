"""N-gram suggestion ranking."""

from __future__ import annotations

from n_gram.model import NGramIndex


def _normalize_query(query: str) -> str:
    """Normalize a user query for prefix lookup."""
    return " ".join(query.lower().split())


def suggest_phrases(index: NGramIndex, query: str, limit: int = 15) -> list[str]:
    """Return ranked autocomplete suggestions.

    Args:
        index: Trained n-gram index.
        query: Partial user query.
        limit: Maximum suggestions to return.

    Returns:
        Ranked suggestion strings.
    """
    normalized_query = _normalize_query(query)
    if not normalized_query:
        ranked = sorted(
            index.phrase_counts,
            key=lambda phrase: (-index.phrase_counts[phrase], phrase),
        )
        return ranked[:limit]
    matches = index.prefix_map.get(normalized_query, [])
    if not matches:
        words = normalized_query.split()
        for i in range(len(words) - 1, 0, -1):
            suffix = " ".join(words[-i:])
            if suffix == normalized_query:
                continue
            matches = index.prefix_map.get(suffix, [])
            if matches:
                break
    return matches[:limit]
