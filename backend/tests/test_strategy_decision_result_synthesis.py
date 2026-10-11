from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="结果综合对象"):
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
            conn, USER_ID, person_id, recommendation_id, decision, "结果综合测试"
        )


def execute(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={},
    )
    assert response.status_code == 201


def outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    response = client.get(f"/api/v1/persons/{person_id}/strategy-decision/result-synthesis")
    assert response.status_code == 200
    return response.json()


def test_result_synthesis_counts_result_states(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    pending = seed_decision(client_person := person["id"], "confirmed", "recommendation-a")
    executed = seed_decision(client_person, "confirmed", "recommendation-b")
    completed = seed_decision(client_person, "confirmed", "recommendation-c")
    rejected = seed_decision(client_person, "rejected", "recommendation-d")
    execute(client, client_person, executed["id"])
    execute(client, client_person, completed["id"])
    outcome(client, client_person, completed["id"])
    body = get_synthesis(client, client_person)
    assert body["result_summary"]["total_decision_count"] == 4
    assert body["result_summary"]["confirmed_pending_execution_count"] == 1
    assert body["result_summary"]["executed_pending_outcome_count"] == 1
    assert body["result_summary"]["outcome_recorded_count"] == 1
    assert body["result_summary"]["not_actionable_count"] == 1
    assert body["actionable_decision_ids"] == [pending["id"], executed["id"]]


def test_result_synthesis_marks_only_pending_execution_and_pending_outcome_actionable(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    pending = seed_decision(person["id"], "confirmed", "recommendation-pending")
    done = seed_decision(person["id"], "confirmed", "recommendation-done")
    execute(client, person["id"], done["id"])
    outcome(client, person["id"], done["id"])
    body = get_synthesis(client, person["id"])
    assert body["actionable_decision_ids"] == [pending["id"]]


def test_result_synthesis_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "confirmed", "recommendation-a")
    first = get_synthesis(client, person["id"])
    second = get_synthesis(client, person["id"])
    assert first == second


def test_result_synthesis_preserves_result_records(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    execute(client, person["id"], decision["id"])
    body = get_synthesis(client, person["id"])
    assert len(body["results"]) == 1
    assert body["results"][0]["execution"]["decision_id"] == decision["id"]
    assert body["results"][0]["outcome"] is None


def test_result_synthesis_excludes_rejected_decision_from_actionable(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    rejected = seed_decision(person["id"], "rejected")
    body = get_synthesis(client, person["id"])
    assert rejected["id"] not in body["actionable_decision_ids"]


def test_result_synthesis_is_person_isolated(client):
    first = create_person(client, "综合A")
    second = create_person(client, "综合B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    execute(client, first["id"], decision["id"])
    body = get_synthesis(client, second["id"])
    assert body["results"] == []
    assert body["actionable_decision_ids"] == []


def test_result_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/result-synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
