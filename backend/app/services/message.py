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
        self._validate_conversation(conn, user_id, conversation_id)
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
        """Return the complete canonical history for analysis and internal services."""
        self._validate_conversation(conn, user_id, conversation_id)
        return self.repository.list(conn, user_id, conversation_id)

    def list_window(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        before: str | None = None,
        limit: int = 100,
    ) -> list[sqlite3.Row]:
        """Return a bounded display window without truncating canonical history."""
        self._validate_conversation(conn, user_id, conversation_id)
        return self.repository.list_window(
            conn,
            user_id,
            conversation_id,
            from_time=from_time,
            to_time=to_time,
            before=before,
            limit=limit,
        )

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> sqlite3.Row:
        message = self.repository.get(conn, user_id, message_id)
        if message is None:
            raise MessageNotFoundError("Message not found")
        return message

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
        *,
        sender_type: str | None = None,
        content: str | None = None,
        sent_at: str | None = None,
        fields_set: set[str] | None = None,
    ) -> sqlite3.Row:
        current = self.get(conn, user_id, message_id)
        fields_set = fields_set or set()
        next_sender = sender_type if "sender_type" in fields_set else current["sender_type"]
        next_content = content if "content" in fields_set else current["content"]
        next_sent_at = sent_at if "sent_at" in fields_set else current["sent_at"]
        if next_sender is None or next_content is None or next_sent_at is None:
            raise ValueError("Message fields cannot be null")
        self._validate_sender_type(next_sender)
        if not str(next_content).strip():
            raise ValueError("Message content cannot be empty")
        updated = self.repository.update(
            conn,
            user_id,
            message_id,
            sender_type=next_sender,
            content=next_content,
            sent_at=next_sent_at,
        )
        if updated is None:
            raise MessageNotFoundError("Message not found")
        return updated

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> bool:
        deleted = self.repository.delete(conn, user_id, message_id)
        if not deleted:
            raise MessageNotFoundError("Message not found")
        return True
