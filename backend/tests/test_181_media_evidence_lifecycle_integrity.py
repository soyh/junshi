from app.services.media_attachment import MediaAttachmentService
from app.ui.media_upload_workspace import MEDIA_UPLOAD_WORKSPACE_SCRIPT


def test_completed_attachment_analysis_is_idempotent():
    class Repository:
        def __init__(self):
            self.row = {
                "id": "attachment-1",
                "conversation_id": "conversation-1",
                "media_type": "image",
                "mime_type": "image/png",
                "storage_path": "/not-used.png",
                "sent_at": "2026-09-24T00:00:00+08:00",
                "analysis_status": "completed",
                "analysis_text": '{"media_summary":"visible chat"}',
                "message_id": "media-evidence-1",
            }
            self.get_calls = 0

        def get(self, conn, user_id, attachment_id):
            self.get_calls += 1
            return self.row

        def try_claim_analysis(self, *args, **kwargs):
            raise AssertionError("completed media must not acquire a new claim")

    repository = Repository()
    service = MediaAttachmentService(repository=repository)

    first, first_token, first_evidence_id = service.claim_analysis(
        object(),
        "user-1",
        "attachment-1",
    )
    second, second_token, second_evidence_id = service.claim_analysis(
        object(),
        "user-1",
        "attachment-1",
    )

    assert first["analysis_status"] == "completed"
    assert second["analysis_status"] == "completed"
    assert first_token is None
    assert second_token is None
    assert first_evidence_id == "media-evidence-1"
    assert second_evidence_id == "media-evidence-1"
    assert repository.get_calls == 2


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
