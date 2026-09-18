from app.api.routes import action_outcome
from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


class FakeOutcomeService:
    def __init__(self):
        self.list_calls = []
        self.create_calls = []

    def list_outcomes(self, conn, user_id, person_id):
        self.list_calls.append((user_id, person_id))
        return [
            {
                "id": "outcome-existing",
                "user_id": user_id,
                "person_id": person_id,
                "decision_id": "decision-existing",
                "outcome": "completed",
                "note": "existing outcome",
                "created_at": "2026-09-19T00:00:00+00:00",
            }
        ]

    def create_outcome(self, conn, user_id, person_id, decision_id, outcome, note):
        self.create_calls.append((user_id, person_id, decision_id, outcome, note))
        return {
            "id": "outcome-created",
            "user_id": user_id,
            "person_id": person_id,
            "decision_id": decision_id,
            "outcome": outcome,
            "note": note,
            "created_at": "2026-09-19T00:00:01+00:00",
        }


def _session(user_id: str) -> str:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        return auth_session_service.create(conn, user_id).access_token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship(client, token: str, name: str = "TEST-143 Person"):
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


def test_product_shell_exposes_outcome_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "action-outcome-workspace",
        "load-action-outcome-context",
        "action-outcome-decision",
        "action-outcome-candidate-detail",
        "action-outcome-state",
        "action-outcome-note",
        "record-action-outcome",
        "action-outcome-status",
        "action-outcome-history",
    ):
        assert f'id="{control_id}"' in html
    assert "Load outcome context" in html
    assert "Record selected outcome" in html


def test_outcome_fragment_uses_canonical_execution_and_outcome_endpoints_only(client):
    html = client.get("/app").text
    start = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    end = html.index("const actionExecutionStatus = byId('action-execution-status')")
    script = html[start:end]

    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/execution-context`" in script
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/outcomes`" in script
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/outcomes/${encodeURIComponent(decisionId)}`" in script
    assert "method: 'POST'" in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/feedback" not in script
    assert "learning-synthesis" not in script
    assert "re-analysis" not in script
    assert "No Feedback, Learning, Re-analysis, message send, or Relationship change was started." in script


def test_outcome_requires_explicit_load_and_separate_record_click(client):
    html = client.get("/app").text
    start = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    end = html.index("const actionExecutionStatus = byId('action-execution-status')")
    script = html[start:end]

    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetActionOutcomeWorkspace" in person_listener
    assert "loadActionOutcomeContext()" not in person_listener
    assert "recordActionOutcome()" not in person_listener
    assert "bind('load-action-outcome-context', loadActionOutcomeContext" in script
    assert "bind('record-action-outcome', recordActionOutcome" in script

    execution_start = html.index("const actionExecutionStatus = byId('action-execution-status')")
    execution_end = html.index("const actionDecisionStatus = byId('action-decision-status')")
    execution_script = html[execution_start:execution_end]
    assert "loadActionOutcomeContext" not in execution_script
    assert "recordActionOutcome" not in execution_script
    assert "/action-plan/outcomes" not in execution_script


def test_outcome_candidates_are_only_confirmed_executed_decisions(client):
    html = client.get("/app").text
    start = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    end = html.index("const actionExecutionStatus = byId('action-execution-status')")
    script = html[start:end]

    assert "item.decision === 'confirmed'" in script
    assert "item.execution_status === 'executed'" in script
    assert "item.execution_status === 'outcome_recorded'" not in script
    assert "recordActionOutcomeButton.disabled = true" in script
    assert "Select an executed decision first" in script


def test_outcome_states_memory_token_and_safe_dom_are_preserved(client):
    html = client.get("/app").text
    assert '<option value="completed">completed</option>' in html
    assert '<option value="skipped">skipped</option>' in html
    assert '<option value="failed">failed</option>' in html
    assert "['completed', 'skipped', 'failed'].includes(outcome)" in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert "document.createElement('option')" in html
    assert "replaceChildren()" in html


def test_real_bearer_identity_flows_into_outcome_history(client, monkeypatch):
    token = _session("test143-history-user")
    person, _ = _create_person_relationship(client, token)
    fake = FakeOutcomeService()
    monkeypatch.setattr(action_outcome, "service", fake)

    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes",
        headers=_auth(token),
    )

    assert response.status_code == 200
    assert response.json()[0]["outcome"] == "completed"
    assert fake.list_calls == [(person["user_id"], person["id"])]


def test_real_bearer_identity_and_payload_flow_into_explicit_outcome(client, monkeypatch):
    token = _session("test143-create-user")
    person, _ = _create_person_relationship(client, token)
    fake = FakeOutcomeService()
    monkeypatch.setattr(action_outcome, "service", fake)

    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/decision-ready",
        headers=_auth(token),
        json={"outcome": "failed", "note": "explicit result"},
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "failed"
    assert fake.create_calls == [
        (
            person["user_id"],
            person["id"],
            "decision-ready",
            "failed",
            "explicit result",
        )
    ]


def test_canonical_outcome_requires_execution_is_scope_isolated_and_single_per_decision(client):
    alice_token = _session("test143-alice")
    bob_token = _session("test143-bob")
    person, _ = _create_person_relationship(client, alice_token, "Alice Outcome Person")

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-143",
            "confirmed",
            "confirmed explicitly",
        )

    before_execution = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        headers=_auth(alice_token),
        json={"outcome": "completed"},
    )
    assert before_execution.status_code == 409
    assert before_execution.json()["detail"] == "outcome requires an executed action decision"

    with get_connection() as conn:
        ActionExecutionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            decision["id"],
            None,
            "executed explicitly",
        )

    foreign = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        headers=_auth(bob_token),
        json={"outcome": "completed"},
    )
    assert foreign.status_code == 404

    created = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        headers=_auth(alice_token),
        json={"outcome": "completed", "note": "observed result"},
    )
    assert created.status_code == 201
    assert created.json()["decision_id"] == decision["id"]

    duplicate = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        headers=_auth(alice_token),
        json={"outcome": "failed"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "action decision already has an outcome"
