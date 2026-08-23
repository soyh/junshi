def create_person(client, name="测试对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_person_profile_returns_person_and_empty_aggregates(client):
    person = create_person(client)
    response = client.get(f"/api/v1/persons/{person['id']}/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["person"]["id"] == person["id"]
    assert body["relationships"] == []
    assert body["statistics"] == {"relationship_count": 0, "conversation_count": 0, "interaction_count": 0, "message_count": 0}
    assert body["latest_interaction"] is None


def test_person_profile_aggregates_existing_person_data(client):
    person = create_person(client)
    person_id = person["id"]
    relationship = client.post("/api/v1/relationships", json={"person_id": person_id, "status": "active", "stage": "dating", "long_term_goal": "建立长期关系", "current_goal": "增加互动", "notes": "profile test"})
    assert relationship.status_code == 201
    conversation = client.post("/api/v1/conversations", json={"person_id": person_id, "title": "测试会话", "status": "active"})
    assert conversation.status_code == 201
    message = client.post("/api/v1/messages", json={"conversation_id": conversation.json()["id"], "sender_type": "person", "content": "今天有空吗？", "sent_at": "2026-08-23T10:00:00+00:00"})
    assert message.status_code == 201
    interaction = client.post("/api/v1/interactions", json={"person_id": person_id, "relationship_id": relationship.json()["id"], "type": "meeting", "occurred_at": "2026-08-23T11:00:00+00:00", "content": "一起喝咖啡"})
    assert interaction.status_code == 201
    response = client.get(f"/api/v1/persons/{person_id}/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["statistics"] == {"relationship_count": 1, "conversation_count": 1, "interaction_count": 1, "message_count": 1}
    assert body["latest_interaction"]["id"] == interaction.json()["id"]


def test_person_profile_isolated_by_user(client):
    person = create_person(client)
    response = client.get(f"/api/v1/persons/{person['id']}/profile", headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"})
    assert response.status_code == 404


def test_person_profile_does_not_mix_other_person_interactions(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    interaction = client.post("/api/v1/interactions", json={"person_id": second["id"], "type": "message", "occurred_at": "2026-08-23T12:00:00+00:00", "content": "属于对象B"})
    assert interaction.status_code == 201
    response = client.get(f"/api/v1/persons/{first['id']}/profile")
    assert response.status_code == 200
    assert response.json()["statistics"]["interaction_count"] == 0
    assert response.json()["latest_interaction"] is None


def test_person_profile_is_read_only(client):
    person = create_person(client)
    before = client.get(f"/api/v1/persons/{person['id']}/profile")
    after = client.get(f"/api/v1/persons/{person['id']}/profile")
    assert before.status_code == 200
    assert after.status_code == 200
    assert after.json() == before.json()


def test_person_profile_relationships_are_deterministically_ordered(client):
    person = create_person(client)
    first = client.post("/api/v1/relationships", json={"person_id": person["id"], "status": "active", "stage": "dating"})
    second = client.post("/api/v1/relationships", json={"person_id": person["id"], "status": "active", "stage": "exclusive"})
    assert first.status_code == 201
    assert second.status_code == 201
    response = client.get(f"/api/v1/persons/{person['id']}/profile")
    assert [item["id"] for item in response.json()["relationships"]] == [first.json()["id"], second.json()["id"]]


def test_person_profile_latest_interaction_uses_occurred_at(client):
    person = create_person(client)
    older = client.post("/api/v1/interactions", json={"person_id": person["id"], "type": "message", "occurred_at": "2026-08-23T12:00:00+00:00", "content": "较早发生"})
    newer = client.post("/api/v1/interactions", json={"person_id": person["id"], "type": "meeting", "occurred_at": "2026-08-24T09:00:00+00:00", "content": "较晚发生"})
    assert older.status_code == 201
    assert newer.status_code == 201
    response = client.get(f"/api/v1/persons/{person['id']}/profile")
    assert response.status_code == 200
    assert response.json()["latest_interaction"]["id"] == newer.json()["id"]


def test_person_profile_missing_person_returns_404(client):
    response = client.get("/api/v1/persons/99999999-9999-9999-9999-999999999999/profile")
    assert response.status_code == 404
