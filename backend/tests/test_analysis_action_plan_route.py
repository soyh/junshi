from fastapi.testclient import TestClient

from app.api.routes import analysis_action_plan
from app.main import app
from app.services.llm import LLMAnalysisError


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def build_context(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((conn, user_id, conversation_id, provider))
        if self.error is not None:
            raise self.error
        return self.result


class FakeProvider:
    pass


def result():
    return {
        "person": {"id": "person-1"},
        "relationship": {"id": "relationship-1"},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": [{"source_id": "message-1"}],
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
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
        },
        "learning_strategy": {
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
        },
        "structured_analysis": {
            "summary": "derived action plan input",
            "observed_facts": [],
            "inferences": [],
            "unknowns": [{
                "content": "unknown",
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
        },
        "action_plan_inputs": {
            "summary": "derived action plan input",
            "signals": {"unknowns": [{
                "content": "unknown",
                "confidence": 1.0,
                "evidence_source_ids": ["message-1"],
            }]},
            "analysis_is_derived": True,
        },
    }


def test_route_returns_derived_action_plan_input(monkeypatch):
    expected = result()
    fake_service = FakeService(result=expected)
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_action_plan, "service", fake_service)
    monkeypatch.setattr(analysis_action_plan, "QwenProvider", lambda: fake_provider)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/conversations/conversation-1/action-plan/context"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["structured_analysis"]["summary"] == "derived action plan input"
    assert body["action_plan_inputs"]["analysis_is_derived"] is True
    assert body["action_constraints"]["must_not_auto_execute"] is True
    assert body["action_plan"] == []
    assert body["learning_strategy"] == expected["learning_strategy"]
    assert len(fake_service.calls) == 1
    assert fake_service.calls[0][1:] == (
        "00000000-0000-0000-0000-000000000001",
        "conversation-1",
        fake_provider,
    )


def test_route_translates_llm_failure(monkeypatch):
    fake_service = FakeService(error=LLMAnalysisError("provider unavailable"))
    monkeypatch.setattr(analysis_action_plan, "service", fake_service)
    monkeypatch.setattr(analysis_action_plan, "QwenProvider", FakeProvider)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/conversations/conversation-1/action-plan/context"
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM analysis failed"
