from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="反馈学习对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id="recommendation-a", decision="confirmed"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            recommendation_id,
            decision,
            "用户决策",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "结果已记录"},
    )
    assert response.status_code == 201


def get_learning_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/feedback/learning-context")


def test_learning_context_combines_summary_trend_and_signals(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    body = get_learning_context(client, person["id"]).json()
    assert body["summary"]["total_decisions"] == 1
    assert len(body["trend"]) == 1
    assert len(body["signals"]) == 1
    assert body["signals"][0]["recommendation_id"] == "recommendation-a"


def test_learning_context_preserves_unknowns_across_views(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    body = get_learning_context(client, person["id"]).json()
    assert body["summary"]["outcome_unknown_count"] == 1
    assert body["trend"][0]["feedback_status"] == "outcome_unknown"
    assert body["trend"][0]["outcome"] == "unknown"
    assert body["signals"][0]["outcome_unknown_count"] == 1


def test_learning_context_views_are_consistent(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "failed")
    body = get_learning_context(client, person["id"]).json()
    assert body["summary"]["outcome_counts"] == {"completed": 0, "skipped": 0, "failed": 1}
    assert body["trend"][0]["outcome"] == "failed"
    assert body["signals"][0]["outcome_counts"] == {"completed": 0, "skipped": 0, "failed": 1}


def test_learning_context_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-b", "confirmed")
    second = seed_decision(person["id"], "recommendation-a", "rejected")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "skipped")
    first_body = get_learning_context(client, person["id"]).json()
    second_body = get_learning_context(client, person["id"]).json()
    assert first_body == second_body
    assert [item["recommendation_id"] for item in first_body["signals"]] == [
        "recommendation-a",
        "recommendation-b",
    ]


def test_learning_context_is_person_isolated(client):
    first = create_person(client, "第一个对象")
    second = create_person(client, "第二个对象")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])
    body = get_learning_context(client, second["id"]).json()
    assert body["summary"]["total_decisions"] == 0
    assert body["trend"] == []
    assert body["signals"] == []


def test_learning_context_exposes_non_inference_boundaries(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_learning_context(client, person["id"]).json()
    constraints = body["feedback_learning_constraints"]
    assert constraints["must_be_source_backed"] is True
    assert constraints["must_preserve_unknowns"] is True
    assert constraints["must_keep_summary_trend_signal_views_consistent"] is True
    assert constraints["must_not_infer_recommendation_quality"] is True
    assert constraints["must_not_infer_success"] is True
    assert constraints["must_not_infer_relationship_impact"] is True


def test_learning_context_is_read_only_and_execution_separate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    before = get_learning_context(client, person["id"]).json()
    after = get_learning_context(client, person["id"]).json()
    assert before == after
    assert before["feedback_learning_constraints"]["must_not_change_relationship"] is True
    assert before["feedback_learning_constraints"]["must_not_auto_execute"] is True
    assert before["feedback_learning_constraints"]["must_not_call_llm"] is True
