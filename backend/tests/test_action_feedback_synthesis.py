from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client):
    response = client.post("/api/v1/persons", json={"name": "行动反馈对象"})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, decision="confirmed"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            "recommendation-feedback-synthesis",
            decision,
            "用户决策",
        )


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/feedback/context")


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "结果已记录"},
    )
    assert response.status_code == 201


def test_feedback_synthesis_marks_missing_outcome_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    item = get_context(client, person["id"]).json()["feedback_synthesis"][0]
    assert item["decision_id"] == decision["id"]
    assert item["feedback_status"] == "outcome_unknown"
    assert item["outcome_signal"] == "unknown"
    assert item["outcome_id"] is None


def test_feedback_synthesis_uses_observed_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    item = get_context(client, person["id"]).json()["feedback_synthesis"][0]
    assert item["feedback_status"] == "outcome_observed"
    assert item["outcome_signal"] == "completed"
    assert item["outcome_id"]


def test_feedback_synthesis_preserves_unknown_relationship_impact(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    item = get_context(client, person["id"]).json()["feedback_synthesis"][0]
    assert "relationship_impact" in item["unknowns"]
    assert "action_effect" in item["unknowns"]


def test_feedback_synthesis_is_deterministic_and_source_backed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = get_context(client, person["id"]).json()
    second = get_context(client, person["id"]).json()
    assert first["feedback_synthesis"] == second["feedback_synthesis"]
    assert first["feedback_synthesis"][0]["source"]["decision_id"] == decision["id"]


def test_feedback_synthesis_keeps_execution_separate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    body = get_context(client, person["id"]).json()
    assert body["feedback_constraints"]["must_not_auto_execute"] is True
    assert body["feedback_constraints"]["must_not_change_relationship"] is True
