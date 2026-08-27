from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略学习汇总对象"):
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
            conn, USER_ID, person_id, recommendation_id, decision, "策略学习汇总测试"
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
        json={"outcome": value, "note": "策略学习汇总结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    response = client.get(f"/api/v1/persons/{person_id}/strategy-decision/learning-synthesis")
    assert response.status_code == 200
    return response.json()


def test_learning_synthesis_counts_observed_and_unknown_states(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    observed = seed_decision(person["id"], "recommendation-a")
    unknown = seed_decision(person["id"], "recommendation-b")
    execute(client, person["id"], observed["id"])
    outcome(client, person["id"], observed["id"])

    body = get_synthesis(client, person["id"])

    assert body["learning_summary"] == {
        "total_decision_count": 2,
        "learning_candidate_count": 1,
        "unknown_count": 1,
    }
    assert body["learning_candidate_decision_ids"] == [observed["id"]]
    assert body["unknown_decision_ids"] == [unknown["id"]]


def test_learning_synthesis_aggregates_observed_recommendation_counts(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-a")
    unknown = seed_decision(person["id"], "recommendation-a", "rejected")
    execute(client, person["id"], first["id"])
    outcome(client, person["id"], first["id"], "completed")
    execute(client, person["id"], second["id"])
    outcome(client, person["id"], second["id"], "failed")

    body = get_synthesis(client, person["id"])

    assert body["recommendation_observed_counts"] == {"recommendation-a": 2}
    assert body["learning_candidate_decision_ids"] == [first["id"], second["id"]]
    assert unknown["id"] in body["unknown_decision_ids"]


def test_learning_synthesis_never_treats_execution_as_learning(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    execute(client, person["id"], decision["id"])

    body = get_synthesis(client, person["id"])

    assert body["learning_summary"]["learning_candidate_count"] == 0
    assert body["learning_candidate_decision_ids"] == []
    assert body["unknown_decision_ids"] == [decision["id"]]


def test_learning_synthesis_preserves_non_actionable_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-rejected", "rejected")

    body = get_synthesis(client, person["id"])
    item = body["learning_items"][0]

    assert item["learning_eligible"] is False
    assert item["learning_status"] == "outcome_unknown"
    assert decision["id"] in body["unknown_decision_ids"]


def test_learning_synthesis_is_deterministic_and_person_isolated(client):
    first = create_person(client, "策略汇总A")
    second = create_person(client, "策略汇总B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    execute(client, first["id"], decision["id"])
    outcome(client, first["id"], decision["id"])

    first_body = get_synthesis(client, first["id"])
    second_body = get_synthesis(client, first["id"])
    isolated = get_synthesis(client, second["id"])

    assert first_body == second_body
    assert len(first_body["learning_items"]) == 1
    assert isolated["learning_items"] == []
    assert isolated["learning_candidate_decision_ids"] == []


def test_learning_synthesis_exposes_non_inference_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    constraints = get_synthesis(client, person["id"])["synthesis_constraints"]

    assert constraints == {
        "deterministic": True,
        "read_only": True,
        "source_backed_only": True,
        "must_preserve_unknowns": True,
        "must_not_infer_recommendation_quality": True,
        "must_not_infer_success": True,
        "must_not_infer_relationship_impact": True,
        "must_not_change_relationship": True,
        "must_not_auto_execute": True,
        "must_not_auto_send": True,
        "must_not_call_llm": True,
    }


def test_learning_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    execute(client, person["id"], decision["id"])
    outcome(client, person["id"], decision["id"])

    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/learning-synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
