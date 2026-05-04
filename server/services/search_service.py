"""Search service: TF-IDF based recipe search with category filtering."""

import logging
import random
import re

import numpy as np
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_stemmer = SnowballStemmer("english")


def _stem_tokenize(text: str) -> list[str]:
    """Tokenize and stem text for TF-IDF vectorization.

    Args:
        text: Raw text to tokenize.

    Returns:
        List of stemmed tokens.
    """
    tokens = re.findall(r"[a-z]+", text.lower())
    return [_stemmer.stem(t) for t in tokens]

from n_gram.loader import load_suggestion_documents
from n_gram.model import NGramIndex
from n_gram.suggester import suggest_phrases
from n_gram.trainer import build_n_gram_index
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
_ngram_index: NGramIndex | None = None


def _ensure_index() -> IndexData:
    """Load and cache the index with TF-IDF matrix and n-gram index on first call."""
    global _cached_index, _tfidf_vectorizer, _tfidf_matrix, _ngram_index  # noqa: PLW0603

    if _cached_index is not None:
        return _cached_index

    data = load_index()
    _cached_index = data

    # Build TF-IDF vectorizer — title repeated 3x to boost title match weight
    corpus = [
        (f"{data.recipes[rid].title} " * 3) + ing_text
        for rid, ing_text in zip(data.recipe_ids, data.ingredient_strings)
    ]
    _tfidf_vectorizer = TfidfVectorizer(
        tokenizer=_stem_tokenize,
        token_pattern=None,  # required when tokenizer= is set
        stop_words="english",
        ngram_range=(1, 2),  # bigrams to capture simple phrase patterns
        max_features=10_000,
    )
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(
        corpus
    )  # train bigram TF-IDF vectorizer on recipe data

    # Build n-gram prefix index for autocomplete
    suggestion_docs = load_suggestion_documents(data)
    _ngram_index = build_n_gram_index(suggestion_docs)

    return data


def _recipe_to_response(recipe: Recipe) -> RecipeResponse:
    """Convert internal Recipe dataclass to Pydantic response."""
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        description=recipe.title,  # Use title as description since CSV lacks descriptions
        image=recipe.image,
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
    effective_limit = request.limit or 50

    if request.query.strip():
        # TF-IDF search — stem query to match stemmed corpus vocabulary
        assert _tfidf_vectorizer is not None  # noqa: S101
        assert _tfidf_matrix is not None  # noqa: S101
        stemmed_query = " ".join(_stem_tokenize(request.query))
        query_vector = _tfidf_vectorizer.transform([stemmed_query])
        similarities = cosine_similarity(query_vector, _tfidf_matrix).flatten()

        # Rank by similarity score
        ranked_indices = np.argsort(similarities)[::-1]

        for idx in ranked_indices:
            if similarities[idx] <= 0.0:
                break  # sorted descending — all remaining are also 0

            recipe_id = data.recipe_ids[idx]
            recipe = data.recipes[recipe_id]

            if request.filters and not any(
                cat in request.filters for cat in recipe.categories
            ):
                continue

            results.append(_recipe_to_response(recipe))

            if len(results) >= effective_limit:
                break
    else:
        # No query: shuffle for variety on landing page
        items = list(data.recipes.items())
        random.shuffle(items)
        for recipe_id, recipe in items:
            if request.filters and not any(
                cat in request.filters for cat in recipe.categories
            ):
                continue

            results.append(_recipe_to_response(recipe))

            if len(results) >= effective_limit:
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


async def get_categories() -> list[tuple[str, int]]:
    """Return all unique recipe categories sorted by popularity (recipe count desc).

    Returns:
        List of (category_name, recipe_count) tuples, sorted most-recipe-heavy first.
    """
    data = _ensure_index()
    categories_with_counts: list[tuple[str, int]] = [
        (cat, data.category_counts.get(cat, 0)) for cat in data.categories
    ]
    categories_with_counts.sort(key=lambda x: x[1], reverse=True)
    return categories_with_counts


async def get_suggestions(query: str) -> list[str]:
    """Return autocomplete suggestions using n-gram prefix matching.

    Args:
        query: Partial search text from the user.

    Returns:
        List of matching suggestion strings ranked by frequency then alphabetically.
    """
    _ensure_index()
    assert _ngram_index is not None  # noqa: S101
    return suggest_phrases(_ngram_index, query)
