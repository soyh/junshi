import sqlite3
import uuid
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MediaAttachmentRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        *,
        user_id: str,
        person_id: str,
        conversation_id: str,
        media_type: str,
        mime_type: str,
        original_filename: str,
        storage_path: str,
        sha256: str,
        size_bytes: int,
        sent_at: str | None,
    ) -> sqlite3.Row:
        attachment_id = str(uuid.uuid4())
        now = utc_now()
        conn.execute(
            """
            INSERT INTO media_attachments (
                id, user_id, person_id, conversation_id, message_id,
                media_type, mime_type, original_filename, storage_path,
                sha256, size_bytes, sent_at, analysis_status,
                analysis_text, created_at, updated_at
            ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?, ?)
            """,
            (
                attachment_id,
                user_id,
                person_id,
                conversation_id,
                media_type,
                mime_type,
                original_filename,
                storage_path,
                sha256,
                size_bytes,
                sent_at,
                now,
                now,
            ),
        )
        return self.get(conn, user_id, attachment_id)  # type: ignore[return-value]

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT * FROM media_attachments
            WHERE id = ? AND user_id = ?
            """,
            (attachment_id, user_id),
        ).fetchone()

    def list_for_conversation(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT * FROM media_attachments
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY COALESCE(sent_at, created_at) ASC, created_at ASC
            """,
            (user_id, conversation_id),
        ).fetchall()

    def count_for_storage_path(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        storage_path: str,
    ) -> int:
        row = conn.execute(
            """
            SELECT COUNT(*) AS reference_count
            FROM media_attachments
            WHERE user_id = ? AND storage_path = ?
            """,
            (user_id, storage_path),
        ).fetchone()
        return int(row["reference_count"] if row is not None else 0)

    def try_claim_analysis(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        *,
        claim_token: str,
        claimed_at: str,
        stale_before: str,
    ) -> sqlite3.Row | None:
        cursor = conn.execute(
            """
            UPDATE media_attachments
            SET analysis_status = 'pending',
                analysis_claim_token = ?,
                analysis_claimed_at = ?,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
              AND NOT (
                  analysis_status = 'completed'
                  AND message_id IS NOT NULL
              )
              AND (
                  analysis_claim_token IS NULL
                  OR analysis_claimed_at IS NULL
                  OR analysis_claimed_at <= ?
              )
            """,
            (
                claim_token,
                claimed_at,
                claimed_at,
                attachment_id,
                user_id,
                stale_before,
            ),
        )
        if cursor.rowcount <= 0:
            return None
        return self.get(conn, user_id, attachment_id)

    def get_claimed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        claim_token: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT * FROM media_attachments
            WHERE id = ?
              AND user_id = ?
              AND analysis_claim_token = ?
            """,
            (attachment_id, user_id, claim_token),
        ).fetchone()

    def mark_completed_claimed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        claim_token: str,
        analysis_text: str,
        message_id: str,
    ) -> sqlite3.Row | None:
        now = utc_now()
        cursor = conn.execute(
            """
            UPDATE media_attachments
            SET analysis_status = 'completed',
                analysis_text = ?,
                message_id = ?,
                analysis_claim_token = NULL,
                analysis_claimed_at = NULL,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
              AND analysis_claim_token = ?
            """,
            (
                analysis_text,
                message_id,
                now,
                attachment_id,
                user_id,
                claim_token,
            ),
        )
        if cursor.rowcount <= 0:
            return None
        return self.get(conn, user_id, attachment_id)

    def mark_failed_claimed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        claim_token: str,
    ) -> sqlite3.Row | None:
        now = utc_now()
        cursor = conn.execute(
            """
            UPDATE media_attachments
            SET analysis_status = 'failed',
                analysis_claim_token = NULL,
                analysis_claimed_at = NULL,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
              AND analysis_claim_token = ?
            """,
            (now, attachment_id, user_id, claim_token),
        )
        if cursor.rowcount <= 0:
            return None
        return self.get(conn, user_id, attachment_id)

    def delete(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
    ) -> bool:
        cursor = conn.execute(
            "DELETE FROM media_attachments WHERE id = ? AND user_id = ?",
            (attachment_id, user_id),
        )
        return cursor.rowcount > 0
