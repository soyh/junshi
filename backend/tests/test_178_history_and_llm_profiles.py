def _conversation(client):
    person = client.post(
        "/api/v1/persons",
        json={"name": "TEST-178 history person"},
    )
    assert person.status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person.json()["id"],
            "title": "TEST-178 bounded history",
        },
    )
    assert conversation.status_code == 201
    return conversation.json()["id"]


def test_history_defaults_to_latest_100_and_supports_time_window(client):
    conversation_id = _conversation(client)
    for index in range(105):
        response = client.post(
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": "user" if index % 2 == 0 else "person",
                "content": f"message-{index:03d}",
                "sent_at": f"2026-09-20T12:{index // 60:02d}:{index % 60:02d}+00:00",
            },
        )
        assert response.status_code == 201

    default_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )
    assert default_response.status_code == 200
    default_items = default_response.json()
    assert len(default_items) == 100
    assert default_items[0]["content"] == "message-005"
    assert default_items[-1]["content"] == "message-104"

    limited = client.get(
        f"/api/v1/conversations/{conversation_id}/messages?limit=10"
    )
    assert limited.status_code == 200
    assert [item["content"] for item in limited.json()] == [
        f"message-{index:03d}" for index in range(95, 105)
    ]

    window = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={
            "from": "2026-09-20T12:00:20+00:00",
            "to": "2026-09-20T12:00:24+00:00",
        },
    )
    assert window.status_code == 200
    assert [item["content"] for item in window.json()] == [
        "message-020",
        "message-021",
        "message-022",
        "message-023",
        "message-024",
    ]


def test_history_message_can_be_modified_deleted_and_is_user_scoped(client):
    conversation_id = _conversation(client)
    created = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "person",
            "content": "original",
            "sent_at": "2026-09-21T10:00:00+00:00",
        },
    )
    assert created.status_code == 201
    message_id = created.json()["id"]

    other_user = {"X-User-ID": "11111111-1111-1111-1111-111111111111"}
    denied = client.patch(
        f"/api/v1/messages/{message_id}",
        headers=other_user,
        json={"content": "should not write"},
    )
    assert denied.status_code == 404

    updated = client.patch(
        f"/api/v1/messages/{message_id}",
        json={
            "sender_type": "user",
            "content": "corrected",
            "sent_at": "2026-09-21T10:05:00+00:00",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["sender_type"] == "user"
    assert body["content"] == "corrected"
    assert body["sent_at"] == "2026-09-21T10:05:00+00:00"

    deleted = client.delete(f"/api/v1/messages/{message_id}")
    assert deleted.status_code == 204


def test_multiple_llm_profiles_can_be_saved_and_switched(client):
    first = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": "Qwen primary",
            "provider": "qwen",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen3.7-flash",
            "api_key": "qwen-secret",
            "timeout_seconds": 45,
        },
    )
    assert first.status_code == 201
    first_body = first.json()
    assert first_body["is_active"] is True
    assert first_body["api_key_configured"] is True
    assert "api_key" not in first_body

    second = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": "DeepSeek backup",
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "api_key": "deepseek-secret",
            "timeout_seconds": 60,
        },
    )
    assert second.status_code == 201
    second_body = second.json()
    assert second_body["is_active"] is False

    listed = client.get("/api/v1/settings/llm/profiles")
    assert listed.status_code == 200
    assert {item["name"] for item in listed.json()} == {
        "Qwen primary",
        "DeepSeek backup",
    }

    activated = client.post(
        f"/api/v1/settings/llm/profiles/{second_body['id']}/activate"
    )
    assert activated.status_code == 200
    assert activated.json()["is_active"] is True

    legacy_view = client.get("/api/v1/settings/llm")
    assert legacy_view.status_code == 200
    assert legacy_view.json()["provider"] == "deepseek"
    assert legacy_view.json()["model"] == "deepseek-chat"
    assert "api_key" not in legacy_view.json()

    renamed = client.put(
        f"/api/v1/settings/llm/profiles/{second_body['id']}",
        json={"name": "DeepSeek active", "model": "deepseek-reasoner"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "DeepSeek active"
    assert renamed.json()["model"] == "deepseek-reasoner"
    assert renamed.json()["api_key_configured"] is True


def test_llm_profiles_are_user_isolated(client):
    created = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": "Private model",
            "provider": "openai_compatible",
            "base_url": "https://provider.example/v1",
            "model": "private-model",
            "api_key": "private-secret",
            "timeout_seconds": 30,
        },
    )
    assert created.status_code == 201
    profile_id = created.json()["id"]

    other_user = {"X-User-ID": "22222222-2222-2222-2222-222222222222"}
    listed = client.get("/api/v1/settings/llm/profiles", headers=other_user)
    assert listed.status_code == 200
    assert listed.json() == []

    denied = client.post(
        f"/api/v1/settings/llm/profiles/{profile_id}/activate",
        headers=other_user,
    )
    assert denied.status_code == 404
