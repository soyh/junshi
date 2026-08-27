from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="生命周期对象"):
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
            conn, USER_ID, person_id, recommendation_id, decision, "生命周期测试"
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


def get_context(client, person_id):
    response = client.get(f"/api/v1/persons/{person_id}/strategy-decision/lifecycle-context")
    assert response.status_code == 200
    return response.json()


def test_lifecycle_context_links_decision_execution_outcome_and_feedback(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    pending = seed_decision(person["id"], "confirmed", "recommendation-pending")
    completed = seed_decision(person["id"], "confirmed", "recommendation-completed")
    execute(client, person["id"], completed["id"])
    outcome(client, person["id"], completed["id"])

    body = get_context(client, person["id"])
    by_id = {item["decision_id"]: item for item in body["lifecycle"]}

    assert by_id[pending["id"]]["result_status"] == "confirmed_pending_execution"
    assert by_id[pending["id"]]["feedback_status"] == "outcome_unknown"
    assert by_id[pending["id"]]["execution_present"] is False
    assert by_id[pending["id"]]["outcome_present"] is False

    assert by_id[completed["id"]]["result_status"] == "outcome_recorded"
    assert by_id[completed["id"]]["feedback_status"] == "outcome_observed"
    assert by_id[completed["id"]]["execution_present"] is True
    assert by_id[completed["id"]]["outcome_present"] is True
    assert by_id[completed["id"]]["source"]["decision_id"] == completed["id"]


def test_lifecycle_context_preserves_unknown_feedback(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    body = get_context(client, person["id"])
    item = body["lifecycle"][0]
    assert item["decision_id"] == decision["id"]
    assert item["feedback_status"] == "outcome_unknown"
    assert item["feedback"]["outcome_signal"] == "unknown"
    assert item["feedback"]["unknowns"] == ["action_effect", "relationship_impact"]


def test_lifecycle_context_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "confirmed", "recommendation-a")
    first = get_context(client, person["id"])
    second = get_context(client, person["id"])
    assert first == second


def test_lifecycle_context_is_person_isolated(client):
    first = create_person(client, "生命周期A")
    second = create_person(client, "生命周期B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    seed_decision(first["id"])
    body = get_context(client, second["id"])
    assert body["lifecycle"] == []


def test_lifecycle_context_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/lifecycle-context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_lifecycle_context_exposes_read_only_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_context(client, person["id"])
    assert body["lifecycle_constraints"] == {
        "read_only": True,
        "execution_is_distinct_from_outcome": True,
        "outcome_is_not_automatic_execution": True,
        "feedback_must_be_source_backed": True,
        "feedback_unknowns_must_be_preserved": True,
        "relationship_impact_must_not_be_inferred": True,
        "must_not_auto_execute": True,
        "must_not_auto_send": True,
        "must_not_call_llm": True,
    }
