import sqlite3

from app.domain.errors import ConversationNotFoundError
from app.repositories.analysis import AnalysisRepository


class AnalysisService:
    def __init__(self, repository: AnalysisRepository | None = None):
        self.repository = repository or AnalysisRepository()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> tuple[sqlite3.Row, sqlite3.Row, list[sqlite3.Row]]:
        conversation, person, messages = self.repository.get_context(
            conn,
            user_id,
            conversation_id,
        )

        if conversation is None or person is None:
            raise ConversationNotFoundError("Conversation not found")

        return conversation, person, messages
