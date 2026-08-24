from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略确认对象"):
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
            conn, USER_ID, person_id, recommendation_id, "confirmed", "确认测试"
        )


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "确认测试结果"},
    )
    assert response.status_code == 201


def test_confirmation_context_requires_explicit_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/confirmation-context")
    assert response.status_code == 200
    body = response.json()
    assert body["decisions"] == []
    assert body["confirmation_constraints"]["must_not_auto_confirm"] is True
    assert body["confirmation_constraints"]["must_not_auto_execute"] is True


def test_confirmation_rejects_unknown_recommendation(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmations",
        json={"recommendation_id": "missing", "decision": "confirmed"},
    )
    assert response.status_code == 409


def test_confirmation_requires_recommendation_for_confirmed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmations",
        json={"decision": "confirmed"},
    )
    assert response.status_code == 409


def test_confirmation_persists_explicit_confirmed_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmations",
        json={"recommendation_id": "recommendation-a", "decision": "confirmed", "note": "确认"},
    )
    assert response.status_code == 201
    assert response.json()["recommendation_id"] == "recommendation-a"
    assert response.json()["decision"] == "confirmed"


def test_confirmation_persists_explicit_rejected_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmations",
        json={"recommendation_id": "recommendation-a", "decision": "rejected", "note": "拒绝"},
    )
    assert response.status_code == 201
    assert response.json()["decision"] == "rejected"


def test_confirmation_is_person_isolated(client):
    first = create_person(client, "确认A")
    second = create_person(client, "确认B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{second['id']}/strategy-decision/confirmation-context")
    assert response.status_code == 200
    assert response.json()["decisions"] == []


def test_confirmation_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmation-context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
