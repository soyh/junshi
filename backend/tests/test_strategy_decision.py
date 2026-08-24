from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略决策对象"):
    response = client.post("/api/v1/persons", json={"name": name})
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
            conn, USER_ID, person_id, recommendation_id, "confirmed", "策略决策测试"
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "策略决策测试结果"},
    )
    assert response.status_code == 201


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/strategy-decision/context")


def test_strategy_decision_context_is_empty_without_candidates(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = get_context(client, person["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["candidates"] == []
    assert body["decision_inputs"]["candidate_count"] == 0
    assert body["decision_inputs"]["selection_status"] == "requires_explicit_decision"


def test_strategy_decision_context_preserves_candidate_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"], "completed")
    body = get_context(client, person["id"]).json()
    assert body["decision_inputs"]["candidate_ids"] == ["recommendation-a"]
    assert body["candidates"][0]["recommendation_id"] == "recommendation-a"
    assert body["decision_inputs"]["observed_outcome_counts"] == {"recommendation-a": 1}


def test_strategy_decision_context_does_not_rank_candidates(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-b")
    second = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "completed")
    body = get_context(client, person["id"]).json()
    assert "ranking" not in body["decision_inputs"]
    assert body["strategy_constraints"]["must_not_rank_recommendations"] is True
    assert body["strategy_constraints"]["must_not_auto_select"] is True


def test_strategy_decision_context_preserves_unknown_outcomes(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-unknown")
    create_outcome(client, person["id"], decision["id"])
    body = get_context(client, person["id"]).json()
    assert body["decision_inputs"]["unknown_outcome_counts"] == {"recommendation-unknown": 0}
    assert body["candidates"][0]["unknowns"]


def test_strategy_decision_context_is_person_isolated(client):
    first = create_person(client, "策略决策A")
    second = create_person(client, "策略决策B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])
    assert get_context(client, second["id"]).json()["candidates"] == []


def test_strategy_decision_context_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_strategy_decision_context_is_deterministic_and_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    first = get_context(client, person["id"]).json()
    second = get_context(client, person["id"]).json()
    assert first == second
    assert first["strategy_constraints"]["must_not_auto_execute"] is True
    assert first["strategy_constraints"]["must_not_auto_send"] is True
