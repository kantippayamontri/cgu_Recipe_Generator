"""N-gram autocomplete data model."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NGramDocument:
    """Normalized phrase used to train the n-gram suggester."""

    text: str
    source: str


@dataclass
class NGramIndex:
    """In-memory n-gram suggestion index."""

    documents: list[NGramDocument] = field(default_factory=list)
    phrase_counts: dict[str, int] = field(default_factory=dict)
    prefix_map: dict[str, list[str]] = field(default_factory=dict)

    @property
    def document_count(self) -> int:
        """Return total indexed documents."""
        return len(self.documents)
