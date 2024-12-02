import requests
import os

from typing import Optional
from src.easyowl.settings import logger


def download_ontology(url: str, destination_dir: str = "data", name: Optional[str] = None):
    """
    Downloads a given ontology file

    # Example usage
    base_urls = [
        "http://purl.obolibrary.org/obo/aero.owl",
        "http://purl.obolibrary.org/obo/uberon.owl",
        "http://purl.obolibrary.org/obo/caro.owl",
        "http://purl.obolibrary.org/obo/hp.owl",

    ]
    for i in base_urls:
        download_ontology(url=i, destination_dir="data")

    :param url: Url to the ontology file
    :param destination_dir: Directory to save the file
    :param name: Optional name to give to the file
    :return:
    """
    if name:
        filename = name
    else:
        filename = url.split("/")[-1]
    os.makedirs(destination_dir, exist_ok=True)
    file_path = os.path.join(destination_dir, filename)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):  # Write in chunks
                file.write(chunk)
        logger.info(f"File downloaded successfully and saved to: {file_path}")
    except requests.exceptions.RequestException as e:
        logger.info(f"An error occurred: {e}")


base_urls = [
    "http://purl.obolibrary.org/obo/bao.owl",
    "http://purl.obolibrary.org/obo/doid.owl",
    "http://purl.obolibrary.org/obo/chebi.owl",
    "http://purl.obolibrary.org/obo/hp.owl",

]
for i in base_urls:
    download_ontology(url=i, destination_dir="data")