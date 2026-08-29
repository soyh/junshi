def create_person(client, name="分析会话证据对象"):
    response = client.post(
        "/api/v1/persons",
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "dating",
            "long_term_goal": "建立长期关系",
            "current_goal": "增加互动",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client, person_id, title="分析会话证据"):
    response = client.post(
        "/api/v1/conversations",
        json={"person_id": person_id, "title": title, "status": "active"},
    )
    assert response.status_code == 201
    return response.json()


def test_analysis_context_reuses_canonical_conversation_evidence(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "person",
            "content": "今天见面了",
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
        f"/api/v1/conversations/{conversation['id']}/analysis/evidence"
    )
    analysis = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context"
    )
    assert canonical.status_code == 200
    assert analysis.status_code == 200
    assert analysis.json()["evidence"] == canonical.json()["evidence"]


def test_analysis_context_evidence_is_empty_for_empty_conversation(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context"
    )
    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_analysis_context_evidence_reflects_deleted_message(client):
    person = create_person(client)
    conversation = create_conversation(client, person["id"])
    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "待删除",
            "sent_at": "2026-08-23T10:00:00+00:00",
        },
    )
    assert message.status_code == 201
    message_id = message.json()["id"]

    assert client.delete(f"/api/v1/messages/{message_id}").status_code == 204
    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context"
    )
    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_analysis_context_evidence_isolated_to_target_conversation(client):
    person = create_person(client)
    conversation_a = create_conversation(client, person["id"], "A")
    conversation_b = create_conversation(client, person["id"], "B")

    for conversation_id, content in (
        (conversation_a["id"], "A消息"),
        (conversation_b["id"], "B消息"),
    ):
        response = client.post(
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": "user",
                "content": content,
                "sent_at": "2026-08-23T10:00:00+00:00",
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/v1/conversations/{conversation_a['id']}/analysis/context"
    )
    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert [item["content"] for item in evidence] == ["A消息"]
    assert all(item["conversation_id"] == conversation_a["id"] for item in evidence)
