from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="学习策略对象"):
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
            conn,
            USER_ID,
            person_id,
            recommendation_id,
            "confirmed",
            "学习策略测试决策",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "学习策略测试结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/learning-strategy/synthesis")


def test_learning_strategy_synthesis_exposes_observed_candidate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-source")
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
        "decision_count": 1,
        "decision_counts": {"confirmed": 1, "rejected": 0},
        "observed_outcomes": 1,
        "unknown_outcomes": 0,
    }


def test_learning_strategy_synthesis_source_provenance_does_not_create_inference(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-source")
    create_outcome(client, person["id"], decision["id"])

    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["source"]["recommendation_id"] == "recommendation-source"
    assert candidate["source"]["observed_outcomes"] == 1
    assert candidate["source"]["unknown_outcomes"] == 0
    assert candidate["source"]["decision_count"] == 1
    assert candidate["source"]["decision_counts"] == {"confirmed": 1, "rejected": 0}
    assert candidate["unknowns"] == [
        "recommendation_quality",
        "success",
        "relationship_impact",
    ]


def test_learning_strategy_synthesis_keeps_unobserved_outcome_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-pending")

    body = get_synthesis(client, person["id"]).json()
    candidate = body["candidates"][0]
    assert candidate["synthesis_status"] == "outcome_unknown"
    assert candidate["source"]["decision_count"] == 1
    assert candidate["source"]["decision_counts"] == {"confirmed": 1, "rejected": 0}
    assert candidate["source"]["observed_outcomes"] == 0
    assert candidate["source"]["unknown_outcomes"] == 1
