"""N-gram autocomplete package."""
from n_gram.model import NGramDocument, NGramIndex
from n_gram.suggester import suggest_phrases
from n_gram.trainer import build_n_gram_index

__all__ = [
    "NGramDocument",
    "NGramIndex",
    "build_n_gram_index",
    "suggest_phrases",
]
