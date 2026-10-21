"""Small SQLite state store: contact mapping, dedup ids, daily counters, flags."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    contact_id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    label TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS seen_messages (
    message_id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_counts (
    day TEXT NOT NULL,
    contact_id TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (day, contact_id)
);
CREATE TABLE IF NOT EXISTS flags (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL UNIQUE,
    contact_id TEXT NOT NULL,
    contact_name TEXT,
    text TEXT NOT NULL,
    sent_at REAL,
    is_group INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'queued',
    reason TEXT,
    next_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS outbox_due ON outbox (state, next_at);
"""


class StateStore:
    def __init__(self, path: str | Path):
        self._path = str(path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # -- contacts ---------------------------------------------------------
    def get_contact(self, contact_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM contacts WHERE contact_id = ?", (contact_id,)
            ).fetchone()
        return dict(row) if row else None

    def save_contact(
        self,
        contact_id: str,
        person_id: str,
        conversation_id: str,
        label: str | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO contacts (contact_id, person_id, conversation_id, label, enabled,
                                      created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(contact_id) DO UPDATE SET
                    person_id = excluded.person_id,
                    conversation_id = excluded.conversation_id,
                    label = COALESCE(excluded.label, contacts.label),
                    enabled = 1,
                    updated_at = excluded.updated_at
                """,
                (contact_id, person_id, conversation_id, label, now, now),
            )
            self._conn.commit()

    def list_contacts(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM contacts ORDER BY created_at"
            ).fetchall()
        return [dict(row) for row in rows]

    def set_enabled(self, contact_id: str, enabled: bool) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE contacts SET enabled = ?, updated_at = ? WHERE contact_id = ?",
                (1 if enabled else 0, datetime.now().isoformat(timespec="seconds"), contact_id),
            )
            self._conn.commit()

    # -- dedup ------------------------------------------------------------
    def first_seen(self, message_id: str, contact_id: str) -> bool:
        """Record the id; return True only the first time it is seen."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO seen_messages (message_id, contact_id, seen_at) VALUES (?, ?, ?)",
                (message_id, contact_id, now),
            )
            self._conn.commit()
        return cur.rowcount == 1

    # -- counters ---------------------------------------------------------
    def today_count(self, day: str, contact_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT count FROM daily_counts WHERE day = ? AND contact_id = ?",
                (day, contact_id),
            ).fetchone()
        return int(row["count"]) if row else 0

    def total_today(self, day: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COALESCE(SUM(count), 0) AS total FROM daily_counts WHERE day = ?",
                (day,),
            ).fetchone()
        return int(row["total"]) if row else 0

    def bump(self, day: str, contact_id: str) -> int:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO daily_counts (day, contact_id, count) VALUES (?, ?, 1)
                ON CONFLICT(day, contact_id) DO UPDATE SET count = count + 1
                """,
                (day, contact_id),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT count FROM daily_counts WHERE day = ? AND contact_id = ?",
                (day, contact_id),
            ).fetchone()
        return int(row["count"])

    # -- outbox -----------------------------------------------------------
    def enqueue(
        self,
        message_id: str,
        contact_id: str,
        text: str,
        *,
        contact_name: str = "",
        sent_at: float | None = None,
        is_group: bool = False,
    ) -> bool:
        """Store an inbound message that still owes a reply. True when new."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT OR IGNORE INTO outbox
                    (message_id, contact_id, contact_name, text, sent_at, is_group,
                     attempts, state, next_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 'queued', ?, ?, ?)
                """,
                (
                    message_id, contact_id, contact_name or "", text,
                    float(sent_at or 0.0), 1 if is_group else 0,
                    now, now, now,
                ),
            )
            self._conn.commit()
        return cur.rowcount == 1

    def outbox_due(self, now: str, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM outbox
                WHERE state = 'queued' AND (next_at IS NULL OR next_at <= ?)
                ORDER BY id LIMIT ?
                """,
                (now, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def outbox_pending(self, contact_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM outbox WHERE contact_id = ? AND state = 'queued' ORDER BY id",
                (contact_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def outbox_counts(self) -> dict[str, int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT state, COUNT(*) AS n FROM outbox GROUP BY state"
            ).fetchall()
        counts = {str(row["state"]): int(row["n"]) for row in rows}
        return {
            "queued": counts.get("queued", 0),
            "failed": counts.get("failed", 0),
            "skipped": counts.get("skipped", 0),
            "sent": counts.get("sent", 0),
        }

    def outbox_finish(self, ids: list[int], state: str, reason: str = "",
                      next_at: str | None = None, *, attempts: int | None = None) -> None:
        if not ids:
            return
        now = datetime.now().isoformat(timespec="seconds")
        marks = ",".join("?" for _ in ids)
        with self._lock:
            self._conn.execute(
                f"""
                UPDATE outbox SET state = ?, reason = ?, next_at = ?, updated_at = ?,
                    attempts = COALESCE(?, attempts)
                WHERE id IN ({marks})
                """,
                [state, reason or None, next_at, now, attempts, *ids],
            )
            self._conn.commit()

    def outbox_rows(self, state: str, limit: int = 20) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM outbox WHERE state = ? ORDER BY updated_at DESC LIMIT ?",
                (state, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def last_failure(self) -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT contact_id, reason, updated_at FROM outbox "
                "WHERE state IN ('failed', 'skipped', 'queued') AND reason IS NOT NULL "
                "ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            return ""
        return f"{row['contact_id']}: {row['reason']}"

    # -- flags ------------------------------------------------------------
    def get_flag(self, name: str) -> str | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM flags WHERE name = ?", (name,)).fetchone()
        return row["value"] if row else None

    def set_flag(self, name: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO flags (name, value) VALUES (?, ?) "
                "ON CONFLICT(name) DO UPDATE SET value = excluded.value",
                (name, value),
            )
            self._conn.commit()

    def set_paused(self, paused: bool) -> None:
        self.set_flag("paused", "1" if paused else "0")

    def paused(self) -> bool:
        return self.get_flag("paused") == "1"

    def close(self) -> None:
        with self._lock:
            self._conn.close()
