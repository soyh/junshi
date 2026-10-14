from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.services.account_identity import AccountIdentityService, AccountIdentityError

router=APIRouter(prefix='/admin/accounts',tags=['account-admin'])
service=AccountIdentityService()

def administrator(user:str=Depends(get_current_user_id)):
    with get_connection() as c:
        try: service.require_admin(c,user)
        except AccountIdentityError: raise HTTPException(403,'需要管理员权限') from None
    return user

class AccountState(BaseModel):
    model_config=ConfigDict(extra='forbid')
    disabled:bool
    reason:str=Field(min_length=1,max_length=500)

@router.get('')
def users(offset:int=Query(0,ge=0),admin:str=Depends(administrator)):
    with get_connection() as c:
        service.audit(c,admin,'accounts','list','查询用户列表')
        rows=c.execute('SELECT u.id,u.created_at,c.username,i.email,i.email_verified_at,COALESCE(i.disabled,0) disabled,COALESCE(i.administrator,0) administrator FROM users u LEFT JOIN user_credentials c ON c.user_id=u.id LEFT JOIN account_identities i ON i.user_id=u.id ORDER BY u.id LIMIT 50 OFFSET ?',(offset,)).fetchall()
    return [dict(r) for r in rows]

@router.patch('/{target}/state')
def state(target:str,p:AccountState,admin:str=Depends(administrator)):
    try:
        with get_connection() as c: service.disable(c,admin,target,p.disabled,p.reason)
    except AccountIdentityError as e: raise HTTPException(400,str(e)) from None
    return {'status':'updated'}

@router.get('/{target}/data/{kind}')
def data(target:str,kind:Literal['persons','conversations','messages'],reason:str=Query(min_length=1,max_length=500),offset:int=Query(0,ge=0),admin:str=Depends(administrator)):
    columns={'persons':'id,name,nickname,notes,created_at','conversations':'id,person_id,title,status,created_at','messages':'id,conversation_id,sender_type,content,sent_at'}
    with get_connection() as c:
        if not c.execute('SELECT 1 FROM users WHERE id=?',(target,)).fetchone(): raise HTTPException(404,'用户不存在')
        service.audit(c,admin,target,'view:'+kind,reason)
        rows=c.execute(f'SELECT {columns[kind]} FROM {kind} WHERE user_id=? ORDER BY id LIMIT 50 OFFSET ?',(target,offset)).fetchall()
    return [dict(r) for r in rows]

@router.get('/audit/history')
def history(offset:int=Query(0,ge=0),admin:str=Depends(administrator)):
    with get_connection() as c:
        service.audit(c,admin,'audit','view:audit','查询管理员操作记录')
        rows=c.execute('SELECT id,actor_id,target_id,action,reason,created_at FROM account_management_audit ORDER BY created_at DESC,id DESC LIMIT 50 OFFSET ?',(offset,)).fetchall()
    return [dict(r) for r in rows]
