def _create_person(client, name="Evidence测试对象"):
    response = client.post(
        "/api/v1/persons",
        json={"name": name, "nickname": None, "notes": "TEST-011"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_conversation(client, person_id):
    response = client.post(
        "/api/v1/conversations",
        json={"person_id": person_id, "title": "Evidence测试会话"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_message(client, conversation_id, content, sent_at):
    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "person",
            "content": content,
            "sent_at": sent_at,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_interaction(client, person_id, occurred_at, content):
    response = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person_id,
            "relationship_id": None,
            "type": "meeting",
            "occurred_at": occurred_at,
            "content": content,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_evidence_returns_messages_and_person_interactions(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    message_id = _create_message(
        client, conversation_id, "聊天证据", "2026-08-23T10:01:00+00:00"
    )
    interaction_id = _create_interaction(
        client, person_id, "2026-08-23T10:00:00+00:00", "见面证据"
    )

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == conversation_id
    assert body["person_id"] == person_id
    assert [item["source_id"] for item in body["evidence"]] == [
        interaction_id,
        message_id,
    ]
    assert body["evidence"][0]["source_type"] == "interaction"
    assert body["evidence"][0]["conversation_id"] is None
    assert body["evidence"][1]["source_type"] == "message"
    assert body["evidence"][1]["conversation_id"] == conversation_id


def test_evidence_response_has_stable_contract(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence"
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"conversation_id", "person_id", "evidence"}
    assert isinstance(body["conversation_id"], str)
    assert isinstance(body["person_id"], str)
    assert isinstance(body["evidence"], list)


def test_evidence_preserves_source_metadata(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    _create_message(client, conversation_id, "消息内容", "2026-08-23T10:00:00+00:00")
    _create_interaction(client, person_id, "2026-08-23T10:01:00+00:00", "互动内容")

    evidence = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence"
    ).json()["evidence"]

    message = next(item for item in evidence if item["source_type"] == "message")
    interaction = next(
        item for item in evidence if item["source_type"] == "interaction"
    )

    assert message["content"] == "消息内容"
    assert message["metadata"] == {"sender_type": "person"}
    assert interaction["content"] == "互动内容"
    assert interaction["metadata"] == {"type": "meeting", "relationship_id": None}


def test_evidence_is_deterministically_ordered(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    message_id = _create_message(
        client, conversation_id, "消息", "2026-08-23T10:01:00+00:00"
    )
    first_interaction = _create_interaction(
        client, person_id, "2026-08-23T10:00:00+00:00", "第一"
    )
    second_interaction = _create_interaction(
        client, person_id, "2026-08-23T10:01:00+00:00", "同刻互动"
    )

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence"
    )

    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert [item["source_id"] for item in evidence] == [
        first_interaction,
        second_interaction,
        message_id,
    ]


def test_evidence_rejects_unknown_conversation(client):
    response = client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000099/analysis/evidence"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_evidence_enforces_user_isolation(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_evidence_contains_only_target_conversation_messages(client):
    person_id = _create_person(client)
    conversation_a = _create_conversation(client, person_id)
    conversation_b = _create_conversation(client, person_id)

    _create_message(client, conversation_a, "A消息", "2026-08-23T10:00:00+00:00")
    _create_message(client, conversation_b, "B消息", "2026-08-23T10:01:00+00:00")

    evidence = client.get(
        f"/api/v1/conversations/{conversation_a}/analysis/evidence"
    ).json()["evidence"]

    messages = [item for item in evidence if item["source_type"] == "message"]
    assert [item["content"] for item in messages] == ["A消息"]


def test_evidence_reflects_deleted_sources(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)
    message_id = _create_message(
        client, conversation_id, "待删除", "2026-08-23T10:00:00+00:00"
    )
    interaction_id = _create_interaction(
        client, person_id, "2026-08-23T10:01:00+00:00", "待删除互动"
    )

    assert client.delete(f"/api/v1/messages/{message_id}").status_code == 204
    assert client.delete(f"/api/v1/interactions/{interaction_id}").status_code == 204

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence"
    )

    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_evidence_does_not_persist_results(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)
    _create_message(client, conversation_id, "输入", "2026-08-23T10:00:00+00:00")

    from app.core.database import get_connection

    with get_connection() as conn:
        before = {
            "persons": conn.execute("SELECT COUNT(*) AS count FROM persons").fetchone()["count"],
            "conversations": conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"],
            "messages": conn.execute("SELECT COUNT(*) AS count FROM messages").fetchone()["count"],
            "interactions": conn.execute("SELECT COUNT(*) AS count FROM interactions").fetchone()["count"],
        }

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/evidence"
    )
    assert response.status_code == 200

    with get_connection() as conn:
        after = {
            "persons": conn.execute("SELECT COUNT(*) AS count FROM persons").fetchone()["count"],
            "conversations": conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"],
            "messages": conn.execute("SELECT COUNT(*) AS count FROM messages").fetchone()["count"],
            "interactions": conn.execute("SELECT COUNT(*) AS count FROM interactions").fetchone()["count"],
        }

    assert after == before
