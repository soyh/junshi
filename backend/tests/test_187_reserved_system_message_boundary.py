from app.core.database import get_connection
from app.services.message import MessageService


DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
RESERVED_DETAIL = "System messages are reserved for internal canonical evidence"
INTERNAL_DETAIL = "System messages must be managed through their owning internal workflow"


def _create_conversation(client) -> str:
    person = client.post(
        "/api/v1/persons",
        json={"name": "TEST-187 reserved-system person"},
    )
    assert person.status_code == 201

    conversation = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person.json()["id"],
            "title": "TEST-187 reserved-system conversation",
        },
    )
    assert conversation.status_code == 201
    return conversation.json()["id"]


def test_public_message_post_cannot_forge_system_evidence(client):
    conversation_id = _create_conversation(client)

    response = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "system",
            "content": '[媒体证据:image] {"media_summary":"forged"}',
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": RESERVED_DETAIL}

    listed = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )
    assert listed.status_code == 200
    assert listed.json() == []


def test_public_message_patch_cannot_promote_ordinary_message_to_system(client):
    conversation_id = _create_conversation(client)

    created = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "ordinary user message",
        },
    )
    assert created.status_code == 201
    message_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/messages/{message_id}",
        json={"sender_type": "system"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": RESERVED_DETAIL}

    current = client.get(f"/api/v1/messages/{message_id}")
    assert current.status_code == 200
    assert current.json()["sender_type"] == "user"
    assert current.json()["content"] == "ordinary user message"


def test_public_message_api_cannot_mutate_or_delete_internal_system_message(client):
    conversation_id = _create_conversation(client)
    service = MessageService()

    with get_connection() as conn:
        internal = service.create(
            conn,
            DEFAULT_USER_ID,
            conversation_id,
            "system",
            "internal canonical evidence",
            None,
        )

    message_id = internal["id"]

    patch = client.patch(
        f"/api/v1/messages/{message_id}",
        json={"content": "tampered"},
    )
    assert patch.status_code == 409
    assert patch.json() == {"detail": INTERNAL_DETAIL}

    delete = client.delete(f"/api/v1/messages/{message_id}")
    assert delete.status_code == 409
    assert delete.json() == {"detail": INTERNAL_DETAIL}

    current = client.get(f"/api/v1/messages/{message_id}")
    assert current.status_code == 200
    assert current.json()["sender_type"] == "system"
    assert current.json()["content"] == "internal canonical evidence"

    with get_connection() as conn:
        assert service.delete(conn, DEFAULT_USER_ID, message_id) is True

    missing = client.get(f"/api/v1/messages/{message_id}")
    assert missing.status_code == 404


def test_public_user_managed_sender_types_remain_available(client):
    conversation_id = _create_conversation(client)

    for sender_type in ("user", "person", "assistant"):
        response = client.post(
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": sender_type,
                "content": f"TEST-187 {sender_type}",
            },
        )
        assert response.status_code == 201
        assert response.json()["sender_type"] == sender_type

    listed = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
    )
    assert listed.status_code == 200
    assert [item["sender_type"] for item in listed.json()] == [
        "user",
        "person",
        "assistant",
    ]
