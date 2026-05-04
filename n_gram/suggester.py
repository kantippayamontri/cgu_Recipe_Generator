"""N-gram suggestion ranking."""

from __future__ import annotations

from nltk.stem import SnowballStemmer

from n_gram.model import NGramIndex

_stemmer = SnowballStemmer("english")


def _normalize_query(query: str) -> str:
    """Normalize a user query for prefix lookup."""
    return " ".join(query.lower().split())


def _stem_all_but_last(query: str) -> str:
    """Stem every token in the query except the last one.

    The last token is left as-is because it is typically a partial word
    still being typed (e.g. "tomatoes pa" → stem "tomatoes"→"tomato",
    leave "pa" so it still prefix-matches "paste").

    Args:
        query: Normalized (lowercased, collapsed-whitespace) query string.

    Returns:
        Query with all-but-last tokens stemmed.
    """
    words = query.split()
    if len(words) == 1:
        return _stemmer.stem(words[0])
    return " ".join(_stemmer.stem(w) for w in words[:-1]) + " " + words[-1]


def _word_boundary_lookup(
    index: NGramIndex,
    complete_words: list[str],
    partial: str,
) -> list[str]:
    """Find phrases containing all complete words and a word starting with partial.

    Complete words are stemmed before lookup because word_index is keyed by
    stemmed forms; this lets "tomatoes" resolve to the same key as "tomato".

    Args:
        index: Trained n-gram index.
        complete_words: Words that must appear in full in the phrase.
        partial: Prefix that at least one word in the phrase must start with.

    Returns:
        Ranked list of matching phrases.
    """
    candidates: set[str] = set(
        index.word_index.get(_stemmer.stem(complete_words[0]), [])
    )
    for word in complete_words[1:]:
        candidates &= set(index.word_index.get(_stemmer.stem(word), []))

    if partial:
        candidates = {
            phrase for phrase in candidates
            if any(w.startswith(partial) for w in phrase.split())
        }

    return sorted(candidates, key=lambda p: (-index.phrase_counts[p], p))


def suggest_phrases(index: NGramIndex, query: str, limit: int = 15) -> list[str]:
    """Return ranked autocomplete suggestions.

    Lookup strategy:
    1. Direct character-prefix match in prefix_map (original phrase prefixes).
    2. Stemmed-query fallback: stem all-but-last token and retry prefix_map.
       Handles "tomatoes" → looks up "tomato" and finds "tomato paste" etc.
    3. For multi-word queries: word-boundary lookup (always merged with Step 1/2).
    4. Trailing-slice fallback when all above are empty.

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

    words = normalized_query.split()

    # Step 1: direct character-prefix match (original phrase prefixes)
    # Step 2: stemmed-query merge — always run so that e.g. "tomatoes" also
    # surfaces "tomato paste" even when prefix_map["tomatoes"] is non-empty.
    prefix_matches: list[str] = list(index.prefix_map.get(normalized_query, []))
    stemmed_q = _stem_all_but_last(normalized_query)
    if stemmed_q != normalized_query:
        seen: set[str] = set(prefix_matches)
        for phrase in index.prefix_map.get(stemmed_q, []):
            if phrase not in seen:
                prefix_matches.append(phrase)
                seen.add(phrase)

    if len(words) >= 2:
        # Step 3: word-boundary lookup — always run and merge for multi-word queries
        boundary_matches = _word_boundary_lookup(index, words[:-1], words[-1])
        seen: set[str] = set(prefix_matches)
        matches: list[str] = list(prefix_matches)
        for phrase in boundary_matches:
            if phrase not in seen:
                matches.append(phrase)
                seen.add(phrase)

        # Step 4: trailing-slice fallback — last resort when all above are empty
        if not matches:
            for i in range(len(words) - 1, 0, -1):
                suffix = " ".join(words[-i:])
                if suffix == normalized_query:
                    continue
                matches = index.prefix_map.get(suffix, [])
                if matches:
                    break
    else:
        matches = prefix_matches

    return matches[:limit]
