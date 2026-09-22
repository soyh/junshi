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

    def mark_completed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        analysis_text: str,
        message_id: str,
    ) -> sqlite3.Row | None:
        now = utc_now()
        conn.execute(
            """
            UPDATE media_attachments
            SET analysis_status = 'completed',
                analysis_text = ?,
                message_id = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (analysis_text, message_id, now, attachment_id, user_id),
        )
        return self.get(conn, user_id, attachment_id)

    def mark_failed(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
    ) -> sqlite3.Row | None:
        now = utc_now()
        conn.execute(
            """
            UPDATE media_attachments
            SET analysis_status = 'failed', updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (now, attachment_id, user_id),
        )
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
