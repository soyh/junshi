from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="执行综合对象"):
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
            conn, USER_ID, person_id, recommendation_id, decision, "执行综合测试"
        )


def execute(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={},
    )
    assert response.status_code == 201
    return response.json()


def test_execution_synthesis_reports_pending_confirmed_decisions(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    assert response.status_code == 200
    body = response.json()
    assert body["pending_decision_ids"] == [decision["id"]]
    assert body["execution_summary"]["pending_execution_count"] == 1


def test_execution_synthesis_removes_executed_decision_from_pending(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execution = execute(client, person["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    assert response.status_code == 200
    body = response.json()
    assert body["pending_decision_ids"] == []
    assert body["execution_summary"]["executed_count"] == 1
    assert body["execution_summary"]["latest_execution_id"] == execution["id"]


def test_execution_synthesis_keeps_outcome_history_separate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execute(client, person["id"], decision["id"])
    outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        json={"outcome": "completed", "note": "结果"},
    )
    assert outcome.status_code == 201
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    assert response.status_code == 200
    body = response.json()
    assert body["pending_decision_ids"] == []
    assert body["execution_summary"]["executed_count"] == 1
    assert body["execution_summary"]["outcome_recorded_count"] == 1


def test_execution_synthesis_excludes_rejected_decisions(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    rejected = seed_decision(person["id"], "rejected", "recommendation-rejected")
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    assert response.status_code == 200
    body = response.json()
    assert rejected["id"] not in body["pending_decision_ids"]
    assert body["execution_summary"]["confirmed_count"] == 0


def test_execution_synthesis_counts_multiple_decisions(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "confirmed", "recommendation-a")
    second = seed_decision(person["id"], "confirmed", "recommendation-b")
    execute(client, person["id"], first["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    assert response.status_code == 200
    body = response.json()
    assert body["execution_summary"]["confirmed_count"] == 2
    assert body["execution_summary"]["executed_count"] == 1
    assert body["pending_decision_ids"] == [second["id"]]


def test_execution_synthesis_is_deterministic_for_single_person(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    first = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    second = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["pending_decision_ids"] == [decision["id"]]


def test_execution_synthesis_is_person_isolated(client):
    first = create_person(client, "综合A")
    second = create_person(client, "综合B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    execute(client, first["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{second['id']}/strategy-decision/execution-synthesis")
    assert response.status_code == 200
    assert response.json()["executions"] == []
    assert response.json()["pending_decision_ids"] == []


def test_execution_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execute(client, person["id"], decision["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/execution-synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
