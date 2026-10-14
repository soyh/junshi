from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.services.account_identity import AccountIdentityService, AccountIdentityError
from app.services.account_deletion import prepare_deletion,cleanup_result,finish_cleanup

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

class AdminDeletion(BaseModel):
    model_config=ConfigDict(extra='forbid')
    confirmation:Literal['DELETE']
    reason:str=Field(min_length=1,max_length=500)

@router.get('')
def users(offset:int=Query(0,ge=0),admin:str=Depends(administrator)):
    with get_connection() as c:
        service.audit(c,admin,'accounts','list','查询用户列表')
        rows=c.execute('SELECT u.id,u.created_at,c.username,i.email,i.email_verified_at,COALESCE(i.disabled,0) disabled,COALESCE(i.administrator,0) administrator FROM users u LEFT JOIN user_credentials c ON c.user_id=u.id LEFT JOIN account_identities i ON i.user_id=u.id ORDER BY u.id LIMIT 50 OFFSET ?',(offset,)).fetchall()
    return [dict(r) for r in rows]

@router.get('/directory')
def directory(q:str=Query('',max_length=100),offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50),admin:str=Depends(administrator)):
    # Parameterized literal search: '%' and '_' in an account name are not wildcards.
    term=q.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
    pattern='%'+term+'%'
    joins=' FROM users u LEFT JOIN user_credentials c ON c.user_id=u.id LEFT JOIN account_identities i ON i.user_id=u.id'
    where=" WHERE (u.id LIKE ? ESCAPE '\\' OR c.username LIKE ? ESCAPE '\\' OR i.email LIKE ? ESCAPE '\\')"
    params=(pattern,pattern,pattern)
    with get_connection() as c:
        service.audit(c,admin,'accounts','list','查询分页用户目录')
        total=c.execute('SELECT COUNT(*)'+joins+where,params).fetchone()[0]
        rows=c.execute('SELECT u.id,u.created_at,c.username,i.email,COALESCE(i.disabled,0) disabled,COALESCE(i.administrator,0) administrator'+joins+where+' ORDER BY u.id LIMIT ? OFFSET ?',(*params,limit,offset)).fetchall()
    return {'items':[dict(row) for row in rows],'total':total,'offset':offset,'limit':limit}

@router.patch('/{target}/state')
def state(target:str,p:AccountState,admin:str=Depends(administrator)):
    try:
        with get_connection() as c: service.disable(c,admin,target,p.disabled,p.reason)
    except AccountIdentityError as e: raise HTTPException(400,str(e)) from None
    return {'status':'updated'}

@router.get('/{target}/data/{kind}')
def data(target:str,kind:Literal['persons','conversations','messages','relationships','person_memories','person_update_events','model_references','person_platform_accounts','media_attachments'],reason:str=Query(min_length=1,max_length=500),offset:int=Query(0,ge=0),admin:str=Depends(administrator)):
    columns={'persons':'id,name,nickname,notes,created_at','conversations':'id,person_id,title,status,created_at','messages':'id,conversation_id,sender_type,content,sent_at',
             'relationships':'id,person_id,status,stage,notes,long_term_goal,current_goal',
             'person_memories':'person_id,revision,summary_json,coverage_json,updated_at',
             'person_update_events':'id,person_id,source,outcome,reason,before_json,after_json,evidence_json,created_at',
             'model_references':'id,name,reference_type,original_filename,description,content',
             'person_platform_accounts':'id,person_id,platform,account_handle,display_name',
             'media_attachments':'id,person_id,conversation_id,media_type,mime_type,original_filename,size_bytes,sent_at,analysis_status,analysis_text'}
    with get_connection() as c:
        if not c.execute('SELECT 1 FROM users WHERE id=?',(target,)).fetchone(): raise HTTPException(404,'用户不存在')
        service.audit(c,admin,target,'view:'+kind,reason)
        order='person_id' if kind=='person_memories' else 'id'
        rows=c.execute(f'SELECT {columns[kind]} FROM {kind} WHERE user_id=? ORDER BY {order} LIMIT 50 OFFSET ?',(target,offset)).fetchall()
    return [dict(r) for r in rows]

@router.get('/audit/history')
def history(offset:int=Query(0,ge=0),admin:str=Depends(administrator)):
    with get_connection() as c:
        service.audit(c,admin,'audit','view:audit','查询管理员操作记录')
        rows=c.execute('SELECT id,actor_id,target_id,action,reason,created_at FROM account_management_audit ORDER BY created_at DESC,id DESC LIMIT 50 OFFSET ?',(offset,)).fetchall()
    return [dict(r) for r in rows]

@router.post('/{target}/delete')
def delete(target:str,p:AdminDeletion,admin:str=Depends(administrator)):
    try:
        with get_connection() as c:
            c.execute('BEGIN IMMEDIATE')
            job=prepare_deletion(c,admin,target,p.reason,administrator=True)
    except AccountIdentityError as e: raise HTTPException(400,str(e)) from None
    return cleanup_result(job)

@router.post('/cleanup/{job}/retry')
def retry_cleanup(job:str,admin:str=Depends(administrator)):
    with get_connection() as c:
        if not c.execute('SELECT 1 FROM account_file_cleanup WHERE id=?',(job,)).fetchone(): raise HTTPException(404,'清理任务不存在')
        service.audit(c,admin,job,'retry:cleanup','重试账号附件清理')
    try: return cleanup_result(job)
    except AccountIdentityError as e: raise HTTPException(400,str(e)) from None
