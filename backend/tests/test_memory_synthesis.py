from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="记忆合成对象"):
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
            "recommendation-memory-synthesis",
            "confirmed",
            "测试确认",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "合成测试结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/memory-updates/synthesis")


def test_memory_synthesis_requires_existing_person(client):
    assert get_synthesis(client, "00000000-0000-0000-0000-000000000099").status_code == 404


def test_memory_synthesis_is_empty_without_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_synthesis(client, person["id"]).json()
    assert body["updates"] == []


def test_memory_synthesis_is_source_backed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    update = get_synthesis(client, person["id"]).json()["updates"][0]
    assert update["status"] == "proposed"
    assert update["source_decision_id"] == decision["id"]
    assert update["source_outcome_id"]
    assert update["source_candidate_id"]


def test_memory_synthesis_preserves_outcome_and_note(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "failed")
    update = get_synthesis(client, person["id"]).json()["updates"][0]
    assert update["memory"] == {
        "action_outcome": "failed",
        "note": "合成测试结果",
    }


def test_memory_synthesis_preserves_unknown_relationship_impact(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    body = get_synthesis(client, person["id"]).json()
    update = body["updates"][0]
    assert "long_term_relationship_impact" in update["unknowns"]
    assert body["memory_constraints"]["must_not_infer_relationship_impact"] is True


def test_memory_synthesis_isolated_by_person(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_confirmed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])
    assert get_synthesis(client, second["id"]).json()["updates"] == []


def test_memory_synthesis_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = get_synthesis(
        client,
        person["id"],
    )
    assert response.status_code == 200
    response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_memory_synthesis_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_confirmed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = get_synthesis(client, person["id"]).json()
    second = get_synthesis(client, person["id"]).json()
    assert first == second
    assert first["memory_constraints"]["must_not_auto_persist"] is True
