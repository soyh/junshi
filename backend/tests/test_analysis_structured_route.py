from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import analysis_structured


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def analyze(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((conn, user_id, conversation_id, provider))
        if self.error is not None:
            raise self.error
        return self.result


class FakeProvider:
    pass


def structured_result():
    return {
        "summary": "A recent conversation signal was observed.",
        "observed_facts": [],
        "inferences": [],
        "unknowns": [],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [],
        "analysis_constraints": [],
    }


def test_structured_analysis_route_uses_qwen_provider(monkeypatch):
    fake_service = FakeService(result=structured_result())
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_structured, "service", fake_service)
    monkeypatch.setattr(analysis_structured, "QwenProvider", lambda: fake_provider)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/analysis/structured")

    assert response.status_code == 200
    assert response.json()["summary"] == "A recent conversation signal was observed."
    assert len(fake_service.calls) == 1
    assert fake_service.calls[0][1:] == ("00000000-0000-0000-0000-000000000001", "conversation-1", fake_provider)


def test_structured_analysis_route_translates_llm_failure(monkeypatch):
    fake_service = FakeService(error=RuntimeError("provider unavailable"))
    monkeypatch.setattr(analysis_structured, "service", fake_service)
    monkeypatch.setattr(analysis_structured, "QwenProvider", FakeProvider)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/analysis/structured")

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM analysis failed"
