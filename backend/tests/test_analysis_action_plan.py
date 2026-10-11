from app.schemas.structured_analysis import StructuredAnalysis, StructuredAnalysisItem
from app.services.action_plan import ActionPlanService
from app.services.analysis_action_plan import AnalysisActionPlanService


def structured_analysis():
    return StructuredAnalysis.model_validate({
        "summary": "derived action-plan context",
        "observed_facts": [{
            "content": "对方询问周末是否有空",
            "confidence": 1.0,
            "evidence_source_ids": ["message-1"],
        }],
        "inferences": [{
            "content": "可能存在主动建立联系的意愿",
            "confidence": 0.7,
            "evidence_source_ids": ["message-1"],
        }],
        "unknowns": [{
            "content": "具体动机未知",
            "confidence": 1.0,
            "evidence_source_ids": ["message-1"],
        }],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [{"evidence_id": "message-1", "type": "message"}],
        "analysis_constraints": ["must_preserve_unknowns"],
    })


def learning_strategy():
    return {
        "candidates": [{
            "recommendation_id": "recommendation-1",
            "observed_outcome_count": 1,
            "outcome_counts": {"positive": 1},
            "unknown_outcome_count": 0,
            "memory_update_count": 1,
            "synthesis_status": "source_backed",
            "unknowns": [],
            "source": {"type": "recommendation"},
        }],
        "strategy_decision_learning": {
            "learning_candidate_decision_ids": ["decision-1"],
            "unknown_decision_ids": [],
            "learning_candidate_provenance": [{"decision_id": "decision-1"}],
            "unknown_decision_provenance": [],
            "recommendation_observed_counts": {"recommendation-1": 1},
        },
        "constraints": {
            "read_only": True,
            "source_backed_only": True,
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


def action_plan_context():
    return {
        "person": {"id": "person-1"},
        "relationship": {"id": "relationship-1"},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": [{"source_id": "message-1", "content": "原始证据"}],
        "facts": [],
        "inferences": [],
        "unknowns": [],
        "recommendations": [],
        "action_plan": [],
        "action_constraints": {
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "requires_user_confirmation": True,
            "must_not_auto_execute": True,
            "must_not_change_relationship": True,
        },
        "learning_strategy": {"candidates": []},
    }


def recommendation_context(recommendations=None):
    return {
        "recommendations": list(recommendations or []),
        "evidence": [{"source_id": "message-1", "content": "原始证据"}],
    }


class FakeAnalysisRecommendationService:
    def __init__(self, recommendations=None):
        self.recommendations = list(recommendations or [])
        self.calls = []

    def build_context(
        self,
        conn,
        user_id,
        conversation_id,
        *,
        provider=None,
        structured_analysis=None,
    ):
        self.calls.append({
            "provider": provider,
            "structured_analysis": structured_analysis,
        })
        return recommendation_context(self.recommendations)


def test_service_projects_analysis_as_derived_action_plan_input():
    expected_learning_strategy = learning_strategy()

    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": expected_learning_strategy,
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            assert context["person"]["id"] == "person-1"
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return action_plan_context()

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService(),
    ).build_context(None, "user-1", "conversation-1")

    assert result["structured_analysis"]["summary"] == "derived action-plan context"
    assert result["action_plan_inputs"]["analysis_is_derived"] is True
    assert result["action_plan_inputs"]["summary"] == "derived action-plan context"
    assert result["learning_strategy"] == expected_learning_strategy


def test_service_preserves_learning_strategy_from_analysis_context():
    expected_learning_strategy = learning_strategy()

    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": expected_learning_strategy,
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            assert context["learning_strategy"] is expected_learning_strategy
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            context = action_plan_context()
            context["learning_strategy"] = {"candidates": ["must-not-win"]}
            return context

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService(),
    ).build_context(None, "user-1", "conversation-1")

    assert result["learning_strategy"] == expected_learning_strategy
    assert result["learning_strategy"] is expected_learning_strategy


def test_service_preserves_provenance_unknowns_and_confirmation_boundary():
    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": learning_strategy(),
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return action_plan_context()

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService(),
    ).build_context(None, "user-1", "conversation-1")

    signals = result["action_plan_inputs"]["signals"]
    assert signals["observed_facts"][0]["evidence_source_ids"] == ["message-1"]
    assert signals["inferences"][0]["evidence_source_ids"] == ["message-1"]
    assert signals["unknowns"][0]["content"] == "具体动机未知"
    assert result["action_plan"] == []
    assert result["action_constraints"]["requires_user_confirmation"] is True
    assert result["action_constraints"]["must_not_auto_execute"] is True
    assert result["action_constraints"]["must_not_change_relationship"] is True
    assert result["action_constraints"]["must_treat_llm_output_as_derived"] is True
    assert result["action_constraints"]["must_preserve_evidence_provenance"] is True


