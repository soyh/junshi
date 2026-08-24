from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="记忆持久化对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_confirmed_decision(person_id):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            "recommendation-memory-persist",
            "confirmed",
            "测试确认",
        )


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "持久化测试结果"},
    )
    assert response.status_code == 201


def test_memory_persistence_requires_existing_candidate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/missing-candidate/persist"
    )
    assert response.status_code == 404


def test_memory_persistence_requires_source_backed_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/missing-candidate/persist"
    )
    assert response.status_code == 404


def test_memory_persistence_explicitly_persists_synthesized_candidate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/synthesis"
    ).json()
    candidate_id = synthesis["updates"][0]["source_candidate_id"]

    response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist"
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "persisted"
    assert body["source_candidate_id"] == candidate_id
    assert body["source_decision_id"] == decision["id"]


def test_memory_persistence_is_idempotent_by_candidate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    candidate_id = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/synthesis"
    ).json()["updates"][0]["source_candidate_id"]

    first = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist"
    )
    second = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist"
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()


def test_memory_persistence_isolated_by_person(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_confirmed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])
    candidate_id = client.get(
        f"/api/v1/persons/{first['id']}/memory-updates/synthesis"
    ).json()["updates"][0]["source_candidate_id"]

    response = client.post(
        f"/api/v1/persons/{second['id']}/memory-updates/{candidate_id}/persist"
    )
    assert response.status_code == 404


def test_memory_persistence_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    candidate_id = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/synthesis"
    ).json()["updates"][0]["source_candidate_id"]

    response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_memory_persistence_preserves_unknowns_by_not_changing_relationship(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    before = client.get(f"/api/v1/persons/{person['id']}/profile").json()
    candidate_id = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/synthesis"
    ).json()["updates"][0]["source_candidate_id"]
    response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist"
    )
    assert response.status_code == 201
    after = client.get(f"/api/v1/persons/{person['id']}/profile").json()
    assert before["relationship"] == after["relationship"]
