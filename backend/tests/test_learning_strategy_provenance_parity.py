from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client):
    response = client.post("/api/v1/persons", json={"name": "学习策略来源一致性对象"})
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
            conn, USER_ID, person_id, recommendation_id, "confirmed", "来源一致性测试决策"
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "来源一致性测试结果"},
    )
    assert response.status_code == 201


def seed_mixed_feedback(client, person_id):
    observed = seed_decision(person_id, "recommendation-parity")
    unknown = seed_decision(person_id, "recommendation-parity")
    create_outcome(client, person_id, observed["id"], "completed")
    return observed, unknown


def test_learning_strategy_provenance_matches_action_feedback_learning_input(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_mixed_feedback(client, person["id"])

    learning = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/learning-input"
    ).json()
    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    ).json()

    source = learning["items"][0]["source"]
    candidate = synthesis["candidates"][0]
    assert candidate["source"] == source
    assert candidate["source"]["decision_count"] == 2
    assert candidate["source"]["observed_outcomes"] == 1
    assert candidate["source"]["unknown_outcomes"] == 1


def test_learning_strategy_provenance_matches_strategic_reply_projection(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_mixed_feedback(client, person["id"])

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    ).json()
    strategic_reply = client.get(
        f"/api/v1/persons/{person['id']}/strategic-reply/context"
    ).json()

    source = synthesis["candidates"][0]["source"]
    projected = strategic_reply["learning_strategy"]["candidates"][0]["source"]
    assert projected == source
    assert strategic_reply["learning_strategy"]["constraints"]["must_not_infer_success"] is True
    assert strategic_reply["learning_strategy"]["constraints"]["must_not_infer_relationship_impact"] is True


def test_learning_strategy_provenance_matches_action_plan_projection(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_mixed_feedback(client, person["id"])

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    ).json()
    action_plan = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/context"
    ).json()

    source = synthesis["candidates"][0]["source"]
    projected = action_plan["learning_strategy"]["candidates"][0]["source"]
    assert projected == source
    assert action_plan["learning_strategy"]["constraints"]["must_not_infer_success"] is True
    assert action_plan["learning_strategy"]["constraints"]["must_not_change_relationship"] is True


def test_learning_strategy_provenance_parity_preserves_unknowns_and_read_only_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_mixed_feedback(client, person["id"])

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    ).json()
    candidate = synthesis["candidates"][0]
    constraints = synthesis["strategy_constraints"]

    assert candidate["unknowns"] == [
        "recommendation_quality",
        "success",
        "relationship_impact",
    ]
    assert candidate["source"]["unknown_outcomes"] == 1
    assert constraints["must_preserve_unknowns"] is True
    assert constraints["must_not_turn_learning_into_fact"] is True
    assert constraints["must_not_rank_recommendations"] is True
    assert constraints["must_not_auto_execute"] is True
    assert constraints["must_not_auto_send"] is True
    assert constraints["must_not_call_llm"] is True
