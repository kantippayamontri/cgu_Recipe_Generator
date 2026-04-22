"""TF-IDF index builder using scikit-learn baseline."""
from __future__ import annotations

from dataclasses import dataclass

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tf_idf.loader import TfidfDocument


@dataclass
class TfidfIndex:
    """Indexed TF-IDF corpus with sklearn baseline artifacts."""

    recipe_ids: list[int]
    documents: list[TfidfDocument]
    vectorizer: TfidfVectorizer
    matrix: csr_matrix
    feature_names: list[str]

    @property
    def document_count(self) -> int:
        """Return total indexed documents."""
        return len(self.recipe_ids)

    def top_terms_for_document(
        self, recipe_id: int, limit: int = 5
    ) -> list[tuple[str, float]]:
        """Return the highest-scoring TF-IDF terms for a document.

        Args:
            recipe_id: Recipe identifier to analyze.
            limit: Maximum number of top terms to return.

        Returns:
            List of (term, score) tuples sorted by TF-IDF score.
        """
        row_index = self.recipe_ids.index(recipe_id)
        row = self.matrix[row_index].toarray().ravel()
        ranked_indices = row.argsort()[::-1]
        results: list[tuple[str, float]] = []
        for feature_index in ranked_indices:
            score = float(row[feature_index])
            if score <= 0:
                continue
            results.append((self.feature_names[feature_index], score))
            if len(results) >= limit:
                break
        return results

    def compare_query(self, query: str, limit: int = 5) -> list[tuple[int, float]]:
        """Return sklearn-baseline query results for comparison.

        Args:
            query: Search query text.
            limit: Maximum number of results.

        Returns:
            List of (recipe_id, score) tuples.
        """
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        ranked_indices = scores.argsort()[::-1]
        results: list[tuple[int, float]] = []
        for row_index in ranked_indices:
            score = float(scores[row_index])
            if score <= 0:
                continue
            results.append((self.recipe_ids[row_index], score))
            if len(results) >= limit:
                break
        return results


def build_tfidf_index(documents: list[TfidfDocument]) -> TfidfIndex:
    """Build a TF-IDF index from recipe documents.

    Args:
        documents: Recipe documents from Phase 7 preprocessing.

    Returns:
        TfidfIndex with fitted sklearn vectorizer and matrix.
    """
    corpus = [document.text for document in documents]
    recipe_ids = [document.recipe_id for document in documents]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=1.0,
    )
    matrix = vectorizer.fit_transform(corpus)
    feature_names = list(vectorizer.get_feature_names_out())

    return TfidfIndex(
        recipe_ids=recipe_ids,
        documents=documents,
        vectorizer=vectorizer,
        matrix=matrix,
        feature_names=feature_names,
    )
