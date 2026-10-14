import uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from app.config.settings import get_settings
from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.auth_account import AuthRegisterRequest
from app.api.routes.auth_account import _session_response
from app.services.auth_account import AuthAccountConflict
from app.services.account_identity import AccountIdentityService, AccountIdentityError
from app.services.account_mail import MailSettings, VerificationMailer, normalize_email
from app.services.email_challenge import EmailChallengeService, EmailChallengeError
from app.services.account_deletion import prepare_deletion,cleanup_result

router=APIRouter(prefix='/auth/email',tags=['account-email'])
identity=AccountIdentityService()

@router.get('/policy')
def policy():
    c=get_settings()
    return {'email_registration_required':c.email_registration_required,
            'mail_available':bool(c.smtp_host and c.smtp_username and c.smtp_password and c.smtp_sender and len(c.email_verification_secret)>=32)}

class SendCode(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email:str=Field(min_length=3,max_length=254)
    purpose:Literal['register','bind','reset','delete']
    current_password:SecretStr|None=None

class Verification(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email:str=Field(min_length=3,max_length=254)
    challenge_id:str=Field(min_length=36,max_length=36)
    code:str=Field(pattern=r'^[0-9]{6}$')

class EmailRegistration(AuthRegisterRequest):
    email:str=Field(min_length=3,max_length=254)
    challenge_id:str=Field(min_length=36,max_length=36)
    code:str=Field(pattern=r'^[0-9]{6}$')

class EmailBinding(Verification):
    current_password:SecretStr

class PasswordReset(Verification):
    new_password:SecretStr=Field(min_length=12,max_length=256)

class AccountDeletion(EmailBinding):
    confirmation:Literal['DELETE']

def challenge_service():
    c=get_settings()
    if not all((c.smtp_host,c.smtp_username,c.smtp_password,c.smtp_sender)) or len(c.email_verification_secret)<32:
        raise HTTPException(503,'邮件服务尚未配置')
    return EmailChallengeService(c.email_verification_secret,VerificationMailer(MailSettings(c.smtp_host,c.smtp_port,c.smtp_username,c.smtp_password,c.smtp_sender,c.smtp_implicit_tls)))

@router.post('/code')
def send_code(p:SendCode,request:Request):
    s=challenge_service()
    try: email=normalize_email(p.email)
    except ValueError as e: raise HTTPException(422,str(e)) from None
    user=None
    if p.purpose in ('bind','delete'):
        user=get_current_user_id(request.headers.get('authorization'),None)
        with get_connection() as conn:
            try: identity.require_password(conn,user,p.current_password.get_secret_value() if p.current_password else '')
            except AccountIdentityError: raise HTTPException(401,'当前密码不正确') from None
            if p.purpose=='delete':
                row=conn.execute('SELECT email FROM account_identities WHERE user_id=? AND email_verified_at IS NOT NULL',(user,)).fetchone()
                if row is None or row['email']!=email: raise HTTPException(400,'请使用已绑定邮箱')
    if p.purpose=='reset':
        with get_connection() as conn:
            row=conn.execute('SELECT 1 FROM account_identities WHERE email=? AND email_verified_at IS NOT NULL AND disabled=0',(email,)).fetchone()
        if row is None: return {'challenge_id':str(uuid.uuid4()),'message':'如果邮箱符合条件，验证码将发送至该邮箱'}
    try:
        with get_connection() as conn:
            identifier=s.send(conn,email,p.purpose,request.client.host if request.client else 'unknown',user)
    except EmailChallengeError as e: raise HTTPException(429,str(e)) from None
    except ValueError as e: raise HTTPException(503,str(e)) from None
    return {'challenge_id':identifier,'message':'如果邮箱符合条件，验证码将发送至该邮箱'}

def verified_action(p,purpose,action,user=None):
    s=challenge_service(); error=None;result=None
    with get_connection() as conn:
        try: valid=s.consume(conn,p.challenge_id,p.email,purpose,p.code,user)
        except ValueError: valid=False
        if not valid: error='验证码无效、过期或尝试次数过多'
        else:
            conn.execute('SAVEPOINT verified_action')
            try: result=action(conn)
            except (AccountIdentityError,AuthAccountConflict) as e:
                conn.execute('ROLLBACK TO verified_action');error=str(e)
            conn.execute('RELEASE verified_action')
    if error: raise HTTPException(400,error)
    return result

@router.post('/register',status_code=201)
def register(p:EmailRegistration):
    return _session_response(verified_action(p,'register',lambda c:identity.register_verified(c,p.username,p.password.get_secret_value(),p.email)))

@router.put('/binding')
def bind(p:EmailBinding,user:str=Depends(get_current_user_id)):
    def action(c):
        identity.require_password(c,user,p.current_password.get_secret_value())
        identity.bind_verified(c,user,p.email)
        return {'status':'bound'}
    return verified_action(p,'bind',action,user)

@router.post('/reset-password')
def reset(p:PasswordReset):
    def action(c):
        identity.reset_verified(c,p.email,p.new_password.get_secret_value())
        return {'status':'password-reset'}
    return verified_action(p,'reset',action)

@router.get('/identity')
def own_identity(user:str=Depends(get_current_user_id)):
    with get_connection() as c:
        row=c.execute('SELECT email,email_verified_at,administrator FROM account_identities WHERE user_id=?',(user,)).fetchone()
    return dict(row) if row else {'email':None,'email_verified_at':None,'administrator':0}

@router.post('/delete-account')
def delete_account(p:AccountDeletion,user:str=Depends(get_current_user_id)):
    def action(c):
        identity.require_password(c,user,p.current_password.get_secret_value())
        row=c.execute('SELECT email FROM account_identities WHERE user_id=? AND email_verified_at IS NOT NULL',(user,)).fetchone()
        if row is None or row['email']!=normalize_email(p.email): raise AccountIdentityError('请使用已绑定邮箱')
        return prepare_deletion(c,user,user,'用户验证密码和邮箱后确认注销')
    job=verified_action(p,'delete',action,user)
    return cleanup_result(job)
