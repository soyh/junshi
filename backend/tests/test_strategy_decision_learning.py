from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略学习对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id, decision="confirmed"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn, USER_ID, person_id, recommendation_id, decision, "策略学习测试"
        )


def execute(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={},
    )
    assert response.status_code == 201


def outcome(client, person_id, decision_id, value="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": value, "note": "策略学习结果"},
    )
    assert response.status_code == 201


def get_learning_input(client, person_id):
    response = client.get(f"/api/v1/persons/{person_id}/strategy-decision/learning-input")
    assert response.status_code == 200
    return response.json()


def test_strategy_decision_learning_exposes_observed_lifecycle_item(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-observed")
    execute(client, person["id"], decision["id"])
    outcome(client, person["id"], decision["id"], "completed")

    body = get_learning_input(client, person["id"])
    item = body["items"][0]

    assert item["decision_id"] == decision["id"]
    assert item["recommendation_id"] == "recommendation-observed"
    assert item["result_status"] == "outcome_recorded"
    assert item["feedback_status"] == "outcome_observed"
    assert item["learning_status"] == "observed_feedback"
    assert item["learning_eligible"] is True
    assert item["source"]["decision_id"] == decision["id"]
    assert item["source"]["outcome_id"] == item["outcome"]["id"]


def test_strategy_decision_learning_preserves_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-unknown")

    body = get_learning_input(client, person["id"])
    item = body["items"][0]

    assert item["decision_id"] == decision["id"]
    assert item["result_status"] == "confirmed_pending_execution"
    assert item["feedback_status"] == "outcome_unknown"
    assert item["learning_status"] == "outcome_unknown"
    assert item["learning_eligible"] is False
    assert item["outcome"] is None
    assert item["source"]["outcome_id"] is None


def test_strategy_decision_learning_does_not_treat_execution_as_learning(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-executed")
    execute(client, person["id"], decision["id"])

    item = get_learning_input(client, person["id"])["items"][0]

    assert item["result_status"] == "executed_pending_outcome"
    assert item["feedback_status"] == "outcome_unknown"
    assert item["learning_eligible"] is False


def test_strategy_decision_learning_keeps_rejected_decisions_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-rejected", "rejected")

    item = get_learning_input(client, person["id"])["items"][0]

    assert item["decision_status"] == "rejected"
    assert item["result_status"] == "not_actionable"
    assert item["feedback_status"] == "outcome_unknown"
    assert item["learning_eligible"] is False


def test_strategy_decision_learning_is_deterministic_and_person_isolated(client):
    first = create_person(client, "策略学习A")
    second = create_person(client, "策略学习B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    execute(client, first["id"], decision["id"])
    outcome(client, first["id"], decision["id"])

    first_body = get_learning_input(client, first["id"])
    second_body = get_learning_input(client, first["id"])
    isolated = get_learning_input(client, second["id"])

    assert first_body == second_body
    assert len(first_body["items"]) == 1
    assert isolated["items"] == []


def test_strategy_decision_learning_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a")

    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/learning-input",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_strategy_decision_learning_exposes_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    constraints = get_learning_input(client, person["id"])["learning_constraints"]

    assert constraints == {
        "source_backed": True,
        "must_preserve_unknowns": True,
        "must_not_infer_recommendation_quality": True,
        "must_not_infer_success": True,
        "must_not_infer_relationship_impact": True,
        "must_not_change_relationship": True,
        "must_not_auto_execute": True,
        "must_not_auto_send": True,
        "must_not_call_llm": True,
    }
