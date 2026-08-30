from app.schemas.structured_analysis import StructuredAnalysis
from app.services.analysis_recommendation import AnalysisRecommendationService


class FakeAnalysisService:
    def get_context(self, conn, user_id, conversation_id):
        return {
            "person": {"id": "person-1"},
            "conversation": {"id": conversation_id},
            "evidence": [
                {"source_type": "interaction", "source_id": "interaction-1", "content": "对方主动联系"}
            ],
        }


class FakeAnalysisLLMService:
    def __init__(self):
        self.analysis_service = FakeAnalysisService()

    def analyze_context(self, context, *, provider=None):
        return StructuredAnalysis(
            summary="保持正常互动",
            observed_facts=[{"content": "对方主动联系"}],
            inferences=[{"content": "仍有互动意愿"}],
            unknowns=["对方真实动机未知"],
            hypotheses=[
                {
                    "content": "保持正常互动，不立即升级关系",
                    "confidence": 0.72,
                    "evidence_source_ids": ["interaction-1"],
                }
            ],
            emotional_signals=[],
            relationship_signals=[],
            risk_signals=[],
            intent_signals=[],
            evidence_links=[],
            analysis_constraints=["derived_only"],
        )


class FakeStrategyDecisionService:
    def get_context(self, conn, user_id, person_id, *, structured_analysis=None):
        return {
            "person": {"id": person_id},
            "relationship": {"status": "active", "stage": "dating"},
            "current_state": {"status": "active", "stage": "dating"},
            "evidence": [
                {"source_type": "interaction", "source_id": "interaction-1", "content": "对方主动联系"}
            ],
            "candidates": [],
            "decision_inputs": {"candidate_count": 0, "selection_status": "requires_explicit_decision"},
            "strategy_constraints": {
                "must_not_auto_select": True,
                "must_not_rank_recommendations": True,
            },
            "structured_analysis": (structured_analysis.model_dump(mode="json") if structured_analysis else {}),
        }


def build_service():
    from app.services.strategy_recommendation_candidate import StrategyRecommendationCandidateService

    return AnalysisRecommendationService(
        analysis_llm_service=FakeAnalysisLLMService(),
        strategy_decision_service=FakeStrategyDecisionService(),
        candidate_service=StrategyRecommendationCandidateService(),
    )


def test_analysis_to_recommendation_is_end_to_end_and_source_backed():
    result = build_service().build_context(None, "user-1", "conversation-1", provider=object())
    assert len(result["recommendations"]) == 1
    recommendation = result["recommendations"][0]
    assert recommendation["recommendation"] == "保持正常互动，不立即升级关系"
    assert recommendation["evidence_source_ids"] == ["interaction-1"]
    assert recommendation["provenance"]["source"] == "strategy_candidate"
    assert result["recommendation_constraints"]["must_not_auto_select"] is True
    assert result["recommendation_constraints"]["must_not_auto_execute"] is True


def test_analysis_to_recommendation_is_deterministic_and_read_only():
    service = build_service()
    first = service.build_context(None, "user-1", "conversation-1", provider=object())
    second = service.build_context(None, "user-1", "conversation-1", provider=object())
    assert first == second


def test_unbacked_strategy_candidate_does_not_enter_recommendation():
    service = build_service()
    original = service.candidate_service.build_candidates
    service.candidate_service.build_candidates = lambda analysis: [
        {
            "id": "unbacked",
            "recommendation": "没有证据支持的建议",
            "evidence_source_ids": ["missing"],
            "provenance": {"source": "strategy_candidate"},
        }
    ]
    result = service.build_context(None, "user-1", "conversation-1", provider=object())
    assert result["recommendations"] == []
    service.candidate_service.build_candidates = original
