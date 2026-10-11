from app.api.routes import action_plan, analysis_action_plan


PASSWORD = "correct-horse-battery-staple"


class FakeProvider:
    pass


class FakeAnalysisActionPlanService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def build_context(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((user_id, conversation_id, provider))
        return self.result


class FakeSavedActionPlanService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def get_context(self, conn, user_id, person_id):
        self.calls.append((user_id, person_id))
        return self.result


def _register(client, username: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_conversation(client, token: str):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "TEST-140 Person"},
    )
    assert person.status_code == 201
    person_body = person.json()
    person_id = person_body["id"]
    conversation = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"person_id": person_id, "title": "TEST-140 Conversation"},
    )
    assert conversation.status_code == 201
    return person_body["user_id"], person_id, conversation.json()["id"]


def _action_constraints():
    return {
        "must_be_evidence_backed": True,
        "must_preserve_unknowns": True,
        "requires_user_confirmation": True,
        "must_not_auto_execute": True,
        "must_not_change_relationship": True,
    }


def _saved_result(person_id: str):
    return {
        "person": {"id": person_id, "name": "TEST-140 Person"},
        "relationship": None,
        "current_state": {"status": "active", "stage": "unknown"},
        "evidence": [{"source_id": "message-1", "content": "source evidence"}],
        "facts": [],
        "inferences": [],
        "unknowns": [],
        "recommendations": [{
            "id": "recommendation-1",
            "action": "Send a light reply",
            "evidence_source_ids": ["message-1"],
        }],
        "action_plan": [{
            "recommendation_id": "recommendation-1",
            "action": "Send a light reply",
            "evidence_source_ids": ["message-1"],
            "status": "proposed",
            "requires_user_confirmation": True,
        }],
        "action_constraints": _action_constraints(),
        "learning_strategy": {"candidates": []},
    }


def _generated_result(person_id: str):
    result = _saved_result(person_id)
    result["action_constraints"] = {
        **_action_constraints(),
        "must_treat_llm_output_as_derived": True,
        "must_preserve_evidence_provenance": True,
    }
    result["structured_analysis"] = {
        "summary": "derived action plan input",
        "observed_facts": [],
        "inferences": [],
        "unknowns": [{
            "content": "intent remains unknown",
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
    }
    result["action_plan_inputs"] = {
        "summary": "derived action plan input",
        "signals": {},
        "analysis_is_derived": True,
        "recommendations_are_source_backed": True,
    }
    return result


def test_product_shell_exposes_explicit_action_plan_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "action-plan-workspace",
        "generate-action-plan",
        "action-plan-generate-status",
        "generated-action-plan-summary",
        "generated-action-plan-list",
        "generated-action-plan-constraints",
        "load-saved-action-plan",
        "saved-action-plan-status",
        "saved-action-plan-list",
        "saved-action-plan-constraints",
    ):
        assert f'id="{control_id}"' in html
    for control_id in ("generate-action-plan", "load-saved-action-plan"):
        marker = f'id="{control_id}" class="requires-auth"'
        assert marker in html
        assert "disabled" in html[html.index(marker): html.index(marker) + 220]


def test_action_plan_workspace_separates_generation_from_saved_read(client):
    html = client.get("/app").text
    assert "/action-plan/context`" in html
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/context`" in html
    assert "Generate &amp; save action plan" in html
    assert "Refresh saved plans" in html
    assert "persist" in html.lower()
    assert "requires_user_confirmation" in html
    assert "status=${item.status" in html


def test_action_plan_is_never_generated_on_selection_change(client):
    html = client.get("/app").text
    script_start = html.index("const actionPlanGenerateStatus = byId('action-plan-generate-status')")
    script_end = html.index("  clearSession();\n})();")
    script = html[script_start:script_end]

    conversation_start = script.index("byId('conversation-select').addEventListener('change'")
    person_start = script.index("byId('person-select').addEventListener('change'", conversation_start)
    conversation_handler = script[conversation_start:person_start]
    person_handler = script[person_start:]

    assert "resetActionPlanWorkspace" in conversation_handler
    assert "generateActionPlan()" not in conversation_handler
    assert "loadSavedActionPlan()" not in conversation_handler
    assert "resetActionPlanWorkspace" in person_handler
    assert "generateActionPlan()" not in person_handler
    assert "loadSavedActionPlan()" not in person_handler


def test_action_plan_fragment_stops_before_decision_and_execution(client):
    html = client.get("/app").text
    script_start = html.index("const actionPlanGenerateStatus = byId('action-plan-generate-status')")
    script_end = html.index("  clearSession();\n})();")
    script = html[script_start:script_end]

    assert "method: 'POST'" not in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/decisions" not in script
    assert "/execution" not in script
    assert "nothing was confirmed or executed" in script
    assert "This read did not create a user decision or execute an action." in script


def test_action_plan_workspace_preserves_token_and_safe_dom_boundary(client):
    html = client.get("/app").text
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert "document.createElement('div')" in html
    assert "replaceChildren()" in html


def test_real_bearer_identity_flows_into_action_plan_generation(client, monkeypatch):
    token = _register(client, "test140-generate-user")
    user_id, person_id, conversation_id = _create_person_conversation(client, token)
    fake_service = FakeAnalysisActionPlanService(_generated_result(person_id))
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_action_plan, "service", fake_service)
    monkeypatch.setattr(analysis_action_plan, "QwenProvider", lambda: fake_provider)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/action-plan/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action_plan"][0]["status"] == "proposed"
    assert body["action_plan"][0]["requires_user_confirmation"] is True
    assert body["action_constraints"]["must_not_auto_execute"] is True
    assert fake_service.calls == [(user_id, conversation_id, fake_provider)]


def test_real_bearer_identity_flows_into_saved_action_plan_read(client, monkeypatch):
    token = _register(client, "test140-saved-user")
    user_id, person_id, _ = _create_person_conversation(client, token)
    fake_service = FakeSavedActionPlanService(_saved_result(person_id))
    monkeypatch.setattr(action_plan, "service", fake_service)

    response = client.get(
        f"/api/v1/persons/{person_id}/action-plan/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action_plan"][0]["recommendation_id"] == "recommendation-1"
    assert body["action_constraints"]["requires_user_confirmation"] is True
    assert fake_service.calls == [(user_id, person_id)]


def test_foreign_scope_is_rejected_before_action_plan_generation_or_read(client):
    alice = _register(client, "test140-alice")
    bob = _register(client, "test140-bob")
    _, person_id, conversation_id = _create_person_conversation(client, alice)

    generated = client.get(
        f"/api/v1/conversations/{conversation_id}/action-plan/context",
        headers=_auth(bob),
    )
    saved = client.get(
        f"/api/v1/persons/{person_id}/action-plan/context",
        headers=_auth(bob),
    )

    assert generated.status_code == 404
    assert saved.status_code == 404
    assert generated.json()["detail"] == "Conversation not found"
    assert "person" in saved.json()["detail"].lower()
