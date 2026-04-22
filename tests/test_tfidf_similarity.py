"""Tests for the TF-IDF similarity module."""
from tf_idf.indexer import build_tfidf_index
from tf_idf.loader import TfidfDocument
from tf_idf.similarity import SimilarRecipe, find_similar_documents


def test_find_similar_documents_excludes_source_recipe() -> None:
    """Similarity search excludes the source recipe."""
    index = build_tfidf_index(
        [
            TfidfDocument(recipe_id=1, text="tomato basil pasta"),
            TfidfDocument(recipe_id=2, text="tomato garlic pasta"),
            TfidfDocument(recipe_id=3, text="chicken soup broth"),
        ]
    )

    results = find_similar_documents(index, recipe_id=1, limit=2)

    assert results[0].recipe_id == 2
    assert all(result.recipe_id != 1 for result in results)


def test_find_similar_documents_returns_empty_for_unknown_recipe() -> None:
    """Similarity search returns empty list for unknown recipe ID."""
    index = build_tfidf_index(
        [TfidfDocument(recipe_id=1, text="tomato basil pasta")]
    )

    assert find_similar_documents(index, recipe_id=999) == []
