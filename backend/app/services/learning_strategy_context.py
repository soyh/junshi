import sqlite3

from app.services.action_feedback_learning_synthesis import ActionFeedbackLearningSynthesisService
from app.services.memory_learning_synthesis import MemoryLearningSynthesisService
from app.services.recommendation import RecommendationService
from app.services.strategy_decision_learning_bridge import StrategyDecisionLearningBridgeService


class LearningStrategyContextService:
    def __init__(
        self,
        recommendation_service: RecommendationService | None = None,
        feedback_learning_service: ActionFeedbackLearningSynthesisService | None = None,
        memory_learning_service: MemoryLearningSynthesisService | None = None,
        strategy_decision_learning_service: StrategyDecisionLearningBridgeService | None = None,
    ):
        self.recommendation_service = recommendation_service or RecommendationService()
        self.feedback_learning_service = feedback_learning_service or ActionFeedbackLearningSynthesisService()
        self.memory_learning_service = memory_learning_service or MemoryLearningSynthesisService()
        self.strategy_decision_learning_service = (
            strategy_decision_learning_service or StrategyDecisionLearningBridgeService()
        )

    def get_context(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        recommendation = self.recommendation_service.get_context(conn, user_id, person_id)
        feedback = self.feedback_learning_service.get_synthesis(conn, user_id, person_id)
        memory = self.memory_learning_service.get_context(conn, user_id, person_id)
        strategy_decision = self.strategy_decision_learning_service.get_context(
            conn, user_id, person_id
        )

        return {
            "person": recommendation["person"],
            "relationship": recommendation["relationship"],
            "current_state": recommendation["current_state"],
            "evidence": recommendation["evidence"],
            "facts": recommendation["facts"],
            "inferences": recommendation["inferences"],
            "unknowns": recommendation["unknowns"],
            "recommendations": recommendation["recommendations"],
            "learning_inputs": {
                "action_feedback": feedback["candidates"],
                "memory_updates": memory["updates"],
                "strategy_decision": strategy_decision,
            },
            "strategy_constraints": {
                "must_be_source_backed": True,
                "must_preserve_facts_inferences_unknowns": True,
                "must_preserve_learning_unknowns": True,
                "must_preserve_source_provenance": True,
                "must_preserve_unknowns": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_success": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
                "must_not_auto_send": True,
                "must_not_call_llm": True,
            },
        }
