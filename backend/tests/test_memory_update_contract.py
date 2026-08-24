from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client):
    response = client.post("/api/v1/persons", json={"name": "记忆契约对象"})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            "recommendation-memory-contract",
            "confirmed",
            "确认行动",
        )


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "执行完成"},
    )
    assert response.status_code == 201


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/memory-updates/context")


def test_memory_update_candidate_has_stable_source_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])

    body = get_context(client, person["id"]).json()
    candidate = body["candidates"][0]
    assert candidate["source_decision_id"] == decision["id"]
    assert candidate["source_outcome_id"]
    assert candidate["source_created_at"]


def test_memory_update_contract_forbids_inference_and_persistence(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_context(client, person["id"]).json()
    constraints = body["memory_constraints"]
    assert constraints["must_have_stable_source_identity"] is True
    assert constraints["must_not_infer_from_missing_outcome"] is True
    assert constraints["must_not_auto_persist"] is True
