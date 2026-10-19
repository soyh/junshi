"""Bridge plugin status: external channels (WeChat / Xiaohongshu / Soul) heartbeat.

The bridge is a separate process on a Windows machine; it only reports liveness
and counters here. No canonical business data is touched by these endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.core.database import get_connection

router = APIRouter(prefix="/bridge", tags=["bridge"])


class HeartbeatPayload(BaseModel):
    channel: str = Field(min_length=1, max_length=40)
    status: str = Field(default="online", max_length=20)
    replies_today: int = Field(default=0, ge=0)
    detail: str = Field(default="", max_length=500)


@router.post("/heartbeat", status_code=202)
def bridge_heartbeat(payload: HeartbeatPayload, user_id: str = Depends(get_current_user_id)):
    now = datetime.now(timezone.utc).isoformat()
    channel = payload.channel.strip().lower()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO bridge_heartbeats (user_id, channel, status, replies_today, detail, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, channel) DO UPDATE SET
                status = excluded.status,
                replies_today = excluded.replies_today,
                detail = excluded.detail,
                updated_at = excluded.updated_at
            """,
            (user_id, channel, payload.status, payload.replies_today, payload.detail, now),
        )
    return {"channel": channel, "updated_at": now}


@router.get("/status")
def bridge_status(user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT channel, status, replies_today, detail, updated_at
            FROM bridge_heartbeats
            WHERE user_id = ?
            ORDER BY channel
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]
