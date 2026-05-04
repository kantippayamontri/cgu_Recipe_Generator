"""N-gram suggestion training loader."""
from __future__ import annotations

import re

from n_gram.model import NGramDocument
from server.services.index_service import IndexData

# Characters to strip from training phrases before indexing.
# Keeps letters, digits, and spaces only.
_STRIP_PATTERN = re.compile(r"[^a-z0-9 ]")


def _normalize_phrase(value: str) -> str:
    """Normalize a phrase for n-gram training.

    Lowercases, removes non-alphanumeric characters (e.g. hyphens, parentheses),
    and collapses whitespace.
    """
    lowered = value.lower()
    cleaned = _STRIP_PATTERN.sub(" ", lowered)
    return " ".join(cleaned.split())


def load_suggestion_documents(data: IndexData) -> list[NGramDocument]:
    """Extract title and ingredient phrases for autocomplete training.

    Args:
        data: Loaded recipe index data.

    Returns:
        List of normalized training phrases.
    """
    documents: list[NGramDocument] = []
    for recipe in data.recipes.values():
        title = _normalize_phrase(recipe.title)
        if title:
            documents.append(NGramDocument(text=title, source="title"))
        for ingredient in recipe.ingredients:
            name = _normalize_phrase(str(ingredient.get("name", "")))
            if name:
                documents.append(NGramDocument(text=name, source="ingredient"))
    return documents
