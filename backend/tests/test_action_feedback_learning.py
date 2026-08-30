from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="学习输入对象"):
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
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            recommendation_id,
            decision,
            "用户决策",
        )


def create_outcome(client, person_id, decision_id, outcome):
    execution = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={"note": "测试执行"},
    )
    assert execution.status_code == 201

    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "结果已记录"},
    )
    assert response.status_code == 201


def get_learning_input(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/feedback/learning-input")


def test_learning_input_exposes_observed_feedback(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"], "completed")
    response = get_learning_input(client, person["id"])
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["recommendation_id"] == "recommendation-a"
    assert item["learning_status"] == "observed_feedback"
    assert item["outcome_observed_count"] == 1


def test_learning_input_preserves_unknown_outcomes(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a", "rejected")
    item = get_learning_input(client, person["id"]).json()["items"][0]
    assert item["learning_status"] == "outcome_unknown"
    assert item["outcome_unknown_count"] == 1
    assert "success" in item["unknowns"]


def test_learning_input_keeps_signal_counts_source_backed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-a", "rejected")
    create_outcome(client, person["id"], first["id"], "failed")
    item = get_learning_input(client, person["id"]).json()["items"][0]
    assert item["decision_count"] == 2
    assert item["decision_counts"] == {"confirmed": 1, "rejected": 1}
    assert item["outcome_counts"] == {"completed": 0, "skipped": 0, "failed": 1}
    assert item["source"]["recommendation_id"] == "recommendation-a"
    assert item["source"]["observed_outcomes"] == 1
    assert item["source"]["unknown_outcomes"] == 1


def test_learning_input_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-b")
    create_outcome(client, person["id"], decision["id"], "completed")
    first = get_learning_input(client, person["id"]).json()
    second = get_learning_input(client, person["id"]).json()
    assert first == second


def test_learning_input_is_person_isolated(client):
    first = create_person(client, "第一个学习对象")
    second = create_person(client, "第二个学习对象")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"], "completed")
    body = get_learning_input(client, second["id"]).json()
    assert body["items"] == []


def test_learning_input_exposes_non_inference_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    constraints = get_learning_input(client, person["id"]).json()["learning_constraints"]
    assert constraints["must_be_source_backed"] is True
    assert constraints["must_preserve_unknowns"] is True
    assert constraints["must_not_infer_recommendation_quality"] is True
    assert constraints["must_not_infer_success"] is True
    assert constraints["must_not_infer_relationship_impact"] is True


def test_learning_input_is_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a")
    before = get_learning_input(client, person["id"]).json()
    after = get_learning_input(client, person["id"]).json()
    assert before == after
    assert before["learning_constraints"]["must_not_auto_execute"] is True
    assert before["learning_constraints"]["must_not_call_llm"] is True
