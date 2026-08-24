from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name):
    response = client.post("/api/v1/persons", json={"name": name})
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
            "recommendation-feedback-trend",
            decision,
            "用户决策",
        )


def create_outcome(client, person_id, decision_id, outcome):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "结果已记录"},
    )
    assert response.status_code == 201


def get_trend(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/feedback/trend")


def test_feedback_trend_preserves_unknown_without_outcome(client):
    person = create_person(client, "趋势对象")
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    response = get_trend(client, person["id"])
    assert response.status_code == 200
    item = response.json()["observations"][0]
    assert item["decision_id"] == decision["id"]
    assert item["feedback_status"] == "outcome_unknown"
    assert item["outcome"] == "unknown"
    assert item["outcome_id"] is None
    assert item["event_at"] == item["decision_created_at"]


def test_feedback_trend_uses_observed_outcome_timestamp(client):
    person = create_person(client, "观察对象")
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "completed")
    item = get_trend(client, person["id"]).json()["observations"][0]
    assert item["feedback_status"] == "outcome_observed"
    assert item["outcome"] == "completed"
    assert item["outcome_id"]
    assert item["event_at"] == item["outcome_created_at"]
    assert item["source"]["decision_id"] == decision["id"]


def test_feedback_trend_contains_observed_and_unknown_records(client):
    person = create_person(client, "混合趋势对象")
    create_relationship(client, person["id"])
    observed = seed_decision(person["id"])
    unknown = seed_decision(person["id"])
    create_outcome(client, person["id"], observed["id"], "failed")
    observations = get_trend(client, person["id"]).json()["observations"]
    by_decision = {item["decision_id"]: item for item in observations}
    assert by_decision[observed["id"]]["feedback_status"] == "outcome_observed"
    assert by_decision[observed["id"]]["outcome"] == "failed"
    assert by_decision[unknown["id"]]["feedback_status"] == "outcome_unknown"
    assert by_decision[unknown["id"]]["outcome"] == "unknown"


def test_feedback_trend_is_deterministically_ordered(client):
    person = create_person(client, "排序趋势对象")
    create_relationship(client, person["id"])
    first = seed_decision(person["id"])
    second = seed_decision(person["id"])
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "skipped")
    first_response = get_trend(client, person["id"]).json()
    second_response = get_trend(client, person["id"]).json()
    assert first_response == second_response
    assert first_response["observations"][0]["event_at"] >= first_response["observations"][1]["event_at"]


def test_feedback_trend_preserves_source_identity(client):
    person = create_person(client, "来源趋势对象")
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"], "skipped")
    item = get_trend(client, person["id"]).json()["observations"][0]
    assert item["source"] == {
        "decision_id": decision["id"],
        "outcome_id": item["outcome_id"],
    }
    assert item["decision_created_at"]
    assert item["outcome_created_at"]


def test_feedback_trend_is_person_isolated(client):
    first = create_person(client, "趋势对象一")
    second = create_person(client, "趋势对象二")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"], "completed")
    assert get_trend(client, second["id"]).json()["observations"] == []


def test_feedback_trend_does_not_change_relationship(client):
    person = create_person(client, "关系边界对象")
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    body = get_trend(client, person["id"]).json()
    assert body["feedback_trend_constraints"]["must_not_change_relationship"] is True
    assert body["feedback_trend_constraints"]["must_not_auto_execute"] is True
    assert body["feedback_trend_constraints"]["must_preserve_unknowns"] is True
