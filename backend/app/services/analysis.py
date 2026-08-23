import sqlite3

from app.repositories.analysis import AnalysisRepository
from app.domain.errors import PersonNotFoundError


class AnalysisService:
    def __init__(self, repository: AnalysisRepository | None = None):
        self.repository = repository or AnalysisRepository()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> dict:
        conversation, person, messages = self.repository.get_context(
            conn,
            user_id,
            conversation_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        if person is None:
            raise PersonNotFoundError("Person not found")

        return {
            "conversation": dict(conversation),
            "person": dict(person),
            "messages": [dict(message) for message in messages],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
        }
