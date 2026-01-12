"""Hierarchy navigation for ontology class relationships."""

from collections import defaultdict
from typing import Any

from easyowl.constants import MAX_RECURSION_DEPTH, UNLIMITED_DEPTH


def build_subclass_map(entities: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    """
    Build a map from entity IDs to their direct superclass IDs.

    This map enables efficient ancestor traversal by recording which classes
    each entity is a subclass of.

    Parameters
    ----------
    entities : dict[str, dict[str, Any]]
        Dictionary of parsed entity data from the ontology.

    Returns
    -------
    dict[str, set[str]]
        Map from entity ID to set of direct superclass IDs.
    """
    subclass_map: dict[str, set[str]] = defaultdict(set)

    for entity_id, entity_data in entities.items():
        for subclass in entity_data.get("subclasses", []):
            if isinstance(subclass, str):
                subclass_map[entity_id].add(subclass)
            elif isinstance(subclass, list):
                for item in subclass:
                    if isinstance(item, str):
                        subclass_map[entity_id].add(item)

    return dict(subclass_map)


def build_reverse_map(subclass_map: dict[str, set[str]]) -> dict[str, set[str]]:
    """
    Build a reverse map from superclass IDs to their direct subclass IDs.

    This map enables efficient descendant traversal.

    Parameters
    ----------
    subclass_map : dict[str, set[str]]
        Map from entity ID to set of superclass IDs.

    Returns
    -------
    dict[str, set[str]]
        Map from superclass ID to set of direct subclass IDs.
    """
    reverse_map: dict[str, set[str]] = defaultdict(set)

    for entity_id, superclasses in subclass_map.items():
        for superclass_id in superclasses:
            reverse_map[superclass_id].add(entity_id)

    return dict(reverse_map)


class HierarchyNavigator:
    """
    Navigate class hierarchies in an ontology.

    This class provides methods to traverse ancestor and descendant relationships
    between ontology classes.

    Parameters
    ----------
    subclass_map : dict[str, set[str]]
        Map from entity ID to set of direct superclass IDs.

    Examples
    --------
    >>> navigator = HierarchyNavigator(subclass_map)
    >>> ancestors = navigator.get_ancestors("http://example.org/MyClass")
    >>> descendants = navigator.get_descendants("http://example.org/MyClass")
    """

    def __init__(self, subclass_map: dict[str, set[str]]) -> None:
        self._subclass_map = subclass_map
        self._reverse_map = build_reverse_map(subclass_map)

    def get_ancestors(
        self,
        entity_id: str,
        *,
        max_depth: int = UNLIMITED_DEPTH,
    ) -> list[str]:
        """
        Find all ancestor classes of the given entity.

        Traverses the subClassOf hierarchy upward from the given entity,
        collecting all superclasses up to the specified depth.

        Parameters
        ----------
        entity_id : str
            The URI of the entity to start from.
        max_depth : int, default=-1
            Maximum depth to traverse. Use -1 for unlimited depth.

        Returns
        -------
        list[str]
            URIs of all ancestor classes (not including the entity itself).

        Notes
        -----
        The traversal stops when:
        - All ancestors have been found
        - The maximum depth is reached
        - A cycle is detected (to prevent infinite loops)
        """
        return self._traverse_ancestors(
            entity_id=entity_id,
            max_depth=max_depth,
            visited=set(),
            current_depth=0,
        )

    def _traverse_ancestors(
        self,
        entity_id: str,
        max_depth: int,
        visited: set[str],
        current_depth: int,
    ) -> list[str]:
        """Internal recursive implementation of ancestor traversal."""
        effective_max = float("inf") if max_depth == UNLIMITED_DEPTH else max_depth

        if current_depth > effective_max:
            return []

        if current_depth > MAX_RECURSION_DEPTH:
            return []

        if entity_id in visited:
            return []

        visited.add(entity_id)

        ancestors: set[str] = set()

        if entity_id in self._subclass_map:
            for superclass_id in self._subclass_map[entity_id]:
                ancestors.add(superclass_id)
                ancestors.update(
                    self._traverse_ancestors(
                        entity_id=superclass_id,
                        max_depth=max_depth,
                        visited=visited,
                        current_depth=current_depth + 1,
                    )
                )

        return list(ancestors)

    def get_descendants(
        self,
        entity_id: str,
        *,
        max_depth: int = UNLIMITED_DEPTH,
    ) -> list[str]:
        """
        Find all descendant classes of the given entity.

        Traverses the subClassOf hierarchy downward from the given entity,
        collecting all subclasses up to the specified depth.

        Parameters
        ----------
        entity_id : str
            The URI of the entity to start from.
        max_depth : int, default=-1
            Maximum depth to traverse. Use -1 for unlimited depth.

        Returns
        -------
        list[str]
            URIs of all descendant classes (not including the entity itself).

        Notes
        -----
        The traversal stops when:
        - All descendants have been found
        - The maximum depth is reached
        - A cycle is detected (to prevent infinite loops)
        """
        return self._traverse_descendants(
            entity_id=entity_id,
            max_depth=max_depth,
            visited=set(),
            current_depth=0,
        )

    def _traverse_descendants(
        self,
        entity_id: str,
        max_depth: int,
        visited: set[str],
        current_depth: int,
    ) -> list[str]:
        """Internal recursive implementation of descendant traversal."""
        effective_max = float("inf") if max_depth == UNLIMITED_DEPTH else max_depth

        if current_depth > effective_max:
            return []

        if current_depth > MAX_RECURSION_DEPTH:
            return []

        if entity_id in visited:
            return []

        visited.add(entity_id)

        descendants: set[str] = set()

        if entity_id in self._reverse_map:
            for subclass_id in self._reverse_map[entity_id]:
                descendants.add(subclass_id)
                descendants.update(
                    self._traverse_descendants(
                        entity_id=subclass_id,
                        max_depth=max_depth,
                        visited=visited,
                        current_depth=current_depth + 1,
                    )
                )

        return list(descendants)

    def has_entity(self, entity_id: str) -> bool:
        """
        Check if an entity exists in the hierarchy.

        Parameters
        ----------
        entity_id : str
            The URI of the entity to check.

        Returns
        -------
        bool
            True if the entity has hierarchy relationships, False otherwise.
        """
        return entity_id in self._subclass_map or entity_id in self._reverse_map
