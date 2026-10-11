from fastapi.testclient import TestClient

from app.api.routes import analysis_strategy
from app.main import app
from app.services.llm import LLMAnalysisError


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def build_strategy_context(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((conn, user_id, conversation_id, provider))
        if self.error is not None:
            raise self.error
        return self.result


class FakeProvider:
    pass


def strategy_context_result():
    return {
        "person": {"id": "person-1", "name": "测试对象"},
        "relationship": {"id": "relationship-1", "status": "active", "stage": "dating"},
        "current_state": {"status": "active", "stage": "dating"},
        "strategy_constraints": {
            "must_not_auto_select": True,
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
            "must_preserve_unknowns": True,
        },
        "candidates": [],
        "decision_inputs": {
            "candidate_count": 0,
            "candidate_ids": [],
            "selection_status": "requires_explicit_decision",
            "observed_outcome_counts": {},
            "unknown_outcome_counts": {},
        },
        "structured_analysis": {
            "summary": "derived strategy input",
            "observed_facts": [],
            "inferences": [],
            "unknowns": [{"content": "unknown", "evidence_source_ids": []}],
            "hypotheses": [],
            "emotional_signals": [],
            "relationship_signals": [],
            "risk_signals": [],
            "intent_signals": [],
            "evidence_links": [],
            "analysis_constraints": ["must_preserve_unknowns"],
        },
    }


def test_analysis_strategy_route_uses_qwen_and_existing_strategy_context(monkeypatch):
    fake_service = FakeService(result=strategy_context_result())
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_strategy, "service", fake_service)
    monkeypatch.setattr(analysis_strategy, "QwenProvider", lambda: fake_provider)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/strategy/context")

    assert response.status_code == 200
    body = response.json()
    assert body["structured_analysis"]["summary"] == "derived strategy input"
    assert body["decision_inputs"]["selection_status"] == "requires_explicit_decision"
    assert body["strategy_constraints"]["must_treat_llm_output_as_derived"] is True
    assert len(fake_service.calls) == 1
    assert fake_service.calls[0][1:] == (
        "00000000-0000-0000-0000-000000000001",
        "conversation-1",
        fake_provider,
    )


def test_analysis_strategy_route_translates_llm_failure(monkeypatch):
    fake_service = FakeService(error=LLMAnalysisError("provider unavailable"))
    monkeypatch.setattr(analysis_strategy, "service", fake_service)
    monkeypatch.setattr(analysis_strategy, "QwenProvider", FakeProvider)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/strategy/context")

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM analysis failed"
