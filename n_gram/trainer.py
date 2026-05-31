"""N-gram suggestion trainer."""
from __future__ import annotations

from collections import Counter, defaultdict

from nltk.stem import SnowballStemmer

from n_gram.model import NGramDocument, NGramIndex

_stemmer = SnowballStemmer("english")


def _stem_phrase(phrase: str) -> str:
    """Return a fully-stemmed version of a phrase (all tokens stemmed).

    Args:
        phrase: Whitespace-separated phrase to stem.

    Returns:
        Phrase with every token replaced by its stemmed form.
    """
    return " ".join(_stemmer.stem(w) for w in phrase.split())


def _prefixes(phrase: str, min_length: int = 1) -> list[str]:
    """Return all character prefixes for a phrase."""
    return [phrase[:index] for index in range(min_length, len(phrase) + 1)]


def build_n_gram_index(documents: list[NGramDocument]) -> NGramIndex:
    """Build prefix lookup data for autocomplete.

    Phrases that reduce to the same stemmed form are deduplicated: only the
    most-frequent original form is kept, so inflected variants like
    "tomatoes" do not appear alongside "tomato" as separate suggestions.

    Args:
        documents: Normalized training phrases.

    Returns:
        Trained n-gram index.
    """
    phrase_counts = Counter(document.text for document in documents)

    # Track which source types each phrase came from (title, ingredient)
    source_map: dict[str, set[str]] = defaultdict(set)
    for document in documents:
        source_map[document.text].add(document.source)

    # Deduplicate: for each unique stemmed form keep the most-frequent original.
    # phrase_counts.most_common() iterates highest-count first, so the first
    # original seen for a stemmed key wins.
    stemmed_seen: dict[str, str] = {}
    surviving: dict[str, int] = {}
    phrase_sources: dict[str, list[str]] = {}
    for phrase, count in phrase_counts.most_common():
        stemmed = _stem_phrase(phrase)
        if stemmed not in stemmed_seen:
            stemmed_seen[stemmed] = phrase
            surviving[phrase] = count
            phrase_sources[phrase] = sorted(source_map.get(phrase, set()))

    # Build prefix_map from original phrase text so partial-word queries
    # (e.g. "frie" → "fried chicken") continue to work without regression.
    prefix_map: dict[str, list[str]] = defaultdict(list)
    for phrase in surviving:
        for prefix in _prefixes(phrase):
            prefix_map[prefix].append(phrase)
    for prefix in prefix_map:
        prefix_map[prefix] = sorted(
            prefix_map[prefix], key=lambda p: (-surviving[p], p)
        )

    # Build word_index with STEMMED word keys so that a query containing
    # "tomatoes" (stemmed → "tomato") correctly resolves to phrases that
    # contain the word "tomato".
    word_index: dict[str, list[str]] = defaultdict(list)
    for phrase in surviving:
        for word in phrase.split():
            word_index[_stemmer.stem(word)].append(phrase)
    for word in word_index:
        word_index[word] = sorted(
            word_index[word], key=lambda p: (-surviving[p], p)
        )

    return NGramIndex(
        documents=documents,
        phrase_counts=dict(surviving),
        prefix_map=dict(prefix_map),
        word_index=dict(word_index),
        phrase_sources=phrase_sources,
    )
