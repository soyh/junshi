import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.routes import media_attachments as media_routes
from app.repositories.media_attachment import MediaAttachmentRepository
from app.services.media_attachment import (
    MediaAnalysisInProgressError,
    MediaAttachmentService,
)


def _media_conn(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(tmp_path / "media-claims.sqlite3")
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
            'abc', 3, NULL, 'pending', NULL,
            NULL, NULL, '2026-09-24T00:00:00+00:00', '2026-09-24T00:00:00+00:00'
        )
        """
    )
    conn.commit()
    return conn


def test_media_claim_blocks_second_worker_and_stale_claim_can_be_recovered(tmp_path):
    conn = _media_conn(tmp_path)
    service = MediaAttachmentService(repository=MediaAttachmentRepository())
    try:
        first_row, first_token, first_existing = service.claim_analysis(
            conn,
            "user-1",
            "attachment-1",
        )
        conn.commit()

        assert first_row["analysis_status"] == "pending"
        assert first_token
        assert first_existing is None

        with pytest.raises(MediaAnalysisInProgressError):
            service.claim_analysis(conn, "user-1", "attachment-1")
        conn.rollback()

        conn.execute(
            """
            UPDATE media_attachments
            SET analysis_claimed_at = '2000-01-01T00:00:00+00:00'
            WHERE id = 'attachment-1'
            """
        )
        conn.commit()

        recovered_row, recovered_token, recovered_existing = service.claim_analysis(
            conn,
            "user-1",
            "attachment-1",
        )
        conn.commit()

        assert recovered_token
        assert recovered_token != first_token
        assert recovered_existing is None
        assert recovered_row["analysis_claim_token"] == recovered_token
    finally:
        conn.close()


def test_completed_media_returns_existing_evidence_without_new_claim(tmp_path):
    conn = _media_conn(tmp_path)
    service = MediaAttachmentService(repository=MediaAttachmentRepository())
    try:
        conn.execute(
            """
            UPDATE media_attachments
            SET analysis_status = 'completed',
                message_id = 'evidence-1'
            WHERE id = 'attachment-1'
            """
        )
        conn.commit()

        row, claim_token, evidence_message_id = service.claim_analysis(
            conn,
            "user-1",
            "attachment-1",
        )

        assert row["analysis_status"] == "completed"
        assert claim_token is None
        assert evidence_message_id == "evidence-1"
    finally:
        conn.close()


def test_analyze_route_runs_external_provider_call_outside_database_transaction(monkeypatch):
    state = {"active": 0, "max_active": 0, "provider_called": False}

    @contextmanager
    def fake_connection():
        state["active"] += 1
        state["max_active"] = max(state["max_active"], state["active"])
        try:
            yield object()
        finally:
            state["active"] -= 1

    class Service:
        def claim_analysis(self, conn, user_id, attachment_id):
            assert state["active"] == 1
            return {"id": attachment_id}, "claim-1", None

        def prepare_claimed_analysis(self, conn, user_id, attachment_id, claim_token):
            assert state["active"] == 1
            assert claim_token == "claim-1"
            return {"id": attachment_id, "media_type": "image"}, object()

        def analyze_claimed_media(self, provider, row):
            assert state["active"] == 0
            state["provider_called"] = True
            return '{"media_summary":"visible chat"}'

        def complete_claimed_analysis(
            self,
            conn,
            user_id,
            attachment_id,
            claim_token,
            analysis_text,
        ):
            assert state["active"] == 1
            assert claim_token == "claim-1"
            assert "visible chat" in analysis_text
            return {"id": attachment_id, "analysis_status": "completed"}, "evidence-1"

        def fail_claimed_analysis(self, *args, **kwargs):
            raise AssertionError("successful analysis must not fail its claim")

    monkeypatch.setattr(media_routes, "get_connection", fake_connection)
    monkeypatch.setattr(media_routes, "service", Service())

    result = media_routes.analyze_media_attachment(
        "attachment-1",
        user_id="user-1",
    )

    assert state["provider_called"] is True
    assert state["active"] == 0
    assert state["max_active"] == 1
    assert result["evidence_message_id"] == "evidence-1"
    assert result["attachment"]["analysis_status"] == "completed"


def test_analyze_route_returns_conflict_for_active_claim(monkeypatch):
    @contextmanager
    def fake_connection():
        yield object()

    class Service:
        def claim_analysis(self, conn, user_id, attachment_id):
            raise MediaAnalysisInProgressError("media analysis already in progress")

    monkeypatch.setattr(media_routes, "get_connection", fake_connection)
    monkeypatch.setattr(media_routes, "service", Service())

    with pytest.raises(HTTPException) as exc_info:
        media_routes.analyze_media_attachment(
            "attachment-1",
            user_id="user-1",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "media analysis already in progress"


def test_media_analysis_claim_migration_is_additive():
    migration = Path(__file__).parents[1] / "migrations" / "018_media_analysis_claims.sql"
    sql = migration.read_text()

    assert "ADD COLUMN analysis_claim_token TEXT" in sql
    assert "ADD COLUMN analysis_claimed_at TEXT" in sql
    assert "idx_media_attachments_analysis_claim" in sql
