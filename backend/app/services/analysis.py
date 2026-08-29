import sqlite3

from app.domain.errors import PersonNotFoundError
from app.repositories.analysis import AnalysisRepository
from app.services.learning_strategy_context import LearningStrategyContextService


class AnalysisService:
    def __init__(
        self,
        repository: AnalysisRepository | None = None,
        learning_strategy_service: LearningStrategyContextService | None = None,
    ):
        self.repository = repository or AnalysisRepository()
        self.learning_strategy_service = learning_strategy_service or LearningStrategyContextService()

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

        try:
            learning_strategy = self.learning_strategy_service.get_learning_context(
                conn,
                user_id,
                person["id"],
            )
        except ValueError as exc:
            if str(exc) != "Relationship not found":
                raise
            learning_strategy = self.learning_strategy_service._empty_learning_context()

        return {
            "conversation": dict(conversation),
            "person": dict(person),
            "messages": [dict(message) for message in messages],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
            "learning_strategy": learning_strategy,
        }
