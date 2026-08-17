import sqlite3

from app.domain.errors import (
    ConversationNotFoundError,
    InvalidMessageSenderTypeError,
    MessageNotFoundError,
)
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository


VALID_MESSAGE_SENDER_TYPES = {
    "user",
    "person",
    "system",
    "assistant",
}


class MessageService:
    def __init__(
        self,
        repository: MessageRepository | None = None,
        conversation_repository: ConversationRepository | None = None,
    ):
        self.repository = repository or MessageRepository()
        self.conversation_repository = (
            conversation_repository
            or ConversationRepository()
        )

    def _validate_sender_type(
        self,
        sender_type: str,
    ) -> None:
        if sender_type not in VALID_MESSAGE_SENDER_TYPES:
            raise InvalidMessageSenderTypeError(
                f"Invalid message sender type: {sender_type}"
            )

    def _validate_conversation(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> None:
        conversation = self.conversation_repository.get(
            conn,
            user_id,
            conversation_id,
        )

        if conversation is None:
            raise ConversationNotFoundError(
                "Conversation not found"
            )

    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        sender_type: str,
        content: str,
        sent_at: str | None,
    ) -> sqlite3.Row:
        self._validate_sender_type(sender_type)

        self._validate_conversation(
            conn,
            user_id,
            conversation_id,
        )

        return self.repository.create(
            conn,
            user_id,
            conversation_id,
            sender_type,
            content,
            sent_at,
        )

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> list[sqlite3.Row]:
        self._validate_conversation(
            conn,
            user_id,
            conversation_id,
        )

        return self.repository.list(
            conn,
            user_id,
            conversation_id,
        )

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> sqlite3.Row:
        message = self.repository.get(
            conn,
            user_id,
            message_id,
        )

        if message is None:
            raise MessageNotFoundError(
                "Message not found"
            )

        return message

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> bool:
        deleted = self.repository.delete(
            conn,
            user_id,
            message_id,
        )

        if not deleted:
            raise MessageNotFoundError(
                "Message not found"
            )

        return True