def test_service_does_not_turn_analysis_into_action_plan_or_mutate_context():
    base = action_plan_context()

    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": learning_strategy(),
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return base

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService(),
    ).build_context(None, "user-1", "conversation-1")

    assert result["recommendations"] == []
    assert result["action_plan"] == []
    assert base["action_plan"] == []


def test_service_passes_provider_to_llm_boundary_and_recommendation_bridge():
    provider = object()
    llm_calls = []
    recommendation_service = FakeAnalysisRecommendationService()

    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": learning_strategy(),
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            llm_calls.append(provider)
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return action_plan_context()

    AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=recommendation_service,
    ).build_context(None, "user-1", "conversation-1", provider=provider)

    assert llm_calls == [provider]
    assert recommendation_service.calls[0]["provider"] is provider
    assert recommendation_service.calls[0]["structured_analysis"] is not None


def test_service_bridges_source_backed_recommendation_into_action_plan():
    recommendation = {
        "id": "recommendation-1",
        "action": "提出轻量邀请",
        "evidence_source_ids": ["message-1"],
        "priority": "medium",
        "time_horizon": "near_term",
    }

    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": learning_strategy(),
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return action_plan_context()

        build_action_plan = staticmethod(ActionPlanService.build_action_plan)

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService([recommendation]),
    ).build_context(None, "user-1", "conversation-1")

    assert result["recommendations"] == [recommendation]
    assert result["action_plan"] == [{
        "recommendation_id": "recommendation-1",
        "action": "提出轻量邀请",
        "evidence_source_ids": ["message-1"],
        "status": "proposed",
        "requires_user_confirmation": True,
        "priority": "medium",
        "time_horizon": "near_term",
    }]
    assert result["action_plan_inputs"]["recommendations_are_source_backed"] is True


def test_service_does_not_promote_structured_analysis_into_action_candidate():
    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": learning_strategy(),
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            analysis = structured_analysis()
            return analysis.model_copy(update={
                "hypotheses": [StructuredAnalysisItem(
                    content="应该立即发送消息",
                    confidence=0.99,
                    evidence_source_ids=["message-1"],
                )],
                "intent_signals": [StructuredAnalysisItem(
                    content="对方明确希望继续推进",
                    confidence=0.99,
                    evidence_source_ids=["message-1"],
                )],
            })

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            context = action_plan_context()
            context["recommendations"] = []
            context["action_plan"] = []
            return context

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService(),
    ).build_context(None, "user-1", "conversation-1")

    assert result["action_plan_inputs"]["signals"]["hypotheses"]
    assert result["action_plan_inputs"]["signals"]["intent_signals"]
    assert result["recommendations"] == []
    assert result["action_plan"] == []


def test_service_keeps_existing_action_candidate_boundary_separate_from_analysis():
    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {
                "person": {"id": "person-1"},
                "learning_strategy": learning_strategy(),
            }

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            context = action_plan_context()
            context["recommendations"] = [{
                "id": "recommendation-existing",
                "action": "提出轻量邀请",
                "evidence_source_ids": ["message-1"],
            }]
            context["action_plan"] = [{
                "recommendation_id": "recommendation-existing",
                "action": "提出轻量邀请",
                "evidence_source_ids": ["message-1"],
                "status": "proposed",
                "requires_user_confirmation": True,
            }]
            return context

    result = AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
        analysis_recommendation_service=FakeAnalysisRecommendationService(),
    ).build_context(None, "user-1", "conversation-1")

    assert result["recommendations"] == [{
        "id": "recommendation-existing",
        "action": "提出轻量邀请",
        "evidence_source_ids": ["message-1"],
    }]
    assert result["action_plan"] == [{
        "recommendation_id": "recommendation-existing",
        "action": "提出轻量邀请",
        "evidence_source_ids": ["message-1"],
        "status": "proposed",
        "requires_user_confirmation": True,
    }]
    assert result["action_plan_inputs"]["analysis_is_derived"] is True
