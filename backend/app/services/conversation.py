import sqlite3

from app.core.sentinels import UNSET
from app.domain.errors import (
    ConversationNotFoundError,
    InvalidConversationStatusError,
    PersonNotFoundError,
    RelationshipNotFoundError,
)
from app.repositories.conversation import ConversationRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository


VALID_CONVERSATION_STATUSES = {
    "active",
    "archived",
}


class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository | None = None,
        person_repository: PersonRepository | None = None,
        relationship_repository: RelationshipRepository | None = None,
    ):
        self.repository = repository or ConversationRepository()
        self.person_repository = (
            person_repository or PersonRepository()
        )
        self.relationship_repository = (
            relationship_repository or RelationshipRepository()
        )

    def _validate_status(self, status: str) -> None:
        if status not in VALID_CONVERSATION_STATUSES:
            raise InvalidConversationStatusError(
                f"Invalid conversation status: {status}"
            )

    def _validate_person(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> None:
        person = self.person_repository.get(
            conn,
            user_id,
            person_id,
        )

        if person is None:
            raise PersonNotFoundError("Person not found")

    def _validate_relationship(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        relationship_id: str,
    ) -> None:
        relationship = self.relationship_repository.get(
            conn,
            user_id,
            relationship_id,
        )

        if relationship is None:
            raise RelationshipNotFoundError(
                "Relationship not found"
            )

        if relationship["person_id"] != person_id:
            raise RelationshipNotFoundError(
                "Relationship not found"
            )

    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        relationship_id: str | None,
        title: str | None,
        status: str,
    ) -> sqlite3.Row:
        self._validate_status(status)

        self._validate_person(
            conn,
            user_id,
            person_id,
        )

        if relationship_id is not None:
            self._validate_relationship(
                conn,
                user_id,
                person_id,
                relationship_id,
            )

        return self.repository.create(
            conn,
            user_id,
            person_id,
            relationship_id,
            title,
            status,
        )

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str | None = None,
    ) -> list[sqlite3.Row]:
        if person_id is not None:
            self._validate_person(
                conn,
                user_id,
                person_id,
            )

        return self.repository.list(
            conn,
            user_id,
            person_id,
        )

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> sqlite3.Row:
        conversation = self.repository.get(
            conn,
            user_id,
            conversation_id,
        )

        if conversation is None:
            raise ConversationNotFoundError(
                "Conversation not found"
            )

        return conversation

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        relationship_id=UNSET,
        title=UNSET,
        status=UNSET,
    ) -> sqlite3.Row:
        existing = self.get(
            conn,
            user_id,
            conversation_id,
        )

        if status is not UNSET:
            if status is None:
                raise InvalidConversationStatusError(
                    "Conversation status cannot be null"
                )

            self._validate_status(status)

        if relationship_id is not UNSET:
            if relationship_id is not None:
                self._validate_relationship(
                    conn,
                    user_id,
                    existing["person_id"],
                    relationship_id,
                )

        updated = self.repository.update(
            conn,
            user_id,
            conversation_id,
            relationship_id,
            title,
            status,
        )

        if updated is None:
            raise ConversationNotFoundError(
                "Conversation not found"
            )

        return updated

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        deleted = self.repository.delete(
            conn,
            user_id,
            conversation_id,
        )

        if not deleted:
            raise ConversationNotFoundError(
                "Conversation not found"
            )

        return True
