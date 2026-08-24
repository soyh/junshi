import sqlite3
import uuid
from datetime import datetime, timezone

from app.repositories.memory_update import MemoryUpdateRepository
from app.services.memory_synthesis import MemorySynthesisService


class MemoryPersistenceService:
    def __init__(
        self,
        synthesis_service: MemorySynthesisService | None = None,
        repository: MemoryUpdateRepository | None = None,
    ):
        self.synthesis_service = synthesis_service or MemorySynthesisService()
        self.repository = repository or MemoryUpdateRepository()

    def persist_candidate(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        candidate_id: str,
    ) -> dict:
        existing = self.repository.get_by_candidate_id(
            conn, user_id, person_id, candidate_id
        )
        if existing is not None:
            return self._serialize(existing)

        context = self.synthesis_service.get_context(conn, user_id, person_id)
        proposal = next(
            (
                item
                for item in context["updates"]
                if item["source_candidate_id"] == candidate_id
            ),
            None,
        )
        if proposal is None:
            raise ValueError("memory update candidate not found")

        row = self.repository.create(
            conn,
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"persisted-memory:{candidate_id}")),
            user_id,
            person_id,
            proposal["source_candidate_id"],
            proposal["source_decision_id"],
            proposal["source_outcome_id"],
            proposal["category"],
            proposal["memory"],
            datetime.now(timezone.utc).isoformat(),
        )
        return self._serialize(row)

    @staticmethod
    def _serialize(row) -> dict:
        import json

        return {
            "id": row["id"],
            "status": "persisted",
            "category": row["category"],
            "person_id": row["person_id"],
            "source_candidate_id": row["source_candidate_id"],
            "source_decision_id": row["source_decision_id"],
            "source_outcome_id": row["source_outcome_id"],
            "memory": json.loads(row["memory_json"]),
            "created_at": row["created_at"],
        }
