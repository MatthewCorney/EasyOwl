"""Similarity search for ontology terms using TF-IDF vectorization."""

from heapq import nlargest
from typing import TYPE_CHECKING, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from easyowl.exceptions import TermNotFoundError

if TYPE_CHECKING:
    from scipy.sparse import csr_array


def build_term_index(
    entities: dict[str, dict[str, Any]],
) -> tuple[dict[str | None, set[str]], dict[int, str | None], dict[str | None, int]]:
    """
    Build index mappings from entity labels and synonyms.

    Parameters
    ----------
    entities : dict[str, dict[str, Any]]
        Dictionary of parsed entity data.

    Returns
    -------
    tuple
        - term_to_ids: Map from term label to set of entity IDs
        - index_to_term: Map from numeric index to term label
        - term_to_index: Map from term label to numeric index
    """
    # Extract labels and exact synonyms
    exact_names: dict[str, Any] = {
        entity["properties"]["id"]: entity["properties"].get("label")
        for entity in entities.values()
        if entity["properties"].get("id") is not None
    }

    synonymy: dict[str, Any] = {
        entity["properties"]["id"]: entity["properties"].get("hasExactSynonym")
        for entity in entities.values()
        if entity["properties"].get("id") is not None
    }

    # Build term to IDs mapping
    term_to_ids: dict[str | None, set[str]] = {}

    for entity_id, name in exact_names.items():
        if name not in term_to_ids:
            term_to_ids[name] = set()
        term_to_ids[name].add(entity_id)

    for entity_id, names in synonymy.items():
        if names is None:
            continue
        if isinstance(names, str):
            names = [names]
        for name in names:
            if name not in term_to_ids:
                term_to_ids[name] = set()
            term_to_ids[name].add(entity_id)

    # Build bidirectional index
    term_to_index: dict[str | None, int] = {
        term: idx for idx, term in enumerate(term_to_ids.keys())
    }
    index_to_term: dict[int, str | None] = {idx: term for term, idx in term_to_index.items()}

    return term_to_ids, index_to_term, term_to_index


class SimilaritySearch:
    """
    Search for similar terms using TF-IDF cosine similarity.

    This class provides fuzzy matching of ontology term labels using
    TF-IDF vectorization and cosine similarity scoring.

    Parameters
    ----------
    term_to_ids : dict[str | None, set[str]]
        Map from term label to set of entity IDs.
    index_to_term : dict[int, str | None]
        Map from numeric index to term label.
    term_to_index : dict[str | None, int]
        Map from term label to numeric index.

    Examples
    --------
    >>> search = SimilaritySearch(term_to_ids, index_to_term, term_to_index)
    >>> results = search.find_similar("heart disease", n=5)
    """

    def __init__(
        self,
        term_to_ids: dict[str | None, set[str]],
        index_to_term: dict[int, str | None],
        term_to_index: dict[str | None, int],
    ) -> None:
        self._term_to_ids = term_to_ids
        self._index_to_term = index_to_term
        self._term_to_index = term_to_index
        self._similarity_matrix: csr_array | None = None

    def _build_matrix(self) -> None:
        """Build the TF-IDF similarity matrix (lazy initialization)."""
        vectorizer = TfidfVectorizer()
        valid_terms = [term for term in self._term_to_ids if term is not None]

        if not valid_terms:
            return

        tfidf_matrix = vectorizer.fit_transform(valid_terms)
        self._similarity_matrix = cosine_similarity(tfidf_matrix, dense_output=False)

    def find_similar(
        self,
        term: str,
        *,
        n: int | None = None,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find terms similar to the given term.

        Parameters
        ----------
        term : str
            The term label to search for.
        n : int | None, default=None
            Return at most N most similar terms.
            If None, returns all matches above threshold (or all if no threshold).
        threshold : float | None, default=None
            Minimum similarity score (0.0 to 1.0).
            If None, no threshold filtering is applied.

        Returns
        -------
        list[dict[str, Any]]
            List of result dictionaries, each containing:
            - 'name': The matched term label
            - 'ids': Set of entity IDs with this label
            - 'score': Similarity score (0.0 to 1.0)

        Raises
        ------
        TermNotFoundError
            If the term is not found in the ontology index.

        Notes
        -----
        When both `n` and `threshold` are provided:
        1. First, terms below the threshold are filtered out
        2. Then, the top N remaining terms are returned

        Examples
        --------
        >>> search.find_similar("heart", n=5)  # Top 5 matches
        >>> search.find_similar("heart", threshold=0.8)  # All with score > 0.8
        >>> search.find_similar("heart", n=10, threshold=0.5)  # Top 10 above 0.5
        """
        if term not in self._term_to_index:
            raise TermNotFoundError(term)

        if self._similarity_matrix is None:
            self._build_matrix()

        if self._similarity_matrix is None:
            return []

        query_index = self._term_to_index[term]

        row_start: int = self._similarity_matrix.indptr[query_index]
        row_end: int = self._similarity_matrix.indptr[query_index + 1]

        similar_terms: list[tuple[Any, Any]] = list(
            zip(
                self._similarity_matrix.indices[row_start:row_end],
                self._similarity_matrix.data[row_start:row_end],
                strict=False,
            )
        )

        # Apply threshold filter
        if threshold is not None:
            similar_terms = [(idx, score) for idx, score in similar_terms if score > threshold]

        # Apply top-n selection
        if n is not None:
            similar_terms = nlargest(n, similar_terms, key=lambda x: x[1])
        else:
            similar_terms = sorted(similar_terms, key=lambda x: x[1], reverse=True)

        # Build result list
        return [
            {
                "name": self._index_to_term[idx],
                "ids": self._term_to_ids[self._index_to_term[idx]],
                "score": float(score),
            }
            for idx, score in similar_terms
        ]

    def has_term(self, term: str) -> bool:
        """
        Check if a term exists in the index.

        Parameters
        ----------
        term : str
            The term label to check.

        Returns
        -------
        bool
            True if the term is indexed, False otherwise.
        """
        return term in self._term_to_index
