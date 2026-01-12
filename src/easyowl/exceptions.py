"""Custom exceptions for the EasyOwl package."""


class EasyOwlError(Exception):
    """
    Base exception for all EasyOwl errors.

    All exceptions raised by EasyOwl inherit from this class,
    allowing users to catch all EasyOwl-related errors with a single handler.
    """


class OntologyParseError(EasyOwlError):
    """
    Raised when an ontology file cannot be parsed.

    This may occur due to:
    - File not found
    - Invalid XML syntax
    - Missing required OWL namespaces
    """


class EntityNotFoundError(EasyOwlError):
    """
    Raised when a requested entity ID is not found in the ontology.

    Parameters
    ----------
    entity_id : str
        The entity ID that was not found.
    """

    def __init__(self, entity_id: str) -> None:
        self.entity_id = entity_id
        super().__init__(f"Entity not found: {entity_id}")


class TermNotFoundError(EasyOwlError):
    """
    Raised when a term label is not found in the ontology index.

    Parameters
    ----------
    term : str
        The term that was not found.
    """

    def __init__(self, term: str) -> None:
        self.term = term
        super().__init__(f"Term not found: {term}")


class DownloadError(EasyOwlError):
    """
    Raised when an ontology file download fails.

    This may occur due to:
    - Network errors
    - Invalid URL
    - Server errors
    """
