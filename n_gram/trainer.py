"""N-gram suggestion trainer."""
from __future__ import annotations

from collections import Counter, defaultdict

from n_gram.model import NGramDocument, NGramIndex


def _prefixes(phrase: str, min_length: int = 1) -> list[str]:
    """Return all character prefixes for a phrase."""
    return [phrase[:index] for index in range(min_length, len(phrase) + 1)]


def build_n_gram_index(documents: list[NGramDocument]) -> NGramIndex:
    """Build prefix lookup data for autocomplete.

    Args:
        documents: Normalized training phrases.

    Returns:
        Trained n-gram index.
    """
    phrase_counts = Counter(document.text for document in documents)
    prefix_map: dict[str, list[str]] = defaultdict(list)
    for phrase, _count in phrase_counts.items():
        for prefix in _prefixes(phrase):
            prefix_map[prefix].append(phrase)
    for prefix, phrases in prefix_map.items():
        prefix_map[prefix] = sorted(
            phrases, key=lambda phrase: (-phrase_counts[phrase], phrase)
        )
    return NGramIndex(
        documents=documents,
        phrase_counts=dict(phrase_counts),
        prefix_map=dict(prefix_map),
    )
