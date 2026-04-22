"""TF-IDF query search for recipe documents."""
from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics.pairwise import cosine_similarity

from tf_idf.indexer import TfidfIndex


@dataclass(frozen=True)
class SearchResult:
    """Ranked search hit for a TF-IDF query."""

    recipe_id: int
    score: float


def search_documents(
    index: TfidfIndex, query: str, limit: int = 5
) -> list[SearchResult]:
    """Search indexed recipe documents by TF-IDF cosine similarity.

    Args:
        index: Built TF-IDF index.
        query: User query text.
        limit: Maximum number of hits to return.

    Returns:
        Ranked search results.
    """
    if not query.strip():
        return []

    query_vector = index.vectorizer.transform([query])
    scores = cosine_similarity(query_vector, index.matrix).flatten()
    ranked_indices = scores.argsort()[::-1]

    results: list[SearchResult] = []
    for row_index in ranked_indices:
        score = float(scores[row_index])
        if score <= 0:
            continue
        results.append(SearchResult(recipe_id=index.recipe_ids[row_index], score=score))
        if len(results) >= limit:
            break

    return results
