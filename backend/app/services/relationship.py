from __future__ import annotations

import sqlite3

from app.core.sentinels import UNSET
from app.domain.errors import (
    PersonNotFoundError,
    RelationshipAlreadyExistsError,
)
from app.repositories.relationship import RelationshipRepository


class RelationshipService:
    def __init__(
        self,
        repository: RelationshipRepository | None = None,
    ):
        self.repository = repository or RelationshipRepository()

    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        status: str,
        stage: str,
        long_term_goal: str | None,
        current_goal: str | None,
        notes: str | None,
        intent: str = "unsure",
    ) -> sqlite3.Row:
        person = conn.execute(
            """
            SELECT id
            FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (person_id, user_id),
        ).fetchone()

        if person is None:
            raise PersonNotFoundError("Person not found")

        try:
            return self.repository.create(
                conn,
                user_id,
                person_id,
                status,
                stage,
                long_term_goal,
                current_goal,
                notes,
                intent,
            )
        except sqlite3.IntegrityError as exc:
            error_message = str(exc)

            if (
                "UNIQUE constraint failed: "
                "relationships.user_id, relationships.person_id"
                in error_message
            ):
                raise RelationshipAlreadyExistsError(
                    "Relationship already exists for this person"
                ) from exc

            raise

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> list[sqlite3.Row]:
        return self.repository.list(conn, user_id)

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
    ) -> sqlite3.Row | None:
        return self.repository.get(
            conn,
            user_id,
            relationship_id,
        )

    def set_intent_many(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_ids: list[str],
        intent: str,
    ) -> list[sqlite3.Row]:
        """Set the same chat intent on several people in one go.

        Missing relationship rows are created rather than skipped, so "select
        eight people, set 长期恋爱" also works for brand-new contacts.
        """
        rows: list[sqlite3.Row] = []
        for person_id in person_ids:
            person = conn.execute(
                "SELECT id FROM persons WHERE id = ? AND user_id = ?",
                (person_id, user_id),
            ).fetchone()
            if person is None:
                continue
            existing = conn.execute(
                "SELECT id FROM relationships WHERE user_id = ? AND person_id = ?",
                (user_id, person_id),
            ).fetchone()
            if existing is None:
                row = self.create(
                    conn, user_id, person_id, "unknown", "unknown",
                    None, None, None, intent,
                )
            else:
                row = self.update(
                    conn, user_id, existing["id"],
                    UNSET, UNSET, UNSET, UNSET, UNSET, intent,
                )
            if row is not None:
                rows.append(row)
        conn.commit()
        return rows

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
        status=UNSET,
        stage=UNSET,
        long_term_goal=UNSET,
        current_goal=UNSET,
        notes=UNSET,
        intent=UNSET,
    ) -> sqlite3.Row | None:
        return self.repository.update(
            conn,
            user_id,
            relationship_id,
            status,
            stage,
            long_term_goal,
            current_goal,
            notes,
            intent,
        )

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
    ) -> bool:
        return self.repository.delete(
            conn,
            user_id,
            relationship_id,
        )
