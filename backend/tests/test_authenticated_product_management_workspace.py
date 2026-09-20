PASSWORD = "correct-horse-battery-staple"
NEW_PASSWORD = "new-correct-horse-battery-staple"


def _register(client, username: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_product_shell_exposes_complete_record_management_and_navigation(client):
    html = client.get("/app").text

    for element_id in (
        "account-security",
        "product-management",
        "load-selected-person",
        "update-selected-person",
        "delete-selected-person",
        "load-selected-relationship",
        "update-selected-relationship",
        "delete-selected-relationship",
        "load-selected-conversation",
        "update-selected-conversation",
        "archive-selected-conversation",
        "activate-selected-conversation",
        "delete-selected-conversation",
        "load-managed-interactions",
        "manage-interaction-select",
        "update-selected-interaction",
        "delete-selected-interaction",
        "load-managed-messages",
        "manage-message-select",
        "delete-selected-message",
        "change-password",
    ):
        assert f'id="{element_id}"' in html

    for anchor in (
        "#account-security",
        "#product-management",
        "#conversation-content",
        "#relationship-evidence",
        "#strategy-recommendation",
        "#action-plan-workspace",
        "#action-decision-workspace",
        "#action-execution-workspace",
        "#action-outcome-workspace",
        "#action-feedback-workspace",
        "#action-learning-workspace",
        "#action-reanalysis-workspace",
    ):
        assert f'href="{anchor}"' in html

    assert "Recommendation 及后续生命周期仍不伪造尚未完成的业务页面" not in html
    assert "完整生命周期" in html


def test_management_ui_reuses_canonical_endpoints_and_requires_explicit_delete_confirmation(client):
    html = client.get("/app").text

    assert "/api/v1/persons/${encodeURIComponent(selectedPersonId)}" in html
    assert "/api/v1/persons/${encodeURIComponent(selectedPersonId)}/profile" in html
    assert "/api/v1/relationships/${encodeURIComponent(selectedRelationshipId)}" in html
    assert "/api/v1/conversations/${encodeURIComponent(selectedConversationId)}" in html
    assert "/api/v1/interactions/${encodeURIComponent(selectedManagedInteractionId)}" in html
    assert "/api/v1/messages/${encodeURIComponent(deletingId)}" in html
    assert "method: 'PATCH'" in html
    assert "method: 'DELETE'" in html
    assert "window.confirm" in html

    assert "/app/persons" not in html
    assert "/app/relationships" not in html
    assert "/app/conversations" not in html


def test_message_management_preserves_no_silent_edit_evidence_contract(client):
    html = client.get("/app").text

    assert "Historical messages are not silently edited" in html
    assert "若录入错误，可显式删除后重新添加" in html
    assert "delete-selected-message" in html
    assert "update-selected-message" not in html


def test_account_security_exposes_canonical_password_change_without_browser_persistence(client):
    html = client.get("/app").text

    assert "api('/api/v1/auth/password', {" in html
    assert "method: 'PUT'" in html
    assert "establishSession(data, 'Password changed.')" in html
    assert "current-password-change" in html
    assert "new-password-change" in html
    assert "confirm-new-password-change" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html


def test_person_and_relationship_patch_can_explicitly_clear_nullable_fields(client):
    token = _register(client, "product-clear-fields")
    headers = _auth(token)

    person_response = client.post(
        "/api/v1/persons",
        headers=headers,
        json={
            "name": "Clearable Person",
            "nickname": "Old nickname",
            "notes": "Old person notes",
        },
    )
    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    person_patch = client.patch(
        f"/api/v1/persons/{person_id}",
        headers=headers,
        json={"nickname": None, "notes": None},
    )
    assert person_patch.status_code == 200
    assert person_patch.json()["name"] == "Clearable Person"
    assert person_patch.json()["nickname"] is None
    assert person_patch.json()["notes"] is None

    relationship_response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "dating",
            "long_term_goal": "Old long term goal",
            "current_goal": "Old current goal",
            "notes": "Old relationship notes",
        },
    )
    assert relationship_response.status_code == 201
    relationship_id = relationship_response.json()["id"]

    relationship_patch = client.patch(
        f"/api/v1/relationships/{relationship_id}",
        headers=headers,
        json={
            "long_term_goal": None,
            "current_goal": None,
            "notes": None,
        },
    )
    assert relationship_patch.status_code == 200
    body = relationship_patch.json()
    assert body["status"] == "active"
    assert body["stage"] == "dating"
    assert body["long_term_goal"] is None
    assert body["current_goal"] is None
    assert body["notes"] is None


