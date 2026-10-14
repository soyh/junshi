import sqlite3
import uuid
from app.services.auth_account import AuthAccountService, hash_password, verify_password
from app.services.auth_session import AuthSessionService
from app.services.account_mail import normalize_email


class AccountIdentityError(ValueError):
    pass


class AccountIdentityService:
    def require_password(self, conn, user_id, password):
        row=conn.execute('SELECT password_hash FROM user_credentials WHERE user_id=?',(user_id,)).fetchone()
        if row is None or not verify_password(password,row['password_hash']):
            raise AccountIdentityError('当前密码不正确')

    def register_verified(self, conn, username, password, email):
        email=normalize_email(email)
        if conn.execute('SELECT 1 FROM account_identities WHERE email=?',(email,)).fetchone():
            raise AccountIdentityError('该邮箱无法用于注册')
        session=AuthAccountService().register(conn,username,password)
        user_id=conn.execute('SELECT user_id FROM user_credentials WHERE username=?',(username.strip().lower(),)).fetchone()[0]
        conn.execute('INSERT INTO account_identities(user_id,email,email_verified_at) VALUES(?,?,CURRENT_TIMESTAMP)',(user_id,email))
        return session

    def bind_verified(self,conn,user_id,email):
        try:
            conn.execute('INSERT INTO account_identities(user_id,email,email_verified_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET email=excluded.email,email_verified_at=CURRENT_TIMESTAMP',(user_id,normalize_email(email)))
        except sqlite3.IntegrityError:
            raise AccountIdentityError('该邮箱无法绑定') from None

    def reset_verified(self,conn,email,password):
        row=conn.execute('SELECT user_id,disabled FROM account_identities WHERE email=? AND email_verified_at IS NOT NULL',(normalize_email(email),)).fetchone()
        if row is None or row['disabled']:
            raise AccountIdentityError('无法重置此账号')
        conn.execute('UPDATE user_credentials SET password_hash=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=?',(hash_password(password),row['user_id']))
        AuthSessionService().revoke_all_for_user(conn,row['user_id'])

    def require_admin(self,conn,user_id):
        row=conn.execute('SELECT administrator,disabled FROM account_identities WHERE user_id=?',(user_id,)).fetchone()
        if row is None or not row['administrator'] or row['disabled']:
            raise AccountIdentityError('需要管理员权限')

    def audit(self,conn,actor,target,action,reason):
        if not reason.strip(): raise AccountIdentityError('请填写操作原因')
        conn.execute('INSERT INTO account_management_audit(id,actor_id,target_id,action,reason) VALUES(?,?,?,?,?)',(str(uuid.uuid4()),actor,target,action,reason.strip()))

    def disable(self,conn,actor,target,disabled,reason):
        self.require_admin(conn,actor)
        if actor==target: raise AccountIdentityError('不能禁用当前管理员')
        if not conn.execute('SELECT 1 FROM users WHERE id=?',(target,)).fetchone(): raise AccountIdentityError('用户不存在')
        self.audit(conn,actor,target,'disable' if disabled else 'enable',reason)
        conn.execute('INSERT INTO account_identities(user_id,disabled) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET disabled=excluded.disabled',(target,int(disabled)))
        if disabled: AuthSessionService().revoke_all_for_user(conn,target)
