"""Tests for the TF-IDF searcher module."""
from tf_idf.indexer import build_tfidf_index
from tf_idf.loader import TfidfDocument
from tf_idf.searcher import SearchResult, search_documents


def test_search_documents_ranks_best_match_first() -> None:
    """Search ranks most relevant document first."""
    index = build_tfidf_index(
        [
            TfidfDocument(recipe_id=1, text="tomato basil pasta"),
            TfidfDocument(recipe_id=2, text="chicken noodle soup"),
            TfidfDocument(recipe_id=3, text="basil pesto pasta"),
        ]
    )

    results = search_documents(index, "tomato pasta", limit=2)

    assert results[0].recipe_id == 1
    assert results[0].score >= results[1].score


def test_search_documents_returns_empty_list_for_blank_query() -> None:
    """Search returns empty list for blank queries."""
    index = build_tfidf_index(
        [TfidfDocument(recipe_id=1, text="tomato basil pasta")]
    )

    assert search_documents(index, " ") == []
