import sqlite3
import uuid
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PersonRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        name: str,
        nickname: str | None,
        notes: str | None,
    ) -> sqlite3.Row:
        person_id = str(uuid.uuid4())
        now = utc_now()

        conn.execute(
            """
            INSERT INTO persons (
                id,
                user_id,
                name,
                nickname,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                user_id,
                name,
                nickname,
                notes,
                now,
                now,
            ),
        )

        return conn.execute(
            "SELECT * FROM persons WHERE id = ? AND user_id = ?",
            (person_id, user_id),
        ).fetchone()

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM persons
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (person_id, user_id),
        ).fetchone()

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        name: str | None,
        nickname: str | None,
        notes: str | None,
    ) -> sqlite3.Row | None:
        existing = self.get(conn, user_id, person_id)

        if existing is None:
            return None

        new_name = name if name is not None else existing["name"]
        new_nickname = (
            nickname if nickname is not None else existing["nickname"]
        )
        new_notes = notes if notes is not None else existing["notes"]

        conn.execute(
            """
            UPDATE persons
            SET name = ?,
                nickname = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                new_name,
                new_nickname,
                new_notes,
                utc_now(),
                person_id,
                user_id,
            ),
        )

        return self.get(conn, user_id, person_id)

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> bool:
        cursor = conn.execute(
            """
            DELETE FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (person_id, user_id),
        )

        return cursor.rowcount > 0
