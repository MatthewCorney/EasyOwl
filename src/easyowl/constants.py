"""Constants used throughout the EasyOwl package."""

# Recursion limits for hierarchy traversal
MAX_RECURSION_DEPTH: int = 1000
"""Maximum depth for ancestor/descendant traversal to prevent infinite loops."""

UNLIMITED_DEPTH: int = -1
"""Sentinel value indicating unlimited traversal depth."""

# Download settings
DOWNLOAD_CHUNK_SIZE: int = 8192
"""Chunk size in bytes for streaming file downloads."""

DOWNLOAD_TIMEOUT_SECONDS: int = 300
"""Timeout in seconds for HTTP requests when downloading ontologies."""

# OWL/XML namespaces commonly found in ontology files
DEFAULT_NAMESPACES: dict[str, str] = {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "oboInOwl": "http://www.geneontology.org/formats/oboInOwl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}
"""Common XML namespaces used in OWL ontology files."""
