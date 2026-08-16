def test_person_crud_and_user_isolation(client):
    create_response = client.post(
        "/api/v1/persons",
        json={
            "name": "自动化测试对象",
            "nickname": "测试A",
            "notes": "TEST-001 Person CRUD",
        },
    )

    assert create_response.status_code == 201

    person = create_response.json()

    assert person["name"] == "自动化测试对象"
    assert person["nickname"] == "测试A"
    assert person["notes"] == "TEST-001 Person CRUD"
    assert person["user_id"] == "00000000-0000-0000-0000-000000000001"

    person_id = person["id"]

    list_response = client.get("/api/v1/persons")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == person_id

    get_response = client.get(
        f"/api/v1/persons/{person_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == person_id

    update_response = client.patch(
        f"/api/v1/persons/{person_id}",
        json={
            "notes": "TEST-001 Person CRUD UPDATED",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "TEST-001 Person CRUD UPDATED"

    get_after_update = client.get(
        f"/api/v1/persons/{person_id}"
    )

    assert get_after_update.status_code == 200
    assert get_after_update.json()["notes"] == "TEST-001 Person CRUD UPDATED"

    other_user_headers = {
        "X-User-ID": "11111111-1111-1111-1111-111111111111"
    }

    other_user_get = client.get(
        f"/api/v1/persons/{person_id}",
        headers=other_user_headers,
    )

    assert other_user_get.status_code == 404

    other_user_list = client.get(
        "/api/v1/persons",
        headers=other_user_headers,
    )

    assert other_user_list.status_code == 200
    assert other_user_list.json() == []
