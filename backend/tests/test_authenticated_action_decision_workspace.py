from app.api.routes import action_decision


PASSWORD = "correct-horse-battery-staple"


class FakeActionDecisionService:
    def __init__(self, context):
        self.context = context
        self.context_calls = []
        self.create_calls = []

    def get_context(self, conn, user_id, person_id):
        self.context_calls.append((user_id, person_id))
        return self.context

    def create_decision(
        self,
        conn,
        user_id,
        person_id,
        recommendation_id,
        decision,
        note,
    ):
        self.create_calls.append(
            (user_id, person_id, recommendation_id, decision, note)
        )
        return {
            "id": "decision-created",
            "user_id": user_id,
            "person_id": person_id,
            "recommendation_id": recommendation_id,
            "decision": decision,
            "note": note,
            "created_at": "2026-09-19T00:00:00+00:00",
        }


def _register(client, username: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship(client, token: str, name: str = "TEST-141 Person"):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": name},
    )
    assert person.status_code == 201
    person_body = person.json()
    relationship = client.post(
        "/api/v1/relationships",
        headers=_auth(token),
        json={
            "person_id": person_body["id"],
            "status": "active",
            "stage": "dating",
        },
    )
    assert relationship.status_code == 201
    return person_body, relationship.json()


def _decision_context(person_id: str, relationship_id: str):
    return {
        "person": {"id": person_id, "name": "TEST-141 Person"},
        "relationship": {"id": relationship_id, "person_id": person_id},
        "action_plan": [
            {
                "recommendation_id": "recommendation-141",
                "action": "Send a light reply",
                "evidence_source_ids": ["message-141"],
                "status": "proposed",
                "requires_user_confirmation": True,
            },
            {
                "recommendation_id": "not-available",
                "action": "Already resolved",
                "evidence_source_ids": ["message-old"],
                "status": "confirmed",
                "requires_user_confirmation": True,
            },
        ],
        "action_constraints": {
            "must_be_evidence_backed": True,
            "must_preserve_unknowns": True,
            "requires_user_confirmation": True,
            "must_not_auto_execute": True,
            "must_not_change_relationship": True,
            "must_record_user_decision": True,
        },
        "decisions": [],
    }


def test_product_shell_exposes_action_decision_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "action-decision-workspace",
        "load-action-decision-context",
        "action-decision-recommendation",
        "action-decision-candidate-detail",
        "action-decision-note",
        "confirm-action-decision",
        "reject-action-decision",
        "action-decision-status",
        "action-decision-constraints",
        "action-decision-history",
    ):
        assert f'id="{control_id}"' in html
    assert "Load decision context" in html
    assert "Confirm selected proposal" in html
    assert "Reject selected proposal" in html


def test_action_decision_fragment_uses_canonical_context_and_post_only(client):
    html = client.get("/app").text
    start = html.index("const actionDecisionStatus = byId('action-decision-status')")
    end = html.index("const actionPlanGenerateStatus = byId('action-plan-generate-status')")
    script = html[start:end]

    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/decisions/context`" in script
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/decisions`" in script
    assert "method: 'POST'" in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/execution-context" not in script
    assert "/executions/" not in script
    assert "/outcomes" not in script
    assert "No execution was started." in script


def test_action_decision_requires_explicit_load_and_click(client):
    html = client.get("/app").text
    start = html.index("const actionDecisionStatus = byId('action-decision-status')")
    end = html.index("const actionPlanGenerateStatus = byId('action-plan-generate-status')")
    script = html[start:end]

    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetActionDecisionWorkspace" in person_listener
    assert "loadActionDecisionContext()" not in person_listener
    assert "submitActionDecision(" not in person_listener
    assert "bind('load-action-decision-context', loadActionDecisionContext" in script
    assert "bind('confirm-action-decision', () => submitActionDecision('confirmed')" in script
    assert "bind('reject-action-decision', () => submitActionDecision('rejected')" in script


def test_action_decision_workspace_preserves_memory_token_and_safe_dom(client):
    html = client.get("/app").text
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert "document.createElement('option')" in html
    assert "replaceChildren()" in html


def test_real_bearer_identity_flows_into_action_decision_context(client, monkeypatch):
    token = _register(client, "test141-context-user")
    person, relationship = _create_person_relationship(client, token)
    fake = FakeActionDecisionService(_decision_context(person["id"], relationship["id"]))
    monkeypatch.setattr(action_decision, "service", fake)

    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/decisions/context",
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action_plan"][0]["recommendation_id"] == "recommendation-141"
    assert body["action_constraints"]["must_record_user_decision"] is True
    assert body["action_constraints"]["must_not_auto_execute"] is True
    assert fake.context_calls == [(person["user_id"], person["id"])]


def test_confirmed_decision_records_only_canonical_user_decision(client, monkeypatch):
    token = _register(client, "test141-confirm-user")
    person, relationship = _create_person_relationship(client, token)
    fake = FakeActionDecisionService(_decision_context(person["id"], relationship["id"]))
    monkeypatch.setattr(action_decision, "service", fake)

    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        headers=_auth(token),
        json={
            "recommendation_id": "recommendation-141",
            "decision": "confirmed",
            "note": "explicit user confirmation",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "confirmed"
    assert fake.create_calls == [
        (
            person["user_id"],
            person["id"],
            "recommendation-141",
            "confirmed",
            "explicit user confirmation",
        )
    ]


def test_rejected_decision_remains_tied_to_selected_proposal(client, monkeypatch):
    token = _register(client, "test141-reject-user")
    person, relationship = _create_person_relationship(client, token)
    fake = FakeActionDecisionService(_decision_context(person["id"], relationship["id"]))
    monkeypatch.setattr(action_decision, "service", fake)

    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        headers=_auth(token),
        json={
            "recommendation_id": "recommendation-141",
            "decision": "rejected",
            "note": "user explicitly declined",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "rejected"
    assert fake.create_calls[0][2:] == (
        "recommendation-141",
        "rejected",
        "user explicitly declined",
    )


def test_foreign_person_scope_rejected_for_context_and_decision(client):
    alice = _register(client, "test141-alice")
    bob = _register(client, "test141-bob")
    person, _ = _create_person_relationship(client, alice, "Alice Person")

    context = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/decisions/context",
        headers=_auth(bob),
    )
    decision = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        headers=_auth(bob),
        json={"decision": "rejected", "note": "must not cross scope"},
    )

    assert context.status_code == 404
    assert decision.status_code == 404
    assert "person" in context.json()["detail"].lower()
    assert "person" in decision.json()["detail"].lower()
