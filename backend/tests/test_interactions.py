def test_interaction_crud_filter_and_isolation(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Interaction测试对象",
            "nickname": "互动测试A",
            "notes": "TEST-005 Interaction CRUD",
        },
    )

    assert person_response.status_code == 201

    person = person_response.json()
    person_id = person["id"]

    relationship_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
            "long_term_goal": "测试互动记录",
            "current_goal": "建立稳定互动",
            "notes": "TEST-005",
        },
    )

    assert relationship_response.status_code == 201

    relationship = relationship_response.json()
    relationship_id = relationship["id"]

    create_response = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "type": "message",
            "occurred_at": "2026-08-16T12:00:00+00:00",
            "content": "TEST-005 第一条互动记录",
        },
    )

    assert create_response.status_code == 201

    interaction = create_response.json()

    assert interaction["person_id"] == person_id
    assert interaction["relationship_id"] == relationship_id
    assert interaction["type"] == "message"
    assert interaction["content"] == "TEST-005 第一条互动记录"
    assert interaction["user_id"] == "00000000-0000-0000-0000-000000000001"

    interaction_id = interaction["id"]

    list_response = client.get("/api/v1/interactions")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == interaction_id

    filtered_response = client.get(
        "/api/v1/interactions",
        params={"person_id": person_id},
    )

    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1
    assert filtered_response.json()[0]["id"] == interaction_id

    get_response = client.get(
        f"/api/v1/interactions/{interaction_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == interaction_id

    update_response = client.patch(
        f"/api/v1/interactions/{interaction_id}",
        json={
            "type": "call",
            "content": "TEST-005 更新后的互动记录",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["type"] == "call"
    assert update_response.json()["content"] == "TEST-005 更新后的互动记录"

    get_after_update = client.get(
        f"/api/v1/interactions/{interaction_id}"
    )

    assert get_after_update.status_code == 200
    assert get_after_update.json()["type"] == "call"
    assert get_after_update.json()["content"] == "TEST-005 更新后的互动记录"

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    other_user_get = client.get(
        f"/api/v1/interactions/{interaction_id}",
        headers=other_user_headers,
    )

    assert other_user_get.status_code == 404

    other_user_list = client.get(
        "/api/v1/interactions",
        headers=other_user_headers,
    )

    assert other_user_list.status_code == 200
    assert other_user_list.json() == []


def test_interaction_boundaries(client):
    missing_interaction_id = (
        "00000000-0000-0000-0000-000000000099"
    )

    get_response = client.get(
        f"/api/v1/interactions/{missing_interaction_id}"
    )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Interaction not found"
    }

    patch_response = client.patch(
        f"/api/v1/interactions/{missing_interaction_id}",
        json={
            "content": "should not exist",
        },
    )

    assert patch_response.status_code == 404
    assert patch_response.json() == {
        "detail": "Interaction not found"
    }

    delete_response = client.delete(
        f"/api/v1/interactions/{missing_interaction_id}"
    )

    assert delete_response.status_code == 404
    assert delete_response.json() == {
        "detail": "Interaction not found"
    }


def test_interaction_requires_owned_person(client):
    response = client.post(
        "/api/v1/interactions",
        json={
            "person_id": "00000000-0000-0000-0000-000000000099",
            "type": "message",
            "occurred_at": "2026-08-16T12:00:00+00:00",
            "content": "should fail",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Person not found"
    }


def test_interaction_rejects_invalid_type(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "非法类型测试对象",
        },
    )

    assert person_response.status_code == 201

    person_id = person_response.json()["id"]

    response = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person_id,
            "type": "invalid_type",
            "occurred_at": "2026-08-16T12:00:00+00:00",
            "content": "should fail",
        },
    )

    assert response.status_code == 422
