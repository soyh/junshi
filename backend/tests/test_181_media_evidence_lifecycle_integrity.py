from app.services.media_attachment import MediaAttachmentService
from app.services.openai_chat_provider import OpenAICompatibleProvider
from app.ui.media_upload_workspace import MEDIA_UPLOAD_WORKSPACE_SCRIPT


def test_completed_attachment_analysis_is_idempotent(monkeypatch):
    class Repository:
        def __init__(self):
            self.row = {
                "id": "attachment-1",
                "conversation_id": "conversation-1",
                "media_type": "image",
                "mime_type": "image/png",
                "storage_path": "/not-used.png",
                "sent_at": "2026-09-24T00:00:00+08:00",
                "analysis_status": "pending",
                "message_id": None,
            }

        def get(self, conn, user_id, attachment_id):
            return self.row

        def mark_completed(
            self,
            conn,
            user_id,
            attachment_id,
            analysis_text,
            message_id,
        ):
            self.row["analysis_status"] = "completed"
            self.row["analysis_text"] = analysis_text
            self.row["message_id"] = message_id
            return self.row

        def mark_failed(self, conn, user_id, attachment_id):
            raise AssertionError("successful media analysis must not be marked failed")

    class MessageService:
        def __init__(self):
            self.create_calls = 0

        def create(
            self,
            conn,
            user_id,
            conversation_id,
            sender_type,
            content,
            sent_at,
        ):
            self.create_calls += 1
            return {"id": "media-evidence-1"}

    repository = Repository()
    message_service = MessageService()
    provider = OpenAICompatibleProvider(
        api_key="vision-secret",
        base_url="https://provider.example/v1",
        model="vision-model",
        timeout_seconds=5,
        provider_name="test",
    )
    service = MediaAttachmentService(
        repository=repository,
        message_service=message_service,
    )
    provider_calls = {"count": 0}

    def build_provider(conn, user_id):
        provider_calls["count"] += 1
        return provider

    monkeypatch.setattr(service.vision_provider_service, "build_provider", build_provider)
    monkeypatch.setattr(
        service,
        "_analyze_with_provider",
        lambda actual_provider, row: '{"media_summary":"visible chat"}',
    )

    first, first_evidence_id = service.analyze(object(), "user-1", "attachment-1")
    second, second_evidence_id = service.analyze(object(), "user-1", "attachment-1")

    assert first["analysis_status"] == "completed"
    assert second["analysis_status"] == "completed"
    assert first_evidence_id == "media-evidence-1"
    assert second_evidence_id == "media-evidence-1"
    assert message_service.create_calls == 1
    assert provider_calls["count"] == 1


def test_delete_attachment_removes_linked_evidence_but_keeps_shared_blob(tmp_path):
    blob = tmp_path / "shared.png"
    blob.write_bytes(b"shared-media")
    captured = {"attachment_deleted": False, "message_ids": []}

    class Repository:
        def get(self, conn, user_id, attachment_id):
            return {
                "storage_path": str(blob),
                "message_id": "media-evidence-1",
            }

        def delete(self, conn, user_id, attachment_id):
            captured["attachment_deleted"] = True
            return True

        def count_for_storage_path(self, conn, user_id, storage_path):
            assert captured["attachment_deleted"] is True
            assert storage_path == str(blob)
            return 1

    class MessageService:
        def delete(self, conn, user_id, message_id):
            captured["message_ids"].append(message_id)
            return True

    service = MediaAttachmentService(
        repository=Repository(),
        message_service=MessageService(),
    )
    service.delete(object(), "user-1", "attachment-1")

    assert captured["message_ids"] == ["media-evidence-1"]
    assert captured["attachment_deleted"] is True
    assert blob.exists()


def test_delete_last_attachment_reference_removes_blob(tmp_path):
    blob = tmp_path / "last.png"
    blob.write_bytes(b"last-media")

    class Repository:
        def get(self, conn, user_id, attachment_id):
            return {
                "storage_path": str(blob),
                "message_id": None,
            }

        def delete(self, conn, user_id, attachment_id):
            return True

        def count_for_storage_path(self, conn, user_id, storage_path):
            return 0

    service = MediaAttachmentService(repository=Repository())
    service.delete(object(), "user-1", "attachment-1")

    assert not blob.exists()


def test_media_delete_ui_refreshes_canonical_evidence_state():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "确定删除附件“${item.original_filename || item.id}”及其媒体证据吗？" in script
    assert "附件及其关联媒体证据已删除。" in script
    assert script.count("await loadMessages(currentMessageWindow || {})") >= 2
    assert "source: '媒体证据删除'" in script
    assert "junshi:evidence-changed" in script
