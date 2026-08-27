from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="Bridge Person"):
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
            conn, USER_ID, person_id, recommendation_id, decision, "bridge test"
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
        json={"outcome": "completed", "note": "bridge test"},
    )
    assert response.status_code == 201


def test_learning_strategy_context_includes_strategy_decision_learning(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")

    response = client.get(f"/api/v1/persons/{person['id']}/learning-strategy/context")
    assert response.status_code == 200
    body = response.json()

    bridge = body["learning_inputs"]["strategy_decision"]
    assert bridge["items"]
    assert bridge["items"][0]["decision_id"] == decision["id"]
    assert bridge["items"][0]["learning_eligible"] is False
    assert bridge["items"][0]["learning_status"] == "outcome_unknown"
    assert bridge["learning_constraints"]["source_backed"] is True


def test_learning_strategy_synthesis_includes_strategy_decision_observed_counts(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    pending = seed_decision(person["id"], "recommendation-a")
    completed = seed_decision(person["id"], "recommendation-a")
    execute(client, person["id"], completed["id"])
    outcome(client, person["id"], completed["id"])

    response = client.get(f"/api/v1/persons/{person['id']}/learning-strategy/synthesis")
    assert response.status_code == 200
    body = response.json()

    bridge = body["strategy_decision_learning"]
    assert bridge["learning_candidate_count"] == 1
    assert bridge["unknown_count"] == 1
    assert bridge["learning_candidate_decision_ids"] == [completed["id"]]
    assert bridge["unknown_decision_ids"] == [pending["id"]]
    assert bridge["recommendation_observed_counts"] == {"recommendation-a": 1}
    assert bridge["constraints"]["read_only"] is True


def test_learning_strategy_synthesis_preserves_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    rejected = seed_decision(person["id"], "recommendation-rejected", "rejected")

    response = client.get(f"/api/v1/persons/{person['id']}/learning-strategy/synthesis")
    assert response.status_code == 200
    bridge = response.json()["strategy_decision_learning"]

    assert bridge["learning_candidate_count"] == 0
    assert bridge["unknown_count"] == 1
    assert bridge["unknown_decision_ids"] == [rejected["id"]]
    assert bridge["constraints"]["must_not_infer_success"] is True
    assert bridge["constraints"]["must_not_infer_relationship_impact"] is True
