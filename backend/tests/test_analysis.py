def _create_person(client, name="分析测试对象"):
    response = client.post(
        "/api/v1/persons",
        json={
            "name": name,
            "nickname": None,
            "notes": "TEST-010",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_conversation(client, person_id, title="分析测试会话"):
    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "title": title,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_message(client, conversation_id, sender_type, content, sent_at):
    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": sender_type,
            "content": content,
            "sent_at": sent_at,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_analysis_context_returns_persisted_context_and_empty_analysis_lists(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    _create_message(client, conversation_id, "user", "你好", "2026-08-23T10:00:00+00:00")
    _create_message(client, conversation_id, "person", "你好呀", "2026-08-23T10:01:00+00:00")

    response = client.get(f"/api/v1/conversations/{conversation_id}/analysis/context")

    assert response.status_code == 200
    body = response.json()
    assert body["conversation"]["id"] == conversation_id
    assert body["conversation"]["person_id"] == person_id
    assert body["person"]["id"] == person_id
    assert [message["content"] for message in body["messages"]] == ["你好", "你好呀"]
    assert body["evidence"]
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []
    assert set(body["learning_strategy"]) == {"learning_inputs", "strategy_constraints"}
    assert body["relationship_state"] == {
        "current_state": None,
        "evidence": [],
        "facts": [],
        "inferences": [],
        "unknowns": [],
        "recommendations": [],
    }


def test_analysis_context_response_has_stable_top_level_contract(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    response = client.get(f"/api/v1/conversations/{conversation_id}/analysis/context")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "conversation",
        "person",
        "messages",
        "evidence",
        "facts",
        "inferences",
        "unknowns",
        "recommendations",
        "learning_strategy",
        "relationship_state",
    }
    assert isinstance(body["conversation"], dict)
    assert isinstance(body["person"], dict)
    assert isinstance(body["messages"], list)
    assert isinstance(body["evidence"], list)
    assert isinstance(body["facts"], list)
    assert isinstance(body["inferences"], list)
    assert isinstance(body["unknowns"], list)
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["learning_strategy"], dict)
    assert isinstance(body["relationship_state"], dict)


def test_analysis_context_returns_empty_messages_for_empty_conversation(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    response = client.get(f"/api/v1/conversations/{conversation_id}/analysis/context")

    assert response.status_code == 200
    body = response.json()
    assert body["conversation"]["id"] == conversation_id
    assert body["person"]["id"] == person_id
    assert body["messages"] == []
    assert body["evidence"] == []
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []
    assert body["learning_strategy"]["learning_inputs"]["action_feedback"] == []
    assert body["learning_strategy"]["learning_inputs"]["memory_updates"] == []
    assert body["relationship_state"]["current_state"] is None
    assert body["relationship_state"]["evidence"] == []


def test_analysis_context_preserves_message_order_contract(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    _create_message(client, conversation_id, "user", "第二条", "2026-08-23T10:01:00+00:00")
    _create_message(client, conversation_id, "person", "第一条", "2026-08-23T10:00:00+00:00")
    _create_message(client, conversation_id, "user", "同一时刻后写入", "2026-08-23T10:01:00+00:00")

    response = client.get(f"/api/v1/conversations/{conversation_id}/analysis/context")

    assert response.status_code == 200
    assert [message["content"] for message in response.json()["messages"]] == [
        "第一条",
        "第二条",
        "同一时刻后写入",
    ]


def test_analysis_context_rejects_unknown_conversation(client):
    response = client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000099/analysis/context"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_analysis_context_enforces_user_isolation(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/analysis/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_analysis_context_maps_messages_only_from_target_conversation(client):
    person_id = _create_person(client)
    conversation_a = _create_conversation(client, person_id, "A")
    conversation_b = _create_conversation(client, person_id, "B")

    _create_message(client, conversation_a, "user", "A消息", "2026-08-23T10:00:00+00:00")
    _create_message(client, conversation_b, "user", "B消息", "2026-08-23T10:01:00+00:00")

    response = client.get(f"/api/v1/conversations/{conversation_a}/analysis/context")
    assert response.status_code == 200
    assert [message["content"] for message in response.json()["messages"]] == ["A消息"]


def test_analysis_context_reflects_deleted_message(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)
    message_id = _create_message(
        client,
        conversation_id,
        "user",
        "待删除消息",
        "2026-08-23T10:00:00+00:00",
    )

    delete_response = client.delete(f"/api/v1/messages/{message_id}")
    assert delete_response.status_code == 204

    response = client.get(f"/api/v1/conversations/{conversation_id}/analysis/context")
    assert response.status_code == 200
    assert response.json()["messages"] == []
    assert response.json()["evidence"] == []
    assert response.json()["relationship_state"]["evidence"] == []


def test_analysis_context_does_not_persist_analysis_results(client):
    person_id = _create_person(client)
    conversation_id = _create_conversation(client, person_id)
    _create_message(client, conversation_id, "user", "分析输入", "2026-08-23T10:00:00+00:00")

    from app.core.database import get_connection

    with get_connection() as conn:
        before = {
            "persons": conn.execute("SELECT COUNT(*) AS count FROM persons").fetchone()["count"],
            "conversations": conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"],
            "messages": conn.execute("SELECT COUNT(*) AS count FROM messages").fetchone()["count"],
        }

    response = client.get(f"/api/v1/conversations/{conversation_id}/analysis/context")
    assert response.status_code == 200

    with get_connection() as conn:
        after = {
            "persons": conn.execute("SELECT COUNT(*) AS count FROM persons").fetchone()["count"],
            "conversations": conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"],
            "messages": conn.execute("SELECT COUNT(*) AS count FROM messages").fetchone()["count"],
        }

    assert after == before
    assert response.json()["facts"] == []
    assert response.json()["inferences"] == []
    assert response.json()["unknowns"] == []
    assert response.json()["recommendations"] == []
    assert response.json()["learning_strategy"]["strategy_constraints"]["must_not_auto_execute"] is True
    assert response.json()["relationship_state"]["current_state"] is None
