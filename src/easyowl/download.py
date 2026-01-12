"""Download utilities for fetching ontology files from URLs."""

import logging
from pathlib import Path

import requests

from easyowl.constants import DOWNLOAD_CHUNK_SIZE, DOWNLOAD_TIMEOUT_SECONDS
from easyowl.exceptions import DownloadError

logger = logging.getLogger(__name__)


def download_ontology(
    url: str,
    destination_dir: str | Path = "data",
    *,
    filename: str | None = None,
) -> Path:
    """
    Download an ontology file from a URL.

    Parameters
    ----------
    url : str
        URL of the ontology file to download.
    destination_dir : str | Path, default="data"
        Directory to save the downloaded file.
    filename : str | None, default=None
        Name for the downloaded file. If None, uses the filename from the URL.

    Returns
    -------
    Path
        Path to the downloaded file.

    Raises
    ------
    ValueError
        If the URL is invalid or the filename contains unsafe characters.
    DownloadError
        If the download fails due to network errors.

    Examples
    --------
    >>> path = download_ontology("http://purl.obolibrary.org/obo/hp.owl")
    >>> path = download_ontology(
    ...     "http://purl.obolibrary.org/obo/hp.owl",
    ...     destination_dir="ontologies",
    ...     filename="human_phenotype.owl",
    ... )
    """
    # Validate URL
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL scheme (must be http or https): {url}")

    # Determine filename
    resolved_filename = filename if filename else url.split("/")[-1]

    # Validate filename for safety
    if not resolved_filename:
        raise ValueError(f"Could not determine filename from URL: {url}")

    unsafe_chars = {".", "/", "\\"}
    if ".." in resolved_filename or any(c in resolved_filename for c in unsafe_chars if c != "."):
        raise ValueError(f"Unsafe characters in filename: {resolved_filename}")

    # Ensure destination directory exists
    dest_path = Path(destination_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    file_path = dest_path / resolved_filename

    # Check for existing file
    if file_path.exists():
        logger.warning("File already exists, overwriting: %s", file_path)

    # Download the file
    try:
        response = requests.get(
            url,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        with file_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)

        logger.info("Downloaded ontology to: %s", file_path)

    except requests.exceptions.Timeout as e:
        raise DownloadError(f"Download timed out after {DOWNLOAD_TIMEOUT_SECONDS}s: {url}") from e

    except requests.exceptions.ConnectionError as e:
        raise DownloadError(f"Connection failed for URL: {url}") from e

    except requests.exceptions.HTTPError as e:
        raise DownloadError(f"HTTP error {e.response.status_code} for URL: {url}") from e

    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Download failed: {url}") from e

    except OSError as e:
        raise DownloadError(f"Failed to write file to {file_path}") from e

    return file_path
