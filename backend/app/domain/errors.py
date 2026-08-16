class DomainError(Exception):
    """Base class for application domain errors."""


class PersonNotFoundError(DomainError, ValueError):
    """Raised when a person does not exist for the current user."""


class RelationshipAlreadyExistsError(DomainError):
    """Raised when a relationship already exists for the person."""
