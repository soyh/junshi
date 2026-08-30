from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略决策综合对象"):
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
            conn, USER_ID, person_id, recommendation_id, "confirmed", "策略决策综合测试"
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    execution = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={"note": "测试执行"},
    )
    assert execution.status_code == 201

    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "策略决策综合测试结果"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/strategy-decision/synthesis")


def test_strategy_decision_synthesis_is_empty_without_candidates(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = get_synthesis(client, person["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["decisions"] == []
    assert body["selection"]["selected_recommendation_id"] is None


def test_strategy_decision_synthesis_marks_observed_candidate_decisionable(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"], "completed")
    body = get_synthesis(client, person["id"]).json()
    item = body["decisions"][0]
    assert item["recommendation_id"] == "recommendation-a"
    assert item["decision_status"] == "decisionable"
    assert "observed_outcome_available" in item["decision_reasons"]


def test_strategy_decision_synthesis_does_not_auto_select(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-b")
    second = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "completed")
    body = get_synthesis(client, person["id"]).json()
    assert body["selection"] == {
        "selected_recommendation_id": None,
        "selection_status": "requires_explicit_decision",
        "selection_is_automatic": False,
    }


def test_strategy_decision_synthesis_does_not_rank(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"], "completed")
    body = get_synthesis(client, person["id"]).json()
    assert "rank" not in body["decisions"][0]
    assert body["strategy_constraints"]["must_not_rank_recommendations"] is True


def test_strategy_decision_synthesis_preserves_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    item = get_synthesis(client, person["id"]).json()["decisions"][0]
    assert item["unknown_outcome_count"] == 0
    assert "recommendation_quality" in item["unknowns"]
    assert "relationship_impact" in item["unknowns"]


def test_strategy_decision_synthesis_is_person_isolated(client):
    first = create_person(client, "策略综合A")
    second = create_person(client, "策略综合B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])
    assert get_synthesis(client, second["id"]).json()["decisions"] == []


def test_strategy_decision_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_strategy_decision_synthesis_is_deterministic_and_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    first = get_synthesis(client, person["id"]).json()
    second = get_synthesis(client, person["id"]).json()
    assert first == second
    assert first["strategy_constraints"]["must_not_auto_execute"] is True
    assert first["strategy_constraints"]["must_not_auto_send"] is True
    assert first["strategy_constraints"]["must_not_turn_decision_status_into_fact"] is True
