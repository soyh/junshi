import sqlite3

from app.services.recommendation import RecommendationService


class StrategicReplyService:
    def __init__(self, recommendation_service: RecommendationService | None = None):
        self.recommendation_service = recommendation_service or RecommendationService()

    def get_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        context = self.recommendation_service.get_context(conn, user_id, person_id)
        return {
            **context,
            "reply_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "must_not_auto_send": True,
                "must_not_change_relationship": True,
            },
            "draft": None,
        }
