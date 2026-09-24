import sqlite3
from pathlib import Path

import pytest

from app.repositories.media_attachment import MediaAttachmentRepository
from app.services.media_attachment import (
    MediaAnalysisInProgressError,
    MediaAttachmentService,
)


_CUTOFF = "2026-09-24T00:10:00+00:00"
_EXPIRED_AT = "2026-09-24T00:00:00+00:00"


def _media_conn(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(tmp_path / "media-lease-expiry.sqlite3")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE media_attachments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            message_id TEXT,
            media_type TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            sent_at TEXT,
            analysis_status TEXT NOT NULL,
            analysis_text TEXT,
            analysis_claim_token TEXT,
            analysis_claimed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO media_attachments (
            id, user_id, person_id, conversation_id, message_id,
            media_type, mime_type, original_filename, storage_path,
            sha256, size_bytes, sent_at, analysis_status, analysis_text,
            analysis_claim_token, analysis_claimed_at, created_at, updated_at
        ) VALUES (
            'attachment-1', 'user-1', 'person-1', 'conversation-1', NULL,
            'image', 'image/png', 'sample.png', '/tmp/sample.png',
            'abc', 3, '2026-09-24T00:00:00+00:00', 'pending', NULL,
            'expired-token', ?, '2026-09-24T00:00:00+00:00',
            '2026-09-24T00:00:00+00:00'
        )
        """,
        (_EXPIRED_AT,),
    )
    conn.commit()
    return conn


class _MessageService:
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
        return {"id": f"evidence-{self.create_calls}"}


def _service(message_service=None) -> MediaAttachmentService:
    service = MediaAttachmentService(
        repository=MediaAttachmentRepository(),
        message_service=message_service or _MessageService(),
    )
    service._analysis_stale_before = lambda: _CUTOFF
    return service


def test_expired_worker_cannot_prepare_or_complete_without_competing_reclaim(tmp_path):
    conn = _media_conn(tmp_path)
    messages = _MessageService()
    service = _service(messages)
    try:
        with pytest.raises(
            MediaAnalysisInProgressError,
            match="claim lost or expired",
        ):
            service.prepare_claimed_analysis(
                conn,
                "user-1",
                "attachment-1",
                "expired-token",
            )

        with pytest.raises(
            MediaAnalysisInProgressError,
            match="claim lost or expired",
        ):
            service.complete_claimed_analysis(
                conn,
                "user-1",
                "attachment-1",
                "expired-token",
                '{"media_summary":"stale result"}',
            )

        row = service.repository.get(conn, "user-1", "attachment-1")
        assert row is not None
        assert row["analysis_status"] == "pending"
        assert row["analysis_claim_token"] == "expired-token"
        assert row["message_id"] is None
        assert messages.create_calls == 0
    finally:
        conn.close()


def test_expired_worker_cannot_mutate_claim_to_failed(tmp_path):
    conn = _media_conn(tmp_path)
    service = _service()
    try:
        service.fail_claimed_analysis(
            conn,
            "user-1",
            "attachment-1",
            "expired-token",
        )

        row = service.repository.get(conn, "user-1", "attachment-1")
        assert row is not None
        assert row["analysis_status"] == "pending"
        assert row["analysis_claim_token"] == "expired-token"
        assert row["analysis_claimed_at"] == _EXPIRED_AT
    finally:
        conn.close()


def test_claim_at_expiry_boundary_is_not_active(tmp_path):
    conn = _media_conn(tmp_path)
    messages = _MessageService()
    service = _service(messages)
    try:
        conn.execute(
            """
            UPDATE media_attachments
            SET analysis_claimed_at = ?
            WHERE id = 'attachment-1'
            """,
            (_CUTOFF,),
        )
        conn.commit()

        with pytest.raises(MediaAnalysisInProgressError):
            service.complete_claimed_analysis(
                conn,
                "user-1",
                "attachment-1",
                "expired-token",
                '{"media_summary":"boundary result"}',
            )

        assert messages.create_calls == 0
    finally:
        conn.close()


def test_expired_claim_can_be_reclaimed_and_only_new_token_can_complete(tmp_path):
    conn = _media_conn(tmp_path)
    messages = _MessageService()
    service = MediaAttachmentService(
        repository=MediaAttachmentRepository(),
        message_service=messages,
    )
    try:
        row, new_token, existing_message_id = service.claim_analysis(
            conn,
            "user-1",
            "attachment-1",
        )
        conn.commit()

        assert new_token
        assert new_token != "expired-token"
        assert existing_message_id is None
        assert row["analysis_claim_token"] == new_token

        with pytest.raises(MediaAnalysisInProgressError):
            service.complete_claimed_analysis(
                conn,
                "user-1",
                "attachment-1",
                "expired-token",
                '{"media_summary":"old worker"}',
            )

        completed, evidence_id = service.complete_claimed_analysis(
            conn,
            "user-1",
            "attachment-1",
            new_token,
            '{"media_summary":"winning worker"}',
        )

        assert completed["analysis_status"] == "completed"
        assert completed["analysis_claim_token"] is None
        assert completed["analysis_claimed_at"] is None
        assert evidence_id == "evidence-1"
        assert messages.create_calls == 1
    finally:
        conn.close()
