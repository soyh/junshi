def create_person(client, name="测试对象"):
    response = client.post(
        "/api/v1/persons",
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def test_person_profile_returns_person_and_empty_aggregates(client):
    person = create_person(client)

    response = client.get(f"/api/v1/persons/{person['id']}/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["person"]["id"] == person["id"]
    assert body["person"]["name"] == "测试对象"
    assert body["relationships"] == []
    assert body["statistics"] == {
        "relationship_count": 0,
        "conversation_count": 0,
        "interaction_count": 0,
        "message_count": 0,
    }
    assert body["latest_interaction"] is None


def test_person_profile_aggregates_existing_person_data(client):
    person = create_person(client)
    person_id = person["id"]

    relationship = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "dating",
            "long_term_goal": "建立长期关系",
            "current_goal": "增加互动",
            "notes": "profile test",
        },
    )
    assert relationship.status_code == 201

    conversation = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "测试会话",
            "status": "active",
        },
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    message = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "sender_type": "person",
            "content": "今天有空吗？",
            "sent_at": "2026-08-23T10:00:00+00:00",
        },
    )
    assert message.status_code == 201

    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person_id,
            "relationship_id": relationship.json()["id"],
            "type": "meeting",
            "occurred_at": "2026-08-23T11:00:00+00:00",
            "content": "一起喝咖啡",
        },
    )
    assert interaction.status_code == 201

    response = client.get(f"/api/v1/persons/{person_id}/profile")

    assert response.status_code == 200
    body = response.json()
    assert len(body["relationships"]) == 1
    assert body["relationships"][0]["id"] == relationship.json()["id"]
    assert body["statistics"] == {
        "relationship_count": 1,
        "conversation_count": 1,
        "interaction_count": 1,
        "message_count": 1,
    }
    assert body["latest_interaction"]["id"] == interaction.json()["id"]
    assert body["latest_interaction"]["content"] == "一起喝咖啡"


def test_person_profile_isolated_by_user(client):
    person = create_person(client)

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    response = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=other_user_headers,
    )

    assert response.status_code == 404


def test_person_profile_does_not_mix_other_person_interactions(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")

    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": second["id"],
            "type": "message",
            "occurred_at": "2026-08-23T12:00:00+00:00",
            "content": "属于对象B",
        },
    )
    assert interaction.status_code == 201

    response = client.get(f"/api/v1/persons/{first['id']}/profile")

    assert response.status_code == 200
    assert response.json()["statistics"]["interaction_count"] == 0
    assert response.json()["latest_interaction"] is None


def test_person_profile_is_read_only(client):
    person = create_person(client)

    before = client.get(f"/api/v1/persons/{person['id']}/profile")
    assert before.status_code == 200

    after = client.get(f"/api/v1/persons/{person['id']}/profile")
    assert after.status_code == 200
    assert after.json() == before.json()
