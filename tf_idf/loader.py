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

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load TF-IDF documents from CSV")
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to the Phase 7 TF-IDF-ready CSV file",
    )
    args = parser.parse_args()

    try:
        docs = load_tfidf_documents(args.csv_path)
        print(f"Loaded {len(docs)} TF-IDF documents from {args.csv_path}")
    except Exception as e:
        print(f"Error loading TF-IDF documents: {e}")
