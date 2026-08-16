import sqlite3

from app.repositories.person import PersonRepository


class PersonService:
    def __init__(self, repository: PersonRepository | None = None):
        self.repository = repository or PersonRepository()

    def create(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        name: str,
        nickname: str | None,
        notes: str | None,
    ) -> sqlite3.Row:
        return self.repository.create(
            conn,
            user_id,
            name,
            nickname,
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
        person_id: str,
    ) -> sqlite3.Row | None:
        return self.repository.get(
            conn,
            user_id,
            person_id,
        )

    def update(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        name: str | None,
        nickname: str | None,
        notes: str | None,
    ) -> sqlite3.Row | None:
        return self.repository.update(
            conn,
            user_id,
            person_id,
            name,
            nickname,
            notes,
        )

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> bool:
        return self.repository.delete(
            conn,
            user_id,
            person_id,
        )
