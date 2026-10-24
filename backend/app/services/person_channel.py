"""Identity of a counterpart across channels, plus WeChat exchange.

The same human can write on WeChat, 小红书 and Soul. `person_platform_accounts`
already stores one row per (user, platform, handle) pointing at a person, so the
strategist keeps ONE conversation and one memory per human instead of one per
platform. This module is the bridge-facing wrapper: resolve a handle, claim it
for a person, and keep the WeChat ids that make a contact hand-off possible.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from app.services.person_conversation import PersonConversationService, PersonNotFoundForConversation

MAX_EXTERNAL_ID = 120

#: WeChat ids the counterpart may type in chat: a letter then 5-19 of
#: letters/digits/`_`/`-`. Deliberately conservative so ordinary words are not
#: captured as a handle.
WECHAT_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{5,19}")

_SPLIT = re.compile(r"[\s，,。.、:：;；!！?？()（）\[\]【】\"'“”‘’~～]+")


class PersonChannelError(Exception):
    pass


class PersonChannelConflict(PersonChannelError):
    """The handle is already bound to a different person."""


def looks_like_wechat_id(text: str) -> bool:
    return bool(WECHAT_ID.fullmatch(text.strip()))


def extract_wechat_id(text: str) -> str:
    """Pull a WeChat id out of what the counterpart wrote, or ''."""
    for token in _SPLIT.split(text or ""):
        token = token.strip()
        if not looks_like_wechat_id(token):
            continue
        if token.lower() in {"wechat", "weixin", "wxid", "contact", "number", "wechatid"}:
            continue
        return token
    return ""


class PersonChannelService:
    def __init__(self) -> None:
        self.conversations = PersonConversationService()

    def _owned_person(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT id, name FROM persons WHERE id = ? AND user_id = ?",
            (person_id, user_id),
        ).fetchone()
        if row is None:
            raise PersonNotFoundForConversation("Person not found")
        return row

    def _handle_row(
        self, conn: sqlite3.Connection, user_id: str, platform: str, handle: str
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT a.id, a.person_id, p.name AS person_name
            FROM person_platform_accounts a
            JOIN persons p ON p.id = a.person_id AND p.user_id = a.user_id
            WHERE a.user_id = ? AND a.platform = ? AND a.account_handle = ?
            """,
            (user_id, (platform or "").strip().lower(), (handle or "").strip()[:MAX_EXTERNAL_ID]),
        ).fetchone()

    def resolve(
        self, conn: sqlite3.Connection, user_id: str, *, platform: str, handle: str
    ) -> dict | None:
        """Which person (and which conversation) owns this channel handle?"""
        known = self._handle_row(conn, user_id, platform, handle)
        if known is None:
            return None
        conversation = self.conversations.ensure_primary(conn, user_id, str(known["person_id"]))
        return {
            "person_id": str(known["person_id"]),
            "person_name": str(known["person_name"]),
            "conversation_id": str(conversation["id"]),
            "platform": (platform or "").strip().lower(),
            "account_handle": (handle or "").strip()[:MAX_EXTERNAL_ID],
        }

    def link(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        *,
        platform: str,
        handle: str,
        display_name: str = "",
        reassign: bool = False,
    ) -> dict:
        """Claim a channel handle for a person.

        A handle belongs to exactly one person (that is what keeps one human on
        one conversation). Claiming a handle that already belongs to someone
        else fails unless the caller explicitly asks to move it.
        """
        person = self._owned_person(conn, user_id, person_id)
        platform = (platform or "").strip().lower()[:40]
        handle = (handle or "").strip()[:MAX_EXTERNAL_ID]
        if not platform or not handle:
            raise PersonChannelError("platform and handle are required")
        known = self._handle_row(conn, user_id, platform, handle)
        if known is not None and str(known["person_id"]) != person_id:
            if not reassign:
                raise PersonChannelConflict(
                    f"此平台账号已绑定到「{known['person_name']}」，如需合并请先在人物资料里合并"
                )
            conn.execute(
                "UPDATE person_platform_accounts SET person_id = ? WHERE id = ? AND user_id = ?",
                (person_id, known["id"], user_id),
            )
        elif known is None:
            conn.execute(
                "INSERT INTO person_platform_accounts"
                " (id, user_id, person_id, platform, account_handle, display_name, notes, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, '', ?)",
                (
                    str(uuid4()),
                    user_id,
                    person_id,
                    platform,
                    handle,
                    (display_name or "")[:120],
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        elif display_name:
            conn.execute(
                "UPDATE person_platform_accounts SET display_name = ? WHERE id = ? AND user_id = ?",
                ((display_name or "")[:120], known["id"], user_id),
            )
        conversation = self.conversations.ensure_primary(conn, user_id, person_id)
        return {
            "person_id": person_id,
            "person_name": str(person["name"]),
            "platform": platform,
            "account_handle": handle,
            "conversation_id": str(conversation["id"]),
        }

    def unlink(
        self, conn: sqlite3.Connection, user_id: str, person_id: str, platform: str, handle: str
    ) -> dict:
        cursor = conn.execute(
            "DELETE FROM person_platform_accounts"
            " WHERE user_id = ? AND person_id = ? AND platform = ? AND account_handle = ?",
            (
                user_id,
                person_id,
                (platform or "").strip().lower(),
                (handle or "").strip()[:MAX_EXTERNAL_ID],
            ),
        )
        return {"deleted": cursor.rowcount > 0}

    def for_person(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> list[dict]:
        self._owned_person(conn, user_id, person_id)
        rows = conn.execute(
            """
            SELECT id, platform, account_handle, display_name, created_at
            FROM person_platform_accounts
            WHERE user_id = ? AND person_id = ?
            ORDER BY created_at, platform
            """,
            (user_id, person_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def set_wechat_id(
        self, conn: sqlite3.Connection, user_id: str, person_id: str, wechat_id: str
    ) -> dict:
        self._owned_person(conn, user_id, person_id)
        value = (wechat_id or "").strip()[:60]
        conn.execute(
            "UPDATE persons SET wechat_id = ?, updated_at = CURRENT_TIMESTAMP"
            " WHERE id = ? AND user_id = ?",
            (value, person_id, user_id),
        )
        return {"person_id": person_id, "wechat_id": value}

    def capture_wechat_id(
        self, conn: sqlite3.Connection, user_id: str, person_id: str, text: str
    ) -> str:
        """Store a WeChat id the counterpart typed; never overwrite an existing one."""
        candidate = extract_wechat_id(text)
        if not candidate:
            return ""
        try:
            row = conn.execute(
                "SELECT wechat_id FROM persons WHERE id = ? AND user_id = ?",
                (person_id, user_id),
            ).fetchone()
        except sqlite3.OperationalError:
            return ""
        if row is None:
            return ""
        if str(row["wechat_id"] or "").strip():
            return ""
        conn.execute(
            "UPDATE persons SET wechat_id = ?, updated_at = CURRENT_TIMESTAMP"
            " WHERE id = ? AND user_id = ?",
            (candidate, person_id, user_id),
        )
        return candidate
