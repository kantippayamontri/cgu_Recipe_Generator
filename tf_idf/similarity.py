"""TF-IDF recipe similarity search."""
from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics.pairwise import cosine_similarity

from tf_idf.indexer import TfidfIndex


@dataclass(frozen=True)
class SimilarRecipe:
    """Ranked recipe similarity result."""

    recipe_id: int
    score: float


def find_similar_documents(
    index: TfidfIndex, recipe_id: int, limit: int = 5
) -> list[SimilarRecipe]:
    """Find recipes similar to a source recipe.

    Args:
        index: Built TF-IDF index.
        recipe_id: Source recipe identifier.
        limit: Maximum number of results.

    Returns:
        Ranked similar recipes excluding the source.
    """
    if recipe_id not in index.recipe_ids:
        return []

    row_index = index.recipe_ids.index(recipe_id)
    scores = cosine_similarity(index.matrix[row_index], index.matrix).flatten()
    ranked_indices = scores.argsort()[::-1]

    results: list[SimilarRecipe] = []
    for candidate_index in ranked_indices:
        candidate_recipe_id = index.recipe_ids[candidate_index]
        if candidate_recipe_id == recipe_id:
            continue
        score = float(scores[candidate_index])
        if score <= 0:
            continue
        results.append(
            SimilarRecipe(recipe_id=candidate_recipe_id, score=score)
        )
        if len(results) >= limit:
            break

    return results
