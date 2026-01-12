"""Enumerations for ontology element types."""

from enum import StrEnum


class SynonymType(StrEnum):
    """
    Types of synonyms found in OBO/OWL ontologies.

    These correspond to the oboInOwl annotation properties for synonyms.
    """

    EXACT = "hasExactSynonym"
    """An exact synonym - fully interchangeable with the primary label."""

    NARROW = "hasNarrowSynonym"
    """A narrower term - more specific than the primary label."""

    BROAD = "hasBroadSynonym"
    """A broader term - more general than the primary label."""


class MatchType(StrEnum):
    """
    Types of SKOS mapping matches between ontology terms.

    These correspond to SKOS mapping properties for cross-references.
    """

    EXACT = "exactMatch"
    """Exact match - terms are identical in meaning."""

    CLOSE = "closeMatch"
    """Close match - terms are similar but not identical."""

    NARROW = "narrowMatch"
    """Narrow match - this term is more specific than the matched term."""

    BROAD = "broadMatch"
    """Broad match - this term is more general than the matched term."""
