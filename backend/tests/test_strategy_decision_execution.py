from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="执行对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, decision="confirmed", recommendation_id="recommendation-a"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn, USER_ID, person_id, recommendation_id, decision, "执行测试"
        )


def execute(client, person_id, decision_id, note="已执行"):
    return client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={"note": note},
    )


def test_execution_context_requires_explicit_execution(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-context")
    assert response.status_code == 200
    body = response.json()
    assert body["decisions"] == []
    assert body["execution_constraints"]["must_require_explicit_execution"] is True
    assert body["execution_constraints"]["must_not_send"] is True


def test_execution_requires_confirmed_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "rejected")
    response = execute(client, person["id"], decision["id"])
    assert response.status_code == 409


def test_execution_rejects_unknown_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = execute(client, person["id"], "missing")
    assert response.status_code == 404


def test_execution_persists_confirmed_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    response = execute(client, person["id"], decision["id"])
    assert response.status_code == 201
    body = response.json()
    assert body["decision_id"] == decision["id"]
    assert body["person_id"] == person["id"]


def test_execution_is_single_step_per_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    assert execute(client, person["id"], decision["id"]).status_code == 201
    response = execute(client, person["id"], decision["id"])
    assert response.status_code == 409


def test_execution_is_blocked_after_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    assert execute(client, person["id"], decision["id"]).status_code == 201
    outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        json={"outcome": "completed", "note": "结果"},
    )
    assert outcome.status_code == 201
    response = execute(client, person["id"], decision["id"])
    assert response.status_code == 409


def test_execution_is_person_isolated(client):
    first = create_person(client, "执行A")
    second = create_person(client, "执行B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    response = execute(client, second["id"], decision["id"])
    assert response.status_code == 404


def test_execution_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/executions/{decision['id']}",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
        json={},
    )
    assert response.status_code == 404
