import sqlite3

from app.domain.errors import PersonNotFoundError
from app.repositories.analysis import AnalysisRepository
from app.services.evidence import EvidenceService
from app.services.learning_strategy_context import LearningStrategyContextService
from app.services.relationship_state import RelationshipStateService


class AnalysisService:
    def __init__(
        self,
        repository: AnalysisRepository | None = None,
        learning_strategy_service: LearningStrategyContextService | None = None,
        relationship_state_service: RelationshipStateService | None = None,
        evidence_service: EvidenceService | None = None,
    ):
        self.repository = repository or AnalysisRepository()
        self.learning_strategy_service = learning_strategy_service or LearningStrategyContextService()
        self.relationship_state_service = relationship_state_service or RelationshipStateService()
        self.evidence_service = evidence_service or EvidenceService()

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

        evidence_result = self.evidence_service.get_conversation_evidence(
            conn,
            user_id,
            conversation_id,
        )
        if evidence_result is None:
            raise ValueError("Conversation not found")

        _, _, evidence = evidence_result

        learning_strategy = self.learning_strategy_service.get_learning_context(
            conn,
            user_id,
            person["id"],
        )

        relationship_state = self._get_relationship_state(
            conn,
            user_id,
            person["id"],
        )

        return {
            "conversation": dict(conversation),
            "person": dict(person),
            "messages": [dict(message) for message in messages],
            "evidence": [item.model_dump() for item in evidence],
            "facts": relationship_state["facts"],
            "inferences": relationship_state["inferences"],
            "unknowns": relationship_state["unknowns"],
            "recommendations": [],
            "learning_strategy": learning_strategy,
            "relationship_state": relationship_state,
        }

    def _get_relationship_state(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        try:
            state = self.relationship_state_service.get_state(
                conn,
                user_id,
                person_id,
            )
        except ValueError as exc:
            if str(exc) != "Relationship not found":
                raise
            return {
                "current_state": None,
                "evidence": [],
                "facts": [],
                "inferences": [],
                "unknowns": [],
                "recommendations": [],
            }

        return {
            "current_state": state["current_state"],
            "evidence": state["evidence"],
            "facts": state["facts"],
            "inferences": state["inferences"],
            "unknowns": state["unknowns"],
            "recommendations": state["recommendations"],
        }
