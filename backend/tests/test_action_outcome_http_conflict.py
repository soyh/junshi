import sqlite3


def create_person(client):
    response = client.post("/api/v1/persons", json={"name": "结果冲突测试对象"})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def test_duplicate_outcome_integrity_error_is_http_409(client, monkeypatch):
    person = create_person(client)
    create_relationship(client, person["id"])

    from app.api.routes import action_outcome

    def raise_integrity_error(*args, **kwargs):
        raise sqlite3.IntegrityError(
            "UNIQUE constraint failed: action_outcomes.decision_id"
        )

    monkeypatch.setattr(action_outcome.service, "create_outcome", raise_integrity_error)

    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/00000000-0000-0000-0000-000000000001",
        json={"outcome": "completed"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "action decision already has an outcome"
