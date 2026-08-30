import sqlite3

from app.services.recommendation_producer import RecommendationProducer
from app.services.relationship_state import RelationshipStateService


class RecommendationService:
    def __init__(
        self,
        relationship_state_service: RelationshipStateService | None = None,
        recommendation_producer: RecommendationProducer | None = None,
    ):
        self.relationship_state_service = relationship_state_service or RelationshipStateService()
        self.recommendation_producer = recommendation_producer or RecommendationProducer()

    def produce_recommendations(self, candidates: list, evidence: list[dict]) -> list[dict]:
        return self.recommendation_producer.produce(candidates, evidence)

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
            "facts": state["facts"],
            "inferences": state["inferences"],
            "unknowns": state["unknowns"],
            "recommendations": [],
        }
