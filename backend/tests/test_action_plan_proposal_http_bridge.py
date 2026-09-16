from app.core.database import get_connection


def test_http_proposal_then_http_decision_uses_persisted_bridge(client, monkeypatch):
    from app.api.routes import analysis_action_plan as analysis_action_plan_route

    person = client.post("/api/v1/persons", json={"name": "HTTP proposal bridge object"}).json()
    assert client.post(
        "/api/v1/relationships",
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    ).status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"], "title": "HTTP proposal bridge"},
    ).json()
    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "当前需要基于证据形成下一步建议",
            "sent_at": "2026-09-16T10:00:00+00:00",
        },
    ).json()

    class Provider:
        def analyze(self, context):
            assert context["person"]["id"] == person["id"]
            return {
                "summary": "形成下一步策略建议",
                "observed_facts": [{"content": "用户提供了当前关系证据", "confidence": 1.0, "evidence_source_ids": [message["id"]]}],
                "inferences": [],
                "unknowns": [{"content": "对方后续反应未知", "confidence": 1.0, "evidence_source_ids": [message["id"]]}],
                "hypotheses": [{"content": "保持低压力互动并观察后续反馈", "confidence": 0.8, "evidence_source_ids": [message["id"]], "action": "保持低压力互动并观察后续反馈"}],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [{"evidence_id": message["id"], "type": "message"}],
                "analysis_constraints": ["must_preserve_unknowns"],
            }

    monkeypatch.setattr(analysis_action_plan_route, "QwenProvider", Provider)

    response = client.post(f"/api/v1/conversations/{conversation['id']}/action-plan/proposals")
    assert response.status_code == 201
    body = response.json()
    recommendation = body["recommendations"][0]
    proposal = body["action_plan"][0]
    assert proposal["proposal_id"]
    assert proposal["recommendation_id"] == recommendation["id"]
    assert proposal["action"] == recommendation["action"]
    assert proposal["status"] == "proposed"
    assert proposal["requires_user_confirmation"] is True

    decision_response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"recommendation_id": recommendation["id"], "decision": "confirmed", "note": "用户显式确认"},
    )
    assert decision_response.status_code == 201
    decision = decision_response.json()
    assert decision["recommendation_id"] == recommendation["id"]
    assert decision["action_plan_proposal_id"] == proposal["proposal_id"]
    assert decision["decision"] == "confirmed"

    with get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_executions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM action_outcomes").fetchone()[0] == 0
