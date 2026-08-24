from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="记忆测试对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201
    return response.json()


def seed_confirmed_decision(person_id):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            "recommendation-seeded-for-memory-test",
            "confirmed",
            "测试确认",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "记忆测试结果"},
    )
    assert response.status_code == 201
    return response.json()


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/memory-updates/context")


def test_memory_update_context_requires_existing_person(client):
    assert get_context(client, "00000000-0000-0000-0000-000000000099").status_code == 404


def test_memory_update_context_is_empty_without_outcomes(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_context(client, person["id"]).json()
    assert body["candidates"] == []
    assert body["memory_constraints"]["must_not_auto_persist"] is True


def test_memory_update_candidate_is_source_backed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    outcome = create_outcome(client, person["id"], decision["id"])
    body = get_context(client, person["id"]).json()
    candidate = body["candidates"][0]
    assert candidate["status"] == "proposed"
    assert candidate["source_decision_id"] == decision["id"]
    assert candidate["source_outcome_id"] == outcome["id"]


def test_memory_update_candidate_preserves_completed_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "completed")
    candidate = get_context(client, person["id"]).json()["candidates"][0]
    assert candidate["content"]["outcome"] == "completed"
    assert candidate["content"]["note"] == "记忆测试结果"


def test_memory_update_candidate_preserves_failed_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "failed")
    candidate = get_context(client, person["id"]).json()["candidates"][0]
    assert candidate["content"]["outcome"] == "failed"


def test_memory_update_candidate_preserves_skipped_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "skipped")
    candidate = get_context(client, person["id"]).json()["candidates"][0]
    assert candidate["content"]["outcome"] == "skipped"


def test_memory_update_isolated_by_person(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_confirmed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])
    assert get_context(client, second["id"]).json()["candidates"] == []


def test_memory_update_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_memory_update_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = get_context(client, person["id"]).json()
    second = get_context(client, person["id"]).json()
    assert first == second
    assert first["memory_constraints"]["must_not_change_relationship"] is True
