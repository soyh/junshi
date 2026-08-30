import sqlite3

from app.services.analysis_llm import AnalysisLLMService
from app.services.recommendation import RecommendationService
from app.services.strategy_decision import StrategyDecisionContextService
from app.services.strategy_recommendation_candidate import StrategyRecommendationCandidateService


class AnalysisRecommendationService:
    """Orchestrate derived Analysis -> explicit Strategy candidates -> Recommendations."""

    def __init__(
        self,
        analysis_llm_service: AnalysisLLMService | None = None,
        strategy_decision_service: StrategyDecisionContextService | None = None,
        candidate_service: StrategyRecommendationCandidateService | None = None,
        recommendation_service: RecommendationService | None = None,
    ):
        self.analysis_llm_service = analysis_llm_service or AnalysisLLMService()
        self.strategy_decision_service = strategy_decision_service or StrategyDecisionContextService()
        self.candidate_service = candidate_service or StrategyRecommendationCandidateService()
        self.recommendation_service = recommendation_service or RecommendationService()

    def build_context(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
        *,
        provider=None,
        structured_analysis=None,
    ) -> dict:
        analysis_context = self.analysis_llm_service.analysis_service.get_context(
            conn, user_id, conversation_id
        )
        person_id = analysis_context["person"]["id"]
        if structured_analysis is None:
            structured_analysis = self.analysis_llm_service.analyze_context(
                analysis_context,
                provider=provider,
            )
        analysis = structured_analysis.model_dump(mode="json")
        strategy_context = self.strategy_decision_service.get_context(
            conn,
            user_id,
            person_id,
            structured_analysis=structured_analysis,
        )
        recommendation_context = self.recommendation_service.get_context(
            conn,
            user_id,
            person_id,
        )
        candidates = self.candidate_service.build_candidates(analysis)
        recommendations = self.recommendation_service.produce_recommendations(
            candidates,
            recommendation_context["evidence"],
        )

        return {
            "person": strategy_context["person"],
            "relationship": strategy_context["relationship"],
            "current_state": strategy_context["current_state"],
            "evidence": recommendation_context["evidence"],
            "facts": analysis.get("observed_facts", []),
            "inferences": analysis.get("inferences", []),
            "unknowns": analysis.get("unknowns", []),
            "recommendations": recommendations,
            "learning_strategy": {
                "candidates": strategy_context.get("candidates", []),
                "strategy_decision_learning": strategy_context.get("decision_inputs", {}),
                "constraints": strategy_context["strategy_constraints"],
            },
            "structured_analysis": analysis,
            "recommendation_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "must_treat_llm_output_as_derived": True,
                "must_preserve_evidence_provenance": True,
                "must_not_auto_select": True,
                "must_not_auto_execute": True,
            },
        }
