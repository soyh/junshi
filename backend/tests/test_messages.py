def test_message_crud_and_user_isolation(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Message API测试对象",
            "nickname": "消息测试A",
            "notes": "TEST-007 Message API CRUD",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "Message API测试会话",
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    create_response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "第一条API消息",
            "sent_at": "2026-08-17T13:00:00+00:00",
        },
    )

    assert create_response.status_code == 201

    message = create_response.json()

    assert message["conversation_id"] == conversation_id
    assert message["sender_type"] == "user"
    assert message["content"] == "第一条API消息"
    assert message["sent_at"] == "2026-08-17T13:00:00+00:00"
    assert message["user_id"] == (
        "00000000-0000-0000-0000-000000000001"
    )

    message_id = message["id"]

    get_response = client.get(
        f"/api/v1/messages/{message_id}",
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == message_id
    assert get_response.json()["content"] == "第一条API消息"

    list_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )

    assert list_response.status_code == 200

    messages = list_response.json()

    assert len(messages) == 1
    assert messages[0]["id"] == message_id

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    other_user_get = client.get(
        f"/api/v1/messages/{message_id}",
        headers=other_user_headers,
    )

    assert other_user_get.status_code == 404
    assert other_user_get.json() == {
        "detail": "Message not found"
    }

    other_user_list = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=other_user_headers,
    )

    assert other_user_list.status_code == 404
    assert other_user_list.json() == {
        "detail": "Conversation not found"
    }

    other_user_delete = client.delete(
        f"/api/v1/messages/{message_id}",
        headers=other_user_headers,
    )

    assert other_user_delete.status_code == 404
    assert other_user_delete.json() == {
        "detail": "Message not found"
    }

    delete_response = client.delete(
        f"/api/v1/messages/{message_id}",
    )

    assert delete_response.status_code == 204

    get_after_delete = client.get(
        f"/api/v1/messages/{message_id}",
    )

    assert get_after_delete.status_code == 404
    assert get_after_delete.json() == {
        "detail": "Message not found"
    }


def test_message_requires_existing_conversation(client):
    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": (
                "00000000-0000-0000-0000-000000000099"
            ),
            "sender_type": "user",
            "content": "不存在会话的消息",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conversation not found"
    }


def test_message_rejects_invalid_sender_type(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Message非法发送者测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "非法发送者测试会话",
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "invalid",
            "content": "非法发送者",
        },
    )

    assert response.status_code == 422


def test_message_rejects_empty_content(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Message空内容测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "   ",
        },
    )

    assert response.status_code == 422


def test_message_list_orders_by_sent_at(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Message排序测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "消息排序测试",
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    second_response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "assistant",
            "content": "第二条",
            "sent_at": "2026-08-17T13:02:00+00:00",
        },
    )

    assert second_response.status_code == 201

    first_response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "第一条",
            "sent_at": "2026-08-17T13:01:00+00:00",
        },
    )

    assert first_response.status_code == 201

    list_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )

    assert list_response.status_code == 200

    messages = list_response.json()

    assert [item["content"] for item in messages] == [
        "第一条",
        "第二条",
    ]


def test_message_supports_all_sender_types(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Message发送者类型测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "发送者类型测试",
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    for sender_type in (
        "user",
        "person",
        "system",
        "assistant",
    ):
        response = client.post(
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": sender_type,
                "content": f"{sender_type}消息",
            },
        )

        assert response.status_code == 201

        message = response.json()

        assert message["sender_type"] == sender_type
        assert message["content"] == f"{sender_type}消息"

    list_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 4


def test_message_get_missing_returns_404(client):
    message_id = (
        "00000000-0000-0000-0000-000000000099"
    )

    response = client.get(
        f"/api/v1/messages/{message_id}",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Message not found"
    }


def test_message_delete_missing_returns_404(client):
    message_id = (
        "00000000-0000-0000-0000-000000000099"
    )

    response = client.delete(
        f"/api/v1/messages/{message_id}",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Message not found"
    }


def test_conversation_messages_missing_conversation_returns_404(
    client,
):
    conversation_id = (
        "00000000-0000-0000-0000-000000000099"
    )

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conversation not found"
    }


def test_message_delete_does_not_delete_conversation(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Message删除边界测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "删除消息不删除会话",
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    message_response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "待删除消息",
        },
    )

    assert message_response.status_code == 201

    message_id = message_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/messages/{message_id}",
    )

    assert delete_response.status_code == 204

    conversation_get = client.get(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert conversation_get.status_code == 200
    assert conversation_get.json()["id"] == conversation_id

    messages_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )

    assert messages_response.status_code == 200
    assert messages_response.json() == []
