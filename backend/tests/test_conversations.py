def test_conversation_crud_and_user_isolation(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation测试对象",
            "nickname": "会话测试A",
            "notes": "TEST-005 Conversation CRUD",
        },
    )

    assert person_response.status_code == 201

    person = person_response.json()
    person_id = person["id"]

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": "第一次聊天",
        },
    )

    assert conversation_response.status_code == 201

    conversation = conversation_response.json()

    assert conversation["person_id"] == person_id
    assert conversation["relationship_id"] is None
    assert conversation["title"] == "第一次聊天"
    assert conversation["status"] == "active"
    assert conversation["user_id"] == (
        "00000000-0000-0000-0000-000000000001"
    )

    conversation_id = conversation["id"]

    list_response = client.get(
        "/api/v1/conversations",
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == conversation_id

    filtered_response = client.get(
        f"/api/v1/conversations?person_id={person_id}",
    )

    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1
    assert filtered_response.json()[0]["id"] == conversation_id

    get_response = client.get(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == conversation_id

    update_response = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={
            "title": "第一次聊天 UPDATED",
            "status": "archived",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "第一次聊天 UPDATED"
    assert update_response.json()["status"] == "archived"

    get_after_update = client.get(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert get_after_update.status_code == 200
    assert get_after_update.json()["title"] == "第一次聊天 UPDATED"
    assert get_after_update.json()["status"] == "archived"

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    other_user_get = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=other_user_headers,
    )

    assert other_user_get.status_code == 404

    other_user_list = client.get(
        "/api/v1/conversations",
        headers=other_user_headers,
    )

    assert other_user_list.status_code == 200
    assert other_user_list.json() == []

    other_user_delete = client.delete(
        f"/api/v1/conversations/{conversation_id}",
        headers=other_user_headers,
    )

    assert other_user_delete.status_code == 404

    delete_response = client.delete(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert delete_response.status_code == 204

    get_after_delete = client.get(
        f"/api/v1/conversations/{conversation_id}",
    )

    assert get_after_delete.status_code == 404


def test_conversation_requires_existing_person(client):
    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": "00000000-0000-0000-0000-000000000099",
            "title": "不存在的人",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Person not found"
    }


def test_conversation_rejects_invalid_relationship(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation关系校验对象",
            "nickname": None,
            "notes": None,
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "relationship_id": (
                "00000000-0000-0000-0000-000000000099"
            ),
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Relationship not found"
    }


def test_conversation_rejects_relationship_from_another_person(
    client,
):
    person_a_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation关系对象A",
            "nickname": None,
            "notes": None,
        },
    )

    person_b_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation关系对象B",
            "nickname": None,
            "notes": None,
        },
    )

    assert person_a_response.status_code == 201
    assert person_b_response.status_code == 201

    person_a_id = person_a_response.json()["id"]
    person_b_id = person_b_response.json()["id"]

    relationship_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_a_id,
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert relationship_response.status_code == 201

    relationship_id = relationship_response.json()["id"]

    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_b_id,
            "relationship_id": relationship_id,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Relationship not found"
    }


def test_conversation_patch_can_clear_relationship(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation清除关系对象",
            "nickname": None,
            "notes": None,
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
            "title": "有关系的会话",
        },
    )

    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    clear_response = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={
            "relationship_id": None,
        },
    )

    assert clear_response.status_code == 200
    assert clear_response.json()["relationship_id"] is None


def test_conversation_rejects_invalid_status(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Conversation状态对象",
            "nickname": None,
            "notes": None,
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "status": "invalid",
        },
    )

    assert response.status_code == 422


def test_conversation_list_rejects_unknown_person_filter(client):
    response = client.get(
        "/api/v1/conversations"
        "?person_id=00000000-0000-0000-0000-000000000099"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Person not found"
    }
