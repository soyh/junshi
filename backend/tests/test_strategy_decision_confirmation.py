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


def test_confirmation_context_is_read_only_and_requires_explicit_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/strategy-decision/confirmation-context")
    assert response.status_code == 200
    body = response.json()
    assert body["decisions"] == []
    assert body["confirmation_constraints"]["must_record_user_decision"] is True
    assert body["confirmation_constraints"]["must_not_auto_confirm"] is True
    assert body["confirmation_constraints"]["must_not_auto_execute"] is True
    assert body["confirmation_constraints"]["must_not_auto_send"] is True


def test_confirmation_write_endpoint_is_removed(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmations",
        json={"recommendation_id": "recommendation-a", "decision": "confirmed"},
    )
    assert response.status_code == 404 or response.status_code == 405


def test_confirmation_write_cannot_create_action_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    with __import__("app.core.database", fromlist=["get_connection"]).get_connection() as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM action_decisions WHERE user_id = ? AND person_id = ?",
            (USER_ID, person["id"]),
        ).fetchone()[0]

    response = client.post(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmations",
        json={"recommendation_id": "recommendation-a", "decision": "confirmed"},
    )
    assert response.status_code == 404 or response.status_code == 405

    with __import__("app.core.database", fromlist=["get_connection"]).get_connection() as conn:
        after = conn.execute(
            "SELECT COUNT(*) FROM action_decisions WHERE user_id = ? AND person_id = ?",
            (USER_ID, person["id"]),
        ).fetchone()[0]
    assert after == before


def test_confirmation_is_person_isolated(client):
    first = create_person(client, "确认A")
    second = create_person(client, "确认B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
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
