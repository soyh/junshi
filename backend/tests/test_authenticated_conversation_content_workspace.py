PASSWORD = "correct-horse-battery-staple"


def _register(client, username: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_and_conversation(client, token: str, *, title="TEST-137 Conversation"):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "TEST-137 Person"},
    )
    assert person.status_code == 201
    person_id = person.json()["id"]

    conversation = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"person_id": person_id, "title": title},
    )
    assert conversation.status_code == 201
    return person_id, conversation.json()["id"]


def test_product_shell_exposes_authenticated_conversation_content_workspace(client):
    html = client.get("/app").text

    for control_id in (
        "conversation-content",
        "message-sender",
        "message-sent-at",
        "message-content",
        "load-messages",
        "create-message",
        "message-list",
        "text-import-body",
        "import-text",
    ):
        assert f'id="{control_id}"' in html

    assert 'id="text-import-title"' not in html
    assert "/api/v1/messages" in html
    assert "/messages`" in html
    assert "/api/v1/text-imports" in html
    assert "Import into current conversation" in html
    assert "conversation_id: targetConversationId" in html
    assert "不会因为批量导入而自动新建会话" in html


def test_content_workspace_exposes_multi_conversation_switching(client):
    html = client.get("/app").text

    assert "当前人物可以保留多个会话" in html
    assert "card.classList.remove('lifecycle-primary-conversation-only')" in html
    assert "select.size = 8" in html
    assert "当前人物的会话（可切换）" in html
    assert "options[0]" in html
    assert "lifecycleEnsurePrimaryConversation = async function()" in html


def test_content_workspace_reuses_single_page_token_boundary(client):
    html = client.get("/app").text

    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert 'id="access-token"' not in html

    content_script = html.index("const messagesStatus = byId('messages-status')")
    shell_close = html.index("  clearSession();\n})();")
    assert content_script < shell_close


def test_content_workspace_controls_are_auth_gated(client):
    html = client.get("/app").text

    for control_id in (
        "message-sender",
        "message-sent-at",
        "message-content",
        "load-messages",
        "create-message",
        "text-import-body",
        "import-text",
    ):
        marker = f'id="{control_id}" class="requires-auth"'
        assert marker in html
        segment = html[html.index(marker): html.index(marker) + 220]
        assert "disabled" in segment


def test_real_bearer_session_can_append_and_list_messages(client):
    token = _register(client, "test137-message-user")
    _, conversation_id = _create_person_and_conversation(client, token)

    first = client.post(
        "/api/v1/messages",
        headers=_auth(token),
        json={
            "conversation_id": conversation_id,
            "sender_type": "person",
            "content": "真实聊天内容",
            "sent_at": "2026-09-18T12:00:00+00:00",
        },
    )
    assert first.status_code == 201

    listed = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=_auth(token),
    )
    assert listed.status_code == 200
    assert [(item["sender_type"], item["content"]) for item in listed.json()] == [
        ("person", "真实聊天内容")
    ]


def test_real_bearer_scope_blocks_foreign_conversation_messages(client):
    alice = _register(client, "test137-alice")
    bob = _register(client, "test137-bob")
    _, conversation_id = _create_person_and_conversation(client, alice)

    created = client.post(
        "/api/v1/messages",
        headers=_auth(alice),
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "Alice only",
        },
    )
    assert created.status_code == 201

    foreign_list = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=_auth(bob),
    )
    assert foreign_list.status_code == 404
    assert foreign_list.json() == {"detail": "Conversation not found"}


def test_text_import_preserves_legacy_contract_and_can_create_new_conversation(client):
    token = _register(client, "test137-import-user")
    person_id, existing_conversation_id = _create_person_and_conversation(client, token)

    imported = client.post(
        "/api/v1/text-imports",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "title": "Imported Conversation",
            "text": (
                "2026-09-18T12:00:00+00:00 | user | 第一条\n"
                "2026-09-18T12:01:00+00:00 | person | 第二条"
            ),
        },
    )
    assert imported.status_code == 201
    body = imported.json()
    assert body["conversation_id"] != existing_conversation_id
    assert body["imported_count"] == 2

    old_messages = client.get(
        f"/api/v1/conversations/{existing_conversation_id}/messages",
        headers=_auth(token),
    )
    assert old_messages.status_code == 200
    assert old_messages.json() == []

    new_messages = client.get(
        f"/api/v1/conversations/{body['conversation_id']}/messages",
        headers=_auth(token),
    )
    assert new_messages.status_code == 200
    assert [item["content"] for item in new_messages.json()] == ["第一条", "第二条"]


