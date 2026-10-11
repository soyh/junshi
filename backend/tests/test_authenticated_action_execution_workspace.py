from app.api.routes import action_execution
from app.core.database import get_connection
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


class FakeActionExecutionService:
    def __init__(self, context):
        self.context = context
        self.context_calls = []
        self.create_calls = []

    def get_context(self, conn, user_id, person_id):
        self.context_calls.append((user_id, person_id))
        return self.context

    def create_execution(
        self,
        conn,
        user_id,
        person_id,
        decision_id,
        executed_at,
        note,
    ):
        self.create_calls.append(
            (user_id, person_id, decision_id, executed_at, note)
        )
        return {
            "id": "execution-created",
            "user_id": user_id,
            "person_id": person_id,
            "decision_id": decision_id,
            "executed_at": executed_at or "2026-09-19T00:00:00+00:00",
            "note": note,
            "created_at": "2026-09-19T00:00:01+00:00",
        }


def _session(user_id: str) -> str:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        return auth_session_service.create(conn, user_id).access_token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship(client, token: str, name: str = "TEST-142 Person"):
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


def _execution_context(person_id: str, relationship_id: str):
    return {
        "person": {"id": person_id, "name": "TEST-142 Person"},
        "relationship": {"id": relationship_id, "person_id": person_id},
        "decisions": [
            {
                "id": "decision-ready",
                "person_id": person_id,
                "recommendation_id": "recommendation-142",
                "decision": "confirmed",
                "note": "user confirmed",
                "created_at": "2026-09-19T00:00:00+00:00",
                "execution_status": "execution_ready",
            },
            {
                "id": "decision-rejected",
                "person_id": person_id,
                "recommendation_id": "recommendation-rejected",
                "decision": "rejected",
                "note": None,
                "created_at": "2026-09-18T23:00:00+00:00",
                "execution_status": "not_executable",
            },
            {
                "id": "decision-executed",
                "person_id": person_id,
                "recommendation_id": "recommendation-old",
                "decision": "confirmed",
                "note": None,
                "created_at": "2026-09-18T22:00:00+00:00",
                "execution_status": "executed",
            },
        ],
        "execution_constraints": {
            "must_require_confirmed_decision": True,
            "must_require_explicit_execution": True,
            "must_not_execute_rejected_decision": True,
            "must_not_execute_from_confirmation_automatically": True,
            "must_not_send": True,
            "must_not_create_outcome_automatically": True,
        },
    }


def test_product_shell_exposes_action_execution_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "action-execution-workspace",
        "load-action-execution-context",
        "action-execution-decision",
        "action-execution-candidate-detail",
        "action-execution-executed-at",
        "action-execution-note",
        "record-action-execution",
        "action-execution-status",
        "action-execution-constraints",
        "action-execution-decisions",
    ):
        assert f'id="{control_id}"' in html
    assert "Load execution context" in html
    assert "Record selected execution" in html


def test_action_execution_fragment_uses_canonical_context_and_explicit_post_only(client):
    html = client.get("/app").text
    start = html.index("const actionExecutionStatus = byId('action-execution-status')")
    end = html.index("const actionDecisionStatus = byId('action-decision-status')")
    script = html[start:end]

    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/execution-context`" in script
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/executions/${encodeURIComponent(decisionId)}`" in script
    assert "method: 'POST'" in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/decisions/context" not in script
    assert "/action-plan/decisions`" not in script
    assert "/outcomes" not in script
    assert "No message was sent and no Outcome was created." in script


def test_action_execution_requires_explicit_load_and_separate_record_click(client):
    html = client.get("/app").text
    start = html.index("const actionExecutionStatus = byId('action-execution-status')")
    end = html.index("const actionDecisionStatus = byId('action-decision-status')")
    script = html[start:end]

    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetActionExecutionWorkspace" in person_listener
    assert "loadActionExecutionContext()" not in person_listener
    assert "recordActionExecution()" not in person_listener
    assert "bind('load-action-execution-context', loadActionExecutionContext" in script
    assert "bind('record-action-execution', recordActionExecution" in script

    decision_start = html.index("const actionDecisionStatus = byId('action-decision-status')")
    decision_end = html.index("const actionPlanGenerateStatus = byId('action-plan-generate-status')")
    decision_script = html[decision_start:decision_end]
    assert "loadActionExecutionContext" not in decision_script
    assert "recordActionExecution" not in decision_script
    assert "/executions/" not in decision_script


def test_action_execution_filters_only_confirmed_execution_ready_candidates(client):
    html = client.get("/app").text
    start = html.index("const actionExecutionStatus = byId('action-execution-status')")
    end = html.index("const actionDecisionStatus = byId('action-decision-status')")
    script = html[start:end]

    assert "item.decision === 'confirmed'" in script
    assert "item.execution_status === 'execution_ready'" in script
    assert "recordActionExecutionButton.disabled = true" in script
    assert "const candidate = actionExecutionCandidates.find" in script
    assert "Select an execution-ready decision first" in script


def test_action_execution_workspace_preserves_memory_token_and_safe_dom(client):
    html = client.get("/app").text
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert "document.createElement('option')" in html
    assert "replaceChildren()" in html


def test_real_bearer_identity_flows_into_action_execution_context(client, monkeypatch):
    token = _session("test142-context-user")
    person, relationship = _create_person_relationship(client, token)
    fake = FakeActionExecutionService(_execution_context(person["id"], relationship["id"]))
    monkeypatch.setattr(action_execution, "service", fake)

    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/execution-context",
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decisions"][0]["execution_status"] == "execution_ready"
    assert body["execution_constraints"]["must_require_explicit_execution"] is True
    assert body["execution_constraints"]["must_not_create_outcome_automatically"] is True
    assert fake.context_calls == [(person["user_id"], person["id"])]


def test_explicit_execution_records_only_canonical_execution(client, monkeypatch):
    token = _session("test142-record-user")
    person, relationship = _create_person_relationship(client, token)
    fake = FakeActionExecutionService(_execution_context(person["id"], relationship["id"]))
    monkeypatch.setattr(action_execution, "service", fake)

    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/decision-ready",
        headers=_auth(token),
        json={
            "executed_at": "2026-09-19T01:02:03+00:00",
            "note": "explicit user execution record",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision_id"] == "decision-ready"
    assert fake.create_calls == [
        (
            person["user_id"],
            person["id"],
            "decision-ready",
            "2026-09-19T01:02:03+00:00",
            "explicit user execution record",
        )
    ]


def test_foreign_person_scope_rejected_for_execution_context_and_create(client):
    alice = _session("test142-alice")
    bob = _session("test142-bob")
    person, _ = _create_person_relationship(client, alice, "Alice Execution Person")

    context = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/execution-context",
        headers=_auth(bob),
    )
    execution = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/decision-foreign",
        headers=_auth(bob),
        json={"note": "scope isolation check"},
    )

    assert context.status_code == 404
    assert execution.status_code == 404
    assert "person" in context.json()["detail"].lower()
    assert execution.json()["detail"] == "action decision not found"
