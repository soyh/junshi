import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.context import get_current_user_id
from app.core.database import get_connection

router = APIRouter(tags=['platform-accounts'])


class AccountInput(BaseModel):
    platform: str = Field(min_length=1, max_length=40)
    account_handle: str = Field(min_length=1, max_length=120)
    display_name: str = Field(default='', max_length=120)
    notes: str = Field(default='', max_length=1000)

    @field_validator('platform', 'account_handle')
    @classmethod
    def normalize(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('不能为空')
        return value


class SourceInput(BaseModel):
    account_id: str | None = None


def owned_person(conn, user_id, person_id):
    if not conn.execute('SELECT 1 FROM persons WHERE id=? AND user_id=?', (person_id, user_id)).fetchone():
        raise HTTPException(404, '人物不存在')


@router.get('/persons/{person_id}/platform-accounts')
def list_accounts(person_id: str, user_id=Depends(get_current_user_id)):
    with get_connection() as conn:
        owned_person(conn, user_id, person_id)
        return [dict(r) for r in conn.execute('SELECT * FROM person_platform_accounts WHERE user_id=? AND person_id=? ORDER BY created_at,id', (user_id, person_id))]


@router.post('/persons/{person_id}/platform-accounts', status_code=201)
def add_account(person_id: str, payload: AccountInput, user_id=Depends(get_current_user_id)):
    with get_connection() as conn:
        owned_person(conn, user_id, person_id)
        identifier = str(uuid4())
        try:
            conn.execute('INSERT INTO person_platform_accounts VALUES (?,?,?,?,?,?,?,?)',
                         (identifier, user_id, person_id, payload.platform.lower(), payload.account_handle,
                          payload.display_name, payload.notes, datetime.now(timezone.utc).isoformat()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, '此平台账号已经绑定人物，请先核对；不会按昵称自动合并。') from None
        return dict(conn.execute('SELECT * FROM person_platform_accounts WHERE id=?', (identifier,)).fetchone())


@router.delete('/persons/{person_id}/platform-accounts/{account_id}', status_code=204)
def remove_account(person_id: str, account_id: str, user_id=Depends(get_current_user_id)):
    with get_connection() as conn:
        owned_person(conn, user_id, person_id)
        if conn.execute('SELECT 1 FROM conversation_platform_sources WHERE user_id=? AND account_id=?', (user_id, account_id)).fetchone():
            raise HTTPException(409, '已有会话使用此账号，请先解除对应会话的来源绑定。')
        try:
            deleted = conn.execute('DELETE FROM person_platform_accounts WHERE id=? AND person_id=? AND user_id=?', (account_id, person_id, user_id))
        except sqlite3.IntegrityError:
            raise HTTPException(409, '已有会话使用此账号，请先解除对应会话的来源绑定。') from None
        if not deleted.rowcount:
            raise HTTPException(404, '账号不存在')


@router.get('/conversations/{conversation_id}/platform-source')
def get_source(conversation_id: str, user_id=Depends(get_current_user_id)):
    with get_connection() as conn:
        if not conn.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?', (conversation_id, user_id)).fetchone():
            raise HTTPException(404, '会话不存在')
        row = conn.execute('SELECT a.* FROM conversation_platform_sources s JOIN person_platform_accounts a ON a.id=s.account_id WHERE s.conversation_id=? AND s.user_id=?', (conversation_id, user_id)).fetchone()
        return dict(row) if row else None


@router.put('/conversations/{conversation_id}/platform-source')
def set_source(conversation_id: str, payload: SourceInput, user_id=Depends(get_current_user_id)):
    with get_connection() as conn:
        conversation = conn.execute('SELECT person_id FROM conversations WHERE id=? AND user_id=?', (conversation_id, user_id)).fetchone()
        if not conversation:
            raise HTTPException(404, '会话不存在')
        if payload.account_id:
            account = conn.execute('SELECT 1 FROM person_platform_accounts WHERE id=? AND user_id=? AND person_id=?', (payload.account_id, user_id, conversation['person_id'])).fetchone()
            if not account:
                raise HTTPException(404, '只能绑定当前人物自己的平台账号')
            conn.execute('INSERT INTO conversation_platform_sources VALUES (?,?,?) ON CONFLICT(conversation_id) DO UPDATE SET account_id=excluded.account_id', (conversation_id, user_id, payload.account_id))
        else:
            conn.execute('DELETE FROM conversation_platform_sources WHERE conversation_id=? AND user_id=?', (conversation_id, user_id))
    return {'saved': True}
