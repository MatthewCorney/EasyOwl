from pathlib import Path

import pytest

from easyowl.reader import OntologyParser

TEST_ONTOLOGY_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "ontology_file",
    [
        str(TEST_ONTOLOGY_DIR / file)
        for file in TEST_ONTOLOGY_DIR.iterdir()
        if file.suffix == ".owl"
    ],
)
def test_ontology_parsing(ontology_file: str) -> None:
    """
    Test that each ontology file in the test_ontologies directory can be read
    and produces a list of entities longer than 100.
    """
    parser = OntologyParser(ontology_file)
    assert len(parser.entities) > 100, f"File {ontology_file} has less than 100 entities."
