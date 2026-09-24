from __future__ import annotations

import sqlite3

from app.domain.errors import (
    ConversationNotFoundError,
    InvalidMessageSenderTypeError,
    MessageNotFoundError,
    ProtectedMessageError,
)
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository


VALID_MESSAGE_SENDER_TYPES = {
    "user",
    "person",
    "system",
    "assistant",
}

USER_MANAGED_MESSAGE_SENDER_TYPES = {
    "user",
    "person",
    "assistant",
}

_RESERVED_SYSTEM_MESSAGE_DETAIL = (
    "System messages are reserved for internal canonical evidence"
)
_INTERNAL_SYSTEM_MESSAGE_DETAIL = (
    "System messages must be managed through their owning internal workflow"
)


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

    def _validate_user_managed_sender_type(
        self,
        sender_type: str,
    ) -> None:
        self._validate_sender_type(sender_type)
        if sender_type not in USER_MANAGED_MESSAGE_SENDER_TYPES:
            raise InvalidMessageSenderTypeError(
                _RESERVED_SYSTEM_MESSAGE_DETAIL
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

    def _ensure_mutable(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> None:
        getter = getattr(
            self.repository,
            "get_linked_media_attachment",
            None,
        )
        if not callable(getter):
            return
        linked = getter(conn, user_id, message_id)
        if linked is not None:
            raise ProtectedMessageError(
                "Media evidence messages must be managed through the media attachment"
            )

    @staticmethod
    def _ensure_user_managed_message(current: sqlite3.Row | dict) -> None:
        if current["sender_type"] == "system":
            raise ProtectedMessageError(
                _INTERNAL_SYSTEM_MESSAGE_DETAIL
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
        """Create a canonical message for trusted internal workflows."""
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

    def create_user_managed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        sender_type: str,
        content: str,
        sent_at: str | None,
    ) -> sqlite3.Row:
        """Create a message through the user-managed Message API boundary."""
        self._validate_user_managed_sender_type(sender_type)
        return self.create(
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
        """Update a canonical message for trusted internal workflows."""
        current = self.get(conn, user_id, message_id)
        self._ensure_mutable(conn, user_id, message_id)
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

    def update_user_managed(
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
        """Update only messages owned by the user-managed Message API."""
        current = self.get(conn, user_id, message_id)
        self._ensure_mutable(conn, user_id, message_id)
        self._ensure_user_managed_message(current)
        fields_set = fields_set or set()
        if "sender_type" in fields_set and sender_type is not None:
            self._validate_user_managed_sender_type(sender_type)
        return self.update(
            conn,
            user_id,
            message_id,
            sender_type=sender_type,
            content=content,
            sent_at=sent_at,
            fields_set=fields_set,
        )

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> bool:
        """Delete a canonical message for trusted internal workflows."""
        self.get(conn, user_id, message_id)
        self._ensure_mutable(conn, user_id, message_id)
        deleted = self.repository.delete(conn, user_id, message_id)
        if not deleted:
            raise MessageNotFoundError("Message not found")
        return True

    def delete_user_managed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        message_id: str,
    ) -> bool:
        """Delete only messages owned by the user-managed Message API."""
        current = self.get(conn, user_id, message_id)
        self._ensure_mutable(conn, user_id, message_id)
        self._ensure_user_managed_message(current)
        deleted = self.repository.delete(conn, user_id, message_id)
        if not deleted:
            raise MessageNotFoundError("Message not found")
        return True
