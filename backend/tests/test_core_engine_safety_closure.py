from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="安全闭环对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201
    return response.json()


def test_core_engine_requires_explicit_confirmation_execution_and_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    execution_context = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/execution-context"
    )
    assert execution_context.status_code == 200
    assert execution_context.json()["decisions"] == []
    assert execution_context.json()["execution_constraints"] == {
        "must_require_confirmed_decision": True,
        "must_require_explicit_execution": True,
        "must_not_execute_rejected_decision": True,
        "must_not_execute_from_confirmation_automatically": True,
        "must_not_send": True,
        "must_not_create_outcome_automatically": True,
    }

    rejected = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"decision": "rejected", "note": "不执行"},
    )
    assert rejected.status_code == 201
    rejected_id = rejected.json()["id"]

    rejected_execution = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/{rejected_id}",
        json={"note": "不应执行"},
    )
    assert rejected_execution.status_code == 409
    assert rejected_execution.json()["detail"] == "execution requires a confirmed action decision"

    with get_connection() as conn:
        confirmed = ActionDecisionRepository.create(
            conn,
            USER_ID,
            person["id"],
            "recommendation-safety",
            "confirmed",
            "用户显式确认",
        )

    confirmed_id = confirmed["id"]
    premature_outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{confirmed_id}",
        json={"outcome": "completed", "note": "不应在执行前记录"},
    )
    assert premature_outcome.status_code == 409
    assert premature_outcome.json()["detail"] == "outcome requires an executed action decision"


def test_core_engine_prevents_duplicate_execution_and_duplicate_outcome(client):
    person = create_person(client, "重复执行对象")
    create_relationship(client, person["id"])

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            USER_ID,
            person["id"],
            "recommendation-duplicate-safety",
            "confirmed",
            "用户显式确认",
        )

    decision_id = decision["id"]
    first_execution = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/{decision_id}",
        json={"note": "首次执行"},
    )
    assert first_execution.status_code == 201

    duplicate_execution = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/{decision_id}",
        json={"note": "重复执行"},
    )
    assert duplicate_execution.status_code == 409
    assert duplicate_execution.json()["detail"] == "action decision has already been executed"

    first_outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "首次结果"},
    )
    assert first_outcome.status_code == 201

    duplicate_outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "重复结果"},
    )
    assert duplicate_outcome.status_code == 409
    assert duplicate_outcome.json()["detail"] == "action decision already has an outcome"


def test_core_engine_execution_and_outcome_are_user_person_isolated(client):
    first = create_person(client, "隔离对象A")
    second = create_person(client, "隔离对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            USER_ID,
            first["id"],
            "recommendation-isolation",
            "confirmed",
            "用户显式确认",
        )

    decision_id = decision["id"]
    wrong_person_execution = client.post(
        f"/api/v1/persons/{second['id']}/action-plan/executions/{decision_id}",
        json={"note": "不应跨对象执行"},
    )
    assert wrong_person_execution.status_code == 404

    correct_execution = client.post(
        f"/api/v1/persons/{first['id']}/action-plan/executions/{decision_id}",
        json={"note": "正确对象执行"},
    )
    assert correct_execution.status_code == 201

    wrong_person_outcome = client.post(
        f"/api/v1/persons/{second['id']}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "不应跨对象记录"},
    )
    assert wrong_person_outcome.status_code == 404