def test_complete_record_management_round_trip_uses_existing_business_contracts(client):
    token = _register(client, "product-round-trip")
    headers = _auth(token)

    person = client.post(
        "/api/v1/persons",
        headers=headers,
        json={"name": "Managed Person", "nickname": "MP", "notes": "start"},
    )
    assert person.status_code == 201
    person_id = person.json()["id"]

    relationship = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert relationship.status_code == 201
    relationship_id = relationship.json()["id"]

    conversation = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "title": "Managed Conversation",
            "status": "active",
        },
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    interaction = client.post(
        "/api/v1/interactions",
        headers=headers,
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "type": "date",
            "occurred_at": "2026-09-20T00:00:00+00:00",
            "content": "Original interaction",
        },
    )
    assert interaction.status_code == 201
    interaction_id = interaction.json()["id"]

    message = client.post(
        "/api/v1/messages",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "Mistyped evidence message",
            "sent_at": "2026-09-20T00:01:00+00:00",
        },
    )
    assert message.status_code == 201
    message_id = message.json()["id"]

    profile = client.get(f"/api/v1/persons/{person_id}/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["statistics"]["relationship_count"] == 1
    assert profile.json()["statistics"]["conversation_count"] == 1
    assert profile.json()["statistics"]["interaction_count"] == 1
    assert profile.json()["statistics"]["message_count"] == 1

    conversation_patch = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        headers=headers,
        json={
            "relationship_id": None,
            "title": "Renamed Conversation",
            "status": "archived",
        },
    )
    assert conversation_patch.status_code == 200
    assert conversation_patch.json()["relationship_id"] is None
    assert conversation_patch.json()["title"] == "Renamed Conversation"
    assert conversation_patch.json()["status"] == "archived"

    reactivate = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        headers=headers,
        json={"status": "active"},
    )
    assert reactivate.status_code == 200
    assert reactivate.json()["status"] == "active"

    interaction_patch = client.patch(
        f"/api/v1/interactions/{interaction_id}",
        headers=headers,
        json={
            "relationship_id": None,
            "type": "meeting",
            "occurred_at": "2026-09-20T00:02:00+00:00",
            "content": None,
        },
    )
    assert interaction_patch.status_code == 200
    assert interaction_patch.json()["relationship_id"] is None
    assert interaction_patch.json()["type"] == "meeting"
    assert interaction_patch.json()["content"] is None

    assert client.delete(f"/api/v1/messages/{message_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/messages/{message_id}", headers=headers).status_code == 404

    assert client.delete(f"/api/v1/interactions/{interaction_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/conversations/{conversation_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/relationships/{relationship_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/persons/{person_id}", headers=headers).status_code == 204


def test_person_delete_uses_existing_database_cascades_for_owned_records(client):
    token = _register(client, "product-delete-cascade")
    headers = _auth(token)

    person = client.post(
        "/api/v1/persons",
        headers=headers,
        json={"name": "Cascade Person"},
    ).json()
    relationship = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    ).json()
    conversation = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "title": "Cascade Conversation",
            "status": "active",
        },
    ).json()
    message = client.post(
        "/api/v1/messages",
        headers=headers,
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "Cascade message",
        },
    ).json()

    deleted = client.delete(f"/api/v1/persons/{person['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/relationships/{relationship['id']}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/conversations/{conversation['id']}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/messages/{message['id']}", headers=headers).status_code == 404


def test_management_write_scope_remains_isolated_by_authenticated_user(client):
    alice_token = _register(client, "product-scope-alice")
    bob_token = _register(client, "product-scope-bob")
    alice_headers = _auth(alice_token)
    bob_headers = _auth(bob_token)

    person = client.post(
        "/api/v1/persons",
        headers=alice_headers,
        json={"name": "Alice managed person", "notes": "private"},
    ).json()

    assert client.patch(
        f"/api/v1/persons/{person['id']}",
        headers=bob_headers,
        json={"notes": "cross-user overwrite"},
    ).status_code == 404
    assert client.delete(
        f"/api/v1/persons/{person['id']}",
        headers=bob_headers,
    ).status_code == 404

    alice_read = client.get(f"/api/v1/persons/{person['id']}", headers=alice_headers)
    assert alice_read.status_code == 200
    assert alice_read.json()["notes"] == "private"


def test_password_change_from_product_contract_returns_replacement_session(client):
    token = _register(client, "product-password-change")
    response = client.put(
        "/api/v1/auth/password",
        headers=_auth(token),
        json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )
    assert response.status_code == 200
    new_token = response.json()["access_token"]
    assert new_token
    assert new_token != token
    assert client.get("/api/v1/auth/sessions", headers=_auth(new_token)).status_code == 200
