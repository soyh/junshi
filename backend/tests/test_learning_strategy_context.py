from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="学习策略对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id="recommendation-a"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            USER_ID,
            person_id,
            recommendation_id,
            "confirmed",
            "学习策略测试决策",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "学习策略测试结果"},
    )
    assert response.status_code == 201
    return response.json()


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/learning-strategy/context")


def test_learning_strategy_context_is_empty_without_learning_events(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_context(client, person["id"]).json()
    assert body["learning_inputs"]["action_feedback"] == []
    assert body["learning_inputs"]["memory_updates"] == []


def test_learning_strategy_context_preserves_observed_learning(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-observed")
    create_outcome(client, person["id"], decision["id"], "completed")
    body = get_context(client, person["id"]).json()
    assert body["learning_inputs"]["action_feedback"][0]["recommendation_id"] == "recommendation-observed"
    assert body["learning_inputs"]["action_feedback"][0]["observed_outcome_count"] == 1
    assert body["learning_inputs"]["memory_updates"][0]["learning_provenance"]["recommendation_id"] == "recommendation-observed"


def test_learning_strategy_context_preserves_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    body = get_context(client, person["id"]).json()
    constraints = body["strategy_constraints"]
    assert constraints["must_preserve_facts_inferences_unknowns"] is True
    assert constraints["must_preserve_learning_unknowns"] is True
    assert constraints["must_not_infer_success"] is True
    assert constraints["must_not_infer_relationship_impact"] is True


def test_learning_strategy_context_does_not_create_recommendations(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_context(client, person["id"]).json()
    assert body["recommendations"] == []


def test_learning_strategy_context_is_person_isolated(client):
    first = create_person(client, "学习策略A")
    second = create_person(client, "学习策略B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"])
    create_outcome(client, first["id"], decision["id"])

    learning_inputs = get_context(client, second["id"]).json()["learning_inputs"]
    assert learning_inputs["action_feedback"] == []
    assert learning_inputs["memory_updates"] == []
    assert learning_inputs["strategy_decision"]["items"] == []
    assert learning_inputs["strategy_decision"]["learning_constraints"]["source_backed"] is True


def test_learning_strategy_context_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_learning_strategy_context_is_deterministic_and_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = get_context(client, person["id"]).json()
    second = get_context(client, person["id"]).json()
    assert first == second
    assert first["strategy_constraints"]["must_not_auto_execute"] is True
    assert first["strategy_constraints"]["must_not_auto_send"] is True
