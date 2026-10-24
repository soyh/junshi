from fastapi.testclient import TestClient

from app.api.routes import analysis_strategic_reply
from app.main import app
from app.services.llm import LLMAnalysisError


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def build_context(self, conn, user_id, conversation_id, *, provider=None,
                      channel_rules="", self_profile=None, option=None,
                      wechat_alias=""):
        self.calls.append((conn, user_id, conversation_id, provider, channel_rules,
                           self_profile))
        if self.error is not None:
            raise self.error
        return self.result


class FakeProvider:
    pass


def strategic_reply_result():
    return {
        "person": {"id": "person-1", "name": "测试对象"},
        "relationship": {"id": "relationship-1", "status": "active", "stage": "dating"},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": [{"source_id": "message-1", "content": "原始证据"}],
        "facts": [],
        "inferences": [],
        "unknowns": [],
        "recommendations": [],
        "reply_constraints": {
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "must_preserve_evidence_provenance": True,
            "must_treat_llm_output_as_derived": True,
            "must_not_auto_send": True,
            "must_not_change_relationship": True,
        },
        "draft": None,
        "learning_strategy": {"candidates": []},
        "structured_analysis": {
            "summary": "derived reply input",
            "observed_facts": [],
            "inferences": [],
            "unknowns": [{"content": "unknown", "confidence": 1.0, "evidence_source_ids": ["message-1"]}],
            "hypotheses": [],
            "emotional_signals": [],
            "relationship_signals": [],
            "risk_signals": [],
            "intent_signals": [],
            "evidence_links": [{"evidence_id": "message-1", "type": "message"}],
            "analysis_constraints": ["must_preserve_unknowns"],
        },
        "reply_inputs": {
            "summary": "derived reply input",
            "signals": {"unknowns": [{"content": "unknown", "confidence": 1.0, "evidence_source_ids": ["message-1"]}]},
            "analysis_is_derived": True,
        },
    }


def test_analysis_strategic_reply_route_returns_derived_input(monkeypatch):
    fake_service = FakeService(result=strategic_reply_result())
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_strategic_reply, "service", fake_service)
    monkeypatch.setattr(analysis_strategic_reply, "QwenProvider", lambda: fake_provider)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/strategic-reply/context")

    assert response.status_code == 200
    body = response.json()
    assert body["structured_analysis"]["summary"] == "derived reply input"
    assert body["reply_inputs"]["analysis_is_derived"] is True
    assert body["reply_constraints"]["must_not_auto_send"] is True
    assert body["draft"] is None
    assert len(fake_service.calls) == 1
    assert fake_service.calls[0][1:] == (
        "00000000-0000-0000-0000-000000000001",
        "conversation-1",
        fake_provider,
        "",
        {},
    )


def test_analysis_strategic_reply_route_forwards_channel_rules(monkeypatch):
    fake_service = FakeService(result=strategic_reply_result())
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_strategic_reply, "service", fake_service)
    monkeypatch.setattr(analysis_strategic_reply, "QwenProvider", lambda: fake_provider)
    rules = "称呼对方“小满”，每次不超过两句，不用问句收尾。"

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/conversations/conversation-1/strategic-reply/context",
            json={"rules": rules},
        )

    assert response.status_code == 200
    assert fake_service.calls[0][4] == rules
    assert fake_service.calls[0][5] == {}


def test_analysis_strategic_reply_route_forwards_self_profile(monkeypatch):
    fake_service = FakeService(result=strategic_reply_result())
    monkeypatch.setattr(analysis_strategic_reply, "service", fake_service)
    monkeypatch.setattr(analysis_strategic_reply, "QwenProvider", lambda: FakeProvider())
    profile = {"nickname": "阿哲", "birth_year": "1994", "city": "杭州"}

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/conversations/conversation-1/strategic-reply/context",
            json={"rules": "像本人在打字", "self_profile": profile},
        )

    assert response.status_code == 200
    assert fake_service.calls[0][4] == "像本人在打字"
    assert fake_service.calls[0][5] == profile


def test_analysis_strategic_reply_route_translates_llm_failure(monkeypatch):
    fake_service = FakeService(error=LLMAnalysisError("provider unavailable"))
    monkeypatch.setattr(analysis_strategic_reply, "service", fake_service)
    monkeypatch.setattr(analysis_strategic_reply, "QwenProvider", FakeProvider)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/strategic-reply/context")

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM analysis failed"


def test_plan_route_returns_the_latest_stored_plan(monkeypatch):
    import json
    import sqlite3
    from contextlib import contextmanager

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE conversations (id TEXT PRIMARY KEY, user_id TEXT NOT NULL);
        CREATE TABLE strategic_reply_plans (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            target_message_id TEXT,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.execute(
        "INSERT INTO conversations (id, user_id) VALUES (?, ?)",
        ("conversation-1", "00000000-0000-0000-0000-000000000001"),
    )
    conn.execute(
        "INSERT INTO strategic_reply_plans"
        " (conversation_id, user_id, target_message_id, payload)"
        " VALUES (?, ?, ?, ?)",
        (
            "conversation-1",
            "00000000-0000-0000-0000-000000000001",
            "message-1",
            json.dumps({"read": "她在接话", "signal": "green"}, ensure_ascii=False),
        ),
    )
    conn.commit()

    @contextmanager
    def fake_connection():
        yield conn

    monkeypatch.setattr(analysis_strategic_reply, "get_connection", fake_connection)

    with TestClient(app) as client:
        response = client.get("/api/v1/conversations/conversation-1/strategic-reply/plan")
        missing = client.get("/api/v1/conversations/conversation-9/strategic-reply/plan")

    assert response.status_code == 200
    assert response.json()["plan"]["read"] == "她在接话"
    assert response.json()["plan"]["target_message_id"] == "message-1"
    assert missing.status_code == 404
