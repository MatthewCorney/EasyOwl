"""Main OntologyParser class - facade for parsing and querying OWL ontologies."""

from pathlib import Path
from typing import Any

from easyowl.constants import UNLIMITED_DEPTH
from easyowl.exceptions import EntityNotFoundError
from easyowl.hierarchy import HierarchyNavigator, build_subclass_map
from easyowl.parsing import parse_owl_file
from easyowl.similarity import SimilaritySearch, build_term_index


class OntologyParser:
    """
    Parser and query interface for OWL ontology files.

    This class provides a high-level interface for loading OWL ontology files
    and querying entity relationships, hierarchy, and similar terms.

    Parameters
    ----------
    file_path : str | Path
        Path to the OWL ontology file.

    Attributes
    ----------
    entities : dict[str, dict[str, Any]]
        Dictionary mapping entity URIs to their parsed data.
    relations : list[dict[str, Any]]
        List of object property definitions.

    Raises
    ------
    OntologyParseError
        If the file cannot be parsed.

    Examples
    --------
    >>> parser = OntologyParser("data/ontology.owl")
    >>> entity = parser.entities["http://example.org/MyClass"]
    >>> ancestors = parser.get_ancestors("http://example.org/MyClass")
    >>> similar = parser.find_similar_terms("heart disease", n=5)
    """

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

        # Parse the ontology file
        self.entities, self.relations, self.namespace_map = parse_owl_file(file_path)

        # Build hierarchy navigator
        self._subclass_map = build_subclass_map(self.entities)
        self._hierarchy = HierarchyNavigator(self._subclass_map)

        # Build similarity search index
        term_to_ids, index_to_term, term_to_index = build_term_index(self.entities)
        self._similarity = SimilaritySearch(term_to_ids, index_to_term, term_to_index)

    def get_ancestors(
        self,
        entity_id: str,
        *,
        max_depth: int = UNLIMITED_DEPTH,
    ) -> list[str]:
        """
        Find all ancestor (superclass) entities of the given entity.

        Parameters
        ----------
        entity_id : str
            The URI of the entity to start from.
        max_depth : int, default=-1
            Maximum depth to traverse. Use -1 for unlimited depth.

        Returns
        -------
        list[str]
            URIs of all ancestor classes.

        Raises
        ------
        EntityNotFoundError
            If the entity_id is not found in the ontology.

        Examples
        --------
        >>> parser = OntologyParser("ontology.owl")
        >>> ancestors = parser.get_ancestors("http://example.org/MyClass")
        >>> direct_parents = parser.get_ancestors("http://example.org/MyClass", max_depth=1)
        """
        if entity_id not in self.entities:
            raise EntityNotFoundError(entity_id)

        return self._hierarchy.get_ancestors(entity_id, max_depth=max_depth)

    def get_descendants(
        self,
        entity_id: str,
        *,
        max_depth: int = UNLIMITED_DEPTH,
    ) -> list[str]:
        """
        Find all descendant (subclass) entities of the given entity.

        Parameters
        ----------
        entity_id : str
            The URI of the entity to start from.
        max_depth : int, default=-1
            Maximum depth to traverse. Use -1 for unlimited depth.

        Returns
        -------
        list[str]
            URIs of all descendant classes.

        Raises
        ------
        EntityNotFoundError
            If the entity_id is not found in the ontology.

        Examples
        --------
        >>> parser = OntologyParser("ontology.owl")
        >>> descendants = parser.get_descendants("http://example.org/MyClass")
        >>> direct_children = parser.get_descendants("http://example.org/MyClass", max_depth=1)
        """
        if entity_id not in self.entities:
            raise EntityNotFoundError(entity_id)

        return self._hierarchy.get_descendants(entity_id, max_depth=max_depth)

    def get_entity_relations(self, entity_id: str) -> dict[str, Any]:
        """
        Get all relationships for a given entity.

        Parameters
        ----------
        entity_id : str
            The URI of the entity.

        Returns
        -------
        dict[str, Any]
            Dictionary containing:
            - 'ancestors': list of direct superclass URIs
            - 'descendants': list of direct subclass URIs
            - 'relations': list of object property relations involving this entity

        Raises
        ------
        EntityNotFoundError
            If the entity_id is not found in the ontology.

        Examples
        --------
        >>> relations = parser.get_entity_relations("http://example.org/MyClass")
        >>> print(relations['ancestors'])
        """
        if entity_id not in self.entities:
            raise EntityNotFoundError(entity_id)

        ancestors = self._hierarchy.get_ancestors(entity_id, max_depth=1)
        descendants = self._hierarchy.get_descendants(entity_id, max_depth=1)

        related_relations = [
            relation
            for relation in self.relations
            if (
                relation.get("domain") == entity_id
                or relation.get("range") == entity_id
                or entity_id in relation.get("properties", {}).values()
            )
        ]

        return {
            "ancestors": ancestors,
            "descendants": descendants,
            "relations": related_relations,
        }

    def find_similar_terms(
        self,
        term: str,
        *,
        n: int | None = None,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find terms similar to the given term using TF-IDF similarity.

        Parameters
        ----------
        term : str
            The term label to search for.
        n : int | None, default=None
            Return at most N most similar terms.
        threshold : float | None, default=None
            Minimum similarity score (0.0 to 1.0).

        Returns
        -------
        list[dict[str, Any]]
            List of result dictionaries with 'name', 'ids', and 'score' keys.

        Raises
        ------
        TermNotFoundError
            If the term is not found in the ontology index.

        Notes
        -----
        When both `n` and `threshold` are provided, threshold filtering
        is applied first, then top-N selection.

        Examples
        --------
        >>> results = parser.find_similar_terms("heart disease", n=5)
        >>> results = parser.find_similar_terms("heart disease", threshold=0.8)
        """
        return self._similarity.find_similar(term, n=n, threshold=threshold)

    def has_entity(self, entity_id: str) -> bool:
        """
        Check if an entity exists in the ontology.

        Parameters
        ----------
        entity_id : str
            The URI of the entity to check.

        Returns
        -------
        bool
            True if the entity exists, False otherwise.
        """
        return entity_id in self.entities

    def has_term(self, term: str) -> bool:
        """
        Check if a term label exists in the similarity index.

        Parameters
        ----------
        term : str
            The term label to check.

        Returns
        -------
        bool
            True if the term is indexed, False otherwise.
        """
        return self._similarity.has_term(term)
