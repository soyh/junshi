from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略决策学习对象"):
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
            "策略决策学习测试",
        )


def get_learning_input(client, person_id):
    response = client.get(
        f"/api/v1/persons/{person_id}/strategy-decision/learning-input"
    )
    assert response.status_code == 200
    return response.json()


def test_strategy_decision_learning_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a")

    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/learning-input",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_strategy_decision_learning_exposes_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    constraints = get_learning_input(client, person["id"])["learning_constraints"]

    assert constraints == {
        "source_backed": True,
        "read_only": True,
        "must_preserve_source_provenance": True,
        "must_preserve_unknowns": True,
        "must_not_infer_recommendation_quality": True,
        "must_not_infer_success": True,
        "must_not_infer_relationship_impact": True,
        "must_not_change_relationship": True,
        "must_not_auto_execute": True,
        "must_not_auto_send": True,
        "must_not_call_llm": True,
    }
