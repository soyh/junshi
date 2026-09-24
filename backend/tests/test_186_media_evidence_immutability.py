import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.media_attachment import MediaAttachmentService


PROTECTED_DETAIL = (
    "Media evidence messages must be managed through the media attachment"
)


def _conversation(client):
    person = client.post(
        "/api/v1/persons",
        json={"name": "TEST-186 media evidence person"},
    )
    assert person.status_code == 201

    conversation = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person.json()["id"],
            "title": "TEST-186 media evidence immutability",
        },
    )
    assert conversation.status_code == 201
    return conversation.json()["id"]


def _completed_media_evidence(client, monkeypatch, tmp_path):
    media_root = tmp_path / "media"
    monkeypatch.setenv("MEDIA_STORAGE_DIRECTORY", str(media_root))
    get_settings.cache_clear()

    conversation_id = _conversation(client)
    user_id = get_settings().local_user_id
    service = MediaAttachmentService()

    with get_connection() as conn:
        attachment = service.create(
            conn,
            user_id=user_id,
            conversation_id=conversation_id,
            original_filename="test186.png",
            mime_type="image/png",
            content=b"TEST-186-CANONICAL-MEDIA-EVIDENCE",
            sent_at="2026-09-24T15:00:00+00:00",
        )

    attachment_id = attachment["id"]
    storage_path = Path(attachment["storage_path"])

    with get_connection() as conn:
        _, claim_token, existing_message_id = service.claim_analysis(
            conn,
            user_id,
            attachment_id,
        )

    assert claim_token
    assert existing_message_id is None

    analysis_text = json.dumps(
        {
            "media_summary": "TEST-186 canonical visible evidence",
            "visible_text": ["immutable"],
            "emotional_signals": [],
            "interaction_signals": [],
            "uncertainty": [],
        },
        ensure_ascii=False,
        sort_keys=True,
    )

    with get_connection() as conn:
        completed, evidence_message_id = service.complete_claimed_analysis(
            conn,
            user_id,
            attachment_id,
            claim_token,
            analysis_text,
        )

    assert completed["analysis_status"] == "completed"
    assert completed["message_id"] == evidence_message_id
    assert storage_path.exists()

    return {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "attachment_id": attachment_id,
        "evidence_message_id": evidence_message_id,
        "analysis_text": analysis_text,
        "storage_path": storage_path,
    }


def test_linked_media_evidence_rejects_generic_patch_and_delete(
    client,
    monkeypatch,
    tmp_path,
):
    state = _completed_media_evidence(client, monkeypatch, tmp_path)
    evidence_id = state["evidence_message_id"]

    original = client.get(f"/api/v1/messages/{evidence_id}")
    assert original.status_code == 200
    original_message = original.json()
    assert original_message["sender_type"] == "system"
    assert original_message["content"].startswith("[媒体证据:image] ")
    assert state["analysis_text"] in original_message["content"]

    content_patch = client.patch(
        f"/api/v1/messages/{evidence_id}",
        json={"content": "tampered media evidence"},
    )
    assert content_patch.status_code == 409
    assert content_patch.json() == {"detail": PROTECTED_DETAIL}

    sender_patch = client.patch(
        f"/api/v1/messages/{evidence_id}",
        json={"sender_type": "user"},
    )
    assert sender_patch.status_code == 409
    assert sender_patch.json() == {"detail": PROTECTED_DETAIL}

    time_patch = client.patch(
        f"/api/v1/messages/{evidence_id}",
        json={"sent_at": "2030-01-01T00:00:00+00:00"},
    )
    assert time_patch.status_code == 409
    assert time_patch.json() == {"detail": PROTECTED_DETAIL}

    delete = client.delete(f"/api/v1/messages/{evidence_id}")
    assert delete.status_code == 409
    assert delete.json() == {"detail": PROTECTED_DETAIL}

    unchanged = client.get(f"/api/v1/messages/{evidence_id}")
    assert unchanged.status_code == 200
    assert unchanged.json()["sender_type"] == original_message["sender_type"]
    assert unchanged.json()["content"] == original_message["content"]
    assert unchanged.json()["sent_at"] == original_message["sent_at"]

    with get_connection() as conn:
        attachment = conn.execute(
            """
            SELECT analysis_status, analysis_text, message_id
            FROM media_attachments
            WHERE id = ? AND user_id = ?
            """,
            (state["attachment_id"], state["user_id"]),
        ).fetchone()

    assert attachment is not None
    assert attachment["analysis_status"] == "completed"
    assert attachment["analysis_text"] == state["analysis_text"]
    assert attachment["message_id"] == evidence_id


def test_attachment_delete_still_removes_protected_evidence_and_blob(
    client,
    monkeypatch,
    tmp_path,
):
    state = _completed_media_evidence(client, monkeypatch, tmp_path)

    response = client.delete(
        f"/api/v1/media/{state['attachment_id']}"
    )
    assert response.status_code == 204

    evidence = client.get(
        f"/api/v1/messages/{state['evidence_message_id']}"
    )
    assert evidence.status_code == 404

    with get_connection() as conn:
        attachment_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM media_attachments
            WHERE id = ?
            """,
            (state["attachment_id"],),
        ).fetchone()[0]
        evidence_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM messages
            WHERE id = ?
            """,
            (state["evidence_message_id"],),
        ).fetchone()[0]

    assert attachment_count == 0
    assert evidence_count == 0
    assert not state["storage_path"].exists()


def test_unlinked_messages_remain_mutable(client):
    conversation_id = _conversation(client)

    created = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "ordinary mutable message",
            "sent_at": "2026-09-24T15:01:00+00:00",
        },
    )
    assert created.status_code == 201
    message_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/messages/{message_id}",
        json={"content": "ordinary message updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["content"] == "ordinary message updated"

    deleted = client.delete(f"/api/v1/messages/{message_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/messages/{message_id}")
    assert missing.status_code == 404
