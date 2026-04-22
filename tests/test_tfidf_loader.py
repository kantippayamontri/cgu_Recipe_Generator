"""Tests for the TF-IDF loader module."""
from pathlib import Path

import pandas as pd
import pytest

from tf_idf.loader import TfidfDocument, load_tfidf_documents


def test_load_tfidf_documents_returns_recipe_id_and_text(tmp_path: Path) -> None:
    """Loader returns recipe IDs and text from CSV."""
    csv_path = tmp_path / "recipes_tfidf_ready.csv"
    pd.DataFrame(
        [
            {"recipe_id": 1, "tfidf_text": "tomato basil pasta"},
            {"recipe_id": 2, "tfidf_text": "chicken soup broth"},
        ]
    ).to_csv(csv_path, index=False)

    documents = load_tfidf_documents(csv_path)

    assert documents == [
        TfidfDocument(recipe_id=1, text="tomato basil pasta"),
        TfidfDocument(recipe_id=2, text="chicken soup broth"),
    ]


def test_load_tfidf_documents_skips_empty_text_rows(tmp_path: Path) -> None:
    """Loader skips rows with empty or NaN text."""
    csv_path = tmp_path / "recipes_tfidf_ready.csv"
    pd.DataFrame(
        [
            {"recipe_id": 1, "tfidf_text": "tomato basil pasta"},
            {"recipe_id": 2, "tfidf_text": ""},
            {"recipe_id": 3, "tfidf_text": None},
        ]
    ).to_csv(csv_path, index=False)

    documents = load_tfidf_documents(csv_path)

    assert documents == [TfidfDocument(recipe_id=1, text="tomato basil pasta")]


def test_load_tfidf_documents_requires_expected_columns(tmp_path: Path) -> None:
    """Loader raises ValueError if required columns are missing."""
    csv_path = tmp_path / "recipes_tfidf_ready.csv"
    pd.DataFrame([{"id": 1, "text": "tomato basil pasta"}]).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="recipe_id"):
        load_tfidf_documents(csv_path)
