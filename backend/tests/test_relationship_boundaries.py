def test_relationship_create_requires_owned_person(client):
    missing_person_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": "00000000-0000-0000-0000-000000000099",
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert missing_person_response.status_code == 404
    assert missing_person_response.json() == {
        "detail": "Person not found"
    }

    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "用户隔离测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    other_user_relationship_response = client.post(
        "/api/v1/relationships",
        headers=other_user_headers,
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert other_user_relationship_response.status_code == 404
    assert other_user_relationship_response.json() == {
        "detail": "Person not found"
    }


def test_relationship_missing_resource_boundaries(client):
    missing_relationship_id = "00000000-0000-0000-0000-000000000099"

    get_response = client.get(
        f"/api/v1/relationships/{missing_relationship_id}"
    )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Relationship not found"
    }

    patch_response = client.patch(
        f"/api/v1/relationships/{missing_relationship_id}",
        json={
            "notes": "should not exist",
        },
    )

    assert patch_response.status_code == 404
    assert patch_response.json() == {
        "detail": "Relationship not found"
    }

    delete_response = client.delete(
        f"/api/v1/relationships/{missing_relationship_id}"
    )

    assert delete_response.status_code == 404
    assert delete_response.json() == {
        "detail": "Relationship not found"
    }


def test_relationship_delete_is_complete_and_isolated(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "删除测试对象",
            "nickname": "删除测试",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    relationship_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert relationship_response.status_code == 201

    relationship_id = relationship_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/relationships/{relationship_id}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_after_delete = client.get(
        f"/api/v1/relationships/{relationship_id}"
    )

    assert get_after_delete.status_code == 404
    assert get_after_delete.json() == {
        "detail": "Relationship not found"
    }

    list_after_delete = client.get("/api/v1/relationships")

    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []


def test_relationship_delete_cascades_to_person(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "FK级联删除测试对象",
        },
    )

    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    relationship_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert relationship_response.status_code == 201
    relationship_id = relationship_response.json()["id"]

    person_delete_response = client.delete(
        f"/api/v1/persons/{person_id}",
    )

    assert person_delete_response.status_code == 204
    assert person_delete_response.content == b""

    relationship_response = client.get(
        f"/api/v1/relationships/{relationship_id}",
    )

    assert relationship_response.status_code == 404
    assert relationship_response.json() == {
        "detail": "Relationship not found"
    }


def test_conversation_relationship_delete_sets_relationship_null(
    client,
):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation关系SET NULL测试对象",
        },
    )

    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    relationship_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert relationship_response.status_code == 201
    relationship_id = relationship_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "title": "关系删除后仍保留的会话",
        },
    )

    assert conversation_response.status_code == 201
    conversation_id = conversation_response.json()["id"]

    relationship_delete_response = client.delete(
        f"/api/v1/relationships/{relationship_id}",
    )

    assert relationship_delete_response.status_code == 204
    assert relationship_delete_response.content == b""

    conversation_get_response = client.get(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert conversation_get_response.status_code == 200

    conversation = conversation_get_response.json()

    assert conversation["id"] == conversation_id
    assert conversation["person_id"] == person_id
    assert conversation["relationship_id"] is None


def test_person_delete_cascades_to_conversations_and_messages(
    client,
):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Person级联删除全链路测试对象",
        },
    )

    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "级联删除测试会话",
        },
    )

    assert conversation_response.status_code == 201
    conversation_id = conversation_response.json()["id"]

    message_response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "级联删除测试消息",
        },
    )

    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    person_delete_response = client.delete(
        f"/api/v1/persons/{person_id}",
    )

    assert person_delete_response.status_code == 204
    assert person_delete_response.content == b""

    conversation_get_response = client.get(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert conversation_get_response.status_code == 404
    assert conversation_get_response.json() == {
        "detail": "Conversation not found"
    }

    message_get_response = client.get(
        f"/api/v1/messages/{message_id}",
    )

    assert message_get_response.status_code == 404
    assert message_get_response.json() == {
        "detail": "Message not found"
    }


def test_conversation_delete_cascades_to_messages(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation级联消息测试对象",
        },
    )

    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "会话删除级联消息测试",
        },
    )

    assert conversation_response.status_code == 201
    conversation_id = conversation_response.json()["id"]

    message_response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "应该被级联删除的消息",
        },
    )

    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    conversation_delete_response = client.delete(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert conversation_delete_response.status_code == 204
    assert conversation_delete_response.content == b""

    message_get_response = client.get(
        f"/api/v1/messages/{message_id}",
    )

    assert message_get_response.status_code == 404
    assert message_get_response.json() == {
        "detail": "Message not found"
    }
