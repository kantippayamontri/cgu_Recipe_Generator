"""Standalone CLI for testing the N-gram autocomplete module.

Usage:
    # Single query
    uv run python -m n_gram --query "tom"

    # Interactive REPL mode
    uv run python -m n_gram
"""

from __future__ import annotations

import argparse
import logging

from n_gram.loader import load_suggestion_documents
from n_gram.suggester import suggest_phrases
from n_gram.trainer import build_n_gram_index
from server.services.index_service import load_index

logger = logging.getLogger(__name__)


def run_query(query: str, limit: int = 10) -> None:
    """Load the index and print suggestions for a single query."""
    data = load_index()
    docs = load_suggestion_documents(data)
    print(f"Loaded {len(docs)} suggestion documents for n-gram training.")
    ngram_index = build_n_gram_index(docs)
    print(f"Built n-gram index with {len(ngram_index.prefix_map)} prefix entries.")

    suggestions = suggest_phrases(ngram_index, query, limit=limit)
    print(f'\nSuggestions for "{query}":')
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")


def run_interactive(limit: int = 10) -> None:
    """Load the index once, then run a REPL for interactive queries."""
    print("Loading N-gram index...")
    data = load_index()
    docs = load_suggestion_documents(data)
    ngram_index = build_n_gram_index(docs)
    print(
        f"Loaded {len(docs)} phrases, {len(ngram_index.prefix_map)} prefix entries.\n"
    )
    print("Enter a prefix to see suggestions (type 'quit' to exit, blank for top by frequency).\n")

    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if query.lower() in ("quit", "exit", "q"):
            break

        suggestions = suggest_phrases(ngram_index, query, limit=limit)
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                count = ngram_index.phrase_counts.get(suggestion, 0)
                print(f"  {i}. {suggestion}  ({count})")
        else:
            print("  (no matches)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test the N-gram autocomplete module with recipe data"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Single search prefix (e.g., 'tom', 'chicken')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum suggestions to return (default: 10)",
    )
    args = parser.parse_args()

    if args.query is not None:
        run_query(args.query, limit=args.limit)
    else:
        run_interactive(limit=args.limit)