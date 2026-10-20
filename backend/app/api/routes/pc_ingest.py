import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.config.settings import get_settings
from app.schemas.message import MessageCreate
from app.services.message import MessageService
from app.services.media_chat_time import TimedMediaAttachmentService
from app.domain.errors import ConversationNotFoundError

router = APIRouter(prefix='/pc', tags=['pc-assistant'])


class Incoming(MessageCreate):
    operation_id: UUID
    content: str = Field(min_length=1, max_length=200000)
    platform: str | None = Field(default=None, max_length=40)
    platform_account_id: str | None = Field(default=None, max_length=64)


def receipt(conn, user, operation, conversation, content):
    if not conn.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?', (conversation, user)).fetchone():
        raise HTTPException(404, '会话不存在')
    fingerprint = hashlib.sha256(content).hexdigest()
    old = conn.execute('SELECT * FROM pc_ingest_receipts WHERE user_id=? AND operation_id=?', (user, str(operation))).fetchone()
    if old:
        if old['fingerprint'] != fingerprint or old['conversation_id'] != conversation:
            raise HTTPException(409, '本次操作内容已变化，请创建新的导入操作')
        return fingerprint, json.loads(old['result_json'])
    return fingerprint, None


def remember(conn, user, operation, conversation, fingerprint, result):
    conn.execute('INSERT INTO pc_ingest_receipts VALUES (?,?,?,?,?)', (user, str(operation), conversation, fingerprint, json.dumps(result)))


@router.post('/messages')
def incoming_message(payload: Incoming, user_id=Depends(get_current_user_id)):
    if payload.sender_type not in ('person', 'user'):
        raise HTTPException(422, 'PC 窗口只登记双方真实消息')
    with get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        raw = payload.model_dump_json(exclude={'operation_id'}).encode()
        fingerprint, old = receipt(conn, user_id, payload.operation_id, payload.conversation_id, raw)
        if old:
            return old
        row = MessageService().create_user_managed(conn, user_id, payload.conversation_id, payload.sender_type, payload.content, payload.sent_at)
        if payload.platform:
            conn.execute(
                'INSERT OR REPLACE INTO message_platform_sources (message_id, user_id, platform, account_id, created_at) VALUES (?,?,?,?,?)',
                (row['id'], user_id, payload.platform.strip().lower(), payload.platform_account_id, row['created_at']),
            )
            row = conn.execute('SELECT * FROM messages WHERE id=?', (row['id'],)).fetchone()
        result = dict(row)
        remember(conn, user_id, payload.operation_id, payload.conversation_id, fingerprint, result)
        return result


@router.post('/conversations/{conversation_id}/media')
def incoming_media(conversation_id: str, operation_id: UUID = Form(), sent_at: str = Form(), file: UploadFile = File(), user_id=Depends(get_current_user_id)):
    limit = get_settings().media_max_upload_bytes
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, '附件超过服务器大小限制')
    service = TimedMediaAttachmentService()
    try:
        with get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            fingerprint, old = receipt(conn, user_id, operation_id, conversation_id,
                                       json.dumps([sent_at, file.filename, file.content_type]).encode() + content)
            if old:
                return old
            row = service.create(conn, user_id=user_id, conversation_id=conversation_id,
                                 original_filename=file.filename or 'upload', mime_type=file.content_type or '',
                                 content=content, sent_at=sent_at)
            result = dict(row)
            remember(conn, user_id, operation_id, conversation_id, fingerprint, result)
            return result
    except (ValueError, ConversationNotFoundError):
        raise HTTPException(422, '附件格式、时间或会话不正确') from None
