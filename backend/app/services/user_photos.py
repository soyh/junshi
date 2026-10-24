"""本人照片库：上传一次，对方要照片时从那几张里发。

只存缩略前的原图（上限 8MB，jpeg/png/webp），说明文字用于让判断层知道这张
照片“拍的是什么场景”，避免把健身房照当成证件照发出去。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

MAX_BYTES = 8 * 1024 * 1024
ALLOWED = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
LIST_LIMIT = 30
PROMPT_LIMIT = 8


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_photo(conn, user_id: str, *, content: bytes, mime: str, filename: str, caption: str = "") -> dict:
    if mime not in ALLOWED:
        raise ValueError("unsupported-image")
    if not content:
        raise ValueError("empty-image")
    if len(content) > MAX_BYTES:
        raise ValueError("image-too-large")
    photo_id = str(uuid.uuid4())
    clean = " ".join(str(caption or "").split())[:120]
    conn.execute(
        "INSERT INTO user_photos (id, user_id, caption, mime, filename, content, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (photo_id, user_id, clean, mime, (filename or "").strip()[:120] or f"photo.{ALLOWED[mime]}",
         content, now()),
    )
    conn.commit()
    return {"id": photo_id, "caption": clean, "mime": mime, "bytes": len(content)}


def list_photos(conn, user_id: str, limit: int = LIST_LIMIT) -> list[dict]:
    rows = conn.execute(
        "SELECT id, caption, mime, filename, LENGTH(content) AS bytes, created_at"
        " FROM user_photos WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, int(limit)),
    ).fetchall()
    return [dict(row) for row in rows]


def read_photo(conn, user_id: str, photo_id: str) -> dict | None:
    row = conn.execute(
        "SELECT id, caption, mime, filename, content FROM user_photos WHERE user_id = ? AND id = ?",
        (user_id, photo_id),
    ).fetchone()
    return dict(row) if row is not None else None


def delete_photo(conn, user_id: str, photo_id: str) -> bool:
    changed = conn.execute(
        "DELETE FROM user_photos WHERE user_id = ? AND id = ?", (user_id, photo_id)
    ).rowcount
    conn.commit()
    return bool(changed)


def pick_for_prompt(conn, user_id: str, limit: int = PROMPT_LIMIT) -> list[dict]:
    """What the planner may hand out: ids plus the scene each one shows."""
    return [
        {"id": row["id"], "caption": row["caption"]}
        for row in list_photos(conn, user_id, limit=limit)
    ]
