import asyncio
import hashlib
import sqlite3
from contextlib import contextmanager

import pytest

from app.api.routes import media_attachments as media_routes
from app.services.media_attachment import MediaAttachmentService


def test_create_repository_failure_removes_new_blob(tmp_path, monkeypatch):
    class Repository:
        def create(self, conn, **kwargs):
            raise RuntimeError("database insert failed")

    class ConversationService:
        def get(self, conn, user_id, conversation_id):
            return {"person_id": "person-1"}

    service = MediaAttachmentService(
        repository=Repository(),
        conversation_service=ConversationService(),
    )
    monkeypatch.setattr(
        MediaAttachmentService,
        "_storage_root",
        staticmethod(lambda: tmp_path),
    )

    content = b"transactional-media"
    expected = (
        tmp_path
        / "user-1"
        / "conversation-1"
        / f"{hashlib.sha256(content).hexdigest()}.png"
    )

    with pytest.raises(RuntimeError, match="database insert failed"):
        service.create(
            object(),
            user_id="user-1",
            conversation_id="conversation-1",
            original_filename="proof.png",
            mime_type="image/png",
            content=content,
            sent_at=None,
        )

    assert not expected.exists()


def test_upload_commit_failure_cleans_unreferenced_blob(tmp_path, monkeypatch):
    blob = tmp_path / "rollback-upload.png"
    calls = {"connections": 0, "cleanup": 0}

    class Upload:
        filename = "rollback-upload.png"
        content_type = "image/png"

        async def read(self):
            return b"upload"

    class Service:
        def create(self, conn, **kwargs):
            blob.write_bytes(b"upload")
            return {"id": "attachment-1", "storage_path": str(blob)}

        def cleanup_unreferenced_blob(self, conn, user_id, storage_path):
            calls["cleanup"] += 1
            assert storage_path == str(blob)
            blob.unlink(missing_ok=True)
            return True

    @contextmanager
    def connection():
        calls["connections"] += 1
        invocation = calls["connections"]
        yield object()
        if invocation == 1:
            raise sqlite3.OperationalError("commit failed")

    monkeypatch.setattr(media_routes, "service", Service())
    monkeypatch.setattr(media_routes, "get_connection", connection)

    with pytest.raises(sqlite3.OperationalError, match="commit failed"):
        asyncio.run(
            media_routes.upload_media_attachment(
                "conversation-1",
                Upload(),
                sent_at=None,
                user_id="user-1",
            )
        )

    assert calls["connections"] == 2
    assert calls["cleanup"] == 1
    assert not blob.exists()


def test_delete_commit_failure_never_unlinks_blob(tmp_path, monkeypatch):
    blob = tmp_path / "rollback-delete.png"
    blob.write_bytes(b"keep-me")
    calls = {"cleanup": 0}

    class Service:
        def delete(self, conn, user_id, attachment_id, *, defer_blob_cleanup=False):
            assert defer_blob_cleanup is True
            return str(blob)

        def cleanup_unreferenced_blob(self, conn, user_id, storage_path):
            calls["cleanup"] += 1
            blob.unlink(missing_ok=True)
            return True

    @contextmanager
    def connection():
        yield object()
        raise sqlite3.OperationalError("commit failed")

    monkeypatch.setattr(media_routes, "service", Service())
    monkeypatch.setattr(media_routes, "get_connection", connection)

    with pytest.raises(sqlite3.OperationalError, match="commit failed"):
        media_routes.delete_media_attachment(
            "attachment-1",
            user_id="user-1",
        )

    assert calls["cleanup"] == 0
    assert blob.read_bytes() == b"keep-me"


def test_delete_blob_cleanup_runs_only_after_successful_commit(tmp_path, monkeypatch):
    blob = tmp_path / "committed-delete.png"
    blob.write_bytes(b"delete-after-commit")
    events = []
    calls = {"connections": 0}

    class Service:
        def delete(self, conn, user_id, attachment_id, *, defer_blob_cleanup=False):
            assert defer_blob_cleanup is True
            events.append("delete-db-row")
            return str(blob)

        def cleanup_unreferenced_blob(self, conn, user_id, storage_path):
            assert storage_path == str(blob)
            events.append("unlink-blob")
            blob.unlink(missing_ok=True)
            return True

    @contextmanager
    def connection():
        calls["connections"] += 1
        invocation = calls["connections"]
        yield object()
        events.append(f"commit-{invocation}")

    monkeypatch.setattr(media_routes, "service", Service())
    monkeypatch.setattr(media_routes, "get_connection", connection)

    media_routes.delete_media_attachment(
        "attachment-1",
        user_id="user-1",
    )

    assert events == [
        "delete-db-row",
        "commit-1",
        "unlink-blob",
        "commit-2",
    ]
    assert not blob.exists()
