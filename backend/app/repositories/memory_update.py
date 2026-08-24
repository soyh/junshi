import json
import sqlite3


class MemoryUpdateRepository:
    @staticmethod
    def get_by_candidate_id(
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        candidate_id: str,
    ):
        return conn.execute(
            """
            SELECT id, user_id, person_id, source_candidate_id,
                   source_decision_id, source_outcome_id, category,
                   memory_json, created_at
            FROM memory_updates
            WHERE user_id = ? AND person_id = ? AND source_candidate_id = ?
            """,
            (user_id, person_id, candidate_id),
        ).fetchone()

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        memory_id: str,
        user_id: str,
        person_id: str,
        source_candidate_id: str,
        source_decision_id: str,
        source_outcome_id: str,
        category: str,
        memory: dict,
        created_at: str,
    ):
        conn.execute(
            """
            INSERT INTO memory_updates (
                id, user_id, person_id, source_candidate_id,
                source_decision_id, source_outcome_id, category,
                memory_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                user_id,
                person_id,
                source_candidate_id,
                source_decision_id,
                source_outcome_id,
                category,
                json.dumps(memory, ensure_ascii=False, sort_keys=True),
                created_at,
            ),
        )
        return MemoryUpdateRepository.get_by_candidate_id(
            conn, user_id, person_id, source_candidate_id
        )
