# EasyOwl

[![CI](https://github.com/MatthewCorney/EasyOwl/actions/workflows/ci.yml/badge.svg)](https://github.com/MatthewCorney/EasyOwl/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight Python library for parsing OWL and OBO ontology files. Created to handle inconsistencies in ontology file formats that cause issues with more comprehensive packages.

## Installation

```bash
pip install git+https://github.com/MatthewCorney/EasyOwl.git
```

## Quick Start

```python
from easyowl import OntologyParser, download_ontology

# Download an ontology
download_ontology(
    url="https://github.com/EBISPOT/efo/releases/download/current/efo.owl",
    destination_dir="data"
)

# Parse it
parser = OntologyParser("data/efo.owl")

# Access entities
entity = parser.entities["http://www.ebi.ac.uk/efo/EFO_0005634"]
```

## API

### Parsing

```python
from easyowl import OntologyParser

parser = OntologyParser("path/to/ontology.owl")

# Access all entities
print(len(parser.entities))

# Access a specific entity
entity = parser.entities["http://example.org/MyClass"]
print(entity["properties"]["label"])
print(entity["synonyms"])
print(entity["matches"])
```

### Hierarchy Navigation

```python
# Get all ancestors (superclasses)
ancestors = parser.get_ancestors("http://example.org/MyClass")

# Get direct parents only
direct_parents = parser.get_ancestors("http://example.org/MyClass", max_depth=1)

# Get all descendants (subclasses)
descendants = parser.get_descendants("http://example.org/MyClass")

# Get direct children only
direct_children = parser.get_descendants("http://example.org/MyClass", max_depth=1)
```

### Similarity Search

```python
# Find similar terms by label
results = parser.find_similar_terms("heart disease", n=5)
for result in results:
    print(f"{result['name']}: {result['score']:.2f}")

# With a similarity threshold
results = parser.find_similar_terms("heart disease", threshold=0.7)
```

### Error Handling

```python
from easyowl import OntologyParser, EntityNotFoundError, OntologyParseError

try:
    parser = OntologyParser("ontology.owl")
    ancestors = parser.get_ancestors("http://nonexistent/entity")
except OntologyParseError as e:
    print(f"Failed to parse: {e}")
except EntityNotFoundError as e:
    print(f"Entity not found: {e.entity_id}")
```

### Downloading Ontologies

```python
from easyowl import download_ontology, DownloadError

try:
    path = download_ontology(
        url="http://purl.obolibrary.org/obo/hp.owl",
        destination_dir="data",
        filename="human_phenotype.owl"  # optional custom name
    )
    print(f"Downloaded to: {path}")
except DownloadError as e:
    print(f"Download failed: {e}")
```

## Entity Structure

Each entity in `parser.entities` is a dictionary with:

```python
{
    "properties": {
        "label": "Entity Label",
        "id": "ENTITY_0001",
        # ... other annotation properties
    },
    "subclasses": ["http://parent/class"],
    "disjoints": ["http://disjoint/class"],
    "synonyms": {
        "hasExactSynonym": ["Exact Synonym"],
        "hasNarrowSynonym": [],
        "hasBroadSynonym": []
    },
    "matches": {
        "exactMatch": [],
        "closeMatch": [],
        "narrowMatch": [],
        "broadMatch": []
    }
}
```

## Development

```bash
# Clone and install
git clone https://github.com/MatthewCorney/EasyOwl.git
cd EasyOwl
poetry install

# Run checks
poetry run ruff check src tests
poetry run mypy
poetry run pytest
```

## License

MIT
