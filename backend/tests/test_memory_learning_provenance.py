from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="记忆学习来源对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id="recommendation-learning"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            recommendation_id,
            "confirmed",
            "学习来源测试决策",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "学习来源测试结果"},
    )
    assert response.status_code == 201
    return response.json()


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/memory-updates/context")


def test_memory_candidate_exposes_recommendation_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    candidate = get_context(client, person["id"]).json()["candidates"][0]
    assert candidate["recommendation_id"] == "recommendation-a"


def test_memory_candidate_exposes_observed_learning_source(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    outcome = create_outcome(client, person["id"], decision["id"])
    candidate = get_context(client, person["id"]).json()["candidates"][0]
    assert candidate["learning_source"] == {
        "status": "observed_outcome",
        "decision_id": decision["id"],
        "outcome_id": outcome["id"],
        "recommendation_id": "recommendation-learning",
    }


def test_memory_learning_provenance_is_source_backed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    body = get_context(client, person["id"]).json()
    assert body["memory_constraints"]["must_preserve_learning_provenance"] is True
    assert body["candidates"][0]["learning_source"]["outcome_id"]


def test_memory_learning_provenance_preserves_unknown_boundary(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    body = get_context(client, person["id"]).json()
    assert body["candidates"] == []
    assert body["memory_constraints"]["must_not_infer_from_missing_outcome"] is True


def test_memory_learning_provenance_is_person_isolated(client):
    first = create_person(client, "来源对象A")
    second = create_person(client, "来源对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])
    assert get_context(client, second["id"]).json()["candidates"] == []


def test_memory_learning_provenance_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_memory_learning_provenance_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = get_context(client, person["id"]).json()
    second = get_context(client, person["id"]).json()
    assert first == second
    assert first["memory_constraints"]["must_not_auto_persist"] is True
