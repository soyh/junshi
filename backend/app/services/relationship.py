import sqlite3

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
            raise ValueError("Person not found")

        return self.repository.create(
            conn,
            user_id,
            person_id,
            status,
            stage,
            long_term_goal,
            current_goal,
            notes,
        )

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

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        relationship_id: str,
        status: str | None,
        stage: str | None,
        long_term_goal: str | None,
        current_goal: str | None,
        notes: str | None,
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
