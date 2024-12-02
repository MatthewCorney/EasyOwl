from collections import defaultdict
from typing import Dict, List, Tuple, Any
from lxml import etree
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class OntologyParser:
    def __init__(self, file_path: str):
        """
        Initialize the OntologyParser by parsing the OWL file and building the subclass map.
        # Example Usage

    parser = OntologyParser(f"data/aero.owl")

    parents = parser.get_parents('http://www.ebi.ac.uk/efo/EFO_0005634', max_depth=-1)
    pprint(parents)

    children = parser.get_children('http://www.ebi.ac.uk/efo/EFO_0005634', max_depth=-1)
    pprint(children)

    res=parser.entities['http://www.ebi.ac.uk/efo/EFO_0005634']

    pprint(res)

    similar_terms = parser.get_similar_terms(res['properties']["label"], threshold=0.6)
    pprint(similar_terms)

    similar_terms = parser.get_similar_terms(res['properties']["label"], n=5)
    pprint(similar_terms)

        :param file_path: Path to the OWL file.
        """
        self.file_path = file_path
        self.entities: Dict[str, dict] = {}
        self.relations: List[dict] = []
        self.subclass_map: Dict = {}
        self.name_ids: Dict = {}
        self.index_name: Dict = {}
        self.name_index: Dict = {}
        # Parse the OWL file and build the subclass map
        self.entities, self.relations, _, self.namespace_map = self.parse_owl(self.file_path)
        self.subclass_map = self.build_subclass_map()

        # Set up mapping dictionaries for name vectorisation
        self.name_ids, self.index_name, self.name_index = self.get_name_label()
        self.similarity_matrix = None

    @staticmethod
    def extract_synonyms(element, namespace_map: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Extract synonyms (exact, narrow, broad) for an OWL entity.

        :param element: XML element to parse.
        :param namespace_map: Namespace mapping from the OWL file.
        :return: Dictionary of synonyms categorized by type.
        """
        synonyms = {}
        for synonym_type in ['hasExactSynonym', 'hasNarrowSynonym', 'hasBroadSynonym']:
            synonyms[synonym_type] = [
                synonym.text.strip() for synonym in element.findall(f'oboInOwl:{synonym_type}', namespace_map)
                if synonym.text is not None
            ]
        return synonyms

    @staticmethod
    def extract_matches(element, namespace_map: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Extract match types (exact, close, narrow, broad) for an OWL entity.

        :param element: XML element to parse.
        :param namespace_map: Namespace mapping from the OWL file.
        :return: Dictionary of matches categorized by type.
        """
        matches = {}

        # Check if 'skos' prefix exists in the namespace map
        skos_prefix = namespace_map.get('skos')
        if not skos_prefix:
            # Return an empty dictionary if 'skos' is not in the namespace map
            return matches

        # Extract match types if 'skos' prefix is available
        for match_type in ['exactMatch', 'closeMatch', 'narrowMatch', 'broadMatch']:
            matches[match_type] = [
                match.get(f"{{{skos_prefix}}}resource")
                for match in element.findall(f'skos:{match_type}', namespace_map)
            ]
        return matches

    @staticmethod
    def extract_properties(element, namespace_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract all properties of an OWL entity.

        :param element: XML element to parse.
        :param namespace_map: Namespace mapping from the OWL file.
        :return: Dictionary of extracted properties.
        """
        properties = {}
        for child in element:
            # Extract tag and namespace
            tag = child.tag.split('}')[-1]
            namespace = child.tag.split('}')[0][1:]

            # Check if the tag belongs to the known namespaces
            if namespace in namespace_map.values():
                # Handle multiple values for the same property
                if tag not in properties:
                    properties[tag] = []
                if child.text:
                    properties[tag].append(child.text.strip())
                # Capture resource attributes if present
                resource = child.get(f"{{{namespace_map['rdf']}}}resource")
                if resource:
                    properties[tag].append(resource)

        # Collapse single-value lists to just the value
        for key in properties:
            if len(properties[key]) == 1:
                properties[key] = properties[key][0]

        return properties

    def parse_owl(self, file_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[str], Dict[str, str]]:
        """
        Parse the OWL file to extract entities, relations, disjoint classes, and namespaces.

        :param file_path: Path to the OWL file.
        :return: Entities, relations, disjoint classes, and namespace map.
        """
        # Parse the OWL file
        tree = etree.parse(file_path)
        root = tree.getroot()

        # Extract namespaces from the root element
        namespace_map = {key: value for key, value in root.nsmap.items() if value}

        # Initialize results
        entities = {}
        relations = []
        disjoints = []

        # Extract entities (classes)
        for owl_class in root.findall('owl:Class', namespace_map):
            entity_id = owl_class.get(f"{{{namespace_map['rdf']}}}about")
            if entity_id:
                properties = self.extract_properties(owl_class, namespace_map)

                # Extract subclasses
                subclasses = []
                for subclass in owl_class.findall('rdfs:subClassOf', namespace_map):
                    # Direct reference to another class
                    subclass_ref = subclass.get(f"{{{namespace_map['rdf']}}}resource")
                    if subclass_ref:
                        subclasses.append(subclass_ref)
                    else:
                        # Nested restriction or intersection
                        subclasses.append(self.parse_restriction_or_intersection(subclass, namespace_map))

                # Extract disjoint classes
                disjoints.extend([
                    disjoint.get(f"{{{namespace_map['rdf']}}}resource")
                    for disjoint in owl_class.findall('owl:disjointWith', namespace_map)
                ])

                # Add entity to the dictionary
                entities[entity_id] = {
                    'properties': properties,
                    'subclasses': subclasses,
                    'disjoints': [],
                    'synonyms': self.extract_synonyms(owl_class, namespace_map),
                    'matches': self.extract_matches(owl_class, namespace_map)
                }

        # Extract relations (object properties)
        for obj_prop in root.findall('owl:ObjectProperty', namespace_map):
            predicate = obj_prop.get(f"{{{namespace_map['rdf']}}}about")
            if predicate:
                # Extract domain and range
                domain_elem = obj_prop.find('rdfs:domain', namespace_map)
                range_elem = obj_prop.find('rdfs:range', namespace_map)
                domain = domain_elem.get(f"{{{namespace_map['rdf']}}}resource") if domain_elem is not None else None
                range_ = range_elem.get(f"{{{namespace_map['rdf']}}}resource") if range_elem is not None else None

                # Extract child elements as properties
                properties = {
                    child.tag.split('}')[-1]: child.text.strip()
                    for child in obj_prop if child.text
                }
                relations.append({
                    'predicate': predicate,
                    'domain': domain,
                    'range': range_,
                    'properties': properties
                })

        return entities, relations, disjoints, namespace_map

    def get_name_label(self):
        exact_name = {x['properties']['id']: x["properties"].get("label") for x in list(self.entities.values()) if
                      x['properties'].get("id") is not None}
        synonymy = {x['properties']['id']: x["properties"].get("hasExactSynonym") for x in
                    list(self.entities.values()) if
                    x['properties'].get("id") is not None}
        name_ids = {}
        for id_value, name in exact_name.items():
            if name not in name_ids:
                name_ids[name] = set()
            name_ids[name].add(id_value)
        for id_value, names in synonymy.items():
            if names is None:
                continue
            for name in names:
                if name not in name_ids:
                    name_ids[name] = set()
                name_ids[name].add(id_value)
        self.name_ids = name_ids
        name_index = {v: k for k, v in enumerate(list(self.name_ids.keys()))}
        index_name = {v: k for k, v in name_index.items()}
        self.index_name = index_name
        self.name_index = name_index
        return name_ids, index_name, name_index

    def vectorise_labels(self):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(list(self.name_ids.keys()))
        similarity_matrix = cosine_similarity(tfidf_matrix, dense_output=False)
        self.similarity_matrix = similarity_matrix

    def build_subclass_map(self):
        """

        :return:
        """
        subclass_map = defaultdict(set)

        # Iterate through the entities to populate the subclass map
        for entity_id, entity_data in self.entities.items():
            for subclass in entity_data.get('subclasses', set()):
                if isinstance(subclass, str):
                    subclass_map[entity_id].add(subclass)
                elif isinstance(subclass, list):
                    for subclass_str in [x for x in subclass if isinstance(x, str)]:
                        subclass_map[entity_id].add(subclass_str)
                elif isinstance(subclass, set):
                    for subclass_str in [x for x in subclass if isinstance(x, str)]:
                        subclass_map[entity_id].add(subclass_str)

        return subclass_map

    def get_parents(self, entity_id, max_depth, cache=None, current_depth=0):
        """
        Recursively find all subclasses of the given entity up to the specified depth.

        :param entity_id: The ID of the entity to start from.
        :param max_depth: The maximum depth to recurse.
        :param cache: A cache dictionary to store already computed subclasses (for memoization).
        :param current_depth: The current depth of recursion (default is 0).
        :return: A list of subclass IDs up to the specified depth.
        """
        if max_depth == -1:
            max_depth = float("inf")
        if current_depth > max_depth:
            return []
        elif current_depth > 1000:
            raise Exception
        if cache is None:
            cache = {}

        if entity_id in cache:
            return cache[entity_id]

        subclasses = set()

        if entity_id in self.subclass_map:
            subclasses.add(entity_id)
            for subclass in self.subclass_map[entity_id]:
                subclasses.update(self.get_parents(subclass, max_depth, cache, current_depth + 1))

        cache[entity_id] = list(subclasses)
        return list(subclasses)

    def get_children(self, entity_id, max_depth, cache=None, current_depth=0):
        """
        Recursively find all child terms of the given entity up to the specified depth.

        :param entity_id: The ID of the entity to start from.
        :param max_depth: The maximum depth to recurse.
        :param cache: A cache dictionary to store already computed children (for memoization).
        :param current_depth: The current depth of recursion (default is 0).
        :return: A list of child term IDs up to the specified depth.
        """
        if max_depth == -1:
            max_depth = float("inf")
        if current_depth > max_depth:
            return []
        elif current_depth > 1000:
            raise Exception
        if cache is None:
            cache = {}

        if entity_id in cache:
            return cache[entity_id]

        children = set()

        for other_id, subclasses in self.subclass_map.items():
            if entity_id in subclasses:
                children.add(other_id)
                children.update(self.get_children(other_id, max_depth, cache, current_depth + 1))

        cache[entity_id] = list(children)
        return list(children)

    def parse_restriction_or_intersection(self, element, namespace_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Parse an owl:Restriction or owl:intersectionOf structure.

        :param element: XML element to parse.
        :param namespace_map: Namespace mapping.
        :return: Parsed restriction or intersection data.
        """
        parsed_data = []

        # Handle owl:intersectionOf
        intersection = element.find('owl:intersectionOf', namespace_map)
        if intersection is not None:
            # Check if it's a collection
            if intersection.get(f"{{{namespace_map['rdf']}}}parseType") == "Collection":
                for item in intersection:
                    if item.tag.endswith('Description') or 'Restriction' in item.tag:
                        parsed_data.extend(self.parse_restriction_or_intersection(item, namespace_map))
            return parsed_data

        # Handle owl:Restriction
        restriction = element.find('owl:Restriction', namespace_map)
        if restriction is not None:
            on_property = restriction.find('owl:onProperty', namespace_map)
            some_values_from = restriction.find('owl:someValuesFrom', namespace_map)

            on_property_id = on_property.get(f"{{{namespace_map['rdf']}}}resource") if on_property is not None else None
            some_values_from_id = some_values_from.get(
                f"{{{namespace_map['rdf']}}}resource") if some_values_from is not None else None

            parsed_data.append({
                'onProperty': on_property_id,
                'someValuesFrom': some_values_from_id
            })
            return parsed_data

        return parsed_data

    def get_entity_relations(self, entity_id: str):
        """

        :param entity_id:
        :return:
        """
        relationships = {"subclasses": set(), "superclasses": set(), "relationships": []}
        # Include all subclasses and superclasses
        subclasses = set(self.get_children(entity_id, max_depth=1))
        superclasses = set(self.get_parents(entity_id, max_depth=1))
        relationships['subclasses'].update(subclasses)
        relationships['superclasses'].update(superclasses)
        for relation in self.relations:
            if (relation.get('domain') == entity_id or
                    relation.get('range') == entity_id or
                    entity_id in relation.get('properties', {}).values()):
                relationships["relationships"].append(relation)
        return relationships

    def get_similar_terms(self, term, n=None, threshold=None):
        """
        Retrieve terms similar to a given index, either by top N most similar or by a similarity threshold.
        """
        query_index = self.name_index[term]
        if self.similarity_matrix is None:
            self.vectorise_labels()

        # Efficient row slicing in CSR format
        row_start = self.similarity_matrix.indptr[query_index]
        row_end = self.similarity_matrix.indptr[query_index + 1]
        similar_terms = list(zip(self.similarity_matrix.indices[row_start:row_end],
                                 self.similarity_matrix.data[row_start:row_end]))

        # Apply threshold filter
        if threshold is not None:
            similar_terms = ((col, score) for col, score in similar_terms if score > threshold)

        # Apply top-N selection
        if n is not None:
            from heapq import nlargest
            similar_terms = nlargest(n, similar_terms, key=lambda x: x[1])
        else:
            similar_terms = sorted(similar_terms, key=lambda x: x[1], reverse=True)

        # Prepare return object
        name_cache = self.index_name
        id_cache = self.name_ids
        return [
            {'name': name_cache[idx], 'ids': id_cache[name_cache[idx]], 'score': float(score)}
            for idx, score in similar_terms
        ]