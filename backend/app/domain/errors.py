class DomainError(Exception):
    """Base class for application domain errors."""


class PersonNotFoundError(DomainError, ValueError):
    """Raised when a person does not exist for the current user."""


class RelationshipAlreadyExistsError(DomainError):
    """Raised when a relationship already exists for the person."""


class RelationshipNotFoundError(DomainError):
    """Raised when a relationship does not exist for the current user."""


class InteractionNotFoundError(DomainError):
    """Raised when an interaction does not exist for the current user."""


class InvalidInteractionTypeError(DomainError, ValueError):
    """Raised when an interaction type is invalid."""
