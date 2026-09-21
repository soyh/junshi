def _create_person(client) -> str:
    response = client.post(
        "/api/v1/persons",
        json={"name": "TEST-159 Auto Order Person"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_auto_sort_flag_accepts_reverse_and_mixed_order(client):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "title": "Auto ordered import",
            "auto_sort_by_sent_at": True,
            "text": (
                "2026-09-21T10:02:00+08:00 | user | 第三条\n"
                "2026-09-21T10:00:00+08:00 | person | 第一条\n"
                "2026-09-21T10:01:00+08:00 | user | 第二条"
            ),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["imported_count"] == 3
    assert [item["line_number"] for item in body["candidates"]] == [2, 3, 1]
    assert [item["content"] for item in body["candidates"]] == [
        "第一条",
        "第二条",
        "第三条",
    ]

    messages = client.get(
        f"/api/v1/conversations/{body['conversation_id']}/messages"
    )
    assert messages.status_code == 200
    assert [item["content"] for item in messages.json()] == [
        "第一条",
        "第二条",
        "第三条",
    ]


def test_auto_sort_is_stable_for_equal_timestamps(client):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "auto_sort_by_sent_at": True,
            "text": (
                "2026-09-21T10:01:00+08:00 | user | 稍后\n"
                "2026-09-21T10:00:00+08:00 | person | 同时第一条\n"
                "2026-09-21T10:00:00+08:00 | user | 同时第二条"
            ),
        },
    )

    assert response.status_code == 201
    candidates = response.json()["candidates"]
    assert [item["line_number"] for item in candidates] == [2, 3, 1]
    assert [item["content"] for item in candidates] == [
        "同时第一条",
        "同时第二条",
        "稍后",
    ]


def test_default_contract_still_rejects_out_of_order_messages(client):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": (
                "2026-09-21T10:01:00+08:00 | user | 第二条\n"
                "2026-09-21T10:00:00+08:00 | person | 第一条"
            ),
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Import messages must be ordered by sent_at"


def test_auto_sort_still_rejects_invalid_timestamp_without_conversation(client):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "auto_sort_by_sent_at": True,
            "text": (
                "2026-09-21T10:00:00+08:00 | user | 正常\n"
                "not-a-timestamp | person | 非法时间"
            ),
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid timestamp at line 2"

    conversations = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert conversations.status_code == 200
    assert conversations.json() == []


def test_product_page_explicitly_requests_auto_order(client):
    html = client.get("/app").text

    assert "auto_sort_by_sent_at: true" in html
    assert "粘贴内容可以是正序、倒序或局部乱序" in html
    assert "同一时间的消息保持原粘贴顺序" in html
