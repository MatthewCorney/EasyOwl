"""
EasyOwl - Lightweight parsing of OWL Ontology files.

A simple, robust Library for parsing OWL and OBO ontology files into
Python data structures, with support for hierarchy navigation and
similarity search.

Examples
--------
>>> from easyowl import OntologyParser, download_ontology
>>>
>>> # Download an ontology
>>> path = download_ontology("http://purl.obolibrary.org/obo/hp.owl")
>>>
>>> # Parse and query
>>> parser = OntologyParser(path)
>>> entity = parser.entities["http://purl.obolibrary.org/obo/HP_0000001"]
>>> ancestors = parser.get_ancestors(entity_id)
>>> similar = parser.find_similar_terms("heart disease", n=5)
"""

from easyowl.download import download_ontology
from easyowl.enums import MatchType, SynonymType
from easyowl.exceptions import (
    DownloadError,
    EasyOwlError,
    EntityNotFoundError,
    OntologyParseError,
    TermNotFoundError,
)
from easyowl.reader import OntologyParser

__all__ = [
    "DownloadError",
    "EasyOwlError",
    "EntityNotFoundError",
    "MatchType",
    "OntologyParseError",
    "OntologyParser",
    "SynonymType",
    "TermNotFoundError",
    "download_ontology",
]

__version__ = "0.1.0"
