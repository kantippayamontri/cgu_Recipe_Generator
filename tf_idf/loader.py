"""Load TF-IDF-ready recipe documents from Phase 7 CSV output."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TfidfDocument:
    """Recipe text prepared for TF-IDF indexing."""

    recipe_id: int
    text: str


def load_tfidf_documents(csv_path: Path) -> list[TfidfDocument]:
    """Load TF-IDF-ready recipe documents from a CSV file.

    Args:
        csv_path: Path to the Phase 7 TF-IDF-ready CSV file.

    Returns:
        List of TF-IDF documents with recipe IDs and combined text.

    Raises:
        ValueError: If required columns are missing.
    """
    df = pd.read_csv(csv_path)

    required_columns = {"recipe_id", "tfidf_text"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    documents: list[TfidfDocument] = []
    for _, row in df.iterrows():
        text = str(row.get("tfidf_text", "")).strip()
        if not text or text == "nan":
            continue
        documents.append(TfidfDocument(recipe_id=int(row["recipe_id"]), text=text))

    return documents
