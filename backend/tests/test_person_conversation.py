def _person(client, name):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _conversation(client, person_id, title):
    response = client.post("/api/v1/conversations", json={"person_id": person_id, "title": title})
    assert response.status_code == 201, response.text
    return response.json()


def _message(client, conversation_id, content):
    response = client.post(
        "/api/v1/messages",
        json={"conversation_id": conversation_id, "sender_type": "person", "content": content},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_primary_conversation_is_stable(client):
    person = _person(client, "主会话人物")

    first = client.get(f"/api/v1/persons/{person['id']}/primary-conversation")
    second = client.get(f"/api/v1/persons/{person['id']}/primary-conversation")

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["is_primary"] == 1


def test_consolidate_merges_platform_conversations(client):
    person = _person(client, "多平台人物")
    wechat = _conversation(client, person["id"], "微信")
    xhs = _conversation(client, person["id"], "小红书")

    _message(client, wechat["id"], "微信消息1")
    _message(client, wechat["id"], "微信消息2")
    _message(client, xhs["id"], "小红书消息")

    preview = client.get(f"/api/v1/persons/{person['id']}/consolidate-preview")
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["target_conversation_id"] == wechat["id"]
    assert body["source_conversation_ids"] == [xhs["id"]]
    assert body["messages"] == 1

    merged = client.post(f"/api/v1/persons/{person['id']}/consolidate", json={})
    assert merged.status_code == 200, merged.text
    assert merged.json()["target_conversation_id"] == wechat["id"]
    assert merged.json()["moved"]["messages"] == 1

    history = client.get(f"/api/v1/conversations/{wechat['id']}/messages").json()
    assert [m["content"] for m in history] == ["微信消息1", "微信消息2", "小红书消息"]

    assert client.get(f"/api/v1/conversations/{xhs['id']}").status_code == 404

    conversations = client.get(f"/api/v1/conversations?person_id={person['id']}").json()
    assert [c["id"] for c in conversations] == [wechat["id"]]


def test_pc_ingest_records_platform_source(client):
    from app.core.database import get_connection

    person = _person(client, "平台来源人物")
    conversation = _conversation(client, person["id"], "小红书")

    response = client.post(
        "/api/v1/pc/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "person",
            "content": "来自小红书的消息",
            "operation_id": "11111111-1111-1111-1111-111111111111",
            "platform": "xhs",
            "platform_account_id": "acc-1",
        },
    )
    assert response.status_code == 200, response.text

    with get_connection() as conn:
        row = conn.execute(
            "SELECT platform, account_id FROM message_platform_sources WHERE message_id = ?",
            (response.json()["id"],),
        ).fetchone()
    assert row is not None
    assert row["platform"] == "xhs"
    assert row["account_id"] == "acc-1"


def test_consolidate_rejects_foreign_target(client):
    first = _person(client, "甲")
    second = _person(client, "乙")
    foreign = _conversation(client, second["id"], "别人的会话")
    _conversation(client, first["id"], "自己的会话")

    response = client.post(
        f"/api/v1/persons/{first['id']}/consolidate",
        json={"target_conversation_id": foreign["id"]},
    )
    assert response.status_code == 409