def test_text_import_can_append_batch_to_existing_conversation(client):
    token = _register(client, "test166-import-existing")
    person_id, conversation_id = _create_person_and_conversation(client, token)

    imported = client.post(
        "/api/v1/text-imports",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "conversation_id": conversation_id,
            "title": "must not rename existing conversation",
            "text": (
                "2026-09-20T12:00:00+00:00 | user | 批量第一条\n"
                "2026-09-20T12:01:00+00:00 | person | 批量第二条"
            ),
            "auto_sort_by_sent_at": True,
        },
    )

    assert imported.status_code == 201
    body = imported.json()
    assert body["conversation_id"] == conversation_id
    assert body["imported_count"] == 2

    conversations = client.get(
        f"/api/v1/conversations?person_id={person_id}",
        headers=_auth(token),
    )
    assert conversations.status_code == 200
    assert len(conversations.json()) == 1
    assert conversations.json()[0]["title"] == "TEST-137 Conversation"

    messages = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=_auth(token),
    )
    assert messages.status_code == 200
    assert [item["content"] for item in messages.json()] == [
        "批量第一条",
        "批量第二条",
    ]


def test_text_import_rejects_conversation_from_different_person(client):
    token = _register(client, "test166-import-person-mismatch")
    first_person_id, first_conversation_id = _create_person_and_conversation(
        client,
        token,
        title="First person conversation",
    )
    second_person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "Second Person"},
    )
    assert second_person.status_code == 201
    second_person_id = second_person.json()["id"]

    response = client.post(
        "/api/v1/text-imports",
        headers=_auth(token),
        json={
            "person_id": second_person_id,
            "conversation_id": first_conversation_id,
            "text": "2026-09-20T12:00:00+00:00 | user | blocked",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Conversation does not belong to person"}

    messages = client.get(
        f"/api/v1/conversations/{first_conversation_id}/messages",
        headers=_auth(token),
    )
    assert messages.status_code == 200
    assert messages.json() == []
    assert first_person_id != second_person_id


def test_text_import_rejects_foreign_conversation_scope(client):
    alice = _register(client, "test166-import-alice")
    bob = _register(client, "test166-import-bob")
    _, alice_conversation_id = _create_person_and_conversation(client, alice)
    bob_person_id, _ = _create_person_and_conversation(client, bob)

    response = client.post(
        "/api/v1/text-imports",
        headers=_auth(bob),
        json={
            "person_id": bob_person_id,
            "conversation_id": alice_conversation_id,
            "text": "2026-09-20T12:00:00+00:00 | user | blocked",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_same_person_can_list_multiple_conversations(client):
    token = _register(client, "test166-multiple-conversations")
    person_id, first_conversation_id = _create_person_and_conversation(
        client,
        token,
        title="Conversation A",
    )
    second = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"person_id": person_id, "title": "Conversation B"},
    )
    assert second.status_code == 201
    second_conversation_id = second.json()["id"]

    listed = client.get(
        f"/api/v1/conversations?person_id={person_id}",
        headers=_auth(token),
    )

    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()}
    assert ids == {first_conversation_id, second_conversation_id}
    assert {item["title"] for item in listed.json()} == {
        "Conversation A",
        "Conversation B",
    }


def test_text_import_cannot_use_foreign_person_scope(client):
    alice = _register(client, "test137-import-alice")
    bob = _register(client, "test137-import-bob")
    person_id, _ = _create_person_and_conversation(client, alice)

    response = client.post(
        "/api/v1/text-imports",
        headers=_auth(bob),
        json={
            "person_id": person_id,
            "text": "2026-09-18T12:00:00+00:00 | user | blocked",
        },
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}
