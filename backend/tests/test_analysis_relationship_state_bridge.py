def create_person(client, name="分析关系状态对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id, **overrides):
    payload = {
        "person_id": person_id,
        "status": "active",
        "stage": "dating",
        "long_term_goal": "建立长期关系",
        "current_goal": "增加互动",
        "notes": "analysis bridge test",
    }
    payload.update(overrides)
    response = client.post("/api/v1/relationships", json=payload)
    assert response.status_code == 201
    return response.json()


def create_conversation(client, person_id, title="分析关系状态会话"):
    response = client.post(
        "/api/v1/conversations",
        json={"person_id": person_id, "title": title, "status": "active"},
    )
    assert response.status_code == 201
    return response.json()


def test_analysis_context_reuses_canonical_relationship_state(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"], stage="exclusive")
    conversation = create_conversation(client, person["id"])

    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "person",
            "content": "最近工作比较忙",
            "sent_at": "2026-08-23T10:00:00+00:00",
        },
    )
    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "meeting",
            "occurred_at": "2026-08-23T11:00:00+00:00",
            "content": "线下见面",
        },
    )
    assert message.status_code == 201
    assert interaction.status_code == 201

    canonical = client.get(
        f"/api/v1/persons/{person['id']}/relationship-analysis/state"
    )
    analysis = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context"
    )
    assert canonical.status_code == 200
    assert analysis.status_code == 200

    canonical_body = canonical.json()
    bridge = analysis.json()["relationship_state"]
    assert bridge["current_state"] == canonical_body["current_state"]
    assert bridge["evidence"] == canonical_body["evidence"]
    assert bridge["facts"] == canonical_body["facts"]
    assert bridge["inferences"] == canonical_body["inferences"]
    assert bridge["unknowns"] == canonical_body["unknowns"]
    assert bridge["recommendations"] == canonical_body["recommendations"]


def test_analysis_context_relationship_state_is_person_scoped_not_conversation_scoped(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    first = create_conversation(client, person["id"], "会话A")
    second = create_conversation(client, person["id"], "会话B")

    first_message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": first["id"],
            "sender_type": "person",
            "content": "A消息",
            "sent_at": "2026-08-23T10:00:00+00:00",
        },
    )
    second_message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": second["id"],
            "sender_type": "person",
            "content": "B消息",
            "sent_at": "2026-08-23T11:00:00+00:00",
        },
    )
    assert first_message.status_code == 201
    assert second_message.status_code == 201

    response = client.get(f"/api/v1/conversations/{first['id']}/analysis/context")
    assert response.status_code == 200
    evidence_ids = [item["source_id"] for item in response.json()["relationship_state"]["evidence"]]
    assert evidence_ids == [first_message.json()["id"], second_message.json()["id"]]
    assert response.json()["relationship_state"]["current_state"]["status"] == relationship["status"]


def test_analysis_context_relationship_state_handles_missing_relationship_without_failure(client):
    person = create_person(client)
    conversation = create_conversation(client, person["id"])

    response = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    assert response.status_code == 200
    assert response.json()["relationship_state"] == {
        "current_state": None,
        "evidence": [],
        "facts": [],
        "inferences": [],
        "unknowns": [],
        "recommendations": [],
    }


def test_analysis_context_relationship_state_respects_user_isolation(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_analysis_context_relationship_state_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"], stage="exclusive")
    conversation = create_conversation(client, person["id"])

    first = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    second = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["relationship_state"] == first.json()["relationship_state"]
