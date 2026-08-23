def create_person(client, name="Timeline测试对象"):
    response = client.post(
        "/api/v1/persons",
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_conversation(client, person_id, title="Timeline会话"):
    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": title,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_message(client, conversation_id, sender_type, content, sent_at):
    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": sender_type,
            "content": content,
            "sent_at": sent_at,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_interaction(client, person_id, interaction_type, occurred_at, content):
    response = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person_id,
            "type": interaction_type,
            "occurred_at": occurred_at,
            "content": content,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_timeline_empty(client):
    person_id = create_person(client)

    response = client.get(f"/api/v1/persons/{person_id}/timeline")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "limit": 50,
        "offset": 0,
        "total": 0,
    }


def test_timeline_aggregates_interaction_conversation_and_message(client):
    person_id = create_person(client)
    conversation_id = create_conversation(client, person_id, "聊天会话")

    interaction_id = create_interaction(
        client,
        person_id,
        "meeting",
        "2026-08-23T12:00:00+00:00",
        "见面",
    )
    message_id = create_message(
        client,
        conversation_id,
        "person",
        "你好",
        "2026-08-23T11:00:00+00:00",
    )

    response = client.get(f"/api/v1/persons/{person_id}/timeline")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [item["source_type"] for item in body["items"]] == [
        "interaction",
        "message",
        "conversation",
    ]
    assert body["items"][0]["id"] == f"interaction:{interaction_id}"
    assert body["items"][0]["event_type"] == "interaction.meeting"
    assert body["items"][1]["id"] == f"message:{message_id}"
    assert body["items"][1]["event_type"] == "message.person"
    assert body["items"][1]["metadata"]["conversation_id"] == conversation_id
    assert body["items"][2]["event_type"] == "conversation.created"


def test_timeline_isolated_by_person_and_user(client):
    person_a = create_person(client, "人物A")
    person_b = create_person(client, "人物B")
    create_interaction(
        client,
        person_a,
        "call",
        "2026-08-23T12:00:00+00:00",
        "A电话",
    )
    create_interaction(
        client,
        person_b,
        "call",
        "2026-08-23T13:00:00+00:00",
        "B电话",
    )

    response = client.get(f"/api/v1/persons/{person_a}/timeline")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["person_id"] == person_a

    other_user = {"X-User-ID": "11111111-1111-1111-1111-111111111111"}
    other_response = client.get(
        f"/api/v1/persons/{person_a}/timeline",
        headers=other_user,
    )
    assert other_response.status_code == 404
    assert other_response.json() == {"detail": "Person not found"}


def test_timeline_pagination(client):
    person_id = create_person(client)
    for minute in range(3):
        create_interaction(
            client,
            person_id,
            "other",
            f"2026-08-23T12:0{minute}:00+00:00",
            f"事件{minute}",
        )

    response = client.get(
        f"/api/v1/persons/{person_id}/timeline?limit=2&offset=1"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["content"] == "事件1"
    assert body["items"][1]["content"] == "事件0"


def test_timeline_rejects_invalid_pagination(client):
    person_id = create_person(client)

    assert client.get(
        f"/api/v1/persons/{person_id}/timeline?limit=0"
    ).status_code == 422
    assert client.get(
        f"/api/v1/persons/{person_id}/timeline?limit=101"
    ).status_code == 422
    assert client.get(
        f"/api/v1/persons/{person_id}/timeline?offset=-1"
    ).status_code == 422


def test_timeline_missing_person_returns_404(client):
    person_id = "00000000-0000-0000-0000-000000000099"

    response = client.get(f"/api/v1/persons/{person_id}/timeline")

    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}


def test_timeline_message_uses_conversation_person(client):
    person_id = create_person(client)
    conversation_id = create_conversation(client, person_id)
    message_id = create_message(
        client,
        conversation_id,
        "user",
        "消息",
        "2026-08-23T10:00:00+00:00",
    )

    response = client.get(f"/api/v1/persons/{person_id}/timeline")

    assert response.status_code == 200
    message_events = [
        item for item in response.json()["items"]
        if item["source_type"] == "message"
    ]
    assert len(message_events) == 1
    assert message_events[0]["source_id"] == message_id
    assert message_events[0]["person_id"] == person_id


def test_timeline_reflects_deleted_message(client):
    person_id = create_person(client)
    conversation_id = create_conversation(client, person_id)
    message_id = create_message(
        client,
        conversation_id,
        "user",
        "待删除",
        "2026-08-23T10:00:00+00:00",
    )

    before = client.get(f"/api/v1/persons/{person_id}/timeline")
    assert before.status_code == 200
    assert before.json()["total"] == 2

    delete_response = client.delete(f"/api/v1/messages/{message_id}")
    assert delete_response.status_code == 204

    after = client.get(f"/api/v1/persons/{person_id}/timeline")
    assert after.status_code == 200
    assert after.json()["total"] == 1
    assert all(
        item["source_id"] != message_id
        for item in after.json()["items"]
    )
