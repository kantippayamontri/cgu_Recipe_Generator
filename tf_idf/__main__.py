"""Demo script for TF-IDF search and similarity with sklearn baseline comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from tf_idf.indexer import build_tfidf_index
from tf_idf.loader import load_tfidf_documents
from tf_idf.searcher import search_documents
from tf_idf.similarity import find_similar_documents


def demo_search(csv_path: Path, query: str, limit: int = 5) -> None:
    """Run a search query and display results with comparison.

    Args:
        csv_path: Path to TF-IDF ready CSV.
        query: Search query string.
        limit: Maximum results to show.
    """
    print(f"Loading documents from {csv_path}...")
    documents = load_tfidf_documents(csv_path)
    print(f"Loaded {len(documents)} documents\n")

    df = pd.read_csv(csv_path)
    id_to_title: dict[int, str] = {}
    if "title" in df.columns:
        id_to_title = dict(zip(df["recipe_id"].astype(int), df["title"].astype(str)))

    print("Building TF-IDF index...")
    index = build_tfidf_index(documents)
    print(
        f"Index built: {index.document_count} docs, {len(index.feature_names)} features\n"
    )

    # Search results
    print(f"Query: '{query}'")
    print("-" * 60)
    results = search_documents(index, query, limit=limit)

    if not results:
        print("No results found.")
        return

    print("\nSearch Results (tf_idf.searcher):")
    for i, result in enumerate(results, 1):
        title = id_to_title.get(result.recipe_id, "Unknown")
        print(f"  {i}. [{result.recipe_id}] {title} (score: {result.score:.4f})")

    # Comparison baseline
    print("\nSklearn Baseline Comparison:")
    baseline_results = index.compare_query(query, limit=limit)
    for i, (recipe_id, score) in enumerate(baseline_results, 1):
        title = id_to_title.get(recipe_id, "Unknown")
        print(f"  {i}. [{recipe_id}] {title} (score: {score:.4f})")


def demo_similarity(csv_path: Path, recipe_id: int, limit: int = 5) -> None:
    """Find similar recipes to a given recipe.

    Args:
        csv_path: Path to TF-IDF ready CSV.
        recipe_id: Source recipe ID.
        limit: Maximum similar recipes to show.
    """
    print(f"Loading documents from {csv_path}...")
    documents = load_tfidf_documents(csv_path)
    print(f"Loaded {len(documents)} documents\n")

    df = pd.read_csv(csv_path)
    id_to_title: dict[int, str] = {}
    if "title" in df.columns:
        id_to_title = dict(zip(df["recipe_id"].astype(int), df["title"].astype(str)))

    print("Building TF-IDF index...")
    index = build_tfidf_index(documents)
    print(f"Index built: {index.document_count} docs\n")

    print(f"Finding recipes similar to recipe {recipe_id}...")
    print("-" * 60)
    results = find_similar_documents(index, recipe_id=recipe_id, limit=limit)

    if not results:
        print("No similar recipes found or recipe ID not in index.")
        return

    print("\nSimilar Recipes:")
    for i, result in enumerate(results, 1):
        title = id_to_title.get(result.recipe_id, "Unknown")
        print(f"  {i}. [{result.recipe_id}] {title} (score: {result.score:.4f})")


def main() -> None:
    """Run TF-IDF demo based on command-line arguments."""
    parser = argparse.ArgumentParser(description="TF-IDF Recipe Search Demo")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/process/recipes_tfidf_ready.csv"),
        help="Path to TF-IDF ready CSV file",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="tomato pasta",
        help="Search query string",
    )
    parser.add_argument(
        "--similar-to",
        type=int,
        default=None,
        help="Find recipes similar to this recipe ID",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results",
    )

    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Error: CSV file not found: {args.csv}")
        print(
            "Run the Phase 7 preprocessing pipeline first to generate the TF-IDF ready CSV."
        )
        return

    if args.similar_to is not None:
        demo_similarity(args.csv, args.similar_to, args.limit)
    else:
        demo_search(args.csv, args.query, args.limit)


if __name__ == "__main__":
    main()
