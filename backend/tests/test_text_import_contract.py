import pytest


VALID_SENDER_TYPES = ["user", "person", "system", "assistant"]


def _create_person(client):
    response = client.post(
        "/api/v1/persons",
        json={"name": "TEST-009 contract person"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.parametrize("sender_type", VALID_SENDER_TYPES)
def test_text_import_accepts_all_supported_sender_types(client, sender_type):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": f"2026-08-23T10:00:00+00:00 | {sender_type} | 测试消息",
        },
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 1
    assert response.json()["candidates"][0]["sender_type"] == sender_type


def test_text_import_without_title_creates_untitled_conversation(client):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "2026-08-23T10:00:00+00:00 | user | 无标题导入",
        },
    )

    assert response.status_code == 201
    conversation_id = response.json()["conversation_id"]

    conversations = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert conversations.status_code == 200
    assert len(conversations.json()) == 1
    assert conversations.json()[0]["id"] == conversation_id
    assert conversations.json()[0]["title"] is None


def test_text_import_preserves_explicit_title(client):
    person_id = _create_person(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "title": "微信聊天导入",
            "text": "2026-08-23T10:00:00+00:00 | person | 保留标题",
        },
    )

    assert response.status_code == 201
    conversations = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert conversations.status_code == 200
    assert conversations.json()[0]["title"] == "微信聊天导入"
