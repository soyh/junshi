from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="Action Plan 执行桥测试对象"):
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
            USER_ID,
            person_id,
            "recommendation-a",
            decision,
            "用户显式决策",
        )


def execute(client, person_id, decision_id, note="已执行"):
    return client.post(
        f"/api/v1/persons/{person_id}/action-plan/executions/{decision_id}",
        json={"note": note},
    )


def test_action_plan_execution_context_reuses_existing_execution_lifecycle(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/execution-context")

    assert response.status_code == 200
    body = response.json()
    assert body["decisions"] == []
    assert body["execution_constraints"]["must_require_confirmed_decision"] is True
    assert body["execution_constraints"]["must_require_explicit_execution"] is True
    assert body["execution_constraints"]["must_not_execute_from_confirmation_automatically"] is True
    assert body["execution_constraints"]["must_not_create_outcome_automatically"] is True


def test_action_plan_execution_requires_confirmed_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "rejected")

    response = execute(client, person["id"], decision["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "execution requires a confirmed action decision"


def test_action_plan_execution_persists_only_after_explicit_confirmation(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])

    response = execute(client, person["id"], decision["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["decision_id"] == decision["id"]
    assert body["person_id"] == person["id"]


def test_action_plan_execution_closes_into_existing_outcome_and_feedback_chain(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])

    assert execute(client, person["id"], decision["id"]).status_code == 201

    outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        json={"outcome": "completed", "note": "结果已记录"},
    )
    assert outcome.status_code == 201

    feedback = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback")
    assert feedback.status_code == 200
    assert feedback.json()["feedback"][0]["outcome_id"] == outcome.json()["id"]

    learning = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/learning-synthesis"
    )
    assert learning.status_code == 200
    candidate = learning.json()["candidates"][0]
    assert candidate["recommendation_id"] == "recommendation-a"
    assert candidate["observed_outcome_count"] == 1
    assert candidate["outcome_counts"]["completed"] == 1
    assert candidate["unknown_outcome_count"] == 0


def test_action_plan_execution_cannot_repeat_same_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"])

    assert execute(client, person["id"], decision["id"]).status_code == 201
    response = execute(client, person["id"], decision["id"], note="重复执行")

    assert response.status_code == 409
