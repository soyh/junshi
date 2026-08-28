from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="决策约束对象"):
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
            conn,
            USER_ID,
            person_id,
            recommendation_id,
            "confirmed",
            "决策约束一致性测试",
        )


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "决策约束一致性测试结果"},
    )
    assert response.status_code == 201


def test_learning_strategy_decision_constraint_is_consistent_across_layers(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])

    synthesis = client.get(f"/api/v1/persons/{person['id']}/learning-strategy/synthesis")
    action_plan = client.get(f"/api/v1/persons/{person['id']}/action-plan/context")
    strategic_reply = client.get(f"/api/v1/persons/{person['id']}/strategic-reply/context")

    assert synthesis.status_code == 200
    assert action_plan.status_code == 200
    assert strategic_reply.status_code == 200

    assert synthesis.json()["strategy_constraints"]["must_preserve_source_provenance"] is True
    assert action_plan.json()["learning_strategy"]["constraints"]["must_preserve_source_provenance"] is True
    assert strategic_reply.json()["learning_strategy"]["constraints"]["must_preserve_source_provenance"] is True


def test_strategy_decision_learning_constraint_declares_source_provenance_and_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a")

    response = client.get(f"/api/v1/persons/{person['id']}/learning-strategy")
    assert response.status_code == 200

    constraints = response.json()["learning_inputs"]["strategy_decision"]["learning_constraints"]
    assert constraints["source_backed"] is True
    assert constraints["read_only"] is True
    assert constraints["must_preserve_source_provenance"] is True
    assert constraints["must_preserve_unknowns"] is True


def test_learning_strategy_decision_constraint_is_read_only_and_isolated(client):
    first = create_person(client, "决策约束A")
    second = create_person(client, "决策约束B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])

    first_response = client.get(f"/api/v1/persons/{first['id']}/learning-strategy/synthesis")
    second_response = client.get(f"/api/v1/persons/{second['id']}/learning-strategy/synthesis")
    foreign_user = client.get(
        f"/api/v1/persons/{first['id']}/learning-strategy/synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert foreign_user.status_code == 404
    assert first_response.json()["strategy_decision_learning"]["constraints"]["read_only"] is True
    assert first_response.json()["strategy_decision_learning"]["constraints"]["source_backed_only"] is True
    assert first_response.json()["strategy_decision_learning"]["constraints"]["must_preserve_source_provenance"] is True
    assert second_response.json()["strategy_decision_learning"]["learning_candidate_decision_ids"] == []
    assert second_response.json()["strategy_decision_learning"]["unknown_decision_ids"] == []
