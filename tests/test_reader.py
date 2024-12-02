import numpy as np
import pytest
from scipy.stats import fisher_exact
from easyowl.reader import OntologyParser
import os

# Define the directory containing the test ontology files
TEST_ONTOLOGY_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.parametrize("ontology_file", [
    os.path.join(TEST_ONTOLOGY_DIR, file) for file in os.listdir(TEST_ONTOLOGY_DIR) if file.endswith(".owl")
])
def test_ontology_parsing(ontology_file: str):
    """
    Test that each ontology file in the test_ontologies directory can be read
    and produces a list of entities longer than 100.
    """
    # Initialize the parser
    parser = OntologyParser(ontology_file)

    # Check that the entities dictionary has more than 100 keys
    assert len(parser.entities) > 100, f"File {ontology_file} has less than 100 entities."
