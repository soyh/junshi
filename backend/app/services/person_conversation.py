"""One primary conversation per person, plus consolidation of duplicates."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4


class PersonConversationError(Exception):
    pass


class PersonNotFoundForConversation(PersonConversationError):
    pass


class ConversationNotOwned(PersonConversationError):
    pass


class PersonConversationService:
    def _owned_person(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT id, name FROM persons WHERE id = ? AND user_id = ?",
            (person_id, user_id),
        ).fetchone()
        if row is None:
            raise PersonNotFoundForConversation("Person not found")
        return row

    def ensure_primary(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> sqlite3.Row:
        person = self._owned_person(conn, user_id, person_id)

        primary = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? AND person_id = ? AND is_primary = 1",
            (user_id, person_id),
        ).fetchone()
        if primary is not None:
            return primary

        existing = conn.execute(
            """
            SELECT * FROM conversations
            WHERE user_id = ? AND person_id = ?
            ORDER BY created_at, id
            LIMIT 1
            """,
            (user_id, person_id),
        ).fetchone()
        if existing is not None:
            conn.execute(
                "UPDATE conversations SET is_primary = 1, updated_at = ? WHERE id = ?",
                (_now(), existing["id"]),
            )
            return conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (existing["id"],)
            ).fetchone()

        conversation_id = str(uuid4())
        now = _now()
        conn.execute(
            """
            INSERT INTO conversations
                (id, user_id, person_id, relationship_id, title, status, created_at, updated_at, is_primary)
            VALUES (?, ?, ?, NULL, ?, 'active', ?, ?, 1)
            """,
            (conversation_id, user_id, person_id, person["name"], now, now),
        )
        return conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()

    def _others(self, conn: sqlite3.Connection, user_id: str, person_id: str, target_id: str) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT id FROM conversations
            WHERE user_id = ? AND person_id = ? AND id != ?
            ORDER BY created_at, id
            """,
            (user_id, person_id, target_id),
        ).fetchall()

    def preview(self, conn: sqlite3.Connection, user_id: str, person_id: str, target_id: str | None = None) -> dict:
        self._owned_person(conn, user_id, person_id)
        primary = self.ensure_primary(conn, user_id, person_id)
        target = primary["id"]
        if target_id:
            self._assert_target(conn, user_id, person_id, target_id)
            target = target_id
        others = [row["id"] for row in self._others(conn, user_id, person_id, target)]
        messages = 0
        media = 0
        overrides = 0
        for conversation_id in others:
            messages += _scalar(conn, "SELECT COUNT(*) FROM messages WHERE user_id = ? AND conversation_id = ?", (user_id, conversation_id))
            media += _scalar(conn, "SELECT COUNT(*) FROM media_attachments WHERE user_id = ? AND conversation_id = ?", (user_id, conversation_id))
            overrides += _scalar(conn, "SELECT COUNT(*) FROM conversation_model_reference_overrides WHERE user_id = ? AND conversation_id = ?", (user_id, conversation_id))
        return {
            "person_id": person_id,
            "target_conversation_id": target,
            "source_conversation_ids": others,
            "messages": messages,
            "media_attachments": media,
            "reference_overrides": overrides,
        }

    def consolidate(self, conn: sqlite3.Connection, user_id: str, person_id: str, target_id: str | None = None) -> dict:
        self._owned_person(conn, user_id, person_id)
        primary = self.ensure_primary(conn, user_id, person_id)
        target = primary["id"]
        if target_id:
            self._assert_target(conn, user_id, person_id, target_id)
            target = target_id
            conn.execute(
                "UPDATE conversations SET is_primary = 0 WHERE user_id = ? AND person_id = ? AND id != ?",
                (user_id, person_id, target),
            )
            conn.execute("UPDATE conversations SET is_primary = 1 WHERE id = ?", (target,))

        others = [row["id"] for row in self._others(conn, user_id, person_id, target)]
        moved = {"conversations": 0, "messages": 0, "media_attachments": 0, "reference_overrides": 0}

        for conversation_id in others:
            cursor = conn.execute(
                "UPDATE messages SET conversation_id = ?, updated_at = ? WHERE user_id = ? AND conversation_id = ?",
                (target, _now(), user_id, conversation_id),
            )
            moved["messages"] += cursor.rowcount

            cursor = conn.execute(
                "UPDATE media_attachments SET conversation_id = ?, updated_at = ? WHERE user_id = ? AND conversation_id = ?",
                (target, _now(), user_id, conversation_id),
            )
            moved["media_attachments"] += cursor.rowcount

            conn.execute(
                """
                DELETE FROM conversation_model_reference_overrides
                WHERE user_id = ? AND conversation_id = ? AND reference_id IN (
                    SELECT reference_id FROM conversation_model_reference_overrides
                    WHERE user_id = ? AND conversation_id = ?
                )
                """,
                (user_id, conversation_id, user_id, target),
            )
            cursor = conn.execute(
                "UPDATE conversation_model_reference_overrides SET conversation_id = ? WHERE user_id = ? AND conversation_id = ?",
                (target, user_id, conversation_id),
            )
            moved["reference_overrides"] += cursor.rowcount

            conn.execute(
                "DELETE FROM conversation_platform_sources WHERE conversation_id = ?",
                (conversation_id,),
            )
            conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
            moved["conversations"] += 1

        conn.execute("UPDATE conversations SET is_primary = 1, updated_at = ? WHERE id = ?", (_now(), target))
        return {"person_id": person_id, "target_conversation_id": target, "moved": moved}

    def _assert_target(self, conn: sqlite3.Connection, user_id: str, person_id: str, target_id: str) -> None:
        row = conn.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND user_id = ? AND person_id = ?",
            (target_id, user_id, person_id),
        ).fetchone()
        if row is None:
            raise ConversationNotOwned("Conversation does not belong to this person")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scalar(conn: sqlite3.Connection, sql: str, params: tuple) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0]) if row else 0
