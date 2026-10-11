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


def _create_person_relationship(client, token: str):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "TEST-138 Person"},
    )
    assert person.status_code == 201
    person_id = person.json()["id"]

    relationship = client.post(
        "/api/v1/relationships",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "unknown",
        },
    )
    assert relationship.status_code == 201
    return person_id, relationship.json()["id"]


def test_product_shell_exposes_relationship_evidence_and_timeline_workspace(client):
    html = client.get("/app").text

    for control_id in (
        "relationship-evidence",
        "interaction-type",
        "interaction-occurred-at",
        "interaction-content",
        "load-interactions",
        "create-interaction",
        "interaction-list",
        "load-timeline",
        "timeline-list",
    ):
        assert f'id="{control_id}"' in html

    assert "/api/v1/interactions" in html
    assert "/timeline?limit=50&offset=0" in html
    for interaction_type in ("message", "call", "meeting", "date", "gift", "other"):
        assert f'<option value="{interaction_type}">{interaction_type}</option>' in html


def test_evidence_workspace_reuses_single_page_token_and_safe_dom_boundary(client):
    html = client.get("/app").text

    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "relationship_id: selectedRelationshipId" in html
    assert "textContent" in html
    assert "replaceChildren" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert 'id="access-token"' not in html

    evidence_script = html.index("const interactionStatus = byId('interaction-status')")
    shell_close = html.index("  clearSession();\n})();")
    assert evidence_script < shell_close


def test_evidence_workspace_controls_are_auth_gated(client):
    html = client.get("/app").text

    for control_id in (
        "interaction-type",
        "interaction-occurred-at",
        "interaction-content",
        "load-interactions",
        "create-interaction",
        "load-timeline",
    ):
        marker = f'id="{control_id}" class="requires-auth"'
        assert marker in html
        segment = html[html.index(marker): html.index(marker) + 220]
        assert "disabled" in segment


def test_real_bearer_can_create_relationship_bound_interaction_and_timeline_event(client):
    token = _register(client, "test138-interaction-user")
    person_id, relationship_id = _create_person_relationship(client, token)

    created = client.post(
        "/api/v1/interactions",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "type": "date",
            "occurred_at": "2026-09-18T15:00:00+00:00",
            "content": "一起吃晚餐",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["relationship_id"] == relationship_id
    assert body["type"] == "date"

    listed = client.get(
        "/api/v1/interactions",
        headers=_auth(token),
        params={"person_id": person_id},
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [body["id"]]

    timeline = client.get(
        f"/api/v1/persons/{person_id}/timeline",
        headers=_auth(token),
    )
    assert timeline.status_code == 200
    interaction_events = [
        item for item in timeline.json()["items"]
        if item["source_type"] == "interaction"
    ]
    assert len(interaction_events) == 1
    assert interaction_events[0]["source_id"] == body["id"]
    assert interaction_events[0]["event_type"] == "interaction.date"


def test_real_bearer_can_create_person_level_interaction_without_relationship(client):
    token = _register(client, "test138-person-level-user")
    person_id, _ = _create_person_relationship(client, token)

    created = client.post(
        "/api/v1/interactions",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "relationship_id": None,
            "type": "call",
            "occurred_at": "2026-09-18T16:00:00+00:00",
            "content": "电话沟通",
        },
    )
    assert created.status_code == 201
    assert created.json()["relationship_id"] is None


def test_real_bearer_scope_blocks_foreign_interactions_and_timeline(client):
    alice = _register(client, "test138-alice")
    bob = _register(client, "test138-bob")
    person_id, relationship_id = _create_person_relationship(client, alice)

    created = client.post(
        "/api/v1/interactions",
        headers=_auth(alice),
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "type": "meeting",
            "occurred_at": "2026-09-18T17:00:00+00:00",
            "content": "Alice only",
        },
    )
    assert created.status_code == 201

    foreign_list = client.get(
        "/api/v1/interactions",
        headers=_auth(bob),
        params={"person_id": person_id},
    )
    assert foreign_list.status_code == 404
    assert foreign_list.json() == {"detail": "Person not found"}

    foreign_timeline = client.get(
        f"/api/v1/persons/{person_id}/timeline",
        headers=_auth(bob),
    )
    assert foreign_timeline.status_code == 404
    assert foreign_timeline.json() == {"detail": "Person not found"}


def test_timeline_canonically_aggregates_conversation_message_and_interaction(client):
    token = _register(client, "test138-timeline-user")
    person_id, relationship_id = _create_person_relationship(client, token)

    conversation = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "title": "TEST-138 conversation",
        },
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    message = client.post(
        "/api/v1/messages",
        headers=_auth(token),
        json={
            "conversation_id": conversation_id,
            "sender_type": "person",
            "content": "timeline message",
            "sent_at": "2026-09-18T18:00:00+00:00",
        },
    )
    assert message.status_code == 201

    interaction = client.post(
        "/api/v1/interactions",
        headers=_auth(token),
        json={
            "person_id": person_id,
            "relationship_id": relationship_id,
            "type": "gift",
            "occurred_at": "2026-09-18T19:00:00+00:00",
            "content": "timeline interaction",
        },
    )
    assert interaction.status_code == 201

    timeline = client.get(
        f"/api/v1/persons/{person_id}/timeline",
        headers=_auth(token),
    )
    assert timeline.status_code == 200
    body = timeline.json()
    source_types = {item["source_type"] for item in body["items"]}
    assert {"conversation", "message", "interaction"}.issubset(source_types)
    assert any(
        item["source_id"] == message.json()["id"]
        for item in body["items"]
    )
    assert any(
        item["source_id"] == interaction.json()["id"]
        for item in body["items"]
    )
