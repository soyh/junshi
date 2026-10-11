def test_relationship_crud_duplicate_and_user_isolation(client):
    person_response = client.post(
        "/api/v1/persons",
        json={
            "name": "Relationship测试对象",
            "nickname": "关系测试A",
            "notes": "TEST-002 Relationship CRUD",
        },
    )

    assert person_response.status_code == 201

    person = person_response.json()
    person_id = person["id"]

    create_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
            "long_term_goal": "判断是否适合发展长期关系",
            "current_goal": "建立稳定互动",
            "notes": "TEST-002 Relationship CRUD",
        },
    )

    assert create_response.status_code == 201

    relationship = create_response.json()

    assert relationship["person_id"] == person_id
    assert relationship["status"] == "active"
    assert relationship["stage"] == "initial_contact"
    assert relationship["long_term_goal"] == "判断是否适合发展长期关系"
    assert relationship["current_goal"] == "建立稳定互动"
    assert relationship["notes"] == "TEST-002 Relationship CRUD"
    assert relationship["user_id"] == "00000000-0000-0000-0000-000000000001"

    relationship_id = relationship["id"]

    list_response = client.get("/api/v1/relationships")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == relationship_id

    get_response = client.get(
        f"/api/v1/relationships/{relationship_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == relationship_id

    update_response = client.patch(
        f"/api/v1/relationships/{relationship_id}",
        json={
            "current_goal": "建立稳定且自然的互动",
            "notes": "TEST-002 Relationship CRUD UPDATED",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["current_goal"] == "建立稳定且自然的互动"
    assert update_response.json()["notes"] == "TEST-002 Relationship CRUD UPDATED"

    get_after_update = client.get(
        f"/api/v1/relationships/{relationship_id}"
    )

    assert get_after_update.status_code == 200
    assert get_after_update.json()["current_goal"] == "建立稳定且自然的互动"
    assert get_after_update.json()["notes"] == "TEST-002 Relationship CRUD UPDATED"

    duplicate_response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "initial_contact",
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "Relationship already exists for this person"
    }

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    other_user_get = client.get(
        f"/api/v1/relationships/{relationship_id}",
        headers=other_user_headers,
    )

    assert other_user_get.status_code == 404

    other_user_list = client.get(
        "/api/v1/relationships",
        headers=other_user_headers,
    )

    assert other_user_list.status_code == 200
    assert other_user_list.json() == []
