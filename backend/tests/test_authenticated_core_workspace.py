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


def test_workspace_exposes_authenticated_person_relationship_conversation_controls(client):
    html = client.get("/app").text

    for element_id in (
        "person-name",
        "person-select",
        "load-persons",
        "create-person",
        "relationship-state",
        "relationship-stage",
        "relationship-select",
        "load-relationships",
        "create-relationship",
        "conversation-title",
        "conversation-state",
        "conversation-select",
        "load-conversations",
        "create-conversation",
    ):
        assert f'id="{element_id}"' in html

    for button_id in (
        "load-persons",
        "create-person",
        "load-relationships",
        "create-relationship",
        "load-conversations",
        "create-conversation",
    ):
        assert f'id="{button_id}" class="requires-auth" type="button" disabled' in html


def test_workspace_reuses_existing_canonical_business_endpoints(client):
    html = client.get("/app").text

    assert "api('/api/v1/persons')" in html
    assert "api('/api/v1/persons', {" in html
    assert "api('/api/v1/relationships')" in html
    assert "api('/api/v1/relationships', {" in html
    assert "/api/v1/conversations?person_id=${encodeURIComponent(selectedPersonId)}" in html
    assert "api('/api/v1/conversations', {" in html

    assert "/app/persons" not in html
    assert "/app/relationships" not in html
    assert "/app/conversations" not in html


def test_workspace_binds_relationship_and_conversation_to_current_selection(client):
    html = client.get("/app").text

    assert "person_id: selectedPersonId" in html
    assert "allItems.filter((item) => item.person_id === selectedPersonId)" in html
    assert "relationship_id: selectedRelationshipId || null" in html
    assert "if (!selectedPersonId) throw new Error('Select a person before creating a relationship')" in html
    assert "if (!selectedPersonId) throw new Error('Select a person before creating a conversation')" in html


def test_workspace_conversation_status_and_analysis_selection_follow_existing_contract(client):
    html = client.get("/app").text

    assert '<option value="active">active</option>' in html
    assert '<option value="archived">archived</option>' in html
    assert "selectedConversationId = byId('conversation-select').value || null" in html
    assert "byId('conversation-id').value = selectedConversationId || ''" in html
    assert "/analysis/structured" in html


def test_workspace_keeps_token_memory_only_and_renders_server_data_without_inner_html(client):
    html = client.get("/app").text

    assert "let currentAccessToken = null" in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "replaceChildren()" in html
    assert "document.createElement('option')" in html
    assert ".textContent =" in html

    assert "innerHTML" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert 'id="access-token"' not in html


def test_workspace_logout_clears_business_selection_and_analysis_target(client):
    html = client.get("/app").text

    assert "selectedPersonId = null" in html
    assert "selectedRelationshipId = null" in html
    assert "selectedConversationId = null" in html
    assert "resetWorkspace();" in html
    assert "byId('conversation-id').value = ''" in html


def test_core_workspace_resources_remain_isolated_by_authenticated_user(client):
    alice_token = _register(client, "workspace-alice")
    bob_token = _register(client, "workspace-bob")

    person_response = client.post(
        "/api/v1/persons",
        headers=_auth(alice_token),
        json={
            "name": "Alice Person",
            "nickname": "AP",
            "notes": "TEST-136 bearer scope",
        },
    )
    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    relationship_response = client.post(
        "/api/v1/relationships",
        headers=_auth(alice_token),
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
        headers=_auth(alice_token),
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "title": "Alice Conversation",
            "status": "active",
        },
    )
    assert conversation_response.status_code == 201
    conversation_id = conversation_response.json()["id"]

    alice_persons = client.get("/api/v1/persons", headers=_auth(alice_token))
    alice_relationships = client.get("/api/v1/relationships", headers=_auth(alice_token))
    alice_conversations = client.get(
        f"/api/v1/conversations?person_id={person_id}",
        headers=_auth(alice_token),
    )

    assert [item["id"] for item in alice_persons.json()] == [person_id]
    assert [item["id"] for item in alice_relationships.json()] == [relationship_id]
    assert [item["id"] for item in alice_conversations.json()] == [conversation_id]

    assert client.get("/api/v1/persons", headers=_auth(bob_token)).json() == []
    assert client.get("/api/v1/relationships", headers=_auth(bob_token)).json() == []
    assert client.get("/api/v1/conversations", headers=_auth(bob_token)).json() == []

    assert client.get(
        f"/api/v1/persons/{person_id}", headers=_auth(bob_token)
    ).status_code == 404
    assert client.get(
        f"/api/v1/relationships/{relationship_id}", headers=_auth(bob_token)
    ).status_code == 404
    assert client.get(
        f"/api/v1/conversations/{conversation_id}", headers=_auth(bob_token)
    ).status_code == 404
