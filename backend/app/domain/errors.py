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


class ConversationNotFoundError(DomainError):
    """Raised when a conversation does not exist for the current user."""


class InvalidConversationStatusError(DomainError, ValueError):
    """Raised when a conversation status is invalid."""


class MessageNotFoundError(DomainError):
    """Raised when a message does not exist for the current user."""


class InvalidMessageSenderTypeError(DomainError, ValueError):
    """Raised when a message sender type is invalid."""
