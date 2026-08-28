from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="学习策略综合对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn, USER_ID, person_id, recommendation_id, "confirmed", "策略综合测试决策"
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "策略综合测试结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/learning-strategy/synthesis")


def test_learning_strategy_synthesis_is_empty_without_observed_outcomes(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_synthesis(client, person["id"]).json()
    assert body["candidates"] == []


def test_learning_strategy_synthesis_preserves_recommendation_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"], "completed")
    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["recommendation_id"] == "recommendation-a"
    assert candidate["observed_outcome_count"] == 1
    assert candidate["outcome_counts"] == {"completed": 1, "skipped": 0, "failed": 0}


def test_learning_strategy_synthesis_counts_memory_updates(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "failed")
    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["observed_outcome_count"] == 2
    assert candidate["memory_update_count"] == 2


def test_learning_strategy_synthesis_preserves_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-unknown")
    create_outcome(client, person["id"], decision["id"])
    body = get_synthesis(client, person["id"]).json()
    candidate = body["candidates"][0]
    assert candidate["synthesis_status"] == "source_backed_candidate"
    assert "recommendation_quality" in candidate["unknowns"]
    assert body["strategy_constraints"]["must_not_turn_learning_into_fact"] is True


def test_learning_strategy_synthesis_preserves_explicit_source_provenance(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-source")
    create_outcome(client, person["id"], decision["id"], "completed")

    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["source"] == {
        "recommendation_id": "recommendation-source",
        "observed_outcomes": 1,
        "unknown_outcomes": 0,
    }


def test_learning_strategy_synthesis_source_provenance_does_not_create_inference(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-source")
    create_outcome(client, person["id"], decision["id"], "completed")

    body = get_synthesis(client, person["id"]).json()
    candidate = body["candidates"][0]
    assert candidate["source"]["observed_outcomes"] == candidate["observed_outcome_count"]
    assert candidate["source"]["unknown_outcomes"] == candidate["unknown_outcome_count"]
    assert candidate["unknowns"] == [
        "recommendation_quality",
        "success",
        "relationship_impact",
    ]
    assert body["strategy_constraints"]["must_not_turn_learning_into_fact"] is True


def test_learning_strategy_synthesis_source_provenance_includes_decision_cardinality(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-cardinality")
    second = seed_decision(person["id"], "recommendation-cardinality")
    create_outcome(client, person["id"], first["id"], "completed")

    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["source"] == {
        "recommendation_id": "recommendation-cardinality",
        "decision_count": 2,
        "decision_counts": {"confirmed": 2, "proposed": 0, "cancelled": 0, "executed": 0},
        "observed_outcomes": 1,
        "unknown_outcomes": 1,
    }
    assert second["id"] != first["id"]


def test_learning_strategy_synthesis_source_counts_remain_distinct_from_outcome_counts(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-cardinality")
    second = seed_decision(person["id"], "recommendation-cardinality")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "failed")

    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["source"]["decision_count"] == 2
    assert candidate["source"]["observed_outcomes"] == 2
    assert candidate["source"]["unknown_outcomes"] == 0
    assert candidate["outcome_counts"] == {"completed": 1, "skipped": 0, "failed": 1}


def test_learning_strategy_synthesis_is_person_isolated(client):
    first = create_person(client, "策略综合A")
    second = create_person(client, "策略综合B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])
    assert get_synthesis(client, second["id"]).json()["candidates"] == []


def test_learning_strategy_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_learning_strategy_synthesis_is_deterministic_and_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    first = get_synthesis(client, person["id"]).json()
    second = get_synthesis(client, person["id"]).json()
    assert first == second
    assert first["strategy_constraints"]["must_not_auto_execute"] is True
    assert first["strategy_constraints"]["must_not_auto_send"] is True
    assert first["strategy_constraints"]["must_not_rank_recommendations"] is True
