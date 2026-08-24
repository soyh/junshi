from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="记忆学习综合对象"):
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
            "记忆学习综合测试决策",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "记忆学习综合测试结果"},
    )
    assert response.status_code == 201
    return response.json()


def get_synthesis(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/memory-updates/learning-synthesis")


def test_memory_learning_synthesis_is_empty_without_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    body = get_synthesis(client, person["id"]).json()
    assert body["updates"] == []


def test_memory_learning_synthesis_links_recommendation_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    outcome = create_outcome(client, person["id"], decision["id"])
    update = get_synthesis(client, person["id"]).json()["updates"][0]
    provenance = update["learning_provenance"]
    assert provenance["status"] == "observed_outcome"
    assert provenance["recommendation_id"] == "recommendation-a"
    assert provenance["source_decision_id"] == decision["id"]
    assert provenance["source_outcome_id"] == outcome["id"]


def test_memory_learning_synthesis_preserves_signal_counts(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "failed")
    update = get_synthesis(client, person["id"]).json()["updates"][0]
    provenance = update["learning_provenance"]
    assert provenance["outcome_observed_count"] == 2
    assert provenance["outcome_unknown_count"] == 0
    assert provenance["outcome_counts"] == {"completed": 1, "skipped": 0, "failed": 1}


def test_memory_learning_synthesis_preserves_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    body = get_synthesis(client, person["id"]).json()
    assert "long_term_relationship_impact" in body["updates"][0]["unknowns"]
    assert body["memory_constraints"]["must_not_infer_recommendation_quality"] is True
    assert body["memory_constraints"]["must_not_infer_success"] is True
    assert body["memory_constraints"]["must_not_infer_relationship_impact"] is True


def test_memory_learning_synthesis_is_person_isolated(client):
    first = create_person(client, "综合对象A")
    second = create_person(client, "综合对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])
    assert get_synthesis(client, second["id"]).json()["updates"] == []


def test_memory_learning_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_memory_learning_synthesis_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = get_synthesis(client, person["id"]).json()
    second = get_synthesis(client, person["id"]).json()
    assert first == second
    assert first["memory_constraints"]["must_not_auto_persist"] is True
