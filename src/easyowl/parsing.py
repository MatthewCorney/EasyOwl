"""Pure functions for parsing OWL ontology XML files."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lxml import etree
from lxml.etree import _Element

from easyowl.enums import MatchType, SynonymType
from easyowl.exceptions import OntologyParseError


def parse_owl_file(
    file_path: str | Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """
    Parse an OWL file and extract entities, relations, and namespace mappings.

    Parameters
    ----------
    file_path : str | Path
        Path to the OWL ontology file.

    Returns
    -------
    tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, str]]
        A tuple containing:
        - entities: Dictionary mapping entity URIs to their data
        - relations: List of object property definitions
        - namespace_map: Dictionary of namespace prefix to URI mappings

    Raises
    ------
    OntologyParseError
        If the file cannot be found, read, or parsed as valid OWL XML.
    """
    path = Path(file_path)

    if not path.exists():
        raise OntologyParseError(f"Ontology file not found: {file_path}")

    if not path.is_file():
        raise OntologyParseError(f"Path is not a file: {file_path}")

    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError as e:
        raise OntologyParseError(f"Invalid XML in ontology file: {file_path}") from e

    root = tree.getroot()

    # Extract namespaces, filtering out None keys (default namespace)
    namespace_map: dict[str, str] = {
        key: value for key, value in root.nsmap.items() if key is not None and value
    }

    # Validate required namespaces
    if "rdf" not in namespace_map:
        raise OntologyParseError(f"Missing required 'rdf' namespace in ontology: {file_path}")

    entities = _extract_all_entities(root, namespace_map)
    relations = _extract_all_relations(root, namespace_map)

    return entities, relations, namespace_map


def _extract_all_entities(
    root: _Element, namespace_map: Mapping[str, str]
) -> dict[str, dict[str, Any]]:
    """
    Extract all OWL class entities from the document root.

    Parameters
    ----------
    root : _Element
        Root element of the OWL XML document.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary mapping entity URIs to their extracted data.
    """
    entities: dict[str, dict[str, Any]] = {}
    rdf_about = f"{{{namespace_map['rdf']}}}about"

    for owl_class in root.findall("owl:Class", namespace_map):
        entity_id = owl_class.get(rdf_about)
        if entity_id:
            entities[entity_id] = _extract_entity(owl_class, namespace_map)

    return entities


def _extract_entity(element: _Element, namespace_map: Mapping[str, str]) -> dict[str, Any]:
    """
    Extract all data from a single OWL class element.

    Parameters
    ----------
    element : _Element
        The owl:Class XML element.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    dict[str, Any]
        Dictionary containing properties, subclasses, disjoints, synonyms, and matches.
    """
    rdf_resource = f"{{{namespace_map['rdf']}}}resource"

    # Extract basic properties
    properties = _extract_properties(element, namespace_map)

    # Extract subclass relationships
    subclasses: list[Any] = []
    for subclass in element.findall("rdfs:subClassOf", namespace_map):
        subclass_ref = subclass.get(rdf_resource)
        if subclass_ref:
            subclasses.append(subclass_ref)
        else:
            # Nested restriction or intersection
            restriction_data = _parse_restriction_or_intersection(subclass, namespace_map)
            if restriction_data:
                subclasses.append(restriction_data)

    # Extract disjoint classes
    disjoints: list[str] = [
        ref
        for disjoint in element.findall("owl:disjointWith", namespace_map)
        if (ref := disjoint.get(rdf_resource)) is not None
    ]

    return {
        "properties": properties,
        "subclasses": subclasses,
        "disjoints": disjoints,
        "synonyms": _extract_synonyms(element, namespace_map),
        "matches": _extract_matches(element, namespace_map),
    }


def _extract_all_relations(
    root: _Element, namespace_map: Mapping[str, str]
) -> list[dict[str, Any]]:
    """
    Extract all OWL object properties from the document root.

    Parameters
    ----------
    root : _Element
        Root element of the OWL XML document.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    list[dict[str, Any]]
        List of relation dictionaries with predicate, domain, range, and properties.
    """
    relations: list[dict[str, Any]] = []
    rdf_about = f"{{{namespace_map['rdf']}}}about"
    rdf_resource = f"{{{namespace_map['rdf']}}}resource"

    for obj_prop in root.findall("owl:ObjectProperty", namespace_map):
        predicate = obj_prop.get(rdf_about)
        if predicate:
            domain_elem = obj_prop.find("rdfs:domain", namespace_map)
            range_elem = obj_prop.find("rdfs:range", namespace_map)

            domain = domain_elem.get(rdf_resource) if domain_elem is not None else None
            range_ = range_elem.get(rdf_resource) if range_elem is not None else None

            # Extract child elements as properties
            obj_properties: dict[str, str] = {
                child.tag.split("}")[-1]: child.text.strip() for child in obj_prop if child.text
            }

            relations.append(
                {
                    "predicate": predicate,
                    "domain": domain,
                    "range": range_,
                    "properties": obj_properties,
                }
            )

    return relations


def _extract_properties(element: _Element, namespace_map: Mapping[str, str]) -> dict[str, Any]:
    """
    Extract all annotation properties from an OWL element.

    Parameters
    ----------
    element : _Element
        The XML element to extract properties from.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    dict[str, Any]
        Dictionary of property names to values. Single values are stored as strings,
        multiple values as lists.
    """
    properties: dict[str, Any] = {}
    rdf_resource = f"{{{namespace_map['rdf']}}}resource"

    for child in element:
        tag = child.tag.split("}")[-1]
        namespace = child.tag.split("}")[0][1:] if "}" in child.tag else ""

        if namespace in namespace_map.values():
            if tag not in properties:
                properties[tag] = []

            if child.text:
                properties[tag].append(child.text.strip())

            resource = child.get(rdf_resource)
            if resource:
                properties[tag].append(resource)

    # Collapse single-value lists to just the value
    for key in properties:
        if len(properties[key]) == 1:
            properties[key] = properties[key][0]

    return properties


def _extract_synonyms(element: _Element, namespace_map: Mapping[str, str]) -> dict[str, list[str]]:
    """
    Extract synonym annotations from an OWL element.

    Parameters
    ----------
    element : _Element
        The XML element to extract synonyms from.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    dict[str, list[str]]
        Dictionary mapping synonym type to list of synonym labels.
    """
    synonyms: dict[str, list[str]] = {}

    for synonym_type in SynonymType:
        synonyms[synonym_type.value] = [
            synonym.text.strip()
            for synonym in element.findall(f"oboInOwl:{synonym_type.value}", namespace_map)
            if synonym.text is not None
        ]

    return synonyms


def _extract_matches(element: _Element, namespace_map: Mapping[str, str]) -> dict[str, list[str]]:
    """
    Extract SKOS match annotations from an OWL element.

    Parameters
    ----------
    element : _Element
        The XML element to extract matches from.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    dict[str, list[str]]
        Dictionary mapping match type to list of matched URIs.
        Empty dict if SKOS namespace is not present.
    """
    matches: dict[str, list[str]] = {}

    skos_prefix = namespace_map.get("skos")
    if not skos_prefix:
        return matches

    for match_type in MatchType:
        matches[match_type.value] = [
            ref
            for match in element.findall(f"skos:{match_type.value}", namespace_map)
            if (ref := match.get(f"{{{skos_prefix}}}resource")) is not None
        ]

    return matches


def _parse_restriction_or_intersection(
    element: _Element, namespace_map: Mapping[str, str]
) -> list[dict[str, str | None]]:
    """
    Parse an owl:Restriction or owl:intersectionOf structure.

    Parameters
    ----------
    element : _Element
        XML element containing the restriction or intersection.
    namespace_map : Mapping[str, str]
        Namespace prefix to URI mapping.

    Returns
    -------
    list[dict[str, str | None]]
        List of restriction dictionaries with 'onProperty' and 'someValuesFrom' keys.
    """
    parsed_data: list[dict[str, str | None]] = []
    rdf_resource = f"{{{namespace_map['rdf']}}}resource"
    rdf_parse_type = f"{{{namespace_map['rdf']}}}parseType"

    # Handle owl:intersectionOf
    intersection = element.find("owl:intersectionOf", namespace_map)
    if intersection is not None:
        if intersection.get(rdf_parse_type) == "Collection":
            for item in intersection:
                if item.tag.endswith("Description") or "Restriction" in item.tag:
                    parsed_data.extend(_parse_restriction_or_intersection(item, namespace_map))
        return parsed_data

    # Handle owl:Restriction
    restriction = element.find("owl:Restriction", namespace_map)
    if restriction is not None:
        on_property = restriction.find("owl:onProperty", namespace_map)
        some_values_from = restriction.find("owl:someValuesFrom", namespace_map)

        on_property_id = on_property.get(rdf_resource) if on_property is not None else None
        some_values_from_id = (
            some_values_from.get(rdf_resource) if some_values_from is not None else None
        )

        parsed_data.append(
            {
                "onProperty": on_property_id,
                "someValuesFrom": some_values_from_id,
            }
        )

    return parsed_data
