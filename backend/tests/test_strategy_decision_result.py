from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="结果对象"):
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
            conn, USER_ID, person_id, recommendation_id, decision, "结果测试"
        )


def execute(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={},
    )
    assert response.status_code == 201


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "结果"},
    )
    assert response.status_code == 201


def test_result_context_classifies_confirmed_pending_execution(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/result-context")
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["id"] == decision["id"]
    assert item["result_status"] == "confirmed_pending_execution"
    assert item["execution"] is None
    assert item["outcome"] is None


def test_result_context_classifies_execution_without_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execute(client, person["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/result-context")
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["result_status"] == "executed_pending_outcome"
    assert item["execution"] is not None
    assert item["outcome"] is None


def test_result_context_classifies_recorded_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execute(client, person["id"], decision["id"])
    create_outcome(client, person["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/result-context")
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["result_status"] == "outcome_recorded"
    assert item["execution"] is not None
    assert item["outcome"] is not None


def test_result_context_keeps_rejected_decision_non_actionable(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "rejected")
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/result-context")
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["id"] == decision["id"]
    assert item["result_status"] == "not_actionable"


def test_result_context_preserves_execution_and_outcome_as_distinct_records(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execute(client, person["id"], decision["id"])
    create_outcome(client, person["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/result-context")
    body = response.json()
    item = body["results"][0]
    assert item["execution"]["decision_id"] == decision["id"]
    assert item["outcome"]["decision_id"] == decision["id"]
    assert body["result_constraints"]["execution_is_distinct_from_outcome"] is True


def test_result_context_is_person_isolated(client):
    first = create_person(client, "结果A")
    second = create_person(client, "结果B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    execute(client, first["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{second['id']}/strategy-decision/result-context")
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_result_context_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/result-context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
