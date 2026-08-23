import sqlite3

from app.services.relationship_state import RelationshipStateService


class RecommendationService:
    def __init__(self, relationship_state_service: RelationshipStateService | None = None):
        self.relationship_state_service = relationship_state_service or RelationshipStateService()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        state = self.relationship_state_service.get_state(conn, user_id, person_id)

        return {
            "person": state["person"],
            "relationship": state["relationship"],
            "current_state": state["current_state"],
            "evidence": state["evidence"],
            "recommendations": [],
        }
