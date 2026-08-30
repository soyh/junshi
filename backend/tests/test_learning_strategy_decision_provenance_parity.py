from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="决策来源对象"):
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
            USER_ID,
            person_id,
            recommendation_id,
            decision,
            "决策来源一致性测试",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    execution = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={"note": "测试执行"},
    )
    assert execution.status_code == 201

    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "决策来源一致性测试结果"},
    )
    assert response.status_code == 201


def test_learning_strategy_preserves_strategy_decision_provenance_across_layers(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    observed = seed_decision(person["id"], "recommendation-observed")
    unknown = seed_decision(person["id"], "recommendation-unknown", "rejected")
    create_outcome(client, person["id"], observed["id"])

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    )
    action_plan = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/context"
    )
    strategic_reply = client.get(
        f"/api/v1/persons/{person['id']}/strategic-reply/context"
    )

    assert synthesis.status_code == 200
    assert action_plan.status_code == 200
    assert strategic_reply.status_code == 200

    expected = synthesis.json()["strategy_decision_learning"]
    assert action_plan.json()["learning_strategy"]["strategy_decision_learning"] == expected
    assert strategic_reply.json()["learning_strategy"]["strategy_decision_learning"] == expected
    assert expected["learning_candidate_decision_ids"] == [observed["id"]]
    assert expected["unknown_decision_ids"] == [unknown["id"]]
    assert expected["learning_candidate_count"] == 1
    assert expected["unknown_count"] == 1


def test_learning_strategy_decision_provenance_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])

    first = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    )
    second = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["strategy_decision_learning"] == first.json()["strategy_decision_learning"]
    assert first.json()["strategy_constraints"]["must_not_turn_learning_into_fact"] is True
    assert first.json()["strategy_constraints"]["must_not_rank_recommendations"] is True


def test_learning_strategy_decision_provenance_is_person_and_user_isolated(client):
    first = create_person(client, "决策来源A")
    second = create_person(client, "决策来源B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])

    second_synthesis = client.get(
        f"/api/v1/persons/{second['id']}/learning-strategy/synthesis"
    )
    assert second_synthesis.status_code == 200
    isolated = second_synthesis.json()["strategy_decision_learning"]
    assert isolated["learning_candidate_decision_ids"] == []
    assert isolated["unknown_decision_ids"] == []
    assert isolated["learning_candidate_count"] == 0
    assert isolated["unknown_count"] == 0

    foreign_user = client.get(
        f"/api/v1/persons/{first['id']}/learning-strategy/synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert foreign_user.status_code == 404
