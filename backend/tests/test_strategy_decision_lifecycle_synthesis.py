from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="生命周期综合对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, decision="confirmed", recommendation_id="recommendation-a"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn, USER_ID, person_id, recommendation_id, decision, "生命周期综合测试"
        )


def execute(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={},
    )
    assert response.status_code == 201


def outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "生命周期结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    response = client.get(f"/api/v1/persons/{person_id}/strategy-decision/lifecycle-synthesis")
    assert response.status_code == 200
    return response.json()


def test_lifecycle_synthesis_counts_result_and_feedback_states(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    pending = seed_decision(person["id"], "confirmed", "recommendation-a")
    executed = seed_decision(person["id"], "confirmed", "recommendation-b")
    completed = seed_decision(person["id"], "confirmed", "recommendation-c")
    rejected = seed_decision(person["id"], "rejected", "recommendation-d")
    execute(client, person["id"], executed["id"])
    execute(client, person["id"], completed["id"])
    outcome(client, person["id"], completed["id"])

    body = get_synthesis(client, person["id"])
    summary = body["lifecycle_summary"]
    assert summary["total_decision_count"] == 4
    assert summary["confirmed_pending_execution_count"] == 1
    assert summary["executed_pending_outcome_count"] == 1
    assert summary["outcome_recorded_count"] == 1
    assert summary["not_actionable_count"] == 1
    assert summary["outcome_observed_count"] == 1
    assert summary["outcome_unknown_count"] == 3
    assert body["actionable_decision_ids"] == [pending["id"], executed["id"]]
    assert body["feedback_learning_decision_ids"] == [completed["id"]]
    assert body["feedback_unknown_decision_ids"] == [pending["id"], executed["id"], rejected["id"]]


def test_lifecycle_synthesis_preserves_unknowns_and_source_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    body = get_synthesis(client, person["id"])
    item = body["lifecycle"][0]
    assert item["decision_id"] == decision["id"]
    assert item["feedback_status"] == "outcome_unknown"
    assert item["source"]["decision_id"] == decision["id"]
    assert item["source"]["outcome_id"] is None


def test_lifecycle_synthesis_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "confirmed", "recommendation-a")
    first = get_synthesis(client, person["id"])
    second = get_synthesis(client, person["id"])
    assert first == second


def test_lifecycle_synthesis_is_person_isolated(client):
    first = create_person(client, "综合生命周期A")
    second = create_person(client, "综合生命周期B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    seed_decision(first["id"])
    body = get_synthesis(client, second["id"])
    assert body["lifecycle"] == []
    assert body["actionable_decision_ids"] == []
    assert body["feedback_learning_decision_ids"] == []
    assert body["feedback_unknown_decision_ids"] == []


def test_lifecycle_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/lifecycle-synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_lifecycle_synthesis_is_read_only_and_does_not_infer_quality(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_synthesis(client, person["id"])
    assert body["synthesis_constraints"] == {
        "deterministic": True,
        "read_only": True,
        "must_preserve_unknowns": True,
        "must_not_infer_recommendation_quality": True,
        "must_not_infer_relationship_impact": True,
        "must_not_auto_execute": True,
        "must_not_auto_send": True,
        "must_not_call_llm": True,
    }
