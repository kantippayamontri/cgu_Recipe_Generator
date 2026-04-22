"""Tests for the TF-IDF indexer module."""
from tf_idf.indexer import TfidfIndex, build_tfidf_index
from tf_idf.loader import TfidfDocument


def test_build_tfidf_index_preserves_recipe_ids() -> None:
    """Index preserves recipe IDs in order."""
    documents = [
        TfidfDocument(recipe_id=10, text="tomato basil pasta"),
        TfidfDocument(recipe_id=20, text="chicken noodle soup"),
    ]

    index = build_tfidf_index(documents)

    assert index.recipe_ids == [10, 20]
    assert index.document_count == 2


def test_build_tfidf_index_exposes_feature_names() -> None:
    """Index exposes feature names from vocabulary."""
    documents = [
        TfidfDocument(recipe_id=10, text="tomato basil pasta"),
        TfidfDocument(recipe_id=20, text="tomato soup"),
    ]

    index = build_tfidf_index(documents)

    assert "tomato" in index.feature_names
    assert index.matrix.shape[0] == 2


def test_build_tfidf_index_returns_top_terms_per_document() -> None:
    """Index can return top TF-IDF terms for a document."""
    documents = [
        TfidfDocument(recipe_id=10, text="tomato basil tomato pasta"),
        TfidfDocument(recipe_id=20, text="chicken soup broth"),
    ]

    index = build_tfidf_index(documents)
    top_terms = index.top_terms_for_document(recipe_id=10, limit=2)

    assert len(top_terms) == 2
    assert top_terms[0][0] in {"tomato", "basil", "pasta"}
    assert top_terms[0][1] > 0
