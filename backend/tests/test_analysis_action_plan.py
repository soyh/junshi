from app.schemas.structured_analysis import StructuredAnalysis
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


def test_service_projects_analysis_as_derived_action_plan_input():
    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {"person": {"id": "person-1"}}

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
    ).build_context(None, "user-1", "conversation-1")

    assert result["structured_analysis"]["summary"] == "derived action-plan context"
    assert result["action_plan_inputs"]["analysis_is_derived"] is True
    assert result["action_plan_inputs"]["summary"] == "derived action-plan context"


def test_service_preserves_provenance_unknowns_and_confirmation_boundary():
    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {"person": {"id": "person-1"}}

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
            return {"person": {"id": "person-1"}}

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
    ).build_context(None, "user-1", "conversation-1")

    assert result["recommendations"] == []
    assert result["action_plan"] == []
    assert base["action_plan"] == []


def test_service_passes_provider_to_llm_boundary():
    provider = object()
    calls = []

    class FakeAnalysisService:
        def get_context(self, conn, user_id, conversation_id):
            return {"person": {"id": "person-1"}}

    class FakeAnalysisLLMService:
        analysis_service = FakeAnalysisService()

        def analyze_context(self, context, *, provider=None):
            calls.append(provider)
            return structured_analysis()

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return action_plan_context()

    AnalysisActionPlanService(
        analysis_llm_service=FakeAnalysisLLMService(),
        action_plan_service=FakeActionPlanService(),
    ).build_context(None, "user-1", "conversation-1", provider=provider)

    assert calls == [provider]
