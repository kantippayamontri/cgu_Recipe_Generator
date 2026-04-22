"""Search service: TF-IDF based recipe search with category filtering."""

import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from server.schemas.recipe import (
    IngredientResponse,
    InstructionResponse,
    RecipeResponse,
)
from server.schemas.search import SearchRequest, SearchResponse
from server.services.index_service import IndexData, Recipe, load_index

logger = logging.getLogger(__name__)

# Module-level cache populated on first use
_cached_index: IndexData | None = None
_tfidf_vectorizer: TfidfVectorizer | None = None
_tfidf_matrix: np.ndarray | None = None


def _ensure_index() -> IndexData:
    """Load and cache the index with TF-IDF matrix on first call."""
    global _cached_index, _tfidf_vectorizer, _tfidf_matrix  # noqa: PLW0603

    if _cached_index is not None:
        return _cached_index

    data = load_index()
    _cached_index = data

    # Build TF-IDF vectorizer over combined ingredient + instruction text
    corpus = [
        f"{ing_text} {instr_text}"
        for ing_text, instr_text in zip(
            data.ingredient_strings,
            data.instruction_strings,
        )
    ]
    _tfidf_vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=10_000,
    )
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(corpus)

    return data


def _recipe_to_response(recipe: Recipe) -> RecipeResponse:
    """Convert internal Recipe dataclass to Pydantic response."""
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        description=recipe.title,  # Use title as description since CSV lacks descriptions
        image="",
        categories=recipe.categories,
        cookTimeMinutes=recipe.cook_time_minutes,
        servings=recipe.servings,
        ingredients=[
            IngredientResponse(name=ing["name"], amount=ing["amount"])
            for ing in recipe.ingredients
        ],
        instructions=[
            InstructionResponse(
                step=int(inst["step"]), description=str(inst["description"])
            )
            for inst in recipe.instructions
        ],
    )


async def search_recipes(request: SearchRequest) -> SearchResponse:
    """Search recipes using TF-IDF and filter by categories.

    Args:
        request: Search request with query, filters, and optional limit.

    Returns:
        SearchResponse with matching recipes.
    """
    data = _ensure_index()
    results: list[RecipeResponse] = []

    if request.query.strip():
        # TF-IDF search
        assert _tfidf_vectorizer is not None  # noqa: S101
        assert _tfidf_matrix is not None  # noqa: S101
        query_vector = _tfidf_vectorizer.transform([request.query])
        similarities = cosine_similarity(query_vector, _tfidf_matrix).flatten()

        # Rank by similarity score
        ranked_indices = np.argsort(similarities)[::-1]

        for idx in ranked_indices:
            recipe_id = data.recipe_ids[idx]
            recipe = data.recipes[recipe_id]

            if request.filters and not any(
                cat in request.filters for cat in recipe.categories
            ):
                continue

            results.append(_recipe_to_response(recipe))

            if request.limit and len(results) >= request.limit:
                break
    else:
        # No query: return all recipes, optionally filtered by categories
        for recipe_id, recipe in data.recipes.items():
            if request.filters and not any(
                cat in request.filters for cat in recipe.categories
            ):
                continue

            results.append(_recipe_to_response(recipe))

            if request.limit and len(results) >= request.limit:
                break

    return SearchResponse(
        query=request.query,
        total=len(results),
        recipes=results,
    )


async def get_recipe(recipe_id: int) -> RecipeResponse | None:
    """Fetch a single recipe by ID.

    Args:
        recipe_id: The recipe identifier.

    Returns:
        RecipeResponse if found, else None.
    """
    data = _ensure_index()
    recipe = data.recipes.get(recipe_id)
    if recipe is None:
        return None

    return _recipe_to_response(recipe)


async def get_similar_recipes(recipe_id: int, limit: int = 3) -> list[RecipeResponse]:
    """Find recipes similar to the given recipe using TF-IDF cosine similarity.

    Args:
        recipe_id: Source recipe identifier.
        limit: Maximum number of similar recipes to return.

    Returns:
        List of similar recipes, excluding the source.
    """
    data = _ensure_index()

    if recipe_id not in data.recipes:
        return []

    idx = data.recipe_ids.index(recipe_id)
    assert _tfidf_matrix is not None  # noqa: S101
    source_vector = _tfidf_matrix[idx]
    similarities = cosine_similarity(source_vector, _tfidf_matrix).flatten()

    ranked_indices = np.argsort(similarities)[::-1]

    results: list[RecipeResponse] = []
    for ranked_idx in ranked_indices:
        rid = data.recipe_ids[ranked_idx]
        if rid == recipe_id:
            continue

        results.append(_recipe_to_response(data.recipes[rid]))
        if len(results) >= limit:
            break

    return results


async def get_categories() -> list[str]:
    """Return all unique recipe categories.

    Returns:
        Sorted list of category names.
    """
    data = _ensure_index()
    return data.categories


async def get_suggestions(query: str) -> list[str]:
    """Return autocomplete suggestions based on ingredients and titles.

    Args:
        query: Partial search text from the user.

    Returns:
        List of matching suggestion strings.
    """
    data = _ensure_index()

    query_lower = query.lower().strip()

    # Collect all unique ingredients and titles as suggestion pool
    suggestions: set[str] = set()
    for recipe in data.recipes.values():
        if query_lower and query_lower in recipe.title.lower():
            suggestions.add(recipe.title.lower())
        for ing in recipe.ingredients:
            name = ing.get("name", "").lower()
            if query_lower and query_lower in name:
                suggestions.add(name)

    # If no query, return top ingredients
    if not query_lower:
        for recipe in data.recipes.values():
            for ing in recipe.ingredients:
                name = ing.get("name", "")
                if name:
                    suggestions.add(name.lower())

    return sorted(suggestions)[:15]
