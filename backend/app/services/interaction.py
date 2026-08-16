import sqlite3
from datetime import datetime

from app.core.sentinels import UNSET
from app.domain.errors import (
    InteractionNotFoundError,
    InvalidInteractionTypeError,
    PersonNotFoundError,
    RelationshipNotFoundError,
)
from app.repositories.interaction import InteractionRepository
from app.repositories.person import PersonRepository
from app.repositories.relationship import RelationshipRepository


VALID_INTERACTION_TYPES = {
    "message",
    "call",
    "meeting",
    "date",
    "gift",
    "other",
}


class InteractionService:
    def __init__(
        self,
        repository: InteractionRepository | None = None,
        person_repository: PersonRepository | None = None,
        relationship_repository: RelationshipRepository | None = None,
    ):
        self.repository = repository or InteractionRepository()
        self.person_repository = (
            person_repository or PersonRepository()
        )
        self.relationship_repository = (
            relationship_repository or RelationshipRepository()
        )

    def _validate_type(self, interaction_type: str) -> None:
        if interaction_type not in VALID_INTERACTION_TYPES:
            raise InvalidInteractionTypeError(
                f"Invalid interaction type: {interaction_type}"
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
        interaction_type: str,
        occurred_at: datetime,
        content: str | None,
    ) -> sqlite3.Row:
        self._validate_type(interaction_type)

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
            interaction_type,
            occurred_at.isoformat(),
            content,
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
        interaction_id: str,
    ) -> sqlite3.Row:
        interaction = self.repository.get(
            conn,
            user_id,
            interaction_id,
        )

        if interaction is None:
            raise InteractionNotFoundError(
                "Interaction not found"
            )

        return interaction

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        interaction_id: str,
        relationship_id=UNSET,
        interaction_type=UNSET,
        occurred_at=UNSET,
        content=UNSET,
    ) -> sqlite3.Row:
        existing = self.get(
            conn,
            user_id,
            interaction_id,
        )

        if interaction_type is not UNSET:
            if interaction_type is None:
                raise InvalidInteractionTypeError(
                    "Interaction type cannot be null"
                )
            self._validate_type(interaction_type)

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
            interaction_id,
            relationship_id,
            interaction_type,
            occurred_at.isoformat()
            if occurred_at is not UNSET and occurred_at is not None
            else occurred_at,
            content,
        )

        if updated is None:
            raise InteractionNotFoundError(
                "Interaction not found"
            )

        return updated

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        interaction_id: str,
    ) -> bool:
        deleted = self.repository.delete(
            conn,
            user_id,
            interaction_id,
        )

        if not deleted:
            raise InteractionNotFoundError(
                "Interaction not found"
            )

        return True
