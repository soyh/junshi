from app.api.routes import analysis_recommendation, analysis_strategy


PASSWORD = "correct-horse-battery-staple"


class FakeProvider:
    pass


class FakeStrategyService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def build_strategy_context(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((user_id, conversation_id, provider))
        return self.result


class FakeRecommendationService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def build_context(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((user_id, conversation_id, provider))
        return self.result


def _register(client, username: str):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    return body["access_token"], body["user"]["id"]


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _create_person_conversation(client, token: str):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "TEST-139 Person"},
    )
    assert person.status_code == 201
    person_id = person.json()["id"]
    conversation = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"person_id": person_id, "title": "TEST-139 Conversation"},
    )
    assert conversation.status_code == 201
    return person_id, conversation.json()["id"]


def _structured_analysis():
    return {
        "summary": "derived summary",
        "observed_facts": [],
        "inferences": [],
        "unknowns": [{"content": "unknown", "evidence_source_ids": []}],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [],
        "analysis_constraints": ["derived_only"],
    }


def _strategy_result(person_id: str):
    return {
        "person": {"id": person_id, "name": "TEST-139 Person"},
        "relationship": {},
        "current_state": {"status": "active", "stage": "dating"},
        "strategy_constraints": {
            "must_not_auto_select": True,
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
            "must_preserve_unknowns": True,
        },
        "candidates": [
            {
                "id": "candidate-1",
                "recommendation": "保持正常互动",
                "evidence_source_ids": ["message-1"],
            }
        ],
        "decision_inputs": {
            "candidate_count": 1,
            "candidate_ids": ["candidate-1"],
            "selection_status": "requires_explicit_decision",
        },
        "structured_analysis": _structured_analysis(),
    }


def _recommendation_result(person_id: str):
    return {
        "person": {"id": person_id, "name": "TEST-139 Person"},
        "relationship": {},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": [
            {
                "source_type": "message",
                "source_id": "message-1",
                "content": "对方主动联系",
            }
        ],
        "facts": [],
        "inferences": [],
        "unknowns": [{"content": "真实动机未知"}],
        "recommendations": [
            {
                "id": "recommendation-1",
                "recommendation": "保持正常互动",
                "evidence_source_ids": ["message-1"],
                "action": "正常回复",
                "reply": "可以呀",
                "priority": "normal",
                "time_horizon": "short_term",
                "provenance": {"source": "strategy_candidate"},
            }
        ],
        "learning_strategy": {
            "candidates": [],
            "strategy_decision_learning": {},
            "constraints": {"must_not_auto_select": True},
        },
        "structured_analysis": _structured_analysis(),
        "recommendation_constraints": {
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "must_treat_llm_output_as_derived": True,
            "must_preserve_evidence_provenance": True,
            "must_not_auto_select": True,
            "must_not_auto_execute": True,
        },
    }


def test_product_shell_exposes_strategy_recommendation_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "strategy-recommendation",
        "load-strategy-context",
        "strategy-context-status",
        "strategy-context-summary",
        "strategy-candidate-list",
        "strategy-constraint-list",
        "load-recommendation-context",
        "recommendation-context-status",
        "recommendation-list",
        "recommendation-constraint-list",
    ):
        assert f'id="{control_id}"' in html
    assert "/strategy/context`" in html
    assert "/recommendation/context`" in html
    assert "must_not_auto_select" in html
    assert "must_not_auto_execute" in html


def test_strategy_recommendation_workspace_preserves_auth_and_safe_dom_boundary(client):
    html = client.get("/app").text
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    for control_id in ("load-strategy-context", "load-recommendation-context"):
        marker = f'id="{control_id}" class="requires-auth"'
        assert marker in html
        assert "disabled" in html[html.index(marker): html.index(marker) + 180]


def test_conversation_change_does_not_automatically_call_llm_context(client):
    html = client.get("/app").text
    script_start = html.index("const strategyContextStatus = byId('strategy-context-status')")
    script_end = html.index("  clearSession();\n})();")
    script = html[script_start:script_end]
    listener_start = script.index("byId('conversation-select').addEventListener('change'")
    listener_end = script.index("byId('person-select').addEventListener('change'", listener_start)
    change_handler = script[listener_start:listener_end]
    assert "resetStrategyRecommendation" in change_handler
    assert "loadStrategyContext()" not in change_handler
    assert "loadRecommendationContext()" not in change_handler


def test_strategy_recommendation_fragment_is_read_only(client):
    html = client.get("/app").text
    script_start = html.index("const strategyContextStatus = byId('strategy-context-status')")
    script_end = html.index("  clearSession();\n})();")
    script = html[script_start:script_end]
    assert "method: 'POST'" not in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/action-plan" not in script
    assert "/execution" not in script
    assert "auto-selected or executed" in script


def test_real_bearer_identity_flows_into_strategy_route(client, monkeypatch):
    token, user_id = _register(client, "test139-strategy-user")
    person_id, conversation_id = _create_person_conversation(client, token)
    fake_service = FakeStrategyService(_strategy_result(person_id))
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_strategy, "service", fake_service)
    monkeypatch.setattr(analysis_strategy, "QwenProvider", lambda: fake_provider)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/strategy/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json()["decision_inputs"]["selection_status"] == "requires_explicit_decision"
    assert fake_service.calls == [(user_id, conversation_id, fake_provider)]


def test_real_bearer_identity_flows_into_recommendation_route(client, monkeypatch):
    token, user_id = _register(client, "test139-recommendation-user")
    person_id, conversation_id = _create_person_conversation(client, token)
    fake_service = FakeRecommendationService(_recommendation_result(person_id))
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_recommendation, "service", fake_service)
    monkeypatch.setattr(analysis_recommendation, "QwenProvider", lambda: fake_provider)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/recommendation/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"][0]["evidence_source_ids"] == ["message-1"]
    assert body["recommendation_constraints"]["must_not_auto_execute"] is True
    assert fake_service.calls == [(user_id, conversation_id, fake_provider)]


def test_foreign_conversation_is_rejected_before_analysis_generation(client):
    alice, _ = _register(client, "test139-alice")
    bob, _ = _register(client, "test139-bob")
    _, conversation_id = _create_person_conversation(client, alice)

    strategy = client.get(
        f"/api/v1/conversations/{conversation_id}/strategy/context",
        headers=_auth(bob),
    )
    recommendation = client.get(
        f"/api/v1/conversations/{conversation_id}/recommendation/context",
        headers=_auth(bob),
    )
    assert strategy.status_code == 404
    assert recommendation.status_code == 404
    assert strategy.json()["detail"] == "Conversation not found"
    assert recommendation.json()["detail"] == "Conversation not found"
